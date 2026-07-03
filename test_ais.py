import os
import json
import asyncio
import websockets

API_KEY = os.environ["AISSTREAM_API_KEY"]

BOUNDING_BOXES = [
    [[12.0, 32.0], [30.0, 44.0]],  # البحر الأحمر
    [[24.0, 47.0], [31.0, 57.0]]   # الخليج العربي
]

async def main():

    async with websockets.connect(
        "wss://stream.aisstream.io/v0/stream"
    ) as ws:

        subscribe = {
            "APIKey": API_KEY,
            "BoundingBoxes": BOUNDING_BOXES
        }

        await ws.send(json.dumps(subscribe))

        print("✅ Connected to AISStream")
        print("Waiting for first message...\n")

        while True:
            try:
                msg = await asyncio.wait_for(ws.recv(), timeout=30)

                print("=" * 80)
                print("FIRST MESSAGE RECEIVED:")
                print("=" * 80)
                print(msg)
                print("=" * 80)

                break

            except asyncio.TimeoutError:
                print("❌ No message received within 30 seconds.")
                break

asyncio.run(main())
