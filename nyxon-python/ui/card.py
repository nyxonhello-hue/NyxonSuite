"""
Nyxon Automation Suite - Automation Card
A self-contained card widget that displays one automation's state.
"""

import threading
import customtkinter as ctk
from typing import Callable

from automations.base import Automation
from utils.constants import STATUS_IDLE, STATUS_RUNNING, STATUS_DONE, STATUS_ERROR, STATUS_CANCELLED, UI_POLL_MS


STATUS_COLORS = {
    STATUS_IDLE:      "#6B7280",
    STATUS_RUNNING:   "#7B5CF0",
    STATUS_DONE:      "#10B981",
    STATUS_ERROR:     "#EF4444",
    STATUS_CANCELLED: "#F59E0B",
}


class AutomationCard(ctk.CTkFrame):
    """
    Renders a single automation as a card:
    ┌──────────────────────────────────────────┐
    │  Name            [status pill]  [Run] [↺] │
    │  Description                               │
    │  ▓▓▓▓▓▓▓░░░░░░░░░░░  progress bar         │
    │  ┌──── log output ────────────────────┐   │
    │  └────────────────────────────────────┘   │
    └──────────────────────────────────────────┘
    """

    def __init__(
        self,
        parent,
        automation: Automation,
        on_configure: Callable[["AutomationCard"], None] | None = None,
        **kwargs,
    ) -> None:
        super().__init__(parent, corner_radius=12, fg_color=("gray90", "#1E1B2E"), **kwargs)
        self.automation = automation
        self._on_configure = on_configure
        self._thread: threading.Thread | None = None

        self._build()
        self._wire_callbacks()

    # ── Build ─────────────────────────────────────────────────────────────────

    def _build(self) -> None:
        self.grid_columnconfigure(0, weight=1)

        # ── Header row ────────────────────────────────────────────────────────
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", padx=16, pady=(14, 4))
        header.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(
            header,
            text=self.automation.name,
            font=ctk.CTkFont(family="Segoe UI", size=14, weight="bold"),
            anchor="w",
        ).grid(row=0, column=0, sticky="w")

        self._status_label = ctk.CTkLabel(
            header,
            text=STATUS_IDLE,
            font=ctk.CTkFont(size=11),
            text_color=STATUS_COLORS[STATUS_IDLE],
            anchor="e",
        )
        self._status_label.grid(row=0, column=1, sticky="e", padx=(8, 0))

        btn_frame = ctk.CTkFrame(header, fg_color="transparent")
        btn_frame.grid(row=0, column=2, sticky="e", padx=(10, 0))

        self._run_btn = ctk.CTkButton(
            btn_frame,
            text="Run",
            width=64,
            height=28,
            corner_radius=6,
            font=ctk.CTkFont(size=12, weight="bold"),
            command=self._on_run,
        )
        self._run_btn.pack(side="left", padx=(0, 6))

        if self._on_configure:
            ctk.CTkButton(
                btn_frame,
                text="⚙",
                width=28,
                height=28,
                corner_radius=6,
                fg_color=("gray80", "#2D2A3E"),
                hover_color=("gray70", "#3A3550"),
                command=lambda: self._on_configure(self),
            ).pack(side="left")

        # ── Description ───────────────────────────────────────────────────────
        ctk.CTkLabel(
            self,
            text=self.automation.description,
            font=ctk.CTkFont(size=11),
            text_color=("gray50", "gray60"),
            anchor="w",
        ).grid(row=1, column=0, sticky="w", padx=16, pady=(0, 8))

        # ── Progress bar ──────────────────────────────────────────────────────
        self._progress = ctk.CTkProgressBar(self, height=6, corner_radius=3)
        self._progress.set(0)
        self._progress.grid(row=2, column=0, sticky="ew", padx=16, pady=(0, 8))

        # ── Log output ────────────────────────────────────────────────────────
        self._log_box = ctk.CTkTextbox(
            self,
            height=110,
            font=ctk.CTkFont(family="Consolas", size=11),
            fg_color=("gray95", "#13111F"),
            corner_radius=6,
            state="disabled",
            wrap="word",
        )
        self._log_box.grid(row=3, column=0, sticky="ew", padx=16, pady=(0, 14))

    # ── Callbacks & threading ─────────────────────────────────────────────────

    def _wire_callbacks(self) -> None:
        self.automation.set_callbacks(
            on_progress=self._cb_progress,
            on_log=self._cb_log,
            on_status=self._cb_status,
        )

    def _on_run(self) -> None:
        if self.automation.status == STATUS_RUNNING:
            self.automation.cancel()
            self._run_btn.configure(text="Run")
            return

        self.automation.reset()
        self._clear_log()
        self._progress.set(0)

        self._run_btn.configure(text="Stop")
        self._thread = threading.Thread(target=self.automation.execute, daemon=True)
        self._thread.start()

    # ── Thread-safe UI updates via after() ────────────────────────────────────

    def _cb_progress(self, value: float) -> None:
        self.after(0, lambda: self._progress.set(value))

    def _cb_log(self, message: str) -> None:
        self.after(0, lambda m=message: self._append_log(m))

    def _cb_status(self, status: str) -> None:
        self.after(0, lambda s=status: self._update_status(s))

    def _append_log(self, message: str) -> None:
        self._log_box.configure(state="normal")
        self._log_box.insert("end", message + "\n")
        self._log_box.see("end")
        self._log_box.configure(state="disabled")

    def _clear_log(self) -> None:
        self._log_box.configure(state="normal")
        self._log_box.delete("1.0", "end")
        self._log_box.configure(state="disabled")

    def _update_status(self, status: str) -> None:
        color = STATUS_COLORS.get(status, "#6B7280")
        self._status_label.configure(text=status, text_color=color)
        if status != STATUS_RUNNING:
            self._run_btn.configure(text="Run")
