# -*- coding: utf-8 -*-
"""
UI Principal — Aetheris ToolBox
================================
MainWindow modular com AppBar, Workspace (QTabBar + QStackedWidget),
ClassificationTool e ConsoleTool como abas independentes.
"""

from __future__ import annotations

import sys
from pathlib import Path
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QProgressBar
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QIcon

from core.app_bar import AppBar
from core.workspace import Workspace
from core.classification_tool import ClassificationTool
from core.console_tool import ConsoleTool
from core.styles import AppStyles, Palette
from core.hud_loader import HudCircularRingsLoader
from core.main_controller import MainController


# ────────────────────────────────────────────────────────────────────────────
# Índices das abas (para referência)
# ────────────────────────────────────────────────────────────────────────────
TAB_CLASSIFIER = 0
TAB_CONSOLE    = 1


class MainWindow(QMainWindow):
    """
    Janela principal do Aetheris ToolBox.

    Layout:
      [AppBar]            → título, toolbar, controles de janela
      [Workspace]         → QTabBar + QStackedWidget
        ├── Classifier    → ClassificationTool
        └── Console       → ConsoleTool (compartilhado)
      [Progress Bar]      → barra global de progresso (rodapé)
    """

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Aetheris ToolBox")
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Window)
        self.setMinimumSize(1200, 800)

        icon_path = Path(__file__).parent / "Aetheris.png"
        if icon_path.exists():
            self.setWindowIcon(QIcon(str(icon_path)))

        self.resize(1400, 880)

        # --- Ferramentas ---
        self.classification_tool: ClassificationTool | None = None
        self.console_tool: ConsoleTool | None = None

        # --- Build UI ---
        self._build_ui()

        # --- Controller (deve vir DEPOIS da UI montada) ---
        self.controller: MainController | None = None
        self.loader_overlay: HudCircularRingsLoader | None = None

        # Connect signals
        self._connect_signals()

    def _build_ui(self):
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

        # === REGISTRAR FERRAMENTA DE CLASSIFICACAO ===
        self.classification_tool = ClassificationTool()
        self.workspace.register_tool(
            name="Classifier",
            widget=self.classification_tool,
            tooltip="Classificacao Raster com Redes Neurais"
        )

        # === REGISTRAR CONSOLE COMPARTILHADO ===
        self.console_tool = ConsoleTool()
        self.workspace.register_tool(
            name="Console",
            widget=self.console_tool,
            tooltip="Console de execucao compartilhado"
        )

        # === PROGRESS BAR GLOBAL ===
        self.progress = QProgressBar()
        self.progress.setValue(0)
        self.progress.setTextVisible(True)
        self.progress.setFormat(" %p% — aguardando... ")
        self.progress.setFixedHeight(20)
        root_layout.addWidget(self.progress)

    def _connect_signals(self):
        """Conecta sinais do Workspace a acoes globais."""
        self.workspace.current_tool_changed.connect(self._on_tool_changed)

    def _on_tool_changed(self, index: int, tool_widget):
        """Callback quando o usuario troca de aba."""
        pass  # Future: update appbar title, etc.

    def initialize_controller(self):
        """Inicializa o controller APOS a UI estar pronta."""
        self.controller = MainController(self)
        self.loader_overlay = HudCircularRingsLoader(self)
        self.loader_overlay.setGeometry(self.rect())

    # ────────────────────────────────────────────────────────────────────────
    # PROPRIEDADES DE DELEGACAO (compatibilidade com MainController)
    # O controller acessa self.view.btn_executar, self.view.spin_epochs,
    # self.view.txt_log, self.view.anchorClicked, etc.
    # ────────────────────────────────────────────────────────────────────────

    def __getattr__(self, name):
        """
        Redireciona acesso a atributos da UI:
        - Se for console/atributos de log → console_tool
        - Se for atributo de classificacao → classification_tool
        """
        # Atributos do console (compartilhado)
        if name in ("txt_log", "anchorClicked"):
            if self.__dict__.get("console_tool") is not None:
                tool = self.console_tool
                if name == "txt_log":
                    return tool.txt_log
                elif name == "anchorClicked":
                    return tool.anchorClicked
                return getattr(tool, name, None)

        # Atributos da ferramenta de classificacao
        if self.__dict__.get("classification_tool") is not None:
            tool = self.classification_tool
            if hasattr(tool, name):
                return getattr(tool, name)

        raise AttributeError(
            f"'{type(self).__name__}' object has no attribute '{name}'"
        )

    # ────────────────────────────────────────────────────────────────────────
    # CONTROLE DE JANELA
    # ────────────────────────────────────────────────────────────────────────

    def _toggle_maximize_restore(self):
        if self.isMaximized():
            self.showNormal()
        else:
            self.showMaximized()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if hasattr(self, "loader_overlay") and self.loader_overlay is not None:
            self.loader_overlay.setGeometry(self.rect())


# =============================================================================
# PONTO DE ENTRADA
# =============================================================================

def main():
    app = QApplication(sys.argv)
    app.setStyleSheet(AppStyles.global_stylesheet())

    font = QFont("Segoe UI", 10)
    font.setStyleHint(QFont.StyleHint.SansSerif)
    app.setFont(font)

    window = MainWindow()
    window.initialize_controller()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()