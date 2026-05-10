# -*- coding: utf-8 -*-
"""
Workspace — Área de trabalho do Aetheris ToolBox
==================================================
Gerencia múltiplas ferramentas via QTabBar + QStackedWidget.
Cada ferramenta é um widget registrado com um nome único.

Abas podem ser fechadas (×) e movidas (drag).
Ao clicar em uma ferramenta na toolbar, se já estiver aberta,
apenas foca a aba. Caso contrário, abre uma nova aba.
"""

from __future__ import annotations

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
        self._tools: dict[str, Tool] = {}   # nome -> Tool
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
        self.tab_bar.tabMoved.connect(self._on_tab_moved)
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

    def register_tool(self, tool: Tool, focus: bool = True) -> str:
        """Registra uma ferramenta. Retorna o nome."""
        name = tool.name
        self._tools[name] = tool

        # Placeholder no stack (na mesma posição da aba)
        placeholder = QWidget()
        self.stack.addWidget(placeholder)

        # Aba no tab bar — tabData guarda o NOME (viaja junto no drag)
        tab_index = self.tab_bar.addTab("")
        if tool.tooltip:
            self.tab_bar.setTabToolTip(tab_index, tool.tooltip)
        self.tab_bar.setTabData(tab_index, name)

        tab_widget = WorkspaceTab(title=name,
                                  tooltip=tool.tooltip or name)
        self.tab_bar.setTabButton(tab_index, QTabBar.LeftSide, tab_widget)

        self._log.info(f"Tool registrada: {name}", code="TOOL_REG")

        if focus:
            self.tab_bar.setCurrentIndex(tab_index)

        return name

    def open_tool(self, tool: Tool) -> str:
        """Abre ou foca uma ferramenta. Retorna o nome."""
        name = tool.name
        if name in self._tools:
            self.set_current_tool(name)
            return name
        return self.register_tool(tool, focus=True)

    def set_current_tool(self, name: str) -> None:
        """Muda para a aba com o nome da ferramenta."""
        for tab_id in range(self.tab_bar.count()):
            if self.tab_bar.tabData(tab_id) == name:
                # Se já está nesta aba, currentChanged NÃO será emitido
                # pelo Qt — forçamos o callback manualmente
                if self.tab_bar.currentIndex() == tab_id:
                    self._on_tab_changed(tab_id)
                else:
                    self.tab_bar.setCurrentIndex(tab_id)
                return

    def current_tool_name(self) -> str | None:
        """Retorna o nome da ferramenta na aba ativa."""
        tid = self.tab_bar.currentIndex()
        return self.tab_bar.tabData(tid) if tid >= 0 else None

    def current_tool_widget(self) -> QWidget | None:
        name = self.current_tool_name()
        if name and name in self._tools:
            return self._tools[name].widget
        return None

    def is_tool_open(self, name: str) -> bool:
        return name in self._tools

    # ------------------------------------------------------------------
    # Slots privados
    # ------------------------------------------------------------------

    @Slot(int, int)
    def _on_tab_moved(self, from_idx: int, to_idx: int) -> None:
        """
        Quando uma aba é arrastada, move o widget correspondente
        no QStackedWidget para a mesma posição.
        """
        # Pega o widget na posição de origem
        w = self.stack.widget(from_idx)
        if w:
            # Remove da posição antiga e insere na nova
            self.stack.removeWidget(w)
            self.stack.insertWidget(to_idx, w)
        self._log.debug(f"Aba movida: {from_idx} -> {to_idx}",
                        code="TAB_MOVED")

    @Slot(int)
    def _on_tab_changed(self, tab_index: int) -> None:
        name = self.tab_bar.tabData(tab_index)
        if not name or name not in self._tools:
            return

        tool = self._tools[name]

        if not tool.is_loaded:
            self._log.info(f"Carregando tool (lazy): {name}",
                           code="LAZY_LOAD")
            widget = tool.widget
            scroll = QScrollArea()
            scroll.setWidgetResizable(True)
            scroll.setHorizontalScrollBarPolicy(
                Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
            scroll.setWidget(widget)
            scroll.setObjectName(f"workspace_scroll_{name}")

            # Substitui o placeholder no stack pela scroll area
            old = self.stack.widget(tab_index)
            if old:
                self.stack.removeWidget(old)
                old.deleteLater()
            self.stack.insertWidget(tab_index, scroll)

        self.stack.setCurrentIndex(tab_index)
        self.current_tool_changed.emit(
            -1,
            tool.widget if tool.is_loaded else None)

    @Slot(int)
    def _on_tab_close_requested(self, tab_index: int) -> None:
        name = self.tab_bar.tabData(tab_index)
        if not name or name not in self._tools:
            self._log.error(
                f"Tentativa de fechar aba inexistente: tab={tab_index}",
                code="TAB_CLOSE_ERR")
            return

        tool = self._tools[name]

        # Remove widget do stack
        w = self.stack.widget(tab_index)
        if w:
            self.stack.removeWidget(w)
            w.deleteLater()

        # Remove aba do bar
        self.tab_bar.removeTab(tab_index)

        # Remove dos dicts
        del self._tools[name]

        tool.unload()
        self.tool_closed.emit(name)
        self._log.info(f"Aba fechada: {name}", code="TAB_CLOSED")