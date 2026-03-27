"""
core/database.py
DatabaseManager — all SQLite operations for SmartStock inventory system.
"""

import sqlite3
import json
import logging
from datetime import datetime, date, timedelta
from pathlib import Path

logger = logging.getLogger(__name__)


class DatabaseManager:
    """Manages all SQLite database operations for the SmartStock inventory system."""

    def __init__(self, db_path: str):
        """
        Connect to SQLite database, enable WAL mode, and create tables.

        Args:
            db_path: Path to the SQLite database file.
        """
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(str(self.db_path), check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA journal_mode=WAL")
        self.conn.execute("PRAGMA foreign_keys=ON")
        self.conn.commit()
        self.create_tables()
        self._item_counter = self._get_max_item_counter()

    def _get_max_item_counter(self) -> int:
        """Return the current maximum item numeric suffix in the items table."""
        try:
            cursor = self.conn.execute(
                "SELECT item_id FROM items ORDER BY rowid DESC LIMIT 1"
            )
            row = cursor.fetchone()
            if row:
                return int(row["item_id"].split("-")[1])
            return 0
        except Exception:
            return 0

    def create_tables(self):
        """Create all 4 database tables and indexes if they don't exist."""
        self.conn.executescript("""
            CREATE TABLE IF NOT EXISTS items (
                item_id         TEXT PRIMARY KEY,
                qr_code_data    TEXT UNIQUE NOT NULL,
                product_name    TEXT NOT NULL,
                category        TEXT NOT NULL,
                supplier_name   TEXT NOT NULL,
                batch_number    TEXT NOT NULL,
                unit_of_measure TEXT NOT NULL,
                quantity        INTEGER NOT NULL DEFAULT 0,
                min_stock_level INTEGER NOT NULL DEFAULT 10,
                shelf_location  TEXT NOT NULL,
                entry_date      TEXT NOT NULL,
                expiry_date     TEXT,
                manufacture_date TEXT,
                unit_price      REAL,
                notes           TEXT,
                created_at      TEXT NOT NULL,
                updated_at      TEXT NOT NULL,
                status          TEXT NOT NULL DEFAULT 'active'
            );

            CREATE TABLE IF NOT EXISTS stock_movements (
                movement_id       INTEGER PRIMARY KEY AUTOINCREMENT,
                item_id           TEXT NOT NULL,
                movement_type     TEXT NOT NULL,
                quantity_change   INTEGER NOT NULL,
                previous_quantity INTEGER NOT NULL,
                new_quantity      INTEGER NOT NULL,
                reason            TEXT,
                performed_by      TEXT DEFAULT 'System',
                timestamp         TEXT NOT NULL,
                FOREIGN KEY (item_id) REFERENCES items(item_id)
            );

            CREATE TABLE IF NOT EXISTS scan_logs (
                log_id          INTEGER PRIMARY KEY AUTOINCREMENT,
                item_id         TEXT NOT NULL,
                scan_timestamp  TEXT NOT NULL,
                scan_type       TEXT NOT NULL,
                alerts_triggered TEXT,
                FOREIGN KEY (item_id) REFERENCES items(item_id)
            );

            CREATE TABLE IF NOT EXISTS alerts_log (
                alert_id    INTEGER PRIMARY KEY AUTOINCREMENT,
                item_id     TEXT NOT NULL,
                alert_type  TEXT NOT NULL,
                alert_message TEXT NOT NULL,
                severity    TEXT NOT NULL,
                timestamp   TEXT NOT NULL,
                acknowledged INTEGER DEFAULT 0,
                FOREIGN KEY (item_id) REFERENCES items(item_id)
            );

            CREATE INDEX IF NOT EXISTS idx_items_expiry    ON items(expiry_date);
            CREATE INDEX IF NOT EXISTS idx_items_status    ON items(status);
            CREATE INDEX IF NOT EXISTS idx_items_category  ON items(category);
            CREATE INDEX IF NOT EXISTS idx_items_shelf     ON items(shelf_location);
            CREATE INDEX IF NOT EXISTS idx_movements_item  ON stock_movements(item_id);
            CREATE INDEX IF NOT EXISTS idx_alerts_item     ON alerts_log(item_id);
            CREATE INDEX IF NOT EXISTS idx_alerts_ack      ON alerts_log(acknowledged);
        """)
        self.conn.commit()

    def _now(self) -> str:
        """Return current datetime as ISO string."""
        return datetime.now().isoformat(sep=" ", timespec="seconds")

    def _today(self) -> str:
        """Return today's date as ISO string."""
        return date.today().isoformat()

    def _row_to_dict(self, row) -> dict:
        """Convert a sqlite3.Row to a plain dictionary."""
        if row is None:
            return None
        return dict(row)

    def add_item(self, item_dict: dict) -> str:
        """
        Insert a new item into the inventory. Auto-generates item_id.

        Args:
            item_dict: Dictionary of item fields (without item_id, created_at, updated_at).

        Returns:
            The generated item_id string.
        """
        self._item_counter += 1
        item_id = f"ITEM-{self._item_counter:05d}"
        now = self._now()

        self.conn.execute(
            """INSERT INTO items (
                item_id, qr_code_data, product_name, category, supplier_name,
                batch_number, unit_of_measure, quantity, min_stock_level,
                shelf_location, entry_date, expiry_date, manufacture_date,
                unit_price, notes, created_at, updated_at, status
            ) VALUES (
                :item_id, :qr_code_data, :product_name, :category, :supplier_name,
                :batch_number, :unit_of_measure, :quantity, :min_stock_level,
                :shelf_location, :entry_date, :expiry_date, :manufacture_date,
                :unit_price, :notes, :created_at, :updated_at, :status
            )""",
            {
                "item_id": item_id,
                "qr_code_data": item_dict.get("qr_code_data", item_id),
                "product_name": item_dict["product_name"],
                "category": item_dict["category"],
                "supplier_name": item_dict["supplier_name"],
                "batch_number": item_dict["batch_number"],
                "unit_of_measure": item_dict.get("unit_of_measure", "units"),
                "quantity": item_dict.get("quantity", 0),
                "min_stock_level": item_dict.get("min_stock_level", 10),
                "shelf_location": item_dict.get("shelf_location", ""),
                "entry_date": item_dict.get("entry_date", self._today()),
                "expiry_date": item_dict.get("expiry_date"),
                "manufacture_date": item_dict.get("manufacture_date"),
                "unit_price": item_dict.get("unit_price"),
                "notes": item_dict.get("notes"),
                "created_at": now,
                "updated_at": now,
                "status": item_dict.get("status", "active"),
            },
        )
        self.conn.commit()
        logger.info(f"Added item {item_id}: {item_dict['product_name']}")
        return item_id

    def get_item_by_qr(self, qr_code_data: str) -> dict:
        """
        Fetch a full item dict by its QR code data string.

        Args:
            qr_code_data: The string encoded in the QR code.

        Returns:
            Item dict or None if not found.
        """
        cursor = self.conn.execute(
            "SELECT * FROM items WHERE qr_code_data = ?", (qr_code_data,)
        )
        return self._row_to_dict(cursor.fetchone())

    def get_item_by_id(self, item_id: str) -> dict:
        """
        Fetch a full item dict by its item_id.

        Args:
            item_id: The item's primary key (e.g., 'ITEM-00001').

        Returns:
            Item dict or None if not found.
        """
        cursor = self.conn.execute(
            "SELECT * FROM items WHERE item_id = ?", (item_id,)
        )
        return self._row_to_dict(cursor.fetchone())

    def get_all_items(self, filters: dict = None) -> list:
        """
        Return list of all items, with optional filters.

        Args:
            filters: Optional dict with keys: category, status, shelf_location,
                     expiry_before_date.

        Returns:
            List of item dicts.
        """
        query = "SELECT * FROM items WHERE 1=1"
        params = []

        if filters:
            if "category" in filters and filters["category"]:
                query += " AND category = ?"
                params.append(filters["category"])
            if "status" in filters and filters["status"]:
                query += " AND status = ?"
                params.append(filters["status"])
            if "shelf_location" in filters and filters["shelf_location"]:
                query += " AND shelf_location LIKE ?"
                params.append(f"%{filters['shelf_location']}%")
            if "expiry_before_date" in filters and filters["expiry_before_date"]:
                query += " AND expiry_date IS NOT NULL AND expiry_date <= ?"
                params.append(filters["expiry_before_date"])

        query += " ORDER BY product_name ASC"
        cursor = self.conn.execute(query, params)
        return [self._row_to_dict(row) for row in cursor.fetchall()]

    def update_item(self, item_id: str, update_dict: dict):
        """
        Partial update of an item. Auto-updates updated_at and logs quantity changes.

        Args:
            item_id: Item to update.
            update_dict: Fields to update (any subset of item columns).
        """
        existing = self.get_item_by_id(item_id)
        if not existing:
            raise ValueError(f"Item {item_id} not found")

        now = self._now()
        update_dict["updated_at"] = now

        # Build dynamic SET clause
        set_clauses = ", ".join(f"{k} = ?" for k in update_dict.keys())
        values = list(update_dict.values()) + [item_id]

        self.conn.execute(
            f"UPDATE items SET {set_clauses} WHERE item_id = ?", values
        )

        # Log quantity change if applicable
        if "quantity" in update_dict and update_dict["quantity"] != existing["quantity"]:
            change = update_dict["quantity"] - existing["quantity"]
            movement_type = "IN" if change > 0 else "OUT"
            self.conn.execute(
                """INSERT INTO stock_movements (
                    item_id, movement_type, quantity_change, previous_quantity,
                    new_quantity, reason, performed_by, timestamp
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (item_id, movement_type, change, existing["quantity"],
                 update_dict["quantity"], "Item update", "System", now),
            )

        self.conn.commit()
        logger.info(f"Updated item {item_id}")

    def update_quantity(self, item_id: str, new_quantity: int,
                        movement_type: str, reason: str, performed_by: str = "User"):
        """
        Update item quantity and record a stock movement.

        Args:
            item_id: Item to update.
            new_quantity: New stock quantity.
            movement_type: 'IN', 'OUT', 'ADJUSTMENT', 'DISPOSED'.
            reason: Human-readable reason string.
            performed_by: Name of person performing the action.
        """
        existing = self.get_item_by_id(item_id)
        if not existing:
            raise ValueError(f"Item {item_id} not found")

        now = self._now()
        prev_qty = existing["quantity"]
        change = new_quantity - prev_qty

        self.conn.execute(
            "UPDATE items SET quantity = ?, updated_at = ? WHERE item_id = ?",
            (new_quantity, now, item_id),
        )
        self.conn.execute(
            """INSERT INTO stock_movements (
                item_id, movement_type, quantity_change, previous_quantity,
                new_quantity, reason, performed_by, timestamp
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (item_id, movement_type, change, prev_qty, new_quantity, reason,
             performed_by, now),
        )
        self.conn.commit()
        logger.info(f"Updated quantity for {item_id}: {prev_qty} -> {new_quantity}")

    def delete_item(self, item_id: str):
        """
        Soft-delete an item by setting status to 'archived'.

        Args:
            item_id: Item to archive.
        """
        now = self._now()
        self.conn.execute(
            "UPDATE items SET status = 'archived', updated_at = ? WHERE item_id = ?",
            (now, item_id),
        )
        self.conn.commit()
        logger.info(f"Archived item {item_id}")

    def get_expiring_items(self, days_threshold: int = 7) -> list:
        """
        Return items expiring within the next N days (but not yet expired).

        Args:
            days_threshold: Number of days to look ahead.

        Returns:
            List of item dicts.
        """
        today = date.today().isoformat()
        future = (date.today() + timedelta(days=days_threshold)).isoformat()
        cursor = self.conn.execute(
            """SELECT * FROM items
               WHERE expiry_date IS NOT NULL
                 AND expiry_date >= ?
                 AND expiry_date <= ?
                 AND status = 'active'
               ORDER BY expiry_date ASC""",
            (today, future),
        )
        return [self._row_to_dict(row) for row in cursor.fetchall()]

    def get_expired_items(self) -> list:
        """Return all items past their expiry date with status 'active'."""
        today = date.today().isoformat()
        cursor = self.conn.execute(
            """SELECT * FROM items
               WHERE expiry_date IS NOT NULL
                 AND expiry_date < ?
                 AND status = 'active'
               ORDER BY expiry_date ASC""",
            (today,),
        )
        return [self._row_to_dict(row) for row in cursor.fetchall()]

    def get_low_stock_items(self) -> list:
        """Return items where quantity <= min_stock_level and status is active."""
        cursor = self.conn.execute(
            """SELECT * FROM items
               WHERE quantity <= min_stock_level
                 AND status = 'active'
               ORDER BY quantity ASC""",
        )
        return [self._row_to_dict(row) for row in cursor.fetchall()]

    def log_scan(self, item_id: str, scan_type: str, alerts: list):
        """
        Record a scan event in scan_logs.

        Args:
            item_id: The item that was scanned.
            scan_type: 'BATCH_SCAN', 'MANUAL_SCAN', or 'SINGLE_SCAN'.
            alerts: List of alert strings generated for this scan.
        """
        now = self._now()
        alerts_json = json.dumps(alerts) if alerts else None
        self.conn.execute(
            """INSERT INTO scan_logs (item_id, scan_timestamp, scan_type, alerts_triggered)
               VALUES (?, ?, ?, ?)""",
            (item_id, now, scan_type, alerts_json),
        )
        self.conn.commit()

    def log_alert(self, item_id: str, alert_type: str, message: str, severity: str):
        """
        Insert a new alert record into alerts_log.

        Args:
            item_id: The item this alert is about.
            alert_type: e.g. 'EXPIRED', 'EXPIRING_SOON', 'LOW_STOCK'.
            message: Human-readable alert message.
            severity: 'CRITICAL', 'WARNING', or 'INFO'.
        """
        now = self._now()
        self.conn.execute(
            """INSERT INTO alerts_log (item_id, alert_type, alert_message, severity, timestamp, acknowledged)
               VALUES (?, ?, ?, ?, ?, 0)""",
            (item_id, alert_type, message, severity, now),
        )
        self.conn.commit()

    def get_unacknowledged_alerts(self) -> list:
        """Return all alerts where acknowledged = 0, newest first."""
        cursor = self.conn.execute(
            """SELECT al.*, i.product_name FROM alerts_log al
               JOIN items i ON al.item_id = i.item_id
               WHERE al.acknowledged = 0
               ORDER BY al.timestamp DESC"""
        )
        return [self._row_to_dict(row) for row in cursor.fetchall()]

    def acknowledge_alert(self, alert_id: int):
        """
        Mark an alert as acknowledged.

        Args:
            alert_id: The alert_id to mark.
        """
        self.conn.execute(
            "UPDATE alerts_log SET acknowledged = 1 WHERE alert_id = ?",
            (alert_id,),
        )
        self.conn.commit()

    def get_dashboard_stats(self) -> dict:
        """
        Return a summary dict for the dashboard sidebar stats.

        Returns:
            Dict with keys: total_items, total_categories, items_expiring_soon,
            items_expired, items_low_stock, total_alerts_unread.
        """
        today = date.today().isoformat()
        future = (date.today() + timedelta(days=7)).isoformat()

        total_items = self.conn.execute(
            "SELECT COUNT(*) FROM items WHERE status = 'active'"
        ).fetchone()[0]

        total_categories = self.conn.execute(
            "SELECT COUNT(DISTINCT category) FROM items WHERE status = 'active'"
        ).fetchone()[0]

        items_expiring_soon = self.conn.execute(
            """SELECT COUNT(*) FROM items
               WHERE expiry_date IS NOT NULL
                 AND expiry_date >= ? AND expiry_date <= ?
                 AND status = 'active'""",
            (today, future),
        ).fetchone()[0]

        items_expired = self.conn.execute(
            """SELECT COUNT(*) FROM items
               WHERE expiry_date IS NOT NULL AND expiry_date < ?
                 AND status = 'active'""",
            (today,),
        ).fetchone()[0]

        items_low_stock = self.conn.execute(
            """SELECT COUNT(*) FROM items
               WHERE quantity <= min_stock_level AND status = 'active'"""
        ).fetchone()[0]

        total_alerts_unread = self.conn.execute(
            "SELECT COUNT(*) FROM alerts_log WHERE acknowledged = 0"
        ).fetchone()[0]

        return {
            "total_items": total_items,
            "total_categories": total_categories,
            "items_expiring_soon": items_expiring_soon,
            "items_expired": items_expired,
            "items_low_stock": items_low_stock,
            "total_alerts_unread": total_alerts_unread,
        }

    def get_stock_movements(self, days: int = 30) -> list:
        """
        Return stock movements within the last N days.

        Args:
            days: Number of days to look back.

        Returns:
            List of movement dicts with product_name joined.
        """
        cutoff = (datetime.now() - timedelta(days=days)).isoformat(sep=" ", timespec="seconds")
        cursor = self.conn.execute(
            """SELECT sm.*, i.product_name FROM stock_movements sm
               JOIN items i ON sm.item_id = i.item_id
               WHERE sm.timestamp >= ?
               ORDER BY sm.timestamp DESC""",
            (cutoff,),
        )
        return [self._row_to_dict(row) for row in cursor.fetchall()]

    def seed_demo_data(self):
        """
        Insert 15 realistic demo items across 5 categories with varied conditions.
        Also generates QR labels for all items.
        """
        from core.qr_generator import QRGenerator

        # Check if already seeded
        count = self.conn.execute("SELECT COUNT(*) FROM items").fetchone()[0]
        if count > 0:
            logger.info("Database already seeded, skipping.")
            return

        logger.info("Seeding demo data...")
        qr_gen = QRGenerator("labels")

        demo_items = [
            {
                "product_name": "Paracetamol 500mg",
                "category": "Medicines",
                "supplier_name": "HealthFirst Pharma",
                "batch_number": "MED-2024-09",
                "unit_of_measure": "units",
                "quantity": 48,
                "min_stock_level": 20,
                "shelf_location": "Rack-1, Row-A, Slot-1",
                "entry_date": "2024-09-15",
                "expiry_date": "2026-03-31",
                "manufacture_date": "2024-09-01",
                "unit_price": 2.50,
                "notes": "Store below 25°C",
            },
            {
                "product_name": "Amoxicillin 250mg",
                "category": "Medicines",
                "supplier_name": "CureMed Ltd",
                "batch_number": "MED-2023-11",
                "unit_of_measure": "units",
                "quantity": 5,
                "min_stock_level": 15,
                "shelf_location": "Rack-1, Row-B, Slot-2",
                "entry_date": "2023-11-01",
                "expiry_date": "2025-12-01",
                "manufacture_date": "2023-10-15",
                "unit_price": 8.00,
                "notes": "Antibiotic — prescription required",
            },
            {
                "product_name": "Hand Sanitizer 500ml",
                "category": "Cleaning Supplies",
                "supplier_name": "PureCare Co.",
                "batch_number": "CLN-2024-05",
                "unit_of_measure": "units",
                "quantity": 120,
                "min_stock_level": 30,
                "shelf_location": "Rack-4, Row-A, Slot-1",
                "entry_date": "2024-05-20",
                "expiry_date": "2027-06-30",
                "manufacture_date": "2024-05-01",
                "unit_price": 120.00,
                "notes": "70% isopropyl alcohol",
            },
            {
                "product_name": "Basmati Rice 1kg",
                "category": "Food & Beverages",
                "supplier_name": "GrainMart",
                "batch_number": "FOOD-2024-08",
                "unit_of_measure": "kg",
                "quantity": 8,
                "min_stock_level": 15,
                "shelf_location": "Rack-2, Row-C, Slot-3",
                "entry_date": "2024-08-10",
                "expiry_date": "2026-08-15",
                "manufacture_date": "2024-08-01",
                "unit_price": 95.00,
                "notes": "Keep dry",
            },
            {
                "product_name": "USB-C Charging Cable",
                "category": "Electronics",
                "supplier_name": "TechZone",
                "batch_number": "ELEC-2024-12",
                "unit_of_measure": "units",
                "quantity": 45,
                "min_stock_level": 10,
                "shelf_location": "Rack-5, Row-A, Slot-1",
                "entry_date": "2024-12-01",
                "expiry_date": None,
                "manufacture_date": "2024-11-15",
                "unit_price": 299.00,
                "notes": "1.5m length, nylon braided",
            },
            {
                "product_name": "A4 Paper Ream (500 sheets)",
                "category": "Stationery",
                "supplier_name": "PaperWorld",
                "batch_number": "STAT-2024-07",
                "unit_of_measure": "units",
                "quantity": 22,
                "min_stock_level": 10,
                "shelf_location": "Rack-6, Row-B, Slot-1",
                "entry_date": "2024-07-15",
                "expiry_date": None,
                "manufacture_date": None,
                "unit_price": 350.00,
                "notes": "75 GSM, bright white",
            },
            {
                "product_name": "Vitamin C Tablets 1000mg",
                "category": "Medicines",
                "supplier_name": "NutraPlus",
                "batch_number": "MED-2024-10",
                "unit_of_measure": "units",
                "quantity": 200,
                "min_stock_level": 50,
                "shelf_location": "Rack-1, Row-C, Slot-3",
                "entry_date": "2024-10-15",
                "expiry_date": "2026-04-02",
                "manufacture_date": "2024-09-30",
                "unit_price": 4.50,
                "notes": "Effervescent tablets",
            },
            {
                "product_name": "Coconut Oil 1 Liter",
                "category": "Food & Beverages",
                "supplier_name": "NatureFarm",
                "batch_number": "FOOD-2024-09",
                "unit_of_measure": "liters",
                "quantity": 30,
                "min_stock_level": 10,
                "shelf_location": "Rack-2, Row-A, Slot-2",
                "entry_date": "2024-09-20",
                "expiry_date": "2026-09-20",
                "manufacture_date": "2024-09-01",
                "unit_price": 180.00,
                "notes": "Cold-pressed, virgin",
            },
            {
                "product_name": "Whiteboard Markers (Set of 4)",
                "category": "Stationery",
                "supplier_name": "OfficeHub",
                "batch_number": "STAT-2024-03",
                "unit_of_measure": "units",
                "quantity": 3,
                "min_stock_level": 8,
                "shelf_location": "Rack-6, Row-C, Slot-2",
                "entry_date": "2024-03-10",
                "expiry_date": None,
                "manufacture_date": None,
                "unit_price": 80.00,
                "notes": "Black, Blue, Red, Green",
            },
            {
                "product_name": "Dettol Antiseptic 250ml",
                "category": "Cleaning Supplies",
                "supplier_name": "CleanCo",
                "batch_number": "CLN-2023-11",
                "unit_of_measure": "units",
                "quantity": 15,
                "min_stock_level": 10,
                "shelf_location": "Rack-4, Row-B, Slot-1",
                "entry_date": "2023-11-20",
                "expiry_date": "2025-11-30",
                "manufacture_date": "2023-11-01",
                "unit_price": 95.00,
                "notes": "Pine fragrance",
            },
            {
                "product_name": "Thermal Printer Paper Roll",
                "category": "Stationery",
                "supplier_name": "PrintMart",
                "batch_number": "STAT-2024-06",
                "unit_of_measure": "rolls",
                "quantity": 60,
                "min_stock_level": 20,
                "shelf_location": "Rack-6, Row-A, Slot-3",
                "entry_date": "2024-06-05",
                "expiry_date": None,
                "manufacture_date": None,
                "unit_price": 45.00,
                "notes": "80mm x 50m roll",
            },
            {
                "product_name": "Instant Noodles (Pack of 12)",
                "category": "Food & Beverages",
                "supplier_name": "QuickBite",
                "batch_number": "FOOD-2024-11",
                "unit_of_measure": "packets",
                "quantity": 0,
                "min_stock_level": 5,
                "shelf_location": "Rack-3, Row-A, Slot-1",
                "entry_date": "2024-11-01",
                "expiry_date": "2026-12-31",
                "manufacture_date": "2024-10-20",
                "unit_price": 120.00,
                "notes": "Masala flavour",
            },
            {
                "product_name": "AA Batteries (Pack of 10)",
                "category": "Electronics",
                "supplier_name": "PowerMax",
                "batch_number": "ELEC-2024-08",
                "unit_of_measure": "units",
                "quantity": 55,
                "min_stock_level": 20,
                "shelf_location": "Rack-5, Row-B, Slot-2",
                "entry_date": "2024-08-20",
                "expiry_date": "2028-01-01",
                "manufacture_date": "2024-08-01",
                "unit_price": 250.00,
                "notes": "1.5V alkaline",
            },
            {
                "product_name": "Floor Cleaner 1 Liter",
                "category": "Cleaning Supplies",
                "supplier_name": "ShineClean",
                "batch_number": "CLN-2024-03",
                "unit_of_measure": "liters",
                "quantity": 4,
                "min_stock_level": 8,
                "shelf_location": "Rack-4, Row-C, Slot-2",
                "entry_date": "2024-03-15",
                "expiry_date": "2026-06-30",
                "manufacture_date": "2024-03-01",
                "unit_price": 85.00,
                "notes": "Lavender fragrance, anti-bacterial",
            },
            {
                "product_name": "Stapler + Staple Pins Set",
                "category": "Stationery",
                "supplier_name": "OfficeHub",
                "batch_number": "STAT-2024-04",
                "unit_of_measure": "units",
                "quantity": 18,
                "min_stock_level": 5,
                "shelf_location": "Rack-6, Row-D, Slot-1",
                "entry_date": "2024-04-10",
                "expiry_date": None,
                "manufacture_date": None,
                "unit_price": 150.00,
                "notes": "Includes 3 boxes of pins",
            },
        ]

        for item_data in demo_items:
            item_id = self.add_item(item_data)
            # Generate QR label
            try:
                qr_gen.generate_qr(
                    item_id=item_id,
                    qr_data=item_id,
                    product_name=item_data["product_name"],
                    expiry_date=item_data.get("expiry_date"),
                    shelf_location=item_data.get("shelf_location", ""),
                    batch_number=item_data.get("batch_number", ""),
                )
            except Exception as e:
                logger.warning(f"Could not generate QR for {item_id}: {e}")

        self.conn.commit()
        logger.info("Demo data seeded successfully (15 items).")

    def close(self):
        """Close the database connection."""
        if self.conn:
            self.conn.close()
            logger.info("Database connection closed.")
