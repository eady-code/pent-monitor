import time
import requests
from bs4 import BeautifulSoup

# ── Config ────────────────────────────────────────────────────────────────────
TELEGRAM_TOKEN   = "8916260072:AAEEs5xGln58_nBayos-dAEGJ9IO79elRsw"
TELEGRAM_CHAT_ID = "8973930274"
CHECK_URL        = "https://ghhostels.com/app/rooms"
CHECK_INTERVAL   = 120  # seconds
TARGET_HOSTELS   = ["new pent", "old pent"]
TARGET_ROOM_TYPE = "4 in"
# ─────────────────────────────────────────────────────────────────────────────

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
}

def send_telegram(message: str):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    try:
        r = requests.post(url, json={
            "chat_id": TELEGRAM_CHAT_ID,
            "text": message,
            "parse_mode": "Markdown"
        }, timeout=10)
        r.raise_for_status()
        print("[Telegram] Alert sent.")
    except Exception as e:
        print(f"[Telegram] Failed: {e}")


def check_rooms():
    try:
        r = requests.get(CHECK_URL, headers=HEADERS, timeout=15)
        content = r.text.lower()

        closed_signals = [
            "booking closed", "not available", "no rooms",
            "portal closed", "coming soon", "sold out", "closed"
        ]
        for signal in closed_signals:
            if signal in content:
                print(f"[Check] Closed signal: '{signal}'")
                return False

        has_hostel    = any(kw in content for kw in TARGET_HOSTELS)
        has_room_type = TARGET_ROOM_TYPE in content

        print(f"[Check] hostel={has_hostel} room_type={has_room_type}")
        return has_hostel and has_room_type

    except Exception as e:
        print(f"[Check] Error: {e}")
        return False


def main():
    print("GH Hostels monitor started.")
    send_telegram(
        "🟢 *GH Hostels Monitor Started*\n\n"
        "Watching for 4-in-a-room at New Pent / Old Pent.\n"
        "You'll get an alert the moment rooms open. Stay ready! 🏃"
    )

    alert_sent = False

    while True:
        print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Checking...")
        found = check_rooms()

        if found and not alert_sent:
            send_telegram(
                "🚨 *ROOM AVAILABLE!*\n\n"
                "A *4-in-a-room* at *New Pent / Old Pent* is now open!\n\n"
                f"👉 Book NOW: {CHECK_URL}\n\n"
                f"⏰ {time.strftime('%I:%M %p, %d %b %Y')}\n\n"
                "_Don't wait — these go fast!_"
            )
            alert_sent = True
        elif not found and alert_sent:
            alert_sent = False

        time.sleep(CHECK_INTERVAL)


if __name__ == "__main__":
    main()
