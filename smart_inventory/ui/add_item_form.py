"""
ui/add_item_form.py
AddItemForm — Tkinter frame for adding new inventory items.
"""

import tkinter as tk
from tkinter import ttk, messagebox
from datetime import date, datetime
import logging
from pathlib import Path

from ui.styles import Theme

logger = logging.getLogger(__name__)


class AddItemForm(tk.Frame):
    """Form for registering new inventory items with QR label generation."""

    CATEGORIES = [
        "Medicines", "Food & Beverages", "Electronics",
        "Stationery", "Cleaning Supplies", "Raw Materials", "Other",
    ]
    UNITS = [
        "units", "kg", "grams", "liters", "ml", "boxes", "packets", "rolls",
    ]

    def __init__(self, parent, db_manager, qr_generator, on_item_saved=None, **kwargs):
        """
        Initialize the Add Item form.

        Args:
            parent: Parent Tkinter widget.
            db_manager: DatabaseManager instance.
            qr_generator: QRGenerator instance.
            on_item_saved: Optional callback called after an item is saved successfully.
        """
        super().__init__(parent, bg=Theme.BG_PRIMARY, **kwargs)
        self.db = db_manager
        self.qr_gen = qr_generator
        self.on_item_saved = on_item_saved
        self._vars = {}
        self._build_ui()

    def _lbl(self, parent, text, row, col, padx=8, pady=4, sticky="e", **kwargs):
        """Helper to create a styled label."""
        label = tk.Label(
            parent, text=text, bg=Theme.BG_SECONDARY,
            fg=Theme.TEXT_SECONDARY, font=Theme.FONT_SMALL, **kwargs
        )
        label.grid(row=row, column=col, padx=padx, pady=pady, sticky=sticky)
        return label

    def _entry(self, parent, var, row, col, width=28, padx=8, pady=4):
        """Helper to create a styled Entry widget."""
        entry = tk.Entry(
            parent, textvariable=var, bg=Theme.BG_TERTIARY, fg=Theme.TEXT_PRIMARY,
            font=Theme.FONT_BODY, relief="flat", insertbackground=Theme.TEXT_PRIMARY,
            width=width,
        )
        entry.grid(row=row, column=col, padx=padx, pady=pady, sticky="ew")
        return entry

    def _build_ui(self):
        """Build all form widgets."""
        # ── Title ──────────────────────────────────────────────────────────
        tk.Label(
            self, text="➕  Add New Inventory Item",
            bg=Theme.BG_PRIMARY, fg=Theme.TEXT_PRIMARY,
            font=Theme.FONT_HEADING,
        ).pack(anchor="w", padx=16, pady=(16, 8))

        # ── Scrollable canvas for the form ─────────────────────────────────
        canvas = tk.Canvas(self, bg=Theme.BG_PRIMARY, highlightthickness=0)
        scrollbar = ttk.Scrollbar(self, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)

        form_frame = tk.Frame(canvas, bg=Theme.BG_SECONDARY, padx=16, pady=16)
        canvas_window = canvas.create_window((0, 0), window=form_frame, anchor="nw")

        def _on_configure(event):
            canvas.configure(scrollregion=canvas.bbox("all"))
            canvas.itemconfig(canvas_window, width=event.width)

        form_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.bind("<Configure>", _on_configure)

        # Mouse wheel scrolling
        def _on_mouse_wheel(event):
            canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
        canvas.bind("<MouseWheel>", _on_mouse_wheel)
        canvas.bind("<Button-4>", lambda e: canvas.yview_scroll(-1, "units"))
        canvas.bind("<Button-5>", lambda e: canvas.yview_scroll(1, "units"))

        self._build_form_fields(form_frame)
        self._build_buttons(form_frame)

    def _build_form_fields(self, parent):
        """Create all the form field rows inside the given parent frame."""
        parent.columnconfigure(1, weight=1)

        # Helper to add StringVar
        def sv(default=""):
            v = tk.StringVar(value=default)
            return v

        # Row 0: Product Name
        self._lbl(parent, "Product Name *", 0, 0)
        self._vars["product_name"] = sv()
        self._entry(parent, self._vars["product_name"], 0, 1)

        # Row 1: Category
        self._lbl(parent, "Category *", 1, 0)
        self._vars["category"] = sv(self.CATEGORIES[0])
        combo = ttk.Combobox(
            parent, textvariable=self._vars["category"],
            values=self.CATEGORIES, state="readonly", width=26,
        )
        combo.grid(row=1, column=1, padx=8, pady=4, sticky="ew")

        # Row 2: Supplier Name
        self._lbl(parent, "Supplier Name *", 2, 0)
        self._vars["supplier_name"] = sv()
        self._entry(parent, self._vars["supplier_name"], 2, 1)

        # Row 3: Batch Number
        self._lbl(parent, "Batch Number *", 3, 0)
        self._vars["batch_number"] = sv()
        self._entry(parent, self._vars["batch_number"], 3, 1)

        # Row 4: Unit of Measure
        self._lbl(parent, "Unit of Measure *", 4, 0)
        self._vars["unit_of_measure"] = sv(self.UNITS[0])
        uom_combo = ttk.Combobox(
            parent, textvariable=self._vars["unit_of_measure"],
            values=self.UNITS, state="readonly", width=26,
        )
        uom_combo.grid(row=4, column=1, padx=8, pady=4, sticky="ew")

        # Row 5: Quantity
        self._lbl(parent, "Quantity *", 5, 0)
        self._vars["quantity"] = tk.IntVar(value=0)
        spinbox = tk.Spinbox(
            parent, textvariable=self._vars["quantity"], from_=0, to=100000,
            bg=Theme.BG_TERTIARY, fg=Theme.TEXT_PRIMARY, font=Theme.FONT_BODY,
            relief="flat", width=10,
        )
        spinbox.grid(row=5, column=1, padx=8, pady=4, sticky="w")

        # Row 6: Min Stock Level
        self._lbl(parent, "Min Stock Level *", 6, 0)
        self._vars["min_stock_level"] = tk.IntVar(value=10)
        spin2 = tk.Spinbox(
            parent, textvariable=self._vars["min_stock_level"], from_=0, to=100000,
            bg=Theme.BG_TERTIARY, fg=Theme.TEXT_PRIMARY, font=Theme.FONT_BODY,
            relief="flat", width=10,
        )
        spin2.grid(row=6, column=1, padx=8, pady=4, sticky="w")

        # Row 7: Shelf Location
        self._lbl(parent, "Shelf Location *", 7, 0)
        self._vars["shelf_location"] = sv()
        shelf_entry = self._entry(parent, self._vars["shelf_location"], 7, 1)
        shelf_entry.configure(fg=Theme.TEXT_MUTED)
        self._vars["shelf_location"].set("Rack-X, Row-Y, Slot-Z")

        def clear_placeholder(event):
            if self._vars["shelf_location"].get() == "Rack-X, Row-Y, Slot-Z":
                self._vars["shelf_location"].set("")
                shelf_entry.configure(fg=Theme.TEXT_PRIMARY)

        shelf_entry.bind("<FocusIn>", clear_placeholder)

        # Row 8: Entry Date
        self._lbl(parent, "Entry Date *", 8, 0)
        self._vars["entry_date"] = sv(date.today().isoformat())
        self._entry(parent, self._vars["entry_date"], 8, 1)

        # Row 9: Expiry Date
        self._lbl(parent, "Expiry Date", 9, 0)
        self._vars["expiry_date"] = sv()
        exp_entry = self._entry(parent, self._vars["expiry_date"], 9, 1)
        tk.Label(
            parent, text="(YYYY-MM-DD, optional for non-perishables)",
            bg=Theme.BG_SECONDARY, fg=Theme.TEXT_MUTED, font=Theme.FONT_SMALL,
        ).grid(row=9, column=2, padx=4, sticky="w")

        # Row 10: Manufacture Date
        self._lbl(parent, "Manufacture Date", 10, 0)
        self._vars["manufacture_date"] = sv()
        self._entry(parent, self._vars["manufacture_date"], 10, 1)

        # Row 11: Unit Price
        self._lbl(parent, "Unit Price (₹)", 11, 0)
        self._vars["unit_price"] = sv()
        self._entry(parent, self._vars["unit_price"], 11, 1)

        # Row 12: Notes
        self._lbl(parent, "Notes", 12, 0, sticky="ne", pady=8)
        self._notes_text = tk.Text(
            parent, bg=Theme.BG_TERTIARY, fg=Theme.TEXT_PRIMARY,
            font=Theme.FONT_BODY, relief="flat", height=4, width=30,
            insertbackground=Theme.TEXT_PRIMARY,
        )
        self._notes_text.grid(row=12, column=1, padx=8, pady=4, sticky="ew")

    def _build_buttons(self, parent):
        """Create action buttons below the form."""
        btn_frame = tk.Frame(parent, bg=Theme.BG_SECONDARY)
        btn_frame.grid(row=13, column=0, columnspan=3, pady=(16, 4))

        buttons = [
            ("💾 Save & Generate QR", Theme.ACCENT_BLUE, self._save_and_generate),
            ("🖨️ Save & Print Label", Theme.ACCENT_GREEN, self._save_and_print),
            ("👁️ Preview QR", Theme.ACCENT_ORANGE, self._preview_qr),
            ("🔄 Reset Form", Theme.BG_TERTIARY, self._reset_form),
        ]
        for text, color, cmd in buttons:
            tk.Button(
                btn_frame, text=text, bg=color, fg=Theme.TEXT_PRIMARY,
                font=Theme.FONT_BODY, relief="flat", padx=12, pady=6,
                cursor="hand2", command=cmd,
            ).pack(side="left", padx=6)

    def _get_form_data(self) -> dict:
        """Collect all form field values into a dict."""
        data = {}
        for key, var in self._vars.items():
            try:
                data[key] = var.get()
            except Exception:
                data[key] = ""
        data["notes"] = self._notes_text.get("1.0", "end-1c")
        return data

    def _validate(self, data: dict) -> list:
        """
        Validate form data. Returns list of error strings (empty = valid).

        Args:
            data: Dict from _get_form_data().

        Returns:
            List of error message strings.
        """
        errors = []

        if len(str(data.get("product_name", "")).strip()) < 3:
            errors.append("Product Name must be at least 3 characters.")
        if not data.get("supplier_name", "").strip():
            errors.append("Supplier Name is required.")
        if not data.get("batch_number", "").strip():
            errors.append("Batch Number is required.")

        shelf = data.get("shelf_location", "").strip()
        if not shelf or shelf == "Rack-X, Row-Y, Slot-Z":
            errors.append("Shelf Location is required.")

        expiry = data.get("expiry_date", "").strip()
        if expiry:
            try:
                exp_date = date.fromisoformat(expiry)
                # Warn but don't block if expiry is in the past (might be intentional for logging)
            except ValueError:
                errors.append("Expiry Date must be in YYYY-MM-DD format.")

        mfg = data.get("manufacture_date", "").strip()
        if mfg:
            try:
                date.fromisoformat(mfg)
            except ValueError:
                errors.append("Manufacture Date must be in YYYY-MM-DD format.")

        price = data.get("unit_price", "").strip()
        if price:
            try:
                float(price)
            except ValueError:
                errors.append("Unit Price must be a valid number.")

        return errors

    def _save_item(self, print_after: bool = False) -> str:
        """
        Validate and save the item to the database.

        Args:
            print_after: If True, call print_label after saving.

        Returns:
            item_id of the saved item, or raises on error.
        """
        data = self._get_form_data()
        errors = self._validate(data)
        if errors:
            messagebox.showerror("Validation Error", "\n".join(errors), parent=self)
            return None

        # Clean up optional fields
        item_dict = {
            "product_name": data["product_name"].strip(),
            "category": data["category"],
            "supplier_name": data["supplier_name"].strip(),
            "batch_number": data["batch_number"].strip(),
            "unit_of_measure": data["unit_of_measure"],
            "quantity": int(data["quantity"]),
            "min_stock_level": int(data["min_stock_level"]),
            "shelf_location": data["shelf_location"].strip(),
            "entry_date": data["entry_date"].strip() or date.today().isoformat(),
            "expiry_date": data["expiry_date"].strip() or None,
            "manufacture_date": data["manufacture_date"].strip() or None,
            "unit_price": float(data["unit_price"]) if data["unit_price"].strip() else None,
            "notes": data["notes"].strip() or None,
        }

        item_id = self.db.add_item(item_dict)

        # Generate QR label
        try:
            label_path = self.qr_gen.generate_qr(
                item_id=item_id,
                qr_data=item_id,
                product_name=item_dict["product_name"],
                expiry_date=item_dict["expiry_date"],
                shelf_location=item_dict["shelf_location"],
                batch_number=item_dict["batch_number"],
            )
        except Exception as e:
            label_path = None
            logger.warning(f"QR label generation failed: {e}")

        # Show success popup
        self._show_success_popup(item_id, item_dict["product_name"], label_path)

        if print_after and label_path:
            try:
                self.qr_gen.print_label(item_id)
            except Exception as e:
                messagebox.showwarning("Print Warning", f"Could not open for printing:\n{e}", parent=self)

        if self.on_item_saved:
            self.on_item_saved(item_id)

        self._reset_form()
        return item_id

    def _show_success_popup(self, item_id: str, product_name: str, label_path):
        """Display a success popup with the generated QR label preview."""
        popup = tk.Toplevel(self)
        popup.title("✅ Item Saved")
        popup.configure(bg=Theme.BG_PRIMARY)
        popup.geometry("420x380")
        popup.resizable(False, False)
        popup.grab_set()

        tk.Label(
            popup, text="✅ Item Saved Successfully!",
            bg=Theme.BG_PRIMARY, fg=Theme.ACCENT_GREEN, font=Theme.FONT_HEADING,
        ).pack(pady=(16, 4))

        tk.Label(
            popup, text=f"{product_name}\nID: {item_id}",
            bg=Theme.BG_PRIMARY, fg=Theme.TEXT_PRIMARY, font=Theme.FONT_BODY,
            justify="center",
        ).pack(pady=4)

        # QR label preview
        if label_path and Path(label_path).exists():
            try:
                from PIL import Image, ImageTk
                img = Image.open(str(label_path)).resize((300, 225), Image.LANCZOS)
                photo = ImageTk.PhotoImage(img)
                lbl = tk.Label(popup, image=photo, bg=Theme.BG_PRIMARY)
                lbl.image = photo  # Keep reference
                lbl.pack(pady=8)
            except Exception:
                tk.Label(
                    popup, text="[QR label generated — see labels/ folder]",
                    bg=Theme.BG_PRIMARY, fg=Theme.TEXT_MUTED, font=Theme.FONT_SMALL,
                ).pack(pady=8)
        else:
            tk.Label(
                popup, text="[QR label generated — see labels/ folder]",
                bg=Theme.BG_PRIMARY, fg=Theme.TEXT_MUTED, font=Theme.FONT_SMALL,
            ).pack(pady=8)

        tk.Button(
            popup, text="OK", bg=Theme.ACCENT_BLUE, fg=Theme.TEXT_PRIMARY,
            font=Theme.FONT_BODY, relief="flat", padx=20, pady=6,
            command=popup.destroy, cursor="hand2",
        ).pack(pady=8)

    def _save_and_generate(self):
        """Save item and generate QR label."""
        self._save_item(print_after=False)

    def _save_and_print(self):
        """Save item, generate QR label, and open for printing."""
        self._save_item(print_after=True)

    def _preview_qr(self):
        """Show a QR label preview without saving to the database."""
        data = self._get_form_data()
        product_name = data.get("product_name", "").strip() or "Preview Item"
        try:
            import tempfile
            from pathlib import Path as _Path
            tmp_dir = _Path(tempfile.mkdtemp())
            label_path = self.qr_gen.generate_qr(
                item_id="PREVIEW",
                qr_data="PREVIEW",
                product_name=product_name,
                expiry_date=data.get("expiry_date") or None,
                shelf_location=data.get("shelf_location", ""),
                batch_number=data.get("batch_number", ""),
            )
            self._show_success_popup("PREVIEW", product_name, label_path)
        except Exception as e:
            messagebox.showerror("Preview Error", str(e), parent=self)

    def _reset_form(self):
        """Reset all form fields back to defaults."""
        for key, var in self._vars.items():
            try:
                if key == "category":
                    var.set(self.CATEGORIES[0])
                elif key == "unit_of_measure":
                    var.set(self.UNITS[0])
                elif key in ("quantity", "min_stock_level"):
                    var.set(0)
                elif key == "entry_date":
                    var.set(date.today().isoformat())
                elif key == "shelf_location":
                    var.set("Rack-X, Row-Y, Slot-Z")
                else:
                    var.set("")
            except Exception:
                pass
        self._notes_text.delete("1.0", "end")
