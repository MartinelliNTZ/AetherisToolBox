# -*- coding: utf-8 -*-
"""
Workspace — Área de trabalho do Aetheris ToolBox
"""

from __future__ import annotations

from typing import Optional

from PySide6.QtCore import Qt, Signal, Slot
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QStackedWidget,
    QTabBar, QScrollArea, QFrame
)

from core.config.LogUtils import LogUtils
from core.model.Tool import Tool
from resources.widgets.WorkspaceTab import WorkspaceTab


class Workspace(QWidget):

    current_tool_changed = Signal(int, object)
    tool_closed          = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._tools:               list[Tool]      = []
        self._tool_name_to_index:  dict[str, int]  = {}
        self._tab_to_tool:         dict[int, int]  = {}  # tab_bar_idx -> tool_idx
        self._log = LogUtils(tool="System", class_name="Workspace")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.tab_bar = QTabBar()
        self.tab_bar.setObjectName("workspace_tabs")
        self.tab_bar.setDrawBase(True)
        self.tab_bar.setExpanding(False)
        self.tab_bar.setMovable(True)
        self.tab_bar.setTabsClosable(True)
        self.tab_bar.tabCloseRequested.connect(self._on_tab_close_requested)
        self.tab_bar.currentChanged.connect(self._on_tab_changed)
        layout.addWidget(self.tab_bar)

        sep = QFrame()
        sep.setObjectName("workspace_separator")
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setFixedHeight(1)
        layout.addWidget(sep)

        self.stack = QStackedWidget()
        layout.addWidget(self.stack, 1)

    # ------------------------------------------------------------------
    # API pública
    # ------------------------------------------------------------------

    def register_tool(self, tool: Tool, focus: bool = True) -> int:
        index = len(self._tools)
        self._tools.append(tool)
        self._tool_name_to_index[tool.name] = index

        placeholder = QWidget()
        self.stack.addWidget(placeholder)

        tab_index = self.tab_bar.addTab("")
        if tool.tooltip:
            self.tab_bar.setTabToolTip(tab_index, tool.tooltip)

        self._tab_to_tool[tab_index] = index

        tab_widget = WorkspaceTab(title=tool.name,
                                  tooltip=tool.tooltip or tool.name)
        self.tab_bar.setTabButton(tab_index, QTabBar.LeftSide, tab_widget)

        self._log.info(f"Tool registrada: {tool.name}",
                       code="TOOL_REG", index=index)

        if focus:
            self.tab_bar.setCurrentIndex(tab_index)

        return index

    def open_tool(self, tool: Tool) -> int:
        if tool.name in self._tool_name_to_index:
            idx = self._tool_name_to_index[tool.name]
            self.set_current_tool(idx)
            return idx
        return self.register_tool(tool, focus=True)

    def set_current_tool(self, index: int) -> None:
        for tab_id, tool_idx in self._tab_to_tool.items():
            if tool_idx == index:
                self.tab_bar.setCurrentIndex(tab_id)
                return

    def current_tool_index(self) -> int:
        return self.tab_bar.currentIndex()

    def current_tool_widget(self) -> QWidget | None:
        tab_idx  = self.tab_bar.currentIndex()
        tool_idx = self._tab_to_tool.get(tab_idx, -1)
        if 0 <= tool_idx < len(self._tools):
            return self._tools[tool_idx].widget
        return None

    def is_tool_open(self, name: str) -> bool:
        return name in self._tool_name_to_index

    def get_tool_index(self, name: str) -> Optional[int]:
        return self._tool_name_to_index.get(name)

    # ------------------------------------------------------------------
    # Slots privados
    # ------------------------------------------------------------------

    @Slot(int)
    def _on_tab_changed(self, tab_index: int) -> None:
        tool_idx = self._tab_to_tool.get(tab_index, -1)
        if tool_idx < 0 or tool_idx >= len(self._tools):
            return

        tool = self._tools[tool_idx]

        if not tool.is_loaded:
            self._log.info(f"Carregando tool (lazy): {tool.name}",
                           code="LAZY_LOAD")
            widget = tool.widget
            scroll = QScrollArea()
            scroll.setWidgetResizable(True)
            scroll.setHorizontalScrollBarPolicy(
                Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
            scroll.setWidget(widget)
            scroll.setObjectName(f"workspace_scroll_{tool.name}")

            # FIX: usa stack index consistente, não tab_index diretamente
            old = self.stack.widget(tab_index)
            if old:
                self.stack.removeWidget(old)
                old.deleteLater()
            self.stack.insertWidget(tab_index, scroll)
        else:
            self._log.debug(f"Aba selecionada: {tool.name}",
                            code="TAB_SWITCH")

        self.stack.setCurrentIndex(tab_index)
        self.current_tool_changed.emit(
            tool_idx, tool.widget if tool.is_loaded else None)

    @Slot(int)
    def _on_tab_close_requested(self, tab_index: int) -> None:
        tool_idx = self._tab_to_tool.pop(tab_index, -1)
        if tool_idx < 0 or tool_idx >= len(self._tools):
            self._log.error(
                f"Tentativa de fechar aba inexistente: tab={tab_index}",
                code="TAB_CLOSE_ERR")
            return

        tool      = self._tools[tool_idx]
        tool_name = tool.name

        # Remove widget do stack
        w = self.stack.widget(tab_index)
        if w:
            self.stack.removeWidget(w)
            w.deleteLater()

        # Remove aba do bar
        self.tab_bar.removeTab(tab_index)

        # FIX CRÍTICO: após removeTab o Qt renumera os índices das abas
        # restantes (todas as abas > tab_index recuam 1).
        # Precisamos espelhar isso nas chaves de _tab_to_tool.
        rebuilt: dict[int, int] = {}
        for t_id, t_idx in self._tab_to_tool.items():
            new_t_id  = t_id  - 1 if t_id  > tab_index else t_id
            new_t_idx = t_idx - 1 if t_idx > tool_idx  else t_idx
            rebuilt[new_t_id] = new_t_idx
        self._tab_to_tool = rebuilt

        # Atualiza _tools e _tool_name_to_index
        self._tools.pop(tool_idx)
        self._tool_name_to_index = {t.name: i
                                    for i, t in enumerate(self._tools)}

        tool.unload()
        self.tool_closed.emit(tool_name)
        self._log.info(f"Aba fechada: {tool_name}", code="TAB_CLOSED")