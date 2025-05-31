from datetime import datetime

from handlers.update_reservations import get_all_reservations

if __name__ == "__main__":
    get_all_reservations()
    print(f"✅ Daily update of reservations completed {datetime.now().strftime('%m-%d-%M')}")