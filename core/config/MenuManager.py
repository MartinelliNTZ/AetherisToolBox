# -*- coding: utf-8 -*-
"""
MenuManager — Construtor e gestor da toolbar + barra de menus
================================================================
Responsabilidades:
  1. Ler o ToolRegistry e obter a lista completa de ferramentas
  2. Agrupar por ToolType para criar ToolGroups (toolbar)
  3. Agrupar por MenuCategory para popular o MenuBar
  4. Encapsular MenuBar, Toolbar e seus sinais em um único lugar

A MainWindow apenas posiciona os widgets prontos.
"""

from __future__ import annotations

from typing import Dict, List, Optional, Tuple

from PySide6.QtCore import Signal, QObject
from PySide6.QtWidgets import QWidget, QHBoxLayout

from core.config.ToolRegistry import ToolRegistry
from core.enum.MenuCategory import MenuCategory
from core.enum.ToolType import ToolType
from core.model.Tool import Tool
from resources.widgets.MenuBar import MenuBar
from resources.widgets.ToolGroup import ToolGroup


class MenuManager(QObject):
    """
    Constrói e gerencia a toolbar E a barra de menus.

    Uso:
        manager = MenuManager()
        manager.build()
        root_layout.addWidget(manager.menu_bar)
        root_layout.addWidget(manager.toolbar_widget)

    Sinais:
        tool_activated — emitido quando o usuário clica em uma ferramenta
                         (seja na toolbar ou no menu)
    """

    tool_activated = Signal(str)  # nome da ferramenta selecionada

    def __init__(self, parent=None):
        super().__init__(parent)
        self._groups: list[ToolGroup] = []
        self._menu_bar: Optional[MenuBar] = None
        self._toolbar_widget: Optional[QWidget] = None

    # ────────────────────────────────────────────────────────────────
    # API pública
    # ────────────────────────────────────────────────────────────────

    def build(self) -> None:
        """
        Constrói a toolbar (ToolGroups) e popula o MenuBar.
        Chame este método antes de acessar .menu_bar e .toolbar_widget.
        """
        registry = ToolRegistry()
        tools = registry.get_all()

        # ── 1. Criar MenuBar e conectar sinais ──
        self._menu_bar = MenuBar()
        self._menu_bar.sair_clicked.connect(self._on_sair)
        self._menu_bar.sobre_clicked.connect(self._on_sobre)
        self._menu_bar.tool_clicked.connect(self._on_tool_clicked)

        # Popula o menu com ferramentas que têm menu_category
        menu_items = self._build_menu_items(tools)
        sistema_items = menu_items.get(MenuCategory.SYSTEM, [])
        self._menu_bar.add_menu_items(sistema_items)

        # ── 2. Criar ToolGroups (toolbar) ──
        grouped: Dict[ToolType, list[Tool]] = {}
        for tool in tools:
            if not tool.show_in_toolbar:
                continue
            tt = tool.tool_type
            if tt not in grouped:
                grouped[tt] = []
            grouped[tt].append(tool)

        self._groups.clear()
        for tool_type in ToolType:
            if tool_type in grouped and grouped[tool_type]:
                group = ToolGroup(tool_type=tool_type, tools=grouped[tool_type])
                group.tool_clicked.connect(self._on_tool_clicked)
                self._groups.append(group)

        # ── 3. Montar toolbar_widget ──
        if self._groups:
            container = QWidget()
            container.setObjectName("toolbar_panel")
            container.setStyleSheet("""
                QWidget#toolbar_panel {
                    background-color: #0A0A0D;
                    border-bottom: 1px solid #1A1A20;
                }
            """)
            layout = QHBoxLayout(container)
            layout.setContentsMargins(4, 2, 4, 2)
            layout.setSpacing(0)
            for group in self._groups:
                layout.addWidget(group)
            layout.addStretch()
            self._toolbar_widget = container
        else:
            self._toolbar_widget = QWidget()
            self._toolbar_widget.setVisible(False)

    # ────────────────────────────────────────────────────────────────
    # Widgets prontos
    # ────────────────────────────────────────────────────────────────

    @property
    def menu_bar(self) -> MenuBar:
        """Barra de menus pronta para ser adicionada ao layout."""
        if self._menu_bar is None:
            raise RuntimeError("Chame build() antes de acessar menu_bar.")
        return self._menu_bar

    @property
    def toolbar_widget(self) -> QWidget:
        """Widget da toolbar pronto para ser adicionado ao layout."""
        if self._toolbar_widget is None:
            raise RuntimeError("Chame build() antes de acessar toolbar_widget.")
        return self._toolbar_widget

    @property
    def tool_groups(self) -> list[ToolGroup]:
        """Lista dos ToolGroups criados (útil para inspeção)."""
        return list(self._groups)

    # ────────────────────────────────────────────────────────────────
    # Sinais internos (conectados pela MainWindow)
    # ────────────────────────────────────────────────────────────────

    # Expostos para a MainWindow conectar
    sair_clicked = Signal()
    sobre_clicked = Signal()

    # ────────────────────────────────────────────────────────────────
    # Métodos privados
    # ────────────────────────────────────────────────────────────────

    @staticmethod
    def _build_menu_items(tools: List[Tool]) -> Dict[MenuCategory, List[Tuple[str, str]]]:
        """Agrupa ferramentas por MenuCategory."""
        grouped: Dict[MenuCategory, List[Tuple[str, str]]] = {}
        for tool in tools:
            mc = tool.menu_category
            if mc is None:
                continue
            if mc not in grouped:
                grouped[mc] = []
            grouped[mc].append((tool.name, tool.title))
        return grouped

    def _on_tool_clicked(self, tool_name: str):
        """Propaga o clique da toolbar ou menu."""
        self.tool_activated.emit(tool_name)

    def _on_sair(self):
        """Propaga sair_clicked."""
        self.sair_clicked.emit()

    def _on_sobre(self):
        """Propaga sobre_clicked."""
        self.sobre_clicked.emit()