import requests

def get_weather(lat, lon):

    url = (
        "https://api.open-meteo.com/v1/forecast"
        f"?latitude={lat}"
        f"&longitude={lon}"
        "&current=wind_speed_10m,wind_direction_10m"
    )

    r = requests.get(url, timeout=20)
    r.raise_for_status()

    current = r.json()["current"]

    return {
        "speed": current["wind_speed_10m"],
        "direction": current["wind_direction_10m"]
    }
