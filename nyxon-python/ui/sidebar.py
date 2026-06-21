"""
Nyxon Automation Suite - Sidebar
Categorised navigation with collapsible sections and scrollable automation list.
To add a new automation: add it to AUTOMATION_REGISTRY with its category.
"""

import platform
import customtkinter as ctk
from typing import Callable

_EMOJI = "Segoe UI Emoji" if platform.system() == "Windows" else "Segoe UI"


# ── Registry — add every automation here ─────────────────────────────────────
# Format: (icon, name, category)
# Categories: "File Tools" | "System Tools" | "Network" | "Other"

AUTOMATION_REGISTRY: list[tuple[str, str, str]] = [
    ("📁", "File Organizer",  "File Tools"),
    ("✏️", "Bulk Rename",     "File Tools"),
    ("🖥",  "System Flush",   "System Tools"),
    ("🚀", "Startup Manager", "System Tools"),
    ("💾", "Disk Analyser",   "System Tools"),
    ("🧹", "DNS Cleaner", "Network"),
]

CATEGORY_ICONS = {
    "File Tools":   "📂",
    "System Tools": "⚙️",
    "Network":      "🌐",
    "Other":        "🔧",
}

SIDEBAR_BG  = "#13111F"
ACTIVE_BG   = "#3B37A0"
HOVER_BG    = "#1E1B2E"
CAT_COLOR   = "#6B6880"
TEXT_COLOR  = "#C4C2D4"
ACTIVE_TEXT = "#FFFFFF"
ACCENT      = "#7B5CF0"
SEP_COLOR   = "#2A2640"


