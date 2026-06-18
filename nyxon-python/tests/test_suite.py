"""
Nyxon Automation Suite - Unit Tests
Run with: pytest tests/ -v
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest
from unittest.mock import patch, MagicMock

from utils.settings import Settings, DEFAULTS
from utils.constants import EXTENSION_MAP, STATUS_DONE, STATUS_ERROR


# ── Settings tests ────────────────────────────────────────────────────────────

class TestSettings:
    def test_defaults_loaded(self, tmp_path, monkeypatch):
        monkeypatch.setattr("utils.settings.CONFIG_DIR", tmp_path)
        monkeypatch.setattr("utils.settings.CONFIG_FILE", tmp_path / "config.json")
        s = Settings()
        assert s.get("theme") == DEFAULTS["theme"]

    def test_set_and_get(self, tmp_path, monkeypatch):
        monkeypatch.setattr("utils.settings.CONFIG_DIR", tmp_path)
        monkeypatch.setattr("utils.settings.CONFIG_FILE", tmp_path / "config.json")
        s = Settings()
        s.set("theme", "light")
        assert s.get("theme") == "light"

    def test_nested_get(self, tmp_path, monkeypatch):
        monkeypatch.setattr("utils.settings.CONFIG_DIR", tmp_path)
        monkeypatch.setattr("utils.settings.CONFIG_FILE", tmp_path / "config.json")
        s = Settings()
        assert s.get("network_checker.timeout_seconds") == 3

    def test_deep_merge_preserves_missing_keys(self):
        base = {"a": 1, "b": {"c": 2, "d": 3}}
        override = {"b": {"c": 99}}
        result = Settings._deep_merge(base, override)
        assert result["b"]["c"] == 99
        assert result["b"]["d"] == 3   # preserved
        assert result["a"] == 1


# ── Constants tests ────────────────────────────────────────────────────────────

class TestConstants:
    def test_extension_map_has_common_types(self):
        assert EXTENSION_MAP[".pdf"] == "Documents"
        assert EXTENSION_MAP[".mp4"] == "Videos"
        assert EXTENSION_MAP[".py"] == "Code"
        assert EXTENSION_MAP[".zip"] == "Archives"

    def test_extension_map_keys_are_lowercase(self):
        for key in EXTENSION_MAP:
            assert key == key.lower(), f"Key {key!r} is not lowercase"


# ── Base Automation tests ─────────────────────────────────────────────────────

class TestBaseAutomation:
    def _make_automation(self):
        from automations.base import Automation

        class DummyAutomation(Automation):
            def run(self):
                self._emit_log("hello")
                self._set_progress(1.0)

        return DummyAutomation("Dummy", "Test automation")

    def test_execute_sets_status_done(self):
        auto = self._make_automation()
        auto.execute()
        assert auto.status == STATUS_DONE

    def test_log_populated_after_run(self):
        auto = self._make_automation()
        auto.execute()
        assert "hello" in auto.log_lines

    def test_progress_is_1_after_done(self):
        auto = self._make_automation()
        auto.execute()
        assert auto.progress == 1.0

    def test_reset_clears_state(self):
        auto = self._make_automation()
        auto.execute()
        auto.reset()
        assert auto.status == "Idle"
        assert auto.progress == 0.0
        assert auto.log_lines == []

    def test_error_sets_status(self):
        from automations.base import Automation

        class BrokenAutomation(Automation):
            def run(self):
                raise ValueError("intentional error")

        broken = BrokenAutomation("Broken", "Breaks on purpose")
        broken.execute()
        assert broken.status == STATUS_ERROR


# ── FileOrganizer tests ───────────────────────────────────────────────────────

class TestFileOrganizer:
    def test_organizes_files_by_extension(self, tmp_path):
        (tmp_path / "photo.jpg").write_text("img")
        (tmp_path / "notes.pdf").write_text("pdf")
        (tmp_path / "script.py").write_text("py")

        from automations.file_organizer import FileOrganizer
        fo = FileOrganizer()
        fo.target_folder = tmp_path
        fo.execute()

        assert (tmp_path / "Images" / "photo.jpg").exists()
        assert (tmp_path / "Documents" / "notes.pdf").exists()
        assert (tmp_path / "Code" / "script.py").exists()

    def test_unknown_extension_goes_to_other(self, tmp_path):
        (tmp_path / "weirdfile.xyz").write_text("x")
        from automations.file_organizer import FileOrganizer
        fo = FileOrganizer()
        fo.target_folder = tmp_path
        fo.execute()
        assert (tmp_path / "Other" / "weirdfile.xyz").exists()

    def test_empty_folder_handled_gracefully(self, tmp_path):
        from automations.file_organizer import FileOrganizer
        fo = FileOrganizer()
        fo.target_folder = tmp_path
        fo.execute()
        assert fo.status == STATUS_DONE


# ── NetworkChecker tests ──────────────────────────────────────────────────────

class TestNetworkChecker:
    def test_tcp_ping_returns_none_on_closed_port(self):
        from automations.net_checker import NetworkChecker
        result = NetworkChecker._tcp_ping("127.0.0.1", port=19999, timeout=1)
        assert result is None

    def test_run_completes(self):
        from automations.net_checker import NetworkChecker
        nc = NetworkChecker()
        # Patch actual network calls so tests run offline
        with patch.object(nc, "_check_host", return_value=None):
            nc.execute()
        assert nc.status == STATUS_DONE
