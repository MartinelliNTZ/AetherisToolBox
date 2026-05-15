# -*- coding: utf-8 -*-
"""
BasePlugin — Classe base para todos os plugins do Aetheris ToolBox
====================================================================
Centraliza:
- Logger automático (via LogUtils) — self.logger
- Gerenciamento de preferências (via Preferences) — self.preferences
- Métodos load_prefs() / save_prefs() — override nos filhos
- Emissão de tool_opened e tool_closed via SignalManager

Uso:
    from core.model.BasePlugin import BasePlugin

    class ConsoleTool(BasePlugin):
        def __init__(self, parent=None):
            super().__init__(tool_key="Console", parent=parent)
            self.load_prefs()
            self._build_ui()

        def load_prefs(self):
            ...

        def save_prefs(self):
            ...
"""

from __future__ import annotations

from PySide6.QtWidgets import QWidget


class BasePlugin(QWidget):
    """
    Classe base para todos os plugins (ferramentas) do sistema.

    Ao ser instanciada, emite: SignalManager.tool_opened(tool_key, self)
    Ao ser fechada,   emite: SignalManager.tool_closed(tool_key)

    Atributos:
        self.logger         : LogUtils — instanciado no __init__
        self.preferences    : Preferences — gerenciador de prefs da tool
        self.sys_preferences: Preferences | None — gerenciador de prefs do sistema
                              (só disponível se sys_prefs=True no __init__)
        self.tool_key       : str — identificador único da ferramenta
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

        from core.config.LogUtils import LogUtils
        self.logger = LogUtils(tool=tool_key, class_name=self.__class__.__name__)

        from core.enum.ToolKey import ToolKey
        from utils.Preferences import Preferences
        self.preferences = Preferences(section=tool_key)
        self.sys_preferences: "Preferences | None" = None
        if sys_prefs:
            self.sys_preferences = Preferences(section=ToolKey.SYSTEM.value)

        from core.manager.SignalManager import SignalManager
        SignalManager.instance().tool_opened.emit(tool_key, self)

    def closeEvent(self, event) -> None:  # type: ignore[override]
        self.logger.info(
            "Ferramenta sendo fechada — persistindo preferências",
            code="TOOL_CLOSE_SAVE",
            tool_key=self.tool_key,
        )
        self.save_prefs()
        # Persiste as preferências em disco (o child pode ter feito set())
        self.preferences.save()
        if self.sys_preferences is not None:
            self.sys_preferences.save()
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
        """Lê widgets e persiste preferências. Override no filho."""
        pass