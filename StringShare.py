import platform
import socket
import threading
import time
import os
import pyperclip
import websockets
from websockets.exceptions import ConnectionClosed
from plyer import notification
from zeroconf import ServiceBrowser, ServiceInfo, Zeroconf, ServiceListener
from dotenv import load_dotenv

load_dotenv()
PORT = os.getenv("PORT")
if not PORT:
    raise ValueError("PORT environment variable not set")
SERVICE = "_stringshare._tcp.local."
HOSTNAME = socket.gethostname()
OS = platform.system()


class StringShareListerer(ServiceListener):
    def update_service(self, zc: Zeroconf, type_: str, name: str) -> None:
        info = zc.get_service_info(type_, name)
        print(f"Found: {name})")
        print(f" IP address: {socket.inet_ntoa(info.addresses[0])}")
        print(f" Port: {info.port}")

    def remove_service(self, zc: Zeroconf, type_: str, name: str) -> None:
        print(f"Service {name} removed")

    def add_service(self, zc: Zeroconf, type_: str, name: str) -> None:
        info = zc.get_service_info(type_, name)
        print(f"Service {name} added, service info: {info}")


my_info = ServiceInfo(
    SERVICE,
    f"{HOSTNAME}.{SERVICE}",
    addresses=[socket.inet_aton(socket.gethostbyname(socket.gethostname()))],
    port=int(PORT),
)

zeroconf = Zeroconf()
zeroconf.register_service(my_info)
browser = ServiceBrowser(zeroconf, "_stringshare._tcp.local.", StringShareListerer())

try:
    input("Press enter to exit...\n\n")
finally:
    zeroconf.close()
