# -*- coding: utf-8 -*-
"""
RecentProjectsMenu — Submenu de projetos recentes
===================================================
QMenu especializado em exibir lista de projetos recentes.

Cada item representa um projeto:
    - active=True  → habilitado, clicável
    - active=False → desabilitado (itálico), arquivo não encontrado

Uso:
    from resources.widgets.RecentProjectsMenu import RecentProjectsMenu

    recent_menu = RecentProjectsMenu()
    recent_menu.rebuild(recents)
    recent_menu.project_clicked.connect(self._on_recent_clicked)
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List

from PySide6.QtCore import Signal
from PySide6.QtGui import QAction, QFont
from PySide6.QtWidgets import QMenu

from resources.styles.AppStyles import AppStyles


class RecentProjectsMenu(QMenu):
    """
    Menu dinâmico exibindo a lista de projetos recentes.

    Sinais:
        project_clicked(path: str) — emitido ao clicar em um projeto ativo
    """

    project_clicked = Signal(str)

    def __init__(self, parent=None):
        super().__init__("Abrir Recente", parent)
        self.setStyleSheet(AppStyles.menu_dropdown_style())

    def rebuild(self, recents: List[Dict[str, Any]]) -> None:
        """
        Reconstrói o menu com a lista de projetos recentes.

        Args:
            recents: Lista de dicts com chaves path, name, active
        """
        self.clear()

        if not recents:
            empty_action = QAction("(nenhum projeto recente)", self)
            empty_action.setEnabled(False)
            self.addAction(empty_action)
            return

        for recent in recents:
            path = recent.get("path", "")
            name = recent.get("name", Path(path).stem if path else "?")
            active = recent.get("active", False)

            action = QAction(name, self)
            action.setToolTip(path)
            action.setData(path)
            action.setEnabled(active)

            if not active:
                font = action.font()
                font.setItalic(True)
                action.setFont(font)

            action.triggered.connect(self._on_action_triggered)
            self.addAction(action)

    def _on_action_triggered(self) -> None:
        """Propaga o clique com o path do projeto."""
        action = self.sender()
        if action and action.isEnabled():
            path = action.data()
            if path:
                self.project_clicked.emit(path)