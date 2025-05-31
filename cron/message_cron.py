from datetime import datetime
from handlers. check_and_respond_messages import check_and_reply

if __name__ == "__main__":
    check_and_reply()
    print(f"✅ Check and respond to messages completed at {datetime.now().strftime('%m-%d-%M')}.")