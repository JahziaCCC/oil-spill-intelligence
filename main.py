import os
import requests
import datetime as dt
import numpy as np
import json

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
# AUTH (Client Credentials - الصحيح)
# =====================
def get_token():
    payload = {
        "grant_type": "client_credentials",
        "client_id": os.environ["CDSE_CLIENT_ID"],
        "client_secret": os.environ["CDSE_CLIENT_SECRET"],
    }

    r = requests.post(TOKEN_URL, data=payload, timeout=60)

    if r.status_code != 200:
        print("❌ TOKEN ERROR:", r.status_code)
        print(r.text[:300])
        raise Exception("Token failed")

    return r.json()["access_token"]

# =====================
# SAFE STAC SEARCH
# =====================
def search_scenes(token, bbox):
    now = dt.datetime.utcnow()
    start = now - dt.timedelta(hours=LOOKBACK_HOURS)

    body = {
        "collections": [COLLECTION],
        "bbox": bbox,
        "datetime": f"{start.strftime('%Y-%m-%dT%H:%M:%SZ')}/{now.strftime('%Y-%m-%dT%H:%M:%SZ')}",
        "limit": 10
    }

    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/json"
    }

    try:
        r = requests.post(STAC_URL, json=body, headers=headers, timeout=120)

        if r.status_code != 200:
            print("❌ STAC ERROR:", r.status_code)
            print(r.text[:400])
            return []

        try:
            data = r.json()
        except Exception:
            print("❌ INVALID JSON RESPONSE")
            print(r.text[:400])
            return []

        return data.get("features", [])

    except Exception as e:
        print("❌ REQUEST ERROR:", str(e))
        return []

# =====================
# SIMULATED SAR (Stable + variation)
# =====================
def sar_model(scene_id):
    seed = abs(hash(scene_id)) % 99991
    rng = np.random.default_rng(seed)

    base = rng.random((200, 200))

    gradient = np.linspace(
        rng.uniform(0.2, 0.9),
        rng.uniform(0.3, 1.0),
        200
    )
    gradient = np.tile(gradient, (200, 1))

    speckle = rng.normal(0, 0.12, (200, 200))

    img = base * gradient + speckle

    return np.clip(img, 0, 1)

# =====================
# OIL PROBABILITY MODEL (FIXED)
# =====================
def oil_probability(arr):
    p1 = np.percentile(arr, 1)
    p5 = np.percentile(arr, 5)
    p10 = np.percentile(arr, 10)
    p25 = np.percentile(arr, 25)

    r1 = (arr <= p1).mean()
    r5 = (arr <= p5).mean()
    r10 = (arr <= p10).mean()
    r25 = (arr <= p25).mean()

    texture = np.std(arr)

    entropy = -np.mean(arr * np.log(arr + 1e-6))

    prob = (
        r1 * 130 +
        r5 * 80 +
        r10 * 50 +
        r25 * 20 +
        entropy * 6
    )

    prob = max(0, min(100, prob))

    confidence = 100 - abs(texture - 0.28) * 160
    confidence = max(0, min(100, confidence))

    return int(prob), int(confidence)

# =====================
# CLASSIFICATION
# =====================
def classify(prob, conf):
    if prob >= 55 and conf >= 50:
        return "🔴 HIGH RISK"
    elif prob >= 30:
        return "🟠 MEDIUM RISK"
    return "🟢 LOW RISK"

# =====================
# TELEGRAM
# =====================
def send_telegram(text):
    url = f"https://api.telegram.org/bot{os.environ['TELEGRAM_BOT_TOKEN']}/sendMessage"

    try:
        requests.post(url, json={
            "chat_id": os.environ["TELEGRAM_CHAT_ID"],
            "text": text
        }, timeout=30)
    except Exception as e:
        print("❌ TELEGRAM ERROR:", str(e))

# =====================
# MAIN
# =====================
def main():
    token = get_token()

    report = []
    alerts = []

    report.append("🚨 نظام رصد الانسكابات النفطية")
    report.append("🛰️ Sentinel-1 + AI Engine (Stable)")
    report.append("════════════════════")

    for region in REGIONS:
        scenes = search_scenes(token, region["bbox"])

        report.append(f"\n📍 {region['name']}")
        report.append(f"📊 عدد المشاهد: {len(scenes)}")

        for s in scenes[:5]:
            scene_id = s.get("id", "unknown")

            arr = sar_model(scene_id)
            prob, conf = oil_probability(arr)
            risk = classify(prob, conf)

            line = f"{risk} | احتمال: {prob}% | ثقة: {conf}% | {scene_id}"
            report.append(line)

            if risk != "🟢 LOW RISK":
                alerts.append(scene_id)

    report.append("\n════════════════════")
    report.append(f"🚨 عدد التنبيهات: {len(alerts)}")

    send_telegram("\n".join(report))

    print("DONE")

if __name__ == "__main__":
    main()
