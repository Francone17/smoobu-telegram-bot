import os
import requests
from dotenv import load_dotenv
from dateutil import parser
from openai import OpenAI

load_dotenv()

SMOOBU_API_KEY = os.getenv("SMOOBU_API_KEY")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

SMOOBU_API_URL = "https://login.smoobu.com/api"
HEADERS = {"API-Key": SMOOBU_API_KEY}
openai_client = OpenAI(api_key=OPENAI_API_KEY)

RELEVANT_PROPERTIES = [
    "B1 Suite 1", "B2 Suite 2", "B3 Suite 3", "B4 Casa dell'Alfiere",
    "B5 Casa Solferino", "B6 Carlina", "B7 San Carlo", "C1 De Lellis 1",
    "C2 De Lellis 2", "C3 De Lellis 3", "C4 De Lellis 4", "D Mercanti"
]

PARKING_MESSAGE_IT = (
    "Per quanto riguarda il parcheggio, ci appoggiamo a un'autorimessa convenzionata che si trova "
    "a 3 a piedi minuti dall'appartamento. Si chiama Garage AUTOPALAZZO in Via Bertola 7. All'arrivo, "
    "comunicando che siete ospiti presso Top Living Apartments, otterrete una tariffa ridotta di 32€ al giorno."
)

PARKING_MESSAGE_EN = (
    "For what concerns parking, you can use a partner garage located 3 minutes away from the apartment. "
    "The place is called Garage AUTOPALAZZO (https://www.garageautopalazzo.it/?page_id=475), in Via Bertola 7. "
    "When you arrive at the garage, tell the personnel you are guests at Top Living Apartments and you'll pay "
    "a reduced tariff of 32€ per day."
)

def get_all_reservations():
    try:
        response = requests.get(f"{SMOOBU_API_URL}/reservations", headers=HEADERS)
        response.raise_for_status()
        return response.json().get("bookings", [])
    except requests.HTTPError as e:
        print("❌ HTTP error:", e)
        return []

def get_messages(res_id):
    try:
        response = requests.get(f"{SMOOBU_API_URL}/reservations/{res_id}/messages", headers=HEADERS)
        response.raise_for_status()
        return response.json().get("messages", [])
    except Exception as e:
        print(f"⚠️ Errore nel recupero messaggi per prenotazione {res_id}: {e}")
        return []

def send_message(res_id, message):
    url = f"{SMOOBU_API_URL}/reservations/{res_id}/messages/send-message-to-guest"
    data = {
        "subject": "Risposta automatica",
        "messageBody": message
    }
    try:
        r = requests.post(url, headers=HEADERS, json=data)
        return r.status_code == 200
    except Exception as e:
        print(f"❌ Errore nell'invio messaggio a prenotazione {res_id}: {e}")
        return False

def notify_telegram(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    data = {"chat_id": TELEGRAM_CHAT_ID, "text": message}
    requests.post(url, data=data)

def detect_language(text):
    if any(word in text.lower() for word in ["where", "when", "how", "is", "are", "can", "you"]):
        return "en"
    return "it"

def generate_ai_reply(prompt, language):
    try:
        response = openai_client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {
                    "role": "system",
                    "content": f"Sei un assistente cordiale e gentile ma non troppo formale. Rispondi nel tono più adatto alla lingua del messaggio, che è: {language}."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0.7
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print("❌ Errore OpenAI:", e)
        return "Grazie per il messaggio! Ti risponderemo al più presto."

def check_and_reply():
    print("🔄 Controllo nuove conversazioni...")
    reservations = get_all_reservations()
    for res in reservations:
        res_id = res.get("id")
        apartment_name = res.get("apartment", {}).get("name", "")
        language = res.get("language", "it")
        messages = get_messages(res_id)

        if not messages:
            continue

        # Ordina messaggi per data decrescente
        sorted_msgs = sorted(
            [m for m in messages if "createdAt" in m],
            key=lambda m: parser.parse(m["createdAt"]),
            reverse=True
        )

        last_msg = sorted_msgs[0]
        if last_msg["type"] == 2:
            print(f"✅ Ultimo messaggio NON dell'ospite — prenotazione {res_id}")
            continue

        last_text = last_msg["message"]

        # Risposte speciali parcheggio
        if "parcheggio" in last_text.lower() and apartment_name in RELEVANT_PROPERTIES:
            reply = PARKING_MESSAGE_IT if language == "it" else PARKING_MESSAGE_EN
        else:
            reply = generate_ai_reply(last_text, language)

        sent = send_message(res_id, reply)
        print(f"🤖 Risposta AI inviata per prenotazione #{res_id} — Successo: {sent}")
        print(f"Messaggio: {reply}")

if __name__ == "__main__":
    check_and_reply()
