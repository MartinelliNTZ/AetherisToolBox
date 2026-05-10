# -*- coding: utf-8 -*-
"""
UI Principal — Aetheris ToolBox
================================
MainWindow modular com AppBar, CentralWorkspace + SideWorkspace.

Tools de categoria CENTRAL vão para o CentralWorkspace (abas horizontais no topo).
Tools de categoria SIDE vão para o SideWorkspace (painel lateral direito expansível).

O SideWorkspace fica colado à direita do CentralWorkspace.
Quando expande/recolhe, o CentralWorkspace se ajusta automaticamente.
"""

from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Optional

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QProgressBar
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon

from core.model.Tool import Tool
from core.enum.CategoryTool import CategoryTool
from resources.widgets.app_bar import AppBar
from core.ui.CentralWorkspace import CentralWorkspace
from core.ui.SideWorkspace import SideWorkspace
from core.config.MenuManager import MenuManager


class MainWindow(QMainWindow):
    """
    Janela principal do Aetheris ToolBox.

    Layout:
      [AppBar]            → título, toolbar com ToolGroups, controles de janela
      [HBoxLayout]        → CentralWorkspace + SideWorkspace lado a lado
        [CentralWorkspace]  → abas horizontais no topo (ferramentas CENTRAL) ← ocupa espaço restante
        [SideWorkspace]     → painel lateral direito expansível (ferramentas SIDE) ← largura fixa
      [Progress Bar]      → barra global de progresso (rodapé)
    """

    def __init__(self, tools: List[Tool]):
        super().__init__()
        self.setWindowTitle("Aetheris ToolBox")
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Window)
        self.setMinimumSize(1000, 650)
        self.resize(1100, 700)

        icon_path = Path(__file__).parent.parent.parent / "Aetheris.png"
        if icon_path.exists():
            self.setWindowIcon(QIcon(str(icon_path)))

        self._tool_map: Dict[str, Tool] = {t.name: t for t in tools}
        self._build_ui(tools)

        self.central_workspace.set_current_tool("Home")

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

        # === TOOLBAR ===
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

        # === WORKSPACE: Central + Side lado a lado ===
        workspace_container = QWidget()
        workspace_layout = QHBoxLayout(workspace_container)
        workspace_layout.setContentsMargins(0, 0, 0, 0)
        workspace_layout.setSpacing(0)

        # CentralWorkspace (expande)
        self.central_workspace = CentralWorkspace()
        workspace_layout.addWidget(self.central_workspace, 1)

        # SideWorkspace (largura fixa, colado à direita)
        self.side_workspace = SideWorkspace()
        workspace_layout.addWidget(self.side_workspace, 0)

        root_layout.addWidget(workspace_container, 1)

        # === REGISTRAR FERRAMENTAS ===
        for tool in tools:
            if tool.category == CategoryTool.SIDE:
                self.side_workspace.register_tool(tool)
            elif tool.name == "Home":
                self.central_workspace.register_tool(tool, focus=False)

        # === PROGRESS BAR ===
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
        tool = self._tool_map.get(tool_name)
        if not tool:
            return

        if tool.category == CategoryTool.SIDE:
            self.side_workspace.open_tool(tool)
        else:
            self.central_workspace.open_tool(tool)

    # ------------------------------------------------------------------
    # Acesso às tools
    # ------------------------------------------------------------------

    def get_tool(self, name: str) -> Tool | None:
        return self._tool_map.get(name)

    def switch_to_tool(self, name: str) -> bool:
        if self.central_workspace.is_tool_open(name):
            self.central_workspace.set_current_tool(name)
            return True
        if self.side_workspace.is_tool_open(name):
            self.side_workspace.expand(name)
            return True
        return False

    def switch_to_console(self) -> None:
        self.switch_to_tool("Console")

    # ------------------------------------------------------------------
    # CONTROLE DE JANELA
    # ------------------------------------------------------------------

    def _toggle_maximize_restore(self) -> None:
        if self.isMaximized():
            self.showNormal()
        else:
            self.showMaximized()