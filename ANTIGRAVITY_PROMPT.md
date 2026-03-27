# ANTIGRAVITY AGENT PROMPT — SMART INVENTORY MANAGEMENT SYSTEM
## Copy this entire prompt and paste it directly into Antigravity

---

You are an expert Python developer and computer vision engineer. Your task is to build a **complete, fully functional Smart Inventory Management System** from scratch. This is a real working application — not pseudocode, not placeholders. Every file must be production-ready and runnable immediately after setup.

---

## PROJECT OVERVIEW

Build a Smart Inventory Management System that uses a **webcam or video feed** to detect and decode **multiple QR codes simultaneously** in a single camera frame. Each QR code is attached to a physical storage box. When scanned, the system fetches the corresponding item's full data from a local SQLite database and displays it on a live dashboard with real-time alerts. The system must also allow the user to **add new items**, **generate QR codes**, **print labels**, **track expiry**, **log stock movements**, and **generate reports**.

This is a project presentation demo. It must work on a standard laptop with a USB webcam or built-in webcam. It must require zero internet connection and zero cloud services.

---

## EXACT FOLDER STRUCTURE TO CREATE

```
smart_inventory/
│
├── main.py                      # Entry point — launches the full application
├── requirements.txt             # All pip dependencies with pinned versions
├── setup.py                     # One-click setup script that installs deps and creates DB
├── README.md                    # Already provided separately
│
├── core/
│   ├── __init__.py
│   ├── database.py              # All SQLite DB logic — create, read, update, delete
│   ├── qr_generator.py          # Generates QR codes for new inventory items
│   ├── scanner.py               # Multi-QR OpenCV scanner with YOLO assist
│   ├── alerts.py                # Expiry checking, low stock logic, alert generation
│   ├── reports.py               # PDF/CSV report generation
│   └── voice.py                 # Optional text-to-speech alert system
│
├── ui/
│   ├── __init__.py
│   ├── dashboard.py             # Main Tkinter dashboard window
│   ├── add_item_form.py         # Form to add new inventory items
│   ├── item_detail_view.py      # Popup window showing full item detail
│   ├── scan_window.py           # Live camera feed window with QR overlay
│   ├── report_window.py         # Report generation UI
│   └── styles.py                # Color theme, fonts, widget styles
│
├── data/
│   ├── inventory.db             # SQLite database (auto-created on first run)
│   └── sample_data.sql          # Sample seed data for demo purposes
│
├── labels/                      # Auto-generated QR code label images go here
│   └── .gitkeep
│
├── reports/                     # Auto-generated PDF/CSV reports go here
│   └── .gitkeep
│
├── models/
│   └── README_MODELS.txt        # Instructions to download YOLOv8n.pt if needed
│
└── assets/
    ├── logo.png                 # App logo (generate a placeholder)
    └── alert_sound.wav          # Alert beep (generate using Python)
```

---

## DATABASE SCHEMA — IMPLEMENT EXACTLY AS FOLLOWS

### Table 1: `items`
```sql
CREATE TABLE items (
    item_id         TEXT PRIMARY KEY,        -- e.g., "ITEM-00142" — human readable
    qr_code_data    TEXT UNIQUE NOT NULL,    -- the exact string encoded in the QR
    product_name    TEXT NOT NULL,
    category        TEXT NOT NULL,           -- e.g., "Medicines", "Electronics", "Food", "Stationery"
    supplier_name   TEXT NOT NULL,
    batch_number    TEXT NOT NULL,
    unit_of_measure TEXT NOT NULL,           -- e.g., "units", "kg", "liters", "boxes"
    quantity        INTEGER NOT NULL DEFAULT 0,
    min_stock_level INTEGER NOT NULL DEFAULT 10,   -- below this = low stock alert
    shelf_location  TEXT NOT NULL,           -- e.g., "Rack-3, Row-B, Slot-2"
    entry_date      TEXT NOT NULL,           -- ISO format: "2025-01-10"
    expiry_date     TEXT,                    -- ISO format, nullable for non-perishables
    manufacture_date TEXT,
    unit_price      REAL,
    notes           TEXT,
    created_at      TEXT NOT NULL,           -- full datetime of record creation
    updated_at      TEXT NOT NULL,
    status          TEXT NOT NULL DEFAULT 'active'   -- active, expired, depleted, archived
);
```

