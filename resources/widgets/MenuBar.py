# -*- coding: utf-8 -*-
"""
MenuBar — Barra de menus do Aetheris ToolBox
==============================================
Exibe menus: "Arquivo" (Sair), "Sistema" (tools), "Ajuda" (Sobre).
Suporta inserção dinâmica de ações de ferramentas via `add_menu_items`.
"""

from __future__ import annotations

from typing import Dict, List, Tuple, Callable

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QMenuBar, QMenu
from PySide6.QtGui import QAction

from core.enum.MenuCategory import MenuCategory


class MenuBar(QMenuBar):
    """
    Barra de menus com Arquivo, Sistema (dinâmico) e Ajuda.

    Sinais:
        sair_clicked  — emitido quando usuário clica em Arquivo > Sair
        sobre_clicked — emitido quando usuário clica em Ajuda > Sobre
        tool_clicked  — emitido quando clica em um item de ferramenta no menu
                        (tool_name)
    """

    sair_clicked = Signal()
    sobre_clicked = Signal()
    tool_clicked = Signal(str)  # nome da ferramenta

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("app_menu_bar")
        self._apply_style()
        self._build_menus()

    def _apply_style(self):
        from resources.styles.styles import AppStyles
        self.setStyleSheet(AppStyles.menu_bar_style())

    def _build_menus(self):
        # Menu Arquivo
        menu_arquivo = QMenu("Arquivo", self)
        acao_sair = QAction("Sair", self)
        acao_sair.triggered.connect(self.sair_clicked)
        menu_arquivo.addAction(acao_sair)
        self.addMenu(menu_arquivo)

        # Menu Sistema (vazio inicialmente, preenchido via add_menu_items)
        self._menu_sistema = QMenu("Sistema", self)
        self.addMenu(self._menu_sistema)

        # Menu Ajuda
        menu_ajuda = QMenu("Ajuda", self)
        acao_sobre = QAction("Sobre", self)
        acao_sobre.triggered.connect(self.sobre_clicked)
        menu_ajuda.addAction(acao_sobre)
        self.addMenu(menu_ajuda)

    def add_menu_items(self, items: List[Tuple[str, str]]):
        """
        Adiciona ações ao menu Sistema.

        Args:
            items: Lista de (tool_name, tool_title) para criar ações.
                   Substitui qualquer conteúdo anterior.
        """
        self._menu_sistema.clear()

        if not items:
            # Se não houver items, mostra desabilitado
            acao_vazio = QAction("(vazio)", self)
            acao_vazio.setEnabled(False)
            self._menu_sistema.addAction(acao_vazio)
            return

        for tool_name, tool_title in items:
            acao = QAction(tool_title, self)
            acao.setData(tool_name)
            acao.triggered.connect(
                lambda checked, name=tool_name: self.tool_clicked.emit(name)
            )
            self._menu_sistema.addAction(acao)