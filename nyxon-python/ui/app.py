"""
Nyxon Automation Suite - Main Application Window
Sidebar layout matching the Nyxon design mockup.
"""

import time
import threading
import customtkinter as ctk
from pathlib import Path
from datetime import datetime
from tkinter import filedialog

from automations import FileOrganizer, SystemFlush, NetworkChecker, DiskAnalyser, BulkRename, DuplicateFinder,WebScraper
from automations.startup_manager import StartupManager
from ui.sidebar import Sidebar
from utils.settings import settings
from utils.constants import (
    APP_NAME, WINDOW_DEFAULT_SIZE, WINDOW_MIN_WIDTH, WINDOW_MIN_HEIGHT, ICON_PATH
)

# ── Palette (matches mockup) ──────────────────────────────────────────────────
BG_MAIN    = "#0F0D1A"
BG_PANEL   = "#13111F"
BG_CARD    = "#1A1726"
BG_CARD2   = "#1E1B2E"
ACCENT     = "#7B5CF0"
ACCENT2    = "#5B4CC0"
TEXT_DIM   = "#6B6880"
TEXT_MID   = "#9895AA"
TEXT_LIGHT = "#C4C2D4"
TEXT_WHITE = "#FFFFFF"
GREEN      = "#10B981"
YELLOW     = "#F59E0B"
RED        = "#EF4444"
BLUE       = "#3B82F6"

def dim(hex_color: str, factor: float = 0.15) -> str:
    """
    Blend a hex color toward the dark card background.
    Replaces 8-digit hex alpha (#RRGGBBAA) which Tkinter does not support.
    factor=0.15 ≈ 13% opacity, matching the original 0x22/255 intent.
    """
    hex_color = hex_color.lstrip("#")
    r, g, b = int(hex_color[0:2], 16), int(hex_color[2:4], 16), int(hex_color[4:6], 16)
    br, bg_, bb = 26, 23, 38   # BG_CARD = #1A1726
    nr = int(br + (r - br) * factor)
    ng = int(bg_ + (g - bg_) * factor)
    nb = int(bb + (b - bb) * factor)
    return f"#{nr:02x}{ng:02x}{nb:02x}"



