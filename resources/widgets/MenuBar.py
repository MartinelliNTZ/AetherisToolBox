# -*- coding: utf-8 -*-
"""
MenuBar — Container da barra de menus do Aetheris ToolBox
===========================================================
Apenas exibe as abas (QMenu) construídas pelos MenuItems.
Cada aba é um BaseMenuItem que sabe construir seu próprio QMenu.

Não contém lógica de negócio — apenas recebe items prontos e os
adiciona ao QMenuBar.
"""

from __future__ import annotations

from typing import Dict

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QMenuBar

from core.menus.BaseMenuItem import BaseMenuItem
from resources.styles.AppStyles import AppStyles


class MenuBar(QMenuBar):
    """
    Container da barra de menus.

    Uso:
        menubar = MenuBar()
        menubar.add_menu_item(item_arquivo)
        menubar.add_menu_item(item_sistema)
        menubar.add_menu_item(item_ajuda)

    Sinais:
        action_triggered — repassa o sinal do BaseMenuItem que foi clicado
                           (data da ação)
    """

    action_triggered = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("app_menu_bar")
        self._apply_style()
        self._items: Dict[str, BaseMenuItem] = {}

    def _apply_style(self):
        """Aplica o estilo padrão da barra de menus."""
        self.setStyleSheet(AppStyles.menu_bar_style())

    # ── API pública ────────────────────────────────────────────────

    def add_menu_item(self, item: BaseMenuItem) -> None:
        """
        Adiciona uma aba à barra de menus.

        O item já deve estar configurado com suas ações.
        O MenuBar cria o QMenu via item.build_menu() e o adiciona.
        """
        name = item.title
        self._items[name] = item

        menu = item.build_menu()
        self.addMenu(menu)

        # Repassa o sinal de clique do item para o container
        item.action_triggered.connect(self._on_item_triggered)

    def remove_menu_item(self, title: str) -> bool:
        """Remove uma aba pelo título. Retorna True se removeu."""
        if title not in self._items:
            return False

        # Remove o QMenu correspondente
        for action in self.actions():
            if action.text() == title and action.menu():
                self.removeAction(action)
                break

        del self._items[title]
        return True

    def get_menu_item(self, title: str) -> BaseMenuItem:
        """Retorna o BaseMenuItem pelo título."""
        return self._items.get(title)

    def refresh_all(self) -> None:
        """
        Reconstrói todos os QMenus a partir dos items atuais.
        Útil quando um item muda dinamicamente (ex: SystemMenuItem).
        """
        # Remove todos os menus atuais
        for action in self.actions():
            self.removeAction(action)

        # Reconstrói
        for name, item in self._items.items():
            menu = item.build_menu()
            self.addMenu(menu)

    # ── Internos ───────────────────────────────────────────────────

    def _on_item_triggered(self, data: str):
        """Repassa o sinal do item para action_triggered do container."""
        self.action_triggered.emit(data)