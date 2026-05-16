# -*- coding: utf-8 -*-
"""
PreferencesManagerTool — Gerenciador de Preferências do Sistema
=================================================================
Ferramenta que exibe todas as preferências salvas no sistema,
permitindo editar, resetar ou remover itens por ToolKey.

Carregamento dinâmico — lê diretamente do preferences.json e
infere tipos automaticamente via Preferences.infer_type().
Não precisa de configuração manual SYSTEM_PREF_CONFIG.

Acessível pelo menu Sistema > Gerenciador de Preferências.
Não aparece na toolbar.
"""

from __future__ import annotations

from typing import Any, Dict

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox,
    QFrame,
)
from PySide6.QtCore import Qt

from resources.widgets.ExecutionButtons import ExecutionButtons
from resources.widgets.PreferenceItemGrid import PreferenceItemGrid
from utils.Preferences import Preferences


def _build_dynamic_config(section: str) -> Dict[str, Any]:
    """
    Constrói um config dinâmico para uma seção a partir do JSON real.
    Usa Preferences.infer_type() para determinar o tipo de cada campo.
    """
    raw = Preferences.all_data().get(section, {})
    config: Dict[str, Any] = {}
    for key, value in raw.items():
        # Pula dicts aninhados complexos (ex: extensoes)
        if isinstance(value, dict):
            continue
        pref_type = Preferences.infer_type(value)
        # Default seguro: se o valor real existe no JSON usa ele, senao 0 ou ""
        safe_default = value if value is not None else (
            0 if pref_type in ("int", "float") else "")
        entry: Dict[str, Any] = {
            "type": pref_type,
            "default": safe_default,
            "label": key.replace("_", " ").title(),
        }
        if pref_type in ("int", "float"):
            entry["min"] = 0
            entry["max"] = 999999
            if pref_type == "float":
                entry["step"] = 0.1
                entry["decimals"] = 2
            else:
                entry["step"] = 1
        config[key] = entry
    return config


class PreferencesPlugin(QWidget):
    """
    Gerenciador de preferências do sistema.
    Carrega dinamicamente todas as seções do preferences.json.
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

        # ── Action Buttons ──
        self._btns = ExecutionButtons(self)
        self._btns.setup({
            "reset": {
                "text": "RESETAR PADRÃO",
                "callback": self._on_reset,
                "type": "secondary",
                "description": "Recarrega valores do disco descartando alterações",
            },
            "clear": {
                "text": "APAGAR TUDO",
                "callback": self._on_clear_all,
                "type": "danger",
                "description": "Remove todas as preferências da seção atual",
            },
            "save": {
                "text": "SALVAR",
                "callback": self._on_save,
                "type": "primary",
                "description": "Salva as preferências da seção atual",
            },
        })
        main_layout.addWidget(self._btns)

        # ── Seletor de ToolKey ──
        selector_row = QHBoxLayout()
        selector_row.setSpacing(8)

        lbl_sel = QLabel("Ferramenta:")
        lbl_sel.setObjectName("pref_selector_label")
        selector_row.addWidget(lbl_sel)

        self._combo_toolkey = QComboBox()
        self._combo_toolkey.setMinimumWidth(200)
        self._combo_toolkey.setObjectName("pref_combo")
        self._combo_toolkey.currentIndexChanged.connect(
            self._on_toolkey_changed)
        selector_row.addWidget(self._combo_toolkey, 1)

        selector_row.addStretch()
        main_layout.addLayout(selector_row)

        # ── Grid de Preferências ──
        self._grid_container = QWidget()
        self._grid_layout = QVBoxLayout(self._grid_container)
        self._grid_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(self._grid_container, 1)

        # Popula combo e carrega primeira
        self._populate_combo()

    def _populate_combo(self):
        """Lê do preferences.json e preenche o combo com todas as seções."""
        self._combo_toolkey.blockSignals(True)
        self._combo_toolkey.clear()

        all_data = Preferences.all_data()
        self._toolkey_order: list[str] = []
        for key in sorted(all_data.keys()):
            # Só mostra seção que tem ao menos um campo não-dict
            section_data = all_data[key]
            if not isinstance(section_data, dict):
                continue
            has_scalar = any(not isinstance(v, dict)
                             for v in section_data.values())
            if not has_scalar:
                continue
            self._combo_toolkey.addItem(key, key)
            self._toolkey_order.append(key)

        self._combo_toolkey.blockSignals(False)

        if self._toolkey_order:
            self._current_section = self._toolkey_order[0]
            self._combo_toolkey.setCurrentIndex(0)
            self._rebuild_grid()

    def _on_toolkey_changed(self, idx: int):
        """Troca a seção de preferências exibida."""
        key = self._combo_toolkey.itemData(idx)
        if not key:
            return
        self._current_section = key
        self._rebuild_grid()

    def _rebuild_grid(self):
        """Recria o PreferenceItemGrid para a seção atual com config dinâmico."""
        # Remove grid anterior
        while self._grid_layout.count():
            item = self._grid_layout.takeAt(0)
            w = item.widget()
            if w:
                self._grid_layout.removeWidget(w)
                w.deleteLater()

        config = _build_dynamic_config(self._current_section)
        self._grid = PreferenceItemGrid(config, section=self._current_section)
        self._grid_layout.addWidget(self._grid)

    def _on_save(self):
        """Salva todas as preferências da seção atual."""
        if self._grid:
            self._grid.save_values()
            from utils.MessageBox import MessageBox
            MessageBox.show_info(
                text=f"Preferências salvas para '{self._current_section}'.",
                title="Salvo",
            )

    def _on_reset(self):
        """Recarrega do JSON descartando alterações não salvas."""
        if self._grid:
            Preferences.all_data()  # força refresh do cache
            self._rebuild_grid()

    def _on_clear_all(self):
        """Remove todas as preferências da seção do JSON inteiro."""
        if self._grid:
            from utils.MessageBox import MessageBox
            ok = MessageBox.show_question(
                text=f"Tem certeza que deseja apagar todas as preferências de '{self._current_section}'?",
                title="Confirmar",
            )
            if ok:
                # Remove a seção inteira do JSON e recria grid vazio
                all_data = Preferences.all_data()
                all_data.pop(self._current_section, None)
                Preferences.save_all(all_data)
                self._populate_combo()
