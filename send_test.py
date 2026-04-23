import asyncio
import json
import websockets


async def send_string(uri, text):
    async with websockets.connect(uri) as websocket:
        await websocket.send(json.dumps({"text": text}))
        print(f"Sent: {text}")


asyncio.run(send_string("ws://192.168.1.129:5765", "Hello, StringShare!"))