### Table 2: `stock_movements`
```sql
CREATE TABLE stock_movements (
    movement_id     INTEGER PRIMARY KEY AUTOINCREMENT,
    item_id         TEXT NOT NULL,
    movement_type   TEXT NOT NULL,   -- "IN", "OUT", "ADJUSTMENT", "DISPOSED"
    quantity_change INTEGER NOT NULL,
    previous_quantity INTEGER NOT NULL,
    new_quantity    INTEGER NOT NULL,
    reason          TEXT,
    performed_by    TEXT DEFAULT 'System',
    timestamp       TEXT NOT NULL,
    FOREIGN KEY (item_id) REFERENCES items(item_id)
);
```

### Table 3: `scan_logs`
```sql
CREATE TABLE scan_logs (
    log_id          INTEGER PRIMARY KEY AUTOINCREMENT,
    item_id         TEXT NOT NULL,
    scan_timestamp  TEXT NOT NULL,
    scan_type       TEXT NOT NULL,   -- "BATCH_SCAN", "MANUAL_SCAN", "SINGLE_SCAN"
    alerts_triggered TEXT,           -- JSON string of alerts found during this scan
    FOREIGN KEY (item_id) REFERENCES items(item_id)
);
```

### Table 4: `alerts_log`
```sql
CREATE TABLE alerts_log (
    alert_id        INTEGER PRIMARY KEY AUTOINCREMENT,
    item_id         TEXT NOT NULL,
    alert_type      TEXT NOT NULL,   -- "EXPIRED", "EXPIRING_SOON", "LOW_STOCK", "OUT_OF_STOCK", "LOCATION_MISMATCH"
    alert_message   TEXT NOT NULL,
    severity        TEXT NOT NULL,   -- "CRITICAL", "WARNING", "INFO"
    timestamp       TEXT NOT NULL,
    acknowledged    INTEGER DEFAULT 0,   -- 0 = unread, 1 = acknowledged
    FOREIGN KEY (item_id) REFERENCES items(item_id)
);
```

---

## CORE MODULE SPECIFICATIONS

### `core/database.py`

Implement a `DatabaseManager` class with the following methods — all must be fully implemented:

- `__init__(self, db_path)` — connect to SQLite, enable WAL mode for performance, call `create_tables()`
- `create_tables(self)` — create all 4 tables above if they don't exist, also create indexes on `expiry_date`, `status`, `category`, and `shelf_location`
- `add_item(self, item_dict)` — insert new item, auto-generate `item_id` in format `ITEM-{5 digit zero-padded counter}`, auto-set `created_at` and `updated_at`
- `get_item_by_qr(self, qr_code_data)` — return full item dict or None
- `get_item_by_id(self, item_id)` — return full item dict or None
- `get_all_items(self, filters=None)` — return list of all items, supports optional filter dict with keys: `category`, `status`, `shelf_location`, `expiry_before_date`
- `update_item(self, item_id, update_dict)` — partial update, auto-update `updated_at`, log movement if quantity changed
- `update_quantity(self, item_id, new_quantity, movement_type, reason)` — update quantity and automatically insert to `stock_movements`
- `delete_item(self, item_id)` — soft delete by setting status to "archived"
- `get_expiring_items(self, days_threshold=7)` — return items expiring within N days
- `get_expired_items(self)` — return all items past expiry date
- `get_low_stock_items(self)` — return items where quantity <= min_stock_level
- `log_scan(self, item_id, scan_type, alerts)` — insert to scan_logs
- `log_alert(self, item_id, alert_type, message, severity)` — insert to alerts_log
- `get_unacknowledged_alerts(self)` — return all alerts where acknowledged=0
- `acknowledge_alert(self, alert_id)` — set acknowledged=1
- `get_dashboard_stats(self)` — return dict with: total_items, total_categories, items_expiring_soon, items_expired, items_low_stock, total_alerts_unread
- `seed_demo_data(self)` — insert 15 realistic demo items across 5 different categories with varied expiry dates (some already expired, some expiring in <7 days, some fine, some low stock) — this is critical for the demo to look impressive

### `core/qr_generator.py`

Implement a `QRGenerator` class:

