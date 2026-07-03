import os
import json
import asyncio
import websockets

API_KEY = os.environ["AISSTREAM_API_KEY"]

# البحر الأحمر + الخليج العربي
BOUNDING_BOXES = [
    [[12.0, 32.0], [30.0, 44.0]],
    [[24.0, 47.0], [31.0, 57.0]]
]

async def main():

    vessels = {}

    async with websockets.connect(
        "wss://stream.aisstream.io/v0/stream"
    ) as ws:

        subscribe = {
            "APIKey": API_KEY,
            "BoundingBoxes": BOUNDING_BOXES,
            "FilterMessageTypes": ["PositionReport"]
        }

        await ws.send(json.dumps(subscribe))

        print("✅ Connected to AISStream")
        print("Receiving data for 20 seconds...\n")

        end_time = asyncio.get_event_loop().time() + 20

        while asyncio.get_event_loop().time() < end_time:

            try:
                msg = await asyncio.wait_for(ws.recv(), timeout=5)

                data = json.loads(msg)

                meta = data.get("MetaData", {})

                mmsi = meta.get("MMSI")

                if not mmsi:
                    continue

                vessels[mmsi] = {
                    "name": meta.get("ShipName", "Unknown"),
                    "lat": meta.get("latitude"),
                    "lon": meta.get("longitude")
                }

            except asyncio.TimeoutError:
                pass

    print("=" * 50)
    print("Total vessels:", len(vessels))
    print("=" * 50)

    for ship in list(vessels.values())[:10]:
        print(ship)

asyncio.run(main())
