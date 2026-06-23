import os
import requests
import datetime as dt
import numpy as np

# =====================
# CONFIG
# =====================
TOKEN_URL = "https://identity.dataspace.copernicus.eu/auth/realms/CDSE/protocol/openid-connect/token"
STAC_URL = "https://stac.dataspace.copernicus.eu/v1/search"

COLLECTION = "sentinel-1-grd"

REGIONS = [
    {"name": "Red Sea", "bbox": [32.0, 12.0, 44.5, 30.5]},
    {"name": "Arabian Gulf", "bbox": [47.0, 23.0, 56.8, 30.8]},
]

LOOKBACK_HOURS = 72

# =====================
# AUTH
# =====================
def get_token():
    payload = {
        "grant_type": "client_credentials",
        "client_id": os.environ["CDSE_CLIENT_ID"],
        "client_secret": os.environ["CDSE_CLIENT_SECRET"],
    }

    r = requests.post(TOKEN_URL, data=payload, timeout=60)
    r.raise_for_status()

    return r.json()["access_token"]

# =====================
# STAC SEARCH
# =====================
def search_s1(token, bbox):
    now = dt.datetime.utcnow()
    start = now - dt.timedelta(hours=LOOKBACK_HOURS)

    body = {
        "collections": [COLLECTION],
        "bbox": bbox,
        "datetime": f"{start.strftime('%Y-%m-%dT%H:%M:%SZ')}/{now.strftime('%Y-%m-%dT%H:%M:%SZ')}",
        "limit": 10
    }

    headers = {"Authorization": f"Bearer {token}"}

    r = requests.post(STAC_URL, json=body, headers=headers, timeout=120)
    r.raise_for_status()

    return r.json().get("features", [])

# =====================
# SIMPLE OIL DETECTION (Prototype AI)
# =====================
def fake_image(scene_id):
    np.random.seed(abs(hash(scene_id)) % 10000)
    return np.random.randint(0, 255, (300, 300)).astype(np.uint8)

def detect_oil(img):
    threshold = np.percentile(img, 8)
    mask = img <= threshold

    dark_ratio = mask.sum() / mask.size
    score = int(dark_ratio * 100)

    if score > 12:
        risk = "🔴 HIGH"
    elif score > 7:
        risk = "🟠 MEDIUM"
    else:
        risk = "🟢 LOW"

    return risk, score

# =====================
# TELEGRAM
# =====================
def send_telegram(msg):
    url = f"https://api.telegram.org/bot{os.environ['TELEGRAM_BOT_TOKEN']}/sendMessage"

    payload = {
        "chat_id": os.environ["TELEGRAM_CHAT_ID"],
        "text": msg
    }

    requests.post(url, json=payload, timeout=30)

# =====================
# MAIN
# =====================
def main():
    print("===== START SYSTEM =====")

    token = get_token()
    print("Token OK")

    report = []
    alert_count = 0

    for region in REGIONS:
        feats = search_s1(token, region["bbox"])

        report.append(f"\n📍 {region['name']} => {len(feats)} scenes")

        for f in feats[:5]:
            scene_id = f.get("id")

            img = fake_image(scene_id)
            risk, score = detect_oil(img)

            line = f"{risk} | {scene_id} | score={score}"
            print(line)
            report.append(line)

            if "HIGH" in risk:
                alert_count += 1

    report.append("\n====================")
    report.append(f"🚨 High Risk Alerts: {alert_count}")

    send_telegram("\n".join(report))

    print("Telegram sent")

# =====================
if __name__ == "__main__":
    main()
