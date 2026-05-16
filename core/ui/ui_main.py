# -*- coding: utf-8 -*-
"""
UI Principal — Aetheris ToolBox
================================
MainWindow modular com AppBar, MenuManager e WorkspaceManager.

A MainWindow POSICIONA os widgets prontos — a lógica de negócio
fica encapsulada nos managers (MenuManager, WorkspaceManager).
"""

from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Optional

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QProgressBar,
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon

from core.model.Tool import Tool
from resources.widgets.app_bar import AppBar
from core.config.MenuManager import MenuManager
from core.config.WorkspaceManager import WorkspaceManager
from core.dialogs.AboutDialog import AboutDialog


class MainWindow(QMainWindow):
    """
    Janela principal do Aetheris ToolBox.

    Layout:
      [AppBar]
      [MenuManager.menu_bar]
      [MenuManager.toolbar_widget]
      [WorkspaceManager]  ← splitter: CentralWorkspace | SideWorkspace
      [ProgressBar]

    Nenhuma lógica de workspace ou menu vive aqui.
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

        self._build_ui(tools)

    def _build_ui(self, tools: List[Tool]) -> None:
        from core.config.LogUtils import LogUtils

        logger = LogUtils(tool="System", class_name="MainWindow")
        logger.info("Construindo interface", code="UI_BUILD", num_tools=len(tools))

        root = QWidget()
        root_layout = QVBoxLayout(root)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)
        self.setCentralWidget(root)

        # ── 1. APPBAR ──
        self.appbar = AppBar()
        self.appbar.minimize_clicked.connect(self.showMinimized)
        self.appbar.maximize_restore_clicked.connect(self._toggle_maximize_restore)
        self.appbar.close_clicked.connect(self.close)
        root_layout.addWidget(self.appbar)

        # ── 2. MENU + TOOLBAR (encapsulado no MenuManager) ──
        self._menu_manager = MenuManager()
        self._menu_manager.build()
        self._menu_manager.tool_activated.connect(self._on_tool_activated)
        self._menu_manager.sair_clicked.connect(self.close)
        self._menu_manager.sobre_clicked.connect(self._show_about)
        root_layout.addWidget(self._menu_manager.menu_bar)
        root_layout.addWidget(self._menu_manager.toolbar_widget)

        # ── 3. WORKSPACE (encapsulado no WorkspaceManager) ──
        self._workspace_manager = WorkspaceManager(tools)
        root_layout.addWidget(self._workspace_manager, 1)

        # ── 4. PROGRESS BAR ──
        # Range 0-10000 = 2 casas decimais de precisão
        self.progress = QProgressBar()
        self.progress.setMinimum(0)
        self.progress.setMaximum(10000)
        self.progress.setValue(0)
        self.progress.setTextVisible(True)
        self.progress.setFormat(" %p% - aguardando... ")
        self.progress.setFixedHeight(20)
        root_layout.addWidget(self.progress)

        # Conecta sinal de progresso
        from core.manager.SignalManager import SignalManager
        SignalManager.instance().progress_update.connect(self._on_progress_update)

    # ────────────────────────────────────────────────────────────────
    # About Dialog
    # ────────────────────────────────────────────────────────────────

    def _show_about(self):
        dialog = AboutDialog(self)
        dialog.exec()

    # ────────────────────────────────────────────────────────────────
    # Ativação de ferramenta (via toolbar ou menu)
    # ────────────────────────────────────────────────────────────────

    def _on_tool_activated(self, tool_name: str):
        """Delega abertura de ferramenta ao WorkspaceManager."""
        self._workspace_manager.open_tool(tool_name)

    # ────────────────────────────────────────────────────────────────
    # Acesso público (compatibilidade com código existente)
    # ────────────────────────────────────────────────────────────────

    @property
    def central_workspace(self):
        return self._workspace_manager.central_workspace

    @property
    def side_workspace(self):
        return self._workspace_manager.side_workspace

    def get_tool(self, name: str) -> Optional[Tool]:
        return self._workspace_manager.get_tool(name)

    def switch_to_tool(self, name: str) -> bool:
        return self._workspace_manager.switch_to_tool(name)

    def switch_to_console(self) -> None:
        self._workspace_manager.switch_to_console()

    # ────────────────────────────────────────────────────────────────
    # Controle de janela
    # ────────────────────────────────────────────────────────────────

    def _on_progress_update(self, value: float):
        """Atualiza a barra de progresso com 2 casas decimais."""
        # value vem em 0-100, range é 0-10000 para 2 casas decimais
        scaled = int(round(value * 100.0))
        self.progress.setValue(scaled)
        if value <= 0:
            self.progress.setFormat(" %p% - aguardando... ")
        elif value >= 100:
            self.progress.setFormat(" 100% - concluído! ")
        else:
            self.progress.setFormat(f" {value:.2f}% - executando... ")

    def _toggle_maximize_restore(self) -> None:
        if self.isMaximized():
            self.showNormal()
        else:
            self.showMaximized()