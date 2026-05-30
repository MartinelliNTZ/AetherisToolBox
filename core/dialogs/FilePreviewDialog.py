# -*- coding: utf-8 -*-
"""
FilePreviewDialog — Diálogo de pré-visualização de arquivo
============================================================
Exibe o path do arquivo selecionado no FileManagerPlugin.

Uso:
    FilePreviewDialog.exec_preview(
        file_path="c:/pasta/arquivo.txt",
        parent=self,
    )
"""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QDialog, QVBoxLayout, QLabel, QPushButton, QHBoxLayout


class FilePreviewDialog(QDialog):
    """
    Diálogo modal que exibe o caminho completo de um arquivo.

    Args:
        file_path: Caminho completo do arquivo a exibir.
        title: Título opcional da janela.
        parent: Widget pai.
    """

    def __init__(
        self,
        file_path: str,
        title: str = "Pré-Visualização do Arquivo",
        parent=None,
    ):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.resize(500, 120)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        # Label com o path
        label = QLabel(file_path)
        label.setObjectName("file_preview_label")
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        label.setWordWrap(True)
        layout.addWidget(label, 1)

        # Botão fechar
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        btn = QPushButton("Fechar")
        btn.clicked.connect(self.accept)
        btn_layout.addWidget(btn)
        layout.addLayout(btn_layout)

    @staticmethod
    def exec_preview(
        file_path: str,
        title: str = "Pré-Visualização do Arquivo",
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