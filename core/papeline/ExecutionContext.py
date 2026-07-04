# -*- coding: utf-8 -*-
"""
ExecutionContext — Shared state between pipeline steps
=========================================================
Container that allows steps to share data without direct coupling.
Also carries cancellation and error state.

Canonical attributes (direct access):
    input_path: str    — Input directory with files to process
    output_path: str   — Base directory where results will be saved
    files: list[str] | None — Specific file list (None = all in input_path)
    tool_key: str      — ToolKey for logging
"""

from __future__ import annotations

from typing import Any


class ExecutionContext:
    """
    Shared state container between all pipeline steps.

    Canonical attributes (direct access):
        input_path: str
        output_path: str
        files: list[str] | None
        tool_key: str

    Legacy methods (kept for compatibility):
        set(key, value) -> ExecutionContext  (fluent)
        get(key, default=None) -> Any
        has(key) -> bool
        add_error(exc) -> None
        get_errors() -> list[Exception]
        has_errors() -> bool
        cancel() -> None
        is_cancelled() -> bool
        clear() -> None
    """

    # ── Canonical attributes (direct access) ──────────────────────
    input_path: str = ""
    """Input directory with files to process."""

    output_path: str = ""
    """Base directory where results will be saved."""

    files: list[str] | None = None
    """Specific file list to process. None = all files in input_path."""

    tool_key: str = ""
    """ToolKey for logging."""

    def __init__(self, initial_data: dict = None):
        self._data: dict = initial_data.copy() if initial_data else {}
        self._errors: list[Exception] = []
        self._is_cancelled: bool = False



   
    def require(self, keys: list[str]) -> None:
        """Raises KeyError if any required key is missing."""
        missing = [k for k in keys if k not in self._data]
        if missing:
            raise KeyError(f"Required keys missing: {missing}")

    # ── Errors ────────────────────────────────────────────────────

    def add_error(self, exc: Exception) -> None:
        """Adds error to the error list."""
        self._errors.append(exc)

    def get_errors(self) -> list[Exception]:
        """Returns a copy of the error list."""
        return self._errors.copy()

    def has_errors(self) -> bool:
        """True if there were any errors."""
        return len(self._errors) > 0

    # ── Cancellation ──────────────────────────────────────────────

    def cancel(self) -> None:
        """Marks context as cancelled."""
        self._is_cancelled = True

    def is_cancelled(self) -> bool:
        """True if cancelled."""
        return self._is_cancelled

    # ── Reset ─────────────────────────────────────────────────────

    def clear(self) -> None:
        """Resets all state (data, errors, cancellation)."""
        self._data.clear()
        self._errors.clear()
        self._is_cancelled = False

    @property
    def data(self) -> dict:
        """Returns internal data dict (legacy compatibility)."""
        return self._data

    def __repr__(self) -> str:
        return (
            f"<ExecutionContext "
            f"data={len(self._data)} keys, "
            f"errors={len(self._errors)}, "
            f"cancelled={self._is_cancelled}, "
            f"input_path='{self.input_path}'>"
        )