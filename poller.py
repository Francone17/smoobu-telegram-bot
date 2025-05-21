import os
import json
import requests
from dotenv import load_dotenv
from dateutil import parser

load_dotenv()

SMOOBU_API_KEY = os.getenv("SMOOBU_API_KEY")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

SMOOBU_API_URL = "https://login.smoobu.com/api"
HEADERS = {"Api-Key": SMOOBU_API_KEY}
TELEGRAM_URL = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"

REPLIED_FILE = "replied.json"

VALID_APARTMENTS = {
    "B1 Suite 1", "B2 Suite 2", "B3 Suite 3", "B4 Casa dell'Alfiere", "B5 Casa Solferino",
    "B6 Carlina", "B7 San Carlo", "C1 De Lellis 1", "C2 De Lellis 2",
    "C3 De Lellis 3", "C4 De Lellis 4", "D Mercanti"
}

KEYWORDS_PARKING = [
    "parcheggio", "auto", "macchina", "garage", "dove parcheggiare",
    "parking", "car", "where to park"
]

PARKING_REPLY_IT = (
    "Per quanto riguarda il parcheggio, ci appoggiamo a un'autorimessa convenzionata che si trova "
    "a 3 a piedi minuti dall'appartamento. Si chiama Garage AUTOPALAZZO in Via Bertola 7. "
    "All'arrivo, comunicando che siete ospiti presso Top Living Apartments, otterrete una tariffa ridotta di 32€ al giorno."
)

PARKING_REPLY_EN = (
    "For what concerns parking, you can use a partner garage located 3 minutes away from the apartment. "
    "The place is called Garage AUTOPALAZZO (https://www.garageautopalazzo.it/?page_id=475), in Via Bertola 7.\n"
    "When you arrive at the garage, tell the personnel you are guests at Top Living Apartments and you'll pay a reduced tariff of 32€ per day."
)

def load_replied():
    if os.path.exists(REPLIED_FILE):
        with open(REPLIED_FILE, "r") as f:
            return set(json.load(f))
    return set()

def save_replied(replied_ids):
    with open(REPLIED_FILE, "w") as f:
        json.dump(list(replied_ids), f)

def get_all_bookings():
    res = requests.get(f"{SMOOBU_API_URL}/reservations", headers=HEADERS)
    return res.json().get("bookings", []) if res.ok else []

def get_messages(booking_id):
    url = f"{SMOOBU_API_URL}/reservations/{booking_id}/messages?onlyRelatedToGuest=true"
    res = requests.get(url, headers=HEADERS)
    return res.json().get("messages", []) if res.ok else []

def send_smoobu_reply(booking_id, message_text):
    url = f"{SMOOBU_API_URL}/reservations/{booking_id}/messages/send-message-to-guest"
    body = {
        "messageBody": message_text,
        "subject": "Risposta automatica"
    }
    res = requests.post(url, headers=HEADERS, json=body)
    return res.ok

def send_telegram_log(message):
    if TELEGRAM_CHAT_ID:
        requests.post(TELEGRAM_URL, json={"chat_id": TELEGRAM_CHAT_ID, "text": message})

def contains_parking_keywords(text):
    lower_text = text.lower()
    return any(keyword in lower_text for keyword in KEYWORDS_PARKING)

def generate_reply_from_ai(message):
    url = "https://api.openai.com/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {OPENAI_API_KEY}",
        "Content-Type": "application/json"
    }
    data = {
        "model": "gpt-3.5-turbo",
        "messages": [
            {
                "role": "system",
                "content": "Sei un assistente virtuale gentile, professionale e rapido nel rispondere agli ospiti che prenotano appartamenti. Fornisci risposte brevi, chiare e cortesi."
            },
            {
                "role": "user",
                "content": message
            }
        ],
        "temperature": 0.6
    }

    try:
        res = requests.post(url, headers=headers, json=data)
        if res.ok:
            return res.json()["choices"][0]["message"]["content"].strip()
        else:
            print("❌ Errore OpenAI:", res.status_code, res.text)
            return "Grazie per il messaggio! Ti risponderemo al più presto."
    except Exception as e:
        print("❌ Errore chiamata OpenAI:", e)
        return "Grazie per il messaggio! Ti risponderemo al più presto."

def check_and_reply():
    replied_ids = load_replied()
    bookings = get_all_bookings()

    for booking in bookings:
        booking_id = booking.get("id")
        apartment_name = booking.get("apartment", {}).get("name", "")
        language = booking.get("language", "it").lower()

        messages = get_messages(booking_id)
        if not messages:
            continue

        latest = messages[-1]
        latest_msg_id = latest["id"]

        if latest["type"] != 1 or str(latest_msg_id) in replied_ids:
            continue

        message_text = latest["message"]

        if apartment_name in VALID_APARTMENTS and contains_parking_keywords(message_text):
            ai_reply = PARKING_REPLY_IT if language == "it" else PARKING_REPLY_EN
        else:
            ai_reply = generate_reply_from_ai(message_text)

        sent = send_smoobu_reply(booking_id, ai_reply)
        if sent:
            replied_ids.add(str(latest_msg_id))
            save_replied(replied_ids)

        log = f"🤖 Risposta AI inviata per prenotazione #{booking_id} — Successo: {sent}\nMessaggio: {ai_reply}"
        print(log)
        send_telegram_log(log)

if __name__ == "__main__":
    check_and_reply()


