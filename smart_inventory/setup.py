"""
setup.py
One-click setup script for SmartStock.
Installs dependencies, initializes the database, and seeds demo data.
"""

import sys
import subprocess
import os
from pathlib import Path


def banner(msg: str):
    print(f"\n{'='*52}\n  {msg}\n{'='*52}")


def check_python():
    """Verify Python 3.8+."""
    banner("SmartStock Setup")
    if sys.version_info < (3, 8):
        print(f"❌ Python 3.8+ required. Found: {sys.version}")
        sys.exit(1)
    print(f"✅ Python {sys.version_info.major}.{sys.version_info.minor} detected")


def upgrade_pip():
    """Upgrade pip to the latest version."""
    print("\n📦 Upgrading pip...")
    subprocess.run(
        [sys.executable, "-m", "pip", "install", "--upgrade", "pip"],
        check=True,
    )
    print("✅ pip upgraded")


def install_requirements():
    """Install all packages from requirements.txt."""
    reqs_path = Path(__file__).parent / "requirements.txt"
    if not reqs_path.exists():
        print("❌ requirements.txt not found!")
        sys.exit(1)
    print(f"\n📦 Installing requirements from {reqs_path}...")
    subprocess.run(
        [sys.executable, "-m", "pip", "install", "-r", str(reqs_path)],
        check=True,
    )
    print("✅ All packages installed")


def create_directories():
    """Create required directories."""
    print("\n📁 Creating directories...")
    dirs = ["data", "labels", "reports", "models", "assets"]
    for d in dirs:
        Path(d).mkdir(parents=True, exist_ok=True)
        print(f"   ✓ {d}/")
    print("✅ Directories ready")


def download_yolo():
    """Attempt to download YOLOv8 nano model weights."""
    print("\n🤖 Checking YOLOv8 model...")
    model_path = Path("models") / "yolov8n.pt"
    if model_path.exists():
        print(f"✅ Model already exists: {model_path}")
        return
    try:
        from ultralytics import YOLO
        print("   Downloading yolov8n.pt (~6MB)...")
        model = YOLO("yolov8n.pt")  # auto-downloads
        # Move to models/ folder if downloaded elsewhere
        import shutil
        downloaded = Path("yolov8n.pt")
        if downloaded.exists():
            shutil.move(str(downloaded), str(model_path))
        print(f"✅ YOLOv8 model saved to {model_path}")
    except Exception as e:
        print(f"⚠️  Could not download YOLO model: {e}")
        print("   The app will fall back to OpenCV-only QR detection.")


def initialize_database():
    """Initialize the database and seed demo data."""
    print("\n🗄️  Initializing database...")
    # Add project root to path so imports work
    sys.path.insert(0, str(Path(__file__).parent))

    from core.database import DatabaseManager
    db_path = Path("data") / "inventory.db"

    if db_path.exists():
        print(f"   ℹ️  Database already exists at {db_path}")
        ans = input("   Reseed demo data? This will add items if DB is empty. [y/N]: ").strip().lower()
        if ans not in ("y", "yes"):
            print("   Skipping seed.")
            db = DatabaseManager(str(db_path))
            db.close()
            return

    db = DatabaseManager(str(db_path))
    print("   Seeding 15 demo inventory items...")
    db.seed_demo_data()
    db.close()
    print(f"✅ Database ready: {db_path}")

    # Count items
    db2 = DatabaseManager(str(db_path))
    stats = db2.get_dashboard_stats()
    db2.close()
    print(f"   Total items in DB: {stats['total_items']}")


def generate_assets():
    """Generate app logo and alert sound."""
    print("\n🎨 Generating assets...")
    sys.path.insert(0, str(Path(__file__).parent))

    # Logo
    logo_path = Path("assets") / "logo.png"
    if not logo_path.exists():
        try:
            from PIL import Image, ImageDraw, ImageFont
            img = Image.new("RGB", (200, 200), "#1C1C1E")
            draw = ImageDraw.Draw(img)
            draw.regular_polygon((100, 100, 75), n_sides=6, fill="#007AFF")
            try:
                font = ImageFont.truetype(
                    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 80
                )
            except Exception:
                font = ImageFont.load_default()
            draw.text((68, 50), "S", fill="white", font=font)
            img.save(str(logo_path), "PNG")
            print(f"   ✓ Logo generated: {logo_path}")
        except Exception as e:
            print(f"   ⚠️  Logo generation skipped: {e}")

    # Alert sound
    sound_path = Path("assets") / "alert_sound.wav"
    if not sound_path.exists():
        try:
            import wave, struct, math
            sr, dur, freq, amp = 44100, 0.3, 880, 16000
            n = int(sr * dur)
            with wave.open(str(sound_path), "w") as wav:
                wav.setnchannels(1)
                wav.setsampwidth(2)
                wav.setframerate(sr)
                for i in range(n):
                    t = i / sr
                    env = math.sin(math.pi * t / dur)
                    sample = int(amp * env * math.sin(2 * math.pi * freq * t))
                    wav.writeframes(struct.pack("<h", sample))
            print(f"   ✓ Alert sound generated: {sound_path}")
        except Exception as e:
            print(f"   ⚠️  Sound generation skipped: {e}")

    print("✅ Assets ready")


def print_success():
    """Print final success message."""
    print("\n" + "=" * 52)
    print("  ✅ Setup complete! SmartStock is ready to use.")
    print("")
    print("  To launch the application, run:")
    print("     python main.py")
    print("")
    print("  Features ready:")
    print("   • 15 demo items pre-loaded in database")
    print("   • QR labels generated in labels/")
    print("   • Live multi-QR scanner (requires webcam)")
    print("   • Expiry, stock, and alert monitoring")
    print("=" * 52 + "\n")


if __name__ == "__main__":
    os.chdir(Path(__file__).parent)
    check_python()
    upgrade_pip()
    install_requirements()
    create_directories()
    download_yolo()
    initialize_database()
    generate_assets()
    print_success()
