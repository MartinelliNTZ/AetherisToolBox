# -*- coding: utf-8 -*-
"""
BasePlugin — Classe base para todos os plugins do Aetheris ToolBox
====================================================================
Centraliza:
- Logger automatico (via LogUtils) — self.logger
- Metodos load_prefs() / save_prefs() — override nos filhos

Uso:
    from core.model.BasePlugin import BasePlugin

    class ConsoleTool(BasePlugin):
        def __init__(self, parent=None):
            super().__init__(tool_key="Console", parent=parent)
            self.load_prefs()
            self._build_ui()
            self.logger.info("ConsoleTool carregada", code="TOOL_READY")

        def load_prefs(self):
            ...

        def save_prefs(self):
            ...
"""

from __future__ import annotations

from typing import Any

from PySide6.QtWidgets import QWidget


class BasePlugin(QWidget):
    """
    Classe base para todos os plugins (ferramentas) do sistema.

    Atributos:
        self.logger   : LogUtils — instanciado no init
        self.tool_key : str — nome da ferramenta
    """

    def __init__(self, *, tool_key: str, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.tool_key = tool_key
        self.logger = None

        # Logger (import local para evitar circular)
        from core.config.LogUtils import LogUtils
        self.logger = LogUtils(tool=tool_key, class_name=self.__class__.__name__)

    # ── Preferences (override nos filhos) ────────────────────────────

    def load_prefs(self) -> None:
        """
        Carrega as preferencias da ferramenta e aplica nos widgets.
        Deve ser sobrescrito pelo plugin filho.
        """
        pass

    def save_prefs(self) -> None:
        """
        Le os valores atuais dos widgets e persiste no arquivo.
        Deve ser sobrescrito pelo plugin filho.
        """
        pass