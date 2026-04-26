"""Configuration management for StringShare application."""

import os
from dotenv import load_dotenv
import socket

load_dotenv()


class Config:
    """Centralized configuration for StringShare."""

    PORT: int = int(os.getenv("PORT", 5000))
    SERVICE_TYPE: str = "_stringshare._tcp.local."
    HOSTNAME: str = socket.gethostname()
    WINDOW_WIDTH: int = 300
    WINDOW_HEIGHT: int = 200
    COPY_BUTTON_TIMEOUT_MS: int = 1000


config = Config()
