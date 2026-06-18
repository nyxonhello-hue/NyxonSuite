"""
Nyxon Automation Suite - File Organizer
Sorts files in a target folder into subfolders by extension.
"""

from pathlib import Path
import shutil

from automations.base import Automation
from utils.constants import EXTENSION_MAP
from utils.settings import settings


class FileOrganizer(Automation):
    """
    Scans a target directory and moves files into category subfolders
    based on their extension (e.g. .mp4 → Videos/, .pdf → Documents/).

    Files with unrecognised extensions land in 'Other/'.
    Subfolders and hidden files (dot-prefixed) are skipped.
    """

    def __init__(self) -> None:
        super().__init__(
            name="File Organizer",
            description="Sort files in a folder into subfolders by type.",
        )
        self.target_folder: Path = Path(
            settings.get("file_organizer.target_folder", str(Path.home() / "Downloads"))
        )

    def run(self) -> None:
        folder = self.target_folder
        if not folder.exists():
            self._emit_log(f"Folder not found: {folder}")
            return

        files = [f for f in folder.iterdir() if f.is_file() and not f.name.startswith(".")]
        total = len(files)

        if total == 0:
            self._emit_log("No files to organise.")
            return

        self._emit_log(f"Found {total} file(s) in {folder.name}")
        moved = 0

        for i, file in enumerate(files):
            if self._cancelled:
                break

            category = EXTENSION_MAP.get(file.suffix.lower(), "Other")
            dest_dir = folder / category
            dest_dir.mkdir(exist_ok=True)
            dest = dest_dir / file.name

            # Avoid overwriting: append a counter if name clash
            counter = 1
            while dest.exists():
                dest = dest_dir / f"{file.stem}_{counter}{file.suffix}"
                counter += 1

            try:
                shutil.move(str(file), str(dest))
                self._emit_log(f"  {file.name}  →  {category}/")
                moved += 1
            except OSError as exc:
                self._emit_log(f"  ✗ Could not move {file.name}: {exc}")

            self._set_progress((i + 1) / total)

        self._emit_log(f"\nDone — moved {moved} of {total} file(s).")