- `__init__(self, output_dir)` — set output folder for label images
- `generate_qr(self, item_id, qr_data, product_name, expiry_date, shelf_location, batch_number)` — generate a QR code PNG image using the `qrcode` library with error correction level H. The QR code must encode ONLY the `qr_data` string (which equals the item_id). Around the QR code, generate a full label image using Pillow that includes: the QR code centered, product name in bold text above, item_id below the QR, expiry date and shelf location in smaller text below. Label size should be 400x300 pixels. Background white, text black, add a thin border. Save as `labels/{item_id}.png`
- `generate_batch(self, items_list)` — generate QR labels for multiple items at once, return list of file paths
- `print_label(self, item_id)` — open the label image with the system default image viewer (use `os.startfile` on Windows, `subprocess` with `xdg-open` on Linux/Mac)
- `generate_qr_sheet(self, items_list)` — generate a single A4 PDF sheet with multiple QR labels arranged in a grid (3 columns), suitable for printing and cutting. Use Pillow to composite the images.

### `core/scanner.py`

This is the most critical module. Implement a `InventoryScanner` class:

- `__init__(self, db_manager, camera_index=0)` — initialize webcam using `cv2.VideoCapture`, initialize `cv2.QRCodeDetector()`, attempt to load YOLOv8 nano model for QR region pre-detection if `ultralytics` is available, otherwise fall back to pure OpenCV
- `start_scan_session(self)` — open a live camera window using OpenCV. This window must:
  - Show the live webcam feed at 640x480 or higher resolution
  - On every frame, call `detect_and_decode_all_qr(frame)` to find all QR codes
  - For every detected QR code, draw a GREEN bounding polygon/rectangle around it on the frame
  - Display the product name as a label directly on the frame above the QR bounding box
  - If the item is expired, make the bounding box RED and add "EXPIRED" text overlay
  - If the item is expiring soon (<7 days), make the bounding box ORANGE and add "⚠ EXPIRING" overlay
  - If the item is low stock, add a YELLOW "LOW STOCK" overlay
  - In the top-left corner of the frame, display a live counter: "QR Codes Detected: N"
  - In the top-right corner, display current timestamp
  - Show the FPS in the bottom-left corner
  - Accept keyboard input: press 'q' to quit, press 's' to take a snapshot and save the annotated frame, press 'r' to generate a scan report of all items seen in this session
  - Run in a separate thread so the UI doesn't block
- `detect_and_decode_all_qr(self, frame)` — takes an OpenCV frame, runs the QR detector, returns a list of dicts: `{qr_data, bounding_box_points, item_data, alerts}`. Must handle: blurry frames gracefully (try image sharpening), multiple QR codes in the same frame, QR codes at different angles and distances
- `preprocess_frame(self, frame)` — apply adaptive thresholding, slight sharpening, and contrast enhancement to improve QR detection in poor lighting
- `get_alerts_for_item(self, item_data)` — check the item and return list of alert strings: check expiry, check low stock, check if status is already "expired"
- `scan_single_qr_from_image(self, image_path)` — decode QR from a saved image file, return item data
- `release(self)` — release camera resource

### `core/alerts.py`

Implement an `AlertManager` class:

- `__init__(self, db_manager)` — init with db reference
- `run_full_inventory_check(self)` — check entire inventory against all alert conditions, log new alerts to database, return summary dict
- `check_expiry_alerts(self)` — find all expired and expiring-soon items, generate alert messages, return list
- `check_stock_alerts(self)` — find low stock and out-of-stock items, return list
- `generate_alert_message(self, item, alert_type)` — return a human-readable alert message string. Examples: "CRITICAL: Paracetamol 500mg (ITEM-00142) has EXPIRED on 2025-03-15! Remove immediately.", "WARNING: Rice Flour 1kg (ITEM-00089) is expiring in 4 days on 2026-04-01. Take action.", "WARNING: USB Cables (ITEM-00201) is LOW STOCK — only 3 units remaining (minimum: 10)."
- `get_alert_color(self, severity)` — return hex color string: CRITICAL = "#FF3B30", WARNING = "#FF9500", INFO = "#007AFF"
- `get_alert_icon(self, alert_type)` — return emoji string for display: EXPIRED = "☠️", EXPIRING_SOON = "⚠️", LOW_STOCK = "📦", OUT_OF_STOCK = "❌"

### `core/reports.py`

Implement a `ReportGenerator` class:

