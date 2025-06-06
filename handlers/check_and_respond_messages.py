import requests
from dateutil import parser
from utils.smoobu_api import get_messages, send_reply
from assistants.assistant import get_assistant_response
from utils.filters import is_sensitive
from utils.file_utils import load_json

ALLOWED_RESERVATION_IDS = [98835313]

def check_and_reply():

    reservations = load_json("current_reservations.json")
    if not reservations:
        print("⚠️ No reservations.")
        return

    for res in reservations:
        res_id = res.get("id")
        if res_id not in ALLOWED_RESERVATION_IDS:
            continue  # Ignora prenotazioni non monitorate

        page = 1
        messages = []
        while True:
            try:
                params = {
                    "page": page,
                    "pageSize": 100
                }
                fetched_messages = get_messages(res_id, params)
                if not fetched_messages:
                    break
                messages.extend(fetched_messages)
                page += 1
            except requests.exceptions.HTTPError as e:
                print(f"[ERROR] HTTP error on page {page}: {e}")
                break
            except Exception as e:
                print(f"[ERROR] Unexpected error on page {page}: {e}")
                break
        if not messages:
            print(f"⚠️ No message for reservation {res_id}, skipping.")
            continue



        last_msg = messages[-1]
        msg_type = last_msg.get("type")

        if msg_type == 1:  # Incoming from guest
            print(f"📨 Ultimo messaggio DELL'ospite — prenotazione {res_id}")
            last_text = last_msg.get("message", "")
            guest_name = res.get("guestName", "ospite")
            apt_object = res.get("apartment") or {}
            apt_name = apt_object.get("name", "Appartamento sconosciuto")

            if is_sensitive(last_text):
                print(f"⚠️ Messaggio sensibile da {guest_name}, escalation umana necessaria.")
                continue

            try:
                ai_reply = get_assistant_response(last_text, res, apt_name)
                send_reply(res_id, ai_reply)
                print(f"✅ Risposta inviata a {guest_name}")
            except Exception as e:
                print(f"❌ Errore nella risposta automatica per {guest_name}: {e}")
        else:
            print(f"✅ Ultimo messaggio NON dell'ospite — prenotazione {res_id}")

