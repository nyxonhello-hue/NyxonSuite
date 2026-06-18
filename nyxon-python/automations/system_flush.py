"""
Nyxon Automation Suite - System Flush
Clears Windows temp folders and optionally empties the Recycle Bin.
"""

import os
import sys
import shutil
import subprocess
import platform
from pathlib import Path

from automations.base import Automation
from utils.settings import settings

IS_WINDOWS = sys.platform == "win32"


class SystemFlush(Automation):
    """
    Frees disk space by deleting temporary files.

    Targets:
        - %TEMP% (user temp folder)
        - C:\\Windows\\Temp (system temp, best-effort)
        - C:\\Windows\\Prefetch (optional, requires admin)
        - Recycle Bin (optional)
    """

    def __init__(self) -> None:
        super().__init__(
            name="System Flush",
            description="Clear temp files and free up disk space.",
        )

    def run(self) -> None:
        cfg = settings.get("system_flush", {})
        clear_temp: bool = cfg.get("clear_temp", True)
        clear_prefetch: bool = cfg.get("clear_prefetch", False)
        empty_recycle: bool = cfg.get("empty_recycle_bin", False)

        steps = []
        if clear_temp:
            if IS_WINDOWS:
                steps.append(("User Temp", Path(os.environ.get("TEMP", "C:/Temp"))))
                steps.append(("System Temp", Path("C:/Windows/Temp")))
            else:
                # Linux/macOS temp locations
                steps.append(("Temp (/tmp)", Path("/tmp")))
                cache_dir = Path.home() / ".cache"
                if cache_dir.exists():
                    steps.append(("User Cache (~/.cache)", cache_dir))

        if clear_prefetch and IS_WINDOWS:
            steps.append(("Prefetch", Path("C:/Windows/Prefetch")))

        total_steps = len(steps) + (1 if empty_recycle else 0)
        done = 0
        total_freed = 0

        for label, folder in steps:
            if self._cancelled:
                return
            freed = self._clear_folder(folder, label)
            total_freed += freed
            done += 1
            self._set_progress(done / total_steps)

        if empty_recycle and IS_WINDOWS and not self._cancelled:
            self._empty_recycle_bin()
            done += 1
            self._set_progress(done / total_steps)
        elif empty_recycle and not IS_WINDOWS:
            self._emit_log("Recycle Bin: not applicable on this OS, skipping.")

        self._emit_log(f"\nTotal freed: {self._fmt_bytes(total_freed)}")

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _clear_folder(self, folder: Path, label: str) -> int:
        """Delete all files/subdirs in folder. Returns bytes freed."""
        if not folder.exists():
            self._emit_log(f"{label}: folder not found, skipping.")
            return 0

        freed = 0
        deleted = 0
        skipped = 0

        for item in folder.iterdir():
            if self._cancelled:
                break
            try:
                size = self._size_of(item)
                if item.is_file() or item.is_symlink():
                    item.unlink()
                else:
                    shutil.rmtree(item, ignore_errors=True)
                freed += size
                deleted += 1
            except (PermissionError, OSError):
                skipped += 1

        self._emit_log(
            f"{label}: removed {deleted} item(s), skipped {skipped} "
            f"(freed ~{self._fmt_bytes(freed)})"
        )
        return freed

    def _empty_recycle_bin(self) -> None:
        """Empty the Windows Recycle Bin via the shell API."""
        try:
            import ctypes
            # SHEmptyRecycleBinW flags: SHERB_NOCONFIRMATION | SHERB_NOPROGRESSUI | SHERB_NOSOUND
            result = ctypes.windll.shell32.SHEmptyRecycleBinW(None, None, 0x00000007)
            if result == 0:
                self._emit_log("Recycle Bin: emptied.")
            else:
                self._emit_log(f"Recycle Bin: already empty or error (code {result}).")
        except Exception as exc:
            self._emit_log(f"Recycle Bin: could not empty — {exc}")

    @staticmethod
    def _size_of(path: Path) -> int:
        try:
            if path.is_file():
                return path.stat().st_size
            return sum(f.stat().st_size for f in path.rglob("*") if f.is_file())
        except OSError:
            return 0

    @staticmethod
    def _fmt_bytes(n: int) -> str:
        for unit in ("B", "KB", "MB", "GB"):
            if n < 1024:
                return f"{n:.1f} {unit}"
            n /= 1024
        return f"{n:.1f} TB"
