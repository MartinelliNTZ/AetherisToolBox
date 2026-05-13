# -*- coding: utf-8 -*-
"""
MenuManager — Construtor da toolbar principal a partir do ToolRegistry
=======================================================================
Agrupa as ferramentas por ToolType, cria ToolGroups e os insere na AppBar.
"""

from __future__ import annotations

from typing import Dict, List, Tuple

from PySide6.QtCore import Signal, QObject

from core.config.ToolRegistry import ToolRegistry
from core.enum.MenuCategory import MenuCategory
from core.enum.ToolType import ToolType
from core.model.Tool import Tool
from resources.widgets.ToolGroup import ToolGroup


class MenuManager(QObject):
    """
    Constrói e gerencia a toolbar com grupos de ferramentas.

    Uso:
        manager = MenuManager()
        manager.build()
        for group in manager.groups:
            appbar.add_tool_widget(group)
    """

    tool_activated = Signal(str)  # nome da ferramenta selecionada (toolbar)
    menu_tool_activated = Signal(str)  # nome da ferramenta selecionada (menu)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._groups: list[ToolGroup] = []

    def build(self) -> list[ToolGroup]:
        """
        Lê o ToolRegistry, agrupa as tools por ToolType e cria ToolGroups.
        Retorna a lista de ToolGroups.
        """
        registry = ToolRegistry()
        tools = registry.get_all()

        # Agrupa tools por tool_type (somente as que devem aparecer na toolbar)
        grouped: Dict[ToolType, list[Tool]] = {}
        for tool in tools:
            if not tool.show_in_toolbar:
                continue
            tt = tool.tool_type
            if tt not in grouped:
                grouped[tt] = []
            grouped[tt].append(tool)

        # Cria um ToolGroup para cada ToolType que tenha tools
        self._groups.clear()
        for tool_type in ToolType:
            if tool_type in grouped and grouped[tool_type]:
                group = ToolGroup(tool_type=tool_type, tools=grouped[tool_type])
                group.tool_clicked.connect(self._on_tool_clicked)
                self._groups.append(group)

        return self._groups

    def build_menu_items(self) -> Dict[MenuCategory, List[Tuple[str, str]]]:
        """
        Agrupa ferramentas por MenuCategory para construir menus.

        Retorna:
            Dict[MenuCategory, List[Tuple[tool_name, tool_title]]]
        """
        registry = ToolRegistry()
        tools = registry.get_all()

        grouped: Dict[MenuCategory, List[Tuple[str, str]]] = {}
        for tool in tools:
            mc = tool.menu_category
            if mc is None:
                continue
            if mc not in grouped:
                grouped[mc] = []
            grouped[mc].append((tool.name, tool.title))

        return grouped

    def get_system_menu_items(self) -> List[Tuple[str, str]]:
        """Retorna itens para o menu Sistema."""
        items = self.build_menu_items()
        return items.get(MenuCategory.SYSTEM, [])

    def _on_tool_clicked(self, tool_name: str):
        """Propaga o clique do botão como sinal."""
        self.tool_activated.emit(tool_name)

    @property
    def groups(self) -> list[ToolGroup]:
        """Retorna a lista de ToolGroups criados."""
        return list(self._groups)