# -*- coding: utf-8 -*-
"""
SideWorkspace — Painel lateral direito expansível
===================================================
Gerencia ferramentas do tipo SIDE (ex: Console).
Funciona com largura fixa controlada: 36px (colapsado, mostra só as abas)
ou 400px (expandido, mostra conteúdo).

O CentralWorkspace se ajusta automaticamente via layout.
"""

from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QStackedWidget, QFrame, QLabel
)

from core.config.LogUtils import LogUtils
from core.model.Tool import Tool
from resources.widgets.VerticalTab import VerticalTab


class SideWorkspace(QWidget):
    """
    Painel lateral com abas verticais à direita.

    O conteúdo SEMPRE existe dentro do widget.
    Quando colapsado (24px), mostra só a aba vertical.
    Quando expandido (400px), mostra a tool SIDE.
    """

    tool_activated = Signal(str)
    tool_closed    = Signal(str)

    # largura colapsado = mostra só a aba vertical (24px)
    # largura expandido = mostra conteúdo (400px)
    _W_COLLAPSED = 24
    _W_EXPANDED  = 400

    def __init__(self, parent=None):
        super().__init__(parent)
        self._tools: dict[str, Tool] = {}
        self._tabs:  dict[str, VerticalTab] = {}
        self._expanded = False
        self._current_name: str | None = None
        self._log = LogUtils(tool="System", class_name="SideWorkspace")

        self.setObjectName("side_workspace")
        self.setFixedWidth(self._W_COLLAPSED)

        # Layout principal: conteúdo + abas
        mlo = QHBoxLayout(self)
        mlo.setContentsMargins(0, 0, 0, 0)
        mlo.setSpacing(0)

        # ── Conteúdo (stack) ──────────────────────────────────────
        self._content = QWidget()
        clo = QVBoxLayout(self._content)
        clo.setContentsMargins(0, 0, 0, 0)
        clo.setSpacing(0)

        tf = QFrame()
        tf.setObjectName("side_title_frame")
        tf.setFixedHeight(32)
        tl = QHBoxLayout(tf)
        tl.setContentsMargins(8, 0, 8, 0)
        self._title_label = QLabel("Ferramentas")
        self._title_label.setObjectName("side_title_label")
        tl.addWidget(self._title_label)
        tl.addStretch()
        clo.addWidget(tf)

        self.stack = QStackedWidget()
        clo.addWidget(self.stack, 1)

        mlo.addWidget(self._content, 1)

        # ── Abas verticais ─────────────────────────────────────────
        self._tab_box = QWidget()
        self._tab_box.setObjectName("side_tabs_container")
        self._tab_box.setFixedWidth(self._W_COLLAPSED)
        tbl = QVBoxLayout(self._tab_box)
        tbl.setContentsMargins(0, 0, 0, 0)
        tbl.setSpacing(2)
        tbl.setAlignment(Qt.AlignmentFlag.AlignTop)
        self._tabs_layout = tbl
        mlo.addWidget(self._tab_box)

    # ── API ──────────────────────────────────────────────────────────

    def register_tool(self, tool: Tool) -> str:
        name = tool.name
        if name in self._tools:
            return name
        self._tools[name] = tool
        self.stack.addWidget(QWidget())  # placeholder

        tab = VerticalTab(title=tool.title,
                          tooltip=tool.tooltip or tool.title)
        tab.clicked.connect(lambda n=name: self._on_tab_clicked(n))
        self._tabs[name] = tab
        self._tabs_layout.addWidget(tab)

        self._log.info(f"Tool SIDE registrada: {name}", code="SIDE_REG")
        return name

    def open_tool(self, tool: Tool) -> str:
        name = tool.name
        if name in self._tools:
            if self._expanded and self._current_name == name:
                self._set_collapsed()
            else:
                self._set_expanded(name)
            return name
        self.register_tool(tool)
        self._set_expanded(name)
        return name

    # ── Controle de estado ────────────────────────────────────────────

    def _set_collapsed(self):
        self._expanded = False
        self._current_name = None
        for tab in self._tabs.values():
            tab.selected = False
        self._content.setVisible(False)
        self.setFixedWidth(self._W_COLLAPSED)

    def _set_expanded(self, name: str):
        if name not in self._tools:
            return
        self._current_name = name
        self._expanded = True

        for n, tab in self._tabs.items():
            tab.selected = (n == name)

        self._load_tool(name)
        self._content.setVisible(True)
        self.setFixedWidth(self._W_EXPANDED)
        self.tool_activated.emit(name)

    def collapse(self):
        self._set_collapsed()

    def expand(self, name: str):
        self._set_expanded(name)

    # ── Helpers ────────────────────────────────────────────────────────

    def _load_tool(self, name: str):
        tool = self._tools.get(name)
        if not tool:
            return
        keys = list(self._tools.keys())
        if name not in keys:
            return
        idx = keys.index(name)

        if not tool.is_loaded:
            self._log.info(f"Carregando tool SIDE (lazy): {name}",
                           code="SIDE_LAZY")
            w = tool.widget
            old = self.stack.widget(idx)
            if old:
                self.stack.removeWidget(old)
                old.deleteLater()
            self.stack.insertWidget(idx, w)
        self.stack.setCurrentIndex(idx)

    # ── Slots ──────────────────────────────────────────────────────────

    def _on_tab_clicked(self, name: str):
        if self._expanded and self._current_name == name:
            self._set_collapsed()
        else:
            self._set_expanded(name)

    def remove_tool(self, name: str):
        if name not in self._tools:
            return
        tool = self._tools[name]

        tab = self._tabs.pop(name, None)
        if tab:
            self._tabs_layout.removeWidget(tab)
            tab.deleteLater()

        keys = list(self._tools.keys())
        if name in keys:
            idx = keys.index(name)
            w = self.stack.widget(idx)
            if w:
                self.stack.removeWidget(w)
                w.deleteLater()

        del self._tools[name]
        tool.unload()
        self.tool_closed.emit(name)
        self._log.info(f"Tool SIDE fechada: {name}", code="SIDE_CLOSED")

        if len(self._tools) == 0:
            self._set_collapsed()

    def is_tool_open(self, name: str) -> bool:
        return name in self._tools

    @property
    def expanded(self) -> bool:
        return self._expanded