"""
ui/styles.py
Theme constants for SmartStock dashboard — dark iOS-inspired palette.
"""


class Theme:
    """Color, font, and layout constants for the SmartStock UI."""

    # ── Background colors ──────────────────────────────────────────────────
    BG_PRIMARY   = "#1C1C1E"   # Dark background (app root)
    BG_SECONDARY = "#2C2C2E"   # Card / sidebar background
    BG_TERTIARY  = "#3A3A3C"   # Input field background
    BG_HOVER     = "#48484A"   # Hover state

    # ── Accent colors ──────────────────────────────────────────────────────
    ACCENT_BLUE   = "#007AFF"  # Primary action color
    ACCENT_GREEN  = "#34C759"  # Success / healthy stock
    ACCENT_ORANGE = "#FF9500"  # Warning / expiring soon
    ACCENT_RED    = "#FF3B30"  # Critical / expired
    ACCENT_YELLOW = "#FFD60A"  # Low stock

    # ── Text colors ────────────────────────────────────────────────────────
    TEXT_PRIMARY   = "#FFFFFF"
    TEXT_SECONDARY = "#EBEBF5"
    TEXT_MUTED     = "#8E8E93"

    # ── Fonts ──────────────────────────────────────────────────────────────
    FONT_TITLE   = ("Helvetica", 22, "bold")
    FONT_HEADING = ("Helvetica", 16, "bold")
    FONT_BODY    = ("Helvetica", 12)
    FONT_SMALL   = ("Helvetica", 10)
    FONT_MONO    = ("Courier", 11)

    # ── Layout ─────────────────────────────────────────────────────────────
    CORNER_RADIUS = 8
    PADDING       = 16

    # ── Treeview row tags ──────────────────────────────────────────────────
    TAG_EXPIRED       = "expired"
    TAG_EXPIRING_SOON = "expiring_soon"
    TAG_LOW_STOCK     = "low_stock"
    TAG_HEALTHY       = "healthy"
