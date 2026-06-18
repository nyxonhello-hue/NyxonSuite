"""
Nyxon Automation Suite - Duplicate File Finder
Finds files with identical content using MD5 hashing.
"""

import hashlib
from pathlib import Path
from collections import defaultdict

from automations.base import Automation
from utils.settings import settings


class DuplicateFinder(Automation):
    """
    Scans a folder recursively, groups files by MD5 hash,
    and reports groups of duplicates.

    Results stored in self.duplicates after run():
        { hash: [Path, Path, ...], ... }
    Only groups with 2+ files are included.
    """

    def __init__(self) -> None:
        super().__init__(
            name="Duplicate Finder",
            description="Find and remove duplicate files wasting your disk space.",
        )
        self.scan_path: Path = Path(
            settings.get("duplicate_finder.scan_path", str(Path.home()))
        )
        self.duplicates: dict[str, list[Path]] = {}

    def run(self) -> None:
        if not self.scan_path.exists():
            self._emit_log(f"Folder not found: {self.scan_path}")
            return

        self._emit_log(f"Scanning {self.scan_path} for duplicates…\n")

        # Step 1: group by file size first (cheap filter)
        size_map: dict[int, list[Path]] = defaultdict(list)
        scanned = 0
        errors = 0

        for f in self.scan_path.rglob("*"):
            if self._cancelled:
                return
            if not f.is_file() or f.name.startswith("."):
                continue
            try:
                size_map[f.stat().st_size].append(f)
                scanned += 1
            except OSError:
                errors += 1

        self._emit_log(f"Found {scanned:,} files. Checking for duplicates…\n")
        self._set_progress(0.3)

        # Step 2: hash only files that share a size
        candidates = [files for files in size_map.values() if len(files) > 1]
        hash_map: dict[str, list[Path]] = defaultdict(list)
        total = sum(len(g) for g in candidates)
        done = 0

        for group in candidates:
            for f in group:
                if self._cancelled:
                    return
                h = self._md5(f)
                if h:
                    hash_map[h].append(f)
                done += 1
                self._set_progress(0.3 + 0.7 * (done / max(total, 1)))

        # Step 3: keep only actual duplicates
        self.duplicates = {h: files for h, files in hash_map.items() if len(files) > 1}

        if not self.duplicates:
            self._emit_log("No duplicate files found.")
            return

        total_groups = len(self.duplicates)
        total_wasted = sum(
            files[0].stat().st_size * (len(files) - 1)
            for files in self.duplicates.values()
        )

        self._emit_log(f"Found {total_groups} duplicate group(s) — {self._fmt(total_wasted)} wasted\n")

        for i, (h, files) in enumerate(self.duplicates.items(), 1):
            size = self._fmt(files[0].stat().st_size)
            self._emit_log(f"  Group {i}  ({size} each):")
            for f in files:
                self._emit_log(f"    {f}")

    def delete_file(self, path: Path) -> bool:
        """Delete a single file. Returns True on success."""
        try:
            path.unlink()
            self._emit_log(f"Deleted: {path}")
            # Remove from results
            for files in self.duplicates.values():
                if path in files:
                    files.remove(path)
            return True
        except OSError as exc:
            self._emit_log(f"Could not delete {path.name}: {exc}")
            return False

    @staticmethod
    def _md5(path: Path) -> str | None:
        try:
            h = hashlib.md5()
            with path.open("rb") as f:
                for chunk in iter(lambda: f.read(8192), b""):
                    h.update(chunk)
            return h.hexdigest()
        except OSError:
            return None

    @staticmethod
    def _fmt(n: int) -> str:
        for unit in ("B", "KB", "MB", "GB"):
            if n < 1024:
                return f"{n:.1f} {unit}"
            n /= 1024
        return f"{n:.1f} TB"