- `__init__(self, db_manager, output_dir)` — init
- `generate_full_inventory_csv(self)` — export all items to a CSV with all columns, save to `reports/inventory_{timestamp}.csv`, return file path
- `generate_expiry_report_csv(self)` — CSV of only expired and expiring-soon items, sorted by expiry date ascending
- `generate_stock_movement_csv(self, days=30)` — CSV of all stock movements in last N days
- `generate_summary_text_report(self)` — plain text report with: total items, category breakdown, expired count, expiring soon count, low stock count, top 5 items by value (quantity × unit_price). Save to `reports/summary_{timestamp}.txt`, return content string
- `generate_scan_session_report(self, scanned_items_list)` — given a list of items seen during a scan session, generate a summary text file

### `core/voice.py`

Implement a `VoiceAlertSystem` class:

- `__init__(self)` — try to initialize `pyttsx3` engine, set voice rate to 150, volume to 1.0. If pyttsx3 is not available, set `self.available = False`
- `speak(self, message)` — speak the message in a background thread so it doesn't block UI
- `announce_scan_result(self, item_count, alert_count)` — say something like "Scan complete. {N} items detected. {M} alerts found."
- `announce_alert(self, alert_message)` — speak the alert message
- `announce_expired(self, product_name)` — say "{product_name} has expired. Please remove immediately."

---

## UI MODULE SPECIFICATIONS

### `ui/styles.py`

Define a `Theme` class with constants:
```python
class Theme:
    BG_PRIMARY = "#1C1C1E"        # Dark background
    BG_SECONDARY = "#2C2C2E"      # Card background
    BG_TERTIARY = "#3A3A3C"       # Input field background
    ACCENT_BLUE = "#007AFF"       # Primary action color
    ACCENT_GREEN = "#34C759"      # Success / in-stock
    ACCENT_ORANGE = "#FF9500"     # Warning / expiring soon
    ACCENT_RED = "#FF3B30"        # Critical / expired
    ACCENT_YELLOW = "#FFD60A"     # Low stock
    TEXT_PRIMARY = "#FFFFFF"
    TEXT_SECONDARY = "#EBEBF5"
    TEXT_MUTED = "#8E8E93"
    FONT_TITLE = ("Helvetica", 22, "bold")
    FONT_HEADING = ("Helvetica", 16, "bold")
    FONT_BODY = ("Helvetica", 12)
    FONT_SMALL = ("Helvetica", 10)
    FONT_MONO = ("Courier", 11)
    CORNER_RADIUS = 8
    PADDING = 16
```

All Tkinter widgets must use these theme values consistently throughout the entire application.

### `ui/dashboard.py`

The main window — a full-featured inventory dashboard using Tkinter. Implement a `DashboardWindow` class that creates a `tk.Tk()` root window sized 1280x800, dark-themed. The layout must be:

**TOP NAVIGATION BAR:**
- App title "SmartStock — Inventory Manager" on the left
- Four main nav buttons: "📊 Dashboard", "📷 Scan", "➕ Add Item", "📋 Reports"
- A live clock displaying current time in the top-right corner, updating every second

**LEFT SIDEBAR (Stats Panel):**
- Five stat cards, each showing an icon, a label, and a big number:
  - 📦 Total Items
  - 🗂️ Categories
  - ⚠️ Expiring Soon (orange if > 0)
  - ☠️ Expired (red if > 0)
  - 📉 Low Stock (yellow if > 0)
- A "🔔 Alerts" section below showing the last 5 unacknowledged alerts as compact rows with severity color coding
- A "Run Full Check" button that triggers `AlertManager.run_full_inventory_check()`

**MAIN CONTENT AREA:**
Implement as a tabbed/frame switcher (NOT ttk.Notebook — manually switch frames using pack/grid show/hide). Four pages:

**Page 1 — Dashboard Overview:**
- A `ttk.Treeview` table showing ALL inventory items with columns: Item ID, Product Name, Category, Quantity, Unit, Expiry Date, Location, Status
- Each row must be color-coded: red background for expired, orange for expiring soon, yellow for low stock, green for healthy
- A search bar at the top to filter the table by typing any text (real-time filter as user types)
- A category filter dropdown to filter by category
- Click any row to open `ItemDetailView` popup
- Right-click context menu on rows with options: Edit Item, Adjust Quantity, Generate QR Label, Archive Item
- A status bar at the bottom showing "Showing X of Y items"

