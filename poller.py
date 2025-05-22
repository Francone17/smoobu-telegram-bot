import os
import json
import requests
from dotenv import load_dotenv
from dateutil import parser

load_dotenv()

if os.getenv("BOT_ACTIVE", "true").lower() != "true":
    print("🛑 BOT DISATTIVATO — nessuna risposta inviata.")
    exit()

SMOOBU_API_KEY = os.getenv("SMOOBU_API_KEY")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

SMOOBU_API_URL = "https://login.smoobu.com/api"
HEADERS = {"Api-Key": SMOOBU_API_KEY}
TELEGRAM_URL = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"

REPLIED_FILE = "replied_bookings.json"

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
    "a 3 minuti a piedi dall'appartamento. Si chiama Garage AUTOPALAZZO in Via Bertola 7. "
    "All'arrivo, comunicando che siete ospiti presso Top Living Apartments, otterrete una tariffa ridotta di 32€ al giorno."
)

PARKING_REPLY_EN = (
    "For what concerns parking, you can use a partner garage located 3 minutes away from the apartment. "
    "The place is called Garage AUTOPALAZZO (https://www.garageautopalazzo.it/?page_id=475), in Via Bertola 7.\n"
    "When you arrive at the garage, tell the personnel you are guests at Top Living Apartments and you'll pay a reduced tariff of 32€ per day."
)

def load_replied_bookings():
    if os.path.exists(REPLIED_FILE):
        with open(REPLIED_FILE, "r") as f:
            return set(json.load(f))
    return set()

def save_replied_bookings(replied_ids):
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
    if not OPENAI_API_KEY:
        print("❌ Nessuna API Key OpenAI configurata.")
        return "Grazie per il messaggio! Ti risponderemo al più presto."

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
                "content": "Sei un assistente virtuale per appartamenti in affitto. Rispondi agli ospiti in modo amichevole, gentile e chiaro. Usa frasi semplici e dirette, evita formalismi eccessivi. Mostrati disponibile e umano, ma non invadente. Mantieni un tono professionale ma caldo."
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
    replied = load_replied_bookings()
    bookings = get_all_bookings()

    for booking in bookings:
        booking_id = booking.get("id")
        if str(booking_id) in replied:
            continue

        apartment_name = booking.get("apartment", {}).get("name", "")
        language = booking.get("language", "it").lower()
        notice_text = booking.get("notice", "").strip()

        messages = get_messages(booking_id)
        user_message = ""

        if messages:
            valid_msgs = [m for m in messages if "date" in m]
            if not valid_msgs:
                print(f"⚠️ Nessuna data valida nei messaggi per prenotazione {booking_id}, salto.")
                continue

            sorted_msgs = sorted(valid_msgs, key=lambda m: parser.parse(m["date"]), reverse=True)
            last_msg = sorted_msgs[0]

            if last_msg["type"] != 1:
                print(f"🔕 Ultimo messaggio per prenotazione {booking_id} non è dell’ospite, nessuna risposta.")
                continue

            user_message = last_msg["message"]
        elif notice_text:
            user_message = notice_text
        else:
            continue

        if apartment_name in VALID_APARTMENTS and contains_parking_keywords(user_message):
            reply = PARKING_REPLY_IT if language == "it" else PARKING_REPLY_EN
        else:
            reply = generate_reply_from_ai(user_message)

        sent = send_smoobu_reply(booking_id, reply)
        if sent:
            replied.add(str(booking_id))
            save_replied_bookings(replied)

        log = f"🤖 Risposta AI inviata per prenotazione #{booking_id} — Successo: {sent}\nMessaggio: {reply}"
        print(log)
        send_telegram_log(log)

if __name__ == "__main__":
    check_and_reply()

