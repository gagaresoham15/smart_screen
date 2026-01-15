import websocket
import logging
import os
import requests
from datetime import datetime

# =====================================================
# Device Configuration
# =====================================================
DEVICE_ID = "SCREEN_101"
SERVER_WS_URL = "ws://127.0.0.1:2000/ws"
SERVER_HTTP_URL = "http://127.0.0.1:2000"

# Local storage (acts like Pi SD Card)
STORAGE_DIR = "device_storage"
os.makedirs(STORAGE_DIR, exist_ok=True)

# =====================================================
# Logging Configuration
# =====================================================
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)
logger = logging.getLogger(__name__)

# =====================================================
# Helper Function : Download File from Server
# =====================================================
def download_file(filename):
    logger.info(f"[{DEVICE_ID}] Download handler triggered")

    file_url = f"{SERVER_HTTP_URL}/media/{filename}"
    local_path = os.path.join(STORAGE_DIR, filename)

    logger.info(f"[{DEVICE_ID}] Server file URL: {file_url}")
    logger.info(f"[{DEVICE_ID}] Local storage path resolved: {local_path}")

    # Check if file already exists (cache logic)
    if os.path.exists(local_path):
        logger.warning(
            f"[{DEVICE_ID}] Cache HIT | File already present locally: {filename}"
        )
        logger.info(
            f"[{DEVICE_ID}] Skipping download to save bandwidth & time"
        )
        return

    logger.info(
        f"[{DEVICE_ID}] Cache MISS | File not found locally, starting download"
    )

    try:
        start_time = datetime.now()

        logger.info(f"[{DEVICE_ID}] Sending HTTP GET request to server")

        response = requests.get(file_url, stream=True, timeout=10)
        response.raise_for_status()

        logger.info(
            f"[{DEVICE_ID}] HTTP response received | Status Code: {response.status_code}"
        )

        bytes_written = 0

        with open(local_path, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
                    bytes_written += len(chunk)

        size_kb = bytes_written / 1024
        end_time = datetime.now()

        logger.info(
            f"[{DEVICE_ID}] Download SUCCESS | "
            f"File: {filename} | Size: {size_kb:.2f} KB"
        )

        logger.info(
            f"[{DEVICE_ID}] Download duration: "
            f"{(end_time - start_time).total_seconds()} seconds"
        )

        logger.info(
            f"[{DEVICE_ID}] File safely stored at: {os.path.abspath(local_path)}"
        )

        logger.info(
            f"[{DEVICE_ID}] File ready for playback / scheduling"
        )

    except requests.exceptions.Timeout:
        logger.error(
            f"[{DEVICE_ID}] Download FAILED | Timeout while downloading {filename}"
        )

    except requests.exceptions.HTTPError as e:
        logger.error(
            f"[{DEVICE_ID}] HTTP ERROR while downloading {filename} | {str(e)}"
        )

    except Exception as e:
        logger.error(
            f"[{DEVICE_ID}] Unexpected ERROR during download | {str(e)}"
        )

# =====================================================
# WebSocket Callbacks
# =====================================================
def on_open(ws):
    logger.info("=" * 60)
    logger.info(f"[{DEVICE_ID}] WebSocket connection ESTABLISHED")
    logger.info(f"[{DEVICE_ID}] Device marked as ONLINE on server")
    logger.info(f"[{DEVICE_ID}] Waiting for content push events...")
    logger.info("=" * 60)

def on_message(ws, message):
    receive_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    logger.info(f"[{DEVICE_ID}] Incoming WebSocket message")
    logger.info(f"[{DEVICE_ID}] Timestamp: {receive_time}")
    logger.info(f"[{DEVICE_ID}] Raw Payload: {message}")

    # Expected message format: NEW_CONTENT:<filename>
    if message.startswith("NEW_CONTENT:"):
        filename = message.replace("NEW_CONTENT:", "").strip()

        logger.info(
            f"[{DEVICE_ID}] Valid content notification detected"
        )

        logger.info(
            f"[{DEVICE_ID}] New media assigned by server | Filename: {filename}"
        )

        download_file(filename)

    else:
        logger.warning(
            f"[{DEVICE_ID}] Unknown / unsupported message format received"
        )

def on_error(ws, error):
    logger.error(f"[{DEVICE_ID}] WebSocket ERROR occurred")
    logger.error(f"[{DEVICE_ID}] Error details: {error}")

def on_close(ws, close_status_code, close_msg):
    logger.warning("=" * 60)
    logger.warning(f"[{DEVICE_ID}] WebSocket connection CLOSED")
    logger.warning(f"[{DEVICE_ID}] Close Code: {close_status_code}")
    logger.warning(f"[{DEVICE_ID}] Reason: {close_msg}")
    logger.warning(f"[{DEVICE_ID}] Device is OFFLINE")
    logger.warning("=" * 60)

# =====================================================
# Client Startup (Device Boot Simulation)
# =====================================================
if __name__ == "__main__":
    logger.info("=" * 60)
    logger.info(f"[{DEVICE_ID}] Fake Raspberry Pi BOOT sequence started")
    logger.info(f"[{DEVICE_ID}] Initializing network modules")
    logger.info(f"[{DEVICE_ID}] Initializing local storage")
    logger.info(f"[{DEVICE_ID}] Storage directory: {os.path.abspath(STORAGE_DIR)}")
    logger.info(f"[{DEVICE_ID}] Connecting to WebSocket server")
    logger.info(f"[{DEVICE_ID}] Server URL: {SERVER_WS_URL}")
    logger.info("=" * 60)

    ws = websocket.WebSocketApp(
        SERVER_WS_URL,
        on_open=on_open,
        on_message=on_message,
        on_error=on_error,
        on_close=on_close
    )

    ws.run_forever()
