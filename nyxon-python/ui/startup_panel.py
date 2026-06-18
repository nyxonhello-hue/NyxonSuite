"""
Nyxon Automation Suite - Startup Manager Panel
Special UI panel for the StartupManager automation that shows an interactive table.
"""

import threading
import customtkinter as ctk

from automations.startup_manager import StartupManager, StartupEntry
from utils.constants import STATUS_RUNNING


class StartupPanel(ctk.CTkFrame):
    """StartupManager-specific UI.

    Responsibilities:
    - Run the StartupManager scan in a background thread (so the UI stays
      responsive).
    - Render one row per startup entry with a short command preview.
    - Toggle enable/disable by calling StartupManager.

    Threading note:
    - `self.automation.execute()` is run on a daemon thread.
    - All widget creation/destruction happens on the Tk main thread via
      `self.after(0, ...)`.
    """


    def __init__(self, parent, **kwargs) -> None:
        super().__init__(parent, corner_radius=12, fg_color=("gray90", "#1E1B2E"), **kwargs)
        self.automation = StartupManager()
        self._thread: threading.Thread | None = None
        self._build()

    def _build(self) -> None:
        self.grid_columnconfigure(0, weight=1)

        # ── Header ────────────────────────────────────────────────────────────
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", padx=16, pady=(14, 4))
        header.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            header,
            text="Startup Manager",
            font=ctk.CTkFont(family="Segoe UI", size=14, weight="bold"),
            anchor="w",
        ).grid(row=0, column=0, sticky="w")

        self._status_label = ctk.CTkLabel(
            header,
            text="Idle",
            font=ctk.CTkFont(size=11),
            text_color="#6B7280",
        )
        self._status_label.grid(row=0, column=1, sticky="e")

        self._scan_btn = ctk.CTkButton(
            header,
            text="Scan",
            width=64,
            height=28,
            corner_radius=6,
            font=ctk.CTkFont(size=12, weight="bold"),
            command=self._scan,
        )
        self._scan_btn.grid(row=0, column=2, sticky="e", padx=(10, 0))

        ctk.CTkLabel(
            self,
            text="View and control programs that launch at Windows startup.",
            font=ctk.CTkFont(size=11),
            text_color=("gray50", "gray60"),
            anchor="w",
        ).grid(row=1, column=0, sticky="w", padx=16, pady=(0, 8))

        # ── Scrollable table ──────────────────────────────────────────────────
        self._table_frame = ctk.CTkScrollableFrame(
            self,
            height=200,
            fg_color=("gray95", "#13111F"),
            corner_radius=6,
        )
        self._table_frame.grid(row=2, column=0, sticky="ew", padx=16, pady=(0, 14))
        self._table_frame.grid_columnconfigure(0, weight=1)

        self._empty_label = ctk.CTkLabel(
            self._table_frame,
            text="Click Scan to load startup entries.",
            text_color=("gray50", "gray60"),
            font=ctk.CTkFont(size=11),
        )
        self._empty_label.grid(row=0, column=0, pady=20)

    def _scan(self) -> None:
        """Kick off a startup scan.

        Guardrails:
        - If the automation is already running, ignore the click.
        - We reset and clear the table before starting.
        - The actual registry scan runs in a background thread.
        """
        if self.automation.status == STATUS_RUNNING:
            return
        self.automation.reset()
        self._clear_table()
        self._status_label.configure(text="Scanning…", text_color="#7B5CF0")

        self._scan_btn.configure(state="disabled")

        def _run():
            self.automation.execute()
            self.after(0, self._populate_table)
            self.after(0, lambda: self._scan_btn.configure(state="normal"))
            self.after(0, lambda: self._status_label.configure(
                text=f"{len(self.automation.entries)} entries found",
                text_color="#10B981",
            ))

        self._thread = threading.Thread(target=_run, daemon=True)
        self._thread.start()

    def _populate_table(self) -> None:
        self._clear_table()
        if not self.automation.entries:
            self._empty_label = ctk.CTkLabel(
                self._table_frame,
                text="No startup entries found.",
                text_color=("gray50", "gray60"),
                font=ctk.CTkFont(size=11),
            )
            self._empty_label.grid(row=0, column=0, pady=20)
            return

        for i, entry in enumerate(self.automation.entries):
            self._add_row(i, entry)

    def _add_row(self, row_idx: int, entry: StartupEntry) -> None:
        """Render a single startup entry row.

        Notes:
        - `entry.enabled` drives the button label/color.
        - `entry.name` may include a `_disabled_` prefix. We remove it for the
          human-readable display.
        """
        row = ctk.CTkFrame(

            self._table_frame,
            fg_color=("gray88", "#201D30") if row_idx % 2 == 0 else ("gray92", "#1A1726"),
            corner_radius=4,
        )
        row.grid(row=row_idx, column=0, sticky="ew", pady=1)
        row.grid_columnconfigure(0, weight=1)

        name = entry.name.removeprefix("_disabled_")
        cmd_short = entry.command[:60] + ("…" if len(entry.command) > 60 else "")

        info = ctk.CTkFrame(row, fg_color="transparent")
        info.grid(row=0, column=0, sticky="w", padx=10, pady=6)

        ctk.CTkLabel(
            info,
            text=name,
            font=ctk.CTkFont(size=12, weight="bold"),
            anchor="w",
        ).pack(anchor="w")

        ctk.CTkLabel(
            info,
            text=cmd_short,
            font=ctk.CTkFont(family="Consolas", size=10),
            text_color=("gray50", "gray60"),
            anchor="w",
        ).pack(anchor="w")

        btn_text = "Disable" if entry.enabled else "Enable"
        btn_color = "#EF4444" if entry.enabled else "#10B981"

        # Button toggles enable/disable by delegating to StartupManager.
        # We capture `entry` and the row index via default args to avoid
        # late-binding issues in lambdas.
        toggle_btn = ctk.CTkButton(
            row,
            text=btn_text,

            width=70,
            height=26,
            corner_radius=4,
            fg_color=btn_color,
            hover_color="#C53030" if entry.enabled else "#059669",
            font=ctk.CTkFont(size=11),
            command=lambda e=entry, b=toggle_btn if False else None, ri=row_idx: self._toggle(e, ri),
        )
        toggle_btn.grid(row=0, column=1, padx=10, pady=6)

    def _toggle(self, entry: StartupEntry, row_idx: int) -> None:
        """Enable or disable an entry and refresh the affected row."""
        if entry.enabled:

            success = self.automation.disable_entry(entry)
        else:
            success = self.automation.enable_entry(entry)

        if success:
            # Refresh just that row
            for widget in self._table_frame.winfo_children():
                info = widget.grid_info()
                if info.get("row") == row_idx:
                    widget.destroy()
                    break
            self._add_row(row_idx, entry)

    def _clear_table(self) -> None:
        for widget in self._table_frame.winfo_children():
            widget.destroy()
