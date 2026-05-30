# -*- coding: utf-8 -*-
"""
FileMenuItem — Aba "Arquivo" da barra de menus
================================================
Itens: Novo, Abrir, Salvar como, Sair

Responsabilidades:
    - Novo: Limpa o projeto atual e emite project_changed
    - Abrir: Abre diálogo para selecionar .mtl, carrega nas prefs, emite project_changed
    - Salvar como: Abre diálogo para criar novo .mtl, salva nas prefs, emite project_changed
    - Sair: Fecha a aplicação

Uso:
    file_item = FileMenuItem()
    file_item.novo_clicked.connect(minha_funcao)
    file_item.abrir_clicked.connect(minha_funcao)
    file_item.salvar_como_clicked.connect(minha_funcao)
    file_item.sair_clicked.connect(minha_funcao)
"""

from __future__ import annotations

import os

from PySide6.QtCore import Signal

from core.enum.ToolKey import ToolKey
from core.menus.BaseMenuItem import BaseMenuItem


class FileMenuItem(BaseMenuItem):
    """
    Menu "Arquivo" — ações de gerenciamento de projeto.

    Sinais:
        novo_clicked       — emitido quando o usuário clica em "Novo"
        abrir_clicked      — emitido quando o usuário clica em "Abrir"
        salvar_como_clicked — emitido quando o usuário clica em "Salvar como"
        sair_clicked       — emitido quando o usuário clica em "Sair"
    """

    novo_clicked = Signal()
    abrir_clicked = Signal()
    salvar_como_clicked = Signal()
    sair_clicked = Signal()

    def __init__(self, parent=None):
        super().__init__("Arquivo", parent)
        self._build_actions()

    def _build_actions(self):
        """Constrói a lista de ações do menu Arquivo."""
        self.add_action(
            text="Novo",
            callback=self._on_novo,
            data="novo",
        )
        self.add_action(
            text="Abrir",
            callback=self._on_abrir,
            data="abrir",
        )
        self.add_action(
            text="Salvar como",
            callback=self._on_salvar_como,
            data="salvar_como",
        )
        self.add_separator()
        self.add_action(
            text="Sair",
            callback=self._on_sair,
            data="sair",
        )

    # ── Handlers ────────────────────────────────────────────────────

    def _on_novo(self):
        """Propaga o clique em Novo."""
        self.novo_clicked.emit()

    def _on_abrir(self):
        """Propaga o clique em Abrir."""
        self.abrir_clicked.emit()

    def _on_salvar_como(self):
        """Propaga o clique em Salvar como."""
        self.salvar_como_clicked.emit()

    def _on_sair(self):
        """Propaga o clique em Sair."""
        self.sair_clicked.emit()