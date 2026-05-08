# -*- coding: utf-8 -*-
"""
ConsoleTool — Console de execução compartilhado
================================================
Widget de console independente que pode ser registrado como
uma aba no Workspace. O controller redireciona as mensagens
para este console.
"""

from __future__ import annotations

from PySide6.QtWidgets import QWidget, QVBoxLayout, QTextBrowser
from PySide6.QtCore import Qt


class ConsoleTool(QWidget):
    """
    Console de execução compartilhado.
    Exibe logs formatados com HTML, suporte a links.
    Pode ser acessado de qualquer ferramenta no workspace.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.txt_log = QTextBrowser()
        self.txt_log.setReadOnly(True)
        self.txt_log.setOpenLinks(False)
        self.txt_log.setOpenExternalLinks(False)
        self.txt_log.setPlaceholderText(
            "Console compartilhado — mensagens de execucao aparecem aqui..."
        )
        layout.addWidget(self.txt_log)

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