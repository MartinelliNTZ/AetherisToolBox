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
    QSplitter, QProgressBar
)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QIcon

from core.model.Tool import Tool
from core.enum.CategoryTool import CategoryTool
from core.enum.ToolKey import ToolKey
from resources.widgets.app_bar import AppBar
from core.ui.CentralWorkspace import CentralWorkspace
from core.ui.SideWorkspace import SideWorkspace
from core.config.MenuManager import MenuManager
from utils.Preferences import Preferences


class MainWindow(QMainWindow):
    """
    Janela principal do Aetheris ToolBox.

    Layout:
      [AppBar]            -> titulo, toolbar com ToolGroups, controles de janela
      [Splitter]          -> CentralWorkspace | SideWorkspace
        [CentralWorkspace]  -> abas horizontais no topo (ferramentas CENTRAL)
        [SideWorkspace]     -> painel lateral direito expansivel (ferramentas SIDE)
      [Progress Bar]      -> barra global de progresso (rodape)
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

        # Preferencias do sistema (ToolKey.SYSTEM)
        self._sys_prefs = Preferences(section=ToolKey.SYSTEM.value)

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

        # === WORKSPACE: Central + Side com QSplitter ===
        self._splitter = QSplitter(Qt.Orientation.Horizontal)
        self._splitter.setHandleWidth(4)
        self._splitter.setChildrenCollapsible(False)
        self._splitter.setObjectName("workspace_splitter")

        self.central_workspace = CentralWorkspace()
        self._splitter.addWidget(self.central_workspace)

        self.side_workspace = SideWorkspace()
        self._splitter.addWidget(self.side_workspace)

        # Restaura largura salva do conteudo side
        saved = self._sys_prefs.get("side_content_width", SideWorkspace.W_DEFAULT)
        self._side_content_width = saved

        # Inicializa colapsado
        self.side_workspace.collapse()
        # Forca tamanho inicial no splitter (agendado pois width() ainda e 0)
        QTimer.singleShot(0, self._init_splitter_sizes)
        self._drag_lock = True  # nao salva enquanto colapsado

        # Conecta sinal de redimensionamento do SideWorkspace
        self.side_workspace.size_changed.connect(self._on_side_size_changed)

        # Sincroniza o splitter quando o usuario arrasta a handle
        self._splitter.splitterMoved.connect(self._on_splitter_moved)

        root_layout.addWidget(self._splitter, 1)

        # === REGISTRAR FERRAMENTAS ===
        for tool in tools:
            if tool.category == CategoryTool.SIDE:
                self.side_workspace.register_tool(tool)
            elif tool.category == CategoryTool.BOTH:
                self.side_workspace.register_tool(tool)
                self.central_workspace.register_tool(tool, focus=False)
            elif tool.name == "Home":
                self.central_workspace.register_tool(tool, focus=False)

        # === PROGRESS BAR ===
        self.progress = QProgressBar()
        self.progress.setValue(0)
        self.progress.setTextVisible(True)
        self.progress.setFormat(" %p% - aguardando... ")
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
        elif tool.category == CategoryTool.BOTH:
            self.side_workspace.open_tool(tool)
            self.central_workspace.open_tool(tool)
        else:
            self.central_workspace.open_tool(tool)

    # ------------------------------------------------------------------
    # Redimensionamento dos workspaces
    # ------------------------------------------------------------------

    def _init_splitter_sizes(self):
        """Forca o splitter para estado colapsado assim que a janela tiver tamanho."""
        try:
            self._splitter.setSizes([
                max(100, self._splitter.width() - SideWorkspace.W_TABS),
                SideWorkspace.W_TABS
            ])
        except Exception:
            pass

    def _on_side_size_changed(self, total_width: int):
        """Ajusta os tamanhos do splitter conforme SideWorkspace."""
        if total_width <= SideWorkspace.W_TABS:
            # Colapsado
            self._drag_lock = True
            self._splitter.setSizes([
                self._splitter.width() - SideWorkspace.W_TABS,
                SideWorkspace.W_TABS
            ])
            # Salva estado colapsado
            prefs = Preferences(section=ToolKey.SYSTEM.value)
            prefs.set("side_collapsed", True)
            prefs.set("side_content_width", self._side_content_width)
            prefs.save()
        else:
            # Expandido
            self._drag_lock = False
            self._splitter.setSizes([
                self._splitter.width() - total_width,
                total_width
            ])

    def _on_splitter_moved(self, pos: int, idx: int):
        """Salva a largura do conteudo side quando o usuario arrasta."""
        if self._drag_lock:
            return
        sizes = self._splitter.sizes()
        if len(sizes) >= 2:
            side_total = sizes[1]
            content_w = side_total - SideWorkspace.W_TABS
            if content_w > 20:
                self._side_content_width = content_w
                prefs = Preferences(section=ToolKey.SYSTEM.value)
                prefs.set("side_collapsed", False)
                prefs.set("side_content_width", content_w)
                prefs.save()

    # ------------------------------------------------------------------
    # Acesso as tools
    # ------------------------------------------------------------------

    def get_tool(self, name: str) -> Tool | None:
        return self._tool_map.get(name)

    def switch_to_tool(self, name: str) -> bool:
        if self.central_workspace.is_tool_open(name):
            self.central_workspace.set_current_tool(name)
            return True
        if self.side_workspace.is_tool_open(name):
            self.side_workspace.expand(name, self._side_content_width)
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