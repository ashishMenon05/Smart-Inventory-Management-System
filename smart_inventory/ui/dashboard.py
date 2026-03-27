"""
ui/dashboard.py
DashboardWindow — main application window for SmartStock.
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import threading
import logging
from datetime import datetime
from pathlib import Path

from ui.styles import Theme

logger = logging.getLogger(__name__)


class DashboardWindow:
    """
    Main 1280x800 dark-themed dashboard with:
    - Top navigation bar with live clock
    - Left sidebar with stat cards and alert panel
    - Main content area (4 pages: Overview, Scan, Add Item, Reports)
    """

    def __init__(self, db_manager, qr_generator, scanner, alert_manager,
                 report_generator, voice=None):
        """
        Initialize and launch the main dashboard window.

        Args:
            db_manager: DatabaseManager instance.
            qr_generator: QRGenerator instance.
            scanner: InventoryScanner instance.
            alert_manager: AlertManager instance.
            report_generator: ReportGenerator instance.
            voice: Optional VoiceAlertSystem instance.
        """
        self.db = db_manager
        self.qr_gen = qr_generator
        self.scanner = scanner
        self.alert_mgr = alert_manager
        self.report_gen = report_generator
        self.voice = voice

        self.root = tk.Tk()
        self.root.title("SmartStock — Inventory Manager")
        self.root.geometry("1280x800")
        self.root.minsize(900, 600)
        self.root.configure(bg=Theme.BG_PRIMARY)

        # Apply ttk style
        style = ttk.Style(self.root)
        style.theme_use("clam")
        style.configure("Treeview",
            background=Theme.BG_TERTIARY,
            foreground=Theme.TEXT_PRIMARY,
            fieldbackground=Theme.BG_TERTIARY,
            rowheight=24,
            font=Theme.FONT_SMALL,
        )
        style.configure("Treeview.Heading",
            background=Theme.BG_SECONDARY,
            foreground=Theme.TEXT_PRIMARY,
            font=Theme.FONT_SMALL,
        )
        style.map("Treeview", background=[("selected", Theme.ACCENT_BLUE)])

        self._search_var = tk.StringVar()
        self._category_filter = tk.StringVar(value="All Categories")
        self._active_page = None

        self._build_navbar()
        self._build_main_area()
        self._build_sidebar()

        # Initial data load
        self._refresh_stats()
        self._refresh_table()
        self._refresh_alerts()

        # Auto-refresh every 30 seconds
        self.root.after(30000, self._auto_refresh)

        # Live clock
        self._update_clock()

        logger.info("Dashboard launched.")

    def _build_navbar(self):
        """Build the top navigation bar."""
        navbar = tk.Frame(self.root, bg=Theme.BG_SECONDARY, height=56)
        navbar.pack(fill="x", side="top")
        navbar.pack_propagate(False)

        # App title
        tk.Label(
            navbar, text="⬡  SmartStock",
            bg=Theme.BG_SECONDARY, fg=Theme.ACCENT_BLUE,
            font=("Helvetica", 20, "bold"), padx=16,
        ).pack(side="left", pady=8)

        tk.Label(
            navbar, text="— Inventory Manager",
            bg=Theme.BG_SECONDARY, fg=Theme.TEXT_MUTED,
            font=("Helvetica", 14),
        ).pack(side="left", pady=8)

        # Clock (right)
        self._clock_var = tk.StringVar()
        tk.Label(
            navbar, textvariable=self._clock_var,
            bg=Theme.BG_SECONDARY, fg=Theme.TEXT_MUTED,
            font=Theme.FONT_BODY, padx=16,
        ).pack(side="right", pady=8)

        # Refresh button
        tk.Button(
            navbar, text="🔄 Refresh", bg=Theme.BG_TERTIARY,
            fg=Theme.TEXT_PRIMARY, font=Theme.FONT_SMALL,
            relief="flat", padx=8, pady=4, cursor="hand2",
            command=self.refresh_all,
        ).pack(side="right", padx=4, pady=8)

        # Nav buttons
        self._nav_buttons = {}
        nav_items = [
            ("📊 Dashboard", "dashboard"),
            ("📷 Scan", "scan"),
            ("➕ Add Item", "add_item"),
            ("📋 Reports", "reports"),
        ]
        for label, page_id in nav_items:
            btn = tk.Button(
                navbar, text=label, bg=Theme.BG_SECONDARY,
                fg=Theme.TEXT_PRIMARY, font=Theme.FONT_SMALL,
                relief="flat", padx=10, pady=4, cursor="hand2",
                command=lambda pid=page_id: self._show_page(pid),
                activebackground=Theme.ACCENT_BLUE,
                activeforeground=Theme.TEXT_PRIMARY,
            )
            btn.pack(side="left", padx=2, pady=8)
            self._nav_buttons[page_id] = btn

    def _build_main_area(self):
        """Build the sidebar + main content layout."""
        self._body = tk.Frame(self.root, bg=Theme.BG_PRIMARY)
        self._body.pack(fill="both", expand=True)

    def _build_sidebar(self):
        """Build the left stats + alerts sidebar."""
        sidebar = tk.Frame(self._body, bg=Theme.BG_SECONDARY, width=210)
        sidebar.pack(side="left", fill="y", padx=(0, 0))
        sidebar.pack_propagate(False)

        # ── Stat cards ─────────────────────────────────────────────────────
        tk.Label(
            sidebar, text="INVENTORY STATS",
            bg=Theme.BG_SECONDARY, fg=Theme.TEXT_MUTED,
            font=("Helvetica", 9, "bold"), padx=12,
        ).pack(anchor="w", pady=(12, 4))

        self._stat_labels = {}
        stat_defs = [
            ("📦", "Total Items", "total_items", Theme.ACCENT_BLUE),
            ("🗂️", "Categories", "total_categories", Theme.ACCENT_BLUE),
            ("⚠️", "Expiring Soon", "items_expiring_soon", Theme.ACCENT_ORANGE),
            ("☠️", "Expired", "items_expired", Theme.ACCENT_RED),
            ("📉", "Low Stock", "items_low_stock", Theme.ACCENT_YELLOW),
        ]
        for icon, label, key, color in stat_defs:
            card = tk.Frame(sidebar, bg=Theme.BG_TERTIARY, padx=10, pady=6)
            card.pack(fill="x", padx=8, pady=3)

            row = tk.Frame(card, bg=Theme.BG_TERTIARY)
            row.pack(fill="x")
            tk.Label(row, text=icon, bg=Theme.BG_TERTIARY,
                     fg=color, font=("Helvetica", 14)).pack(side="left")
            tk.Label(row, text=label, bg=Theme.BG_TERTIARY,
                     fg=Theme.TEXT_MUTED, font=Theme.FONT_SMALL).pack(side="left", padx=4)

            num_lbl = tk.Label(card, text="—", bg=Theme.BG_TERTIARY,
                               fg=color, font=("Helvetica", 22, "bold"), anchor="w")
            num_lbl.pack(anchor="w")
            self._stat_labels[key] = num_lbl

        # ── Run Full Check button ───────────────────────────────────────────
        tk.Button(
            sidebar, text="🔍 Run Full Check",
            bg=Theme.ACCENT_BLUE, fg=Theme.TEXT_PRIMARY,
            font=Theme.FONT_SMALL, relief="flat", padx=10, pady=5,
            cursor="hand2", command=self._run_full_check,
        ).pack(fill="x", padx=8, pady=8)

        # ── Unacknowledged Alerts ──────────────────────────────────────────
        tk.Label(
            sidebar, text="🔔 ALERTS",
            bg=Theme.BG_SECONDARY, fg=Theme.TEXT_MUTED,
            font=("Helvetica", 9, "bold"), padx=12,
        ).pack(anchor="w", pady=(4, 2))

        self._alert_frame = tk.Frame(sidebar, bg=Theme.BG_SECONDARY)
        self._alert_frame.pack(fill="both", expand=True, padx=8)

        # Build main content pages
        self._content_area = tk.Frame(self._body, bg=Theme.BG_PRIMARY)
        self._content_area.pack(side="left", fill="both", expand=True)

        self._pages = {}
        self._build_page_dashboard()
        self._build_page_scan()
        self._build_page_add_item()
        self._build_page_reports()

        # Show dashboard by default
        self._show_page("dashboard")

    def _build_page_dashboard(self):
        """Build the main inventory table page."""
        page = tk.Frame(self._content_area, bg=Theme.BG_PRIMARY)
        self._pages["dashboard"] = page

        # ── Search + filter bar ────────────────────────────────────────────
        filter_bar = tk.Frame(page, bg=Theme.BG_SECONDARY, padx=12, pady=8)
        filter_bar.pack(fill="x")

        tk.Label(
            filter_bar, text="🔍", bg=Theme.BG_SECONDARY,
            fg=Theme.TEXT_MUTED, font=Theme.FONT_BODY,
        ).pack(side="left")

        self._search_var.trace_add("write", lambda *a: self._refresh_table())
        tk.Entry(
            filter_bar, textvariable=self._search_var,
            bg=Theme.BG_TERTIARY, fg=Theme.TEXT_PRIMARY,
            font=Theme.FONT_BODY, relief="flat", insertbackground=Theme.TEXT_PRIMARY,
            width=30,
        ).pack(side="left", padx=8, ipady=4)

        tk.Label(
            filter_bar, text="Category:",
            bg=Theme.BG_SECONDARY, fg=Theme.TEXT_MUTED, font=Theme.FONT_SMALL,
        ).pack(side="left", padx=4)

        categories = ["All Categories", "Medicines", "Food & Beverages",
                      "Electronics", "Stationery", "Cleaning Supplies",
                      "Raw Materials", "Other"]
        cat_combo = ttk.Combobox(
            filter_bar, textvariable=self._category_filter,
            values=categories, state="readonly", width=18,
        )
        cat_combo.pack(side="left", padx=4)
        cat_combo.bind("<<ComboboxSelected>>", lambda e: self._refresh_table())

        # Status bar
        self._status_var = tk.StringVar(value="Loading...")
        tk.Label(
            filter_bar, textvariable=self._status_var,
            bg=Theme.BG_SECONDARY, fg=Theme.TEXT_MUTED, font=Theme.FONT_SMALL,
        ).pack(side="right", padx=8)

        # ── Inventory table ────────────────────────────────────────────────
        table_frame = tk.Frame(page, bg=Theme.BG_PRIMARY)
        table_frame.pack(fill="both", expand=True, padx=8, pady=8)

        columns = ("item_id", "product_name", "category", "quantity",
                   "unit", "expiry_date", "location", "status")
        self._tree = ttk.Treeview(table_frame, columns=columns, show="headings")

        col_config = [
            ("item_id", "Item ID", 90),
            ("product_name", "Product Name", 200),
            ("category", "Category", 120),
            ("quantity", "Qty", 60),
            ("unit", "Unit", 70),
            ("expiry_date", "Expiry Date", 100),
            ("location", "Location", 150),
            ("status", "Status", 80),
        ]
        for col_id, header, width in col_config:
            self._tree.heading(col_id, text=header,
                               command=lambda c=col_id: self._sort_by(c))
            self._tree.column(col_id, width=width, anchor="w")

        # Row color tags
        self._tree.tag_configure(Theme.TAG_EXPIRED, background="#3D1C1C",
                                 foreground=Theme.ACCENT_RED)
        self._tree.tag_configure(Theme.TAG_EXPIRING_SOON, background="#3D2E1C",
                                 foreground=Theme.ACCENT_ORANGE)
        self._tree.tag_configure(Theme.TAG_LOW_STOCK, background="#3D3D1C",
                                 foreground=Theme.ACCENT_YELLOW)
        self._tree.tag_configure(Theme.TAG_HEALTHY, background=Theme.BG_TERTIARY,
                                 foreground=Theme.ACCENT_GREEN)

        # Scrollbars
        vsb = ttk.Scrollbar(table_frame, orient="vertical", command=self._tree.yview)
        hsb = ttk.Scrollbar(table_frame, orient="horizontal", command=self._tree.xview)
        self._tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        hsb.pack(side="bottom", fill="x")
        vsb.pack(side="right", fill="y")
        self._tree.pack(fill="both", expand=True)

        # Bind events
        self._tree.bind("<Double-1>", self._on_row_double_click)
        self._tree.bind("<Button-3>", self._on_right_click)

        # Right-click context menu
        self._context_menu = tk.Menu(self.root, tearoff=0, bg=Theme.BG_SECONDARY,
                                     fg=Theme.TEXT_PRIMARY, activebackground=Theme.ACCENT_BLUE)
        self._context_menu.add_command(label="✏️ Edit Item", command=self._edit_selected)
        self._context_menu.add_command(label="📊 Adjust Quantity", command=self._adjust_selected_qty)
        self._context_menu.add_command(label="🖨️ Generate QR Label", command=self._gen_qr_selected)
        self._context_menu.add_separator()
        self._context_menu.add_command(label="🗃️ Archive Item", command=self._archive_selected)

        self._sort_col = None
        self._sort_reverse = False

    def _build_page_scan(self):
        """Build the scan page."""
        from ui.scan_window import ScanWindow

        page = tk.Frame(self._content_area, bg=Theme.BG_PRIMARY)
        self._pages["scan"] = page

        tk.Label(
            page, text="📷  QR Code Scanner",
            bg=Theme.BG_PRIMARY, fg=Theme.TEXT_PRIMARY, font=Theme.FONT_HEADING,
        ).pack(anchor="w", padx=16, pady=(16, 8))

        btn_row = tk.Frame(page, bg=Theme.BG_PRIMARY)
        btn_row.pack(anchor="w", padx=16, pady=8)

        tk.Button(
            btn_row, text="🎥 START LIVE SCAN",
            bg=Theme.ACCENT_BLUE, fg=Theme.TEXT_PRIMARY,
            font=("Helvetica", 16, "bold"), relief="flat",
            padx=24, pady=12, cursor="hand2",
            command=self._open_scan_window,
        ).pack(side="left", padx=4)

        tk.Button(
            btn_row, text="📁 Scan from Image",
            bg=Theme.BG_TERTIARY, fg=Theme.TEXT_PRIMARY,
            font=Theme.FONT_BODY, relief="flat",
            padx=16, pady=8, cursor="hand2",
            command=self._scan_from_image,
        ).pack(side="left", padx=4)

        # Last scan results
        tk.Label(
            page, text="Last Scan Results",
            bg=Theme.BG_PRIMARY, fg=Theme.TEXT_SECONDARY, font=Theme.FONT_SMALL,
        ).pack(anchor="w", padx=16, pady=(16, 2))

        self._last_scan_frame = tk.Frame(page, bg=Theme.BG_SECONDARY)
        self._last_scan_frame.pack(fill="both", expand=True, padx=16, pady=(0, 16))

        last_cols = ("name", "item_id", "category", "status")
        self._last_scan_tree = ttk.Treeview(
            self._last_scan_frame, columns=last_cols, show="headings", height=10
        )
        for col, header in [("name", "Product Name"), ("item_id", "Item ID"),
                             ("category", "Category"), ("status", "Alert Status")]:
            self._last_scan_tree.heading(col, text=header)
            self._last_scan_tree.column(col, width=180 if col == "name" else 120, anchor="w")

        self._last_scan_tree.tag_configure("expired", foreground=Theme.ACCENT_RED)
        self._last_scan_tree.tag_configure("expiring", foreground=Theme.ACCENT_ORANGE)
        self._last_scan_tree.tag_configure("low", foreground=Theme.ACCENT_YELLOW)
        self._last_scan_tree.tag_configure("ok", foreground=Theme.ACCENT_GREEN)

        self._last_scan_tree.pack(fill="both", expand=True)

    def _build_page_add_item(self):
        """Build the add item page."""
        from ui.add_item_form import AddItemForm

        page = tk.Frame(self._content_area, bg=Theme.BG_PRIMARY)
        self._pages["add_item"] = page

        form = AddItemForm(
            page,
            db_manager=self.db,
            qr_generator=self.qr_gen,
            on_item_saved=lambda item_id: self._refresh_table(),
        )
        form.pack(fill="both", expand=True)

    def _build_page_reports(self):
        """Build the reports page."""
        from ui.report_window import ReportWindow

        page = tk.Frame(self._content_area, bg=Theme.BG_PRIMARY)
        self._pages["reports"] = page

        rw = ReportWindow(page, report_generator=self.report_gen)
        rw.pack(fill="both", expand=True)

    # ── Navigation ─────────────────────────────────────────────────────────

    def _show_page(self, page_id: str):
        """Switch to the specified page."""
        for pid, frame in self._pages.items():
            frame.pack_forget()

        if page_id in self._pages:
            self._pages[page_id].pack(fill="both", expand=True)
            self._active_page = page_id

        # Highlight active nav button
        for pid, btn in self._nav_buttons.items():
            btn.configure(
                bg=Theme.ACCENT_BLUE if pid == page_id else Theme.BG_SECONDARY
            )

    # ── Data refresh ────────────────────────────────────────────────────────

    def refresh_all(self):
        """Refresh stats, table, and alerts."""
        self._refresh_stats()
        self._refresh_table()
        self._refresh_alerts()

    def _auto_refresh(self):
        """Auto-refresh every 30 seconds."""
        self.refresh_all()
        self.root.after(30000, self._auto_refresh)

    def _refresh_stats(self):
        """Update the sidebar stat card numbers."""
        try:
            stats = self.db.get_dashboard_stats()
            for key, lbl in self._stat_labels.items():
                val = stats.get(key, 0)
                lbl.configure(text=str(val))
                # Color override for alert counts
                if key in ("items_expiring_soon", "items_low_stock") and val > 0:
                    lbl.configure(fg=Theme.ACCENT_ORANGE if "expiring" in key else Theme.ACCENT_YELLOW)
                elif key == "items_expired" and val > 0:
                    lbl.configure(fg=Theme.ACCENT_RED)
        except Exception as e:
            logger.warning(f"Stats refresh error: {e}")

    def _refresh_table(self):
        """Reload the inventory table with current search/category filters."""
        try:
            search = self._search_var.get().lower()
            cat = self._category_filter.get()
            filters = {}
            if cat and cat != "All Categories":
                filters["category"] = cat

            items = self.db.get_all_items(filters=filters)

            # Apply text search
            if search:
                items = [
                    i for i in items
                    if any(
                        search in str(v).lower()
                        for v in [i.get("product_name", ""), i.get("item_id", ""),
                                  i.get("category", ""), i.get("shelf_location", ""),
                                  i.get("supplier_name", "")]
                    )
                ]

            self._tree.delete(*self._tree.get_children())

            from datetime import date
            today = date.today().isoformat()
            from datetime import timedelta
            week_ahead = (date.today() + timedelta(days=7)).isoformat()

            for item in items:
                expiry = item.get("expiry_date") or ""
                qty = item.get("quantity", 0)
                min_stock = item.get("min_stock_level", 10)

                # Determine row tag
                if expiry and expiry < today:
                    tag = Theme.TAG_EXPIRED
                elif expiry and expiry <= week_ahead:
                    tag = Theme.TAG_EXPIRING_SOON
                elif qty <= min_stock:
                    tag = Theme.TAG_LOW_STOCK
                else:
                    tag = Theme.TAG_HEALTHY

                self._tree.insert(
                    "", "end",
                    iid=item["item_id"],
                    values=(
                        item["item_id"],
                        item["product_name"],
                        item["category"],
                        item["quantity"],
                        item.get("unit_of_measure", ""),
                        expiry or "—",
                        item.get("shelf_location", ""),
                        item.get("status", "active"),
                    ),
                    tags=(tag,),
                )

            total = self.db.get_all_items(filters=({"category": cat} if cat != "All Categories" else None))
            self._status_var.set(f"Showing {len(items)} of {len(total)} items")

        except Exception as e:
            logger.warning(f"Table refresh error: {e}")

    def _refresh_alerts(self):
        """Update the alerts sidebar panel."""
        try:
            for widget in self._alert_frame.winfo_children():
                widget.destroy()

            alerts = self.db.get_unacknowledged_alerts()[:5]
            if not alerts:
                tk.Label(
                    self._alert_frame, text="✅ No active alerts",
                    bg=Theme.BG_SECONDARY, fg=Theme.ACCENT_GREEN, font=Theme.FONT_SMALL,
                ).pack(anchor="w", pady=4)
                return

            for alert in alerts:
                severity = alert.get("severity", "INFO")
                color = self.alert_mgr.get_alert_color(severity)
                icon = self.alert_mgr.get_alert_icon(alert.get("alert_type", ""))

                row_frame = tk.Frame(self._alert_frame, bg=Theme.BG_TERTIARY, padx=6, pady=4)
                row_frame.pack(fill="x", pady=2)

                tk.Label(
                    row_frame, text=f"{icon} {alert.get('alert_type', '').replace('_', ' ')}",
                    bg=Theme.BG_TERTIARY, fg=color, font=Theme.FONT_SMALL, anchor="w",
                ).pack(anchor="w")
                tk.Label(
                    row_frame,
                    text=(alert.get("product_name", "") or alert.get("item_id", ""))[:22],
                    bg=Theme.BG_TERTIARY, fg=Theme.TEXT_MUTED,
                    font=("Helvetica", 8), anchor="w",
                ).pack(anchor="w")

                def _ack(aid=alert["alert_id"]):
                    try:
                        self.db.acknowledge_alert(aid)
                        self._refresh_alerts()
                    except Exception:
                        pass

                tk.Button(
                    row_frame, text="✓ Ack", bg=color,
                    fg=Theme.TEXT_PRIMARY, font=("Helvetica", 8),
                    relief="flat", padx=4, pady=1, cursor="hand2",
                    command=_ack,
                ).pack(anchor="e")

        except Exception as e:
            logger.warning(f"Alerts refresh error: {e}")

    # ── Clock ───────────────────────────────────────────────────────────────

    def _update_clock(self):
        """Update the live clock every second."""
        self._clock_var.set(datetime.now().strftime("  %A, %d %b %Y   %H:%M:%S  "))
        self.root.after(1000, self._update_clock)

    # ── Table actions ───────────────────────────────────────────────────────

    def _get_selected_item(self) -> dict:
        """Return the item dict for the currently selected tree row."""
        selection = self._tree.selection()
        if not selection:
            return None
        item_id = selection[0]
        return self.db.get_item_by_id(item_id)

    def _on_row_double_click(self, event):
        """Open ItemDetailView on double-click."""
        item = self._get_selected_item()
        if item:
            from ui.item_detail_view import ItemDetailView
            ItemDetailView(
                self.root, item, self.db, self.qr_gen,
                on_updated=self.refresh_all,
            )

    def _on_right_click(self, event):
        """Show context menu on right-click."""
        row = self._tree.identify_row(event.y)
        if row:
            self._tree.selection_set(row)
            self._context_menu.post(event.x_root, event.y_root)

    def _edit_selected(self):
        """Open edit dialog for selected item."""
        item = self._get_selected_item()
        if item:
            from ui.item_detail_view import ItemDetailView
            d = ItemDetailView(
                self.root, item, self.db, self.qr_gen,
                on_updated=self.refresh_all,
            )
            d._edit_item()

    def _adjust_selected_qty(self):
        """Open quantity adjustment dialog for selected item."""
        item = self._get_selected_item()
        if item:
            from ui.item_detail_view import AdjustQtyDialog
            AdjustQtyDialog(
                self.root, item, self.db,
                on_done=self.refresh_all,
            )

    def _gen_qr_selected(self):
        """Regenerate QR label for selected item."""
        item = self._get_selected_item()
        if item:
            try:
                path = self.qr_gen.generate_qr(
                    item_id=item["item_id"],
                    qr_data=item.get("qr_code_data", item["item_id"]),
                    product_name=item["product_name"],
                    expiry_date=item.get("expiry_date"),
                    shelf_location=item.get("shelf_location", ""),
                    batch_number=item.get("batch_number", ""),
                )
                messagebox.showinfo("QR Generated", f"Label saved:\n{path}", parent=self.root)
            except Exception as e:
                messagebox.showerror("Error", str(e), parent=self.root)

    def _archive_selected(self):
        """Archive the selected item."""
        item = self._get_selected_item()
        if item and messagebox.askyesno(
            "Archive", f"Archive '{item['product_name']}'?", parent=self.root
        ):
            try:
                self.db.delete_item(item["item_id"])
                self.refresh_all()
            except Exception as e:
                messagebox.showerror("Error", str(e), parent=self.root)

    def _sort_by(self, column: str):
        """Sort the inventory table by the clicked column header."""
        if self._sort_col == column:
            self._sort_reverse = not self._sort_reverse
        else:
            self._sort_col = column
            self._sort_reverse = False

        rows = [(self._tree.set(k, column), k) for k in self._tree.get_children("")]
        rows.sort(reverse=self._sort_reverse)
        for index, (_, k) in enumerate(rows):
            self._tree.move(k, "", index)

    # ── Scan actions ─────────────────────────────────────────────────────────

    def _open_scan_window(self):
        """Open the live scan window."""
        from ui.scan_window import ScanWindow
        from core.scanner import InventoryScanner

        # Create a fresh scanner for each session
        new_scanner = InventoryScanner(
            db_manager=self.db,
            alert_manager=self.alert_mgr,
            camera_index=0,
        )

        def _on_scan_close():
            # Update last scan results table
            session_items = new_scanner.get_session_items()
            self._update_last_scan_table(session_items)
            # Announce result
            if self.voice:
                alerts = sum(
                    len(self.alert_mgr.get_alerts_for_item(i))
                    for i in session_items
                )
                self.voice.announce_scan_result(len(session_items), alerts)
            self.refresh_all()

        ScanWindow(
            self.root,
            scanner=new_scanner,
            db_manager=self.db,
            report_generator=self.report_gen,
            voice=self.voice,
            on_close=_on_scan_close,
        )

    def _scan_from_image(self):
        """Scan QR codes from a user-selected image file."""
        path = filedialog.askopenfilename(
            parent=self.root,
            title="Select Image with QR Codes",
            filetypes=[("Image files", "*.png *.jpg *.jpeg *.bmp *.tiff"), ("All files", "*.*")],
        )
        if not path:
            return
        try:
            results = self.scanner.scan_single_qr_from_image(path)
            items = [r["item_data"] for r in results if r.get("item_data")]
            self._update_last_scan_table(items)
            messagebox.showinfo(
                "Scan Complete",
                f"Found {len(results)} QR code(s)\n{len(items)} item(s) identified.",
                parent=self.root,
            )
            self._show_page("scan")
        except Exception as e:
            messagebox.showerror("Scan Error", str(e), parent=self.root)

    def _update_last_scan_table(self, items: list):
        """Update the last scan results table on the scan page."""
        try:
            self._last_scan_tree.delete(*self._last_scan_tree.get_children())
            from datetime import date
            today = date.today().isoformat()
            from datetime import timedelta
            week_ahead = (date.today() + timedelta(days=7)).isoformat()

            for item in items:
                if not item:
                    continue
                expiry = item.get("expiry_date") or ""
                qty = item.get("quantity", 0)
                min_qty = item.get("min_stock_level", 10)

                alerts = self.alert_mgr.get_alerts_for_item(item)
                if any(a["alert_type"] == "EXPIRED" for a in alerts):
                    tag = "expired"
                    status = "☠ EXPIRED"
                elif any(a["alert_type"] == "EXPIRING_SOON" for a in alerts):
                    tag = "expiring"
                    status = "⚠ EXPIRING"
                elif any(a["alert_type"] in ("LOW_STOCK", "OUT_OF_STOCK") for a in alerts):
                    tag = "low"
                    status = "📦 LOW STOCK"
                else:
                    tag = "ok"
                    status = "✓ OK"

                self._last_scan_tree.insert(
                    "", "end",
                    values=(item["product_name"], item["item_id"], item["category"], status),
                    tags=(tag,),
                )
        except Exception as e:
            logger.warning(f"Last scan table update error: {e}")

    # ── Alert Check ──────────────────────────────────────────────────────────

    def _run_full_check(self):
        """Run a full inventory alert check."""

        def _check():
            try:
                summary = self.alert_mgr.run_full_inventory_check()
                self.root.after(0, lambda: self._show_check_result(summary))
                self.root.after(0, self.refresh_all)
            except Exception as e:
                self.root.after(0, lambda: messagebox.showerror("Error", str(e)))

        threading.Thread(target=_check, daemon=True).start()

    def _show_check_result(self, summary: dict):
        """Show a dialog with the full check results."""
        msg = (
            f"Inventory Check Complete!\n\n"
            f"☠️  Expired: {summary.get('expired_count', 0)}\n"
            f"⚠️  Expiring Soon: {summary.get('expiring_count', 0)}\n"
            f"📦  Low Stock: {summary.get('low_stock_count', 0)}\n"
            f"❌  Out of Stock: {summary.get('out_of_stock_count', 0)}\n"
            f"\nTotal Alerts Generated: {summary.get('total_alerts', 0)}"
        )
        messagebox.showinfo("Full Inventory Check", msg, parent=self.root)

    # ── Lifecycle ────────────────────────────────────────────────────────────

    def run(self):
        """Start the Tkinter main event loop."""
        self.root.mainloop()
