# -*- coding: utf-8 -*-
"""
ToolSeparator — Separador vertical decorativo entre ToolGroups.
===============================================================
Forma de losango vertical com gradiente dourado:
- Pontas finas e transparentes (topo/base)
- Centro mais largo com cor dourada
"""

from __future__ import annotations

import math

from PySide6.QtWidgets import QWidget
from PySide6.QtGui import QPainter, QColor
from PySide6.QtCore import Qt


class ToolSeparator(QWidget):
    """
    Separador vertical em formato de losango com gradiente dourado.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedWidth(3)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        rect = self.rect()
        w = rect.width()
        h = rect.height()

        for y in range(h):
            t = y / h
            factor = math.sin(t * 3.14159)
            current_w = max(1, int(w * factor))
            alpha = int(180 * factor)
            if current_w > 0:
                x_offset = (w - current_w) // 2
                color = QColor(201, 168, 76, alpha)
                painter.setPen(color)
                painter.drawLine(x_offset, y, x_offset + current_w - 1, y)