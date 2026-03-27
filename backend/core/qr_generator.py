"""
core/qr_generator.py
QRGenerator — generates QR code label images for inventory items.
"""

import logging
import subprocess
import sys
from pathlib import Path
from datetime import datetime

logger = logging.getLogger(__name__)


class QRGenerator:
    """Generates QR code label PNG images for SmartStock inventory items."""

    LABEL_WIDTH = 400
    LABEL_HEIGHT = 300

    def __init__(self, output_dir: str):
        """
        Initialize the QR generator.

        Args:
            output_dir: Directory where generated label images will be saved.
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def generate_qr(
        self,
        item_id: str,
        qr_data: str,
        product_name: str,
        expiry_date: str = None,
        shelf_location: str = "",
        batch_number: str = "",
    ) -> Path:
        """
        Generate a QR code label image for an inventory item.

        The label contains:
        - Product name in bold at the top
        - QR code centred
        - Item ID below the QR
        - Expiry date and shelf location in small text

        Args:
            item_id: Inventory item ID (e.g., 'ITEM-00001').
            qr_data: String to encode in the QR code (usually item_id).
            product_name: Human-readable product name for the label.
            expiry_date: Expiry date string (ISO) or None.
            shelf_location: Shelf location string.
            batch_number: Batch number string.

        Returns:
            Path to the saved label PNG.
        """
        try:
            import qrcode
            from PIL import Image, ImageDraw, ImageFont
        except ImportError as e:
            logger.error(f"Required package missing: {e}")
            raise

        # ── Generate QR code ──────────────────────────────────────────────
        qr = qrcode.QRCode(
            version=None,
            error_correction=qrcode.constants.ERROR_CORRECT_H,
            box_size=6,
            border=2,
        )
        qr.add_data(qr_data)
        qr.make(fit=True)
        qr_img = qr.make_image(fill_color="black", back_color="white").convert("RGB")

        # ── Create label canvas ───────────────────────────────────────────
        label = Image.new("RGB", (self.LABEL_WIDTH, self.LABEL_HEIGHT), "white")
        draw = ImageDraw.Draw(label)

        # Border
        draw.rectangle(
            [2, 2, self.LABEL_WIDTH - 3, self.LABEL_HEIGHT - 3],
            outline="black",
            width=2,
        )

        # ── Fonts ──────────────────────────────────────────────────────────
        try:
            from PIL import ImageFont
            font_bold = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 14)
            font_body = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 11)
            font_small = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 9)
        except Exception:
            try:
                font_bold = ImageFont.truetype("arial.ttf", 14)
                font_body = ImageFont.truetype("arial.ttf", 11)
                font_small = ImageFont.truetype("arial.ttf", 9)
            except Exception:
                font_bold = ImageFont.load_default()
                font_body = ImageFont.load_default()
                font_small = ImageFont.load_default()

        # ── Product name (top, centred) ────────────────────────────────────
        # Truncate if too long
        display_name = product_name if len(product_name) <= 38 else product_name[:35] + "..."
        try:
            name_bbox = draw.textbbox((0, 0), display_name, font=font_bold)
            name_w = name_bbox[2] - name_bbox[0]
        except AttributeError:
            name_w = len(display_name) * 8

        name_x = (self.LABEL_WIDTH - name_w) // 2
        draw.text((name_x, 10), display_name, fill="black", font=font_bold)

        # ── QR code (centred) ──────────────────────────────────────────────
        qr_size = 180
        qr_resized = qr_img.resize((qr_size, qr_size), Image.LANCZOS)
        qr_x = (self.LABEL_WIDTH - qr_size) // 2
        qr_y = 32
        label.paste(qr_resized, (qr_x, qr_y))

        # ── Item ID below QR ───────────────────────────────────────────────
        id_text = f"ID: {item_id}"
        try:
            id_bbox = draw.textbbox((0, 0), id_text, font=font_body)
            id_w = id_bbox[2] - id_bbox[0]
        except AttributeError:
            id_w = len(id_text) * 7
        id_x = (self.LABEL_WIDTH - id_w) // 2
        draw.text((id_x, qr_y + qr_size + 4), id_text, fill="black", font=font_body)

        # ── Expiry date ────────────────────────────────────────────────────
        expiry_text = f"Expiry: {expiry_date}" if expiry_date else "Expiry: N/A"
        draw.text((10, self.LABEL_HEIGHT - 50), expiry_text, fill="#333333", font=font_small)

        # ── Shelf location ─────────────────────────────────────────────────
        loc_text = f"Loc: {shelf_location}" if shelf_location else ""
        draw.text((10, self.LABEL_HEIGHT - 36), loc_text, fill="#333333", font=font_small)

        # ── Batch number ───────────────────────────────────────────────────
        batch_text = f"Batch: {batch_number}" if batch_number else ""
        draw.text((10, self.LABEL_HEIGHT - 22), batch_text, fill="#333333", font=font_small)

        # ── Save ───────────────────────────────────────────────────────────
        output_path = self.output_dir / f"{item_id}.png"
        label.save(str(output_path), "PNG")
        logger.info(f"Generated QR label: {output_path}")
        return output_path

    def generate_batch(self, items_list: list) -> list:
        """
        Generate QR labels for a list of items.

        Args:
            items_list: List of item dicts (must have item_id, qr_code_data,
                        product_name, expiry_date, shelf_location, batch_number).

        Returns:
            List of file paths (as strings) for generated labels.
        """
        paths = []
        for item in items_list:
            try:
                path = self.generate_qr(
                    item_id=item["item_id"],
                    qr_data=item.get("qr_code_data", item["item_id"]),
                    product_name=item["product_name"],
                    expiry_date=item.get("expiry_date"),
                    shelf_location=item.get("shelf_location", ""),
                    batch_number=item.get("batch_number", ""),
                )
                paths.append(str(path))
            except Exception as e:
                logger.warning(f"Failed to generate QR for {item.get('item_id', '?')}: {e}")
        return paths

    def print_label(self, item_id: str):
        """
        Open the label image in the system default image viewer for printing.

        Args:
            item_id: The item whose label to open.
        """
        label_path = self.output_dir / f"{item_id}.png"
        if not label_path.exists():
            raise FileNotFoundError(f"Label not found: {label_path}")

        try:
            if sys.platform == "win32":
                import os
                os.startfile(str(label_path))
            elif sys.platform == "darwin":
                subprocess.Popen(["open", str(label_path)])
            else:
                subprocess.Popen(["xdg-open", str(label_path)])
            logger.info(f"Opened label for printing: {label_path}")
        except Exception as e:
            logger.error(f"Could not open label: {e}")
            raise

    def generate_qr_sheet(self, items_list: list) -> Path:
        """
        Generate a printable A4 PDF sheet with multiple QR labels in a 3-column grid.

        Args:
            items_list: List of item dicts to include on the sheet.

        Returns:
            Path to the saved PDF/PNG sheet.
        """
        try:
            from PIL import Image
        except ImportError:
            raise

        cols = 3
        label_w, label_h = self.LABEL_WIDTH, self.LABEL_HEIGHT
        padding = 10

        # Generate individual labels first
        label_paths = self.generate_batch(items_list)
        if not label_paths:
            raise ValueError("No labels to generate sheet for")

        rows = (len(label_paths) + cols - 1) // cols
        sheet_w = cols * label_w + (cols + 1) * padding
        sheet_h = rows * label_h + (rows + 1) * padding

        sheet = Image.new("RGB", (sheet_w, sheet_h), "white")

        for idx, label_path in enumerate(label_paths):
            try:
                lbl_img = Image.open(label_path)
                col = idx % cols
                row = idx // cols
                x = padding + col * (label_w + padding)
                y = padding + row * (label_h + padding)
                sheet.paste(lbl_img, (x, y))
            except Exception as e:
                logger.warning(f"Could not paste label {label_path}: {e}")

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        sheet_path = self.output_dir / f"qr_sheet_{timestamp}.png"
        sheet.save(str(sheet_path), "PNG")
        logger.info(f"Generated QR sheet: {sheet_path}")
        return sheet_path
