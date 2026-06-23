import os
import requests
import datetime as dt

TOKEN_URL = "https://identity.dataspace.copernicus.eu/auth/realms/CDSE/protocol/openid-connect/token"
STAC_URL = "https://stac.dataspace.copernicus.eu/v1/search"

COLLECTION = "sentinel-1-grd"

REGIONS = [
    {"name": "Red Sea", "bbox": [32.0, 12.0, 44.5, 30.5]},
    {"name": "Arabian Gulf", "bbox": [47.0, 23.0, 56.8, 30.8]},
]

def get_token():
    payload = {
        "grant_type": "client_credentials",
        "client_id": os.environ["CDSE_CLIENT_ID"],
        "client_secret": os.environ["CDSE_CLIENT_SECRET"],
    }

    r = requests.post(TOKEN_URL, data=payload)
    return r.json()["access_token"]

def search_s1(token, bbox):
    now = dt.datetime.utcnow()
    start = now - dt.timedelta(hours=72)

    body = {
        "collections": [COLLECTION],
        "bbox": bbox,
        "datetime": f"{start.strftime('%Y-%m-%dT%H:%M:%SZ')}/{now.strftime('%Y-%m-%dT%H:%M:%SZ')}",
        "limit": 10
    }

    headers = {"Authorization": f"Bearer {token}"}

    r = requests.post(STAC_URL, json=body, headers=headers)

    return r.json().get("features", [])

def main():
    token = get_token()

    for region in REGIONS:
        feats = search_s1(token, region["bbox"])
        print(region["name"], "=>", len(feats), "scenes")

if __name__ == "__main__":
    main()
