
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


PORT = os.getenv("PORT")
SERVICE = "_stringshare._tcp.local"
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


zeroconf = Zeroconf()
listener = StringShareListerer()
browser = ServiceBrowser(zeroconf, "_http._tcp.local.", listener)

try:
    input("Press enter to exit...\n\n")
finally:
    zeroconf.close()