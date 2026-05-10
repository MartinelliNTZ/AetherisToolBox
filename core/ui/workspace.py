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

from typing import List, Optional

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QStackedWidget,
    QTabBar, QScrollArea, QFrame
)

from core.model.Tool import Tool


class Workspace(QWidget):
    """
    Workspace com QTabBar no topo e QStackedWidget para alternar
    entre ferramentas registradas.

    Abas podem ser fechadas (×) e movidas (drag).
    """

    current_tool_changed = Signal(int, object)  # index, tool_widget
    tool_closed = Signal(str)  # nome da ferramenta fechada

    def __init__(self, parent=None):
        super().__init__(parent)
        self._tools: list[Tool] = []
        self._tool_name_to_index: dict[str, int] = {}  # nome -> nosso index
        self._tab_to_index: dict[int, int] = {}  # tab_bar_id -> nosso index

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # --- Tab bar ---
        self.tab_bar = QTabBar()
        self.tab_bar.setObjectName("workspace_tabs")
        self.tab_bar.setDrawBase(True)
        self.tab_bar.setExpanding(False)
        self.tab_bar.setMovable(True)
        self.tab_bar.setTabsClosable(True)
        self.tab_bar.tabCloseRequested.connect(self._on_tab_close_requested)
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

    def register_tool(self, tool: Tool, focus: bool = True) -> int:
        """
        Registra uma ferramenta (objeto Tool) no workspace.
        O widget so e instanciado (lazy) quando a aba e selecionada
        pela primeira vez.
        
        Parametros:
            tool  : Objeto Tool a ser registrado
            focus : Se True, seleciona a nova aba automaticamente.
        
        Retorna o indice da ferramenta.
        """
        from core.config.LogUtils import LogUtils

        index = len(self._tools)
        self._tools.append(tool)
        self._tool_name_to_index[tool.name] = index

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

        # Foca a nova aba se solicitado
        if focus:
            self.tab_bar.setCurrentIndex(tab_index)

        return index

    def open_tool(self, tool: Tool) -> int:
        """
        Abre (ou foca) uma ferramenta.
        Se já estiver aberta, apenas seleciona a aba existente.
        Se não estiver, registra uma nova aba e já a foca.
        Retorna o indice interno da ferramenta.
        """
        if tool.name in self._tool_name_to_index:
            # Já está aberta — apenas foca
            idx = self._tool_name_to_index[tool.name]
            self.set_current_tool(idx)
            return idx
        else:
            # Abre uma nova aba com focus=True
            return self.register_tool(tool, focus=True)

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

    def _on_tab_close_requested(self, tab_index: int) -> None:
        """Fecha a aba e remove a ferramenta do workspace."""
        tool_idx = self._tab_to_index.pop(tab_index, -1)
        if tool_idx < 0 or tool_idx >= len(self._tools):
            return

        tool = self._tools[tool_idx]
        tool_name = tool.name

        # Remove do stacked
        w = self.stack.widget(tab_index)
        if w:
            self.stack.removeWidget(w)
            w.deleteLater()

        # Remove a aba
        self.tab_bar.removeTab(tab_index)

        # Reindexa
        self._tools.pop(tool_idx)
        new_tab_to_index: dict[int, int] = {}
        for tab_id, our_idx in self._tab_to_index.items():
            if our_idx > tool_idx:
                new_tab_to_index[tab_id] = our_idx - 1
            else:
                new_tab_to_index[tab_id] = our_idx
        self._tab_to_index = new_tab_to_index

        # Reindexa _tool_name_to_index
        self._tool_name_to_index.clear()
        for i, t in enumerate(self._tools):
            self._tool_name_to_index[t.name] = i

        tool.unload()
        self.tool_closed.emit(tool_name)
        from core.config.LogUtils import LogUtils
        logger = LogUtils(tool="System", class_name="Workspace")
        logger.info(f"Aba fechada: {tool_name}", code="TAB_CLOSED")

    def is_tool_open(self, name: str) -> bool:
        """Verifica se uma ferramenta ja esta aberta pelo nome."""
        return name in self._tool_name_to_index

    def get_tool_index(self, name: str) -> Optional[int]:
        """Retorna o indice interno de uma ferramenta pelo nome, ou None."""
        return self._tool_name_to_index.get(name)