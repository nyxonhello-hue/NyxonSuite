"""
Nyxon Automation Suite - Bulk Rename
Renames files in a folder using one of four modes, with preview support.
"""

from pathlib import Path
from dataclasses import dataclass
from enum import Enum

from automations.base import Automation
from utils.settings import settings


class RenameMode(Enum):
    PREFIX     = "prefix"
    SUFFIX     = "suffix"
    REPLACE    = "replace"
    SEQUENTIAL = "sequential"


@dataclass
class RenamePreview:
    """Holds a before/after pair for preview display."""
    original: Path
    renamed: Path

    @property
    def changed(self) -> bool:
        return self.original.name != self.renamed.name


class BulkRename(Automation):
    """
    Renames files in a target folder according to the selected mode.

    Usage:
        1. Set target_folder, mode, and mode-specific params.
        2. Call preview() to get a list of RenamePreview without touching disk.
        3. Call execute() to actually apply the renames.

    Attributes:
        target_folder : folder containing files to rename
        mode          : RenameMode enum value
        prefix        : string to prepend (PREFIX mode)
        suffix        : string to append before extension (SUFFIX mode)
        find_text     : text to find (REPLACE mode)
        replace_text  : text to substitute (REPLACE mode)
        start_number  : starting integer (SEQUENTIAL mode)
        padding       : zero-padding digits e.g. 3 → 001 (SEQUENTIAL mode)
        base_name     : base name before number (SEQUENTIAL mode)
        file_filter   : e.g. ".jpg" to only rename that type, "" for all
    """

    def __init__(self) -> None:
        super().__init__(
            name="Bulk Rename",
            description="Rename multiple files at once with prefix, suffix, replace, or numbering.",
        )
        self.target_folder: Path = Path(
            settings.get("bulk_rename.target_folder", str(Path.home()))
        )
        self.mode: RenameMode = RenameMode.PREFIX
        self.prefix: str      = ""
        self.suffix: str      = ""
        self.find_text: str   = ""
        self.replace_text: str = ""
        self.start_number: int = 1
        self.padding: int      = 3
        self.base_name: str    = "file"
        self.file_filter: str  = ""   # e.g. ".jpg" or "" for all

        self.previews: list[RenamePreview] = []

    # ── Preview (no disk writes) ──────────────────────────────────────────────

    def preview(self) -> list[RenamePreview]:
        """
        Compute new names for all matching files without renaming anything.
        Returns a list of RenamePreview objects for the UI to display.
        """
        files = self._get_files()
        self.previews = [
            RenamePreview(original=f, renamed=f.parent / self._new_name(f, i))
            for i, f in enumerate(files)
        ]
        return self.previews

    # ── Run (actual rename) ───────────────────────────────────────────────────

    def run(self) -> None:
        if not self.target_folder.exists():
            self._emit_log(f"Folder not found: {self.target_folder}")
            return

        if not self.previews:
            self.preview()

        total = len(self.previews)
        if total == 0:
            self._emit_log("No files matched the filter.")
            return

        self._emit_log(f"Renaming {total} file(s) in {self.target_folder.name}…\n")
        renamed = 0
        skipped = 0

        for i, p in enumerate(self.previews):
            if self._cancelled:
                break

            if not p.changed:
                skipped += 1
                self._set_progress((i + 1) / total)
                continue

            # Avoid overwriting existing files
            dest = p.renamed
            counter = 1
            while dest.exists() and dest != p.original:
                dest = p.renamed.parent / f"{p.renamed.stem}_{counter}{p.renamed.suffix}"
                counter += 1

            try:
                p.original.rename(dest)
                self._emit_log(f"  {p.original.name}  →  {dest.name}")
                renamed += 1
            except OSError as exc:
                self._emit_log(f"  ✗ {p.original.name}: {exc}")

            self._set_progress((i + 1) / total)

        self._emit_log(
            f"\nDone — renamed {renamed}, skipped {skipped} (no change)."
        )

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _get_files(self) -> list[Path]:
        if not self.target_folder.exists():
            return []
        files = sorted(
            f for f in self.target_folder.iterdir()
            if f.is_file() and not f.name.startswith(".")
            and (not self.file_filter or f.suffix.lower() == self.file_filter.lower())
        )
        return files

    def _new_name(self, file: Path, index: int) -> str:
        stem = file.stem
        ext  = file.suffix

        if self.mode == RenameMode.PREFIX:
            return f"{self.prefix}{stem}{ext}"

        elif self.mode == RenameMode.SUFFIX:
            return f"{stem}{self.suffix}{ext}"

        elif self.mode == RenameMode.REPLACE:
            new_stem = stem.replace(self.find_text, self.replace_text)
            return f"{new_stem}{ext}"

        elif self.mode == RenameMode.SEQUENTIAL:
            n = self.start_number + index
            return f"{self.base_name}_{str(n).zfill(self.padding)}{ext}"

        return file.name
