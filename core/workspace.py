# -*- coding: utf-8 -*-
"""
Workspace — Área de trabalho do Aetheris ToolBox
==================================================
Gerencia múltiplas ferramentas via QStackedWidget.
Cada ferramenta é um widget registrado com um nome único.
"""

from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QStackedWidget, QHBoxLayout,
    QPushButton, QSizePolicy, QScrollArea, QFrame, QLabel
)


class ToolButton(QPushButton):
    """Botão de seleção de ferramenta no painel lateral."""

    def __init__(self, text: str, tooltip: str = "", parent=None):
        super().__init__(text, parent)
        self.setObjectName("tool_selector_btn")
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setCheckable(True)
        self.setFixedHeight(36)
        if tooltip:
            self.setToolTip(tooltip)


class ToolSidePanel(QWidget):
    """Painel lateral com botões de navegação entre ferramentas."""

    tool_selected = Signal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("tool_side_panel")
        self.setFixedWidth(48)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(4)
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        self._buttons: list[ToolButton] = []
        self._current_index = 0

    def add_tool(self, name: str, tooltip: str = "", icon_text: str = "") -> None:
        """Adiciona um botão para uma ferramenta no painel."""
        display = icon_text if icon_text else name[:2].upper()
        btn = ToolButton(display, tooltip=tooltip)
        index = len(self._buttons)
        btn.clicked.connect(lambda checked, idx=index: self._select_tool(idx))
        self._buttons.append(btn)
        layout = self.layout()
        layout.insertWidget(layout.count() - 1, btn)

        # If first tool, select it
        if len(self._buttons) == 1:
            btn.setChecked(True)

    def _select_tool(self, index: int) -> None:
        if index < 0 or index >= len(self._buttons):
            return
        self._current_index = index
        for i, btn in enumerate(self._buttons):
            btn.setChecked(i == index)
        self.tool_selected.emit(index)

    def select_tool(self, index: int) -> None:
        self._select_tool(index)


class Workspace(QWidget):
    """
    Workspace com painel lateral e QStackedWidget para alternar
    entre ferramentas registradas.
    """

    current_tool_changed = Signal(int, object)  # index, tool_widget

    def __init__(self, parent=None):
        super().__init__(parent)
        self._tools: list[tuple[str, QWidget]] = []

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Side panel
        self.side_panel = ToolSidePanel()
        self.side_panel.tool_selected.connect(self._on_tool_selected)
        layout.addWidget(self.side_panel)

        # Separator vertical
        sep = QFrame()
        sep.setObjectName("workspace_separator")
        sep.setFrameShape(QFrame.Shape.VLine)
        sep.setFixedWidth(1)
        layout.addWidget(sep)

        # Stacked widget
        self.stack = QStackedWidget()
        layout.addWidget(self.stack, 1)

    def register_tool(self, name: str, widget: QWidget, tooltip: str = "",
                      icon_text: str = "") -> int:
        """
        Registra uma ferramenta no workspace.
        Retorna o índice da ferramenta.
        """
        index = len(self._tools)
        self._tools.append((name, widget))

        # Adiciona ao side panel
        self.side_panel.add_tool(name, tooltip=tooltip, icon_text=icon_text)

        # Adiciona ao stacked widget
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setWidget(widget)
        scroll.setObjectName(f"workspace_scroll_{name}")
        self.stack.addWidget(scroll)

        return index

    def current_tool_index(self) -> int:
        return self.stack.currentIndex()

    def current_tool_widget(self) -> QWidget | None:
        idx = self.stack.currentIndex()
        if 0 <= idx < len(self._tools):
            return self._tools[idx][1]
        return None

    def set_current_tool(self, index: int) -> None:
        if 0 <= index < len(self._tools):
            self.side_panel.select_tool(index)

    def _on_tool_selected(self, index: int) -> None:
        if 0 <= index < self.stack.count():
            self.stack.setCurrentIndex(index)
            tool_widget = self._tools[index][1] if index < len(self._tools) else None
            self.current_tool_changed.emit(index, tool_widget)