**Page 2 — Scan View:**
- A large prominent button "START LIVE SCAN" that opens the OpenCV scan window
- A "Scan from Image" button to load an image file and decode QR codes from it
- A "Last Scan Results" section that shows the table of items scanned in the most recent session
- An "Alerts from Last Scan" box listing any alerts generated during the last scan with severity colors

**Page 3 — Add Item Form:**
- Use `AddItemForm` component (see below)

**Page 4 — Reports:**
- Use `ReportWindow` component (see below)

The dashboard must auto-refresh stats and the table every 30 seconds. Add a manual "🔄 Refresh" button.

### `ui/add_item_form.py`

Implement `AddItemForm` as a Tkinter Frame. It must contain a form with these fields:

| Field | Widget Type | Validation |
|---|---|---|
| Product Name | Entry | Required, min 3 chars |
| Category | Combobox | Options: Medicines, Food & Beverages, Electronics, Stationery, Cleaning Supplies, Raw Materials, Other |
| Supplier Name | Entry | Required |
| Batch Number | Entry | Required |
| Unit of Measure | Combobox | Options: units, kg, grams, liters, ml, boxes, packets, rolls |
| Quantity | Spinbox | Required, integer >= 0 |
| Minimum Stock Level | Spinbox | Required, integer >= 0 |
| Shelf Location | Entry | Required, format hint: "Rack-X, Row-Y, Slot-Z" |
| Entry Date | DateEntry or Entry | Default today, format YYYY-MM-DD |
| Expiry Date | Entry | Optional, format YYYY-MM-DD, validate it's a valid future date if provided |
| Manufacture Date | Entry | Optional |
| Unit Price (₹) | Entry | Optional, float |
| Notes | Text widget | Optional, multi-line |

Form buttons:
- "💾 Save & Generate QR" — validates all fields, saves to DB, generates QR label, shows success popup with QR preview
- "🖨️ Save & Print Label" — same as above but also calls `print_label()`
- "🔄 Reset Form" — clears all fields back to defaults
- "👁️ Preview QR" — generates a preview QR without saving

### `ui/item_detail_view.py`

A popup `tk.Toplevel` window that shows when user clicks an item in the table. Must display:
- QR code image (loaded from `labels/` folder) on the left side, 200x200px
- All item fields displayed as label-value pairs on the right
- Status badge with color coding
- Alert badges if any active alerts
- Action buttons at the bottom: "Edit", "Adjust Quantity", "Reprint Label", "Archive"
- "Adjust Quantity" opens a small dialog with: current quantity shown, +/- spinbox to adjust, reason dropdown (Received Stock, Disposed, Sold/Used, Stock Count Correction), confirm button

### `ui/scan_window.py`

A `tk.Toplevel` window that embeds the OpenCV scan feed. Must:
- Display a live-updating label with the camera frame converted to Tkinter PhotoImage using PIL
- Below the camera feed, show a real-time table of all items detected in this scan session (auto-updates as new QR codes are found)
- Highlight new detections with a flash animation
- Show alert badges next to each detected item name
- "Stop Scan" button, "Save Snapshot" button, "Generate Report" button
- Update the camera frame at 30fps using `after()` callbacks

### `ui/report_window.py`

A Tkinter Frame with:
- Three report type buttons with descriptions: "📋 Full Inventory CSV", "⏰ Expiry Report CSV", "📈 Stock Movement Report CSV"
- A date range picker for stock movement report
- A "📝 Generate Text Summary" button
- After generating, show a preview of the report content in a scrollable Text widget
- "📂 Open File" button to open the generated file in the system file explorer
- "🖨️ Print" button (use OS print dialog if possible)

---

## `main.py` — ENTRY POINT

```python
# main.py
# Must do the following in order:
# 1. Check Python version >= 3.8
# 2. Check all required packages are installed, if not print helpful error message
# 3. Create all directories: data/, labels/, reports/, models/
# 4. Initialize DatabaseManager
# 5. Check if DB is empty — if yes, call seed_demo_data() automatically
# 6. Initialize AlertManager and run initial check
# 7. Initialize VoiceAlertSystem
# 8. Launch DashboardWindow
# 9. Handle clean shutdown: release camera if open, close DB connection
```

---

## `setup.py` — ONE-CLICK INSTALLER

