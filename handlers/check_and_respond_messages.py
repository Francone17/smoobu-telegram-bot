from datetime import datetime

import requests
from dateutil import parser
from utils.smoobu_api import get_messages, send_reply
from assistants.assistant import get_assistant_response
from utils.filters import is_sensitive
from utils.file_utils import load_json
from utils.flags import (
    is_test_mode_enabled,
    get_allowed_reservation_ids,
    get_blocked_reservation_ids,
    get_human_resolved_complaint_ids
)

def check_and_reply():
    reservations = load_json("current_reservations.json")
    if not reservations:
        print("⚠️ No reservations.")
        return

    test_mode = is_test_mode_enabled()
    allowed_ids = get_allowed_reservation_ids()
    blocked_ids = get_blocked_reservation_ids()
    human_resolved_complaint_ids = get_human_resolved_complaint_ids()

    for res in reservations:
        res_id = res.get("id")

        if res_id in blocked_ids:
            print(f"⛔ Reservation {res_id} is blocked by feature flag.")
            continue

        if test_mode and res_id not in allowed_ids:
            print(f"⛔ Reservation {res_id} not in test-mode allowlist.")
            continue

        page = 1
        messages = []
        while True:
            try:
                params = {"page": page, "pageSize": 100}
                fetched = get_messages(res_id, params)
                if not fetched:
                    break
                messages.extend(fetched)
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

        sorted_messages = sorted(
            messages,
            key=lambda m: datetime.strptime(m["createdAt"], "%Y-%m-%d %H:%M:%S"),
            reverse=True
        )

        last_msg = sorted_messages[0]
        if last_msg.get("type") == 1:
            print(f"📨 Ultimo messaggio DELL'ospite — prenotazione {res_id}")
            last_text = last_msg.get("message", "")
            guest_name = res.get("guestName", "ospite")
            apt_name = (res.get("apartment") or {}).get("name", "Appartamento sconosciuto")
            print(last_text)

            if is_sensitive(last_text) and res_id not in human_resolved_complaint_ids :
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
