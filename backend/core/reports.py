"""
core/reports.py
ReportGenerator — CSV and text report generation for SmartStock.
"""

import csv
import logging
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)


class ReportGenerator:
    """Generates CSV and text reports from the SmartStock inventory database."""

    def __init__(self, db_manager, output_dir: str = "reports"):
        """
        Initialize the report generator.

        Args:
            db_manager: DatabaseManager instance.
            output_dir: Directory where generated reports will be saved.
        """
        self.db = db_manager
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def _timestamp(self) -> str:
        """Return a filesystem-safe timestamp string."""
        return datetime.now().strftime("%Y%m%d_%H%M%S")

    def _write_csv(self, filename: str, rows: list, fieldnames: list) -> Path:
        """
        Write a list of dicts to a CSV file.

        Args:
            filename: Output filename (without directory).
            rows: List of row dicts.
            fieldnames: List of column header names.

        Returns:
            Path to saved CSV.
        """
        path = self.output_dir / filename
        with open(str(path), "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
            writer.writeheader()
            writer.writerows(rows)
        logger.info(f"Report saved: {path}")
        return path

    def generate_full_inventory_csv(self) -> Path:
        """
        Export all inventory items to a CSV file.

        Returns:
            Path to the saved CSV file.
        """
        items = self.db.get_all_items()
        fieldnames = [
            "item_id", "product_name", "category", "supplier_name",
            "batch_number", "unit_of_measure", "quantity", "min_stock_level",
            "shelf_location", "entry_date", "expiry_date", "manufacture_date",
            "unit_price", "notes", "status", "created_at", "updated_at",
        ]
        filename = f"inventory_{self._timestamp()}.csv"
        return self._write_csv(filename, items, fieldnames)

    def generate_expiry_report_csv(self) -> Path:
        """
        Generate CSV of expired and expiring-soon items, sorted by expiry date.

        Returns:
            Path to the saved CSV file.
        """
        expired = self.db.get_expired_items()
        expiring = self.db.get_expiring_items(days_threshold=30)

        # Merge and de-duplicate by item_id
        seen = set()
        combined = []
        for item in expired + expiring:
            if item["item_id"] not in seen:
                seen.add(item["item_id"])
                combined.append(item)

        # Sort by expiry date ascending
        combined.sort(key=lambda x: x.get("expiry_date") or "9999-99-99")

        # Add urgency label
        from datetime import date
        today = date.today().isoformat()
        for item in combined:
            if item.get("expiry_date") and item["expiry_date"] < today:
                item["urgency"] = "EXPIRED"
            else:
                item["urgency"] = "EXPIRING SOON"

        fieldnames = [
            "urgency", "item_id", "product_name", "category", "expiry_date",
            "quantity", "unit_of_measure", "shelf_location", "supplier_name",
            "batch_number",
        ]
        filename = f"expiry_report_{self._timestamp()}.csv"
        return self._write_csv(filename, combined, fieldnames)

    def generate_stock_movement_csv(self, days: int = 30) -> Path:
        """
        Generate CSV of all stock movements in the last N days.

        Args:
            days: Number of days to look back.

        Returns:
            Path to the saved CSV file.
        """
        movements = self.db.get_stock_movements(days=days)
        fieldnames = [
            "movement_id", "item_id", "product_name", "movement_type",
            "quantity_change", "previous_quantity", "new_quantity",
            "reason", "performed_by", "timestamp",
        ]
        filename = f"stock_movements_{self._timestamp()}.csv"
        return self._write_csv(filename, movements, fieldnames)

    def generate_summary_text_report(self) -> tuple:
        """
        Generate a plain-text summary report with key statistics.

        Returns:
            Tuple of (file_path, content_string).
        """
        stats = self.db.get_dashboard_stats()
        items = self.db.get_all_items(filters={"status": "active"})

        # Category breakdown
        categories = {}
        for item in items:
            cat = item["category"]
            categories[cat] = categories.get(cat, 0) + 1

        # Top 5 items by value
        items_with_value = [
            i for i in items if i.get("unit_price") and i.get("quantity", 0) > 0
        ]
        items_with_value.sort(
            key=lambda x: (x["unit_price"] or 0) * x["quantity"], reverse=True
        )
        top_5 = items_with_value[:5]

        lines = [
            "=" * 60,
            "  SMARTSTOCK — INVENTORY SUMMARY REPORT",
            f"  Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "=" * 60,
            "",
            "OVERVIEW",
            "-" * 40,
            f"  Total Active Items    : {stats['total_items']}",
            f"  Total Categories     : {stats['total_categories']}",
            f"  Expiring Soon (7d)   : {stats['items_expiring_soon']}",
            f"  Expired              : {stats['items_expired']}",
            f"  Low Stock            : {stats['items_low_stock']}",
            f"  Unread Alerts        : {stats['total_alerts_unread']}",
            "",
            "CATEGORY BREAKDOWN",
            "-" * 40,
        ]
        for cat, count in sorted(categories.items(), key=lambda x: -x[1]):
            lines.append(f"  {cat:<30} {count} items")

        lines += [
            "",
            "TOP 5 ITEMS BY TOTAL VALUE",
            "-" * 40,
        ]
        for i, item in enumerate(top_5, 1):
            total = (item["unit_price"] or 0) * item["quantity"]
            lines.append(
                f"  {i}. {item['product_name'][:35]:<35} "
                f"Qty: {item['quantity']:>5}  "
                f"Unit: ₹{item['unit_price']:.2f}  "
                f"Total: ₹{total:.2f}"
            )

        lines += ["", "=" * 60, "  END OF REPORT", "=" * 60]

        content = "\n".join(lines)

        ts = self._timestamp()
        file_path = self.output_dir / f"summary_{ts}.txt"
        with open(str(file_path), "w", encoding="utf-8") as f:
            f.write(content)
        logger.info(f"Text summary saved: {file_path}")
        return file_path, content

    def generate_scan_session_report(self, scanned_items_list: list) -> tuple:
        """
        Generate a summary report for items seen in a scan session.

        Args:
            scanned_items_list: List of item dicts from the scan session.

        Returns:
            Tuple of (file_path, content_string).
        """
        from core.alerts import AlertManager

        lines = [
            "=" * 60,
            "  SMARTSTOCK — SCAN SESSION REPORT",
            f"  Session Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"  Items Scanned: {len(scanned_items_list)}",
            "=" * 60,
            "",
            "ITEMS DETECTED IN THIS SCAN SESSION",
            "-" * 40,
        ]

        alert_mgr = AlertManager(self.db)
        total_alerts = 0
        for i, item in enumerate(scanned_items_list, 1):
            if not item:
                continue
            alerts = alert_mgr.get_alerts_for_item(item)
            total_alerts += len(alerts)
            status_str = "✓ OK" if not alerts else " | ".join(
                a["alert_type"] for a in alerts
            )
            lines.append(
                f"  {i:>2}. {item['product_name'][:35]:<35} "
                f"[{item['item_id']}] — {status_str}"
            )
            for alert in alerts:
                lines.append(f"        → {alert['message']}")

        lines += [
            "",
            f"  Total Alerts Found: {total_alerts}",
            "",
            "=" * 60,
        ]
        content = "\n".join(lines)

        ts = self._timestamp()
        file_path = self.output_dir / f"scan_session_{ts}.txt"
        with open(str(file_path), "w", encoding="utf-8") as f:
            f.write(content)
        logger.info(f"Scan session report saved: {file_path}")
        return file_path, content