Create a setup script that:
1. Checks Python version
2. Upgrades pip
3. Installs all requirements from requirements.txt
4. Downloads YOLOv8 nano model weights (yolov8n.pt) using ultralytics auto-download
5. Creates all necessary directories
6. Runs the DB setup
7. Seeds demo data
8. Prints a success message with instructions to run `python main.py`

---

## `requirements.txt` — EXACT VERSIONS

```
opencv-python>=4.8.0
opencv-contrib-python>=4.8.0
Pillow>=10.0.0
qrcode[pil]>=7.4.2
ultralytics>=8.0.0
pyttsx3>=2.90
numpy>=1.24.0
```

Note: sqlite3 is built into Python. tkinter is built into Python. No external database server needed.

---

## SAMPLE SEED DATA — IMPLEMENT IN `database.py`

The `seed_demo_data()` method must insert exactly these 15 items (hardcoded for demo consistency):

1. **Paracetamol 500mg** — Category: Medicines — Qty: 48 — Expiry: 2026-03-31 (expiring in ~4 days from demo date) — Rack-1, Row-A — Batch: MED-2024-09 — Supplier: HealthFirst Pharma — Min Stock: 20 — ⚠️ EXPIRING SOON ALERT
2. **Amoxicillin 250mg** — Category: Medicines — Qty: 5 — Expiry: 2025-12-01 (already expired) — Rack-1, Row-B — Batch: MED-2023-11 — Supplier: CureMed Ltd — Min Stock: 15 — ☠️ EXPIRED ALERT + LOW STOCK
3. **Hand Sanitizer 500ml** — Category: Cleaning Supplies — Qty: 120 — Expiry: 2027-06-30 — Rack-4, Row-A — Batch: CLN-2024-05 — Supplier: PureCare Co. — Min Stock: 30 — ✅ HEALTHY
4. **Basmati Rice 1kg** — Category: Food & Beverages — Qty: 8 — Expiry: 2026-08-15 — Rack-2, Row-C — Batch: FOOD-2024-08 — Supplier: GrainMart — Min Stock: 15 — ⚠️ LOW STOCK
5. **USB-C Charging Cable** — Category: Electronics — Qty: 45 — Expiry: null — Rack-5, Row-A — Batch: ELEC-2024-12 — Supplier: TechZone — Min Stock: 10 — ✅ HEALTHY
6. **A4 Paper Ream (500 sheets)** — Category: Stationery — Qty: 22 — Expiry: null — Rack-6, Row-B — Batch: STAT-2024-07 — Supplier: PaperWorld — Min Stock: 10 — ✅ HEALTHY
7. **Vitamin C Tablets 1000mg** — Category: Medicines — Qty: 200 — Expiry: 2026-04-02 (expiring in ~6 days) — Rack-1, Row-C — Batch: MED-2024-10 — Supplier: NutraPlus — Min Stock: 50 — ⚠️ EXPIRING SOON
8. **Coconut Oil 1 Liter** — Category: Food & Beverages — Qty: 30 — Expiry: 2026-09-20 — Rack-2, Row-A — Batch: FOOD-2024-09 — Supplier: NatureFarm — Min Stock: 10 — ✅ HEALTHY
9. **Whiteboard Markers (Set of 4)** — Category: Stationery — Qty: 3 — Expiry: null — Rack-6, Row-C — Batch: STAT-2024-03 — Supplier: OfficeHub — Min Stock: 8 — ⚠️ LOW STOCK
10. **Dettol Antiseptic 250ml** — Category: Cleaning Supplies — Qty: 15 — Expiry: 2025-11-30 (already expired) — Rack-4, Row-B — Batch: CLN-2023-11 — Supplier: CleanCo — Min Stock: 10 — ☠️ EXPIRED ALERT
11. **Thermal Printer Paper Roll** — Category: Stationery — Qty: 60 — Expiry: null — Rack-6, Row-A — Batch: STAT-2024-06 — Supplier: PrintMart — Min Stock: 20 — ✅ HEALTHY
12. **Instant Noodles (Pack of 12)** — Category: Food & Beverages — Qty: 0 — Expiry: 2026-12-31 — Rack-3, Row-A — Batch: FOOD-2024-11 — Supplier: QuickBite — Min Stock: 5 — ❌ OUT OF STOCK
13. **AA Batteries (Pack of 10)** — Category: Electronics — Qty: 55 — Expiry: 2028-01-01 — Rack-5, Row-B — Batch: ELEC-2024-08 — Supplier: PowerMax — Min Stock: 20 — ✅ HEALTHY
14. **Floor Cleaner 1 Liter** — Category: Cleaning Supplies — Qty: 4 — Expiry: 2026-06-30 — Rack-4, Row-C — Batch: CLN-2024-03 — Supplier: ShineClean — Min Stock: 8 — ⚠️ LOW STOCK
15. **Stapler + Staple Pins Set** — Category: Stationery — Qty: 18 — Expiry: null — Rack-6, Row-D — Batch: STAT-2024-04 — Supplier: OfficeHub — Min Stock: 5 — ✅ HEALTHY

