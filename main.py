import os
import requests

TOKEN_URL = "https://identity.dataspace.copernicus.eu/auth/realms/CDSE/protocol/openid-connect/token"

client_id = os.environ["CDSE_CLIENT_ID"]
client_secret = os.environ["CDSE_CLIENT_SECRET"]

r = requests.post(
    TOKEN_URL,
    data={
        "grant_type": "client_credentials",
        "client_id": client_id,
        "client_secret": client_secret,
    },
    timeout=30,
)

r.raise_for_status()

token = r.json()["access_token"]

print("SUCCESS")
print("Token length:", len(token))
