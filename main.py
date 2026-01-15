from fastapi import FastAPI, WebSocket, WebSocketDisconnect, UploadFile, File, Request
from fastapi.staticfiles import StaticFiles
import os
import logging
from datetime import datetime
import uuid

# =====================================================
# Logging Configuration
# =====================================================
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)

logger = logging.getLogger("SMART_AD_SERVER")

# =====================================================
# FastAPI App Initialization
# =====================================================
logger.info("🚀 Smart Advertisement Server BOOTING")
app = FastAPI(title="LCD Smart Advertisement System")

# =====================================================
# Uploads Directory Setup
# =====================================================
UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

logger.info(f"📂 Upload directory ready: {os.path.abspath(UPLOAD_DIR)}")

app.mount("/media", StaticFiles(directory=UPLOAD_DIR), name="media")
logger.info("🌐 Static media endpoint mounted → /media")

# =====================================================
# Active WebSocket Connections
# =====================================================
active_connections = []

# =====================================================
# Middleware : API Request Logger
# =====================================================
@app.middleware("http")
async def log_http_requests(request: Request, call_next):
    request_id = str(uuid.uuid4())[:8]
    start_time = datetime.now()

    logger.info("=" * 80)
    logger.info(f"➡️  HTTP REQUEST STARTED | ID: {request_id}")
    logger.info(f"Method: {request.method}")
    logger.info(f"URL: {request.url}")
    logger.info(f"Client: {request.client.host if request.client else 'UNKNOWN'}")

    response = await call_next(request)

    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()

    logger.info(f"⬅️  HTTP REQUEST COMPLETED | ID: {request_id}")
    logger.info(f"Status Code: {response.status_code}")
    logger.info(f"Processing Time: {duration:.3f} sec")
    logger.info("=" * 80)

    return response

# =====================================================
# WebSocket Endpoint (Screens)
# =====================================================
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    client_ip = websocket.client.host if websocket.client else "UNKNOWN"

    logger.info("=" * 80)
    logger.info("🔌 WEBSOCKET CONNECTION REQUEST")
    logger.info(f"Client IP: {client_ip}")

    await websocket.accept()
    active_connections.append(websocket)

    logger.info("✅ WEBSOCKET ACCEPTED")
    logger.info(f"📺 Active Screens Connected: {len(active_connections)}")
    logger.info("=" * 80)

    try:
        while True:
            data = await websocket.receive_text()
            logger.info(
                f"💓 HEARTBEAT / MESSAGE | From: {client_ip} | Payload: {data}"
            )

    except WebSocketDisconnect:
        if websocket in active_connections:
            active_connections.remove(websocket)

        logger.warning("=" * 80)
        logger.warning("❌ WEBSOCKET DISCONNECTED")
        logger.warning(f"Client IP: {client_ip}")
        logger.warning(f"Remaining Screens: {len(active_connections)}")
        logger.warning("=" * 80)

    except Exception as e:
        logger.error("=" * 80)
        logger.error("🔥 WEBSOCKET ERROR")
        logger.error(f"Client IP: {client_ip}")
        logger.error(f"Error: {str(e)}")
        logger.error("=" * 80)

# =====================================================
# File Upload API (Admin Panel)
# =====================================================
@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    request_id = str(uuid.uuid4())[:8]
    start_time = datetime.now()

    logger.info("=" * 80)
    logger.info(f"📤 UPLOAD API STARTED | Request ID: {request_id}")

    try:
        logger.info(f"📄 Filename Received: {file.filename}")
        logger.info(f"📦 Content-Type: {file.content_type}")

        file_path = os.path.join(UPLOAD_DIR, file.filename)
        logger.info(f"📍 Target Storage Path: {file_path}")

        logger.info("📥 Reading file into memory")
        contents = await file.read()
        file_size_kb = len(contents) / 1024

        logger.info(f"📊 File Size: {file_size_kb:.2f} KB")

        logger.info("💾 Writing file to disk")
        with open(file_path, "wb") as f:
            f.write(contents)

        logger.info("✅ File successfully saved")

        # WebSocket notification
        notified = 0
        logger.info("📡 Broadcasting update to connected screens")

        for ws in active_connections:
            await ws.send_text(f"NEW_CONTENT:{file.filename}")
            notified += 1
            logger.info("➡️ Notification sent to one screen")

        logger.info(
            f"📢 Broadcast completed | Screens notified: {notified}"
        )

        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()

        logger.info(f"⏱️ Upload request completed in {duration:.2f} sec")
        logger.info(f"📤 UPLOAD API SUCCESS | Request ID: {request_id}")
        logger.info("=" * 80)

        return {
            "status": "uploaded",
            "request_id": request_id,
            "filename": file.filename,
            "file_url": f"/media/{file.filename}",
            "file_size_kb": round(file_size_kb, 2),
            "notified_screens": notified
        }

    except Exception as e:
        logger.error("=" * 80)
        logger.error(f"❌ UPLOAD API FAILED | Request ID: {request_id}")
        logger.error(f"Filename: {file.filename}")
        logger.error(f"Error: {str(e)}")
        logger.error("=" * 80)

        return {
            "status": "error",
            "request_id": request_id,
            "message": str(e)
        }
