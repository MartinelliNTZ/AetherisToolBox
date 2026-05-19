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
        tool_opened(str, object)    — tool_key + instância da tool
        tool_closed(str)            — tool_key da ferramenta fechada
        console_message(str)        — mensagem para exibir no console
    """

    tool_opened: Signal = Signal(str)
    tool_closed: Signal = Signal(str)
    console_message: Signal = Signal(str)
    progress_update: Signal = Signal(float)

    _instance: SignalManager | None = None

    @classmethod
    def instance(cls) -> SignalManager:
        if cls._instance is None:
            SignalManager()
        return cls._instance  # type: ignore[return-value]

    def __init__(self, parent: QObject | None = None) -> None:
        if SignalManager._instance is not None:
            raise RuntimeError("SignalManager é singleton. Use SignalManager.instance()")
        super().__init__(parent)
        SignalManager._instance = self