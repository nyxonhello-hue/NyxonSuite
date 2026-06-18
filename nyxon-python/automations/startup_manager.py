"""
Nyxon Automation Suite - Startup Manager
Lists and toggles Windows startup programs via the registry.
Windows-only feature; on other platforms the automation reports unsupported gracefully.
"""

import sys
import platform
from dataclasses import dataclass

from automations.base import Automation
from utils.logger import get_logger

logger = get_logger(__name__)

IS_WINDOWS = sys.platform == "win32"

# Only import winreg on Windows — it doesn't exist on Linux/macOS
if IS_WINDOWS:
    import winreg
    STARTUP_KEYS: list[tuple[int, str]] = [
        (winreg.HKEY_CURRENT_USER,  r"Software\Microsoft\Windows\CurrentVersion\Run"),
        (winreg.HKEY_LOCAL_MACHINE, r"Software\Microsoft\Windows\CurrentVersion\Run"),
        (winreg.HKEY_CURRENT_USER,  r"Software\Microsoft\Windows\CurrentVersion\RunOnce"),
    ]
else:
    winreg = None       # type: ignore[assignment]
    STARTUP_KEYS = []


@dataclass
class StartupEntry:
    """Represents a single startup program."""
    name: str
    command: str
    hive: int
    reg_path: str
    enabled: bool = True


class StartupManager(Automation):
    """
    Reads the Windows registry to enumerate startup programs.

    Design notes:
    - This automation is Windows-only: it uses the registry via `winreg`.
    - To "disable" a startup entry we do NOT delete it permanently.
      Instead we move the value under a different name by prefixing it with
      `_disabled_`.

      This has two benefits:
      1) It is reversible (enable_entry can restore the original name).
      2) It mirrors the spirit of Task Manager (disable/enable without losing
         the underlying configuration).

    - UI code (see ui/startup_panel.py) reads `StartupEntry.enabled` to decide
      whether to render a "Disable" or "Enable" button.
    """


    def __init__(self) -> None:
        super().__init__(
            name="Startup Manager",
            description="View and control programs that launch at Windows startup.",
        )
        self.entries: list[StartupEntry] = []

    def run(self) -> None:
        """Scan all startup registry keys and populate self.entries."""
        if not IS_WINDOWS:
            self._emit_log("Startup Manager is a Windows-only feature.")
            self._emit_log(f"Current platform: {platform.system()} — registry not available.")
            return

        self.entries.clear()
        self._emit_log("Scanning startup registry keys…\n")

        total = len(STARTUP_KEYS)
        for i, (hive, path) in enumerate(STARTUP_KEYS):
            if self._cancelled:
                break
            self._scan_key(hive, path)
            self._set_progress((i + 1) / total)

        count = len(self.entries)
        self._emit_log(f"Found {count} startup entr{'y' if count == 1 else 'ies'}.")
        for e in self.entries:
            state = "✓ Enabled" if e.enabled else "✗ Disabled"
            self._emit_log(f"  [{state}] {e.name}")
            self._emit_log(f"           {e.command[:80]}{'…' if len(e.command) > 80 else ''}")

    def disable_entry(self, entry: StartupEntry) -> bool:
        """Disable a startup entry (non-destructive).

        Implementation details:
        - We open the registry key containing the entry.
        - We create a new value with the same command but a modified name
          prefixed with `_disabled_`.
        - Then we delete the original value name.

        This approach is deterministic and avoids deleting the underlying
        configuration permanently.

        Returns:
            bool: True on success, False otherwise.
        """

        if not IS_WINDOWS:
            return False
        try:
            hive_name = "HKCU" if entry.hive == winreg.HKEY_CURRENT_USER else "HKLM"
            self._emit_log(f"Disabling [{entry.name}] in {hive_name}…")

            key = winreg.OpenKey(entry.hive, entry.reg_path, 0, winreg.KEY_SET_VALUE)
            # Prefix name with underscore to signal disabled (simple non-destructive toggle)
            winreg.SetValueEx(key, f"_disabled_{entry.name}", 0, winreg.REG_SZ, entry.command)
            winreg.DeleteValue(key, entry.name)
            winreg.CloseKey(key)

            entry.enabled = False
            entry.name = f"_disabled_{entry.name}"
            self._emit_log(f"  ✓ Disabled.")
            return True
        except (PermissionError, FileNotFoundError, OSError) as exc:
            self._emit_log(f"  ✗ Failed: {exc}")
            logger.error("Could not disable %s: %s", entry.name, exc)
            return False

    def enable_entry(self, entry: StartupEntry) -> bool:
        """Re-enable a previously disabled entry.

        If the UI toggles an entry from "Disabled" back to "Enabled", the
        `StartupPanel` calls this method.

        The enable logic reverses `disable_entry` by:
        1) stripping the `_disabled_` prefix from the stored entry name
        2) restoring that original value name

        Returns True on success.
        """

        if not IS_WINDOWS:
            return False
        try:
            original_name = entry.name.removeprefix("_disabled_")
            self._emit_log(f"Enabling [{original_name}]…")

            key = winreg.OpenKey(entry.hive, entry.reg_path, 0, winreg.KEY_SET_VALUE)
            winreg.SetValueEx(key, original_name, 0, winreg.REG_SZ, entry.command)
            winreg.DeleteValue(key, entry.name)
            winreg.CloseKey(key)

            entry.enabled = True
            entry.name = original_name
            self._emit_log(f"  ✓ Enabled.")
            return True
        except (PermissionError, FileNotFoundError, OSError) as exc:
            self._emit_log(f"  ✗ Failed: {exc}")
            logger.error("Could not enable %s: %s", entry.name, exc)
            return False

    # ── Private ───────────────────────────────────────────────────────────────

    def _scan_key(self, hive: int, path: str) -> None:
        """Enumerate startup registry values under a specific registry key.

        Each value in the Run/RunOnce keys represents a startup program.

        We treat names starting with `_disabled_` as disabled, so the UI can
        show Enable/Disable without deleting the original configuration.
        """
        if not IS_WINDOWS or winreg is None:
            return
        try:
            key = winreg.OpenKey(hive, path, 0, winreg.KEY_READ)

        except FileNotFoundError:
            return
        except PermissionError:
            self._emit_log(f"  ⚠ Access denied: {path}")
            return

        try:
            i = 0
            while True:
                try:
                    name, value, _ = winreg.EnumValue(key, i)
                    enabled = not name.startswith("_disabled_")
                    self.entries.append(StartupEntry(
                        name=name,
                        command=value,
                        hive=hive,
                        reg_path=path,
                        enabled=enabled,
                    ))
                    i += 1
                except OSError:
                    break
        finally:
            winreg.CloseKey(key)
