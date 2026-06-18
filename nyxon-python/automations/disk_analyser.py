"""
Nyxon Automation Suite - Disk Analyser
Scans a drive or folder and reports the top N largest files.
"""

import os
from pathlib import Path
from dataclasses import dataclass

from automations.base import Automation
from utils.settings import settings


@dataclass
class FileEntry:
    """Represents a single file found during the scan."""
    path: Path
    size: int   # bytes

    @property
    def size_str(self) -> str:
        return DiskAnalyser.fmt_bytes(self.size)


class DiskAnalyser(Automation):
    """
    Walks a target directory recursively and collects the largest files.
    Results are stored in self.results (list of FileEntry) after run() completes,
    so the UI can render them however it likes.
    """

    def __init__(self) -> None:
        super().__init__(
            name="Disk Analyser",
            description="Find the largest files eating your disk space.",
        )
        self.scan_path: Path = Path(
            settings.get("disk_analyser.scan_path", self._default_path())
        )
        self.top_n: int = settings.get("disk_analyser.top_n", 10)
        self.results: list[FileEntry] = []

    def run(self) -> None:
        if not self.scan_path.exists():
            self._emit_log(f"Path not found: {self.scan_path}")
            return

        self._emit_log(f"Scanning {self.scan_path} …")
        self._emit_log("This may take a moment on large drives.\n")

        entries: list[FileEntry] = []
        scanned = 0
        errors = 0

        # Walk the directory tree
        for root, dirs, files in os.walk(self.scan_path, topdown=True):
            if self._cancelled:
                self._emit_log("Scan cancelled.")
                return

            # Skip system/hidden dirs to avoid permission errors and irrelevant noise
            dirs[:] = [
                d for d in dirs
                if not d.startswith(".") and d not in _SKIP_DIRS
            ]

            for filename in files:
                if self._cancelled:
                    return
                try:
                    fp = Path(root) / filename
                    size = fp.stat().st_size
                    entries.append(FileEntry(path=fp, size=size))
                    scanned += 1

                    # Keep only top_n*4 candidates in memory to avoid
                    # holding millions of entries at once on large drives
                    if len(entries) > self.top_n * 40:
                        entries.sort(key=lambda e: e.size, reverse=True)
                        entries = entries[: self.top_n * 4]

                except (PermissionError, OSError):
                    errors += 1

        # Final sort and trim
        entries.sort(key=lambda e: e.size, reverse=True)
        self.results = entries[: self.top_n]

        self._emit_log(f"Scanned {scanned:,} files  ({errors} skipped — permission denied)\n")
        self._emit_log(f"Top {len(self.results)} largest files:\n")

        for i, entry in enumerate(self.results, 1):
            self._emit_log(f"  {i:>2}. {entry.size_str:>10}   {entry.path}")
            self._set_progress(i / len(self.results))

    # ── Helpers ───────────────────────────────────────────────────────────────

    @staticmethod
    def fmt_bytes(n: int) -> str:
        for unit in ("B", "KB", "MB", "GB", "TB"):
            if n < 1024:
                return f"{n:.1f} {unit}"
            n /= 1024
        return f"{n:.1f} PB"

    @staticmethod
    def _default_path() -> str:
        import sys
        if sys.platform == "win32":
            return "C:\\"
        return str(Path.home())   # safe fallback on Linux/macOS


# Directories to skip during scanning (system folders, virtual FSes, etc.)
_SKIP_DIRS = {
    # Windows
    "Windows", "System Volume Information", "$Recycle.Bin",
    "Recovery", "PerfLogs", "pagefile.sys",
    # Linux/macOS
    "proc", "sys", "dev", "run", "snap",
    # Common noise
    "__pycache__", ".git", "node_modules",
}
