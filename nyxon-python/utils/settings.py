"""
Nyxon Automation Suite - Settings Utility
Loads, saves, and provides access to application configuration.
"""

import json
from pathlib import Path
from utils.logger import get_logger

logger = get_logger(__name__)

CONFIG_DIR = Path.home() / ".nyxon"
CONFIG_FILE = CONFIG_DIR / "config.json"

DEFAULTS: dict = {
    "theme": "dark",
    "accent_color": "#7B5CF0",
    "bg_dark": True,
        "file_organizer": {
        "target_folder": str(Path.home() / "Downloads"),
        "organize_by": "extension",
    },
    "system_flush": {
        "clear_temp": True,
        "clear_prefetch": False,
        "empty_recycle_bin": False,
    },
    "network_checker": {
        "hosts": ["8.8.8.8", "1.1.1.1", "google.com"],
        "timeout_seconds": 3,
    },
    "startup_manager": {
        "show_disabled": True,
    },
}


class Settings:
    """Manages persistent application configuration via a JSON file."""

    def __init__(self) -> None:
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        self._data: dict = {}
        self.load()

    def load(self) -> None:
        """Load settings from disk, falling back to defaults for missing keys."""
        if CONFIG_FILE.exists():
            try:
                with CONFIG_FILE.open("r", encoding="utf-8") as f:
                    stored = json.load(f)
                self._data = self._deep_merge(DEFAULTS, stored)
                logger.debug("Settings loaded from %s", CONFIG_FILE)
            except (json.JSONDecodeError, OSError) as exc:
                logger.warning("Could not read config (%s). Using defaults.", exc)
                self._data = dict(DEFAULTS)
        else:
            self._data = dict(DEFAULTS)
            self.save()

    def save(self) -> None:
        """Persist current settings to disk."""
        try:
            with CONFIG_FILE.open("w", encoding="utf-8") as f:
                json.dump(self._data, f, indent=2)
            logger.debug("Settings saved.")
        except OSError as exc:
            logger.error("Could not save config: %s", exc)

    def get(self, key: str, default=None):
        """Retrieve a top-level or dot-separated nested value."""
        keys = key.split(".")
        val = self._data
        for k in keys:
            if isinstance(val, dict):
                val = val.get(k, default)
            else:
                return default
        return val

    def set(self, key: str, value) -> None:
        """Set a top-level or dot-separated nested value and save."""
        keys = key.split(".")
        d = self._data
        for k in keys[:-1]:
            d = d.setdefault(k, {})
        d[keys[-1]] = value
        self.save()

    @staticmethod
    def _deep_merge(base: dict, override: dict) -> dict:
        result = dict(base)
        for k, v in override.items():
            if k in result and isinstance(result[k], dict) and isinstance(v, dict):
                result[k] = Settings._deep_merge(result[k], v)
            else:
                result[k] = v
        return result


# Module-level singleton
settings = Settings()
