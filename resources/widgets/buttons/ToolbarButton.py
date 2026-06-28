# -*- coding: utf-8 -*-
"""
ToolbarButton — Botão de ícone para a toolbar principal.
==========================================================
Cada ToolbarButton representa uma ferramenta individual na toolbar,
exibindo apenas o ícone da ferramenta com tooltip no hover.

Uso:
    from resources.widgets.buttons.ToolbarButton import ToolbarButton

    btn = ToolbarButton(tool)
    btn.tool_clicked.connect(self._on_tool_activated)
"""

from __future__ import annotations

from PySide6.QtCore import Qt, Signal, QSize
from PySide6.QtWidgets import QToolButton

from core.model.Tool import Tool
from resources.styles.AppStyles import AppStyles
from resources.styles.AnimationManager import AnimationManager


class ToolbarButton(QToolButton):
    """
    Botão de ícone para uma ferramenta na toolbar.

    Configura automaticamente ícone, tooltip, tamanho, estilo
    e animação hover grow (aumenta ao passar o mouse).
    """

    tool_clicked = Signal(str)  # tool.name

    def __init__(self, tool: Tool, parent=None):
        super().__init__(parent)
        self._tool = tool

        self.setIcon(tool.icon)
        self.setToolTip(tool.tooltip or tool.title)
        self.setObjectName("toolgroup_btn")
        self.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonIconOnly)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

        btn_size = AppStyles.toolbar_btn_size()
        icon_size = AppStyles.toolbar_icon_size()
        self.setFixedSize(btn_size, btn_size)
        self.setIconSize(QSize(icon_size, icon_size))
        self.setStyleSheet(AppStyles.toolbar_btn_style())

        self.clicked.connect(lambda: self.tool_clicked.emit(tool.name))

        # ── Animação hover grow (aumenta no hover) ──
        AnimationManager.animate_hover_grow(
            self,
            grow_px=AppStyles.toolbar_btn_hover_grow(),
        )

    @property
    def tool(self) -> Tool:
        """Retorna o objeto Tool associado a este botão."""
        return self._tool

    @property
    def tool_name(self) -> str:
        """Retorna o nome da ferramenta."""
        return self._tool.name