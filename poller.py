import os
import requests
from dotenv import load_dotenv
from datetime import datetime
from dateutil import parser
import openai

load_dotenv()

SMOOBU_API_KEY = os.getenv("SMOOBU_API_KEY")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
SMOOBU_API_URL = "https://login.smoobu.com/api"
TELEGRAM_URL = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"

# Appartamenti con garage convenzionato
PARKING_APTS = {
    "B1 Suite 1", "B2 Suite 2", "B3 Suite 3", "B4 Casa dell'Alfiere",
    "B5 Casa Solferino", "B6 Carlina", "B7 San Carlo",
    "C1 De Lellis 1", "C2 De Lellis 2", "C3 De Lellis 3", "C4 De Lellis 4",
    "D Mercanti"
}

def send_telegram_message(text):
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": text,
    }
    requests.post(TELEGRAM_URL, json=payload)

def get_all_reservations():
    url = f"{SMOOBU_API_URL}/bookings"
    headers = {"Api-Key": SMOOBU_API_KEY}
    response = requests.get(url, headers=headers)

    try:
        data = response.json()
        return data.get("bookings", [])
    except Exception as e:
        print("❌ Errore nel parsing JSON della risposta Smoobu:")
        print("Status Code:", response.status_code)
        print("Contenuto grezzo:", response.text[:500])
        raise e

def get_messages(reservation_id):
    url = f"{SMOOBU_API_URL}/reservations/{reservation_id}/messages"
    headers = {"Api-Key": SMOOBU_API_KEY}
    params = {"onlyRelatedToGuest": "true"}
    res = requests.get(url, headers=headers, params=params)

    try:
        return res.json().get("messages", [])
    except Exception as e:
        print(f"❌ Errore parsing messaggi prenotazione {reservation_id}")
        print("Contenuto:", res.text[:500])
        return []

def send_message(reservation_id, text):
    url = f"{SMOOBU_API_URL}/reservations/{reservation_id}/messages/send-message-to-guest"
    headers = {
        "Api-Key": SMOOBU_API_KEY,
        "Content-Type": "application/json"
    }
    payload = {
        "subject": "Risposta automatica",
        "messageBody": text
    }
    response = requests.post(url, headers=headers, json=payload)
    return response.status_code == 200

def is_guest_last_sender(messages):
    sorted_msgs = sorted(
        [m for m in messages if m.get("createdAt")],
        key=lambda m: parser.parse(m["createdAt"]),
        reverse=True
    )
    if not sorted_msgs:
        return False
    return sorted_msgs[0]["type"] == 1

def detect_language(text):
    try:
        if any(ord(c) > 127 for c in text):
            return "en"
        return "it"
    except:
        return "it"

def build_response(text, apt_name, lang):
    if apt_name in PARKING_APTS and "parcheggio" in text.lower() or "parking" in text.lower():
        if lang == "it":
            return (
                "Per quanto riguarda il parcheggio, ci appoggiamo a un'autorimessa convenzionata "
                "che si trova a 3 a piedi minuti dall'appartamento. Si chiama Garage AUTOPALAZZO in Via Bertola 7. "
                "All'arrivo, comunicando che siete ospiti presso Top Living Apartments, otterrete una tariffa ridotta di 32€ al giorno."
            )
        else:
            return (
                "For what concerns parking, you can use a partner garage located 3 minutes away from the apartment. "
                "The place is called Garage AUTOPALAZZO (https://www.garageautopalazzo.it/?page_id=475), in Via Bertola 7. "
                "When you arrive at the garage, tell the personnel you are guests at Top Living Apartments and you'll pay a reduced tariff of 32€ per day."
            )
    elif OPENAI_API_KEY:
        try:
            openai.api_key = OPENAI_API_KEY
            prompt = f"Rispondi con tono cordiale, gentile e professionale (non troppo formale) al seguente messaggio: \"{text}\""
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            print(f"❌ Errore OpenAI: {e}")
            return "Grazie per il messaggio! Ti risponderemo al più presto."
    else:
        return "Grazie per il messaggio! Ti risponderemo al più presto."

def check_and_reply():
    print("🔄 Controllo nuove conversazioni...")
    reservations = get_all_reservations()
    for res in reservations:
        res_id = res["id"]
        apt_name = res.get("apartment", {}).get("name", "")
        messages = get_messages(res_id)
        if not messages:
            continue
        if not is_guest_last_sender(messages):
            print(f"✅ Ultimo messaggio NON dell'ospite — prenotazione {res_id}")
            continue
        guest_msg = sorted(messages, key=lambda m: parser.parse(m["createdAt"]), reverse=True)[0]["message"]
        lang = detect_language(guest_msg)
        reply = build_response(guest_msg, apt_name, lang)
        success = send_message(res_id, reply)
        print(f"🤖 Risposta AI inviata per prenotazione #{res_id} — Successo: {success}\nMessaggio: {reply}")

if __name__ == "__main__":
    check_and_reply()