class NyxonApp(ctk.CTk):
    """Root application window — sidebar layout."""

    def __init__(self) -> None:
        super().__init__()
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")
        self.configure(fg_color=BG_MAIN)

        self.title(APP_NAME)
        self.geometry(WINDOW_DEFAULT_SIZE)
        self.minsize(WINDOW_MIN_WIDTH, WINDOW_MIN_HEIGHT)
        if ICON_PATH.exists():
            self.iconbitmap(str(ICON_PATH))

        # Automation instances (shared so run history persists across nav)
        self._automations = {
            "File Organizer":   FileOrganizer(),
            "System Flush":     SystemFlush(),
            "Network Checker":  NetworkChecker(),
            "Startup Manager":  StartupManager(),
            "Disk Analyser":    DiskAnalyser(),
            "Bulk Rename":      BulkRename(),
            "Duplicate Finder": DuplicateFinder(),
            "Web Scraper": WebScraper(),
        }
        self._activity_log: list[dict] = []   # recent activity entries

        self._build()

    # ── Layout skeleton ───────────────────────────────────────────────────────

    def _build(self) -> None:
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # Sidebar
        self._sidebar = Sidebar(self, on_navigate=self._navigate)
        self._sidebar.grid(row=0, column=0, sticky="ns")

        # Content area (everything to the right of sidebar)
        self._content = ctk.CTkFrame(self, fg_color=BG_MAIN, corner_radius=0)
        self._content.grid(row=0, column=1, sticky="nsew")
        self._content.grid_columnconfigure(0, weight=1)
        self._content.grid_rowconfigure(1, weight=1)

        self._build_topbar()

        # Page container
        self._page_frame = ctk.CTkFrame(self._content, fg_color="transparent")
        self._page_frame.grid(row=1, column=0, sticky="nsew", padx=0, pady=0)
        self._page_frame.grid_columnconfigure(0, weight=1)
        self._page_frame.grid_rowconfigure(0, weight=1)

        self._show_dashboard()

    def _build_topbar(self) -> None:
        bar = ctk.CTkFrame(self._content, fg_color=BG_PANEL, corner_radius=0, height=56)
        bar.grid(row=0, column=0, sticky="ew")
        bar.grid_columnconfigure(1, weight=1)
        bar.grid_propagate(False)

        # Search bar
        search_frame = ctk.CTkFrame(bar, fg_color=BG_CARD, corner_radius=8, height=34)
        search_frame.grid(row=0, column=0, sticky="w", padx=20, pady=11)
        search_frame.grid_propagate(False)

        ctk.CTkLabel(
            search_frame, text="🔍", font=ctk.CTkFont(size=12), text_color=TEXT_DIM
        ).pack(side="left", padx=(10, 4), pady=6)
        self._search_var = ctk.StringVar()
        self._search_var.trace_add("write", self._on_search)
        search_entry = ctk.CTkEntry(
            search_frame,
            placeholder_text="Search tools...",
            font=ctk.CTkFont(size=12),
            fg_color="transparent",
            border_width=0,
            text_color=TEXT_LIGHT,
            placeholder_text_color=TEXT_DIM,
            textvariable=self._search_var,
            width=220,
        )
        search_entry.pack(side="left", pady=4)
        self.bind("<Control-k>", lambda e: search_entry.focus())
        ctk.CTkLabel(
            search_frame, text="Ctrl+K",
            font=ctk.CTkFont(size=10),
            text_color=TEXT_DIM,
            fg_color="#252236",
            corner_radius=4,
            width=46,
        ).pack(side="left", padx=(6, 8), pady=6)

        # Right side icons
        icon_bar = ctk.CTkFrame(bar, fg_color="transparent")
        icon_bar.grid(row=0, column=2, sticky="e", padx=20)

        # Theme toggle
        self._theme_var = ctk.StringVar(value="dark")
        ctk.CTkButton(
            icon_bar, text="☀", width=32, height=32, corner_radius=8,
            fg_color=BG_CARD, hover_color=BG_CARD2, font=ctk.CTkFont(size=14),
            command=self._toggle_theme,
        ).pack(side="left", padx=4)

        ctk.CTkLabel(
            icon_bar, text="🔔", font=ctk.CTkFont(size=16),
            text_color=TEXT_MID, fg_color="transparent",
        ).pack(side="left", padx=4)

        ctk.CTkLabel(
            icon_bar,
            text="N",
            width=32, height=32,
            corner_radius=16,
            fg_color=ACCENT,
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color=TEXT_WHITE,
        ).pack(side="left", padx=(8, 0))

    # ── Navigation ────────────────────────────────────────────────────────────

    def _navigate(self, page: str) -> None:
        for w in self._page_frame.winfo_children():
            w.destroy()

        if page == "Dashboard":
            self._show_dashboard()
        elif page == "Settings":
            self._show_settings()
        else:
            self._show_tool_page(page)

    # ── Dashboard ─────────────────────────────────────────────────────────────

    def _show_dashboard(self) -> None:
        # Outer scrollable wrapper so dashboard content is always reachable
        scroll = ctk.CTkScrollableFrame(
            self._page_frame, fg_color="transparent", corner_radius=0,
        )
        scroll.grid(row=0, column=0, sticky="nsew")
        scroll.grid_columnconfigure(0, weight=1)

        frame = ctk.CTkFrame(scroll, fg_color="transparent")
        frame.pack(fill="both", expand=True, padx=24, pady=20)
        frame.grid_columnconfigure(0, weight=1)

        # ── Welcome header ────────────────────────────────────────────────────
        top = ctk.CTkFrame(frame, fg_color="transparent")
        top.grid(row=0, column=0, sticky="ew", pady=(0, 20))
        top.grid_columnconfigure(0, weight=1)

        left = ctk.CTkFrame(top, fg_color="transparent")
        left.pack(side="left")
        ctk.CTkLabel(left,
            text="Welcome back, Nyxon User! 👋",
            font=ctk.CTkFont(family="Segoe UI", size=22, weight="bold"),
            text_color=TEXT_WHITE, anchor="w").pack(anchor="w")
        ctk.CTkLabel(left,
            text="Automate. Optimise. Achieve more.",
            font=ctk.CTkFont(size=13), text_color=TEXT_MID, anchor="w").pack(anchor="w", pady=(2, 0))

        now = datetime.now()
        date_badge = ctk.CTkFrame(top, fg_color=BG_CARD, corner_radius=10)
        date_badge.pack(side="right")
        ctk.CTkLabel(date_badge,
            text=f"📅  {now.strftime('%b %d, %Y')}\n      {now.strftime('%I:%M %p')}",
            font=ctk.CTkFont(size=12), text_color=TEXT_LIGHT, justify="left").pack(padx=16, pady=10)

        # ── Quick Tools — built dynamically from _automations ─────────────────
        ctk.CTkLabel(frame, text="Quick Tools",
            font=ctk.CTkFont(size=15, weight="bold"),
            text_color=TEXT_WHITE, anchor="w").grid(row=1, column=0, sticky="w", pady=(0, 10))

        # Pull icon/color from sidebar registry
        from ui.sidebar import AUTOMATION_REGISTRY
        reg = {name: (icon, cat) for icon, name, cat in AUTOMATION_REGISTRY}

        _colors = {
            "File Organizer":  ACCENT,
            "System Flush":    "#14B8A6",
            "Network Checker": YELLOW,
            "Startup Manager": "#F97316",
            "Disk Analyser":   "#EC4899",
            "Bulk Rename":     "#8B5CF6",
            "Web Scraper": "#06B6D4",
        }

        tools_grid = ctk.CTkFrame(frame, fg_color="transparent")
        tools_grid.grid(row=2, column=0, sticky="ew")
        cols_per_row = 4
        names = list(self._automations.keys())
        for i in range(min(cols_per_row, len(names))):
            tools_grid.grid_columnconfigure(i, weight=1)

        for idx, name in enumerate(names):
            icon, _ = reg.get(name, ("⚙", "Other"))
            color = _colors.get(name, ACCENT)
            desc = self._automations[name].description
            col = idx % cols_per_row
            row_num = idx // cols_per_row
            self._quick_tool_card(tools_grid, icon, name, desc, color, col, row_num)

        # ── Automation Overview ───────────────────────────────────────────────
        ctk.CTkLabel(frame, text="Automation Overview",
            font=ctk.CTkFont(size=15, weight="bold"),
            text_color=TEXT_WHITE, anchor="w").grid(row=3, column=0, sticky="w", pady=(24, 10))

        stats_row = ctk.CTkFrame(frame, fg_color="transparent")
        stats_row.grid(row=4, column=0, sticky="ew")
        for i in range(4):
            stats_row.grid_columnconfigure(i, weight=1)

        completed = sum(1 for a in self._automations.values() if a.status == "Done")
        running   = sum(1 for a in self._automations.values() if a.status == "Running…")

        stat_defs = [
            ("☰",  str(len(self._automations)), "Total Tools",  "All available tools",    ACCENT),
            ("✔",  str(completed),              "Completed",    "Tasks completed",        GREEN),
            ("◷",  str(running),                "Running",      "Tasks in progress",      YELLOW),
            ("📅", str(len(self._activity_log)), "Activity",    "Tasks run this session", BLUE),
        ]
        for col, (icon, num, label, sub, color) in enumerate(stat_defs):
            self._stat_card(stats_row, icon, num, label, sub, color, col)

        # ── Recent Activity ───────────────────────────────────────────────────
        ctk.CTkLabel(frame, text="Recent Activity",
            font=ctk.CTkFont(size=15, weight="bold"),
            text_color=TEXT_WHITE, anchor="w").grid(row=5, column=0, sticky="w", pady=(24, 10))

        act_frame = ctk.CTkFrame(frame, fg_color=BG_PANEL, corner_radius=12)
        act_frame.grid(row=6, column=0, sticky="ew")
        act_frame.grid_columnconfigure(0, weight=1)

        if not self._activity_log:
            ctk.CTkLabel(act_frame,
                text="No recent activity — run a tool to get started.",
                font=ctk.CTkFont(size=12), text_color=TEXT_DIM).pack(pady=24)
        else:
            for i, entry in enumerate(reversed(self._activity_log[-5:])):
                self._activity_row(act_frame, entry, i)

        ctk.CTkLabel(frame,
            text='"Automate the boring things so you can focus on the great things."  — Nyxon',
            font=ctk.CTkFont(size=11, slant="italic"),
            text_color=TEXT_DIM).grid(row=7, column=0, pady=(20, 0))

    def _on_search(self, *_) -> None:
        """Filter automations by search query and navigate on exact match."""
        query = self._search_var.get().strip().lower()
        if not query:
            return
        for name in self._automations:
            if query in name.lower():
                self._sidebar.set_active(name)
                return

    def _quick_tool_card(self, parent, icon, name, desc, color, col, row_num=0) -> None:
        card = ctk.CTkFrame(parent, fg_color=BG_CARD, corner_radius=12)
        card.grid(row=row_num, column=col, sticky="ew", padx=(0 if col == 0 else 10, 0), pady=(0 if row_num == 0 else 10, 0))

        # Icon circle
        ctk.CTkLabel(
            card, text=icon,
            font=ctk.CTkFont(size=22),
            fg_color=dim(color),
            width=52, height=52,
            corner_radius=26,
        ).pack(anchor="w", padx=16, pady=(16, 8))

        ctk.CTkLabel(
            card, text=name,
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color=TEXT_WHITE, anchor="w",
        ).pack(anchor="w", padx=16)

        ctk.CTkLabel(
            card, text=desc,
            font=ctk.CTkFont(size=11),
            text_color=TEXT_DIM, anchor="w",
            wraplength=160, justify="left",
        ).pack(anchor="w", padx=16, pady=(4, 12))

        ctk.CTkButton(
            card,
            text="Run Tool  →",
            height=32,
            corner_radius=8,
            fg_color=BG_CARD2,
            hover_color="#252236",
            text_color=TEXT_LIGHT,
            font=ctk.CTkFont(size=11),
            anchor="w",
            command=lambda n=name: self._sidebar.set_active(n),
        ).pack(fill="x", padx=16, pady=(0, 16))

    def _stat_card(self, parent, icon, number, label, sub, color, col) -> None:
        card = ctk.CTkFrame(parent, fg_color=BG_CARD, corner_radius=12)
        card.grid(row=0, column=col, sticky="ew", padx=(0 if col == 0 else 10, 0))

        row = ctk.CTkFrame(card, fg_color="transparent")
        row.pack(fill="x", padx=16, pady=16)

        ctk.CTkLabel(
            row, text=icon,
            font=ctk.CTkFont(size=18),
            fg_color=dim(color),
            width=40, height=40, corner_radius=20,
            text_color=color,
        ).pack(side="left")

        info = ctk.CTkFrame(row, fg_color="transparent")
        info.pack(side="left", padx=12)

        ctk.CTkLabel(
            info, text=number,
            font=ctk.CTkFont(size=22, weight="bold"),
            text_color=TEXT_WHITE, anchor="w",
        ).pack(anchor="w")
        ctk.CTkLabel(
            info, text=label,
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color=TEXT_LIGHT, anchor="w",
        ).pack(anchor="w")
        ctk.CTkLabel(
            info, text=sub,
            font=ctk.CTkFont(size=10),
            text_color=TEXT_DIM, anchor="w",
        ).pack(anchor="w")

    def _activity_row(self, parent, entry: dict, idx: int) -> None:
        bg = BG_CARD if idx % 2 == 0 else "transparent"
        row = ctk.CTkFrame(parent, fg_color=bg, corner_radius=8)
        row.pack(fill="x", padx=12, pady=2)
        row.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(
            row,
            text=entry.get("icon", "⚙"),
            font=ctk.CTkFont(size=18),
            fg_color=dim(entry.get("color", ACCENT)),
            width=36, height=36, corner_radius=18,
        ).grid(row=0, column=0, padx=(12, 10), pady=8)

        info = ctk.CTkFrame(row, fg_color="transparent")
        info.grid(row=0, column=1, sticky="w")
        ctk.CTkLabel(
            info, text=entry["name"],
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=TEXT_WHITE, anchor="w",
        ).pack(anchor="w")
        ctk.CTkLabel(
            info, text=entry.get("detail", ""),
            font=ctk.CTkFont(size=11),
            text_color=TEXT_DIM, anchor="w",
        ).pack(anchor="w")

        ctk.CTkLabel(
            row, text=entry.get("time", ""),
            font=ctk.CTkFont(size=11),
            text_color=TEXT_DIM,
        ).grid(row=0, column=2, padx=16)

        status_color = GREEN if entry.get("status") == "Done" else (
            RED if entry.get("status") == "Error" else YELLOW
        )
        ctk.CTkLabel(
            row, text=entry.get("status", "Done"),
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color=status_color,
            fg_color=dim(status_color),
            corner_radius=6,
            width=74,
        ).grid(row=0, column=3, padx=(0, 12))

    # ── Tool pages ────────────────────────────────────────────────────────────

    def _show_tool_page(self, name: str) -> None:
        """Two-column layout: main config/log on left, right panel for quick actions."""
        automation = self._automations[name]

        outer = ctk.CTkFrame(self._page_frame, fg_color="transparent")
        outer.grid(row=0, column=0, sticky="nsew", padx=24, pady=20)
        outer.grid_columnconfigure(0, weight=1)
        outer.grid_columnconfigure(1, minsize=260)
        outer.grid_rowconfigure(1, weight=1)

        # Page title
        ctk.CTkLabel(
            outer, text=name,
            font=ctk.CTkFont(size=20, weight="bold"),
            text_color=TEXT_WHITE, anchor="w",
        ).grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 16))

        # ── Left: main card ───────────────────────────────────────────────────
        left = ctk.CTkFrame(outer, fg_color="transparent")
        left.grid(row=1, column=0, sticky="nsew", padx=(0, 16))
        left.grid_columnconfigure(0, weight=1)

        self._build_tool_main(left, name, automation)

        # ── Right panel ───────────────────────────────────────────────────────
        right = ctk.CTkFrame(outer, fg_color=BG_PANEL, corner_radius=14)
        right.grid(row=1, column=1, sticky="nsew")
        right.grid_columnconfigure(0, weight=1)

        self._build_right_panel(right, name, automation)

    def _build_tool_main(self, parent, name: str, automation) -> None:
        """Main content area per tool — config options + log."""
        icons = {
            "File Organizer":  "📁",
            "System Flush":    "🖥",
            "Network Checker": "🌐",
            "Startup Manager": "🚀",
            "Disk Analyser":   "💾",
            "Bulk Rename":     "✏️",
            "Duplicate Finder": "🔍",
            "Web Scraper": "🌍",
        }
        colors = {
            "File Organizer":  ACCENT,
            "System Flush":    "#14B8A6",
            "Network Checker": YELLOW,
            "Startup Manager": "#F97316",
            "Disk Analyser":   "#EC4899",
            "Bulk Rename":     "#8B5CF6",
            "Duplicate Finder": "#F43F5E",
            "Web Scraper": "#06B6D4",
        }

        # Status card
        status_card = ctk.CTkFrame(parent, fg_color=BG_CARD, corner_radius=12)
        status_card.pack(fill="x", pady=(0, 12))
        status_card.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(
            status_card,
            text=icons.get(name, "⚙"),
            font=ctk.CTkFont(size=26),
            fg_color=dim(colors.get(name, ACCENT)),
            width=56, height=56, corner_radius=28,
        ).grid(row=0, column=0, padx=16, pady=14)

        info = ctk.CTkFrame(status_card, fg_color="transparent")
        info.grid(row=0, column=1, sticky="w")

        ctk.CTkLabel(
            info, text=automation.description,
            font=ctk.CTkFont(size=12),
            text_color=TEXT_MID, anchor="w",
        ).pack(anchor="w")

        self._status_lbl = ctk.CTkLabel(
            info, text=f"Status: {automation.status}",
            font=ctk.CTkFont(size=12),
            text_color=TEXT_DIM, anchor="w",
        )
        self._status_lbl.pack(anchor="w", pady=(2, 0))

        # Config options per tool
        cfg_card = ctk.CTkFrame(parent, fg_color=BG_CARD, corner_radius=12)
        cfg_card.pack(fill="x", pady=(0, 12))
        cfg_card.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            cfg_card, text="Configuration",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color=TEXT_WHITE, anchor="w",
        ).pack(anchor="w", padx=16, pady=(14, 8))

        if name == "File Organizer":
            self._cfg_file_organizer(cfg_card, automation)
        elif name == "System Flush":
            self._cfg_system_flush(cfg_card)
        elif name == "Network Checker":
            self._cfg_network_checker(cfg_card)
        elif name == "Startup Manager":
            self._cfg_startup_manager(cfg_card, automation)
        elif name == "Disk Analyser":
            self._cfg_disk_analyser(cfg_card, automation)
        elif name == "Bulk Rename":
            self._cfg_bulk_rename(cfg_card, automation)
        elif name == "Web Scraper":
            self._cfg_web_scraper(cfg_card, automation)    

        # Log output
        log_card = ctk.CTkFrame(parent, fg_color=BG_CARD, corner_radius=12)
        log_card.pack(fill="x", pady=(0, 0))
        log_card.grid_columnconfigure(0, weight=1)
        log_card.grid_rowconfigure(1, weight=1)

        ctk.CTkLabel(
            log_card, text="Output Log",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color=TEXT_WHITE, anchor="w",
        ).grid(row=0, column=0, sticky="w", padx=16, pady=(14, 6))

        self._log_box = ctk.CTkTextbox(
            log_card,
            font=ctk.CTkFont(family="Consolas", size=11),
            fg_color="#0C0A18",
            text_color="#A0F0A0",
            corner_radius=8,
            state="disabled",
            wrap="word",
        )
        self._log_box.grid(row=1, column=0, sticky="nsew", padx=14, pady=(0, 14))

        # Replay existing log lines
        if automation.log_lines:
            self._log_box.configure(state="normal")
            for line in automation.log_lines:
                self._log_box.insert("end", line + "\n")
            self._log_box.see("end")
            self._log_box.configure(state="disabled")

        # Wire callbacks to this log box
        automation.set_callbacks(
            on_progress=None,
            on_log=self._cb_log,
            on_status=lambda s: self._status_lbl.configure(text=f"Status: {s}"),
        )

    def _build_right_panel(self, parent, name: str, automation) -> None:
        """Right-side panel: icon, Run/Settings buttons, mini log."""
        icons = {
            "File Organizer":  "📁",
            "System Flush":    "🖥",
            "Network Checker": "🌐",
            "Startup Manager": "🚀",
            "Disk Analyser":   "💾",
            "Bulk Rename":     "✏️",
            "Duplicate Finder": "🔍",
            "Web Scraper": "🌍",
        }
        colors = {
            "File Organizer":  ACCENT,
            "System Flush":    "#14B8A6",
            "Network Checker": YELLOW,
            "Startup Manager": "#F97316",
            "Disk Analyser":   "#EC4899",
            "Bulk Rename":     "#8B5CF6",
            "Web Scraper": "#06B6D4",
        }

        ctk.CTkLabel(
            parent,
            text=icons.get(name, "⚙"),
            font=ctk.CTkFont(size=32),
            fg_color=dim(colors.get(name, ACCENT)),
            width=64, height=64, corner_radius=32,
        ).pack(pady=(20, 6))

        ctk.CTkLabel(
            parent, text=name,
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=TEXT_WHITE,
        ).pack()

        ctk.CTkLabel(
            parent, text=automation.description,
            font=ctk.CTkFont(size=11),
            text_color=TEXT_DIM,
            wraplength=220, justify="center",
        ).pack(pady=(4, 16), padx=16)

        ctk.CTkLabel(
            parent, text="Actions",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=TEXT_MID, anchor="w",
        ).pack(anchor="w", padx=16)

        # Progress bar
        self._progress_bar = ctk.CTkProgressBar(parent, height=6, corner_radius=3)
        self._progress_bar.set(automation.progress)
        self._progress_bar.pack(fill="x", padx=16, pady=(10, 4))

        self._run_btn = ctk.CTkButton(
            parent,
            text="▷  Run Now",
            height=42,
            corner_radius=10,
            fg_color=ACCENT,
            hover_color=ACCENT2,
            font=ctk.CTkFont(size=14, weight="bold"),
            command=lambda: self._run_automation(name, automation),
        )
        self._run_btn.pack(fill="x", padx=16, pady=(6, 6))

        ctk.CTkButton(
            parent,
            text="⚙  Settings",
            height=36,
            corner_radius=10,
            fg_color=BG_CARD2,
            hover_color="#252236",
            text_color=TEXT_LIGHT,
            font=ctk.CTkFont(size=12),
            command=lambda: self._navigate("Settings"),
        ).pack(fill="x", padx=16, pady=(0, 16))

        # Wire progress callback here
        automation.set_callbacks(
            on_progress=lambda v: self.after(0, lambda: self._progress_bar.set(v)),
            on_log=self._cb_log,
            on_status=self._cb_status_right,
        )

    # ── Settings page ─────────────────────────────────────────────────────────

    def _show_settings(self) -> None:
        frame = ctk.CTkFrame(self._page_frame, fg_color="transparent")
        frame.grid(row=0, column=0, sticky="nsew", padx=24, pady=20)
        frame.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            frame, text="Settings",
            font=ctk.CTkFont(size=20, weight="bold"),
            text_color=TEXT_WHITE, anchor="w",
        ).grid(row=0, column=0, sticky="w", pady=(0, 20))

        card = ctk.CTkFrame(frame, fg_color=BG_CARD, corner_radius=12)
        card.grid(row=1, column=0, sticky="ew")

        ctk.CTkLabel(
            card, text="Appearance",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color=TEXT_WHITE, anchor="w",
        ).pack(anchor="w", padx=20, pady=(16, 8))

        row = ctk.CTkFrame(card, fg_color="transparent")
        row.pack(fill="x", padx=20, pady=(0, 16))
        ctk.CTkLabel(row, text="Theme", font=ctk.CTkFont(size=12), text_color=TEXT_LIGHT).pack(side="left")
        ctk.CTkOptionMenu(
            row, values=["dark", "light", "system"],
            command=lambda v: (ctk.set_appearance_mode(v), settings.set("theme", v)),
            font=ctk.CTkFont(size=12), width=120,
        ).pack(side="right")

    # ── Tool config builders ──────────────────────────────────────────────────

    def _cfg_file_organizer(self, parent, automation) -> None:
        row = ctk.CTkFrame(parent, fg_color="transparent")
        row.pack(fill="x", padx=16, pady=(0, 14))
        row.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(row, text="Target folder", font=ctk.CTkFont(size=12), text_color=TEXT_LIGHT).grid(
            row=0, column=0, sticky="w", padx=(0, 12)
        )

        self._folder_entry = ctk.CTkEntry(
            row, font=ctk.CTkFont(size=11),
            fg_color=BG_MAIN, border_color="#3A3550", text_color=TEXT_LIGHT,
            placeholder_text=str(automation.target_folder),
        )
        self._folder_entry.grid(row=0, column=1, sticky="ew")
        self._folder_entry.insert(0, str(automation.target_folder))

        ctk.CTkButton(
            row, text="📂", width=34, height=32, corner_radius=6,
            fg_color=BG_CARD2, hover_color="#252236",
            command=lambda: self._browse_folder(automation),
        ).grid(row=0, column=2, padx=(6, 0))


    def _cfg_web_scraper(self, parent, automation) -> None:
        from automations.web_scraper import ScrapeMode, PRESETS

        # URL row
        url_row = ctk.CTkFrame(parent, fg_color="transparent")
        url_row.pack(fill="x", padx=16, pady=(0, 8))
        url_row.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(url_row, text="URL", font=ctk.CTkFont(size=12),
            text_color=TEXT_LIGHT).grid(row=0, column=0, sticky="w", padx=(0, 12))

        url_entry = ctk.CTkEntry(url_row, font=ctk.CTkFont(size=11),
            fg_color=BG_MAIN, border_color="#3A3550", text_color=TEXT_LIGHT,
            placeholder_text="https://example.com")
        url_entry.grid(row=0, column=1, sticky="ew")
        if automation.url:
            url_entry.insert(0, automation.url)

        def _on_url_change(*_):
            automation.url = url_entry.get().strip()
        url_entry.bind("<KeyRelease>", _on_url_change)

        # Preset dropdown
        preset_row = ctk.CTkFrame(parent, fg_color="transparent")
        preset_row.pack(fill="x", padx=16, pady=(0, 8))

        ctk.CTkLabel(preset_row, text="Preset", font=ctk.CTkFont(size=12),
            text_color=TEXT_LIGHT).pack(side="left", padx=(0, 12))

        preset_labels = ["— none —"] + [label for label, _, _ in PRESETS]
        preset_var = ctk.StringVar(value="— none —")

        def _on_preset(choice):
            for label, url, mode in PRESETS:
                if label == choice:
                    url_entry.delete(0, "end")
                    url_entry.insert(0, url)
                    automation.url = url
                    automation.mode = mode
                    mode_var.set(mode.value)
                    break

        ctk.CTkOptionMenu(preset_row, values=preset_labels,
            variable=preset_var, command=_on_preset,
            font=ctk.CTkFont(size=12), width=180).pack(side="left")

        # Mode selector
        mode_row = ctk.CTkFrame(parent, fg_color="transparent")
        mode_row.pack(fill="x", padx=16, pady=(0, 8))

        ctk.CTkLabel(mode_row, text="Mode", font=ctk.CTkFont(size=12),
            text_color=TEXT_LIGHT).pack(side="left", padx=(0, 12))

        mode_var = ctk.StringVar(value=automation.mode.value)

        def _on_mode(choice):
            automation.mode = ScrapeMode(choice)

        ctk.CTkOptionMenu(mode_row,
        values=[m.value for m in ScrapeMode],
        variable=mode_var, command=_on_mode,
        font=ctk.CTkFont(size=12), width=120).pack(side="left")

        # Save options
        save_row = ctk.CTkFrame(parent, fg_color="transparent")
        save_row.pack(fill="x", padx=16, pady=(0, 8))

        ctk.CTkLabel(save_row, text="Save as", font=ctk.CTkFont(size=12),
            text_color=TEXT_LIGHT).pack(side="left", padx=(0, 12))

        txt_var = ctk.BooleanVar(value=automation.save_txt)
        csv_var = ctk.BooleanVar(value=automation.save_csv)

        ctk.CTkCheckBox(save_row, text="TXT", variable=txt_var,
            font=ctk.CTkFont(size=12), text_color=TEXT_LIGHT,
            command=lambda: setattr(automation, "save_txt", txt_var.get())
        ).pack(side="left", padx=(0, 12))

        ctk.CTkCheckBox(save_row, text="CSV", variable=csv_var,
            font=ctk.CTkFont(size=12), text_color=TEXT_LIGHT,
            command=lambda: setattr(automation, "save_csv", csv_var.get())
        ).pack(side="left")

        # Output folder
        out_row = ctk.CTkFrame(parent, fg_color="transparent")
        out_row.pack(fill="x", padx=16, pady=(0, 14))
        out_row.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(out_row, text="Save to", font=ctk.CTkFont(size=12),
            text_color=TEXT_LIGHT).grid(row=0, column=0, sticky="w", padx=(0, 12))

        out_entry = ctk.CTkEntry(out_row, font=ctk.CTkFont(size=11),
            fg_color=BG_MAIN, border_color="#3A3550", text_color=TEXT_LIGHT)
        out_entry.grid(row=0, column=1, sticky="ew")
        out_entry.insert(0, str(automation.output_dir))

        def _browse_output():
            from tkinter import filedialog
            folder = filedialog.askdirectory(title="Select save folder")
            if folder:
                out_entry.delete(0, "end")
                out_entry.insert(0, folder)
                automation.output_dir = Path(folder)
                settings.set("web_scraper.output_dir", folder)

        ctk.CTkButton(out_row, text="📂", width=34, height=32, corner_radius=6,
            fg_color=BG_CARD2, hover_color="#252236",
            command=_browse_output).grid(row=0, column=2, padx=(6, 0))


    def _cfg_system_flush(self, parent) -> None:
        cfg = settings.get("system_flush", {})
        self._var_temp = ctk.BooleanVar(value=cfg.get("clear_temp", True))
        self._var_prefetch = ctk.BooleanVar(value=cfg.get("clear_prefetch", False))
        self._var_recycle = ctk.BooleanVar(value=cfg.get("empty_recycle_bin", False))

        for text, var, key in [
            ("Clear Temp folders", self._var_temp, "system_flush.clear_temp"),
            ("Clear Prefetch (admin)", self._var_prefetch, "system_flush.clear_prefetch"),
            ("Empty Recycle Bin", self._var_recycle, "system_flush.empty_recycle_bin"),
        ]:
            ctk.CTkCheckBox(
                parent, text=text, variable=var,
                font=ctk.CTkFont(size=12), text_color=TEXT_LIGHT,
                command=lambda k=key, v=var: settings.set(k, v.get()),
            ).pack(anchor="w", padx=16, pady=4)
        ctk.CTkFrame(parent, height=12, fg_color="transparent").pack()

    def _cfg_network_checker(self, parent) -> None:
        ctk.CTkLabel(
            parent, text="Hosts to check (comma-separated)",
            font=ctk.CTkFont(size=12), text_color=TEXT_LIGHT, anchor="w",
        ).pack(anchor="w", padx=16, pady=(0, 4))

        current = ", ".join(settings.get("network_checker.hosts", []))
        self._hosts_entry = ctk.CTkEntry(
            parent, font=ctk.CTkFont(size=11),
            fg_color=BG_MAIN, border_color="#3A3550", text_color=TEXT_LIGHT,
        )
        self._hosts_entry.pack(fill="x", padx=16, pady=(0, 8))
        self._hosts_entry.insert(0, current)

        ctk.CTkButton(
            parent, text="Save", width=80, height=30, corner_radius=6,
            fg_color=ACCENT, hover_color=ACCENT2,
            command=self._save_hosts,
        ).pack(anchor="w", padx=16, pady=(0, 14))

    def _cfg_startup_manager(self, parent, automation) -> None:
        ctk.CTkLabel(
            parent,
            text="Click Run Now to scan Windows startup registry entries.\nYou can then enable or disable individual programs.",
            font=ctk.CTkFont(size=12),
            text_color=TEXT_MID,
            anchor="w", justify="left",
        ).pack(anchor="w", padx=16, pady=(0, 14))

    def _cfg_disk_analyser(self, parent, automation) -> None:
        row = ctk.CTkFrame(parent, fg_color="transparent")
        row.pack(fill="x", padx=16, pady=(0, 14))
        row.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(
            row, text="Scan path", font=ctk.CTkFont(size=12), text_color=TEXT_LIGHT
        ).grid(row=0, column=0, sticky="w", padx=(0, 12))

        self._disk_path_entry = ctk.CTkEntry(
            row, font=ctk.CTkFont(size=11),
            fg_color=BG_MAIN, border_color="#3A3550", text_color=TEXT_LIGHT,
        )
        self._disk_path_entry.grid(row=0, column=1, sticky="ew")
        self._disk_path_entry.insert(0, str(automation.scan_path))

        def _browse():
            from tkinter import filedialog
            folder = filedialog.askdirectory(title="Select folder to scan")
            if folder:
                self._disk_path_entry.delete(0, "end")
                self._disk_path_entry.insert(0, folder)
                automation.scan_path = Path(folder)
                settings.set("disk_analyser.scan_path", folder)

        ctk.CTkButton(
            row, text="\U0001f4c2", width=34, height=32, corner_radius=6,
            fg_color=BG_CARD2, hover_color="#252236",
            command=_browse,
        ).grid(row=0, column=2, padx=(6, 0))


    def _cfg_bulk_rename(self, parent, automation) -> None:
        from automations.bulk_rename import RenameMode

        # ── Folder picker ──────────────────────────────────────────────────
        row = ctk.CTkFrame(parent, fg_color="transparent")
        row.pack(fill="x", padx=16, pady=(0, 10))
        row.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(row, text="Folder", font=ctk.CTkFont(size=12), text_color=TEXT_LIGHT).grid(
            row=0, column=0, sticky="w", padx=(0, 12)
        )
        self._rename_folder_entry = ctk.CTkEntry(
            row, font=ctk.CTkFont(size=11),
            fg_color=BG_MAIN, border_color="#3A3550", text_color=TEXT_LIGHT,
        )
        self._rename_folder_entry.grid(row=0, column=1, sticky="ew")
        self._rename_folder_entry.insert(0, str(automation.target_folder))

        def _browse():
            from tkinter import filedialog
            folder = filedialog.askdirectory()
            if folder:
                self._rename_folder_entry.delete(0, "end")
                self._rename_folder_entry.insert(0, folder)
                automation.target_folder = Path(folder)
                settings.set("bulk_rename.target_folder", folder)

        ctk.CTkButton(
            row, text="📂", width=34, height=32, corner_radius=6,
            fg_color=BG_CARD2, hover_color="#252236", command=_browse,
        ).grid(row=0, column=2, padx=(6, 0))

        # ── Mode selector ──────────────────────────────────────────────────
        mode_row = ctk.CTkFrame(parent, fg_color="transparent")
        mode_row.pack(fill="x", padx=16, pady=(0, 10))

        ctk.CTkLabel(mode_row, text="Mode", font=ctk.CTkFont(size=12), text_color=TEXT_LIGHT).pack(side="left", padx=(0, 12))

        mode_var = ctk.StringVar(value="Prefix")
        mode_menu = ctk.CTkOptionMenu(
            mode_row,
            values=["Prefix", "Suffix", "Replace", "Sequential"],
            variable=mode_var,
            font=ctk.CTkFont(size=12),
            width=130,
        )
        mode_menu.pack(side="left")

        # File filter
        ctk.CTkLabel(mode_row, text="  Filter (e.g. .jpg)", font=ctk.CTkFont(size=12), text_color=TEXT_DIM).pack(side="left", padx=(16, 6))
        filter_entry = ctk.CTkEntry(
            mode_row, width=80, font=ctk.CTkFont(size=11),
            fg_color=BG_MAIN, border_color="#3A3550", text_color=TEXT_LIGHT,
            placeholder_text="all files",
        )
        filter_entry.pack(side="left")

        # ── Dynamic options panel ──────────────────────────────────────────
        opts = ctk.CTkFrame(parent, fg_color=BG_MAIN, corner_radius=8)
        opts.pack(fill="x", padx=16, pady=(0, 8))

        # Fields storage
        fields: dict = {}

        def _rebuild_opts(*_):
            for w in opts.winfo_children():
                w.destroy()
            fields.clear()
            m = mode_var.get()

            def _lbl(text):
                ctk.CTkLabel(opts, text=text, font=ctk.CTkFont(size=12), text_color=TEXT_LIGHT, anchor="w").pack(anchor="w", padx=12, pady=(8, 2))

            def _entry(key, placeholder=""):
                e = ctk.CTkEntry(opts, font=ctk.CTkFont(size=11),
                    fg_color=BG_CARD, border_color="#3A3550", text_color=TEXT_LIGHT,
                    placeholder_text=placeholder)
                e.pack(fill="x", padx=12, pady=(0, 6))
                fields[key] = e

            if m == "Prefix":
                _lbl("Prefix text")
                _entry("prefix", "e.g.  Project_")

            elif m == "Suffix":
                _lbl("Suffix text")
                _entry("suffix", "e.g.  _final")

            elif m == "Replace":
                _lbl("Find text")
                _entry("find", "e.g.  IMG")
                _lbl("Replace with")
                _entry("replace", "e.g.  Photo")

            elif m == "Sequential":
                _lbl("Base name")
                _entry("base", "e.g.  photo")
                row2 = ctk.CTkFrame(opts, fg_color="transparent")
                row2.pack(fill="x", padx=12, pady=(0, 6))
                ctk.CTkLabel(row2, text="Start #", font=ctk.CTkFont(size=11), text_color=TEXT_DIM).pack(side="left")
                e_start = ctk.CTkEntry(row2, width=60, font=ctk.CTkFont(size=11),
                    fg_color=BG_CARD, border_color="#3A3550", text_color=TEXT_LIGHT)
                e_start.insert(0, "1")
                e_start.pack(side="left", padx=(6, 16))
                ctk.CTkLabel(row2, text="Padding", font=ctk.CTkFont(size=11), text_color=TEXT_DIM).pack(side="left")
                e_pad = ctk.CTkEntry(row2, width=60, font=ctk.CTkFont(size=11),
                    fg_color=BG_CARD, border_color="#3A3550", text_color=TEXT_LIGHT)
                e_pad.insert(0, "3")
                e_pad.pack(side="left", padx=(6, 0))
                fields["start"] = e_start
                fields["padding"] = e_pad

        mode_var.trace_add("write", _rebuild_opts)
        _rebuild_opts()

        # ── Preview table ──────────────────────────────────────────────────
        ctk.CTkLabel(parent, text="Preview", font=ctk.CTkFont(size=12, weight="bold"),
            text_color=TEXT_WHITE, anchor="w").pack(anchor="w", padx=16, pady=(8, 4))

        preview_box = ctk.CTkScrollableFrame(parent, height=130, fg_color=BG_MAIN, corner_radius=8)
        preview_box.pack(fill="x", padx=16, pady=(0, 10))
        preview_box.grid_columnconfigure(0, weight=1)
        preview_box.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(preview_box, text="Original", font=ctk.CTkFont(size=11, weight="bold"),
            text_color=TEXT_MID, anchor="w").grid(row=0, column=0, sticky="w", padx=8)
        ctk.CTkLabel(preview_box, text="→  New Name", font=ctk.CTkFont(size=11, weight="bold"),
            text_color=TEXT_MID, anchor="w").grid(row=0, column=1, sticky="w", padx=8)

        preview_rows: list = []

        def _apply_to_automation():
            m = mode_var.get()
            automation.file_filter = filter_entry.get().strip()
            if m == "Prefix":
                automation.mode = RenameMode.PREFIX
                automation.prefix = fields.get("prefix", ctk.CTkEntry(parent)).get()
            elif m == "Suffix":
                automation.mode = RenameMode.SUFFIX
                automation.suffix = fields.get("suffix", ctk.CTkEntry(parent)).get()
            elif m == "Replace":
                automation.mode = RenameMode.REPLACE
                automation.find_text = fields.get("find", ctk.CTkEntry(parent)).get()
                automation.replace_text = fields.get("replace", ctk.CTkEntry(parent)).get()
            elif m == "Sequential":
                automation.mode = RenameMode.SEQUENTIAL
                automation.base_name = fields.get("base", ctk.CTkEntry(parent)).get() or "file"
                try:
                    automation.start_number = int(fields["start"].get())
                    automation.padding = int(fields["padding"].get())
                except (ValueError, KeyError):
                    pass

        def _preview():
            for w in preview_rows:
                w.destroy()
            preview_rows.clear()
            _apply_to_automation()
            previews = automation.preview()
            if not previews:
                lbl = ctk.CTkLabel(preview_box, text="No files found.", font=ctk.CTkFont(size=11), text_color=TEXT_DIM)
                lbl.grid(row=1, column=0, columnspan=2, pady=8)
                preview_rows.append(lbl)
                return
            for i, p in enumerate(previews[:20]):   # cap at 20 rows
                color = TEXT_LIGHT if p.changed else TEXT_DIM
                l1 = ctk.CTkLabel(preview_box, text=p.original.name, font=ctk.CTkFont(family="Consolas", size=10),
                    text_color=TEXT_DIM, anchor="w")
                l1.grid(row=i + 1, column=0, sticky="w", padx=8, pady=1)
                l2 = ctk.CTkLabel(preview_box, text=p.renamed.name, font=ctk.CTkFont(family="Consolas", size=10),
                    text_color=color, anchor="w")
                l2.grid(row=i + 1, column=1, sticky="w", padx=8, pady=1)
                preview_rows += [l1, l2]
            if len(previews) > 20:
                lbl = ctk.CTkLabel(preview_box,
                    text=f"… and {len(previews) - 20} more files",
                    font=ctk.CTkFont(size=10), text_color=TEXT_DIM)
                lbl.grid(row=21, column=0, columnspan=2, pady=4)
                preview_rows.append(lbl)

        ctk.CTkButton(
            parent, text="Preview", height=32, corner_radius=8,
            fg_color=BG_CARD2, hover_color="#252236", text_color=TEXT_LIGHT,
            font=ctk.CTkFont(size=12), command=_preview,
        ).pack(fill="x", padx=16, pady=(0, 6))

    # ── Actions ───────────────────────────────────────────────────────────────

    def _run_automation(self, name: str, automation) -> None:
        from utils.constants import STATUS_RUNNING
        if automation.status == STATUS_RUNNING:
            automation.cancel()
            self._run_btn.configure(text="▷  Run Now", fg_color=ACCENT)
            return

        automation.reset()
        self._run_btn.configure(text="◼  Stop", fg_color=RED)
        if hasattr(self, "_log_box"):
            self._log_box.configure(state="normal")
            self._log_box.delete("1.0", "end")
            self._log_box.configure(state="disabled")

        def _done_callback():
            entry = {
                "name": name,
                "icon": {"File Organizer": "📁", "System Flush": "🖥",
                         "Network Checker": "🌐", "Startup Manager": "🚀"}.get(name, "⚙"),
                "color": {"File Organizer": ACCENT, "System Flush": "#14B8A6",
                          "Network Checker": YELLOW, "Startup Manager": "#F97316"}.get(name, ACCENT),
                "detail": automation.log_lines[-1] if automation.log_lines else "",
                "time": datetime.now().strftime("%I:%M %p"),
                "status": automation.status,
            }
            self._activity_log.append(entry)
            self.after(0, lambda: self._run_btn.configure(text="▷  Run Now", fg_color=ACCENT))

        def _thread():
            automation.execute()
            _done_callback()

        threading.Thread(target=_thread, daemon=True).start()

    def _cb_log(self, message: str) -> None:
        if hasattr(self, "_log_box"):
            self.after(0, lambda m=message: self._append_log(m))

    def _append_log(self, message: str) -> None:
        self._log_box.configure(state="normal")
        self._log_box.insert("end", message + "\n")
        self._log_box.see("end")
        self._log_box.configure(state="disabled")

    def _cb_status_right(self, status: str) -> None:
        pass  # progress bar handles visual; status_lbl wired separately

    def _toggle_theme(self) -> None:
        current = settings.get("theme", "dark")
        new = "light" if current == "dark" else "dark"
        ctk.set_appearance_mode(new)
        settings.set("theme", new)

    def _browse_folder(self, automation) -> None:
        folder = filedialog.askdirectory(title="Select folder to organise")
        if folder:
            if hasattr(self, "_folder_entry"):
                self._folder_entry.delete(0, "end")
                self._folder_entry.insert(0, folder)
            settings.set("file_organizer.target_folder", folder)
            automation.target_folder = Path(folder)

    def _save_hosts(self) -> None:
        raw = self._hosts_entry.get()
        hosts = [h.strip() for h in raw.split(",") if h.strip()]
        settings.set("network_checker.hosts", hosts)