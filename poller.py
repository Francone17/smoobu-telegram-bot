import os
import requests
from dotenv import load_dotenv

load_dotenv()

SMOOBU_API_KEY = os.getenv("SMOOBU_API_KEY")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")  # il tuo ID Telegram

SMOOBU_API_URL = "https://login.smoobu.com/api"
HEADERS = {"Api-Key": SMOOBU_API_KEY}
TELEGRAM_URL = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"

def get_all_bookings():
    response = requests.get(f"{SMOOBU_API_URL}/reservations", headers=HEADERS)
    return response.json().get("bookings", []) if response.status_code == 200 else []

def get_messages(booking_id):
    url = f"{SMOOBU_API_URL}/reservations/{booking_id}/messages?onlyRelatedToGuest=true"
    res = requests.get(url, headers=HEADERS)
    return res.json().get("messages", []) if res.status_code == 200 else []

def send_smoobu_reply(booking_id, message_text):
    url = f"{SMOOBU_API_URL}/reservations/{booking_id}/messages/send-message-to-guest"
    body = {
        "messageBody": message_text,
        "subject": "Risposta automatica"
    }
    res = requests.post(url, headers=HEADERS, json=body)
    return res.status_code == 200

def send_telegram_log(message):
    if TELEGRAM_CHAT_ID:
        requests.post(TELEGRAM_URL, json={"chat_id": TELEGRAM_CHAT_ID, "text": message})

def generate_reply_from_ai(message):
    # risposta finta per ora, sostituibile con OpenAI
    return "Grazie per il messaggio! Ti risponderemo al più presto."

def check_and_reply():
    bookings = get_all_bookings()
    for booking in bookings:
        booking_id = booking.get("id")
        messages = get_messages(booking_id)
        if not messages:
            continue

        latest = messages[-1]
        if latest["type"] != 1:
            continue  # ultimo messaggio NON è da parte dell’ospite

        if any(m["type"] == 2 and m["id"] > latest["id"] for m in messages):
            continue  # hai già risposto dopo quel messaggio

        reply_text = generate_reply_from_ai(latest["message"])
        sent = send_smoobu_reply(booking_id, reply_text)

        log = f"📩 Prenotazione #{booking_id} — risposta inviata: {sent}"
        print(log)
        send_telegram_log(log)

if __name__ == "__main__":
    check_and_reply()
