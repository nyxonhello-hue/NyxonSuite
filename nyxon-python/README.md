# ⚡ Nyxon Automation Suite

A desktop automation toolkit for Windows, built with Python and CustomTkinter.

**By Nyxon Technologies** · v1.0.0

---

## Features

| Automation | What it does |
|---|---|
| **File Organizer** | Sorts files in any folder into subfolders by type (Images, Videos, Documents…) |
| **System Flush** | Clears Windows Temp folders and optionally empties the Recycle Bin |
| **Network Checker** | Pings a list of hosts, reports DNS resolution time and TCP/ICMP latency |
| **Startup Manager** | Lists all Windows startup programs; enable or disable them without deleting |

---

## Architecture

```
nyxon-python/
├── main.py                  # Entry point
├── requirements.txt
├── README.md
├── assets/
│   └── icon.ico
│
├── ui/                      # Presentation layer
│   ├── app.py               # Root CTk window, CTkTabview layout
│   ├── card.py              # Reusable AutomationCard widget
│   └── startup_panel.py     # Extended panel for StartupManager
│
├── automations/             # Business logic layer
│   ├── base.py              # Abstract Automation base class
│   ├── file_organizer.py
│   ├── system_flush.py
│   ├── net_checker.py
│   └── startup_manager.py
│
└── utils/                   # Infrastructure
    ├── constants.py          # App-wide constants (no magic numbers)
    ├── logger.py             # Centralised logging (file + console)
    └── settings.py           # JSON config with dot-path access
```

### Component diagram

```
┌─────────────────────────────────────────────────────────┐
│                      NyxonApp (CTk)                     │
│  ┌───────────────────────────────────────────────────┐  │
│  │              CTkTabview (4 tabs)                  │  │
│  │  ┌────────────────┐  ┌────────────────────────┐  │  │
│  │  │ AutomationCard │  │    StartupPanel        │  │  │
│  │  │ ┌────────────┐ │  │  CTkScrollableFrame    │  │  │
│  │  │ │ CTkProgress│ │  │  (one row per entry)   │  │  │
│  │  │ │ CTkTextbox │ │  └────────────────────────┘  │  │
│  │  │ └────────────┘ │                               │  │
│  │  └────────┬───────┘                               │  │
│  └───────────┼───────────────────────────────────────┘  │
└──────────────┼──────────────────────────────────────────┘
               │  threading.Thread
               ▼
┌──────────────────────────────┐
│     Automation (ABC)         │
│  execute() → run() [thread]  │
│  cancel()  reset()           │
│  _set_progress()  _emit_log()│
├──────────────┬───────────────┤
│ FileOrganizer│ SystemFlush   │
│ NetworkCheck │ StartupManager│
└──────────────┴───────────────┘
               │
               ▼
┌──────────────────────────────┐
│           Utils              │
│  Settings (config.json)      │
│  Logger   (~/nyxon/logs/)    │
│  Constants                   │
└──────────────────────────────┘
```

---

## Getting Started

### Prerequisites

- Python 3.11+
- Windows 10 / 11

### Install dependencies

```bash
pip install -r requirements.txt
```

### Run

```bash
python main.py
```

### Run tests

```bash
pytest tests/ -v
```

---

## Building the .exe

```bash
pyinstaller --onedir --windowed --icon=assets/icon.ico --name="NyxonSuite" main.py
```

> **Note:** `--onedir` is preferred over `--onefile` for faster startup. Distribute the entire `dist/NyxonSuite/` folder, not just the `.exe`.

Test the build on a clean Windows machine before submission.

---

## Configuration

Settings are stored at `%USERPROFILE%\.nyxon\config.json` and are created automatically on first run. You can edit them manually or through the UI.

Logs are written to `%USERPROFILE%\.nyxon\logs\nyxon_YYYYMMDD.log`.

---

## Design Decisions

- **Separation of concerns** — UI, automation logic, and utilities are in separate packages with no cross-layer imports going the wrong direction.
- **Abstract base class** — `Automation` enforces a consistent `run()` / `cancel()` / `reset()` contract so every module is interchangeable from the UI's perspective.
- **Thread safety** — All automation work runs in daemon threads; UI updates use `after(0, callback)` so CustomTkinter's main loop is never blocked.
- **No magic numbers** — All thresholds, paths, and string literals live in `utils/constants.py` or `config.json`.
- **Graceful cancellation** — Every automation checks `self._cancelled` at loop checkpoints rather than forcing thread termination.

---

*Nyxon Technologies · Built in Ghana 🇬🇭*
