import time
import requests
from playwright.sync_api import sync_playwright

# ── Config ────────────────────────────────────────────────────────────────────
TELEGRAM_TOKEN  = "8916260072:AAEEs5xGln58_nBayos-dAEGJ9IO79elRsw"
TELEGRAM_CHAT_ID = "8973930274"
CHECK_URL       = "https://ghhostels.com/app/rooms"
CHECK_INTERVAL  = 120   # seconds between checks (2 minutes)
TARGET_KEYWORDS = ["new pent", "old pent"]  # case-insensitive
TARGET_ROOM_TYPE = "4 in"                   # matches "4 in a room", "4-in-1", etc.
# ─────────────────────────────────────────────────────────────────────────────


def send_telegram(message: str):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "Markdown",
    }
    try:
        r = requests.post(url, json=payload, timeout=10)
        r.raise_for_status()
        print("[Telegram] Alert sent.")
    except Exception as e:
        print(f"[Telegram] Failed to send: {e}")


def check_rooms():
    """Returns True if a matching room is found/available."""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0.0.0 Safari/537.36"
            )
        )
        page = context.new_page()
        try:
            page.goto(CHECK_URL, timeout=30000, wait_until="networkidle")
            # Give JS a moment to render
            page.wait_for_timeout(4000)
            content = page.content().lower()

            # Check for "booking closed" / "not available" signals
            closed_signals = [
                "booking closed",
                "not available",
                "no rooms",
                "portal closed",
                "coming soon",
                "sold out",
            ]
            for signal in closed_signals:
                if signal in content:
                    print(f"[Check] Closed signal found: '{signal}'")
                    browser.close()
                    return False

            # Check if target hostels + room type appear together
            has_target_hostel = any(kw in content for kw in TARGET_KEYWORDS)
            has_room_type     = TARGET_ROOM_TYPE in content

            if has_target_hostel and has_room_type:
                print("[Check] ✅ Match found!")
                browser.close()
                return True

            print(f"[Check] No match yet. hostel={has_target_hostel} room_type={has_room_type}")
            browser.close()
            return False

        except Exception as e:
            print(f"[Check] Error loading page: {e}")
            browser.close()
            return False


def main():
    print("🟢 GH Hostels monitor started.")
    send_telegram(
        "🟢 *GH Hostels Monitor Started*\n\n"
        "I'm now watching for 4-in-a-room availability at New Pent / Old Pent.\n"
        "You'll get an alert the moment a room opens. Stay ready! 🏃"
    )

    alert_sent = False

    while True:
        print(f"\n[{time.strftime('%Y-%m-%d %H:%M:%S')}] Checking...")
        found = check_rooms()

        if found and not alert_sent:
            send_telegram(
                "🚨 *ROOM AVAILABLE!*\n\n"
                "A *4-in-a-room* at *New Pent / Old Pent* is now open for booking!\n\n"
                f"👉 Book NOW: {CHECK_URL}\n\n"
                f"⏰ Detected at: {time.strftime('%I:%M %p, %d %b %Y')}\n\n"
                "_Don't wait — these go fast!_"
            )
            alert_sent = True
            # Keep checking so we can alert again if portal closes and reopens
        elif not found and alert_sent:
            # Reset so we alert again if rooms reopen
            alert_sent = False

        time.sleep(CHECK_INTERVAL)


if __name__ == "__main__":
    main()
