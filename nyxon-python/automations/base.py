"""
Nyxon Automation Suite - Base Automation
Abstract base class for all automation modules.
"""

from abc import ABC, abstractmethod
from typing import Callable
from utils.logger import get_logger
from utils.constants import STATUS_IDLE, STATUS_RUNNING, STATUS_DONE, STATUS_ERROR, STATUS_CANCELLED

logger = get_logger(__name__)


class Automation(ABC):
    """
    Abstract base class every automation must inherit from.

    Subclasses implement:
        - run()    : the actual work, called inside a thread
        - cancel() : optional mid-run cancellation logic

    The base class manages status, progress, and callback wiring so
    the UI layer never has to touch thread internals.
    """

    def __init__(self, name: str, description: str) -> None:
        self.name = name
        self.description = description
        self.status: str = STATUS_IDLE
        self.progress: float = 0.0        # 0.0 – 1.0
        self.log_lines: list[str] = []
        self._cancelled: bool = False

        # Callbacks set by the UI
        self._on_progress: Callable[[float], None] | None = None
        self._on_log: Callable[[str], None] | None = None
        self._on_status: Callable[[str], None] | None = None

    # ── Public interface ──────────────────────────────────────────────────────

    def set_callbacks(
        self,
        on_progress: Callable[[float], None] | None = None,
        on_log: Callable[[str], None] | None = None,
        on_status: Callable[[str], None] | None = None,
    ) -> None:
        """Wire UI callbacks before calling execute()."""
        self._on_progress = on_progress
        self._on_log = on_log
        self._on_status = on_status

    def execute(self) -> None:
        """Entry point called by the thread. Wraps run() with lifecycle management."""
        self._cancelled = False
        self._set_status(STATUS_RUNNING)
        self._set_progress(0.0)
        logger.info("Starting automation: %s", self.name)
        try:
            self.run()
            if not self._cancelled:
                self._set_status(STATUS_DONE)
                self._set_progress(1.0)
                logger.info("Automation complete: %s", self.name)
        except Exception as exc:
            self._set_status(STATUS_ERROR)
            self._emit_log(f"Error: {exc}")
            logger.exception("Automation %s failed: %s", self.name, exc)

    def cancel(self) -> None:
        """Signal the automation to stop at its next checkpoint."""
        self._cancelled = True
        self._set_status(STATUS_CANCELLED)
        logger.info("Automation cancelled: %s", self.name)

    def reset(self) -> None:
        """Reset state so the automation can be run again."""
        self.status = STATUS_IDLE
        self.progress = 0.0
        self.log_lines.clear()
        self._cancelled = False

    # ── Abstract methods ──────────────────────────────────────────────────────

    @abstractmethod
    def run(self) -> None:
        """Perform the automation work. Must call _set_progress() periodically."""

    # ── Protected helpers ─────────────────────────────────────────────────────

    def _set_progress(self, value: float) -> None:
        self.progress = max(0.0, min(1.0, value))
        if self._on_progress:
            self._on_progress(self.progress)

    def _emit_log(self, message: str) -> None:
        self.log_lines.append(message)
        logger.debug("[%s] %s", self.name, message)
        if self._on_log:
            self._on_log(message)

    def _set_status(self, status: str) -> None:
        self.status = status
        if self._on_status:
            self._on_status(status)
