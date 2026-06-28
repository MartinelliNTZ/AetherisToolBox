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

    Configura icone, tooltip, tamanho, estilo e animacao hover grow.
    O tamanho inicial e definido via min/max (nao setFixedSize)
    para permitir que a animacao redimensione o botao + icone.
    """

    tool_clicked = Signal(str)  # tool.name

    def __init__(self, tool: Tool, parent=None):
        super().__init__(parent)
        self._tool = tool
        self._base_btn_size = AppStyles.toolbar_btn_size()
        self._base_icon_size = AppStyles.toolbar_icon_size()

        self.setIcon(tool.icon)
        self.setToolTip(tool.tooltip or tool.title)
        self.setObjectName("toolgroup_btn")
        self.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonIconOnly)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

        # Usa min/max em vez de setFixedSize para animacao funcionar
        size = self._base_btn_size
        self.setMinimumSize(size, size)
        self.setMaximumSize(size, size)
        self.setIconSize(QSize(self._base_icon_size, self._base_icon_size))
        self.setStyleSheet(AppStyles.toolbar_btn_style())

        self.clicked.connect(lambda: self.tool_clicked.emit(tool.name))

        # ── Animacao hover grow (aumenta botao + icone) ──
        AnimationManager.animate_hover_grow(
            self,
            grow_px=AppStyles.toolbar_btn_hover_grow(),
            grow_icon_px=self._base_icon_size + AppStyles.toolbar_btn_hover_grow(),
        )

    @property
    def tool(self) -> Tool:
        """Retorna o objeto Tool associado a este botao."""
        return self._tool

    @property
    def tool_name(self) -> str:
        """Retorna o nome da ferramenta."""
        return self._tool.name