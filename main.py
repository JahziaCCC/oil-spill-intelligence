import os
import requests
import datetime as dt
import numpy as np
from collections import defaultdict

# =====================
# CONFIG
# =====================
TOKEN_URL = "https://identity.dataspace.copernicus.eu/auth/realms/CDSE/protocol/openid-connect/token"
STAC_SEARCH_URL = "https://stac.dataspace.copernicus.eu/v1/search"

COLLECTION = "sentinel-1-grd"

REGIONS = [
    {"name_ar": "البحر الأحمر", "bbox": [32.0, 12.0, 44.5, 30.5]},
    {"name_ar": "الخليج العربي", "bbox": [47.0, 23.0, 56.8, 30.8]},
]

LOOKBACK_HOURS = 72
LIMIT_PER_REGION = 50

# =====================
# AUTH
# =====================
def get_access_token():
    payload = {
        "grant_type": "client_credentials",
        "client_id": os.environ["CDSE_CLIENT_ID"],
        "client_secret": os.environ["CDSE_CLIENT_SECRET"],
    }

    r = requests.post(TOKEN_URL, data=payload, timeout=60)

    if r.status_code != 200:
        print(r.text)
        r.raise_for_status()

    return r.json()["access_token"]

# =====================
# STAC SEARCH
# =====================
def stac_search(token, bbox, start_utc, end_utc):
    headers = {"Authorization": f"Bearer {token}"}

    body = {
        "collections": [COLLECTION],
        "bbox": bbox,
        "datetime": f"{start_utc}/{end_utc}",
        "limit": LIMIT_PER_REGION
    }

    r = requests.post(STAC_SEARCH_URL, headers=headers, json=body, timeout=120)
    r.raise_for_status()
    return r.json().get("features", [])

# =====================
# MAIN
# =====================
def main():
    now = dt.datetime.utcnow()
    start = now - dt.timedelta(hours=LOOKBACK_HOURS)

    start_utc = start.strftime("%Y-%m-%dT%H:%M:%SZ")
    end_utc = now.strftime("%Y-%m-%dT%H:%M:%SZ")

    token = get_access_token()

    print("Token OK")

    for region in REGIONS:
        feats = stac_search(token, region["bbox"], start_utc, end_utc)
        print(region["name_ar"], "=>", len(feats), "features")

if __name__ == "__main__":
    main()
