"""Main application for StringShare - a cross-device clipboard sharing tool."""

import asyncio
import logging
import platform
import threading
import time
import tkinter as tk
import keyboard
import signal
import pyperclip
from typing import Optional, List, Dict

from config import config
from discovery import ServiceDiscovery
from gui import StringShareWindow, PeerSelectionWindow
from network import start_server, send_string

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


class StringShareApplication:
    """Main application controller for StringShare."""

    def __init__(self):
        """Initialize the StringShare application."""
        self.service_discovery: Optional[ServiceDiscovery] = None
        self.server_thread: Optional[threading.Thread] = None
        self.stop_event = threading.Event()
        self._gui_lock = threading.Lock()
        self._gui_windows: List[tk.Tk] = []
        self._gui_threads: List[threading.Thread] = []
        self.running = False

    def _on_message_received(self, data: dict) -> None:
        """
        Handle incoming messages from the network.

        Args:
            data: Dictionary containing the message data
        """
        text = data.get("text", "")
        if text:
            logger.info(f"Displaying received text: {text}")
            gui_thread = threading.Thread(
                target=self._run_received_text_gui,
                args=(text,),
                daemon=False,
            )
            self._track_gui_thread(gui_thread)
            gui_thread.start()

    def _on_service_added(self, peer_name: str, ip: str) -> None:
        """
        Handle service discovery of a new peer.

        Args:
            peer_name: The name of the discovered peer
            ip: The IP address of the peer
        """
        logger.info(f"Discovered peer: {peer_name} at {ip}")

    def _on_service_removed(self, peer_name: str) -> None:
        """
        Handle removal of a discovered peer.

        Args:
            peer_name: The name of the removed peer
        """
        logger.info(f"Peer removed: {peer_name}")

    def _start_server(self) -> None:
        """Start the WebSocket server in a background thread."""
        try:
            asyncio.run(
                start_server(
                    config.PORT,
                    self._on_message_received,
                    self.stop_event,
                )
            )
        except Exception as e:
            logger.error(f"Server error: {e}")

    def start(self) -> None:
        """Start the StringShare application."""
        try:
            logger.info(
                f"Starting StringShare on {platform.system()} ({platform.machine()})"
            )

            self.service_discovery = ServiceDiscovery(
                config.SERVICE_TYPE, config.HOSTNAME, config.PORT
            )
            self.service_discovery.start(
                self._on_service_added, self._on_service_removed
            )

            self.running = True
            self.stop_event.clear()
            self.server_thread = threading.Thread(
                target=self._start_server, daemon=False
            )
            self.server_thread.start()

            logger.info("StringShare application started successfully")

            self._keep_alive()

        except KeyboardInterrupt:
            logger.info("Interrupt received, shutting down...")
            self.stop()
        except Exception as e:
            logger.error(f"Failed to start application: {e}")
            self.stop()
            raise

    def process_copy_event(self) -> None:
        """Handle the Ctrl+C hotkey event to send the current clipboard text."""
        try:
            time.sleep(0.1)
            text = pyperclip.paste()
            if text:
                logger.info(f"Clipboard text ready to send: {text}")
                self._show_peer_selection(text)
            else:
                logger.info("Clipboard is empty, nothing to send.")
        except Exception as e:
            logger.error(f"Error processing copy event: {e}")

    def _show_peer_selection(self, text: str) -> None:
        """
        Show peer selection window for sending text.

        Args:
            text: The text to send
        """
        if not self.service_discovery:
            logger.warning("Service discovery not initialized")
            return

        peers = self.service_discovery.get_peers()
        if not peers:
            logger.warning("No peers available")
            return

        # Run GUI in a separate thread to avoid blocking
        gui_thread = threading.Thread(
            target=self._run_peer_selection_gui, args=(peers, text), daemon=False
        )
        self._track_gui_thread(gui_thread)
        gui_thread.start()

    def _track_gui_thread(self, gui_thread: threading.Thread) -> None:
        """Track a GUI thread so shutdown can wait briefly for it."""
        with self._gui_lock:
            self._gui_threads.append(gui_thread)

    def _register_window(self, window: tk.Tk) -> None:
        """Track a GUI window so shutdown can request it to close."""
        with self._gui_lock:
            self._gui_windows.append(window)

    def _unregister_window(self, window: tk.Tk) -> None:
        """Stop tracking a closed GUI window."""
        with self._gui_lock:
            if window in self._gui_windows:
                self._gui_windows.remove(window)

    def _run_received_text_gui(self, text: str) -> None:
        """Run the received text GUI in its own thread."""
        window = StringShareWindow(
            text,
            on_close=lambda: self._unregister_window(window),
        )
        self._register_window(window)
        logger.info("Received text window created")
        try:
            window.mainloop()
        finally:
            self._unregister_window(window)

    def _run_peer_selection_gui(self, peers: Dict[str, str], text: str) -> None:
        """
        Run the peer selection GUI in a separate thread.

        Args:
            peers: Dictionary of peer names to IPs
            text: The text to send
        """
        def on_send_selected(ips: List[str]) -> None:
            """Handle selected peers."""
            asyncio.run(self.send_to_peers_async(ips, text))

        window = PeerSelectionWindow(peers, on_send_selected)
        window.protocol(
            "WM_DELETE_WINDOW",
            lambda: self._close_window(window),
        )
        self._register_window(window)
        logger.info("Peer selection window created")
        try:
            window.mainloop()
        finally:
            self._unregister_window(window)

    def _close_window(self, window: tk.Tk) -> None:
        """Close and unregister a tracked Tk window."""
        self._unregister_window(window)
        window.destroy()

    async def send_to_peers_async(self, ips: List[str], text: str) -> None:
        """
        Send text to multiple peers asynchronously.

        Args:
            ips: List of IP addresses to send to
            text: The text to send
        """
        tasks = [send_string(ip, config.PORT, text) for ip in ips]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        for ip, result in zip(ips, results):
            if isinstance(result, Exception):
                logger.error(f"Failed to send to {ip}: {result}")
            elif result:
                logger.info(f"Successfully sent to {ip}")
            else:
                logger.warning(f"Send to {ip} returned False")

    def _keep_alive(self) -> None:
        """Keep the application running."""
        keyboard.add_hotkey(
            "ctrl+c",
            lambda: self.process_copy_event(),
            suppress=False,
        )
        keyboard.add_hotkey("ctrl+q", lambda: self.stop())

        logger.info("App running. Press Ctrl+C send string or Ctrl+Q to quit.")

        try:
            while not self.stop_event.wait(0.2):
                pass
        except Exception as e:
            logger.error(f"Error in main loop: {e}")
        finally:
            keyboard.unhook_all()

    def stop(self) -> None:
        """Stop the StringShare application."""
        if self.stop_event.is_set():
            return

        logger.info("Shutting down StringShare...")
        self.running = False
        self.stop_event.set()

        if self.service_discovery:
            self.service_discovery.stop()

        self._close_gui_windows()
        self._join_threads()

        logger.info("StringShare stopped")

    def _close_gui_windows(self) -> None:
        """Ask open GUI windows to close."""
        with self._gui_lock:
            windows = list(self._gui_windows)

        for window in windows:
            try:
                window.after(0, lambda w=window: self._close_window(w))
            except tk.TclError:
                self._unregister_window(window)

    def _join_threads(self) -> None:
        """Wait briefly for worker threads to exit."""
        current_thread = threading.current_thread()

        if self.server_thread and self.server_thread is not current_thread:
            self.server_thread.join(timeout=2)

        with self._gui_lock:
            gui_threads = list(self._gui_threads)

        for gui_thread in gui_threads:
            if gui_thread is not current_thread:
                gui_thread.join(timeout=1)


def ignore_keyboard_interrupt():
    signal.signal(signal.SIGINT, signal.SIG_IGN)


def main():
    """Entry point for the application."""
    ignore_keyboard_interrupt()
    app = StringShareApplication()
    app.start()


if __name__ == "__main__":
    main()
