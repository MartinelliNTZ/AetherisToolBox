# -*- coding: utf-8 -*-
"""
SideWorkspace — Painel lateral direito com abas verticais expansíveis
======================================================================
Gerencia ferramentas do tipo SIDE (ex: Console).
Abas ficam na vertical à direita e ao clicar expandem/recolhem o painel.
Um QSplitter permite redimensionar entre o CentralWorkspace e este painel.
"""

from __future__ import annotations

from PySide6.QtCore import Qt, Signal, Slot
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QStackedWidget, QFrame, QLabel, QListWidget,
    QListWidgetItem, QSizePolicy
)

from core.config.LogUtils import LogUtils
from core.model.Tool import Tool
from core.enum.CategoryTool import CategoryTool


class SideWorkspace(QWidget):
    """
    Painel lateral com abas verticais à direita.
    Cada aba representa uma ferramenta SIDE.

    Ao clicar em uma aba, o painel expande para mostrar o conteúdo.
    Ao clicar novamente (mesma aba), recolhe.
    O QSplitter no MainWindow permite redimensionar.
    """

    tool_activated = Signal(str)
    tool_closed    = Signal(str)
    _EXPANDED_WIDTH = 400
    _COLLAPSED_WIDTH = 40

    def __init__(self, parent=None):
        super().__init__(parent)
        self._tools: dict[str, Tool] = {}
        self._expanded = False
        self._current_name: str | None = None
        self._log = LogUtils(tool="System", class_name="SideWorkspace")

        self.setObjectName("side_workspace")
        self.setFixedWidth(self._COLLAPSED_WIDTH)

        # Layout horizontal: conteúdo | abas verticais
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # --- Conteúdo expandido (oculto inicialmente) ---
        self._content = QWidget()
        content_layout = QVBoxLayout(self._content)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)

        title_frame = QFrame()
        title_frame.setObjectName("side_title_frame")
        title_frame.setFixedHeight(32)
        title_layout = QHBoxLayout(title_frame)
        title_layout.setContentsMargins(8, 0, 8, 0)
        self._title_label = QLabel("Ferramentas")
        self._title_label.setObjectName("side_title_label")
        title_layout.addWidget(self._title_label)
        title_layout.addStretch()
        content_layout.addWidget(title_frame)

        self.stack = QStackedWidget()
        content_layout.addWidget(self.stack, 1)
        self._content.hide()

        main_layout.addWidget(self._content, 1)

        # --- Abas verticais (sempre visível) ---
        self._tab_list = QListWidget()
        self._tab_list.setObjectName("side_tab_list")
        self._tab_list.setFixedWidth(self._COLLAPSED_WIDTH)
        self._tab_list.setSpacing(2)
        self._tab_list.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self._tab_list.setVerticalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self._tab_list.setSelectionMode(
            QListWidget.SelectionMode.SingleSelection)
        self._tab_list.itemClicked.connect(self._on_tab_clicked)
        main_layout.addWidget(self._tab_list)

    # ------------------------------------------------------------------
    # API pública
    # ------------------------------------------------------------------

    def register_tool(self, tool: Tool) -> str:
        """Registra uma ferramenta SIDE. Retorna o nome."""
        name = tool.name
        if name in self._tools:
            return name

        self._tools[name] = tool

        # Placeholder no stack
        placeholder = QWidget()
        self.stack.addWidget(placeholder)

        # Item na lista vertical
        item = QListWidgetItem(tool.title)
        item.setData(Qt.ItemDataRole.UserRole, name)
        item.setToolTip(tool.tooltip or tool.title)
        self._tab_list.addItem(item)

        self._log.info(f"Tool SIDE registrada: {name}", code="SIDE_REG")
        return name

    def open_tool(self, tool: Tool) -> str:
        """Abre ou foca uma ferramenta SIDE. Se já está aberta, recolhe."""
        name = tool.name
        if name in self._tools:
            if self._expanded and self._current_name == name:
                self.collapse()
            else:
                self.expand(name)
            return name

        self.register_tool(tool)
        self.expand(name)
        return name

    def expand(self, name: str) -> None:
        """Expande o painel e mostra a ferramenta."""
        for i in range(self._tab_list.count()):
            item = self._tab_list.item(i)
            if item.data(Qt.ItemDataRole.UserRole) == name:
                self._tab_list.setCurrentItem(item)
                self._current_name = name
                self._expanded = True
                self.setFixedWidth(self._EXPANDED_WIDTH)
                self._content.show()
                self._load_tool_content(name)
                self.tool_activated.emit(name)
                return

    def collapse(self) -> None:
        """Recolhe o painel."""
        self._expanded = False
        self._current_name = None
        self._tab_list.clearSelection()
        self.setFixedWidth(self._COLLAPSED_WIDTH)
        self._content.hide()
        self.stack.setCurrentIndex(-1)

    def is_tool_open(self, name: str) -> bool:
        return name in self._tools

    @property
    def expanded(self) -> bool:
        return self._expanded

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------

    def _load_tool_content(self, name: str) -> None:
        """Carrega (lazy) e mostra o widget da ferramenta."""
        tool = self._tools.get(name)
        if not tool:
            return

        # Encontra o índice no stack pelo nome no tabData
        tab_index = -1
        for i in range(self._tab_list.count()):
            item = self._tab_list.item(i)
            if item.data(Qt.ItemDataRole.UserRole) == name:
                tab_index = i
                break

        if tab_index < 0:
            return

        if not tool.is_loaded:
            self._log.info(f"Carregando tool SIDE (lazy): {name}",
                           code="SIDE_LAZY")
            widget = tool.widget
            old = self.stack.widget(tab_index)
            if old:
                self.stack.removeWidget(old)
                old.deleteLater()
            self.stack.insertWidget(tab_index, widget)

        self.stack.setCurrentIndex(tab_index)

    # ------------------------------------------------------------------
    # Slots
    # ------------------------------------------------------------------

    @Slot(QListWidgetItem)
    def _on_tab_clicked(self, item: QListWidgetItem) -> None:
        name = item.data(Qt.ItemDataRole.UserRole)
        if not name:
            return

        if self._expanded and self._current_name == name:
            self.collapse()
        else:
            self.expand(name)

    def _on_tab_close_requested(self, name: str) -> None:
        """Remove uma ferramenta SIDE."""
        if name not in self._tools:
            return

        tool = self._tools[name]
        tab_index = -1

        # Encontra e remove o item da lista
        for i in range(self._tab_list.count()):
            item = self._tab_list.item(i)
            if item.data(Qt.ItemDataRole.UserRole) == name:
                self._tab_list.takeItem(i)
                tab_index = i
                break

        # Remove do stack
        if tab_index >= 0:
            w = self.stack.widget(tab_index)
            if w:
                self.stack.removeWidget(w)
                w.deleteLater()

        del self._tools[name]
        tool.unload()
        self.tool_closed.emit(name)
        self._log.info(f"Tool SIDE fechada: {name}", code="SIDE_CLOSED")

        if self._tab_list.count() == 0:
            self.collapse()
