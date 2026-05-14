# -*- coding: utf-8 -*-
"""
ToolGroup — Grupo horizontal de ferramentas na toolbar principal.
==================================================================
Cada ToolGroup representa uma categoria (System, Raster, Vector, etc.)
com botões de ícone para cada ferramenta da categoria.
"""

from __future__ import annotations

from PySide6.QtCore import Qt, Signal, QSize
from PySide6.QtWidgets import QWidget, QHBoxLayout, QToolButton

from core.enum.ToolType import ToolType
from core.model.Tool import Tool
from resources.widgets.ToolSeparator import ToolSeparator


class ToolGroup(QWidget):
    """
    Grupo de ferramentas na toolbar horizontal.

    Layout horizontal com botões de ícone e um separador após o grupo.
    """

    tool_clicked = Signal(str)  # nome da ferramenta

    def __init__(
        self,
        tool_type: ToolType,
        tools: list[Tool],
        parent=None,
    ):
        super().__init__(parent)
        self._tool_type = tool_type

        layout = QHBoxLayout(self)
        layout.setContentsMargins(4, 2, 4, 2)
        layout.setSpacing(2)

        # ── Botões de cada ferramenta (apenas ícone) ──
        for tool in tools:
            btn = QToolButton()
            btn.setIcon(tool.icon)
            btn.setToolTip(tool.tooltip or tool.title)
            btn.setObjectName("toolgroup_btn")
            btn.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonIconOnly)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setFixedSize(32, 32)
            btn.setIconSize(QSize(20, 20))
            btn.clicked.connect(lambda checked, name=tool.name: self.tool_clicked.emit(name))
            btn.setStyleSheet("""
                QToolButton {
                    background-color: transparent;
                    border: none;
                    border-radius: 6px;
                }
                QToolButton:hover {
                    background-color: #1E1E24;
                }
                QToolButton:pressed {
                    background-color: #121216;
                }
            """)
            layout.addWidget(btn)

        # ── Separador decorativo ──
        layout.addWidget(ToolSeparator())

    @property
    def tool_type(self) -> ToolType:
        return self._tool_type