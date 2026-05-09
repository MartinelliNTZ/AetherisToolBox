# -*- coding: utf-8 -*-
"""
UI Principal — Aetheris ToolBox
================================
MainWindow modular com AppBar, Workspace (QTabBar + QStackedWidget),
e ferramentas registradas via ToolRegistry.
"""

from __future__ import annotations

from pathlib import Path
from typing import Dict, List

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QProgressBar
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon

from core.model.Tool import Tool
from resources.widgets.app_bar import AppBar
from core.ui.workspace import Workspace


class MainWindow(QMainWindow):
    """
    Janela principal do Aetheris ToolBox.

    Layout:
      [AppBar]            → título, toolbar, controles de janela
      [Workspace]         → QTabBar + QStackedWidget (tools registradas)
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
        self.workspace.set_current_tool(0)

    def _build_ui(self, tools: List[Tool]) -> None:
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

        # === WORKSPACE ===
        self.workspace = Workspace()
        root_layout.addWidget(self.workspace, 1)

        # === REGISTRAR FERRAMENTAS NO WORKSPACE (objetos Tool) ===
        for tool in tools:
            self.workspace.register_tool(tool)

        # === PROGRESS BAR GLOBAL ===
        self.progress = QProgressBar()
        self.progress.setValue(0)
        self.progress.setTextVisible(True)
        self.progress.setFormat(" %p% — aguardando... ")
        self.progress.setFixedHeight(20)
        root_layout.addWidget(self.progress)

    # ------------------------------------------------------------------
    # Acesso às tools registradas
    # ------------------------------------------------------------------

    def get_tool(self, name: str) -> Tool | None:
        """Retorna o objeto Tool pelo nome."""
        return self._tool_map.get(name)

    def switch_to_tool(self, name: str) -> bool:
        """Muda para a aba de uma tool pelo nome."""
        for i, tool in enumerate(self.workspace._tools):
            if tool.name == name:
                self.workspace.set_current_tool(i)
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
