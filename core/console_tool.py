# -*- coding: utf-8 -*-
"""
ConsoleTool — Console de execução compartilhado
================================================
Widget de console independente com botão "Limpar Console" incluso.
Registrado como uma aba no Workspace.
"""

from __future__ import annotations

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTextBrowser, QPushButton
)
from PySide6.QtCore import Qt
from core.styles import AppStyles


class ConsoleTool(QWidget):
    """
    Console de execução compartilhado.
    Exibe logs formatados com HTML, suporte a links.
    Inclui botão "Limpar Console" na barra superior.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Toolbar do console
        toolbar = QWidget()
        toolbar.setObjectName("console_toolbar")
        toolbar_layout = QHBoxLayout(toolbar)
        toolbar_layout.setContentsMargins(8, 6, 8, 6)
        toolbar_layout.setSpacing(6)

        self.btn_clear_console = QPushButton("Limpar Console")
        self.btn_clear_console.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_clear_console.setStyleSheet(AppStyles.btn_ghost_style())
        self.btn_clear_console.setFixedHeight(28)
        toolbar_layout.addWidget(self.btn_clear_console)
        toolbar_layout.addStretch()
        layout.addWidget(toolbar)

        # Text browser do log
        self.txt_log = QTextBrowser()
        self.txt_log.setReadOnly(True)
        self.txt_log.setOpenLinks(False)
        self.txt_log.setOpenExternalLinks(False)
        self.txt_log.setPlaceholderText(
            "Console compartilhado — mensagens de execucao aparecem aqui..."
        )
        layout.addWidget(self.txt_log, 1)

    def append_log(self, html: str) -> None:
        """Adiciona uma mensagem formatada em HTML ao console."""
        self.txt_log.append(html)

    def clear_log(self) -> None:
        """Limpa o console."""
        self.txt_log.clear()

    def set_placeholder(self, text: str) -> None:
        self.txt_log.setPlaceholderText(text)

    @property
    def anchorClicked(self):
        """Expoe o sinal para conexao externa."""
        return self.txt_log.anchorClicked