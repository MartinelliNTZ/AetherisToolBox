# -*- coding: utf-8 -*-
"""
GroupDiv — Container com título dourado e fundo escuro.
Uso: agrupar widgets relacionados dentro de um card com título.
Suporta QVBoxLayout (padrão) e QGridLayout.
"""

from __future__ import annotations

from typing import Type

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QGridLayout, QGroupBox, QLayout
)


class GroupPainel(QWidget):
    """
    Container com título dourado estilo QGroupBox.
    Fornece um layout interno (`group_layout`) para adicionar widgets filhos.

    Uso:
        grp = GroupDiv("Título do Grupo")
        grp.group_layout.addWidget(QLabel("Conteúdo"))
        parent_layout.addWidget(grp)

    Para layout em grade:
        grp = GroupDiv("Título", layout_type=QGridLayout)
        grp.group_layout.addWidget(QLabel("Item"), 0, 0)
    """

    def __init__(
        self,
        title: str = "",
        parent=None,
        layout_type: Type[QLayout] = QVBoxLayout,
    ):
        super().__init__(parent)

        self._group = QGroupBox(title)

        self._outer_layout = QVBoxLayout(self)
        self._outer_layout.setContentsMargins(0, 0, 0, 0)
        self._outer_layout.setSpacing(0)
        self._outer_layout.addWidget(self._group)

        self.group_layout: QLayout = layout_type(self._group)
