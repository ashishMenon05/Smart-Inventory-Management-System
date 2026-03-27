"""
core/alerts.py
AlertManager — checks inventory for expiry/stock alerts and generates messages.
"""

import logging
from datetime import date, timedelta

logger = logging.getLogger(__name__)


class AlertManager:
    """Manages expiry and stock level alerts for the SmartStock inventory system."""

    def __init__(self, db_manager):
        """
        Initialize AlertManager with a database reference.

        Args:
            db_manager: DatabaseManager instance.
        """
        self.db = db_manager

    def run_full_inventory_check(self) -> dict:
        """
        Scan the entire inventory for all alert conditions and log to DB.

        Returns:
            Summary dict with keys: expired_count, expiring_count, low_stock_count,
            out_of_stock_count, total_alerts.
        """
        expired = self.check_expiry_alerts()
        stock = self.check_stock_alerts()

        expired_count = sum(1 for a in expired if a["alert_type"] == "EXPIRED")
        expiring_count = sum(1 for a in expired if a["alert_type"] == "EXPIRING_SOON")
        low_stock_count = sum(1 for a in stock if a["alert_type"] == "LOW_STOCK")
        out_of_stock_count = sum(1 for a in stock if a["alert_type"] == "OUT_OF_STOCK")

        # Log all new alerts to the database
        all_alerts = expired + stock
        for alert in all_alerts:
            try:
                self.db.log_alert(
                    item_id=alert["item_id"],
                    alert_type=alert["alert_type"],
                    message=alert["message"],
                    severity=alert["severity"],
                )
            except Exception as e:
                logger.warning(f"Could not log alert: {e}")

        summary = {
            "expired_count": expired_count,
            "expiring_count": expiring_count,
            "low_stock_count": low_stock_count,
            "out_of_stock_count": out_of_stock_count,
            "total_alerts": len(all_alerts),
        }
        logger.info(f"Full inventory check complete: {summary}")
        return summary

    def check_expiry_alerts(self) -> list:
        """
        Find all expired and expiring-soon items and return alert dicts.

        Returns:
            List of alert dicts with keys: item_id, alert_type, message, severity.
        """
        alerts = []

        # Expired items
        for item in self.db.get_expired_items():
            alert_type = "EXPIRED"
            message = self.generate_alert_message(item, alert_type)
            alerts.append({
                "item_id": item["item_id"],
                "alert_type": alert_type,
                "message": message,
                "severity": "CRITICAL",
                "item": item,
            })

        # Expiring soon (within 7 days)
        for item in self.db.get_expiring_items(days_threshold=7):
            # Skip items already in expired list
            if item["expiry_date"] < date.today().isoformat():
                continue
            remaining = (
                date.fromisoformat(item["expiry_date"]) - date.today()
            ).days
            alert_type = "EXPIRING_SOON"
            message = self.generate_alert_message(item, alert_type, remaining_days=remaining)
            alerts.append({
                "item_id": item["item_id"],
                "alert_type": alert_type,
                "message": message,
                "severity": "WARNING",
                "item": item,
            })

        return alerts

    def check_stock_alerts(self) -> list:
        """
        Find all low-stock and out-of-stock items and return alert dicts.

        Returns:
            List of alert dicts with keys: item_id, alert_type, message, severity.
        """
        alerts = []
        for item in self.db.get_low_stock_items():
            if item["quantity"] == 0:
                alert_type = "OUT_OF_STOCK"
                severity = "CRITICAL"
            else:
                alert_type = "LOW_STOCK"
                severity = "WARNING"
            message = self.generate_alert_message(item, alert_type)
            alerts.append({
                "item_id": item["item_id"],
                "alert_type": alert_type,
                "message": message,
                "severity": severity,
                "item": item,
            })
        return alerts

    def generate_alert_message(
        self, item: dict, alert_type: str, remaining_days: int = None
    ) -> str:
        """
        Generate a human-readable alert message string.

        Args:
            item: Item dict from the database.
            alert_type: Type of alert (EXPIRED, EXPIRING_SOON, LOW_STOCK, OUT_OF_STOCK).
            remaining_days: For EXPIRING_SOON alerts, number of days until expiry.

        Returns:
            Formatted alert message string.
        """
        name = item["product_name"]
        item_id = item["item_id"]

        if alert_type == "EXPIRED":
            expiry = item.get("expiry_date", "unknown date")
            return (
                f"CRITICAL: {name} ({item_id}) has EXPIRED on {expiry}! "
                f"Remove from inventory immediately."
            )
        elif alert_type == "EXPIRING_SOON":
            expiry = item.get("expiry_date", "unknown date")
            days_str = f"{remaining_days} day{'s' if remaining_days != 1 else ''}"
            return (
                f"WARNING: {name} ({item_id}) is expiring in {days_str} on {expiry}. "
                f"Take action before it expires."
            )
        elif alert_type == "LOW_STOCK":
            qty = item.get("quantity", 0)
            min_stock = item.get("min_stock_level", 10)
            unit = item.get("unit_of_measure", "units")
            return (
                f"WARNING: {name} ({item_id}) is LOW STOCK — "
                f"only {qty} {unit} remaining (minimum: {min_stock})."
            )
        elif alert_type == "OUT_OF_STOCK":
            return (
                f"CRITICAL: {name} ({item_id}) is OUT OF STOCK — "
                f"0 units remaining. Reorder immediately."
            )
        else:
            return f"INFO: Alert for {name} ({item_id}): {alert_type}"

    def get_alert_color(self, severity: str) -> str:
        """
        Return hex color string for a given severity level.

        Args:
            severity: 'CRITICAL', 'WARNING', or 'INFO'.

        Returns:
            Hex color string.
        """
        colors = {
            "CRITICAL": "#FF3B30",
            "WARNING": "#FF9500",
            "INFO": "#007AFF",
        }
        return colors.get(severity, "#8E8E93")

    def get_alert_icon(self, alert_type: str) -> str:
        """
        Return an emoji icon for the given alert type.

        Args:
            alert_type: Alert type string.

        Returns:
            Emoji string.
        """
        icons = {
            "EXPIRED": "☠️",
            "EXPIRING_SOON": "⚠️",
            "LOW_STOCK": "📦",
            "OUT_OF_STOCK": "❌",
            "LOCATION_MISMATCH": "📍",
        }
        return icons.get(alert_type, "🔔")

    def get_alerts_for_item(self, item: dict) -> list:
        """
        Check an individual item and return a list of alert dicts.

        Args:
            item: Item dict from the database.

        Returns:
            List of alert dicts (may be empty if item is healthy).
        """
        if not item:
            return []
        alerts = []
        today = date.today()

        expiry_date_str = item.get("expiry_date")
        if expiry_date_str:
            try:
                expiry_date = date.fromisoformat(expiry_date_str)
                if expiry_date < today:
                    alerts.append({
                        "alert_type": "EXPIRED",
                        "message": self.generate_alert_message(item, "EXPIRED"),
                        "severity": "CRITICAL",
                    })
                elif expiry_date <= today + timedelta(days=7):
                    remaining = (expiry_date - today).days
                    alerts.append({
                        "alert_type": "EXPIRING_SOON",
                        "message": self.generate_alert_message(
                            item, "EXPIRING_SOON", remaining_days=remaining
                        ),
                        "severity": "WARNING",
                    })
            except (ValueError, TypeError):
                pass

        qty = item.get("quantity", 0)
        min_stock = item.get("min_stock_level", 10)
        if qty == 0:
            alerts.append({
                "alert_type": "OUT_OF_STOCK",
                "message": self.generate_alert_message(item, "OUT_OF_STOCK"),
                "severity": "CRITICAL",
            })
        elif qty <= min_stock:
            alerts.append({
                "alert_type": "LOW_STOCK",
                "message": self.generate_alert_message(item, "LOW_STOCK"),
                "severity": "WARNING",
            })

        return alerts
