"""Retention Desk palette: light console. Coral means act, amber monitor, teal stable."""

BG = "#f4f6f9"        # page
PANEL = "#ffffff"     # panels and charts
PANEL_2 = "#f1f3f6"   # insets, tracks, empty LEDs
LINE = "#dfe3e9"
TEXT = "#141a22"
MUTED = "#4f5866"
DIM = "#6d7684"

CORAL = "#d4462a"   # act / raises the risk (4.6:1 on white)
AMBER = "#a8660a"   # monitor
TEAL = "#0d8370"    # stable / lowers the risk
BLUE = "#2f64c8"    # neutral series

STATUS = {
    "Act": {"label": "Act now", "color": CORAL, "icon": "priority_high"},
    "Monitor": {"label": "Monitor", "color": AMBER, "icon": "visibility"},
    "Stable": {"label": "Stable", "color": TEAL, "icon": "check"},
}

FONT = '"Inter", system-ui, -apple-system, "Segoe UI", Roboto, sans-serif'
DISPLAY = '"Space Grotesk", "Inter", system-ui, sans-serif'
MONO = '"JetBrains Mono", ui-monospace, "SFMono-Regular", Consolas, monospace'
