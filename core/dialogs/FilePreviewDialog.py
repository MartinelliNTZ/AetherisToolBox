# -*- coding: utf-8 -*-
"""
FilePreviewDialog — Diálogo de pré-visualização de arquivo
============================================================
Exibe abas horizontais customizadas no topo (HorizontalTab) e
um QStackedWidget que troca de conteúdo conforme a aba selecionada.

- Aba "Preview": exibe o path do arquivo
- Aba "Propriedades": vazia (futuro)

Uso:
    FilePreviewDialog.exec_preview(
        file_path="c:/pasta/arquivo.txt",
        parent=self,
    )
"""

from __future__ import annotations

import os

from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QStackedWidget, QWidget)

from resources.widgets.DialogPage import DialogPage
from resources.widgets.HorizontalTab import HorizontalTab
from resources.widgets.PreviewPanel import PreviewPanel
from utils.DictManager import IMAGE_EXTENSIONS


# ── Conjunto de extensões de imagem ──────────────────────────────────
_IMAGE_EXTS: set[str] = set(IMAGE_EXTENSIONS.keys())


def _is_image(file_path: str) -> bool:
    """Retorna True se a extensão do arquivo é de imagem conhecida."""
    _, ext = os.path.splitext(file_path)
    return ext.lower() in _IMAGE_EXTS


class FilePreviewDialog(QDialog):
    """
    Diálogo modal com HorizontalTab (QTabBar) + QStackedWidget.

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

        # ── Barra de abas (HorizontalTab como QTabBar) ──────────────
        self.tab_bar = HorizontalTab(closable=False, parent=self)
        layout.addWidget(self.tab_bar)

        # ── Stack de páginas ────────────────────────────────────────
        self._stack = QStackedWidget()
        self._stack.setObjectName("file_preview_stack")
        layout.addWidget(self._stack, 1)

        # ── Conteúdo das abas ───────────────────────────────────────
        self._add_tab("Preview", file_path, is_image=_is_image(file_path))
        self._add_tab("Propriedades", None)

        # Conecta sinal de troca de aba
        self.tab_bar.currentChanged.connect(self._on_tab_changed)

        # Ativa primeira aba — usa QTimer para garantir que o layout
        # já esteja resolvido antes de exibir o preview (necessário
        # para PreviewPanel com fixed_size=None).
        if self.tab_bar.count() > 0:
            self.tab_bar.setCurrentIndex(0)
            QTimer.singleShot(0, lambda: self._on_tab_changed(0))

        # ── Botão fechar ────────────────────────────────────────────
        btn_layout = QHBoxLayout()
        btn_layout.setContentsMargins(12, 8, 12, 8)
        btn_layout.addStretch()
        btn = QPushButton("Fechar")
        btn.clicked.connect(self.accept)
        btn_layout.addWidget(btn)
        layout.addLayout(btn_layout)

    def _add_tab(self, title: str, file_path: str | None, is_image: bool = False) -> None:
        """Adiciona uma aba + sua DialogPage no stack."""
        tab_index = self.tab_bar.addTab("")
        self.tab_bar.setTabData(tab_index, title)
        if file_path is not None:
            self.tab_bar.setTabToolTip(tab_index, file_path)

        page = DialogPage(self)
        self._stack.addWidget(page)

        if file_path is not None and not is_image:
            label = QLabel(file_path)
            label.setObjectName(f"file_preview_{title.lower()}")
            label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            label.setWordWrap(True)
            page.add_widget(label, 1)
        elif is_image:
            # Preview com zoom/pan para imagens
            # Não chama show_preview aqui — será feito em _on_tab_changed
            # após o layout estar resolvido (via QTimer no __init__).
            preview = PreviewPanel(fixed_size=None, parent=self)
            preview.setProperty("file_path", file_path)
            page.add_widget(preview, 1)

    def _on_tab_changed(self, index: int) -> None:
        """Atualiza a página visível quando a aba muda."""
        page = self._stack.widget(index)
        if page:
            self._stack.setCurrentWidget(page)

        # Carrega preview da imagem se for PreviewPanel com file_path pendente
        if page:
            preview = page.findChild(PreviewPanel)
            if preview:
                path = preview.property("file_path")
                if path:
                    preview.show_preview(str(path))
                    preview.setProperty("file_path", None)
                    preview.setFocus()

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