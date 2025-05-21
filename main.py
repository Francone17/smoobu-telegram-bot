from flask import Flask, request
import os
import requests
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

SMOOBU_API_KEY = os.getenv("SMOOBU_API_KEY")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
SMOOBU_API_URL = "https://login.smoobu.com/api"
TELEGRAM_URL = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/"

def send_telegram_message(chat_id, text):
    requests.post(TELEGRAM_URL + "sendMessage", json={
        "chat_id": chat_id,
        "text": text
    })

def get_latest_booking():
    headers = {"Api-Key": SMOOBU_API_KEY}
    response = requests.get(f"{SMOOBU_API_URL}/reservations", headers=headers)
    if response.status_code != 200:
        return "Errore nel recupero delle prenotazioni"
    data = response.json().get("bookings", [])
    if not data:
        return "Nessuna prenotazione trovata."
    latest = data[0]
    return f"Ultima prenotazione: {latest.get('guest-name')} — arrivo: {latest.get('arrival')}"

@app.route("/", methods=["POST"])
def webhook():
    data = request.get_json()
    chat_id = data.get("message", {}).get("chat", {}).get("id")
    text = data.get("message", {}).get("text", "").strip().lower()
    if text == "prenotazioni":
        reply = get_latest_booking()
    else:
        reply = "Scrivi 'prenotazioni' per vedere l'ultima prenotazione."
    send_telegram_message(chat_id, reply)
    return "ok"

# 🔥 Necessario per gunicorn
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
