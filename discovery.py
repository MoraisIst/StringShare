"""Service discovery using mDNS for StringShare."""

import socket
import logging
from network import get_local_ip
from typing import Dict, Callable, Optional
from zeroconf import ServiceBrowser, ServiceInfo, Zeroconf, ServiceListener

logger = logging.getLogger(__name__)


class StringShareListener(ServiceListener):
    """Listener for StringShare service discovery events."""

    def __init__(
        self,
        on_service_added: Optional[Callable[[str, str], None]] = None,
        on_service_removed: Optional[Callable[[str], None]] = None,
    ):
        """
        Initialize the StringShare listener.

        Args:
            on_service_added: Callback when a service is discovered (name, ip)
            on_service_removed: Callback when a service is removed (name)
        """
        self.peers: Dict[str, str] = {}
        self._on_service_added = on_service_added
        self._on_service_removed = on_service_removed

    def update_service(self, zc: Zeroconf, type_: str, name: str) -> None:
        """Handle service update event."""
        self.add_service(zc, type_, name)

    def remove_service(self, zc: Zeroconf, type_: str, name: str) -> None:
        """Handle service removal event."""
        peer_name = name.removesuffix(f".{type_}")
        if peer_name in self.peers:
            del self.peers[peer_name]
            logger.info(f"Peer {peer_name} removed")
            if self._on_service_removed:
                self._on_service_removed(peer_name)

    def add_service(self, zc: Zeroconf, type_: str, name: str) -> None:
        """Handle service discovery event."""
        try:
            info = zc.get_service_info(type_, name)
            if info is None:
                logger.warning(f"Could not get info for service {name}")
                return

            peer_name = name.removesuffix(f".{type_}")

            # Skip if it's our own service
            local_hostname = socket.gethostname()
            if peer_name == local_hostname:
                return

            ip = socket.inet_ntoa(info.addresses[0])
            self.peers[peer_name] = ip
            logger.info(f"Peer {peer_name} with IP {ip} added")

            if self._on_service_added:
                self._on_service_added(peer_name, ip)
        except Exception as e:
            logger.error(f"Error adding service {name}: {e}")


class ServiceDiscovery:
    """Manager for mDNS service discovery."""

    def __init__(self, service_type: str, hostname: str, port: int):
        """
        Initialize service discovery.

        Args:
            service_type: The service type (e.g., "_stringshare._tcp.local.")
            hostname: The hostname for this service
            port: The port number
        """
        self.service_type = service_type
        self.hostname = hostname
        self.port = port
        self.zeroconf: Optional[Zeroconf] = None
        self.listener: Optional[StringShareListener] = None
        self.browser: Optional[ServiceBrowser] = None

    def start(
        self,
        on_service_added: Optional[Callable[[str, str], None]] = None,
        on_service_removed: Optional[Callable[[str], None]] = None,
    ) -> None:
        """
        Start service discovery and publish this service.

        Args:
            on_service_added: Callback when a service is discovered
            on_service_removed: Callback when a service is removed
        """
        try:
            self.zeroconf = Zeroconf()

            local_ip = get_local_ip()
            service_info = ServiceInfo(
                self.service_type,
                f"{self.hostname}.{self.service_type}",
                addresses=[local_ip],
                port=self.port,
                properties={"version": "1.0"},
            )
            self.zeroconf.register_service(service_info)
            logger.info(f"Published service {self.hostname} on {local_ip}:{self.port}")

            self.listener = StringShareListener(on_service_added, on_service_removed)
            self.browser = ServiceBrowser(
                self.zeroconf, self.service_type, self.listener
            )
            logger.info("Service discovery started")
        except Exception as e:
            logger.error(f"Failed to start service discovery: {e}")
            raise

    def stop(self) -> None:
        """Stop service discovery."""
        try:
            if self.browser:
                self.browser.cancel()
            if self.zeroconf:
                self.zeroconf.close()
            logger.info("Service discovery stopped")
        except Exception as e:
            logger.error(f"Error stopping service discovery: {e}")

    def get_peers(self) -> Dict[str, str]:
        """
        Get discovered peers.

        Returns:
            Dictionary mapping peer names to IP addresses
        """
        if self.listener:
            return self.listener.peers
        return {}
