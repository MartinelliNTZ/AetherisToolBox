# -*- coding: utf-8 -*-
"""
WorkspaceTab — Aba customizada para o Workspace do Aetheris ToolBox
====================================================================
Widget que substitui a aba padrão do QTabBar, exibindo apenas o título
com tamanho calculado dinamicamente com base no texto.

Usado via QTabBar.setTabButton() no RightSide.
O botão fechar (×) continua sendo gerenciado pelo próprio QTabBar.
"""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QFontMetrics
from PySide6.QtWidgets import QWidget, QHBoxLayout, QLabel, QSizePolicy


class WorkspaceTab(QWidget):
    """
    Widget que substitui o conteúdo visual de uma aba no QTabBar.

    Exibe apenas o título com tamanho calculado dinamicamente.
    """

    def __init__(
        self,
        title: str,
        tooltip: str = "",
        parent=None,
    ):
        super().__init__(parent)
        self._title = title

        self.setObjectName("workspace_tab")
        if tooltip:
            self.setToolTip(tooltip)

        self._build_ui()

    def _build_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(6, 2, 6, 2)
        layout.setSpacing(0)

        # -- Título --
        self._label = QLabel(self._title)
        self._label.setObjectName("workspace_tab_label")
        font = self._label.font()
        font.setPointSize(11)
        self._label.setFont(font)
        layout.addWidget(self._label)

        # Calcula largura com base no texto
        self._resize_to_text()

    def _resize_to_text(self):
        """Ajusta a largura do widget com base no comprimento do texto."""
        font = self._label.font()
        fm = QFontMetrics(font)
        text_width = fm.horizontalAdvance(self._title) + 24  # padding extra
        self.setFixedWidth(text_width)

    @property
    def title(self) -> str:
        return self._title

    @title.setter
    def title(self, value: str):
        self._title = value
        self._label.setText(value)
        self._resize_to_text()