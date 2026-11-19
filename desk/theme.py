"""Retention Desk palette: a dark operations console. Coral means act, amber monitor, teal stable."""

BG = "#0e1217"
PANEL = "#161c24"
PANEL_2 = "#1c2430"
LINE = "#2a3441"
TEXT = "#e7eaee"
MUTED = "#9aa4b2"
DIM = "#6b7685"

CORAL = "#ff7a59"   # act / raises the risk
AMBER = "#f2b84b"   # monitor
TEAL = "#3ec7b0"    # stable / lowers the risk
BLUE = "#6ea8fe"    # neutral series

STATUS = {
    "Act": {"label": "Act now", "color": CORAL, "icon": "priority_high"},
    "Monitor": {"label": "Monitor", "color": AMBER, "icon": "visibility"},
    "Stable": {"label": "Stable", "color": TEAL, "icon": "check"},
}

FONT = '"Inter", system-ui, -apple-system, "Segoe UI", Roboto, sans-serif'
DISPLAY = '"Space Grotesk", "Inter", system-ui, sans-serif'
MONO = '"JetBrains Mono", ui-monospace, "SFMono-Regular", Consolas, monospace'
