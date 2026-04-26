# StringShare

A cross-device clipboard sharing application using mDNS service discovery and WebSockets.

### Modules

- **config.py**: Centralized configuration using environment variables and defaults
- **gui.py**: GUI components - `StringShareWindow` class for displaying and copying strings
- **network.py**: Async WebSocket server and client for message passing
- **discovery.py**: mDNS service discovery using Zeroconf
- **StringShare.py**: Main application controller coordinating all components

## Installation

1. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Configure environment variables:
```bash
cp .env.example .env
# Edit .env with your desired settings
```

## Usage

### Run the application:
```bash
python StringShare.py
```
