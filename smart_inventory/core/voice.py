"""
core/voice.py
VoiceAlertSystem — optional text-to-speech for SmartStock alerts.
"""

import logging
import threading

logger = logging.getLogger(__name__)


class VoiceAlertSystem:
    """Optional offline text-to-speech alert system using pyttsx3."""

    def __init__(self):
        """
        Initialize the TTS engine. Sets self.available = False if pyttsx3
        is not installed or fails to initialize.
        """
        self.available = False
        self.engine = None
        self._lock = threading.Lock()

        try:
            import pyttsx3
            self.engine = pyttsx3.init()
            self.engine.setProperty("rate", 150)
            self.engine.setProperty("volume", 1.0)
            self.available = True
            logger.info("VoiceAlertSystem initialized successfully.")
        except Exception as e:
            logger.warning(f"pyttsx3 not available — voice alerts disabled. Reason: {e}")

    def speak(self, message: str):
        """
        Speak a message in a background thread so the UI is not blocked.

        Args:
            message: Text to speak aloud.
        """
        if not self.available:
            return

        def _speak():
            try:
                with self._lock:
                    engine = None
                    try:
                        import pyttsx3
                        engine = pyttsx3.init()
                        engine.setProperty("rate", 150)
                        engine.setProperty("volume", 1.0)
                        engine.say(message)
                        engine.runAndWait()
                    finally:
                        if engine:
                            try:
                                engine.stop()
                            except Exception:
                                pass
            except Exception as e:
                logger.warning(f"Voice speak error: {e}")

        thread = threading.Thread(target=_speak, daemon=True)
        thread.start()

    def announce_scan_result(self, item_count: int, alert_count: int):
        """
        Announce a scan completion summary.

        Args:
            item_count: Number of items detected in the scan.
            alert_count: Number of alerts found during the scan.
        """
        alert_word = "alert" if alert_count == 1 else "alerts"
        item_word = "item" if item_count == 1 else "items"
        message = (
            f"Scan complete. {item_count} {item_word} detected. "
            f"{alert_count} {alert_word} found."
        )
        self.speak(message)

    def announce_alert(self, alert_message: str):
        """
        Speak a full alert message.

        Args:
            alert_message: The alert message to announce.
        """
        # Strip emoji and special characters that TTS might not handle well
        clean_msg = alert_message.replace("☠️", "").replace("⚠️", "").replace("📦", "")
        clean_msg = clean_msg.replace("❌", "").replace("🔔", "").strip()
        self.speak(clean_msg)

    def announce_expired(self, product_name: str):
        """
        Announce that a specific product has expired.

        Args:
            product_name: Name of the expired product.
        """
        self.speak(f"{product_name} has expired. Please remove immediately.")
