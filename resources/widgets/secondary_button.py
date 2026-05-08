# -*- coding: utf-8 -*-
"""
SimpleSecondaryButton — Botão secundário.
Uso: Salvar Config, Carregar Config, Restaurar Padrão, etc.
"""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QPushButton
from resources.styles.styles import AppStyles


class SimpleSecondaryButton(QPushButton):
    """
    Botão secundário com fundo escuro e texto dourado.
    """

    def __init__(self, text: str = "Ação", parent=None):
        super().__init__(text, parent)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setStyleSheet(AppStyles.btn_secondary_style())
        self.setMinimumHeight(32)