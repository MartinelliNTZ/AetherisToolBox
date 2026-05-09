# -*- coding: utf-8 -*-
"""
SimpleGhostButton — Botão ghost (invisível, aparece no hover).
Uso: Adicionar Shapefile, ações sutis.
"""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QPushButton
from resources.styles.styles import AppStyles


class SimpleGhostButton(QPushButton):
    """
    Botão ghost (invisível, aparece no hover).
    """

    def __init__(self, text: str = "Ação", parent=None):
        super().__init__(text, parent)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setStyleSheet(AppStyles.btn_ghost_style())