# -*- coding: utf-8 -*-
"""
UI Principal — Aetheris ToolBox
================================
MainWindow modular com AppBar, Workspace e Ferramentas.
A ferramenta de classificacao (ClassificationTool) e registrada
no workspace como o principal modulo do sistema.
"""

from __future__ import annotations

import sys
from pathlib import Path
from PySide6.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QIcon

from core.app_bar import AppBar
from core.workspace import Workspace
from core.classification_tool import ClassificationTool
from core.styles import AppStyles, Palette
from core.hud_loader import HudCircularRingsLoader
from core.main_controller import MainController


class MainWindow(QMainWindow):
    """
    Janela principal do Aetheris ToolBox.
    Organizacao:
      [AppBar]          → título, toolbar, controles de janela
      [Workspace]       → side panel + stacked widget com ferramentas
        ├── Classifier  → ClassificationTool
        └── ...         → futuras ferramentas
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
            tooltip="Classificacao Raster com Redes Neurais",
            icon_text="CL"
        )

    def _connect_signals(self):
        """Conecta sinais do AppBar/Workspace a acoes globais."""
        self.workspace.current_tool_changed.connect(self._on_tool_changed)

    def _on_tool_changed(self, index: int, tool_widget):
        """Callback quando o usuario troca de ferramenta no workspace."""
        pass  # Future: update appbar title, etc.

    def initialize_controller(self):
        """Inicializa o controller APOS a UI estar pronta."""
        self.controller = MainController(self)
        self.loader_overlay = HudCircularRingsLoader(self)
        self.loader_overlay.setGeometry(self.rect())

    # ────────────────────────────────────────────────────────────────────────
    # PROPRIEDADES DE DELEGACAO (compatibilidade com MainController)
    # O controller acessa self.view.btn_executar, self.view.spin_epochs, etc.
    # Delegamos automaticamente para o classification_tool.
    # ────────────────────────────────────────────────────────────────────────

    def __getattr__(self, name):
        """
        Redireciona acesso a atributos da UI para o classification_tool,
        mantendo compatibilidade total com MainController.
        """
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

    # Nota: eventos de mouse para arrasto sao tratados pelo AppBar,
    # nao precisam mais estar no MainWindow.


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