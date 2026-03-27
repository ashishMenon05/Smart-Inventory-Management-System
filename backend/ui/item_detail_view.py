"""
ui/item_detail_view.py
ItemDetailView — popup window showing full details of an inventory item.
"""

import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import logging
from pathlib import Path

from ui.styles import Theme

logger = logging.getLogger(__name__)


class ItemDetailView(tk.Toplevel):
    """Popup window displaying complete item information with action buttons."""

    def __init__(self, parent, item: dict, db_manager, qr_generator,
                 on_updated=None, **kwargs):
        """
        Initialize the item detail popup.

        Args:
            parent: Parent Tkinter widget.
            item: Item dict from the database.
            db_manager: DatabaseManager instance.
            qr_generator: QRGenerator instance.
            on_updated: Optional callback invoked after an edit or quantity change.
        """
        super().__init__(parent, **kwargs)
        self.item = item
        self.db = db_manager
        self.qr_gen = qr_generator
        self.on_updated = on_updated

        self.title(f"Item Detail — {item['item_id']}")
        self.configure(bg=Theme.BG_PRIMARY)
        self.geometry("760x540")
        self.resizable(True, True)
        self.grab_set()

        self._build_ui()

    def _build_ui(self):
        """Build the detail view layout."""
        main = tk.Frame(self, bg=Theme.BG_PRIMARY)
        main.pack(fill="both", expand=True, padx=16, pady=12)

        # ── Left: QR code image ────────────────────────────────────────────
        left = tk.Frame(main, bg=Theme.BG_SECONDARY, padx=12, pady=12)
        left.pack(side="left", fill="y", padx=(0, 12))

        self._load_qr_image(left)

        # Status badge
        status = self.item.get("status", "active").upper()
        status_color = {
            "ACTIVE": Theme.ACCENT_GREEN,
            "EXPIRED": Theme.ACCENT_RED,
            "DEPLETED": Theme.ACCENT_ORANGE,
            "ARCHIVED": Theme.TEXT_MUTED,
        }.get(status, Theme.TEXT_MUTED)

        tk.Label(
            left, text=f"⬤  {status}",
            bg=Theme.BG_SECONDARY, fg=status_color, font=Theme.FONT_SMALL,
        ).pack(pady=(8, 4))

        # Alert badges
        self._show_alert_badges(left)

        # ── Right: Field list ──────────────────────────────────────────────
        right = tk.Frame(main, bg=Theme.BG_PRIMARY)
        right.pack(side="left", fill="both", expand=True)

        canvas = tk.Canvas(right, bg=Theme.BG_PRIMARY, highlightthickness=0)
        scrollbar = ttk.Scrollbar(right, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)

        fields_frame = tk.Frame(canvas, bg=Theme.BG_PRIMARY, padx=4)
        canvas.create_window((0, 0), window=fields_frame, anchor="nw")
        fields_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        canvas.bind("<Button-4>", lambda e: canvas.yview_scroll(-1, "units"))
        canvas.bind("<Button-5>", lambda e: canvas.yview_scroll(1, "units"))

        self._build_fields(fields_frame)

        # ── Bottom buttons ─────────────────────────────────────────────────
        btn_frame = tk.Frame(self, bg=Theme.BG_PRIMARY)
        btn_frame.pack(fill="x", padx=16, pady=(4, 12))

        buttons = [
            ("✏️ Edit", Theme.ACCENT_BLUE, self._edit_item),
            ("📊 Adjust Qty", Theme.ACCENT_GREEN, self._adjust_quantity_dialog),
            ("🖨️ Reprint Label", Theme.ACCENT_ORANGE, self._reprint_label),
            ("🗃️ Archive", Theme.ACCENT_RED, self._archive_item),
        ]
        for text, color, cmd in buttons:
            tk.Button(
                btn_frame, text=text, bg=color, fg=Theme.TEXT_PRIMARY,
                font=Theme.FONT_SMALL, relief="flat", padx=10, pady=5,
                cursor="hand2", command=cmd,
            ).pack(side="left", padx=4)

    def _load_qr_image(self, parent):
        """Load and display the QR label image."""
        label_path = Path("labels") / f"{self.item['item_id']}.png"
        if label_path.exists():
            try:
                from PIL import Image, ImageTk
                img = Image.open(str(label_path)).resize((200, 150), Image.LANCZOS)
                self._qr_photo = ImageTk.PhotoImage(img)
                tk.Label(
                    parent, image=self._qr_photo, bg=Theme.BG_SECONDARY
                ).pack(pady=4)
                return
            except Exception as e:
                logger.warning(f"Could not load QR image: {e}")

        # Placeholder if image not found
        tk.Label(
            parent, text="[QR Code]\nnot found",
            bg=Theme.BG_TERTIARY, fg=Theme.TEXT_MUTED,
            font=Theme.FONT_SMALL, width=20, height=8,
        ).pack(pady=4)

    def _show_alert_badges(self, parent):
        """Display alert badges for this item."""
        try:
            from core.alerts import AlertManager
            alert_mgr = AlertManager(self.db)
            alerts = alert_mgr.get_alerts_for_item(self.item)
            for alert in alerts:
                badge_color = {
                    "CRITICAL": Theme.ACCENT_RED,
                    "WARNING": Theme.ACCENT_ORANGE,
                }.get(alert["severity"], Theme.ACCENT_BLUE)
                icon = {
                    "EXPIRED": "☠️",
                    "EXPIRING_SOON": "⚠️",
                    "LOW_STOCK": "📦",
                    "OUT_OF_STOCK": "❌",
                }.get(alert["alert_type"], "🔔")
                tk.Label(
                    parent,
                    text=f"{icon} {alert['alert_type'].replace('_', ' ')}",
                    bg=badge_color, fg=Theme.TEXT_PRIMARY,
                    font=Theme.FONT_SMALL, padx=6, pady=2,
                ).pack(pady=2, fill="x")
        except Exception as e:
            logger.warning(f"Could not load alerts: {e}")

    def _build_fields(self, parent):
        """Build the label-value pair grid for item fields."""
        tk.Label(
            parent, text=f"📦  {self.item.get('product_name', 'Unknown')}",
            bg=Theme.BG_PRIMARY, fg=Theme.TEXT_PRIMARY,
            font=Theme.FONT_HEADING, anchor="w",
        ).grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 8))

        fields = [
            ("Item ID", "item_id"),
            ("Category", "category"),
            ("Supplier", "supplier_name"),
            ("Batch Number", "batch_number"),
            ("Quantity", None),
            ("Unit of Measure", "unit_of_measure"),
            ("Min Stock Level", "min_stock_level"),
            ("Shelf Location", "shelf_location"),
            ("Entry Date", "entry_date"),
            ("Expiry Date", "expiry_date"),
            ("Manufacture Date", "manufacture_date"),
            ("Unit Price", "unit_price"),
            ("Notes", "notes"),
            ("Created At", "created_at"),
            ("Updated At", "updated_at"),
        ]

        for i, (label, key) in enumerate(fields, 1):
            tk.Label(
                parent, text=f"{label}:", bg=Theme.BG_PRIMARY,
                fg=Theme.TEXT_MUTED, font=Theme.FONT_SMALL, anchor="e", width=16,
            ).grid(row=i, column=0, sticky="e", padx=(0, 8), pady=2)

            if key == "unit_price":
                val = self.item.get(key)
                display = f"₹{val:.2f}" if val is not None else "—"
            elif key is None:  # quantity with unit
                qty = self.item.get("quantity", 0)
                unit = self.item.get("unit_of_measure", "units")
                display = f"{qty} {unit}"
            else:
                display = str(self.item.get(key, "") or "—")

            fg = Theme.TEXT_PRIMARY
            if key == "expiry_date" and display != "—":
                from datetime import date
                try:
                    exp = date.fromisoformat(display)
                    if exp < date.today():
                        fg = Theme.ACCENT_RED
                    elif (exp - date.today()).days <= 7:
                        fg = Theme.ACCENT_ORANGE
                except Exception:
                    pass

            tk.Label(
                parent, text=display, bg=Theme.BG_PRIMARY,
                fg=fg, font=Theme.FONT_BODY, anchor="w", wraplength=400,
            ).grid(row=i, column=1, sticky="w", pady=2)

    def _edit_item(self):
        """Open a simple edit dialog for editable fields."""
        popup = tk.Toplevel(self)
        popup.title(f"Edit — {self.item['item_id']}")
        popup.configure(bg=Theme.BG_PRIMARY)
        popup.geometry("460px x 400px".replace("px ", "").replace("x", "x"))
        popup.geometry("460x420")
        popup.grab_set()

        tk.Label(
            popup, text="Edit Item", bg=Theme.BG_PRIMARY,
            fg=Theme.TEXT_PRIMARY, font=Theme.FONT_HEADING,
        ).pack(pady=12)

        frame = tk.Frame(popup, bg=Theme.BG_SECONDARY, padx=16, pady=12)
        frame.pack(fill="both", expand=True, padx=12, pady=8)

        editable = [
            ("Product Name", "product_name"),
            ("Supplier Name", "supplier_name"),
            ("Shelf Location", "shelf_location"),
            ("Expiry Date (YYYY-MM-DD)", "expiry_date"),
            ("Unit Price (₹)", "unit_price"),
            ("Notes", "notes"),
        ]
        vars_ = {}
        for i, (label, key) in enumerate(editable):
            tk.Label(
                frame, text=label + ":", bg=Theme.BG_SECONDARY,
                fg=Theme.TEXT_SECONDARY, font=Theme.FONT_SMALL, anchor="e", width=22,
            ).grid(row=i, column=0, sticky="e", padx=4, pady=4)
            v = tk.StringVar(value=str(self.item.get(key, "") or ""))
            vars_[key] = v
            tk.Entry(
                frame, textvariable=v, bg=Theme.BG_TERTIARY,
                fg=Theme.TEXT_PRIMARY, font=Theme.FONT_BODY, relief="flat", width=24,
            ).grid(row=i, column=1, sticky="ew", padx=4, pady=4)

        def _save():
            update = {k: v.get().strip() or None for k, v in vars_.items()}
            if update.get("unit_price"):
                try:
                    update["unit_price"] = float(update["unit_price"])
                except ValueError:
                    update["unit_price"] = None
            try:
                self.db.update_item(self.item["item_id"], update)
                self.item.update(update)
                messagebox.showinfo("Saved", "Item updated successfully.", parent=popup)
                popup.destroy()
                if self.on_updated:
                    self.on_updated()
                self.destroy()
            except Exception as e:
                messagebox.showerror("Error", str(e), parent=popup)

        tk.Button(
            popup, text="💾 Save Changes", bg=Theme.ACCENT_BLUE,
            fg=Theme.TEXT_PRIMARY, font=Theme.FONT_BODY, relief="flat",
            padx=16, pady=6, cursor="hand2", command=_save,
        ).pack(pady=8)

    def _adjust_quantity_dialog(self):
        """Open the quantity adjustment dialog."""
        AdjustQtyDialog(self, self.item, self.db, on_done=self._quantity_adjusted)

    def _quantity_adjusted(self):
        """Refresh item data after quantity adjustment."""
        updated = self.db.get_item_by_id(self.item["item_id"])
        if updated:
            self.item = updated
        if self.on_updated:
            self.on_updated()
        self.destroy()

    def _reprint_label(self):
        """Regenerate and open the QR label for printing."""
        try:
            self.qr_gen.generate_qr(
                item_id=self.item["item_id"],
                qr_data=self.item.get("qr_code_data", self.item["item_id"]),
                product_name=self.item["product_name"],
                expiry_date=self.item.get("expiry_date"),
                shelf_location=self.item.get("shelf_location", ""),
                batch_number=self.item.get("batch_number", ""),
            )
            self.qr_gen.print_label(self.item["item_id"])
        except Exception as e:
            messagebox.showerror("Print Error", str(e), parent=self)

    def _archive_item(self):
        """Archive (soft-delete) this item after confirmation."""
        if messagebox.askyesno(
            "Archive Item",
            f"Archive '{self.item['product_name']}'?\nThis will hide it from the main list.",
            parent=self,
        ):
            try:
                self.db.delete_item(self.item["item_id"])
                messagebox.showinfo("Archived", "Item archived successfully.", parent=self)
                if self.on_updated:
                    self.on_updated()
                self.destroy()
            except Exception as e:
                messagebox.showerror("Error", str(e), parent=self)


