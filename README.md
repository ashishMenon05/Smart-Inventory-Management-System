# 📦 SmartStock — AI-Powered Smart Inventory Management System

> A real-time, multi-QR scanning inventory management system built with Python, OpenCV, YOLOv8, and Tkinter. Designed for zero-cost deployment on any laptop or Raspberry Pi.

---

## 🏆 Project Overview

SmartStock is a **fully offline, budget-friendly smart inventory management system** that replaces manual stock counting and single-item barcode scanning with an intelligent camera-based solution. Using a standard webcam, the system can **detect and decode multiple QR codes simultaneously in a single camera frame**, instantly fetching each item's complete profile from a local database and displaying real-time alerts for expired goods, low stock, and misplaced items.

This project was built to solve real problems faced by small warehouses, hospital pharmacies, school labs, retail storerooms, and any organization that manages physical inventory without the budget for expensive RFID systems or enterprise software.

---

## 📋 Table of Contents

1. [The Problem Being Solved](#-the-problem-being-solved)
2. [Why This Solution Is Innovative](#-why-this-solution-is-innovative)
3. [System Architecture](#-system-architecture)
4. [Technology Stack](#-technology-stack)
5. [How Multi-QR Scanning Works](#-how-multi-qr-scanning-works)
6. [How YOLOv8 Is Used](#-how-yolov8-is-used)
7. [Database Design](#-database-design)
8. [Project File Structure](#-project-file-structure)
9. [Features — Full List](#-features--full-list)
10. [Installation Guide](#-installation-guide)
11. [Running the Application](#-running-the-application)
12. [How to Use Each Feature](#-how-to-use-each-feature)
13. [QR Code System Explained](#-qr-code-system-explained)
14. [Alert System Explained](#-alert-system-explained)
15. [The Dashboard — UI Walkthrough](#-the-dashboard--ui-walkthrough)
16. [Report Generation](#-report-generation)
17. [Budget Cost Breakdown](#-budget-cost-breakdown)
18. [Comparison with Traditional Systems](#-comparison-with-traditional-systems)
19. [Known Limitations](#-known-limitations)
20. [Future Scope](#-future-scope)
21. [Team & Credits](#-team--credits)

---

## 🚨 The Problem Being Solved

Inventory management is one of the most repetitive, error-prone, and expensive operations in any organization that handles physical goods. Here is what actually goes wrong in traditional inventory management every single day:

### Problem 1: Items Expire Without Anyone Knowing

In hospitals, pharmacies, school labs, and food storage facilities, items have expiry dates. Traditional systems rely on someone physically checking each label, which almost never happens on schedule. The result: expired medicines get administered, expired food gets consumed, or outdated components get used in products. This is not just a financial loss — it is a safety hazard.

**Real scale of the problem:** The WHO estimates that 25–35% of medicines in developing countries are either expired or substandard. This is directly caused by poor inventory tracking.

### Problem 2: Manual Counting Is Slow, Inaccurate, and Expensive

A person doing manual stock counting walks through a warehouse, looks at each shelf, counts items, and writes numbers down. This process:
- Takes hours or even days in large stores
- Introduces human counting errors (studies show 3–5% error rate in manual counting)
- Cannot be done while the store is operating (requires downtime)
- Gives you data that is already hours old by the time it is recorded

### Problem 3: Single-Item Barcode Scanning Is Inefficient

Most modern systems use handheld barcode scanners that scan one item at a time. While better than manual counting, this still requires:
- A dedicated employee to walk every row
- Scanning each box individually (imagine 500 boxes — that is 500 scans)
- No automation — still 100% dependent on human action
- No proactive alerts — only tells you what is there, not what is wrong

### Problem 4: No Traceability — Where Did This Come From?

When you find a box on a shelf, can you immediately know: who supplied it, when it arrived, what batch it belongs to, and whether it has been flagged before? In most small-to-mid-sized organizations, the answer is no. This lack of traceability causes massive losses during audits, product recalls, and quality control checks.

### Problem 5: No Real-Time Awareness

Traditional inventory gives you a snapshot in time (the last time someone counted). Between counts, stock moves, items expire, and quantities change. Nobody knows in real time. A purchase manager orders 100 units of something that is already sitting in a back warehouse at 200 units because the data is not current. A hospital pharmacy runs out of a critical drug because nobody received the low-stock alert in time.

### Problem 6: High Cost of Existing Smart Solutions

RFID-based smart inventory systems exist, but they cost ₹50,000–₹5,00,000 for hardware (readers, tags, antennas, gateways), plus recurring software licensing fees. This makes them completely inaccessible to small organizations, schools, local pharmacies, and small businesses.

---

## 💡 Why This Solution Is Innovative

SmartStock takes a fundamentally different approach to every problem listed above.

### Innovation 1: Batch Multi-QR Scanning (The Core Idea)

Instead of scanning one item at a time, SmartStock mounts a fixed camera (or uses a handheld phone/webcam) and scans **an entire shelf or pallet in one frame**. In a single camera shot, the system can detect and decode 10, 15, or 20 QR codes simultaneously — each one fetching complete item data from the database in real time. What takes a warehouse worker 30 minutes to scan manually, SmartStock can do in 3 seconds with one camera frame.

### Innovation 2: Proactive Visual Alerting Overlaid on Camera Feed

When the camera is scanning, it does not just read the QR codes — it visually flags problems directly on the live video feed. A box with an expired item gets a bright RED bounding box drawn around it on-screen. An item expiring within 7 days gets an ORANGE box. An item with low stock gets a YELLOW warning overlay. The person monitoring the screen can see at a glance exactly which physical boxes on the shelf need attention, without touching anything or reading any reports.

### Innovation 3: Near-Zero Cost Implementation

QR codes can be generated in Python in milliseconds and printed on plain paper. A printed QR label costs fractions of a rupee. The software is entirely open-source. The only hardware needed is a webcam (₹300–₹1500) or a phone. Compare this to ₹10,000+ per RFID tag in enterprise systems. SmartStock democratizes smart inventory for small organizations.

### Innovation 4: Complete Item Traceability from Day One

Every item in SmartStock has a digital passport encoded in its QR code. The moment a box is received, it is registered with: supplier name, batch number, manufacture date, entry date, expiry date, shelf location, and quantity. Every time that QR is scanned, the scan is logged with a timestamp. Every time quantity changes, a stock movement record is created. You always know the full history of any item in seconds.

### Innovation 5: FIFO Enforcement Through Scan Intelligence

SmartStock can be set to recommend which item to pick first based on entry date and expiry date. When multiple identical products are on the shelf, the system highlights which box should be used first to ensure First In, First Out (FIFO) ordering — a crucial principle in food, medicine, and chemical storage.

### Innovation 6: Works Completely Offline

Unlike cloud-based inventory systems that stop working when the internet goes down, SmartStock stores everything in a local SQLite database. There are no monthly fees, no internet dependency, no cloud vendor lock-in. The entire system runs on the same laptop that runs the application.

---

## 🏗️ System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    SmartStock Application                    │
│                                                             │
│  ┌────────────────────────────────────────────────────────┐ │
│  │                   Tkinter Dashboard UI                  │ │
│  │   ┌──────────┐  ┌──────────┐  ┌──────────┐            │ │
│  │   │Dashboard │  │ Add Item │  │ Reports  │            │ │
│  │   │  Table   │  │   Form   │  │  Panel   │            │ │
│  │   └──────────┘  └──────────┘  └──────────┘            │ │
│  │                 ┌──────────────────┐                   │ │
│  │                 │  Live Scan View  │                   │ │
│  │                 │  (Camera Feed)   │                   │ │
│  │                 └──────────────────┘                   │ │
│  └────────────────────────────────────────────────────────┘ │
│                            │                                 │
│  ┌─────────────────────────▼──────────────────────────────┐ │
│  │                    Core Engine Layer                    │ │
│  │                                                        │ │
│  │  ┌─────────────┐  ┌─────────────┐  ┌───────────────┐  │ │
│  │  │   Scanner   │  │  QR         │  │  Alert        │  │ │
│  │  │   (OpenCV   │  │  Generator  │  │  Manager      │  │ │
│  │  │   + YOLO)   │  │  (qrcode    │  │  (Expiry,     │  │ │
│  │  │             │  │  + Pillow)  │  │  Stock)       │  │ │
│  │  └──────┬──────┘  └──────┬──────┘  └───────┬───────┘  │ │
│  │         │                │                  │          │ │
│  │  ┌──────┴────────────────┴──────────────────┴───────┐  │ │
│  │  │              Database Manager (SQLite)            │  │ │
│  │  │   items | stock_movements | scan_logs |           │  │ │
│  │  │   alerts_log                                      │  │ │
│  │  └──────────────────────────────────────────────────┘  │ │
│  └────────────────────────────────────────────────────────┘ │
│                            │                                 │
│  ┌─────────────────────────▼──────────────────────────────┐ │
│  │                    Data & Output Layer                  │ │
│  │  inventory.db  |  /labels/*.png  |  /reports/*.csv      │ │
│  └────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘

Hardware Layer:
┌──────────────┐     ┌──────────────────┐     ┌─────────────┐
│   Webcam /   │────▶│  Python OpenCV   │────▶│   SQLite    │
│   Phone Cam  │     │  Frame Capture   │     │  Database   │
└──────────────┘     └──────────────────┘     └─────────────┘
```

### Data Flow — From Physical Box to Alert

```
Physical box with printed QR label
         │
         ▼
Camera captures video frame
         │
         ▼
OpenCV converts frame to grayscale + applies preprocessing
         │
         ▼
YOLOv8 detects regions in frame likely containing QR codes
(speeds up decoding, handles far/blurry QR codes better)
         │
         ▼
cv2.QRCodeDetectorAruco decodes ALL QR strings simultaneously
         │
         ▼
For each QR string → DatabaseManager.get_item_by_qr(qr_string)
         │
         ▼
AlertManager checks: Is it expired? Expiring soon? Low stock?
         │
         ▼
OpenCV draws colored overlay on frame (GREEN/ORANGE/RED/YELLOW)
         │
         ▼
Dashboard table updates with detected items
         │
         ▼
Alerts logged to database + displayed in sidebar
         │
         ▼
(Optional) VoiceAlertSystem announces critical alerts
```

---

## 🛠️ Technology Stack

### Python (Core Language)
Python 3.8+ is used as the primary language. Python was chosen because:
- It has the richest ecosystem for computer vision (OpenCV), machine learning (PyTorch/YOLO), and UI development (Tkinter)
- It runs on Windows, macOS, and Linux without modification
- The standard library includes SQLite support, so no extra database installation is needed
- It allows rapid prototyping, which is critical for a student project with a tight timeline

### OpenCV (`opencv-python` and `opencv-contrib-python`)
OpenCV (Open Source Computer Vision Library) is the world's most popular computer vision library, maintained by Intel and the open-source community. Version 4.8+ is used specifically because it includes `cv2.QRCodeDetectorAruco`, which is a significantly improved QR detection engine that supports:
- Detecting multiple QR codes in a single frame simultaneously
- Handling QR codes at various angles (rotated, tilted)
- Handling partial occlusion (boxes partially behind each other)
- Faster processing than the older `cv2.QRCodeDetector`

OpenCV is used in this project for:
- Capturing live video frames from the webcam (`cv2.VideoCapture`)
- Preprocessing frames for better QR detection (thresholding, sharpening, histogram equalization)
- Decoding QR codes (`cv2.QRCodeDetectorAruco.detectAndDecodeMulti`)
- Drawing bounding boxes, text overlays, and color indicators on live video frames
- Converting frames to formats compatible with Tkinter for display in the dashboard

### YOLOv8 Nano (`ultralytics`)
YOLO stands for "You Only Look Once" — it is a state-of-the-art real-time object detection neural network. In this project, YOLOv8 Nano (the smallest, fastest variant) is used as a **pre-processing accelerator** for QR code detection.

Here is the problem it solves: when a QR code is small, far away, or partially blurry in a large frame (say 1920x1080), running the QR decoder on the entire frame is slow and may miss small codes. YOLOv8 first scans the entire frame and identifies the regions that **likely contain QR codes** (by detecting square-like patterns with finder patterns). OpenCV's decoder then only needs to process those small sub-regions, which is much faster and more accurate.

YOLOv8 Nano runs on CPU (no GPU required), making it suitable for standard laptops. It processes frames in real time at 10–30fps depending on the hardware. The model weights file (`yolov8n.pt`) is only 6MB and is downloaded once during setup.

### SQLite (Database)
SQLite is a lightweight, serverless relational database engine that stores everything in a single `.db` file. No database server needs to be installed, configured, or maintained. SQLite is built into Python's standard library, so there is zero additional installation for the database layer.

SQLite was chosen over alternatives for these reasons:
- **vs PostgreSQL/MySQL:** No server to install, no configuration, no port management, works offline — perfect for a self-contained desktop application
- **vs CSV files:** Supports proper SQL queries, indexes, foreign keys, and concurrent access
- **vs JSON files:** Structured, queryable, can handle complex relationships between items, movements, and alerts

The database uses WAL (Write-Ahead Logging) mode for better performance when multiple reads and writes happen simultaneously (scan logging and UI updates happening at the same time).

### Tkinter (Desktop UI)
Tkinter is Python's built-in GUI framework. It comes pre-installed with Python on all platforms. No additional installation is needed. While not as visually polished as Qt or Electron, Tkinter is chosen because:
- Zero additional dependencies
- Runs identically on Windows, macOS, and Linux
- Perfectly sufficient for a data-management desktop application
- Fast startup time
- Full control over custom dark-themed UI via `.configure()` calls

The UI is custom-styled using a dark color palette with accent colors (blue, green, orange, red) to create a professional-looking dashboard that makes the demo impressive.

### qrcode + Pillow (QR Generation and Label Creation)
The `qrcode` library generates QR code matrix data and renders it as a Pillow (PIL) image. Pillow is then used to:
- Add border padding around the QR code
- Overlay text (product name, item ID, expiry date, shelf location)
- Composite multiple label images into a printable A4 sheet
- Save the final label as a PNG file

Error correction level H (High) is used, which means up to 30% of the QR code can be obscured or damaged and it will still decode correctly. This is important for physical labels that may get dirty, folded, or partially torn.

### pyttsx3 (Voice Alerts — Optional)
pyttsx3 is a text-to-speech library that works offline using the operating system's built-in speech engine. On Windows it uses SAPI5, on macOS it uses NSSpeechSynthesizer, and on Linux it uses eSpeak. The voice alert system announces critical alerts (like expired items detected during scan) in the background without blocking the UI.

---

## 🔍 How Multi-QR Scanning Works

This section explains the technical pipeline in detail, step by step.

### Step 1: Frame Capture

The webcam continuously captures video frames at 30fps using `cv2.VideoCapture(0)`. Each frame is a NumPy array with shape `(height, width, 3)` representing pixel values in BGR (Blue-Green-Red) color space. A typical frame from a 720p webcam is `(720, 1280, 3)`.

### Step 2: Preprocessing

Raw camera frames are often not ideal for QR decoding due to:
- Inconsistent lighting (fluorescent flicker, shadows)
- Motion blur from camera movement
- Low contrast on matte surfaces
- Reflections from glossy box surfaces

The preprocessing pipeline applies these transformations in sequence:

**Grayscale Conversion:** Converts the 3-channel BGR frame to single-channel grayscale. QR code detection only needs brightness information, not color.

**Gaussian Blur followed by Sharpening:** A slight Gaussian blur is applied first to reduce noise, then an unsharp mask (the original minus the blurred version, scaled) is applied to sharpen edges. This makes the QR finder patterns more defined.

**Adaptive Thresholding:** Instead of applying a single brightness threshold to the entire image, adaptive thresholding computes a local threshold for each small region of the image. This handles frames where one part of the shelf is bright (near a window) and another part is dark (in shadow) — both regions get correctly binarized.

**CLAHE (Contrast Limited Adaptive Histogram Equalization):** Applied to enhance local contrast, making QR patterns stand out better against similar-colored backgrounds (e.g., a white QR label on a white box).

### Step 3: YOLO Region Proposal (Optional Acceleration)

If YOLOv8 is available and loaded, it processes the full frame and returns a list of bounding boxes where it detected potential QR code regions. These are not decoded yet — YOLO just says "there is probably a QR code in this rectangular area of the frame."

The QR decoder then crops each proposed region from the frame and works on the cropped sub-image, which is much smaller and faster to process. This also allows detection of very small QR codes that might be missed when running the decoder on the full high-resolution frame.

If YOLO is not available or cannot load its weights, the system falls back to running the QR decoder on the full preprocessed frame directly — this still works, just with slightly lower accuracy on very small or distant QR codes.

### Step 4: Multi-QR Decoding

`cv2.QRCodeDetectorAruco.detectAndDecodeMulti(frame)` is called on the preprocessed frame (or sub-regions if YOLO is being used). This function:
- Looks for the three distinctive square finder patterns in the corners of each QR code
- Computes the perspective transform for each detected QR code (to correct rotation/angle)
- Decodes the binary data encoded in the QR matrix
- Returns a tuple: `(retval, decoded_info, points, straight_qrcode)` where:
  - `retval` is True if at least one QR was decoded
  - `decoded_info` is a list of decoded strings, one per QR code
  - `points` is a list of polygon corner coordinates for each QR code

Each entry in `decoded_info` gives the raw string encoded in that QR code (in our case, the item ID like "ITEM-00142").

### Step 5: Database Lookup

For each decoded QR string, `DatabaseManager.get_item_by_qr(qr_string)` is called. This performs a parameterized SQL query:
```sql
SELECT * FROM items WHERE qr_code_data = ?
```
The result is returned as a Python dictionary with all item fields. If no matching item is found (unknown QR code), the system displays an "UNKNOWN ITEM" warning in purple on the frame.

### Step 6: Alert Evaluation

For each retrieved item, `AlertManager.get_alerts_for_item(item)` evaluates:
- Is `expiry_date` in the past? → EXPIRED (critical)
- Is `expiry_date` within the next 7 days? → EXPIRING SOON (warning)
- Is `quantity` <= `min_stock_level`? → LOW STOCK (warning)
- Is `quantity` == 0? → OUT OF STOCK (critical)

This returns a list of alert strings and severity levels.

### Step 7: Visual Overlay Drawing

Using the `points` array from the QR detector and the alert evaluation results, OpenCV draws on the frame:
- `cv2.polylines` draws a polygon connecting the 4 corner points of each QR code
- Color: GREEN if healthy, ORANGE if expiring soon, RED if expired or out of stock, YELLOW if low stock
- `cv2.putText` draws the product name above the bounding polygon
- A filled dark rectangle is drawn behind the text for readability contrast
- Alert icons (⚠, ☠, 📦) are drawn as text overlays near the bounding box

### Step 8: Frame Display

The annotated frame (now containing all the colored overlays) is:
1. Converted from BGR to RGB color space (Tkinter expects RGB)
2. Converted to a Pillow Image
3. Converted to a Tkinter `PhotoImage`
4. Displayed in the scan window's label widget

This happens every 33 milliseconds (~30fps) using Tkinter's `after()` scheduling mechanism, which safely updates the UI from the main thread.

---

## 🤖 How YOLOv8 Is Used

YOLO (You Only Look Once) was originally designed for object detection — identifying objects like people, cars, and dogs in images. In SmartStock, it is used differently: as a **region proposer** that helps the QR decoder work more efficiently.

### The Problem Without YOLO

Imagine a camera looking at a shelf with 15 boxes, each with a small QR label (say 3cm x 3cm). In a 1280x720 frame, each QR code might only be 50x50 pixels — very small relative to the full frame. Running `detectAndDecodeMulti` on the entire 1280x720 frame can miss these small codes or take longer because it has to search the entire image space.

### How YOLO Helps

YOLOv8 Nano is trained to detect objects in real time. Even without a specific QR-code class, we use it to detect rectangular/square regions with high-frequency visual patterns (the characteristic look of QR codes). Alternatively, a YOLO model specifically fine-tuned on QR codes can be used for even better accuracy.

YOLO outputs a list of bounding boxes with confidence scores. For each box above a confidence threshold of 0.4:
1. The corresponding region is cropped from the original frame
2. The crop is upscaled to 200x200 pixels for better decoding
3. Only this small image is passed to the QR decoder

This reduces the QR decoder's search space by 95%+ and significantly improves detection of small/distant/rotated QR codes.

### Running on CPU

YOLOv8 Nano is specifically designed for edge deployment without a GPU. On a standard Intel Core i5 or AMD Ryzen 5 laptop from the last 5 years, YOLOv8 Nano runs at 15–30fps on CPU-only inference. This is fast enough for real-time inventory scanning where the shelf is stationary.

The model weights file is 6MB (yolov8n.pt). It is downloaded once during `setup.py` and cached locally. Subsequent runs use the cached weights with no internet connection needed.

---

## 🗄️ Database Design

SmartStock uses four related SQLite tables that together capture the complete lifecycle of every inventory item.

### Table 1: `items` — The Core Inventory

This is the central table. Every physical box in your inventory has exactly one row in this table. The `item_id` (e.g., "ITEM-00142") is the primary key and is also encoded in the QR code label on the physical box. Key design decisions:

- `qr_code_data` has a UNIQUE constraint, preventing duplicate QR labels from causing confusion
- `status` field allows items to be "archived" (soft-deleted) rather than permanently removed, preserving historical data
- `min_stock_level` is stored per-item (not globally), because different items have different criticality — you might accept having only 2 units of a rarely-used tool, but 0 units of a frequently-used medicine is immediately critical
- `expiry_date` is nullable — non-perishable items like electronics and stationery do not have expiry dates

### Table 2: `stock_movements` — Complete Audit Trail

Every time the quantity of any item changes, a new record is inserted into `stock_movements`. This creates an immutable audit trail. Nobody can change the quantity of an item without the system recording: what the old quantity was, what the new quantity is, what type of change it was (received stock, disposed, sold/used, count correction), and when it happened.

This table answers questions like: "We had 50 units of this medicine last month, we now have 12 — where did 38 go?" The movement log will show every IN and OUT event with timestamps.

### Table 3: `scan_logs` — Every Scan Recorded

Every time a QR code is scanned (whether in a live camera session or a single manual scan), the event is logged. This table records which item was scanned, when, what type of scan it was, and what alerts (if any) were triggered during that scan. This allows generating reports like: "Show me all items that had expiry alerts triggered during scans in March."

### Table 4: `alerts_log` — Alert History and Acknowledgement

Every generated alert is stored here with its type, message, severity, and a timestamp. The `acknowledged` field (0 or 1) tracks which alerts have been seen and dismissed by a user. The dashboard sidebar always shows the count of unacknowledged alerts. When a user clicks "Acknowledge" on an alert, it is marked in this table and removed from the urgent alerts display.

### Database Indexes

The following indexes are created for query performance:
- `idx_items_expiry` on `items(expiry_date)` — makes expiry queries fast
- `idx_items_status` on `items(status)` — makes filtering active vs archived fast
- `idx_items_category` on `items(category)` — makes category filtering fast
- `idx_movements_item` on `stock_movements(item_id)` — makes movement history lookup fast
- `idx_alerts_item` on `alerts_log(item_id)` — makes per-item alert lookup fast
- `idx_alerts_ack` on `alerts_log(acknowledged)` — makes unread alert count fast

---

## 📁 Project File Structure

```
smart_inventory/
│
├── main.py                        # Entry point — run this to start the application
├── requirements.txt               # All Python package dependencies
├── setup.py                       # One-click automated installer and DB seeder
├── README.md                      # This file
│
├── core/                          # Business logic — no UI code here
│   ├── __init__.py                # Makes core a Python package
│   ├── database.py                # All SQLite database operations
│   │                              #   - DatabaseManager class
│   │                              #   - CRUD operations for all 4 tables
│   │                              #   - Stats computation for dashboard
│   │                              #   - Demo data seeding
│   │
│   ├── qr_generator.py            # QR code generation and label printing
│   │                              #   - QRGenerator class
│   │                              #   - Single label generation
│   │                              #   - Batch label generation
│   │                              #   - A4 printable QR sheet generation
│   │
│   ├── scanner.py                 # Computer vision scanning engine
│   │                              #   - InventoryScanner class
│   │                              #   - Live webcam capture loop
│   │                              #   - Multi-QR detection and decoding
│   │                              #   - Frame preprocessing pipeline
│   │                              #   - YOLOv8 integration
│   │                              #   - Visual overlay drawing
│   │
│   ├── alerts.py                  # Alert generation and management
│   │                              #   - AlertManager class
│   │                              #   - Full inventory health check
│   │                              #   - Expiry alert logic
│   │                              #   - Stock level alert logic
│   │                              #   - Alert message formatting
│   │
│   ├── reports.py                 # Report generation
│   │                              #   - ReportGenerator class
│   │                              #   - CSV exports (full, expiry, movements)
│   │                              #   - Text summary reports
│   │                              #   - Scan session reports
│   │
│   └── voice.py                   # Optional voice alert system
│                                  #   - VoiceAlertSystem class
│                                  #   - Background text-to-speech
│                                  #   - Scan completion announcements
│
├── ui/                            # All Tkinter UI code
│   ├── __init__.py                # Makes ui a Python package
│   ├── styles.py                  # Theme constants (colors, fonts, padding)
│   ├── dashboard.py               # Main application window (1280x800)
│   │                              #   - Navigation bar
│   │                              #   - Stats sidebar
│   │                              #   - Alerts sidebar
│   │                              #   - Inventory table (sortable, filterable)
│   │                              #   - Auto-refresh logic
│   │
│   ├── add_item_form.py           # New item registration form
│   │                              #   - All input fields with validation
│   │                              #   - QR preview on save
│   │                              #   - Success popup with generated label
│   │
│   ├── item_detail_view.py        # Item detail popup window
│   │                              #   - QR code image display
│   │                              #   - All item fields
│   │                              #   - Quantity adjustment dialog
│   │                              #   - Edit and archive actions
│   │
│   ├── scan_window.py             # Live scan window
│   │                              #   - Real-time camera feed display
│   │                              #   - Detected items table
│   │                              #   - Snapshot and report buttons
│   │
│   └── report_window.py           # Report generation interface
│                                  #   - Report type selection
│                                  #   - Preview panel
│                                  #   - Open in file explorer
│
├── data/
│   ├── inventory.db               # SQLite database file (auto-created)
│   └── sample_data.sql            # Raw SQL for the 15 demo items
│
├── labels/                        # Generated QR label PNG images
│   └── (auto-populated)           # e.g., ITEM-00001.png, ITEM-00002.png, ...
│
├── reports/                       # Generated report files
│   └── (auto-populated)           # e.g., inventory_20260327_143022.csv
│
├── models/
│   └── README_MODELS.txt          # Instructions for YOLO model download
│
└── assets/
    ├── logo.png                   # Application logo
    └── alert_sound.wav            # Alert notification sound
```

---

## ✨ Features — Full List

### Inventory Management
- ✅ Add new inventory items with complete metadata (name, category, supplier, batch, dates, location, quantity, price)
- ✅ Edit existing item details
- ✅ Soft-delete (archive) items without losing history
- ✅ Adjust stock quantities with reason tracking (received, disposed, sold, corrected)
- ✅ View complete stock movement history per item
- ✅ Search inventory by any text field in real time
- ✅ Filter inventory by category
- ✅ Sort inventory table by any column

### QR Code System
- ✅ Auto-generate QR codes when adding new items
- ✅ QR labels include: product name, item ID, expiry date, shelf location as human-readable text
- ✅ Batch QR generation for multiple items at once
- ✅ Generate printable A4 PDF sheet with grid of QR labels
- ✅ Open label images for printing via system default viewer
- ✅ Error correction level H (up to 30% damage tolerance)

### Live Scanning
- ✅ Open live webcam scan window from dashboard
- ✅ Detect and decode multiple QR codes simultaneously in one camera frame
- ✅ Real-time colored bounding boxes on detected QR codes (green/orange/red/yellow)
- ✅ Product name overlay on each detected QR code in the live frame
- ✅ Live detection counter, FPS display, and timestamp overlay
- ✅ Keyboard shortcut to save annotated snapshot (press 'S')
- ✅ Session report generation from all items seen in one scan session
- ✅ Scan log automatically written to database
- ✅ Scan image file support (scan from saved photo, not just live camera)

### Alert System
- ✅ EXPIRED alerts — critical, red — items past their expiry date
- ✅ EXPIRING SOON alerts — warning, orange — items expiring within 7 days
- ✅ LOW STOCK alerts — warning, yellow — items at or below minimum stock level
- ✅ OUT OF STOCK alerts — critical, red — items with zero quantity
- ✅ Full inventory health check button (scans entire DB, not just scanned items)
- ✅ Alert history log with timestamps
- ✅ Alert acknowledgement (mark as read)
- ✅ Unacknowledged alert counter badge in sidebar
- ✅ Voice announcements for critical alerts (optional)

### Dashboard
- ✅ Dark-themed professional UI
- ✅ Live stats sidebar: total items, categories, expiring soon, expired, low stock
- ✅ Color-coded inventory table rows (red=expired, orange=expiring, yellow=low stock, green=healthy)
- ✅ Auto-refresh every 30 seconds
- ✅ Live clock in navigation bar
- ✅ Quick-access buttons for all major functions
- ✅ Right-click context menu on inventory table rows

### Reports
- ✅ Full inventory export to CSV
- ✅ Expiry-focused report CSV (expired + expiring soon, sorted by urgency)
- ✅ Stock movement history CSV (configurable date range)
- ✅ Text summary report (counts, category breakdown, top items by value)
- ✅ Scan session report (items detected and alerts during a specific scan)
- ✅ Report preview in the UI before saving
- ✅ Open generated reports in system file explorer

---

## 🚀 Installation Guide

### Prerequisites

Before installing SmartStock, make sure the following are available on your system:

- **Python 3.8 or newer** — check by running `python --version` in terminal. Download from https://python.org if needed.
- **pip** — Python's package installer, comes bundled with Python 3.4+
- **A webcam** — built-in laptop webcam or USB webcam. The application also works with an IP camera (phone running IP Webcam app)
- **At least 2GB free disk space** — for Python packages, YOLO model weights, and the application itself
- **Windows 10/11, macOS 10.14+, or Ubuntu 18.04+** — all are fully supported

### Method 1: Automated Setup (Recommended)

This is the easiest method. One command does everything:

```bash
# Step 1: Download or clone the project
git clone https://github.com/your-team/smartstock.git
cd smartstock

# Step 2: Run the automated setup script
python setup.py
```

The `setup.py` script will:
1. Verify your Python version
2. Upgrade pip to the latest version
3. Install all required packages from `requirements.txt`
4. Create the necessary folders (`data/`, `labels/`, `reports/`, `models/`)
5. Initialize the SQLite database with all tables and indexes
6. Download YOLOv8 Nano model weights (~6MB, downloaded once)
7. Seed the database with 15 demo items across 5 categories
8. Generate QR code labels for all 15 demo items
9. Print a success message

Total setup time: approximately 2–5 minutes depending on internet speed (for package downloads).

After setup completes, you will see:
```
✅ Setup complete! SmartStock is ready to use.
Run: python main.py
```

### Method 2: Manual Setup

If you prefer to install dependencies manually:

```bash
# Create a virtual environment (optional but recommended)
python -m venv venv

# Activate the virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Initialize the database and seed demo data
python -c "from core.database import DatabaseManager; db = DatabaseManager('data/inventory.db'); db.seed_demo_data(); print('Database ready!')"

# Generate QR labels for demo items
python -c "
from core.database import DatabaseManager
from core.qr_generator import QRGenerator
db = DatabaseManager('data/inventory.db')
qr = QRGenerator('labels/')
items = db.get_all_items()
for item in items:
    qr.generate_qr(item['item_id'], item['qr_code_data'], item['product_name'], item['expiry_date'], item['shelf_location'], item['batch_number'])
print('QR labels generated!')
"
```

### Package Details — What Gets Installed and Why

| Package | Version | Purpose |
|---|---|---|
| `opencv-python` | ≥ 4.8.0 | Core computer vision: camera capture, image processing |
| `opencv-contrib-python` | ≥ 4.8.0 | Extended OpenCV with QRCodeDetectorAruco for multi-QR support |
| `Pillow` | ≥ 10.0.0 | Image manipulation for QR label generation and camera feed display |
| `qrcode[pil]` | ≥ 7.4.2 | QR code matrix generation |
| `ultralytics` | ≥ 8.0.0 | YOLOv8 object detection for QR region proposal |
| `pyttsx3` | ≥ 2.90 | Offline text-to-speech for voice alerts |
| `numpy` | ≥ 1.24.0 | Numerical arrays for image processing (OpenCV dependency) |

Note: `sqlite3` and `tkinter` are built into Python and require no separate installation.

### Troubleshooting Common Installation Issues

**Issue: `tkinter` not found on Linux**
```bash
# Ubuntu/Debian:
sudo apt-get install python3-tk
# Fedora:
sudo dnf install python3-tkinter
```

**Issue: `pyttsx3` fails on Linux**
```bash
sudo apt-get install espeak espeak-data libespeak-dev
```

**Issue: Camera not detected (cv2.VideoCapture fails)**
```bash
# Test camera index 0, 1, 2:
python -c "import cv2; cap = cv2.VideoCapture(0); print(cap.isOpened())"
# If False, try index 1: cv2.VideoCapture(1)
```

**Issue: YOLO model download fails (no internet)**
- The application automatically falls back to OpenCV-only QR detection if YOLO is unavailable
- You can manually place the `yolov8n.pt` file in the `models/` directory
- Download it from: https://github.com/ultralytics/assets/releases/download/v0.0.0/yolov8n.pt

---

## ▶️ Running the Application

```bash
# Make sure you are in the project directory
cd smartstock

# Run the application
python main.py
```

The application window will open (1280x800 pixels) with the dark-themed dashboard. On first run, you will see the 15 pre-seeded demo items populated in the inventory table. Several items will already show alert indicators (expired items in red, expiring soon in orange, low stock in yellow) to demonstrate the alert system immediately.

### Running in Demo Mode

The application automatically enters "demo mode" on first launch because the database is pre-seeded with items that have intentionally varied conditions. You do not need a real webcam for the demo — you can print the QR labels from the `labels/` folder, hold them up to any camera, and the system will scan and identify them in real time.

---

## 📖 How to Use Each Feature

### Adding a New Item

1. Click "➕ Add Item" in the navigation bar
2. Fill in all required fields in the form:
   - Product Name (required)
   - Category — select from dropdown
   - Supplier Name (required)
   - Batch Number (required)
   - Unit of Measure — select from dropdown
   - Quantity (required, must be a non-negative integer)
   - Minimum Stock Level — the threshold for low stock alerts
   - Shelf Location — use the format "Rack-X, Row-Y, Slot-Z" for consistency
   - Entry Date — defaults to today
   - Expiry Date — leave blank for non-perishable items
   - Unit Price — optional, used for value calculations in reports
3. Click "💾 Save & Generate QR"
4. A success popup appears with:
   - The generated QR label image preview
   - The assigned Item ID
   - A "Print Label" button to print and attach to the physical box
5. The item immediately appears in the main inventory table

### Scanning Items

**Live Camera Scan:**
1. Click "📷 Scan" in the navigation bar
2. Click "START LIVE SCAN"
3. The scan window opens with the live camera feed
4. Hold QR-labeled boxes in front of the camera (or point the camera at a shelf)
5. Detected items automatically appear in the "Detected Items" table below the camera feed
6. Colored bounding boxes appear on the video feed:
   - 🟢 GREEN = item is healthy (in stock, not expired)
   - 🟠 ORANGE = item is expiring within 7 days
   - 🔴 RED = item has expired or is out of stock
   - 🟡 YELLOW = item is low on stock
7. Press 'S' on the keyboard to save an annotated snapshot
8. Click "Stop Scan" when done
9. A summary of the scan session appears

**Scan from Image:**
1. Click "📷 Scan" then "Scan from Image"
2. Browse and select a photo containing QR codes
3. The system decodes all QR codes in the image and shows results

### Adjusting Stock Quantities

1. Click any item in the inventory table to open the Item Detail window
2. Click "Adjust Quantity"
3. A dialog appears showing the current quantity
4. Enter the adjustment (positive = adding stock, negative = removing stock)
5. Select the reason: Received Stock, Disposed, Sold/Used, Stock Count Correction
6. Click Confirm
7. The new quantity is saved, and a stock movement record is created automatically

### Generating Reports

1. Click "📋 Reports" in the navigation bar
2. Choose the report type:
   - **Full Inventory CSV** — all items with all details
   - **Expiry Report CSV** — only expired and expiring-soon items, sorted by urgency
   - **Stock Movement CSV** — all quantity changes in a date range
   - **Text Summary** — a human-readable summary with statistics
3. Click the generate button
4. The report content is previewed in the panel below
5. Click "📂 Open File" to open the saved file in your file manager

---

## 📌 QR Code System Explained

### What Is Encoded in Each QR Code

Each QR code encodes only one piece of information: the **Item ID** (e.g., `ITEM-00142`). This is intentionally minimal — the QR code is just a key to the database record. All the actual item data lives in the database. This approach has several advantages:

- If item details change (new supplier, new batch, updated quantity), the QR label on the physical box does not need to be reprinted — only the database record is updated
- The QR code stays small and easy to scan, because it encodes very little data
- The system works even if the label is partially damaged, because the QR error correction can recover from up to 30% data loss (Error Correction Level H)

### QR Label Layout

Each printed label (400x300 pixels PNG) contains:
```
┌──────────────────────────────┐
│    [PRODUCT NAME IN BOLD]    │
│                              │
│       ┌──────────────┐       │
│       │              │       │
│       │   QR CODE    │       │
│       │              │       │
│       └──────────────┘       │
│                              │
│       ITEM-00142             │
│       Exp: 2026-03-31        │
│       Rack-1, Row-A          │
└──────────────────────────────┘
```

### How to Attach Labels to Boxes

1. Print the label PNG on standard paper (A4 works fine)
2. Cut around the label border
3. Attach to the box using transparent tape or a self-adhesive label sheet
4. Make sure the QR code is unobstructed — do not put tape over the QR code itself
5. For better durability, use glossy label paper or laminate the printed label

### The Printable QR Sheet

The "Generate QR Sheet" function creates a single A4 PDF with a grid of labels — 3 columns, multiple rows — so you can print and cut multiple labels at once. This is the most practical workflow for initially labeling a large inventory: register all items in the system, generate the QR sheet, print it once, cut, and attach.

---

## 🔔 Alert System Explained

### Alert Types and Severity Levels

| Alert Type | Severity | Color | Trigger Condition |
|---|---|---|---|
| EXPIRED | CRITICAL | 🔴 Red | Current date > Expiry date |
| EXPIRING_SOON | WARNING | 🟠 Orange | Expiry date within next 7 days |
| LOW_STOCK | WARNING | 🟡 Yellow | Quantity ≤ Min Stock Level |
| OUT_OF_STOCK | CRITICAL | 🔴 Red | Quantity = 0 |

### When Alerts Are Generated

Alerts are generated in three situations:

1. **During Live Scan** — every time a QR code is decoded and the item data is fetched, the alert conditions are evaluated immediately. If the item being scanned has an issue, the bounding box color changes instantly on screen.

2. **During Full Inventory Check** — when the user clicks "Run Full Check" in the sidebar, the system scans every item in the database (not just the ones being physically scanned) and generates alerts for all items that meet any alert condition.

3. **On Application Startup** — every time `main.py` is run, a quick inventory check is performed automatically and new alerts are logged.

### Alert Acknowledgement Workflow

New alerts appear in the sidebar with a colored badge. The sidebar shows the 5 most recent unacknowledged alerts. A counter badge in the sidebar header shows the total count of unacknowledged alerts.

To acknowledge an alert: click the alert in the sidebar, then click "Acknowledge". The alert is marked as read and the counter decreases. Acknowledged alerts are not deleted — they remain in the `alerts_log` table for audit purposes — they just no longer appear in the urgent sidebar.

### Voice Alerts

If pyttsx3 is installed and working, critical alerts (EXPIRED and OUT_OF_STOCK) trigger voice announcements. When the scanner detects an expired item, the system says: "Warning. [Product Name] has expired. Please remove immediately." This allows the person operating the scanner to receive alerts without looking at the screen.

---

## 🖥️ The Dashboard — UI Walkthrough

### Navigation Bar (Top)
The dark navigation bar spans the full width of the window. On the left: the SmartStock logo and app name. In the center: four navigation buttons for Dashboard, Scan, Add Item, and Reports. On the right: a live clock updating every second.

### Stats Sidebar (Left)
Five stat cards provide at-a-glance inventory health. Each card shows an icon, a label, and a large number. The numbers for "Expiring Soon" and "Expired" and "Low Stock" are colored (orange, red, yellow respectively) when non-zero, making problem situations immediately visible.

Below the stat cards is the Alerts panel showing the last 5 unacknowledged alerts as compact rows, each color-coded by severity. At the bottom of the sidebar is the "Run Full Check" button.

### Inventory Table (Main Area)
A scrollable table with these columns:
- **Item ID** — the unique identifier
- **Product Name** — full product name
- **Category** — category badge
- **Quantity** — current stock count with unit
- **Expiry Date** — formatted date, or "N/A" for non-perishables
- **Location** — shelf location string
- **Status** — active / expiring soon / expired / low stock (shown as colored badge)

Row colors:
- Red background — expired items
- Orange background — expiring within 7 days
- Yellow background — low stock items
- Default background — healthy items

Above the table: a search bar and a category filter dropdown. Below the table: a status bar showing "Showing X of Y items".

---

## 📊 Report Generation

### Full Inventory CSV

Exports a CSV file with all columns from the `items` table for all non-archived items. Columns: Item ID, Product Name, Category, Supplier Name, Batch Number, Unit, Quantity, Min Stock Level, Location, Entry Date, Expiry Date, Unit Price, Status.

Use case: Import into Excel for custom analysis, share with management, use as a backup of current inventory state.

### Expiry Report CSV

Exports only expired items and items expiring within the next 30 days, sorted by expiry date in ascending order (most urgent first). Adds a "Days Until Expiry" calculated column (negative values = already expired).

Use case: Weekly review meeting — quickly know what needs to be disposed of or used urgently.

### Stock Movement CSV

Exports all records from `stock_movements` for a configurable date range (default: last 30 days). Columns: Item ID, Product Name, Movement Type, Quantity Change, Previous Quantity, New Quantity, Reason, Timestamp.

Use case: Monthly reconciliation, tracking where stock went, identifying high-movement items.

### Text Summary Report

A human-readable `.txt` file containing:
- Report generation date and time
- Total active items count
- Items by category breakdown (count and percentage)
- Expired items list with expiry dates
- Expiring soon items list with days remaining
- Low stock items list with current vs minimum quantities
- Top 5 items by total value (quantity × unit_price)

Use case: Weekly management summary, presentation slide data source.

---

## 💰 Budget Cost Breakdown

| Component | Cost | Notes |
|---|---|---|
| Webcam (USB) | ₹300 – ₹1,500 | Or use laptop built-in camera (₹0) |
| QR Code Labels | ₹0 – ₹2 per label | Print on plain paper, or buy label sheets |
| Python & Libraries | ₹0 | Entirely open-source |
| SQLite Database | ₹0 | Built into Python |
| YOLOv8 Nano Model | ₹0 | Free, open-source |
| Server / Cloud | ₹0 | Fully offline, no server needed |
| **Total Hardware** | **₹300 – ₹1,500** | One-time cost |
| **Total Software** | **₹0** | Zero recurring cost |

Compare with enterprise RFID systems:
- RFID reader: ₹15,000 – ₹80,000
- RFID tags: ₹100 – ₹500 each (×500 items = ₹50,000 – ₹2,50,000)
- Software license: ₹10,000 – ₹50,000 per year
- **Typical enterprise RFID total: ₹75,000 – ₹3,80,000**

SmartStock achieves similar functionality at 0.2% of the cost.

---

## 📊 Comparison with Traditional Systems

| Feature | Paper Register | Barcode Scanner | RFID System | **SmartStock (This Project)** |
|---|---|---|---|---|
| Cost | ₹50 (notebook) | ₹5,000–₹20,000 | ₹75,000+ | **₹300–₹1,500** |
| Items per minute | 5–10 | 15–30 | 100–200 | **Up to 20 simultaneous** |
| Expiry tracking | Manual, unreliable | Manual | Yes | **Automatic, real-time** |
| Needs internet | No | No | Sometimes | **No — fully offline** |
| Real-time alerts | No | No | Yes (expensive) | **Yes — free** |
| Scan all at once | No | No | Yes (with gates) | **Yes — one camera** |
| Works on laptop | Yes | Needs reader | Needs reader | **Yes — any laptop** |
| Audit trail | No | Basic | Yes | **Yes — full history** |
| Visual overlay | No | No | No | **Yes — live camera** |
| Setup time | None | Hours | Days/weeks | **5 minutes** |

---

## ⚠️ Known Limitations

1. **QR code detection degrades in very poor lighting.** The preprocessing pipeline helps, but a minimum ambient light level is needed. A small LED light near the camera improves results significantly.

2. **Very small QR codes (less than 40px in the camera frame) may not decode reliably.** This can be mitigated by: moving the camera closer, using a higher-resolution webcam, or printing larger QR labels.

3. **Heavily overlapping QR codes** (one box directly in front of another with minimal gap) may result in only one code being detected. In practice, boxes on a shelf have enough separation.

4. **The Tkinter UI does not support touch input.** This is a mouse-and-keyboard application. A phone app or web interface would be needed for touch-based warehouse workers. This is a known scope limitation.

5. **Reports are currently CSV and text only.** PDF report generation with charts requires additional libraries (`matplotlib`, `reportlab`) which were kept out of scope to minimize dependencies.

6. **YOLOv8 is not specifically trained on QR codes.** It is used as a general region proposer. A fine-tuned model would improve detection accuracy for edge cases.

7. **Single user system.** The application is designed for one user at a time. Multi-user concurrent access (e.g., multiple warehouse workers scanning simultaneously on different devices) requires a client-server architecture, which is outside the current scope.

---

## 🔮 Future Scope

The following features have been identified as high-value extensions for a production version of SmartStock:

**Short-term improvements (1–3 months):**
- Mobile companion app (Flutter or React Native) for phone-based scanning
- PDF report generation with charts and graphs
- Email notification system for critical alerts
- Item photo capture and storage

**Medium-term improvements (3–6 months):**
- Multi-user support with role-based access control (Admin, Viewer, Scanner)
- Web dashboard accessible from any device on the local network (Flask backend)
- Barcode support alongside QR codes (EAN-13, Code 128)
- Automated reorder recommendations based on stock movement trends
- Integration with WhatsApp/Telegram for alert forwarding

**Long-term improvements (6–12 months):**
- Machine learning model trained to detect damaged or missing labels
- Predictive stock depletion using historical movement data
- Integration with popular accounting software (Tally, QuickBooks)
- Cloud sync option for multi-location inventory management
- RFID reader support as an optional upgrade path

---

## 👥 Team & Credits

| Role | Responsibility |
|---|---|
| Project Lead | System architecture, feature planning, presentation |
| Computer Vision Engineer | OpenCV multi-QR pipeline, YOLO integration, scanner module |
| Backend Developer | Database design, alert system, reports module |
| Frontend Developer | Tkinter dashboard, UI design, form implementation |
| QA & Documentation | Testing, README, demo data preparation |

**Libraries and Tools Used:**
- OpenCV — open-source computer vision library (Apache License 2.0)
- Ultralytics YOLOv8 — object detection framework (AGPL-3.0)
- Python Imaging Library / Pillow — image processing (HPND License)
- qrcode — QR code generation (MIT License)
- pyttsx3 — text-to-speech (Mozilla Public License 2.0)
- SQLite — embedded database (Public Domain)

---

*SmartStock — Making Smart Inventory Accessible to Everyone*

*Built for the Project Presentation Event | Computer Science Department*
