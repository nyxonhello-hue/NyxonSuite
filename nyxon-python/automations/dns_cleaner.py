"""
Nyxon Automation Suite - DNS History Cleaner
Flushes the DNS cache and optionally clears browser DNS history.
Windows-only for DNS flush; browser clearing works cross-platform.
"""

import sys
import subprocess
from pathlib import Path

from automations.base import Automation


IS_WINDOWS = sys.platform == "win32"


class DNSCleaner(Automation):
    """
    Clears DNS cache via ipconfig /flushdns (Windows) or
    systemd-resolve / nscd on Linux.

    Options:
        flush_system_dns  : flush OS-level DNS cache
        flush_chrome      : delete Chrome DNS cache file
        flush_firefox     : delete Firefox network cache
        show_current      : display current DNS cache stats before flushing
    """

    def __init__(self) -> None:
        super().__init__(
            name="DNS Cleaner",
            description="Flush DNS cache and clear browser DNS history.",
        )
        self.flush_system_dns: bool = True
        self.flush_chrome: bool     = True
        self.flush_firefox: bool    = True
        self.show_current: bool     = True

    def run(self) -> None:
        steps = []
        if self.flush_system_dns:
            steps.append(self._flush_system)
        if self.flush_chrome:
            steps.append(self._flush_chrome)
        if self.flush_firefox:
            steps.append(self._flush_firefox)

        total = len(steps)
        if total == 0:
            self._emit_log("Nothing selected.")
            return

        for i, step in enumerate(steps):
            if self._cancelled:
                break
            step()
            self._set_progress((i + 1) / total)

        self._emit_log("\nDone.")

    # ── Steps ─────────────────────────────────────────────────────────────────

    def _flush_system(self) -> None:
        self._emit_log("── System DNS Cache ──")
        if IS_WINDOWS:
            # Show current cache size first
            if self.show_current:
                try:
                    result = subprocess.run(
                        ["ipconfig", "/displaydns"],
                        capture_output=True, text=True, timeout=10
                    )
                    lines = [l for l in result.stdout.splitlines() if l.strip()]
                    self._emit_log(f"  Current entries: ~{max(0, len(lines) // 5)}")
                except Exception:
                    pass

            try:
                result = subprocess.run(
                    ["ipconfig", "/flushdns"],
                    capture_output=True, text=True, timeout=15
                )
                if result.returncode == 0:
                    self._emit_log("  ✓ Windows DNS cache flushed.")
                else:
                    self._emit_log(f"  ✗ Failed: {result.stderr.strip()}")
            except FileNotFoundError:
                self._emit_log("  ✗ ipconfig not found.")
            except Exception as exc:
                self._emit_log(f"  ✗ Error: {exc}")
        else:
            # Linux — try systemd-resolve, then nscd
            flushed = False
            for cmd in [
                ["systemd-resolve", "--flush-caches"],
                ["resolvectl", "flush-caches"],
                ["nscd", "--invalidate=hosts"],
            ]:
                try:
                    result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
                    if result.returncode == 0:
                        self._emit_log(f"  ✓ Flushed via {cmd[0]}.")
                        flushed = True
                        break
                except FileNotFoundError:
                    continue
                except Exception as exc:
                    self._emit_log(f"  ✗ {cmd[0]}: {exc}")

            if not flushed:
                self._emit_log("  ✗ No supported DNS flush tool found.")

    def _flush_chrome(self) -> None:
        self._emit_log("── Chrome DNS Cache ──")
        # Chrome stores DNS in a SQLite file inside the profile
        paths = []
        if IS_WINDOWS:
            local = Path.home() / "AppData/Local"
            paths = [
                local / "Google/Chrome/User Data/Default/Network Persistent State",
                local / "Google/Chrome/User Data/Default/Cache",
            ]
        else:
            config = Path.home() / ".config"
            paths = [
                config / "google-chrome/Default/Network Persistent State",
                config / "chromium/Default/Network Persistent State",
            ]

        cleared = 0
        for p in paths:
            if p.exists():
                try:
                    if p.is_file():
                        p.unlink()
                    else:
                        import shutil
                        shutil.rmtree(p, ignore_errors=True)
                    self._emit_log(f"  ✓ Cleared: {p.name}")
                    cleared += 1
                except OSError as exc:
                    self._emit_log(f"  ✗ {p.name}: {exc}")

        if cleared == 0:
            self._emit_log("  Chrome profile not found or already clean.")

    def _flush_firefox(self) -> None:
        self._emit_log("── Firefox DNS Cache ──")
        # Firefox network cache lives in profiles
        if IS_WINDOWS:
            base = Path.home() / "AppData/Local/Mozilla/Firefox/Profiles"
        else:
            base = Path.home() / ".mozilla/firefox"

        if not base.exists():
            self._emit_log("  Firefox profile not found.")
            return

        cleared = 0
        for profile in base.iterdir():
            if not profile.is_dir():
                continue
            cache_dirs = [
                profile / "cache2",
                profile / "Cache",
            ]
            for cache in cache_dirs:
                if cache.exists():
                    try:
                        import shutil
                        shutil.rmtree(cache, ignore_errors=True)
                        self._emit_log(f"  ✓ Cleared: {profile.name}/{cache.name}")
                        cleared += 1
                    except OSError as exc:
                        self._emit_log(f"  ✗ {cache.name}: {exc}")

        if cleared == 0:
            self._emit_log("  No Firefox cache found or already clean.")
