import websocket
import logging
import os
import requests
from datetime import datetime

# =====================================================
# Device Configuration
# =====================================================
DEVICE_ID = "SCREEN_101"

# 🔥 ngrok PUBLIC URLs
SERVER_WS_URL = "wss://c784b905d3b6.ngrok-free.app/ws"
SERVER_HTTP_URL = "https://c784b905d3b6.ngrok-free.app"

# Local storage (acts like Raspberry Pi SD Card)
STORAGE_DIR = "device_storage"
os.makedirs(STORAGE_DIR, exist_ok=True)

# =====================================================
# Logging Configuration
# =====================================================
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)

logger = logging.getLogger("SMART_AD_DEVICE")

# =====================================================
# Helper Function : Download File from Server
# =====================================================
def download_file(filename):
    logger.info("=" * 60)
    logger.info(f"[{DEVICE_ID}] DOWNLOAD WORKFLOW STARTED")

    file_url = f"{SERVER_HTTP_URL}/media/{filename}"
    local_path = os.path.join(STORAGE_DIR, filename)

    logger.info(f"[{DEVICE_ID}] Remote file URL : {file_url}")
    logger.info(f"[{DEVICE_ID}] Local path        : {local_path}")

    # Cache check
    if os.path.exists(local_path):
        logger.warning(f"[{DEVICE_ID}] CACHE HIT | File already exists")
        logger.info(f"[{DEVICE_ID}] Download skipped")
        logger.info("=" * 60)
        return

    logger.info(f"[{DEVICE_ID}] CACHE MISS | Download required")

    try:
        start_time = datetime.now()
        logger.info(f"[{DEVICE_ID}] Sending HTTP GET request")

        response = requests.get(file_url, stream=True, timeout=15)
        response.raise_for_status()

        logger.info(
            f"[{DEVICE_ID}] HTTP Response OK | Status: {response.status_code}"
        )

        bytes_written = 0

        with open(local_path, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
                    bytes_written += len(chunk)

        size_kb = bytes_written / 1024
        duration = (datetime.now() - start_time).total_seconds()

        logger.info(
            f"[{DEVICE_ID}] DOWNLOAD SUCCESS | "
            f"File: {filename} | Size: {size_kb:.2f} KB"
        )

        logger.info(f"[{DEVICE_ID}] Download time: {duration:.2f} seconds")
        logger.info(f"[{DEVICE_ID}] Stored at: {os.path.abspath(local_path)}")
        logger.info(f"[{DEVICE_ID}] File ready for playback")
        logger.info("=" * 60)

    except requests.exceptions.Timeout:
        logger.error(f"[{DEVICE_ID}] DOWNLOAD FAILED | Timeout")

    except requests.exceptions.HTTPError as e:
        logger.error(f"[{DEVICE_ID}] HTTP ERROR | {str(e)}")

    except Exception as e:
        logger.error(f"[{DEVICE_ID}] UNKNOWN ERROR | {str(e)}")

# =====================================================
# WebSocket Callbacks
# =====================================================
def on_open(ws):
    logger.info("=" * 60)
    logger.info(f"[{DEVICE_ID}] WebSocket CONNECTED")
    logger.info(f"[{DEVICE_ID}] Device STATUS: ONLINE")
    logger.info(f"[{DEVICE_ID}] Waiting for content notifications...")
    logger.info("=" * 60)

def on_message(ws, message):
    logger.info("=" * 60)
    logger.info(f"[{DEVICE_ID}] WebSocket MESSAGE RECEIVED")
    logger.info(f"[{DEVICE_ID}] Payload: {message}")

    if message.startswith("NEW_CONTENT:"):
        filename = message.replace("NEW_CONTENT:", "").strip()
        logger.info(f"[{DEVICE_ID}] New content assigned: {filename}")
        download_file(filename)
    else:
        logger.warning(f"[{DEVICE_ID}] Unknown message format")
    logger.info("=" * 60)

def on_error(ws, error):
    logger.error("=" * 60)
    logger.error(f"[{DEVICE_ID}] WebSocket ERROR")
    logger.error(f"[{DEVICE_ID}] Error: {error}")
    logger.error("=" * 60)

def on_close(ws, close_status_code, close_msg):
    logger.warning("=" * 60)
    logger.warning(f"[{DEVICE_ID}] WebSocket DISCONNECTED")
    logger.warning(f"[{DEVICE_ID}] Close Code: {close_status_code}")
    logger.warning(f"[{DEVICE_ID}] Reason    : {close_msg}")
    logger.warning(f"[{DEVICE_ID}] Device STATUS: OFFLINE")
    logger.warning("=" * 60)

# =====================================================
# Device Boot Simulation
# =====================================================
if __name__ == "__main__":
    logger.info("=" * 60)
    logger.info(f"[{DEVICE_ID}] FAKE RASPBERRY PI BOOTING")
    logger.info(f"[{DEVICE_ID}] Storage initialized")
    logger.info(f"[{DEVICE_ID}] Storage path: {os.path.abspath(STORAGE_DIR)}")
    logger.info(f"[{DEVICE_ID}] Connecting to server...")
    logger.info(f"[{DEVICE_ID}] WS URL: {SERVER_WS_URL}")
    logger.info("=" * 60)

    ws = websocket.WebSocketApp(
        SERVER_WS_URL,
        on_open=on_open,
        on_message=on_message,
        on_error=on_error,
        on_close=on_close
    )

    ws.run_forever()
