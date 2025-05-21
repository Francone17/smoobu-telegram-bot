import os
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
            return "Grazie per il messaggio! Ti risponderemo al più presto."
    except Exception as e:
        return f"Errore generazione AI: {e}"

def check_and_reply():
    bookings = get_all_bookings()
    for booking in bookings:
        booking_id = booking.get("id")
        messages = get_messages(booking_id)
        if not messages:
            continue

        latest = messages[-1]
        if latest["type"] != 1:
            continue

        latest_time = parser.parse(latest["createdAt"])
        already_replied = any(
            m["type"] == 2 and parser.parse(m["createdAt"]) > latest_time
            for m in messages
        )
        if already_replied:
            continue

        ai_reply = generate_reply_from_ai(latest["message"])
        sent = send_smoobu_reply(booking_id, ai_reply)

        log = f"🤖 Risposta AI inviata per prenotazione #{booking_id} — Successo: {sent}\nMessaggio: {ai_reply}"
        print(log)
        send_telegram_log(log)

if __name__ == "__main__":
    check_and_reply()
