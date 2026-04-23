import platform
import socket
import threading
import time
import os
import pyperclip
import websockets
import asyncio
import json
from websockets.exceptions import ConnectionClosed
from plyer import notification
from zeroconf import ServiceBrowser, ServiceInfo, Zeroconf, ServiceListener
from dotenv import load_dotenv

load_dotenv()
PORT = os.getenv("PORT")
print(type(PORT), PORT)
SERVICE = "_stringshare._tcp.local."
HOSTNAME = socket.gethostname()
OS = platform.system()


class StringShareListerer(ServiceListener):
    def update_service(self, zc: Zeroconf, type_: str, name: str) -> None:
        print(f"Service {name} updated")

    def remove_service(self, zc: Zeroconf, type_: str, name: str) -> None:
        print(f"Service {name} removed")

    def add_service(self, zc: Zeroconf, type_: str, name: str) -> None:
        info = zc.get_service_info(type_, name)
        print(f"Service {name} added, service info: {info}")


def get_local_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect(("8.8.8.8", 80))
    ip = s.getsockname()[0]
    s.close()
    return ip


async def handle_connection(websocket):
    peer = websocket.remote_address
    print(f"Connection from {peer[0]}:{peer[1]}")
    try:
        async for message in websocket:
            data = json.loads(message)
            print(f"Received: {data['text']}")
    except ConnectionClosed:
        print(f"Connection closed by {peer[0]}")


async def start_server():
    async with websockets.serve(handle_connection, "0.0.0.0", int(PORT)):
        print(f"WebSocket server started on port {PORT}")
        await asyncio.Future()


async def send_string(ip, text):
    url = f"ws://{ip}:{PORT}"
    try:
        async with websockets.connect(url) as websocket:
            await websocket.send(json.dumps({"text": text}))
            print(f"Sent: {text} to {url}")
    except Exception as e:
        print(f"Failed to send to {url}: {e}")


def run_server():
    asyncio.run(start_server())


my_info = ServiceInfo(
    SERVICE,
    f"{HOSTNAME}.{SERVICE}",
    addresses=[socket.inet_aton(get_local_ip())],
    port=int(PORT),
)

print(f"{my_info}")
zeroconf = Zeroconf()
zeroconf.register_service(my_info)
listener = StringShareListerer()
browser = ServiceBrowser(zeroconf, "_stringshare._tcp.local.", listener)

try:
    server_thread = threading.Thread(target=run_server, daemon=True)
    server_thread.start()
    while True:
        ip = input("Enter the IP address to send to (or 'exit' to quit): ")
        if ip.lower() == "exit":
            break
        text = input("Enter the text to send: ")
        asyncio.run(send_string(ip, text))
except KeyboardInterrupt:
    print("Shutting down...")
finally:
    zeroconf.close()
