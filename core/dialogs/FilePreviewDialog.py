# -*- coding: utf-8 -*-
"""
FilePreviewDialog — Diálogo simples de pré-visualização de arquivo
===================================================================
Diálogo modal contendo apenas um PreviewPanel que auto-detecta
o tipo do arquivo (imagem, texto, etc.) e exibe o preview.

Uso:
    FilePreviewDialog.exec_preview(
        file_path="c:/pasta/arquivo.txt",
        parent=self,
    )
"""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton)

from resources.widgets.PreviewPanel import PreviewPanel


class FilePreviewDialog(QDialog):
    """
    Diálogo modal com PreviewPanel que auto-detecta o tipo do arquivo.

    Args:
        file_path: Caminho completo do arquivo a exibir.
        title: Título opcional da janela.
        parent: Widget pai.
    """

    def __init__(
        self,
        file_path: str,
        title: str = "Pré-Visualização",
        parent=None,
    ):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.resize(800, 600)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # PreviewPanel — carrega imediatamente para evitar placeholder
        self._preview = PreviewPanel(fixed_size=None, parent=self)
        self._preview.show_preview(file_path)
        layout.addWidget(self._preview, 1)

        # ── Botão fechar ────────────────────────────────────────────
        btn_layout = QHBoxLayout()
        btn_layout.setContentsMargins(8, 6, 8, 6)
        btn_layout.addStretch()
        btn = QPushButton("Fechar")
        btn.clicked.connect(self.accept)
        btn_layout.addWidget(btn)
        layout.addLayout(btn_layout)

    @staticmethod
    def exec_preview(
        file_path: str,
        title: str = "Pré-Visualização",
        parent=None,
    ) -> None:
        """
        Atalho para criar, executar e descartar o diálogo.

        Args:
            file_path: Caminho completo do arquivo.
            title: Título opcional da janela.
            parent: Widget pai.
        """
        dlg = FilePreviewDialog(file_path=file_path, title=title, parent=parent)
        dlg.exec()