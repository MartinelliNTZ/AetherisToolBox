# -*- coding: utf-8 -*-
"""
UI Principal — Aetheris ToolBox
================================
MainWindow modular com AppBar, Workspace (QTabBar + QStackedWidget),
e ferramentas registradas via ToolRegistry.
"""

from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Optional

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QProgressBar, QHBoxLayout
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon

from core.model.Tool import Tool
from resources.widgets.app_bar import AppBar
from core.ui.CentralWorkspace import CentralWorkspace
from core.config.MenuManager import MenuManager


class MainWindow(QMainWindow):
    """
    Janela principal do Aetheris ToolBox.

    Layout:
      [AppBar]            → título, toolbar com ToolGroups, controles de janela
      [Workspace]         → área de trabalho com as ferramentas
      [Progress Bar]      → barra global de progresso (rodapé)
    """

    def __init__(self, tools: List[Tool]):
        """
        Parametros:
            tools: Lista de objetos Tool vindos do ToolRegistry.get_all()
        """
        super().__init__()
        self.setWindowTitle("Aetheris ToolBox")
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Window)
        self.setMinimumSize(1000, 650)
        self.resize(1100, 700)

        icon_path = Path(__file__).parent.parent.parent / "Aetheris.png"
        if icon_path.exists():
            self.setWindowIcon(QIcon(str(icon_path)))

        # Guarda referencias das tools (nome -> Tool)
        self._tool_map: Dict[str, Tool] = {t.name: t for t in tools}

        # --- Build UI ---
        self._build_ui(tools)

        # Seleciona a primeira aba (Home) por padrao
        self.workspace.set_current_tool("Home")

    def _build_ui(self, tools: List[Tool]) -> None:
        from core.config.LogUtils import LogUtils

        logger = LogUtils(tool="System", class_name="MainWindow")
        logger.info("Construindo interface", code="UI_BUILD", num_tools=len(tools))

        root = QWidget()
        root_layout = QVBoxLayout(root)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)
        self.setCentralWidget(root)

        # === APPBAR ===
        self.appbar = AppBar()
        self.appbar.minimize_clicked.connect(self.showMinimized)
        self.appbar.maximize_restore_clicked.connect(self._toggle_maximize_restore)
        self.appbar.close_clicked.connect(self.close)
        root_layout.addWidget(self.appbar)

        # === TOOLBAR (grupos de ferramentas) ===
        self._menu_manager = MenuManager()
        self._menu_manager.tool_activated.connect(self._on_tool_activated)
        groups = self._menu_manager.build()

        if groups:
            toolbar_container = QWidget()
            toolbar_container.setObjectName("toolbar_panel")
            toolbar_container.setStyleSheet("""
                QWidget#toolbar_panel {
                    background-color: #0A0A0D;
                    border-bottom: 1px solid #1A1A20;
                }
            """)
            toolbar_layout = QHBoxLayout(toolbar_container)
            toolbar_layout.setContentsMargins(4, 2, 4, 2)
            toolbar_layout.setSpacing(0)
            for group in groups:
                toolbar_layout.addWidget(group)
            toolbar_layout.addStretch()
            root_layout.addWidget(toolbar_container)

        # === WORKSPACE ===
        self.workspace = CentralWorkspace()
        root_layout.addWidget(self.workspace, 1)

        # === REGISTRAR FERRAMENTAS NO WORKSPACE ===
        # Apenas Home é registrada por padrão (sem focar, pois o set_current_tool já foca).
        # As demais são abertas sob demanda via toolbar (open_tool).
        for tool in tools:
            if tool.name == "Home":
                self.workspace.register_tool(tool, focus=False)
                break

        # === PROGRESS BAR GLOBAL ===
        self.progress = QProgressBar()
        self.progress.setValue(0)
        self.progress.setTextVisible(True)
        self.progress.setFormat(" %p% — aguardando... ")
        self.progress.setFixedHeight(20)
        root_layout.addWidget(self.progress)

    # ------------------------------------------------------------------
    # MenuManager callback
    # ------------------------------------------------------------------

    def _on_tool_activated(self, tool_name: str):
        """Quando um botão do ToolGroup é clicado, abre ou foca a tool."""
        tool = self._tool_map.get(tool_name)
        if tool:
            self.workspace.open_tool(tool)

    # ------------------------------------------------------------------
    # Acesso às tools registradas
    # ------------------------------------------------------------------

    def get_tool(self, name: str) -> Tool | None:
        """Retorna o objeto Tool pelo nome."""
        return self._tool_map.get(name)

    def switch_to_tool(self, name: str) -> bool:
        """Muda para a aba de uma tool pelo nome."""
        if self.workspace.is_tool_open(name):
            self.workspace.set_current_tool(name)
            return True
        return False

    def switch_to_console(self) -> None:
        """Muda para a aba Console."""
        self.switch_to_tool("Console")

    # ------------------------------------------------------------------
    # CONTROLE DE JANELA
    # ------------------------------------------------------------------

    def _toggle_maximize_restore(self) -> None:
        if self.isMaximized():
            self.showNormal()
        else:
            self.showMaximized()
