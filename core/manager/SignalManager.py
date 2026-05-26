# -*- coding: utf-8 -*-
"""
SignalManager — Orquestrador central de sinais do Aetheris ToolBox
"""

from __future__ import annotations

from PySide6.QtCore import QObject, Signal


class SignalManager(QObject):
    """
    Singleton que centraliza os sinais do sistema.

    Sinais:
        tool_opened(str)        — tool_key da ferramenta aberta
        tool_closed(str)        — tool_key da ferramenta fechada
        console_message(str)    — mensagem para exibir no console
        progress_update(float)  — valor de progresso (0.0 a 100.0)
    """

    tool_opened: Signal = Signal(str)
    tool_closed: Signal = Signal(str)
    console_message: Signal = Signal(str)
    progress_update: Signal = Signal(float)

    _instance: SignalManager | None = None

    def __new__(cls, parent: QObject | None = None) -> SignalManager:
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self, parent: QObject | None = None) -> None:
        if self._initialized:
            return
        self._initialized = True
        super().__init__(parent)
        SignalManager._instance = self

    @classmethod
    def instance(cls) -> SignalManager:
        if cls._instance is None:
            SignalManager()
        return cls._instance  # type: ignore[return-value]
