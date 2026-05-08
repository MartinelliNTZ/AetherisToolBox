# -*- coding: utf-8 -*-
"""
Workspace — Área de trabalho do Aetheris ToolBox
==================================================
Gerencia múltiplas ferramentas via QTabBar + QStackedWidget.
Cada ferramenta é um widget registrado com um nome único.
"""

from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QStackedWidget, QHBoxLayout,
    QTabBar, QSizePolicy, QScrollArea, QFrame
)


class Workspace(QWidget):
    """
    Workspace com QTabBar no topo e QStackedWidget para alternar
    entre ferramentas registradas.
    """

    current_tool_changed = Signal(int, object)  # index, tool_widget

    def __init__(self, parent=None):
        super().__init__(parent)
        self._tools: list[tuple[str, QWidget]] = []

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # --- Tab bar ---
        self.tab_bar = QTabBar()
        self.tab_bar.setObjectName("workspace_tabs")
        self.tab_bar.setDrawBase(True)
        self.tab_bar.setExpanding(False)
        self.tab_bar.setMovable(False)
        self.tab_bar.currentChanged.connect(self._on_tab_changed)
        layout.addWidget(self.tab_bar)

        # --- Separator ---
        sep = QFrame()
        sep.setObjectName("workspace_separator")
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setFixedHeight(1)
        layout.addWidget(sep)

        # --- Stacked widget ---
        self.stack = QStackedWidget()
        layout.addWidget(self.stack, 1)

    def register_tool(self, name: str, widget: QWidget, tooltip: str = "") -> int:
        """
        Registra uma ferramenta no workspace.
        Retorna o índice da ferramenta.
        """
        index = len(self._tools)
        self._tools.append((name, widget))

        # Add tab
        tab_index = self.tab_bar.addTab(name)
        if tooltip:
            self.tab_bar.setTabToolTip(tab_index, tooltip)

        # Add to stacked widget (with scroll)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setWidget(widget)
        scroll.setObjectName(f"workspace_scroll_{name}")
        self.stack.addWidget(scroll)

        return index

    def current_tool_index(self) -> int:
        return self.tab_bar.currentIndex()

    def current_tool_widget(self) -> QWidget | None:
        idx = self.tab_bar.currentIndex()
        if 0 <= idx < len(self._tools):
            return self._tools[idx][1]
        return None

    def set_current_tool(self, index: int) -> None:
        if 0 <= index < self.tab_bar.count():
            self.tab_bar.setCurrentIndex(index)

    def set_tab_text(self, index: int, text: str) -> None:
        if 0 <= index < self.tab_bar.count():
            self.tab_bar.setTabText(index, text)

    def _on_tab_changed(self, index: int) -> None:
        if 0 <= index < self.stack.count():
            self.stack.setCurrentIndex(index)
            tool_widget = self._tools[index][1] if index < len(self._tools) else None
            self.current_tool_changed.emit(index, tool_widget)