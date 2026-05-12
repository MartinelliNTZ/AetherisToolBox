# -*- coding: utf-8 -*-
"""
MenuBar — Barra de menus do Aetheris ToolBox
==============================================
Exibe dois menus: "Arquivo" (Sair) e "Ajuda" (Sobre).
Estilizado com Palette do sistema.
"""

from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QMenuBar, QMenu
from PySide6.QtGui import QAction

from resources.styles.styles import Palette


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
        self._apply_style()
        self._build_menus()

    def _apply_style(self):
        p = Palette
        self.setStyleSheet(f"""
            QMenuBar#app_menu_bar {{
                background-color: {p.TITLE_BAR_BG};
                border-bottom: 1px solid {p.BORDER};
                padding: 0;
                font-size: 13px;
                color: {p.TEXT_SECONDARY};
            }}
            QMenuBar::item {{
                background-color: transparent;
                color: {p.TEXT_SECONDARY};
                padding: 4px 12px;
                border-radius: 4px;
                margin: 2px 0;
            }}
            QMenuBar::item:selected {{
                background-color: {p.BG_CARD};
                color: {p.TEXT_GOLD};
            }}
            QMenuBar::item:pressed {{
                background-color: {p.BG_ELEVATED};
                color: {p.TEXT_GOLD_BRIGHT};
            }}
            QMenu {{
                background-color: {p.BG_CARD};
                border: 1px solid {p.BORDER};
                border-radius: 6px;
                padding: 4px;
            }}
            QMenu::item {{
                background-color: transparent;
                color: {p.TEXT_PRIMARY};
                padding: 6px 24px;
                border-radius: 4px;
                font-size: 12px;
            }}
            QMenu::item:selected {{
                background-color: {p.GOLD};
                color: {p.BG_DEEPEST};
                font-weight: 700;
            }}
            QMenu::separator {{
                height: 1px;
                background-color: {p.DIVIDER};
                margin: 4px 8px;
            }}
        """)

    def _build_menus(self):
        # Menu Arquivo
        menu_arquivo = QMenu("Arquivo", self)
        acao_sair = QAction("Sair", self)
        acao_sair.triggered.connect(self.sair_clicked)
        menu_arquivo.addAction(acao_sair)
        self.addMenu(menu_arquivo)

        # Menu Ajuda
        menu_ajuda = QMenu("Ajuda", self)
        acao_sobre = QAction("Sobre", self)
        acao_sobre.triggered.connect(self.sobre_clicked)
        menu_ajuda.addAction(acao_sobre)
        self.addMenu(menu_ajuda)