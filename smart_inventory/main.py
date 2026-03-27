"""
main.py
Entry point for SmartStock — Smart Inventory Management System.
"""

import sys
import logging
import os
from pathlib import Path

# ── Configure logging ──────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(name)s — %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("smartstock")


def check_python_version():
    """Ensure Python 3.8 or newer is being used."""
    if sys.version_info < (3, 8):
        print(
            f"❌ Python 3.8+ is required. You are using {sys.version}.\n"
            f"   Download from: https://python.org"
        )
        sys.exit(1)
    logger.info(f"Python {sys.version_info.major}.{sys.version_info.minor} OK")


def check_packages():
    """Check that all required packages are importable."""
    required = {
        "cv2": "opencv-python",
        "PIL": "Pillow",
        "qrcode": "qrcode[pil]",
        "numpy": "numpy",
    }
    missing = []
    for module, package in required.items():
        try:
            __import__(module)
        except ImportError:
            missing.append(package)

    if missing:
        print(
            "❌ Required packages are missing:\n"
            + "\n".join(f"   • {p}" for p in missing)
            + "\n\n   Run:  pip install -r requirements.txt"
        )
        sys.exit(1)

    # Optional packages
    for mod in ("pyttsx3", "ultralytics"):
        try:
            __import__(mod)
        except ImportError:
            logger.info(f"Optional package '{mod}' not found — feature will be disabled.")

    logger.info("All required packages are available.")


def create_directories():
    """Create required directories if they don't exist."""
    dirs = ["data", "labels", "reports", "models", "assets"]
    for d in dirs:
        Path(d).mkdir(parents=True, exist_ok=True)
    logger.info("Directories verified.")


def generate_alert_sound():
    """Generate a simple beep WAV file for alert notifications."""
    sound_path = Path("assets") / "alert_sound.wav"
    if sound_path.exists():
        return
    try:
        import wave
        import struct
        import math

        sample_rate = 44100
        duration = 0.3   # seconds
        frequency = 880  # Hz (A5)
        amplitude = 16000
        n_samples = int(sample_rate * duration)

        with wave.open(str(sound_path), "w") as wav:
            wav.setnchannels(1)
            wav.setsampwidth(2)
            wav.setframerate(sample_rate)
            for i in range(n_samples):
                t = i / sample_rate
                # Fade in/out envelope
                env = math.sin(math.pi * t / duration)
                sample = int(amplitude * env * math.sin(2 * math.pi * frequency * t))
                wav.writeframes(struct.pack("<h", sample))
        logger.info(f"Alert sound generated: {sound_path}")
    except Exception as e:
        logger.warning(f"Could not generate alert sound: {e}")


def generate_logo():
    """Generate a simple app logo PNG."""
    logo_path = Path("assets") / "logo.png"
    if logo_path.exists():
        return
    try:
        from PIL import Image, ImageDraw, ImageFont
        img = Image.new("RGB", (200, 200), "#1C1C1E")
        draw = ImageDraw.Draw(img)
        # Draw a hexagon-like shape
        draw.regular_polygon((100, 100, 75), n_sides=6, fill="#007AFF")
        # "S" for SmartStock
        try:
            font = ImageFont.truetype(
                "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 80
            )
        except Exception:
            font = ImageFont.load_default()
        draw.text((68, 50), "S", fill="white", font=font)
        img.save(str(logo_path), "PNG")
        logger.info(f"Logo generated: {logo_path}")
    except Exception as e:
        logger.warning(f"Could not generate logo: {e}")


def main():
    """Main entry point — sets up and launches SmartStock."""
    print("\n" + "=" * 52)
    print("  ⬡  SmartStock — Smart Inventory Manager")
    print("  Starting up...")
    print("=" * 52 + "\n")

    # Step 1: Check Python version
    check_python_version()

    # Step 2: Check required packages
    check_packages()

    # Step 3: Create directories
    create_directories()

    # Step 4: Generate assets
    generate_alert_sound()
    generate_logo()

    # Step 5: Initialize DatabaseManager
    from core.database import DatabaseManager
    db_path = Path("data") / "inventory.db"
    is_new_db = not db_path.exists()

    try:
        db = DatabaseManager(str(db_path))
        logger.info(f"Database connected: {db_path}")
    except Exception as e:
        # Backup corrupted DB and create fresh one
        import shutil
        from datetime import datetime
        if db_path.exists():
            backup = db_path.parent / f"inventory_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
            shutil.copy2(str(db_path), str(backup))
            logger.warning(f"Database backed up to: {backup}")
            db_path.unlink(missing_ok=True)
        db = DatabaseManager(str(db_path))
        is_new_db = True
        logger.info("Fresh database created after backup.")

    # Step 6: Seed demo data if DB is empty
    if is_new_db:
        logger.info("New database detected — seeding demo data...")
        try:
            db.seed_demo_data()
        except Exception as e:
            logger.warning(f"Demo data seeding error: {e}")

    # Step 7: Initialize AlertManager and run initial check
    from core.alerts import AlertManager
    alert_mgr = AlertManager(db)
    try:
        summary = alert_mgr.run_full_inventory_check()
        logger.info(f"Initial alert check: {summary}")
    except Exception as e:
        logger.warning(f"Initial alert check failed: {e}")

    # Step 8: Initialize QRGenerator
    from core.qr_generator import QRGenerator
    qr_gen = QRGenerator("labels")

    # Step 9: Initialize InventoryScanner (camera opened on demand, not now)
    from core.scanner import InventoryScanner
    scanner = InventoryScanner(db_manager=db, alert_manager=alert_mgr, camera_index=0)

    # Step 10: Initialize ReportGenerator
    from core.reports import ReportGenerator
    report_gen = ReportGenerator(db, output_dir="reports")

    # Step 11: Initialize VoiceAlertSystem
    from core.voice import VoiceAlertSystem
    voice = VoiceAlertSystem()

    # Step 12: Launch DashboardWindow
    from ui.dashboard import DashboardWindow
    dashboard = DashboardWindow(
        db_manager=db,
        qr_generator=qr_gen,
        scanner=scanner,
        alert_manager=alert_mgr,
        report_generator=report_gen,
        voice=voice,
    )

    logger.info("Dashboard launched — SmartStock is running.")

    try:
        dashboard.run()
    finally:
        # Step 13: Clean shutdown
        logger.info("Shutting down SmartStock...")
        try:
            scanner.release()
        except Exception:
            pass
        try:
            db.close()
        except Exception:
            pass
        print("\n✅ SmartStock closed cleanly. Goodbye!\n")


if __name__ == "__main__":
    main()
