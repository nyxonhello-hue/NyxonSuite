"""
Nyxon Automation Suite - Constants
Application-wide constants and type definitions.
"""

from pathlib import Path

# ── App identity ──────────────────────────────────────────────────────────────
APP_NAME = "Nyxon Automation Suite"
APP_AUTHOR = "Nyxon Technologies"
__version__ = "1.0.0"

# ── Window ────────────────────────────────────────────────────────────────────
WINDOW_MIN_WIDTH = 960
WINDOW_MIN_HEIGHT = 620
WINDOW_DEFAULT_SIZE = "1100x680"

# ── Paths ─────────────────────────────────────────────────────────────────────
ASSETS_DIR = Path(__file__).parent.parent / "assets"
ICON_PATH = ASSETS_DIR / "icon.ico"

# ── File Organizer ────────────────────────────────────────────────────────────
EXTENSION_MAP: dict[str, str] = {
    # Images
    ".jpg": "Images", ".jpeg": "Images", ".png": "Images",
    ".gif": "Images", ".bmp": "Images", ".webp": "Images", ".svg": "Images",
    # Videos
    ".mp4": "Videos", ".mkv": "Videos", ".avi": "Videos",
    ".mov": "Videos", ".wmv": "Videos",
    # Audio
    ".mp3": "Audio", ".wav": "Audio", ".flac": "Audio",
    ".aac": "Audio", ".ogg": "Audio",
    # Documents
    ".pdf": "Documents", ".doc": "Documents", ".docx": "Documents",
    ".xls": "Documents", ".xlsx": "Documents", ".ppt": "Documents",
    ".pptx": "Documents", ".txt": "Documents", ".md": "Documents",
    # Archives
    ".zip": "Archives", ".rar": "Archives", ".7z": "Archives",
    ".tar": "Archives", ".gz": "Archives",
    # Code
    ".py": "Code", ".js": "Code", ".ts": "Code", ".html": "Code",
    ".css": "Code", ".json": "Code", ".xml": "Code", ".dart": "Code",
    ".kt": "Code",
    # Executables
    ".exe": "Executables", ".msi": "Executables", ".bat": "Executables",
}

# ── Timing ────────────────────────────────────────────────────────────────────
UI_POLL_MS = 100          # How often the UI polls thread progress (ms)
NETWORK_TIMEOUT_S = 3     # Default ping timeout in seconds

# ── Status strings ────────────────────────────────────────────────────────────
STATUS_IDLE = "Idle"
STATUS_RUNNING = "Running…"
STATUS_DONE = "Done"
STATUS_ERROR = "Error"
STATUS_CANCELLED = "Cancelled"
