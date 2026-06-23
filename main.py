import os
import requests

TOKEN_URL = (
    "https://identity.dataspace.copernicus.eu/"
    "auth/realms/CDSE/protocol/openid-connect/token"
)

print("===== ENV CHECK =====")

client_id = os.environ.get("CDSE_CLIENT_ID")
client_secret = os.environ.get("CDSE_CLIENT_SECRET")

print("CDSE_CLIENT_ID exists:", client_id is not None)
print("CDSE_CLIENT_SECRET exists:", client_secret is not None)

if client_id:
    print("Client ID:", client_id)

if client_secret:
    print("Client Secret length:", len(client_secret))

print("\n===== TOKEN REQUEST =====")

try:
    r = requests.post(
        TOKEN_URL,
        data={
            "grant_type": "client_credentials",
            "client_id": client_id,
            "client_secret": client_secret,
        },
        timeout=30,
    )

    print("HTTP Status:", r.status_code)
    print("\nResponse:")
    print(r.text)

    if r.status_code == 200:
        token = r.json()["access_token"]
        print("\nSUCCESS")
        print("Token length:", len(token))
    else:
        print("\nAUTH FAILED")

except Exception as e:
    print("\nEXCEPTION:")
    print(str(e))
    raise
