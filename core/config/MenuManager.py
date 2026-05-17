# -*- coding: utf-8 -*-
"""
MenuManager — Construtor e gestor da toolbar + barra de menus
================================================================
Responsabilidades:
  1. Ler o ToolRegistry e obter a lista completa de ferramentas
  2. Agrupar por ToolType para criar ToolGroups (toolbar)
  3. Instanciar FileMenuItem, SystemMenuItem, HelpMenuItem
  4. Montar a MenuBar com os items e conectar sinais
  5. Encapsular MenuBar, Toolbar e seus sinais em um único lugar

A MainWindow apenas posiciona os widgets prontos.
"""

from __future__ import annotations

from typing import Dict, List, Optional

from PySide6.QtCore import Signal, QObject
from PySide6.QtWidgets import QWidget, QHBoxLayout

from core.config.ToolRegistry import ToolRegistry
from core.enum.ToolType import ToolType
from core.menus.FileMenuItem import FileMenuItem
from core.menus.SystemMenuItem import SystemMenuItem
from core.menus.HelpMenuItem import HelpMenuItem
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

        # ── 1. Criar MenuBar ──
        self._menu_bar = MenuBar()

        # ── 2. Criar e registrar FileMenuItem ──
        self._file_item = FileMenuItem()
        self._file_item.sair_clicked.connect(self._on_sair)
        self._menu_bar.add_menu_item(self._file_item)

        # ── 3. Criar e registrar SystemMenuItem ──
        self._system_item = SystemMenuItem()
        self._system_item.refresh_tools()
        self._system_item.tool_clicked.connect(self._on_tool_clicked)
        self._menu_bar.add_menu_item(self._system_item)

        # ── 4. Criar e registrar HelpMenuItem ──
        self._help_item = HelpMenuItem()
        self._help_item.sobre_clicked.connect(self._on_sobre)
        self._menu_bar.add_menu_item(self._help_item)

        # Conecta sinal genérico do MenuBar (fallback para cliques não tratados)
        self._menu_bar.action_triggered.connect(self._on_menu_action)

        # ── 5. Criar ToolGroups (toolbar) ──
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

        # ── 6. Montar toolbar_widget ──
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

    sair_clicked = Signal()
    sobre_clicked = Signal()

    # ────────────────────────────────────────────────────────────────
    # Métodos privados
    # ────────────────────────────────────────────────────────────────

    def _on_tool_clicked(self, tool_name: str):
        """Propaga o clique da toolbar ou menu."""
        self.tool_activated.emit(tool_name)

    def _on_menu_action(self, data: str):
        """
        Fallback para ações disparadas pelo MenuBar.
        Se o data for um tool_name conhecido, propaga como tool_activated.
        """
        # Apenas propaga se não foi tratado por File/System/Help
        registry = ToolRegistry()
        tool = registry.get(data)
        if tool is not None:
            self.tool_activated.emit(data)

    def _on_sair(self):
        """Propaga sair_clicked."""
        self.sair_clicked.emit()

    def _on_sobre(self):
        """Propaga sobre_clicked."""
        self.sobre_clicked.emit()