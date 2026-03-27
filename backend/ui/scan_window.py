"""
ui/scan_window.py
ScanWindow — live webcam scan window with Tkinter camera feed display.
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import threading
import logging
from pathlib import Path

from ui.styles import Theme

logger = logging.getLogger(__name__)


class ScanWindow(tk.Toplevel):
    """
    Live scan window that embeds the OpenCV camera feed in Tkinter,
    shows detected items in a real-time table, and allows snapshot/report.
    """

    def __init__(self, parent, scanner, db_manager, report_generator=None,
                 voice=None, on_close=None, **kwargs):
        """
        Initialize the scan window.

        Args:
            parent: Parent Tkinter widget.
            scanner: InventoryScanner instance.
            db_manager: DatabaseManager instance.
            report_generator: Optional ReportGenerator instance.
            voice: Optional VoiceAlertSystem instance.
            on_close: Callback invoked when the window is closed.
        """
        super().__init__(parent, **kwargs)
        self.scanner = scanner
        self.db = db_manager
        self.report_gen = report_generator
        self.voice = voice
        self.on_close = on_close
        self._running = False
        self._seen_item_ids = set()

        self.title("📷 Live QR Scanner")
        self.configure(bg=Theme.BG_PRIMARY)
        self.geometry("900x640")
        self.resizable(True, True)
        self.protocol("WM_DELETE_WINDOW", self._on_close)

        self._build_ui()
        self._start_scan()

    def _build_ui(self):
        """Build the scan window layout."""
        # ── Top bar ────────────────────────────────────────────────────────
        top = tk.Frame(self, bg=Theme.BG_SECONDARY, padx=8, pady=6)
        top.pack(fill="x")

        tk.Label(
            top, text="📷  Live QR Code Scanner",
            bg=Theme.BG_SECONDARY, fg=Theme.TEXT_PRIMARY, font=Theme.FONT_HEADING,
        ).pack(side="left", padx=8)

        btn_frame = tk.Frame(top, bg=Theme.BG_SECONDARY)
        btn_frame.pack(side="right", padx=8)

        buttons = [
            ("📸 Snapshot", Theme.ACCENT_BLUE, self._take_snapshot),
            ("📋 Report", Theme.ACCENT_GREEN, self._generate_report),
            ("⏹ Stop Scan", Theme.ACCENT_RED, self._on_close),
        ]
        for text, color, cmd in buttons:
            tk.Button(
                btn_frame, text=text, bg=color, fg=Theme.TEXT_PRIMARY,
                font=Theme.FONT_SMALL, relief="flat", padx=8, pady=4,
                cursor="hand2", command=cmd,
            ).pack(side="left", padx=4)

        # ── Main content ───────────────────────────────────────────────────
        content = tk.Frame(self, bg=Theme.BG_PRIMARY)
        content.pack(fill="both", expand=True)

        # Camera feed (left)
        cam_frame = tk.Frame(content, bg="#000000")
        cam_frame.pack(side="left", fill="both", expand=True, padx=(8, 4), pady=8)

        self._cam_label = tk.Label(
            cam_frame, bg="#000000",
            text="🎥 Starting camera...",
            fg=Theme.TEXT_MUTED, font=Theme.FONT_BODY,
        )
        self._cam_label.pack(fill="both", expand=True)

        # ── Right panel ────────────────────────────────────────────────────
        right = tk.Frame(content, bg=Theme.BG_SECONDARY, width=300)
        right.pack(side="right", fill="y", padx=(4, 8), pady=8)
        right.pack_propagate(False)

        tk.Label(
            right, text="Detected Items",
            bg=Theme.BG_SECONDARY, fg=Theme.TEXT_PRIMARY, font=Theme.FONT_HEADING,
        ).pack(anchor="w", padx=8, pady=(8, 4))

        self._counter_var = tk.StringVar(value="Items this session: 0")
        tk.Label(
            right, textvariable=self._counter_var,
            bg=Theme.BG_SECONDARY, fg=Theme.TEXT_MUTED, font=Theme.FONT_SMALL,
        ).pack(anchor="w", padx=8)

        # Detected items table
        tree_frame = tk.Frame(right, bg=Theme.BG_SECONDARY)
        tree_frame.pack(fill="both", expand=True, padx=8, pady=4)

        self._tree = ttk.Treeview(
            tree_frame,
            columns=("name", "status"),
            show="headings",
            height=12,
        )
        self._tree.heading("name", text="Product Name")
        self._tree.heading("status", text="Status")
        self._tree.column("name", width=160, anchor="w")
        self._tree.column("status", width=80, anchor="center")

        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Treeview",
            background=Theme.BG_TERTIARY,
            foreground=Theme.TEXT_PRIMARY,
            fieldbackground=Theme.BG_TERTIARY,
            rowheight=22,
        )
        style.configure("Treeview.Heading",
            background=Theme.BG_SECONDARY, foreground=Theme.TEXT_PRIMARY,
            font=Theme.FONT_SMALL,
        )
        self._tree.tag_configure("expired", foreground=Theme.ACCENT_RED)
        self._tree.tag_configure("expiring", foreground=Theme.ACCENT_ORANGE)
        self._tree.tag_configure("low", foreground=Theme.ACCENT_YELLOW)
        self._tree.tag_configure("ok", foreground=Theme.ACCENT_GREEN)
        self._tree.tag_configure("unknown", foreground="#BB86FC")

        vsb = ttk.Scrollbar(tree_frame, orient="vertical", command=self._tree.yview)
        self._tree.configure(yscrollcommand=vsb.set)
        vsb.pack(side="right", fill="y")
        self._tree.pack(fill="both", expand=True)

        # Alerts log box
        tk.Label(
            right, text="Alerts This Session",
            bg=Theme.BG_SECONDARY, fg=Theme.ACCENT_ORANGE, font=Theme.FONT_SMALL,
        ).pack(anchor="w", padx=8, pady=(8, 2))

        self._alert_text = tk.Text(
            right, height=6, bg=Theme.BG_TERTIARY, fg=Theme.ACCENT_ORANGE,
            font=Theme.FONT_SMALL, relief="flat", state="disabled",
            insertbackground=Theme.TEXT_PRIMARY,
        )
        self._alert_text.pack(fill="x", padx=8, pady=(0, 8))

    def _start_scan(self):
        """Open the camera and begin the capture-display loop."""
        if not self.scanner.open_camera():
            messagebox.showerror(
                "Camera Error",
                "Could not open camera. Please check your webcam connection.\n\n"
                "Tip: Try changing the camera index in settings, or use 'Scan from Image'.",
                parent=self,
            )
            return

        self.scanner.start_capture_thread()
        self._running = True
        self._update_frame()

    def _update_frame(self):
        """Periodic callback to update the camera display at ~30fps."""
        if not self._running:
            return

        try:
            import numpy as np
            from PIL import Image, ImageTk

            frame = self.scanner.get_current_frame_rgb()
            if frame is not None:
                h, w = frame.shape[:2]
                # Scale to fit the label while preserving aspect ratio
                max_w = self._cam_label.winfo_width() or 560
                max_h = self._cam_label.winfo_height() or 440
                scale = min(max_w / max(w, 1), max_h / max(h, 1), 1.0)
                new_w, new_h = int(w * scale), int(h * scale)
                img = Image.fromarray(frame).resize((new_w, new_h), Image.LANCZOS)
                photo = ImageTk.PhotoImage(img)
                self._cam_label.configure(image=photo, text="")
                self._cam_label.image = photo  # Keep reference

            # Update detected items table
            self._update_detected_table()

        except Exception as e:
            logger.debug(f"Frame update error: {e}")

        self.after(33, self._update_frame)  # ~30fps

    def _update_detected_table(self):
        """Update the right-panel detected items table from current scan results."""
        results = self.scanner.get_detected_items()
        new_items = []

        for result in results:
            item = result.get("item_data")
            alerts = result.get("alerts", [])

            if item:
                item_id = item["item_id"]
                name = item["product_name"][:25]
                alert_types = [a["alert_type"] for a in alerts]

                if "EXPIRED" in alert_types:
                    tag = "expired"
                    status = "☠ EXPIRED"
                elif "EXPIRING_SOON" in alert_types:
                    tag = "expiring"
                    status = "⚠ EXPIRING"
                elif "LOW_STOCK" in alert_types or "OUT_OF_STOCK" in alert_types:
                    tag = "low"
                    status = "📦 LOW"
                else:
                    tag = "ok"
                    status = "✓ OK"

                if item_id not in self._seen_item_ids:
                    self._seen_item_ids.add(item_id)
                    self._tree.insert("", 0, iid=item_id, values=(name, status), tags=(tag,))
                    # Log alerts to text box
                    for al in alerts:
                        self._append_alert(al["message"])
                    # Voice announce critical alerts
                    if self.voice:
                        for al in alerts:
                            if al["severity"] == "CRITICAL":
                                self.voice.announce_alert(al["message"])
            else:
                qr = result.get("qr_data", "?")
                node_id = f"unknown_{qr}"
                if node_id not in self._seen_item_ids:
                    self._seen_item_ids.add(node_id)
                    try:
                        self._tree.insert(
                            "", 0, iid=node_id,
                            values=(f"Unknown QR: {qr[:15]}", "❓"),
                            tags=("unknown",),
                        )
                    except Exception:
                        pass

        # Update counter
        self._counter_var.set(f"Items this session: {len(self._seen_item_ids)}")

    def _append_alert(self, message: str):
        """Append a line to the alerts text box."""
        self._alert_text.configure(state="normal")
        self._alert_text.insert("end", f"• {message}\n")
        self._alert_text.see("end")
        self._alert_text.configure(state="disabled")

    def _take_snapshot(self):
        """Save annotated snapshot to disk."""
        try:
            path = self.scanner.take_snapshot("reports")
            messagebox.showinfo("Snapshot Saved", f"Saved to:\n{path}", parent=self)
        except Exception as e:
            messagebox.showerror("Error", str(e), parent=self)

    def _generate_report(self):
        """Generate a scan session report."""
        if not self.report_gen:
            messagebox.showinfo("No Report Generator", "Report generator not available.", parent=self)
            return
        try:
            session_items = self.scanner.get_session_items()
            file_path, content = self.report_gen.generate_scan_session_report(session_items)
            messagebox.showinfo(
                "Report Generated",
                f"Scan session report saved to:\n{file_path}",
                parent=self,
            )
        except Exception as e:
            messagebox.showerror("Error", str(e), parent=self)

    def _on_close(self):
        """Stop the scan and close the window."""
        self._running = False
        try:
            self.scanner.release()
        except Exception:
            pass
        if self.on_close:
            self.on_close()
        self.destroy()
