from datetime import timedelta, datetime
import requests

from utils.file_utils import save_json
from utils.smoobu_api import get_reservations

ALLOWED_RESERVATION_IDS = [98806978]  # Not actively used, but kept for filtering if needed

def get_all_reservations():
    today = datetime.utcnow()
    ten_days_ago = (today - timedelta(days=10)).strftime('%Y-%m-%d')
    twenty_days_ahead = (today + timedelta(days=20)).strftime('%Y-%m-%d')

    all_reservations = []
    page = 1

    while True:
        try:
            params = {
                "arrivalFrom": ten_days_ago,
                "arrivalTo": twenty_days_ahead,
                "page": page,
                "pageSize": 100
            }
            data = get_reservations(params)
            if not data:
                break

            all_reservations.extend(data)
            page += 1

        except requests.exceptions.HTTPError as e:
            print(f"[ERROR] HTTP error on page {page}: {e}")
            break
        except Exception as e:
            print(f"[ERROR] Unexpected error on page {page}: {e}")
            break

    save_json("current_reservations.json", all_reservations)
    print(f"[INFO] Saved {len(all_reservations)} reservations to current_reservations.json")
