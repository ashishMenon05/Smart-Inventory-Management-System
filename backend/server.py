"""
server.py
FastAPI server to expose SmartStock AI Vision capabilities to the Next.js frontend.
"""

import cv2
import logging
import asyncio
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import StreamingResponse
from pathlib import Path
import threading
import json
import time

# Add project root to path so imports work
import sys
sys.path.insert(0, str(Path(__file__).parent))

from core.database import DatabaseManager
from core.scanner import InventoryScanner
from core.alerts import AlertManager

# ── Logging ──────────────────────────────────────────────────────────────────
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("smartstock-server")
from fastapi.middleware.cors import CORSMiddleware

# ...
app = FastAPI(title="SmartStock AI Vision API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── State ─────────────────────────────────────────────────────────────────────
db_path = Path("data") / "inventory.db"
db = DatabaseManager(str(db_path))
alert_mgr = AlertManager(db)
scanner = InventoryScanner(db_manager=db, alert_manager=alert_mgr, camera_index=0)

# Track connected clients for WebSocket
class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            await connection.send_text(message)

manager = ConnectionManager()

# ── Background Scanner Worker ─────────────────────────────────────────────────
def start_scanner():
    if not scanner.open_camera():
        logger.error("Failed to open camera. Scanning will not be available.")
        return
    scanner.start_capture_thread()
    logger.info("Scanner thread started.")

@app.on_event("startup")
async def startup_event():
    start_scanner()
    # Start the broadcast loop
    asyncio.create_task(broadcast_scan_data())

@app.on_event("shutdown")
async def shutdown_event():
    scanner.release()
    db.close()

async def broadcast_scan_data():
    """Periodically check for detected items and notify clients via WebSocket."""
    last_detected = set()
    while True:
        try:
            detected = scanner.get_detected_items()
            current_ids = {r["item_data"]["item_id"] for r in detected if r["item_data"]}
            
            # If we found new items or something changed, broadcast
            if current_ids != last_detected and current_ids:
                data = []
                for r in detected:
                    if r["item_data"]:
                        data.append({
                            "item_id": r["item_data"]["item_id"],
                            "product_name": r["item_data"]["product_name"],
                            "alerts": r["alerts"],
                            "qr_data": r["qr_data"]
                        })
                
                if data:
                    await manager.broadcast(json.dumps({"type": "SCAN_UPDATE", "data": data}))
                last_detected = current_ids
            elif not current_ids and last_detected:
                last_detected = set() # cleared
            
            await asyncio.sleep(0.5) # Check every 500ms
        except Exception as e:
            logger.error(f"Broadcast error: {e}")
            await asyncio.sleep(1)

# ── API Routes ───────────────────────────────────────────────────────────────

@app.get("/")
async def root():
    return {"status": "ok", "message": "SmartStock AI Vision API is running"}

def gen_frames():
    """Generator for MJPEG stream."""
    while True:
        rgb_frame = scanner.get_current_frame_rgb()
        if rgb_frame is None:
            time.sleep(0.1)
            continue
        
        # Convert RGB back to BGR for encoding
        bgr_frame = cv2.cvtColor(rgb_frame, cv2.COLOR_RGB2BGR)
        ret, buffer = cv2.imencode('.jpg', bgr_frame)
        if not ret:
            continue
            
        frame = buffer.tobytes()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
        time.sleep(0.04) # ~25 FPS

@app.get("/video_feed")
async def video_feed():
    """Video streaming route. Use this in <img> tag's src."""
    return StreamingResponse(gen_frames(),
                             media_type='multipart/x-mixed-replace; boundary=frame')

@app.websocket("/ws/scan")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            # We don't expect messages from client, but we must keep connection alive
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
