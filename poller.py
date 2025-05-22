import os
import requests
from dotenv import load_dotenv
from dateutil import parser
import openai

load_dotenv()

SMOOBU_API_KEY = os.getenv("SMOOBU_API_KEY")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
SMOOBU_API_URL = "https://login.smoobu.com/api"
HEADERS = {"Api-Key": SMOOBU_API_KEY}
openai.api_key = OPENAI_API_KEY

AUTO_REPLY_SIGNATURE = "🤖 Risposta AI inviata"

PARKING_PROPERTIES = [
    "B1 Suite 1", "B2 Suite 2", "B3 Suite 3", "B4 Casa dell'Alfiere",
    "B5 Casa Solferino", "B6 Carlina", "B7 San Carlo",
    "C1 De Lellis 1", "C2 De Lellis 2", "C3 De Lellis 3",
    "C4 De Lellis 4", "D Mercanti"
]

def send_telegram_message(text):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": text}
    requests.post(url, json=payload)

def get_all_reservations():
    response = requests.get(f"{SMOOBU_API_URL}/bookings", headers=HEADERS)
    return response.json().get("bookings", [])

def get_messages(reservation_id):
    url = f"{SMOOBU_API_URL}/reservations/{reservation_id}/messages?onlyRelatedToGuest=true"
    response = requests.get(url, headers=HEADERS)
    if response.status_code == 200:
        return response.json().get("messages", [])
    return []

def send_reply(reservation_id, text):
    url = f"{SMOOBU_API_URL}/reservations/{reservation_id}/messages/send-message-to-guest"
    payload = {
        "subject": "Risposta automatica",
        "messageBody": f"{text}\n\n{AUTO_REPLY_SIGNATURE}"
    }
    response = requests.post(url, headers=HEADERS, json=payload)
    return response.status_code == 200

def generate_reply(message_text, apartment_name, language):
    # Risposta parcheggio in base alla struttura
    if apartment_name in PARKING_PROPERTIES and "park" in message_text.lower():
        if language == "it":
            return ("Per quanto riguarda il parcheggio, ci appoggiamo a un'autorimessa convenzionata "
                    "che si trova a 3 minuti a piedi dall'appartamento. Si chiama Garage AUTOPALAZZO in Via Bertola 7. "
                    "All'arrivo, comunicando che siete ospiti presso Top Living Apartments, otterrete una tariffa ridotta di 32€ al giorno.")
        else:
            return ("For what concerns parking, you can use a partner garage located 3 minutes away from the apartment. "
                    "The place is called Garage AUTOPALAZZO (https://www.garageautopalazzo.it/?page_id=475), in Via Bertola 7.\n"
                    "When you arrive at the garage, tell the personnel you are guests at Top Living Apartments and you'll pay a reduced tariff of 32€ per day.")

    # Altrimenti usa OpenAI
    try:
        system_prompt = (
            "Sei un assistente per un host di appartamenti a Torino. Rispondi ai messaggi degli ospiti con tono cordiale e gentile, ma non eccessivamente formale. "
            "Evita risposte troppo lunghe. Firma non necessaria."
        )
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": message_text}
            ],
            temperature=0.7,
            max_tokens=300
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        send_telegram_message(f"❌ Errore OpenAI: {e}")
        return "Grazie per il messaggio! Ti risponderemo al più presto."

def check_and_reply():
    print("🔄 Controllo nuove conversazioni...")
    reservations = get_all_reservations()
    for res in reservations:
        res_id = res["id"]
        apt_name = res.get("apartment", {}).get("name", "")
        language = res.get("language", "it")

        messages = get_messages(res_id)
        if not messages:
            continue

        valid_msgs = [m for m in messages if "createdAt" in m]
        if not valid_msgs:
            print(f"⚠️ Nessuna data valida nei messaggi per prenotazione {res_id}, salto.")
            continue

        sorted_msgs = sorted(valid_msgs, key=lambda m: parser.parse(m["createdAt"]), reverse=True)
        last_msg = sorted_msgs[0]

        if last_msg["type"] == 2:
            print(f"📭 Ultimo messaggio per prenotazione {res_id} è nostro, nessuna risposta necessaria.")
            continue

        if AUTO_REPLY_SIGNATURE in last_msg.get("message", ""):
            print(f"⏭️ Messaggio già risposto automaticamente per prenotazione {res_id}, salto.")
            continue

        msg_text = last_msg.get("message", "")
        reply = generate_reply(msg_text, apt_name, language)
        success = send_reply(res_id, reply)

        print(f"🤖 Risposta AI inviata per prenotazione #{res_id} — Successo: {success}\nMessaggio: {reply}")

if __name__ == "__main__":
    check_and_reply()
