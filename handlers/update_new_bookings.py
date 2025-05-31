import requests
from datetime import datetime, timedelta

from utils.file_utils import load_json, save_json
from utils.smoobu_api import get_reservations

def update_new_bookings():
    now = datetime.utcnow()
    created_from = (now - timedelta(minutes=15)).strftime("%Y-%m-%dT%H:%M:%S")
    created_to = now.strftime("%Y-%m-%dT%H:%M:%S")

    existing = load_json("data/current_reservations.json") or []
    existing_ids = {r["id"] for r in existing}

    all_new = []
    page = 1

    while True:
        try:
            params = {
                "createdFrom": created_from,
                "createdTo": created_to,
                "page": page,
                "pageSize": 100
            }
            fetched = get_reservations(params, page=page)
            if not fetched:
                break

            new = [r for r in fetched if r["id"] not in existing_ids]
            all_new.extend(new)
            existing_ids.update(r["id"] for r in new)

            page += 1

        except requests.exceptions.HTTPError as e:
            print(f"[ERROR] HTTP error on page {page}: {e}")
            break
        except Exception as e:
            print(f"[ERROR] Unexpected error on page {page}: {e}")
            break

    if all_new:
        print(f"[INFO] Found {len(all_new)} new reservations.")
        combined = existing + all_new
        save_json("current_reservations.json", combined)
    else:
        print("[INFO] No new reservations found.")
