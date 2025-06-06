import os
import requests
from dotenv import load_dotenv

load_dotenv()

SMOOBU_API_KEY = os.getenv("SMOOBU_API_KEY")

HEADERS = {"API-Key": SMOOBU_API_KEY}
BASE_URL = "https://login.smoobu.com/api"

def get_reservations(params: dict):
    response = requests.get(
        f"{BASE_URL}/reservations",
        headers=HEADERS,
        params=params
    )
    response.raise_for_status()
    data = response.json().get('bookings', {})
    return data


def get_messages(reservation_id, params):
    try:
        response = requests.get(
            f"{BASE_URL}/reservations/{reservation_id}/messages",
            headers=HEADERS,
            params=params
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
