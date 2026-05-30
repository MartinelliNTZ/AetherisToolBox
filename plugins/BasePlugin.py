# -*- coding: utf-8 -*-
"""
BasePlugin — Classe base para todos os plugins do Aetheris ToolBox
====================================================================
Centraliza:
- Logger automático (via LogUtils) — self.logger
- Preferências carregadas do disco — self.preferences
- Métodos load_prefs() / save_prefs() — override nos filhos
- Emissão de tool_opened e tool_closed via SignalManager
- _build_ui() chamado automaticamente no __init__
- load_prefs() chamado automaticamente no __init__

Uso:
    from core.model.BasePlugin import BasePlugin

    class ConsoleTool(BasePlugin):
        def __init__(self, parent=None):
            super().__init__(tool_key="Console", parent=parent)

        def _build_ui(self):
            super()._build_ui()
            self.main_layout.addWidget(...)

        def load_prefs(self):
            texto = self.preferences.get("texto", "")

        def save_prefs(self):
            self.preferences["texto"] = self._edit.text()
"""

from __future__ import annotations

from typing import Any, Dict

from PySide6.QtWidgets import QWidget, QVBoxLayout

from core.config.LogUtils import LogUtils
from core.enum.ToolKey import ToolKey
from core.manager.SignalManager import SignalManager
from resources.widgets.PluginPage import PluginPage
from utils.Preferences import Preferences


class BasePlugin(QWidget):
    """
    Classe base para todos os plugins (ferramentas) do sistema.

    Ao ser instanciada:
        - Cria PluginPage com título opcional (self.page, self.main_layout)
        - Chama self._build_ui() — override no filho com super()
        - Chama self.load_prefs() — override no filho opcional
        - Emite SignalManager.tool_opened(tool_key, self)

    Atributos:
        self.logger          : LogUtils
        self.preferences     : Dict[str, Any]
        self.sys_preferences : Dict[str, Any] | None
        self.tool_key        : str
        self.main_layout     : QVBoxLayout — layout do PluginPage para addWidget
    """

    def __init__(
        self,
        *,
        tool_key: str,
        parent: QWidget | None = None,
        sys_prefs: bool = False,
        title: str | None = None,
        show_project_path: bool = False,
    ) -> None:
        self._show_project_path = show_project_path
        super().__init__(parent)
        self.tool_key = tool_key
        self._title = title

        self.preferences: Dict[str,
                               Any] = Preferences.load_tool_prefs(tool_key)
        self.sys_preferences: Dict[str, Any] | None = None
        if sys_prefs:
            self.sys_preferences = Preferences.load_tool_prefs(ToolKey.SYSTEM)

        self.logger = LogUtils(
            tool=tool_key, class_name=self.__class__.__name__)

        self._build_ui()
        self.load_prefs()

        SignalManager.instance().tool_opened.emit(tool_key)

    def _build_ui(self) -> None:
        """
        Constrói a UI base do plugin.

        Cria um QVBoxLayout externo (margins 0) com um PluginPage inside.
        self.main_layout = PluginPage.main_layout (margins 18,10,18,10 / spacing 8).

        Os filhos DEVEM chamar super()._build_ui() antes de adicionar
        widgets em self.main_layout.
        """
        # Layout externo sem margins para ancorar a PluginPage
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        self.page = PluginPage(self, title=self._title)
        self.main_layout = self.page.main_layout
        outer.addWidget(self.page)

        # Exibe caminho do projeto no header se solicitado
        if self._show_project_path:
            try:
                root = self.sys_preferences.get("root_folder", "") if self.sys_preferences else ""
                if root:
                    self.page.set_project_path(root)
            except Exception as e:
                self.logger.warning("Não foi possível exibir caminho do projeto", code="SHOW_PATH_ERR", error=str(e))

    def closeEvent(self, event) -> None:  # type: ignore[override]
        self.logger.info(
            "Ferramenta sendo fechada — persistindo preferências",
            code="TOOL_CLOSE_SAVE",
            tool_key=self.tool_key,
        )
        self.save_prefs()
        self.force_save_prefs()
        self.logger.info(
            "Preferências persistidas ao fechar",
            code="TOOL_CLOSE_DONE",
            tool_key=self.tool_key,
        )
        SignalManager.instance().tool_closed.emit(self.tool_key)
        super().closeEvent(event)

    def force_save_prefs(self, toolkey=None) -> None:
        """
        Força a persistência imediata das preferências atuais.
        
        ATENÇÃO: Salva no tool_key ou no toolkey passado.
        Se o plugin usa sys_prefs=True, as system preferences (tema, etc.)
        NÃO são salvas aqui. Use:
            Preferences.save_tool_prefs(ToolKey.SYSTEM, self.sys_preferences)
        """
        if toolkey is None:
            toolkey = self.tool_key
        self.logger.info(
            "Forçando salvamento de preferências",
            code="TOOL_FORCE_SAVE",
            tool_key=self.tool_key,
        )
        Preferences.save_tool_prefs(self.tool_key, self.preferences)
        self.logger.info(
            "Preferências forçadas a salvar",
            code="TOOL_FORCE_SAVE_DONE",
            tool_key=toolkey,
        )

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