"""
core/scanner.py
InventoryScanner — multi-QR OpenCV scanner with optional YOLO assist.
"""

import logging
import threading
import time
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)


class InventoryScanner:
    """Live webcam scanner that detects and decodes multiple QR codes per frame."""

    def __init__(self, db_manager, alert_manager=None, camera_index: int = 0):
        """
        Initialize the webcam scanner.

        Args:
            db_manager: DatabaseManager instance for item lookups.
            alert_manager: AlertManager instance for real-time alert checking.
            camera_index: OpenCV camera index (usually 0 for built-in webcam).
        """
        self.db = db_manager
        self.alert_manager = alert_manager
        self.camera_index = camera_index
        self.cap = None
        self.running = False
        self._frame_lock = threading.Lock()
        self._current_frame = None
        self._detected_items = []
        self._session_items = {}   # item_id -> item dict, across entire session
        self._fps = 0.0
        self.yolo_model = None
        self._try_load_yolo()

        # Try to initialize QRCodeDetectorAruco (multi-QR, OpenCV 4.8+)
        try:
            import cv2
            self._qr_detector = cv2.QRCodeDetectorAruco()
            self._use_aruco = True
            logger.info("Using cv2.QRCodeDetectorAruco for multi-QR detection.")
        except AttributeError:
            try:
                import cv2
                self._qr_detector = cv2.QRCodeDetector()
                self._use_aruco = False
                logger.info("Falling back to cv2.QRCodeDetector (single/multi QR).")
            except Exception as e:
                logger.error(f"Could not initialize QR detector: {e}")
                self._qr_detector = None
                self._use_aruco = False

    def _try_load_yolo(self):
        """Attempt to load YOLOv8 Nano model for QR region pre-detection."""
        model_path = Path("models") / "yolov8n.pt"
        try:
            from ultralytics import YOLO
            if model_path.exists():
                self.yolo_model = YOLO(str(model_path))
                logger.info("YOLOv8 Nano model loaded successfully.")
            else:
                logger.info("YOLOv8 model not found — using OpenCV-only mode.")
        except Exception as e:
            logger.info(f"YOLO not available: {e} — using OpenCV-only mode.")

    def open_camera(self) -> bool:
        """
        Open the webcam. Returns True on success, False on failure.

        Returns:
            True if camera opened successfully.
        """
        try:
            import cv2
            self.cap = cv2.VideoCapture(self.camera_index)
            if not self.cap.isOpened():
                logger.error(f"Could not open camera index {self.camera_index}")
                return False
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
            self.cap.set(cv2.CAP_PROP_FPS, 30)
            logger.info("Camera opened successfully.")
            return True
        except Exception as e:
            logger.error(f"Camera open error: {e}")
            return False

    def preprocess_frame(self, frame):
        """
        Apply preprocessing to improve QR detection in poor lighting.

        Steps: grayscale → sharpening → adaptive thresholding → CLAHE.

        Args:
            frame: OpenCV BGR image array.

        Returns:
            Preprocessed grayscale image.
        """
        import cv2
        import numpy as np

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        # Sharpening kernel
        kernel = np.array([[0, -1, 0], [-1, 5, -1], [0, -1, 0]], dtype=np.float32)
        sharpened = cv2.filter2D(gray, -1, kernel)

        # CLAHE for local contrast enhancement
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        enhanced = clahe.apply(sharpened)

        return enhanced

    def detect_and_decode_all_qr(self, frame) -> list:
        """
        Detect and decode all QR codes in a frame.

        Args:
            frame: OpenCV BGR image array.

        Returns:
            List of dicts: {qr_data, bounding_box_points, item_data, alerts}.
        """
        import cv2
        import numpy as np

        results = []
        if self._qr_detector is None:
            return results

        preprocessed = self.preprocess_frame(frame)

        decoded_texts = []
        points_list = []

        # ── Try ARUCO-based multi-QR detector ──────────────────────────────
        if self._use_aruco:
            try:
                retval, decoded_info, points, _ = self._qr_detector.detectAndDecodeMulti(
                    preprocessed
                )
                if retval and decoded_info:
                    for i, text in enumerate(decoded_info):
                        if text:
                            decoded_texts.append(text)
                            pts = points[i] if points is not None and i < len(points) else None
                            points_list.append(pts)
            except Exception as e:
                logger.debug(f"Aruco detector error: {e}")

        # ── Fallback to standard QRCodeDetector ───────────────────────────
        if not decoded_texts:
            try:
                fallback = cv2.QRCodeDetector()
                retval, decoded_info, points, _ = fallback.detectAndDecodeMulti(preprocessed)
                if retval and decoded_info:
                    for i, text in enumerate(decoded_info):
                        if text:
                            decoded_texts.append(text)
                            pts = points[i] if points is not None and i < len(points) else None
                            points_list.append(pts)
            except Exception as e:
                logger.debug(f"Fallback QR detector error: {e}")

        # ── YOLO region proposals ─────────────────────────────────────────
        if self.yolo_model and not decoded_texts:
            try:
                yolo_results = self.yolo_model(frame, verbose=False, conf=0.4)
                fallback = cv2.QRCodeDetector()
                for result in yolo_results:
                    if result.boxes is None:
                        continue
                    for box in result.boxes:
                        x1, y1, x2, y2 = map(int, box.xyxy[0].tolist())
                        crop = preprocessed[max(0, y1):y2, max(0, x1):x2]
                        if crop.size == 0:
                            continue
                        crop_up = cv2.resize(crop, (200, 200))
                        text, pts, _ = fallback.detectAndDecode(crop_up)
                        if text:
                            decoded_texts.append(text)
                            # Map points back to original frame coords
                            if pts is not None:
                                scale_x = (x2 - x1) / 200
                                scale_y = (y2 - y1) / 200
                                mapped = pts.reshape(-1, 2)
                                mapped[:, 0] = mapped[:, 0] * scale_x + x1
                                mapped[:, 1] = mapped[:, 1] * scale_y + y1
                                points_list.append(mapped.astype(np.float32))
                            else:
                                points_list.append(None)
            except Exception as e:
                logger.debug(f"YOLO region proposal error: {e}")

        # ── Build result list ─────────────────────────────────────────────
        for i, qr_text in enumerate(decoded_texts):
            qr_text = qr_text.strip()
            if not qr_text:
                continue
            bbox = points_list[i] if i < len(points_list) else None
            item_data = self.db.get_item_by_qr(qr_text)
            alerts = []
            if item_data and self.alert_manager:
                alerts = self.alert_manager.get_alerts_for_item(item_data)
            results.append({
                "qr_data": qr_text,
                "bounding_box_points": bbox,
                "item_data": item_data,
                "alerts": alerts,
            })
            if item_data:
                self._session_items[item_data["item_id"]] = item_data

        return results

    def draw_overlays(self, frame, qr_results: list):
        """
        Draw colored bounding boxes and text overlays on the frame.

        Args:
            frame: OpenCV BGR image (modified in place).
            qr_results: List of dicts from detect_and_decode_all_qr.

        Returns:
            Annotated frame.
        """
        import cv2
        import numpy as np

        for result in qr_results:
            item = result["item_data"]
            alerts = result["alerts"]
            bbox = result["bounding_box_points"]
            qr_data = result["qr_data"]

            # Determine color based on alert severity
            alert_types = [a["alert_type"] for a in alerts]
            if "EXPIRED" in alert_types or "OUT_OF_STOCK" in alert_types:
                color = (0, 0, 255)      # RED (BGR)
            elif "EXPIRING_SOON" in alert_types:
                color = (0, 165, 255)    # ORANGE
            elif "LOW_STOCK" in alert_types:
                color = (0, 255, 255)    # YELLOW
            elif item:
                color = (0, 255, 0)      # GREEN
            else:
                color = (255, 0, 255)    # PURPLE for unknown

            # Draw bounding polygon
            if bbox is not None:
                try:
                    pts = bbox.reshape(-1, 1, 2).astype(np.int32)
                    cv2.polylines(frame, [pts], isClosed=True, color=color, thickness=2)
                    x_min = int(bbox[:, 0].min())
                    y_min = int(bbox[:, 1].min())
                    y_max = int(bbox[:, 1].max())
                except Exception:
                    x_min, y_min, y_max = 50, 50, 80

            else:
                x_min, y_min, y_max = 50, 50, 80

            # Label text
            if item:
                label = item["product_name"][:30]
                alert_icons = " ".join(
                    ["☠" if a["alert_type"] == "EXPIRED" else
                     "⚠" if a["alert_type"] == "EXPIRING_SOON" else
                     "!" for a in alerts]
                )
                if alert_icons:
                    label = f"{label} {alert_icons}"
            else:
                label = f"UNKNOWN: {qr_data[:20]}"

            # Background rectangle behind text
            (text_w, text_h), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.55, 1)
            text_x, text_y = x_min, max(y_min - 8, 14)
            cv2.rectangle(
                frame,
                (text_x, text_y - text_h - 3),
                (text_x + text_w + 4, text_y + 3),
                color,
                -1,
            )
            cv2.putText(
                frame,
                label,
                (text_x + 2, text_y),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.55,
                (0, 0, 0),
                1,
                cv2.LINE_AA,
            )

            # Alert sub-label below bounding box
            for j, al in enumerate(alerts[:2]):
                sub = al["alert_type"].replace("_", " ")
                cv2.putText(
                    frame,
                    sub,
                    (x_min, y_max + 16 + j * 16),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.45,
                    color,
                    1,
                    cv2.LINE_AA,
                )

        # ── HUD overlays ──────────────────────────────────────────────────
        # QR counter (top-left)
        count_str = f"QR Codes Detected: {len(qr_results)}"
        cv2.putText(frame, count_str, (10, 24),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.65, (255, 255, 255), 2)

        # Timestamp (top-right)
        ts = datetime.now().strftime("%Y-%m-%d  %H:%M:%S")
        (ts_w, _), _ = cv2.getTextSize(ts, cv2.FONT_HERSHEY_SIMPLEX, 0.50, 1)
        cv2.putText(frame, ts, (frame.shape[1] - ts_w - 8, 24),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.50, (200, 200, 200), 1)

        # FPS (bottom-left)
        fps_str = f"FPS: {self._fps:.1f}"
        cv2.putText(frame, fps_str, (10, frame.shape[0] - 10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.55, (180, 180, 180), 1)

        return frame

    def get_current_frame_rgb(self):
        """
        Return the latest annotated frame as RGB numpy array (for Tkinter display).

        Returns:
            RGB numpy array or None.
        """
        with self._frame_lock:
            return self._current_frame.copy() if self._current_frame is not None else None

    def get_detected_items(self) -> list:
        """Return items detected in the current camera frame."""
        return list(self._detected_items)

    def get_session_items(self) -> list:
        """Return all unique items detected in the entire scan session."""
        return list(self._session_items.values())

    def start_capture_thread(self):
        """Start the background camera capture thread."""
        self.running = True
        self._session_items = {}
        thread = threading.Thread(target=self._capture_loop, daemon=True)
        thread.start()
        logger.info("Camera capture thread started.")

    def _capture_loop(self):
        """Background loop: capture frames, detect QR codes, update state."""
        try:
            import cv2
            import numpy as np
        except ImportError:
            logger.error("OpenCV not available")
            self.running = False
            return

        prev_time = time.time()

        while self.running:
            if self.cap is None or not self.cap.isOpened():
                time.sleep(0.1)
                continue

            ret, frame = self.cap.read()
            if not ret:
                time.sleep(0.03)
                continue

            # Detect QR codes
            qr_results = self.detect_and_decode_all_qr(frame)
            self._detected_items = qr_results

            # Draw overlays
            annotated = self.draw_overlays(frame.copy(), qr_results)

            # Convert to RGB for Tkinter
            rgb_frame = cv2.cvtColor(annotated, cv2.COLOR_BGR2RGB)

            with self._frame_lock:
                self._current_frame = rgb_frame

            # FPS calculation
            now = time.time()
            elapsed = now - prev_time
            if elapsed > 0:
                self._fps = 1.0 / elapsed
            prev_time = now

            time.sleep(0.001)  # Yield CPU

    def take_snapshot(self, output_dir: str = "reports") -> Path:
        """
        Save the current annotated frame as a PNG snapshot.

        Args:
            output_dir: Directory to save the snapshot in.

        Returns:
            Path to the saved snapshot file.
        """
        import cv2
        import numpy as np

        frame = self.get_current_frame_rgb()
        if frame is None:
            raise RuntimeError("No frame available to snapshot.")

        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        file_path = output_path / f"snapshot_{ts}.png"

        # Convert RGB back to BGR for imwrite
        bgr = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
        cv2.imwrite(str(file_path), bgr)
        logger.info(f"Snapshot saved: {file_path}")
        return file_path

    def scan_single_qr_from_image(self, image_path: str) -> list:
        """
        Decode QR codes from a saved image file.

        Args:
            image_path: Path to the image file.

        Returns:
            List of result dicts (same format as detect_and_decode_all_qr).
        """
        import cv2

        img = cv2.imread(str(image_path))
        if img is None:
            raise FileNotFoundError(f"Image not found: {image_path}")
        return self.detect_and_decode_all_qr(img)

    def release(self):
        """Stop capture and release camera resources."""
        self.running = False
        time.sleep(0.2)
        if self.cap:
            self.cap.release()
            self.cap = None
        logger.info("Camera released.")
