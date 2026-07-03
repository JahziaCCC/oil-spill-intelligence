import os
import json
import websocket

API_KEY = os.environ["AISSTREAM_API_KEY"]

def on_open(ws):
    print("Connected!")

    subscribe_message = {
        "APIKey": API_KEY,
        "BoundingBoxes": [
            [[12.0, 32.0], [30.0, 44.0]]  # البحر الأحمر
        ]
    }

    ws.send(json.dumps(subscribe_message))

def on_message(ws, message):
    data = json.loads(message)

    if "MetaData" in data:
        vessel = data["MetaData"].get("ShipName", "Unknown")
        mmsi = data["MetaData"].get("MMSI", "Unknown")

        print(f"Ship: {vessel} | MMSI: {mmsi}")

        ws.close()

def on_error(ws, error):
    print("ERROR:", error)

def on_close(ws, close_status_code, close_msg):
    print("Connection closed")

ws = websocket.WebSocketApp(
    "wss://stream.aisstream.io/v0/stream",
    on_open=on_open,
    on_message=on_message,
    on_error=on_error,
    on_close=on_close,
)

ws.run_forever()
