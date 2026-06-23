import os
import requests
import datetime as dt
import numpy as np
from PIL import Image
from io import BytesIO

# =====================
# CONFIG
# =====================
TOKEN_URL = "https://identity.dataspace.copernicus.eu/auth/realms/CDSE/protocol/openid-connect/token"
STAC_URL = "https://stac.dataspace.copernicus.eu/v1/search"

COLLECTION = "sentinel-1-grd"

REGIONS = [
    {"name": "البحر الأحمر", "bbox": [32.0, 12.0, 44.5, 30.5]},
    {"name": "الخليج العربي", "bbox": [47.0, 23.0, 56.8, 30.8]},
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
# LOAD SAR IMAGE (REAL QUICKLOOK)
# =====================
def load_sar_image(feature):
    assets = feature.get("assets", {})

    for key in ["quicklook", "preview", "thumbnail"]:
        if key in assets:
            url = assets[key].get("href")
            if url:
                r = requests.get(url, timeout=60)
                img = Image.open(BytesIO(r.content)).convert("L")
                return np.array(img)

    return None

# =====================
# AI DETECTION
# =====================
def detect_oil(img):
    dark_threshold = np.percentile(img, 10)
    mask = img <= dark_threshold

    dark_ratio = mask.mean()
    std = np.std(img)

    score = int((dark_ratio * 120) - (std * 0.1))
    score = max(0, min(100, score))

    if score >= 25:
        risk = "🔴 HIGH"
    elif score >= 15:
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
    high_alerts = 0

    # Header عربي
    report.append("🚨 نظام رصد الانسكابات النفطية")
    report.append("🛰️ بيانات Sentinel-1 + تحليل ذكي")
    report.append("════════════════════")

    for region in REGIONS:
        feats = search_s1(token, region["bbox"])

        report.append(f"\n📍 المنطقة: {region['name']}")
        report.append(f"📊 عدد المشاهد: {len(feats)}")

        for f in feats[:5]:
            scene_id = f.get("id")

            img = load_sar_image(f)
            if img is None:
                continue

            risk, score = detect_oil(img)

            # ترجمة الحالة
            if risk == "🔴 HIGH":
                risk_ar = "🔴 خطر مرتفع (احتمال تسرب)"
            elif risk == "🟠 MEDIUM":
                risk_ar = "🟠 متوسط (يحتاج متابعة)"
            else:
                risk_ar = "🟢 منخفض (طبيعي)"

            line = f"{risk_ar} | الدقة: {score}% | {scene_id}"
            print(line)
            report.append(line)

            if risk == "🔴 HIGH":
                high_alerts += 1

    report.append("\n════════════════════")

    if high_alerts == 0:
        report.append("🟢 لا توجد مؤشرات خطيرة حالياً")
    else:
        report.append(f"🚨 عدد الإنذارات العالية: {high_alerts}")

    send_telegram("\n".join(report))

    print("Telegram sent")

# =====================
if __name__ == "__main__":
    main()
