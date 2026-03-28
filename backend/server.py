"""
server.py
FastAPI server to expose SmartStock AI Vision capabilities to the Next.js frontend.
"""

import cv2
import logging
import asyncio
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Body, HTTPException, Query
from fastapi.responses import StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path
import threading
import json
import time
import sys
from pydantic import BaseModel
from typing import Optional

# Add project root to path so imports work
sys.path.insert(0, str(Path(__file__).parent))

from core.database import DatabaseManager
from core.scanner import InventoryScanner
from core.alerts import AlertManager
from core.qr_generator import QRGenerator

# ── Logging ──────────────────────────────────────────────────────────────────
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("smartstock-server")

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
qr_gen = QRGenerator(output_dir="labels")

# Serve labels as static files
labels_path = Path("labels")
labels_path.mkdir(parents=True, exist_ok=True)
app.mount("/labels", StaticFiles(directory="labels"), name="labels")

# Track connected clients for WebSocket
class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        # Send initial confirmation
        try:
            await websocket.send_text(json.dumps({"type": "CONNECTED", "server": "SmartStock AI"}))
        except Exception:
            pass

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast(self, message: str):
        # Create a copy of the list for iteration in case we modify it while broadcasting
        for connection in list(self.active_connections):
            try:
                await connection.send_text(message)
            except Exception as e:
                logger.warning(f"Failed to send to a websocket, removing: {e}")
                self.disconnect(connection)

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
    counter = 0
    while True:
        try:
            detected = scanner.get_detected_items()
            current_ids = {r["item_data"]["item_id"] for r in detected if r["item_data"]}
            
            # 1. Update detections if changed
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
                # Clear detections on clients
                await manager.broadcast(json.dumps({"type": "SCAN_UPDATE", "data": []}))
                last_detected = set() # cleared
            
            # 2. Heartbeat every 10 iterations (~5 seconds) to keep things alive
            counter += 1
            if counter >= 10:
                await manager.broadcast(json.dumps({"type": "HEARTBEAT", "ts": time.time()}))
                counter = 0
            
            await asyncio.sleep(0.5) # Check every 500ms
        except Exception as e:
            logger.error(f"Broadcast error: {e}")
            await asyncio.sleep(1)

# ── API Routes ───────────────────────────────────────────────────────────────

@app.get("/")
async def root():
    return {"status": "ok", "message": "SmartStock AI Vision API is running"}

class ItemCreate(BaseModel):
    product_name: str
    category: str
    supplier_name: str
    batch_number: str
    unit_of_measure: str
    quantity: int
    min_stock_level: int
    shelf_location: str
    entry_date: str
    expiry_date: Optional[str] = None
    manufacture_date: Optional[str] = None
    unit_price: Optional[float] = 0.0
    notes: Optional[str] = ""

@app.post("/items")
async def create_item(item: ItemCreate, print_label: bool = False):
    """Create a new item, generate QR label, and optionally print."""
    try:
        # 1. Add to database
        item_dict = item.dict()
        item_id = db.add_item(item_dict)
        
        # 2. Generate QR Label
        label_path = qr_gen.generate_qr(
            item_id=item_id,
            qr_data=item_id,
            product_name=item.product_name,
            expiry_date=item.expiry_date,
            shelf_location=item.shelf_location,
            batch_number=item.batch_number
        )
        
        # 3. Print if requested
        if print_label:
            qr_gen.print_label(item_id)
            
        return {
            "status": "success",
            "item_id": item_id,
            "label_url": f"/labels/{item_id}.png"
        }
    except Exception as e:
        logger.error(f"Error creating item: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/items")
async def get_items():
    """List all items."""
    return db.get_all_items()

@app.get("/items/{item_id}")
async def get_item(item_id: str):
    """Get item details."""
    item = db.get_item_by_id(item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    return item

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
    uvicorn.run(app, host="0.0.0.0", port=8001)
