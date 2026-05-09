# -*- coding: utf-8 -*-
"""
LogDetailDialog — Dialog de detalhes de um evento de log
===========================================================
Exibe todos os campos de um evento em formato texto selecionavel.
Pode ser aberto com duplo clique na LogViewer ou qualquer outro lugar.

Uso:
    from core.dialogs.LogDetailDialog import LogDetailDialog

    dialog = LogDetailDialog({"level": "INFO", "message": "OK"}, parent=self)
    dialog.exec()
"""

from __future__ import annotations

from typing import List

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QApplication, QDialog, QTextEdit, QVBoxLayout, QHBoxLayout,
)


class LogDetailDialog(QDialog):
    """
    Dialog de detalhes de um evento de log.
    Exibe todos os campos em formato texto selecionavel.
    """

    def __init__(self, event: dict, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Detalhes do Evento")
        self.setMinimumSize(600, 400)
        self.setWindowFlags(
            Qt.WindowType.Dialog |
            Qt.WindowType.WindowCloseButtonHint |
            Qt.WindowType.WindowStaysOnTopHint
        )
        self._build_ui(event)

    def _build_ui(self, event: dict) -> None:
        from utils.ColorProvider import ColorProvider

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(8)

        # Monta texto formatado com todas as chaves do evento
        lines: List[str] = []
        for key, value in event.items():
            if isinstance(value, dict):
                value = str(value)
            if value is None:
                value = ""
            lines.append(f"{key}: {value}")

        text_content = "\n".join(lines)

        self.text_edit = QTextEdit()
        self.text_edit.setPlainText(text_content)
        self.text_edit.setReadOnly(False)  # permite selecionar e copiar
        self.text_edit.setStyleSheet(f"""
            QTextEdit {{
                background-color: #0C0C0F;
                color: {ColorProvider.text_primary()};
                border: 1px solid #1A1A20;
                border-radius: 6px;
                padding: 12px;
                font-family: 'Consolas', 'Courier New', monospace;
                font-size: 13px;
                selection-background-color: #C9A84C;
                selection-color: #08080A;
            }}
        """)
        layout.addWidget(self.text_edit, 1)

        # Botoes
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        from resources.widgets.buttons import SimpleGhostButton

        copy_btn = SimpleGhostButton("Copiar Tudo")
        copy_btn.clicked.connect(self._copy_all)
        btn_layout.addWidget(copy_btn)

        close_btn = SimpleGhostButton("Fechar")
        close_btn.clicked.connect(self.accept)
        btn_layout.addWidget(close_btn)

        layout.addLayout(btn_layout)

        # Aplica tema escuro no dialog
        self.setStyleSheet(f"""
            QDialog {{
                background-color: #121216;
                color: {ColorProvider.text_primary()};
            }}
        """)

    def _copy_all(self) -> None:
        """Copia todo o texto para a clipboard."""
        QApplication.clipboard().setText(self.text_edit.toPlainText())