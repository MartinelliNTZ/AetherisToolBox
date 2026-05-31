# -*- coding: utf-8 -*-
"""
FilePreviewDialog — Diálogo de pré-visualização de arquivo
============================================================
Exibe um QTabWidget com duas abas não fecháveis:
- Preview: área para futura visualização do conteúdo
- Propriedades: área para futuras informações do arquivo

Uso:
    FilePreviewDialog.exec_preview(
        file_path="c:/pasta/arquivo.txt",
        parent=self,
    )
"""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QTabWidget, QLabel, QPushButton, QHBoxLayout,
)

from resources.widgets.BasePage import BasePage


class FilePreviewDialog(QDialog):
    """
    Diálogo modal com QTabWidget de duas abas (Preview e Propriedades).

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
        self.resize(700, 500)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # QTabWidget com as duas abas
        self.tab_widget = QTabWidget()
        self.tab_widget.setObjectName("file_preview_tabs")
        self.tab_widget.setTabsClosable(False)  # abas não fecháveis
        layout.addWidget(self.tab_widget, 1)

        # Aba Preview
        self._preview_page = BasePage()
        self._preview_page.setObjectName("file_preview_page")
        self._build_preview_tab(file_path)
        self.tab_widget.addTab(self._preview_page, "Preview")

        # Aba Propriedades
        self._properties_page = BasePage()
        self._properties_page.setObjectName("file_properties_page")
        self.tab_widget.addTab(self._properties_page, "Propriedades")

        # Botão fechar
        btn_layout = QHBoxLayout()
        btn_layout.setContentsMargins(12, 8, 12, 8)
        btn_layout.addStretch()
        btn = QPushButton("Fechar")
        btn.clicked.connect(self.accept)
        btn_layout.addWidget(btn)
        layout.addLayout(btn_layout)

    def _build_preview_tab(self, file_path: str) -> None:
        """Constrói o conteúdo inicial da aba Preview exibindo o path."""
        label = QLabel(file_path)
        label.setObjectName("file_preview_path")
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        label.setWordWrap(True)
        self._preview_page.add_widget(label, 1)

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