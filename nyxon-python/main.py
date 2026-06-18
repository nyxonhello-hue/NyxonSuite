"""
Nyxon Automation Suite
Entry point — run this file to launch the application.

    python main.py

To build the Windows executable:
    pyinstaller --onedir --windowed --icon=assets/icon.ico --name="NyxonSuite" main.py
"""

import sys
from pathlib import Path

# Make sure project root is on sys.path when run directly
sys.path.insert(0, str(Path(__file__).parent))

from utils.logger import get_logger
from utils.constants import APP_NAME, __version__

logger = get_logger("main")


def main() -> None:
    logger.info("Starting %s v%s", APP_NAME, __version__)

    # customtkinter import deferred so logging is ready first
    import customtkinter as ctk
    from ui.app import NyxonApp

    app = NyxonApp()
    app.mainloop()

    logger.info("Application closed.")


if __name__ == "__main__":
    main()
