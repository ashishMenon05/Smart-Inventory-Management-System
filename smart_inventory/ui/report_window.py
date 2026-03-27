"""
ui/report_window.py
ReportWindow — Tkinter frame for generating and previewing inventory reports.
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import subprocess
import sys
import logging
from pathlib import Path

from ui.styles import Theme

logger = logging.getLogger(__name__)


class ReportWindow(tk.Frame):
    """Report generation UI with type selection, preview, and file open."""

    def __init__(self, parent, report_generator, **kwargs):
        """
        Initialize the report window frame.

        Args:
            parent: Parent Tkinter widget.
            report_generator: ReportGenerator instance.
        """
        super().__init__(parent, bg=Theme.BG_PRIMARY, **kwargs)
        self.report_gen = report_generator
        self._last_file = None
        self._build_ui()

    def _build_ui(self):
        """Build the report window layout."""
        # ── Title ──────────────────────────────────────────────────────────
        tk.Label(
            self, text="📋  Report Generation",
            bg=Theme.BG_PRIMARY, fg=Theme.TEXT_PRIMARY, font=Theme.FONT_HEADING,
        ).pack(anchor="w", padx=16, pady=(16, 8))

        # ── Report type buttons ────────────────────────────────────────────
        btn_row = tk.Frame(self, bg=Theme.BG_PRIMARY)
        btn_row.pack(fill="x", padx=16, pady=4)

        report_types = [
            ("📋 Full Inventory CSV",
             "Export all inventory items to a CSV file with complete details.",
             self._gen_full_inventory),
            ("⏰ Expiry Report CSV",
             "Export expired and expiring-soon items, sorted by urgency.",
             self._gen_expiry),
            ("📈 Stock Movement CSV",
             "Export all stock changes in the last 30 days.",
             self._gen_movements),
            ("📝 Text Summary Report",
             "Generate a human-readable inventory summary with statistics.",
             self._gen_summary),
        ]

        for i, (title, desc, cmd) in enumerate(report_types):
            card = tk.Frame(btn_row, bg=Theme.BG_SECONDARY, padx=12, pady=10)
            card.grid(row=i // 2, column=i % 2, padx=6, pady=6, sticky="nsew")
            btn_row.columnconfigure(i % 2, weight=1)

            tk.Label(
                card, text=title, bg=Theme.BG_SECONDARY,
                fg=Theme.TEXT_PRIMARY, font=Theme.FONT_BODY, anchor="w",
            ).pack(anchor="w")
            tk.Label(
                card, text=desc, bg=Theme.BG_SECONDARY,
                fg=Theme.TEXT_MUTED, font=Theme.FONT_SMALL,
                wraplength=250, anchor="w", justify="left",
            ).pack(anchor="w", pady=4)
            tk.Button(
                card, text="Generate", bg=Theme.ACCENT_BLUE,
                fg=Theme.TEXT_PRIMARY, font=Theme.FONT_SMALL, relief="flat",
                padx=10, pady=4, cursor="hand2", command=cmd,
            ).pack(anchor="w")

        # ── Days input for movement report ─────────────────────────────────
        day_row = tk.Frame(self, bg=Theme.BG_PRIMARY)
        day_row.pack(anchor="w", padx=16, pady=4)
        tk.Label(
            day_row, text="Days for movement report:",
            bg=Theme.BG_PRIMARY, fg=Theme.TEXT_MUTED, font=Theme.FONT_SMALL,
        ).pack(side="left")
        self._days_var = tk.IntVar(value=30)
        tk.Spinbox(
            day_row, textvariable=self._days_var, from_=1, to=365,
            bg=Theme.BG_TERTIARY, fg=Theme.TEXT_PRIMARY, font=Theme.FONT_SMALL,
            relief="flat", width=6,
        ).pack(side="left", padx=8)

        # ── Preview panel ──────────────────────────────────────────────────
        tk.Label(
            self, text="Report Preview",
            bg=Theme.BG_PRIMARY, fg=Theme.TEXT_SECONDARY, font=Theme.FONT_SMALL,
        ).pack(anchor="w", padx=16, pady=(8, 2))

        preview_frame = tk.Frame(self, bg=Theme.BG_SECONDARY)
        preview_frame.pack(fill="both", expand=True, padx=16, pady=(0, 8))

        self._preview_text = tk.Text(
            preview_frame, bg=Theme.BG_TERTIARY, fg=Theme.TEXT_PRIMARY,
            font=Theme.FONT_MONO, relief="flat", state="disabled",
            insertbackground=Theme.TEXT_PRIMARY, wrap="none",
        )
        vsb = ttk.Scrollbar(preview_frame, orient="vertical",
                            command=self._preview_text.yview)
        hsb = ttk.Scrollbar(preview_frame, orient="horizontal",
                            command=self._preview_text.xview)
        self._preview_text.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        hsb.pack(side="bottom", fill="x")
        vsb.pack(side="right", fill="y")
        self._preview_text.pack(fill="both", expand=True)

        # ── Bottom action buttons ──────────────────────────────────────────
        action_row = tk.Frame(self, bg=Theme.BG_PRIMARY)
        action_row.pack(fill="x", padx=16, pady=(0, 12))

        tk.Button(
            action_row, text="📂 Open File", bg=Theme.ACCENT_ORANGE,
            fg=Theme.TEXT_PRIMARY, font=Theme.FONT_SMALL, relief="flat",
            padx=12, pady=5, cursor="hand2", command=self._open_file,
        ).pack(side="left", padx=4)

        tk.Button(
            action_row, text="🗂️ Open Folder", bg=Theme.BG_TERTIARY,
            fg=Theme.TEXT_PRIMARY, font=Theme.FONT_SMALL, relief="flat",
            padx=12, pady=5, cursor="hand2", command=self._open_folder,
        ).pack(side="left", padx=4)

    def _show_preview(self, content: str):
        """Display content in the preview text widget."""
        self._preview_text.configure(state="normal")
        self._preview_text.delete("1.0", "end")
        self._preview_text.insert("end", content)
        self._preview_text.configure(state="disabled")

    def _gen_full_inventory(self):
        """Generate full inventory CSV."""
        try:
            path = self.report_gen.generate_full_inventory_csv()
            self._last_file = path
            # Preview first 50 lines
            with open(str(path), "r", encoding="utf-8") as f:
                lines = f.readlines()[:50]
            self._show_preview("".join(lines))
            messagebox.showinfo("Done", f"Full inventory CSV saved:\n{path}", parent=self)
        except Exception as e:
            messagebox.showerror("Error", str(e), parent=self)

    def _gen_expiry(self):
        """Generate expiry report CSV."""
        try:
            path = self.report_gen.generate_expiry_report_csv()
            self._last_file = path
            with open(str(path), "r", encoding="utf-8") as f:
                lines = f.readlines()[:50]
            self._show_preview("".join(lines))
            messagebox.showinfo("Done", f"Expiry report saved:\n{path}", parent=self)
        except Exception as e:
            messagebox.showerror("Error", str(e), parent=self)

    def _gen_movements(self):
        """Generate stock movement CSV."""
        try:
            days = int(self._days_var.get())
            path = self.report_gen.generate_stock_movement_csv(days=days)
            self._last_file = path
            with open(str(path), "r", encoding="utf-8") as f:
                lines = f.readlines()[:50]
            self._show_preview("".join(lines))
            messagebox.showinfo("Done", f"Stock movement CSV saved:\n{path}", parent=self)
        except Exception as e:
            messagebox.showerror("Error", str(e), parent=self)

    def _gen_summary(self):
        """Generate text summary report."""
        try:
            path, content = self.report_gen.generate_summary_text_report()
            self._last_file = path
            self._show_preview(content)
            messagebox.showinfo("Done", f"Summary report saved:\n{path}", parent=self)
        except Exception as e:
            messagebox.showerror("Error", str(e), parent=self)

    def _open_file(self):
        """Open the last generated file in the system default app."""
        if not self._last_file:
            messagebox.showinfo("No File", "Generate a report first.", parent=self)
            return
        path = str(self._last_file)
        try:
            if sys.platform == "win32":
                import os
                os.startfile(path)
            elif sys.platform == "darwin":
                subprocess.Popen(["open", path])
            else:
                subprocess.Popen(["xdg-open", path])
        except Exception as e:
            messagebox.showerror("Error", str(e), parent=self)

    def _open_folder(self):
        """Open the reports folder in the system file manager."""
        reports_dir = Path("reports")
        reports_dir.mkdir(exist_ok=True)
        path = str(reports_dir.resolve())
        try:
            if sys.platform == "win32":
                import os
                os.startfile(path)
            elif sys.platform == "darwin":
                subprocess.Popen(["open", path])
            else:
                subprocess.Popen(["xdg-open", path])
        except Exception as e:
            messagebox.showerror("Error", str(e), parent=self)
