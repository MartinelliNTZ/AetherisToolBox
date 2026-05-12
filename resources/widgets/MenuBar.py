# -*- coding: utf-8 -*-
"""
MenuBar — Barra de menus do Aetheris ToolBox
==============================================
Exibe dois menus: "Arquivo" (Sair) e "Ajuda" (Sobre).
Utiliza QMenuBar do Qt para o comportamento padrão de menus suspensos.
"""

from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QMenuBar, QMenu
from PySide6.QtGui import QAction


class MenuBar(QMenuBar):
    """
    Barra de menus com Arquivo e Ajuda.

    Sinais:
        sair_clicked  — emitido quando usuário clica em Arquivo > Sair
        sobre_clicked — emitido quando usuário clica em Ajuda > Sobre
    """

    sair_clicked = Signal()
    sobre_clicked = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("app_menu_bar")
        self._build_menus()

    def _build_menus(self):
        # ── Menu Arquivo ────────────────────────────────────────────
        menu_arquivo = QMenu("Arquivo", self)
        acao_sair = QAction("Sair", self)
        acao_sair.triggered.connect(self.sair_clicked)
        menu_arquivo.addAction(acao_sair)
        self.addMenu(menu_arquivo)

        # ── Menu Ajuda ──────────────────────────────────────────────
        menu_ajuda = QMenu("Ajuda", self)
        acao_sobre = QAction("Sobre", self)
        acao_sobre.triggered.connect(self.sobre_clicked)
        menu_ajuda.addAction(acao_sobre)
        self.addMenu(menu_ajuda)