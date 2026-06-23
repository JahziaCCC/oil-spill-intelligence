import os
import requests
import datetime as dt

# =====================
# CONFIG
# =====================
TOKEN_URL = "https://identity.dataspace.copernicus.eu/auth/realms/CDSE/protocol/openid-connect/token"

# =====================
# AUTH (Copernicus)
# =====================
def get_access_token():
    payload = {
        "grant_type": "client_credentials",
        "client_id": os.environ["CDSE_CLIENT_ID"],
        "client_secret": os.environ["CDSE_CLIENT_SECRET"],
    }

    r = requests.post(TOKEN_URL, data=payload, timeout=60)

    print("TOKEN STATUS:", r.status_code)

    if r.status_code != 200:
        print(r.text)
        r.raise_for_status()

    return r.json()["access_token"]

# =====================
# TELEGRAM TEST
# =====================
def send_telegram(message):
    bot_token = os.environ["TELEGRAM_BOT_TOKEN"]
    chat_id = os.environ["TELEGRAM_CHAT_ID"]

    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"

    payload = {
        "chat_id": chat_id,
        "text": message
    }

    r = requests.post(url, json=payload, timeout=30)

    print("Telegram status:", r.status_code)
    print("Telegram response:", r.text)

# =====================
# MAIN
# =====================
def main():
    print("===== START =====")

    # 1) Test Token
    token = get_access_token()
    print("Token OK (length):", len(token))

    # 2) Test Telegram
    send_telegram("🟢 النظام شغال تمام - Copernicus + Telegram OK")

    print("===== DONE =====")


if __name__ == "__main__":
    main()
