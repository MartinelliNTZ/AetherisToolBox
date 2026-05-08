# -*- coding: utf-8 -*-
"""
SimplePrimaryButton — Botão primário com gradiente ouro.
Uso: executar pipeline, ações principais.
"""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QPushButton
from resources.styles.styles import AppStyles


class SimplePrimaryButton(QPushButton):
    """
    Botão primário com gradiente ouro.
    """

    def __init__(self, text: str = "EXECUTAR", parent=None):
        super().__init__(text, parent)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setStyleSheet(AppStyles.btn_primary_style())
        self.setMinimumWidth(180)
        self.setMinimumHeight(34)