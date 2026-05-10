# -*- coding: utf-8 -*-
"""
UI Principal — Aetheris ToolBox
================================
MainWindow modular com AppBar, CentralWorkspace (QTabBar + QStackedWidget),
SideWorkspace (painel lateral direito) e ferramentas registradas via ToolRegistry.

Tools de categoria CENTRAL vão para o CentralWorkspace (abas horizontais no topo).
Tools de categoria SIDE vão para o SideWorkspace (painel lateral direito expansível).
"""

from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Optional

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QProgressBar, QSplitter
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
      [QSplitter]         → separa CentralWorkspace (esquerda) do SideWorkspace (direita)
        [CentralWorkspace]  → abas horizontais no topo (ferramentas CENTRAL)
        [SideWorkspace]     → painel lateral direito expansível (ferramentas SIDE)
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

        # === SPLITTER: CentralWorkspace + SideWorkspace ===
        self.splitter = QSplitter(Qt.Orientation.Horizontal)
        self.splitter.setObjectName("main_splitter")
        self.splitter.setHandleWidth(4)

        # CentralWorkspace (ferramentas CENTRAL)
        self.central_workspace = CentralWorkspace()
        self.splitter.addWidget(self.central_workspace)

        # SideWorkspace (ferramentas SIDE)
        self.side_workspace = SideWorkspace()
        self.splitter.addWidget(self.side_workspace)

        # Define proporção inicial: central toma todo o espaço, side começa colapsado
        self.splitter.setStretchFactor(0, 1)  # central workspace expande
        self.splitter.setStretchFactor(1, 0)  # side workspace não expande
        self.splitter.setSizes([800, 40])     # side começa colapsado

        root_layout.addWidget(self.splitter, 1)

        # === REGISTRAR FERRAMENTAS NO WORKSPACE ===
        # CENTRAL: Home registrada por padrão (sem focar)
        # SIDE: Console registrada por padrão no SideWorkspace
        for tool in tools:
            if tool.category == CategoryTool.SIDE:
                self.side_workspace.register_tool(tool)
            elif tool.name == "Home":
                self.central_workspace.register_tool(tool, focus=False)

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
        """Quando um botão do ToolGroup é clicado, abre ou foca a tool
        no workspace apropriado conforme sua categoria."""
        tool = self._tool_map.get(tool_name)
        if not tool:
            return

        if tool.category == CategoryTool.SIDE:
            self.side_workspace.open_tool(tool)
        else:
            self.central_workspace.open_tool(tool)

    # ------------------------------------------------------------------
    # Acesso às tools registradas
    # ------------------------------------------------------------------

    def get_tool(self, name: str) -> Tool | None:
        """Retorna o objeto Tool pelo nome."""
        return self._tool_map.get(name)

    def switch_to_tool(self, name: str) -> bool:
        """Muda para uma tool. Procura primeiro no Central, depois no Side."""
        if self.central_workspace.is_tool_open(name):
            self.central_workspace.set_current_tool(name)
            return True
        if self.side_workspace.is_tool_open(name):
            self.side_workspace.expand(name)
            return True
        return False

    def switch_to_console(self) -> None:
        """Muda para o Console (SideWorkspace)."""
        self.switch_to_tool("Console")

    # ------------------------------------------------------------------
    # CONTROLE DE JANELA
    # ------------------------------------------------------------------

    def _toggle_maximize_restore(self) -> None:
        if self.isMaximized():
            self.showNormal()
        else:
            self.showMaximized()