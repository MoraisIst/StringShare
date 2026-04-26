"""Network utilities for StringShare application."""

import socket
import json
import asyncio
import logging
import threading
from typing import Callable
import websockets
from websockets.server import WebSocketServerProtocol

logger = logging.getLogger(__name__)


def get_local_ip() -> str:
    """
    Get the local IP address of the machine.

    Returns:
        The local IP address as a string
    """
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        sock.connect(("8.8.8.8", 80))
        return sock.getsockname()[0]
    except OSError as e:
        logger.error(f"Failed to get local IP: {e}")
        return "127.0.0.1"
    finally:
        sock.close()


async def start_server(
    port: int,
    message_handler: Callable[[dict], None],
    stop_event: threading.Event,
) -> None:
    """
    Start the WebSocket server.

    Args:
        port: The port to listen on
        message_handler: Callback function to handle received messages
        stop_event: Event that signals the server should shut down
    """

    async def handle_connection(websocket: WebSocketServerProtocol) -> None:
        """Handle incoming WebSocket connections."""
        peer = websocket.remote_address
        logger.info(f"Connection from {peer[0]}:{peer[1]}")
        try:
            async for message in websocket:
                data = json.loads(message)
                logger.debug(f"Received: {data.get('text', 'N/A')}")
                message_handler(data)
        except websockets.exceptions.ConnectionClosed:
            logger.info(f"Connection closed by {peer[0]}")
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON from {peer[0]}: {e}")
        except Exception as e:
            logger.error(f"Error handling connection from {peer[0]}: {e}")

    try:
        async with websockets.serve(handle_connection, "0.0.0.0", port):
            logger.info(f"WebSocket server started on port {port}")
            while not stop_event.is_set():
                await asyncio.sleep(0.2)
            logger.info("WebSocket server stopping")
    except Exception as e:
        logger.error(f"Server error: {e}")
        raise


async def send_string(ip: str, port: int, text: str) -> bool:
    """
    Send a string to a remote StringShare instance.

    Args:
        ip: The IP address to send to
        port: The port number
        text: The text to send

    Returns:
        True if successful, False otherwise
    """
    url = f"ws://{ip}:{port}"
    try:
        async with websockets.connect(url, open_timeout=5, close_timeout=1) as websocket:
            await asyncio.wait_for(
                websocket.send(json.dumps({"text": text})), timeout=5
            )
            logger.info(f"Sent: {text} to {url}")
            return True
    except Exception as e:
        logger.error(f"Failed to send to {url}: {e}")
        return False
