import platform
import socket
import threading
import plyer
import os
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

peers: dict[str, str] = {}


class StringShareListerer:
    def update_service(self, zc: Zeroconf, type_: str, name: str) -> None:
        self.add_service(zc, type_, name)

    def remove_service(self, zc: Zeroconf, type_: str, name: str) -> None:
        peer_name = name.removesuffix(f".{type_}")
        if peer_name in peers:
            del peers[peer_name]
        print(f"Peer {peer_name} removed")

    def add_service(self, zc: Zeroconf, type_: str, name: str) -> None:
        info = zc.get_service_info(type_, name)
        peer_name = name.removesuffix(f".{type_}")
        if peer_name == HOSTNAME:
            return
        ip = socket.inet_ntoa(info.addresses[0])
        peers[peer_name] = ip
        print(f"Peer {peer_name} with IP {ip} added")


def get_local_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))
        return s.getsockname()[0]
    finally:
        s.close()


async def handle_connection(websocket):
    peer = websocket.remote_address
    print(f"Connection from {peer[0]}:{peer[1]}")
    try:
        async for message in websocket:
            data = json.loads(message)
            print(f"Received: {data['text']}")
            notification.notify(
                title="StringShare",
                message=data["text"],
                app_name="StringShare",
                timeout=5,
            )
    except ConnectionClosed:
        print(f"Connection closed by {peer[0]}")
    except Exception as e:
        print(f"Error handling connection from {peer[0]}: {e}")


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
            notification.notify(
                title="StringShare",
                message=f"Sent: {text} to {ip}",
                app_name="StringShare",
                timeout=5,
            )
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


def main():
    local_ip = get_local_ip()
    print(f"Hostname: {HOSTNAME}")
    print(f"Local IP: {local_ip}")
    print(f"PORT: {PORT}")
    print(f"Service: {SERVICE}")
    print()

    zc = Zeroconf()

    my_service_info = ServiceInfo(
        SERVICE,
        f"{HOSTNAME}.{SERVICE}",
        addresses=[socket.inet_aton(local_ip)],
        port=int(PORT),
    )

    zc.register_service(my_service_info)
    print(f"Advertised service: {my_service_info}")
    print(f"Browsing for services of type {SERVICE}...")

    browser = ServiceBrowser(zc, SERVICE, StringShareListerer())

    # Create a single event loop and keep it alive
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    # Run the server in a separate thread
    server_thread = threading.Thread(
        target=lambda: loop.run_until_complete(start_server()), daemon=True
    )
    server_thread.start()
    print("Server started in background thread")

    try:
        while True:
            ip = input("Enter the IP address to send to (or 'exit' to quit): ")
            if ip.lower() == "exit":
                break
            text = input("Enter the text to send: ")
            asyncio.run_coroutine_threadsafe(send_string(ip, text), loop)
    except KeyboardInterrupt:
        print("Shutting down...")
    finally:
        zc.unregister_service(my_service_info)
        zc.close()
        loop.call_soon_threadsafe(loop.stop)
        print("Cleaned up Zeroconf resources.")


if __name__ == "__main__":
    main()
