"""
Nyxon Automation Suite - Network Checker
Tests connectivity to a list of hosts and reports latency.
"""

import socket
import time
import subprocess
import platform

from automations.base import Automation
from utils.settings import settings


class NetworkChecker(Automation):
    """
    Pings a list of hosts (configurable in settings) and reports:
      - Reachability (up / down)
      - Round-trip latency (ms)
      - DNS resolution time

    Uses socket-level TCP probing so it works without admin rights.
    Falls back to ICMP ping via subprocess for latency accuracy.
    """

    def __init__(self) -> None:
        super().__init__(
            name="Network Checker",
            description="Test connectivity and latency to key hosts.",
        )

    def run(self) -> None:
        cfg = settings.get("network_checker", {})
        hosts: list[str] = cfg.get("hosts", ["8.8.8.8", "1.1.1.1", "google.com"])
        timeout: int = cfg.get("timeout_seconds", 3)

        self._emit_log(f"Checking {len(hosts)} host(s)…\n")
        total = len(hosts)

        for i, host in enumerate(hosts):
            if self._cancelled:
                break

            self._emit_log(f"▶ {host}")
            self._check_host(host, timeout)
            self._emit_log("")
            self._set_progress((i + 1) / total)

        if not self._cancelled:
            self._emit_log("Check complete.")

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _check_host(self, host: str, timeout: int) -> None:
        # DNS resolution
        dns_start = time.perf_counter()
        try:
            ip = socket.gethostbyname(host)
            dns_ms = (time.perf_counter() - dns_start) * 1000
            self._emit_log(f"  DNS: {ip}  ({dns_ms:.1f} ms)")
        except socket.gaierror:
            self._emit_log(f"  DNS: failed — host unreachable")
            return

        # TCP probe on port 80 for latency
        tcp_ms = self._tcp_ping(ip, port=80, timeout=timeout)
        if tcp_ms is not None:
            self._emit_log(f"  TCP (port 80): {tcp_ms:.1f} ms  ✓")
        else:
            # Try port 443
            tcp_ms = self._tcp_ping(ip, port=443, timeout=timeout)
            if tcp_ms is not None:
                self._emit_log(f"  TCP (port 443): {tcp_ms:.1f} ms  ✓")
            else:
                self._emit_log(f"  TCP: no response on 80/443")

        # ICMP ping via subprocess (best-effort)
        ping_ms = self._icmp_ping(host, timeout)
        if ping_ms is not None:
            self._emit_log(f"  ICMP ping: {ping_ms:.1f} ms")

    @staticmethod
    def _tcp_ping(ip: str, port: int, timeout: int) -> float | None:
        try:
            start = time.perf_counter()
            with socket.create_connection((ip, port), timeout=timeout):
                return (time.perf_counter() - start) * 1000
        except OSError:
            return None

    @staticmethod
    def _icmp_ping(host: str, timeout: int) -> float | None:
        try:
            cmd = ["ping", "-n", "1", "-w", str(timeout * 1000), host]
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout + 2,
            )
            for line in result.stdout.splitlines():
                if "Average" in line or "average" in line:
                    # "Average = 14ms" → 14.0
                    part = line.split("=")[-1].strip().replace("ms", "")
                    return float(part)
        except Exception:
            pass
        return None
