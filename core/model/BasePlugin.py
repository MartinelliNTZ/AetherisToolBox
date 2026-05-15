# -*- coding: utf-8 -*-
"""
BasePlugin — Classe base para todos os plugins do Aetheris ToolBox
====================================================================
Centraliza:
- Logger automático (via LogUtils) — self.logger
- Preferências carregadas do disco — self.preferences
- Métodos load_prefs() / save_prefs() — override nos filhos
- Emissão de tool_opened e tool_closed via SignalManager

Uso:
    from core.model.BasePlugin import BasePlugin

    class ConsoleTool(BasePlugin):
        def __init__(self, parent=None):
            super().__init__(tool_key="Console", parent=parent)
            self._build_ui()
            self.load_prefs()

        def load_prefs(self):
            texto = self.preferences.get("texto", "")

        def save_prefs(self):
            self.preferences["texto"] = self._edit.text()
"""

from __future__ import annotations

from typing import Any, Dict

from PySide6.QtWidgets import QWidget


class BasePlugin(QWidget):
    """
    Classe base para todos os plugins (ferramentas) do sistema.

    Ao ser instanciada, emite: SignalManager.tool_opened(tool_key, self)
    Ao ser fechada,   emite: SignalManager.tool_closed(tool_key)

    Atributos:
        self.logger          : LogUtils — instanciado no __init__
        self.preferences     : Dict[str, Any] — preferências carregadas do disco
        self.sys_preferences : Dict[str, Any] | None — preferências do sistema
        self.tool_key        : str — identificador único da ferramenta
    """

    def __init__(
        self,
        *,
        tool_key: str,
        parent: QWidget | None = None,
        sys_prefs: bool = False,
    ) -> None:
        super().__init__(parent)
        self.tool_key = tool_key

        from utils.Preferences import Preferences
        from core.enum.ToolKey import ToolKey

        self.preferences: Dict[str, Any] = Preferences.load_tool_prefs(tool_key)
        self.sys_preferences: Dict[str, Any] | None = None
        if sys_prefs:
            self.sys_preferences = Preferences.load_tool_prefs(ToolKey.SYSTEM)

        from core.config.LogUtils import LogUtils
        self.logger = LogUtils(tool=tool_key, class_name=self.__class__.__name__)

        from core.manager.SignalManager import SignalManager
        SignalManager.instance().tool_opened.emit(tool_key, self)

    def closeEvent(self, event) -> None:  # type: ignore[override]
        self.logger.info(
            "Ferramenta sendo fechada — persistindo preferências",
            code="TOOL_CLOSE_SAVE",
            tool_key=self.tool_key,
        )
        self.save_prefs()

        from utils.Preferences import Preferences
        from core.enum.ToolKey import ToolKey

        Preferences.save_tool_prefs(self.tool_key, self.preferences)

        self.logger.info(
            "Preferências persistidas ao fechar",
            code="TOOL_CLOSE_DONE",
            tool_key=self.tool_key,
        )
        from core.manager.SignalManager import SignalManager
        SignalManager.instance().tool_closed.emit(self.tool_key)
        super().closeEvent(event)

    # ── Preferences (override nos filhos) ────────────────────────────

    def load_prefs(self) -> None:
        """Carrega preferências e aplica nos widgets. Override no filho."""
        pass

    def save_prefs(self) -> None:
        """
        Lê widgets e atualiza self.preferences.
        O closeEvent persiste automaticamente com save_tool_prefs.
        """
        pass