class Sidebar(ctk.CTkFrame):

    def __init__(self, parent, on_navigate: Callable[[str], None], **kwargs) -> None:
        super().__init__(parent, width=230, corner_radius=0, fg_color=SIDEBAR_BG, **kwargs)
        self.grid_propagate(False)
        self._on_navigate = on_navigate
        self._active = "Dashboard"
        self._buttons: dict[str, ctk.CTkButton] = {}
        self._collapsed: dict[str, bool] = {}
        self._cat_frames: dict[str, ctk.CTkFrame] = {}
        self._build()

    def _build(self) -> None:
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # Logo
        logo = ctk.CTkFrame(self, fg_color="transparent", height=72)
        logo.grid(row=0, column=0, sticky="ew", padx=18, pady=(18, 8))
        logo.grid_propagate(False)
        ctk.CTkLabel(logo, text="✕ NYXON",
            font=ctk.CTkFont(family="Segoe UI", size=18, weight="bold"),
            text_color=ACTIVE_TEXT, anchor="w").pack(anchor="w")
        ctk.CTkLabel(logo, text="AUTOMATION SUITE",
            font=ctk.CTkFont(size=9, weight="bold"),
            text_color=ACCENT, anchor="w").pack(anchor="w")

        # Scrollable nav
        scroll = ctk.CTkScrollableFrame(
            self, fg_color="transparent", corner_radius=0,
            scrollbar_button_color=SIDEBAR_BG,
            scrollbar_button_hover_color=HOVER_BG,
        )
        scroll.grid(row=1, column=0, sticky="nsew")
        scroll.grid_columnconfigure(0, weight=1)

        self._nav_btn(scroll, "🏠", "Dashboard")
        self._separator(scroll)

        categories: dict[str, list] = {}
        for icon, name, cat in AUTOMATION_REGISTRY:
            categories.setdefault(cat, []).append((icon, name))
        for cat, items in categories.items():
            self._category_section(scroll, cat, items)

        self._separator(scroll)
        self._nav_btn(scroll, "⚙", "Settings")

        # Footer
        footer = ctk.CTkFrame(self, fg_color="#0E0C1A", corner_radius=10)
        footer.grid(row=2, column=0, sticky="ew", padx=10, pady=(4, 10))
        ctk.CTkLabel(footer, text="N", width=34, height=34, corner_radius=17,
            fg_color=ACCENT, font=ctk.CTkFont(size=14, weight="bold"),
            text_color="white").grid(row=0, column=0, padx=(10, 8), pady=10)
        info = ctk.CTkFrame(footer, fg_color="transparent")
        info.grid(row=0, column=1, sticky="w")
        ctk.CTkLabel(info, text="Nyxon User",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=ACTIVE_TEXT, anchor="w").pack(anchor="w")
        ctk.CTkLabel(info, text="Pro",
            font=ctk.CTkFont(size=9, weight="bold"),
            text_color=ACCENT, fg_color="#1E1B2E",
            corner_radius=4, width=28, anchor="center").pack(anchor="w")

    def _nav_btn(self, parent, icon: str, label: str) -> None:
        is_active = label == self._active
        btn = ctk.CTkButton(
            parent,
            text=f"  {icon}  {label}",
            anchor="w", height=38, corner_radius=8, border_spacing=6,
            fg_color=ACTIVE_BG if is_active else "transparent",
            hover_color=HOVER_BG,
            text_color=ACTIVE_TEXT if is_active else TEXT_COLOR,
            font=ctk.CTkFont(size=13),
            command=lambda l=label: self._on_click(l),
        )
        btn.pack(fill="x", padx=10, pady=2)
        self._buttons[label] = btn

    def _category_section(self, parent, category: str, items: list) -> None:
        self._collapsed[category] = False
        cat_icon = CATEGORY_ICONS.get(category, "🔧")

        header = ctk.CTkButton(
            parent,
            text=f"  {cat_icon}  {category}   ▾",
            anchor="w", height=32, corner_radius=6, border_spacing=4,
            fg_color="transparent", hover_color=HOVER_BG,
            text_color=CAT_COLOR,
            font=ctk.CTkFont(size=11, weight="bold"),
            command=lambda c=category: self._toggle_category(c),
        )
        header.pack(fill="x", padx=10, pady=(8, 2))
        self._buttons[f"__cat_{category}"] = header

        items_frame = ctk.CTkFrame(parent, fg_color="transparent")
        items_frame.pack(fill="x")
        self._cat_frames[category] = items_frame

        for icon, name in items:
            btn = ctk.CTkButton(
                items_frame,
                text=f"      {icon}  {name}",
                anchor="w", height=36, corner_radius=8, border_spacing=4,
                fg_color=ACTIVE_BG if name == self._active else "transparent",
                hover_color=HOVER_BG,
                text_color=ACTIVE_TEXT if name == self._active else TEXT_COLOR,
                font=ctk.CTkFont(size=12),
                command=lambda l=name: self._on_click(l),
            )
            btn.pack(fill="x", padx=10, pady=1)
            self._buttons[name] = btn

    def _separator(self, parent) -> None:
        ctk.CTkFrame(parent, height=1, fg_color=SEP_COLOR).pack(
            fill="x", padx=14, pady=6
        )

    def _toggle_category(self, category: str) -> None:
        self._collapsed[category] = not self._collapsed[category]
        frame = self._cat_frames[category]
        header = self._buttons[f"__cat_{category}"]
        cat_icon = CATEGORY_ICONS.get(category, "🔧")

        if self._collapsed[category]:
            frame.pack_forget()
            header.configure(text=f"  {cat_icon}  {category}   ▸")
        else:
            frame.pack(fill="x", after=header)
            header.configure(text=f"  {cat_icon}  {category}   ▾")

    def _on_click(self, label: str) -> None:
        if self._active in self._buttons:
            self._buttons[self._active].configure(
                fg_color="transparent", text_color=TEXT_COLOR
            )
        self._active = label
        if label in self._buttons:
            self._buttons[label].configure(fg_color=ACTIVE_BG, text_color=ACTIVE_TEXT)
        self._on_navigate(label)

    def set_active(self, label: str) -> None:
        self._on_click(label)