class AdjustQtyDialog(tk.Toplevel):
    """Small dialog for adjusting item stock quantity."""

    REASONS = [
        "Received Stock",
        "Sold / Used",
        "Disposed",
        "Stock Count Correction",
    ]

    def __init__(self, parent, item: dict, db_manager, on_done=None, **kwargs):
        """
        Initialize the quantity adjustment dialog.

        Args:
            parent: Parent widget.
            item: Item dict.
            db_manager: DatabaseManager instance.
            on_done: Callback invoked after successful adjustment.
        """
        super().__init__(parent, **kwargs)
        self.item = item
        self.db = db_manager
        self.on_done = on_done

        self.title("Adjust Quantity")
        self.configure(bg=Theme.BG_PRIMARY)
        self.geometry("380x280")
        self.resizable(False, False)
        self.grab_set()

        self._build()

    def _build(self):
        """Build the adjustment dialog UI."""
        tk.Label(
            self, text=f"Adjust Quantity\n{self.item['product_name']}",
            bg=Theme.BG_PRIMARY, fg=Theme.TEXT_PRIMARY,
            font=Theme.FONT_HEADING, justify="center",
        ).pack(pady=(16, 4))

        current_qty = self.item.get("quantity", 0)
        unit = self.item.get("unit_of_measure", "units")
        tk.Label(
            self, text=f"Current stock: {current_qty} {unit}",
            bg=Theme.BG_PRIMARY, fg=Theme.TEXT_MUTED, font=Theme.FONT_BODY,
        ).pack()

        frame = tk.Frame(self, bg=Theme.BG_SECONDARY, padx=16, pady=12)
        frame.pack(fill="x", padx=16, pady=12)

        tk.Label(
            frame, text="New Quantity:", bg=Theme.BG_SECONDARY,
            fg=Theme.TEXT_SECONDARY, font=Theme.FONT_SMALL,
        ).grid(row=0, column=0, sticky="e", padx=4, pady=6)

        self._qty_var = tk.IntVar(value=current_qty)
        tk.Spinbox(
            frame, textvariable=self._qty_var, from_=0, to=1000000,
            bg=Theme.BG_TERTIARY, fg=Theme.TEXT_PRIMARY, font=Theme.FONT_BODY,
            relief="flat", width=12,
        ).grid(row=0, column=1, sticky="w", padx=4, pady=6)

        tk.Label(
            frame, text="Movement Type:", bg=Theme.BG_SECONDARY,
            fg=Theme.TEXT_SECONDARY, font=Theme.FONT_SMALL,
        ).grid(row=1, column=0, sticky="e", padx=4, pady=6)

        self._type_var = tk.StringVar(value="ADJUSTMENT")
        ttk.Combobox(
            frame, textvariable=self._type_var,
            values=["IN", "OUT", "ADJUSTMENT", "DISPOSED"],
            state="readonly", width=14,
        ).grid(row=1, column=1, sticky="w", padx=4, pady=6)

        tk.Label(
            frame, text="Reason:", bg=Theme.BG_SECONDARY,
            fg=Theme.TEXT_SECONDARY, font=Theme.FONT_SMALL,
        ).grid(row=2, column=0, sticky="e", padx=4, pady=6)

        self._reason_var = tk.StringVar(value=self.REASONS[0])
        ttk.Combobox(
            frame, textvariable=self._reason_var,
            values=self.REASONS, state="readonly", width=20,
        ).grid(row=2, column=1, sticky="w", padx=4, pady=6)

        tk.Button(
            self, text="✅ Confirm", bg=Theme.ACCENT_GREEN,
            fg=Theme.TEXT_PRIMARY, font=Theme.FONT_BODY, relief="flat",
            padx=16, pady=6, cursor="hand2", command=self._confirm,
        ).pack(pady=8)

    def _confirm(self):
        """Save the quantity adjustment."""
        try:
            new_qty = int(self._qty_var.get())
            movement_type = self._type_var.get()
            reason = self._reason_var.get()
            self.db.update_quantity(
                self.item["item_id"], new_qty, movement_type, reason
            )
            messagebox.showinfo(
                "Updated", f"Quantity updated to {new_qty}.", parent=self
            )
            if self.on_done:
                self.on_done()
            self.destroy()
        except Exception as e:
            messagebox.showerror("Error", str(e), parent=self)
