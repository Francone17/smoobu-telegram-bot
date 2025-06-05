from dateutil import parser
from utils.smoobu_api import get_messages, send_reply
from assistants.assistant import get_assistant_response
from utils.filters import is_sensitive
from utils.file_utils import load_json

ALLOWED_RESERVATION_IDS = [98806978]

def check_and_reply():

    reservations = load_json("current_reservations.json")
    if not reservations:
        print("⚠️ No reservations.")
        return

    for res in reservations:
        res_id = res.get("id")
        if res_id not in ALLOWED_RESERVATION_IDS:
            continue  # Ignora prenotazioni non monitorate

        messages = get_messages(res_id)
        if not messages:
            print(f"⚠️ No message for reservation {res_id}, skipping.")
            continue

        try:
            sorted_msgs = sorted(
                messages,
                key=lambda m: parser.parse(m["createdAt"]),
                reverse=True
            )
        except Exception as e:
            print(f"⚠️ Errore ordinamento messaggi prenotazione {res_id}: {e}")
            continue

        last_msg = sorted_msgs[0]
        msg_type = last_msg.get("type")

        if msg_type == 1:  # Incoming from guest
            print(f"📨 Ultimo messaggio DELL'ospite — prenotazione {res_id}")
            last_text = last_msg.get("message", "")
            guest_name = res.get("guestName", "ospite")

            if is_sensitive(last_text):
                print(f"⚠️ Messaggio sensibile da {guest_name}, escalation umana necessaria.")
                continue

            try:
                ai_reply = get_assistant_response(last_text, res)
                send_reply(res_id, ai_reply)
                print(f"✅ Risposta inviata a {guest_name}")
            except Exception as e:
                print(f"❌ Errore nella risposta automatica per {guest_name}: {e}")
        else:
            print(f"✅ Ultimo messaggio NON dell'ospite — prenotazione {res_id}")

