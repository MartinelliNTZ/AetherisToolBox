# -*- coding: utf-8 -*-
"""
PreferencesManagerTool — Gerenciador de Preferências do Sistema
=================================================================
Ferramenta que exibe todas as preferências salvas no sistema,
permitindo editar, resetar ou remover itens por ToolKey.

Acessível pelo menu Sistema > Gerenciador de Preferências.
Não aparece na toolbar.
"""

from __future__ import annotations

from typing import Any, Dict

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox,
    QScrollArea, QFrame,
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon

from core.enum.ToolKey import ToolKey
from resources.widgets.SimplePrimaryButton import SimplePrimaryButton
from resources.widgets.SimpleSecondaryButton import SimpleSecondaryButton
from resources.widgets.SimpleDangerButton import SimpleDangerButton
from resources.widgets.PreferenceItemGrid import PreferenceItemGrid
from resources.styles.styles import AppStyles, Palette
from utils.Preferences import Preferences

# ── Configuração das preferências padrão do sistema ──────────────
# Estrutura: { "tool_key": { "pref_key": { "type", "label", "default", ... } } }
# type pode ser: "bool", "float", "int", "text"

SYSTEM_PREF_CONFIG: Dict[str, Dict[str, Any]] = {
    "LogViewer": {
        "search_text": {
            "type": "text",
            "default": "",
            "label": "Texto de Busca",
            "placeholder": "Digite para filtrar...",
        },
        "level_filter": {
            "type": "text",
            "default": "ALL",
            "label": "Filtro de Nível",
        },
    },
    "TecladorF": {
        "value": {
            "type": "text",
            "default": "",
            "label": "Valor",
        },
        "hotkey": {
            "type": "text",
            "default": "f",
            "label": "Tecla de Atalho",
        },
        "startup_delay": {
            "type": "float",
            "default": 0.15,
            "label": "Delay Inicial (s)",
            "min": 0.0,
            "max": 10.0,
            "step": 0.01,
            "decimals": 2,
        },
        "interval_delay": {
            "type": "float",
            "default": 0.01,
            "label": "Intervalo (s)",
            "min": 0.001,
            "max": 5.0,
            "step": 0.001,
            "decimals": 3,
        },
    },
    "System": {
        "side_content_width": {
            "type": "int",
            "default": 400,
            "label": "Largura do Side Panel",
            "min": 100,
            "max": 2000,
        },
        "side_collapsed": {
            "type": "bool",
            "default": True,
            "label": "Side Panel Recolhido",
        },
    },
}


class PreferencesPlugin(QWidget):
    """
    Gerenciador de preferências do sistema.
    Seleciona uma ToolKey e edita os valores salvos.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self._current_section: str = ""
        self._grid: PreferenceItemGrid | None = None
        self._build_ui()

    def _build_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(18, 10, 18, 10)
        main_layout.setSpacing(8)

        # ── Header ──
        header = QLabel("Gerenciador de Preferências")
        header.setObjectName("header_title")
        main_layout.addWidget(header)

        # ── Separator ──
        sep = QFrame()
        sep.setObjectName("separator")
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setFixedHeight(1)
        main_layout.addWidget(sep)

        # ── Seletor de ToolKey ──
        selector_row = QHBoxLayout()
        selector_row.setSpacing(8)

        lbl_sel = QLabel("Ferramenta:")
        lbl_sel.setObjectName("pref_selector_label")
        selector_row.addWidget(lbl_sel)

        self._combo_toolkey = QComboBox()
        self._combo_toolkey.setMinimumWidth(200)
        self._combo_toolkey.setObjectName("pref_combo")
        # Preenche com as ToolKeys que têm config
        self._toolkey_order: list[str] = []
        for key in SYSTEM_PREF_CONFIG:
            self._combo_toolkey.addItem(key, key)
            self._toolkey_order.append(key)
        self._combo_toolkey.currentIndexChanged.connect(self._on_toolkey_changed)
        selector_row.addWidget(self._combo_toolkey, 1)

        selector_row.addStretch()
        main_layout.addLayout(selector_row)

        # ── Action Buttons ──
        actions_row = QHBoxLayout()
        actions_row.setSpacing(6)

        self.btn_save = SimplePrimaryButton("SALVAR")
        self.btn_save.clicked.connect(self._on_save)
        actions_row.addWidget(self.btn_save)

        self.btn_reset = SimpleSecondaryButton("RESETAR PADRÃO")
        self.btn_reset.clicked.connect(self._on_reset)
        actions_row.addWidget(self.btn_reset)

        self.btn_clear_all = SimpleDangerButton("APAGAR TUDO")
        self.btn_clear_all.clicked.connect(self._on_clear_all)
        actions_row.addWidget(self.btn_clear_all)

        actions_row.addStretch()
        main_layout.addLayout(actions_row)

        # ── Grid de Preferências ──
        self._grid_container = QWidget()
        self._grid_layout = QVBoxLayout(self._grid_container)
        self._grid_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(self._grid_container, 1)

        # Carrega a primeira toolkey
        if self._toolkey_order:
            self._current_section = self._toolkey_order[0]
            self._rebuild_grid()

    def _on_toolkey_changed(self, idx: int):
        """Troca a seção de preferências exibida."""
        key = self._combo_toolkey.itemData(idx)
        if not key:
            return
        self._current_section = key
        self._rebuild_grid()

    def _rebuild_grid(self):
        """Recria o PreferenceItemGrid para a seção atual."""
        # Remove grid anterior
        while self._grid_layout.count():
            item = self._grid_layout.takeAt(0)
            w = item.widget()
            if w:
                self._grid_layout.removeWidget(w)
                w.deleteLater()

        config = SYSTEM_PREF_CONFIG.get(self._current_section, {})
        self._grid = PreferenceItemGrid(config, section=self._current_section)
        self._grid_layout.addWidget(self._grid)

    def _on_save(self):
        """Salva todas as preferências da seção atual."""
        if self._grid:
            saved = self._grid.save_values()
            from utils.MessageBox import MessageBox
            MessageBox.show_info(
                text=f"Preferências salvas para '{self._current_section}'.",
                title="Salvo",
            )

    def _on_reset(self):
        """Restaura os valores padrão da seção atual."""
        if self._grid:
            self._grid.reset_values()

    def _on_clear_all(self):
        """Remove todas as preferências da seção atual."""
        if self._grid:
            from utils.MessageBox import MessageBox
            ok = MessageBox.show_question(
                text=f"Tem certeza que deseja apagar todas as preferências de '{self._current_section}'?",
                title="Confirmar",
            )
            if ok:
                self._grid.clear_all()