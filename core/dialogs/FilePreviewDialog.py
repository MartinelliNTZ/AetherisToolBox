# -*- coding: utf-8 -*-
"""
FilePreviewDialog — Diálogo de pré-visualização de arquivo
============================================================
Exibe abas (HorizontalTab) no topo e um DialogPage que troca
de conteúdo conforme a aba selecionada.

- Aba "Preview": exibe o path do arquivo
- Aba "Propriedades": vazia (futuro)

Uso:
    FilePreviewDialog.exec_preview(
        file_path="c:/pasta/arquivo.txt",
        parent=self,
    )
"""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QStackedWidget,QWidget)

from resources.widgets.DialogPage import DialogPage
from resources.widgets.HorizontalTab import HorizontalTab


class FilePreviewDialog(QDialog):
    """
    Diálogo modal com abas HorizontalTab + DialogPage.

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

        self._tabs: list[HorizontalTab] = []
        self._pages: list[DialogPage] = []

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # ── Barra de abas ──────────────────────────────────────────
        self._tab_bar = QWidget()        
        self._tab_layout = QHBoxLayout(self._tab_bar)
        self._tab_layout.setContentsMargins(4, 4, 4, 0)
        self._tab_layout.setSpacing(2)
        self._tab_layout.addStretch(1)
        layout.addWidget(self._tab_bar)

        # ── Stack de páginas ───────────────────────────────────────
        self._stack = QStackedWidget()
        self._stack.setObjectName("file_preview_stack")
        layout.addWidget(self._stack, 1)

        # ── Conteúdo das abas ──────────────────────────────────────
        self._add_tab("Preview", file_path, closable=False)
        self._add_tab("Propriedades", None, closable=False)

        # Ativa primeira aba
        if self._tabs:
            self._select_tab(0)

        # ── Botão fechar ───────────────────────────────────────────
        btn_layout = QHBoxLayout()
        btn_layout.setContentsMargins(12, 8, 12, 8)
        btn_layout.addStretch()
        btn = QPushButton("Fechar")
        btn.clicked.connect(self.accept)
        btn_layout.addWidget(btn)
        layout.addLayout(btn_layout)

    def _add_tab(self, title: str, file_path: str | None, closable: bool = True) -> None:
        """Adiciona uma aba HorizontalTab + sua DialogPage."""
        tab = HorizontalTab(title, closable=closable, parent=self)
        tab.setCursor(Qt.CursorShape.PointingHandCursor)
        tab.mousePressEvent = lambda e, t=tab: self._on_tab_clicked(t)
        # Insere antes do stretch
        self._tab_layout.insertWidget(len(self._tabs), tab)
        self._tabs.append(tab)

        page = DialogPage(self)
        self._stack.addWidget(page)
        self._pages.append(page)

        if file_path is not None:
            label = QLabel(file_path)
            label.setObjectName(f"file_preview_{title.lower()}")
            label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            label.setWordWrap(True)
            page.add_widget(label, 1)

        page.setVisible(False)

    def _select_tab(self, index: int) -> None:
        """Ativa a aba no índice."""
        for i, (tab, page) in enumerate(zip(self._tabs, self._pages)):
            active = (i == index)
            # Visual: marcar/desmarcar aba ativa (opcional, QSS pode tratar)
            # Conteúdo
            page.setVisible(active)
            if active:
                self._stack.setCurrentWidget(page)

    def _on_tab_clicked(self, clicked_tab: HorizontalTab) -> None:
        """Manipula clique em uma aba."""
        for i, tab in enumerate(self._tabs):
            if tab is clicked_tab:
                self._select_tab(i)
                break

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