import os
import requests
from dotenv import load_dotenv
from dateutil import parser
import openai

load_dotenv()

SMOOBU_API_KEY = os.getenv("SMOOBU_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

HEADERS = {"API-Key": SMOOBU_API_KEY}
BASE_URL = "https://login.smoobu.com/api"
openai.api_key = OPENAI_API_KEY


# Solo queste due prenotazioni verranno monitorate
ALLOWED_RESERVATION_IDS = [98806978]

def get_all_reservations():
    try:
        response = requests.get(f"{BASE_URL}/reservations/${ALLOWED_RESERVATION_IDS[0]}", headers=HEADERS)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.HTTPError as e:
        print(f"❌ HTTP error: {e}")
        return []

def get_messages(reservation_id):
    try:
        response = requests.get(
            f"{BASE_URL}/reservations/{reservation_id}/messages",
            headers=HEADERS
        )
        response.raise_for_status()
        return response.json().get("messages", [])
    except requests.exceptions.RequestException as e:
        print(f"❌ Errore recupero messaggi per prenotazione {reservation_id}: {e}")
        return []

def send_reply(reservation_id, message):
    data = {
        "subject": "Risposta automatica",
        "messageBody": message
    }
    response = requests.post(
        f"{BASE_URL}/reservations/{reservation_id}/messages/send-message-to-guest",
        headers=HEADERS,
        json=data
    )
    success = response.status_code == 200
    print(f"🤖 Risposta AI inviata per prenotazione #{reservation_id} — Successo: {success}")
    print(f"Messaggio: {message}")
    return success

def send_telegram_notification(text):
    requests.post(
        f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage",
        data={"chat_id": TELEGRAM_CHAT_ID, "text": text}
    )

def generate_ai_response(message_text, guest_name):
    try:
        system_prompt = (
            f"Sei un host di appartamenti turistici. Rispondi a questo messaggio da parte dell'ospite {guest_name} "
            "in modo gentile, utile e cordiale. Non troppo formale. Se chiede informazioni su parcheggio, rispondi con i dettagli dell'autorimessa convenzionata."
        )
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": message_text}
            ],
            max_tokens=300,
            temperature=0.7
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"❌ Errore OpenAI: {e}")
        return "Grazie per il messaggio! Ti risponderemo al più presto."

def check_and_reply():
    print("🔄 Controllo nuove conversazioni...")
    reservations = [get_all_reservations()]

    for res in reservations:
        res_id = res["id"]
        if res_id not in ALLOWED_RESERVATION_IDS:
            continue  # ignora prenotazioni non monitorate

        messages = get_messages(res_id)
        if not messages:
            print(f"⚠️ Nessun messaggio per prenotazione {res_id}, salto.")
            continue

        # Ordina messaggi per data
        try:
            sorted_msgs = sorted(
                messages,
                key=lambda m: parser.parse(m["createdAt"]),
                reverse=True
            )
        except Exception as e:
            print(f"⚠️ Errore ordinamento messaggi prenotazione {res_id}: {e}")
            continue

        last_msg = sorted_msgs[0]
        msg_type = last_msg.get("type")

        if msg_type == 1:
            print(f"📨 Ultimo messaggio DELL'ospite — prenotazione {res_id}")
            last_text = last_msg.get("message", "")
            guest_name = res.get("guest-name", "ospite")

            ai_reply = generate_ai_response(last_text, guest_name)
            send_reply(res_id, ai_reply)
        else:
            print(f"✅ Ultimo messaggio NON dell'ospite — prenotazione {res_id}")

if __name__ == "__main__":
    check_and_reply()
