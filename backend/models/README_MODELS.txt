YOLOv8 Nano Model Weights
==========================

The SmartStock scanner can use YOLOv8 Nano (yolov8n.pt) as a region proposer
to speed up and improve multi-QR code detection.

HOW TO DOWNLOAD:
  Run `python setup.py` and it will auto-download the weights (~6MB).

  OR manually download from:
  https://github.com/ultralytics/assets/releases/download/v0.0.0/yolov8n.pt

  Place the file as: models/yolov8n.pt

FALLBACK:
  If yolov8n.pt is not present, the application automatically falls back
  to pure OpenCV QR detection (cv2.QRCodeDetectorAruco). This still works
  for most use cases — YOLO just improves accuracy on small/distant QR codes.

NO INTERNET REQUIRED AFTER FIRST DOWNLOAD.
