import schedule
import time

from cron.message_cron import check_and_reply
from cron.update_new import update_new_bookings
from cron.update_daily import get_all_reservations

# Run once at startup
print("🚀 Running initial full reservation sync...")
get_all_reservations()

# Schedule recurring jobs
schedule.every(1).minutes.do(check_and_reply)
schedule.every(15).minutes.do(update_new_bookings)
schedule.every().day.at("03:00").do(get_all_reservations)

while True:
    schedule.run_pending()
    time.sleep(30)