Generate QR codes automatically for all 15 items during seeding using QRGenerator.

---

## OPENCV MULTI-QR SCANNING — IMPLEMENTATION DETAILS

The `detect_and_decode_all_qr` function in `scanner.py` must:

1. Convert frame to grayscale
2. Apply `cv2.adaptiveThreshold` to handle varying lighting
3. Try `cv2.QRCodeDetectorAruco` first (best multi-QR support in OpenCV 4.8+)
4. If that fails, fall back to `cv2.QRCodeDetector` with `detectAndDecodeMulti`
5. For each decoded QR string, call `db_manager.get_item_by_qr(qr_string)` to fetch item data
6. Call `get_alerts_for_item(item_data)` to compute active alerts
7. Return full results list

The drawing overlay on the frame must use:
- `cv2.polylines` to draw the bounding polygon
- `cv2.putText` with a filled background rectangle for contrast (use `cv2.FONT_HERSHEY_SIMPLEX`)
- Color must be BGR format: GREEN = (0, 255, 0), RED = (0, 0, 255), ORANGE = (0, 165, 255), YELLOW = (0, 255, 255)

---

## ERROR HANDLING REQUIREMENTS

Every function must have proper try/except blocks. Specific requirements:
- If webcam fails to open, show a clear error dialog with the message "Could not open camera. Please check your webcam connection." and offer to demo with a pre-recorded test video
- If a QR code is decoded but not found in the database, display "UNKNOWN ITEM" in PURPLE on the frame and log a warning
- If the database file is corrupted, back it up as `inventory_backup_{timestamp}.db` and create a fresh one
- All file I/O operations must handle permission errors gracefully
- Network calls: there are none — this system is fully offline

---

## WHAT TO GENERATE FIRST, THEN SECOND, ETC. — BUILD ORDER:

1. `requirements.txt`
2. `core/__init__.py` (empty)
3. `core/database.py` — full implementation
4. `core/qr_generator.py` — full implementation
5. `core/alerts.py` — full implementation
6. `core/voice.py` — full implementation
7. `core/scanner.py` — full implementation
8. `core/reports.py` — full implementation
9. `ui/__init__.py` (empty)
10. `ui/styles.py` — full implementation
11. `ui/add_item_form.py` — full implementation
12. `ui/item_detail_view.py` — full implementation
13. `ui/scan_window.py` — full implementation
14. `ui/report_window.py` — full implementation
15. `ui/dashboard.py` — full implementation (depends on all other UI files)
16. `main.py` — entry point
17. `setup.py` — installer
18. `data/sample_data.sql` — raw SQL insert statements for the 15 demo items

---

## ABSOLUTE RULES — DO NOT VIOLATE

- Do NOT use any external database (PostgreSQL, MySQL, Firebase, etc.) — SQLite only
- Do NOT require any internet connection at runtime
- Do NOT use Flask, Django, FastAPI, or any web framework — pure Tkinter desktop app
- Do NOT use placeholder comments like `# TODO: implement this` — every function must be fully implemented
- Do NOT leave any `pass` statements in non-empty classes — all methods must have real code
- Every file must be immediately runnable without modification after `pip install -r requirements.txt`
- Use f-strings for all string formatting
- Use `pathlib.Path` for all file path operations (not `os.path`)
- All datetime operations must use `datetime` module from stdlib
- Add a docstring to every class and every public method
- The entire application must work on Windows, macOS, and Linux (Ubuntu)
- For Tkinter color config use `.configure()` not direct attribute assignment

---

Build the complete project now. Start with `requirements.txt`, then proceed in the build order listed above. Output every file completely without truncation. Do not summarize — write the full code for every file.
