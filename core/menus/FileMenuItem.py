# -*- coding: utf-8 -*-
"""
FileMenuItem — Aba "Arquivo" da barra de menus
================================================
Itens: Sair
Herda de BaseMenuItem e expõe sinal sair_clicked.
"""

from __future__ import annotations

from PySide6.QtCore import Signal

from core.menus.BaseMenuItem import BaseMenuItem


class FileMenuItem(BaseMenuItem):
    """
    Menu "Arquivo" — ações relacionadas a arquivo/abertura/saída.

    Sinais:
        sair_clicked — emitido quando o usuário clica em "Sair"
    """

    sair_clicked = Signal()

    def __init__(self, parent=None):
        super().__init__("Arquivo", parent)
        self._build_actions()

    def _build_actions(self):
        """Constrói a lista de ações do menu Arquivo."""
        self.add_action(
            text="Sair",
            callback=self._on_sair,
            data="sair",
        )

    def _on_sair(self):
        """Propaga o clique em Sair."""
        self.sair_clicked.emit()