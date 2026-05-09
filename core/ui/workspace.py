# -*- coding: utf-8 -*-
"""
Workspace — Área de trabalho do Aetheris ToolBox
==================================================
Gerencia múltiplas ferramentas via QTabBar + QStackedWidget.
Cada ferramenta é um widget registrado com um nome único.
"""

from __future__ import annotations

from typing import List

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QStackedWidget, QHBoxLayout,
    QTabBar, QSizePolicy, QScrollArea, QFrame
)

from core.model.Tool import Tool


class Workspace(QWidget):
    """
    Workspace com QTabBar no topo e QStackedWidget para alternar
    entre ferramentas registradas.
    """

    current_tool_changed = Signal(int, object)  # index, tool_widget

    def __init__(self, parent=None):
        super().__init__(parent)
        self._tools: list[Tool] = []
        self._tab_to_index: dict[int, int] = {}  # tab_bar_id -> nosso index

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

    def register_tool(self, tool: Tool) -> int:
        """
        Registra uma ferramenta (objeto Tool) no workspace.
        O widget so e instanciado (lazy) quando a aba e selecionada
        pela primeira vez.
        Retorna o indice da ferramenta.
        """
        from core.config.LogUtils import LogUtils

        index = len(self._tools)
        self._tools.append(tool)

        # Cria uma pagina placeholder no stacked widget
        placeholder = QWidget()
        self.stack.addWidget(placeholder)

        # Adiciona a aba
        tab_index = self.tab_bar.addTab(tool.name)
        if tool.tooltip:
            self.tab_bar.setTabToolTip(tab_index, tool.tooltip)
        self._tab_to_index[tab_index] = index

        logger = LogUtils(tool="System", class_name="Workspace")
        logger.info(f"Tool registrada: {tool.name}", code="TOOL_REG", index=index)

        return index

    def current_tool_index(self) -> int:
        return self.tab_bar.currentIndex()

    def current_tool_widget(self) -> QWidget | None:
        idx = self.tab_bar.currentIndex()
        tool_idx = self._tab_to_index.get(idx, -1)
        if 0 <= tool_idx < len(self._tools):
            return self._tools[tool_idx].widget
        return None

    def set_current_tool(self, index: int) -> None:
        """Muda para a aba no indice interno especificado."""
        # Procura o tab_bar_id correspondente ao nosso index
        for tab_id, our_idx in self._tab_to_index.items():
            if our_idx == index:
                self.tab_bar.setCurrentIndex(tab_id)
                return

    def set_tab_text(self, index: int, text: str) -> None:
        """Altera o texto de uma aba pelo indice interno."""
        for tab_id, our_idx in self._tab_to_index.items():
            if our_idx == index:
                self.tab_bar.setTabText(tab_id, text)
                return

    def _on_tab_changed(self, tab_index: int) -> None:
        """Quando a aba muda, carrega o widget real (lazy) se necessario."""
        from core.config.LogUtils import LogUtils

        tool_idx = self._tab_to_index.get(tab_index, -1)
        if tool_idx < 0 or tool_idx >= len(self._tools):
            return

        tool = self._tools[tool_idx]
        logger = LogUtils(tool="System", class_name="Workspace")

        if not tool.is_loaded:
            logger.info(f"Carregando tool (lazy): {tool.name}", code="LAZY_LOAD")
            widget = tool.widget  # aciona a factory
            scroll = QScrollArea()
            scroll.setWidgetResizable(True)
            scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
            scroll.setWidget(widget)
            scroll.setObjectName(f"workspace_scroll_{tool.name}")
            self.stack.removeWidget(self.stack.widget(tab_index))
            self.stack.insertWidget(tab_index, scroll)
        else:
            logger.debug(f"Aba selecionada: {tool.name}", code="TAB_SWITCH")

        self.stack.setCurrentIndex(tab_index)
        self.current_tool_changed.emit(tool_idx, tool.widget if tool.is_loaded else None)
