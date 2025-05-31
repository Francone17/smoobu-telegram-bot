from datetime import datetime

from handlers.update_new_bookings import update_new_bookings

if __name__ == "__main__":
    update_new_bookings()
    print(f"✅ Daily update of reservations completed {datetime.now().strftime('%m-%d-%M')}.")