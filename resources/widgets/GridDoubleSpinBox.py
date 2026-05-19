# -*- coding: utf-8 -*-
"""
GridDoubleSpinBox — Grade de campos numéricos (QDoubleSpinBox) com labels
==========================================================================
Agrupa múltiplos campos numéricos em um layout de grid, configurados
via dicionário. Suporta inteiros (decimal=0) e floats, valor padrão,
mínimo, máximo, step, tooltip e callback onchanged.

Configuração via dicionário:
    {
        "intervalo": {
            "label": "Intervalo (s)",
            "description": "Intervalo entre execuções",
            "decimal": 1,
            "default": 1.0,
            "min": 0.0,
            "max": 999.0,
            "step": 0.1,
            "prefix": "",      # opcional, texto antes do valor
            "suffix": "s",     # opcional, texto depois do valor
        },
        "repeticoes": {
            "label": "Repetições",
            "description": "Número de vezes",
            "decimal": 0,       # 0 = inteiro (QSpinBox internally)
            "default": 3,
            "min": 1,
            "max": 9999,
        },
    }

Uso:
    grid = GridDoubleSpinBox(config)
    grid.values          # {"intervalo": 1.0, "repeticoes": 3}
    grid.set_values({"intervalo": 2.5})
    grid.get("intervalo")   # 1.0
    grid.set("repeticoes", 5)
    grid.changed.connect(self._on_value_changed)
"""

from __future__ import annotations

from typing import Any, Dict, Optional, Callable

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QWidget, QGridLayout, QLabel, QDoubleSpinBox, QSpinBox,
    QScrollArea, QHBoxLayout, QSizePolicy,
)
from PySide6.QtCore import Signal


class GridDoubleSpinBox(QScrollArea):
    """
    Grade rolável de QDoubleSpinBox configurados por dicionário.

    Sinais:
        changed(key, value) — emitido quando qualquer spin box muda de valor
    """

    changed = Signal(str, float)

    def __init__(
        self,
        config: Dict[str, Dict[str, Any]],
        parent=None,
    ):
        super().__init__(parent)
        self._config = config
        self._spinboxes: Dict[str, QDoubleSpinBox | QSpinBox] = {}

        self.setWidgetResizable(True)
        self.setObjectName("grid_doublespinbox_scroll")

        self._container = QWidget()
        self._container.setObjectName("grid_doublespinbox_container")
        self._grid = QGridLayout(self._container)
        self._grid.setContentsMargins(4, 4, 4, 4)
        self._grid.setSpacing(6)
        self._grid.setColumnStretch(1, 1)
        self.setWidget(self._container)

        self._build()

    def _build(self):
        """Constrói a grade de spin boxes a partir do config."""
        row = 0
        for key, item in self._config.items():
            label_text = item.get("label", key)
            description = item.get("description", "")
            decimal = item.get("decimal", 1)
            default = item.get("default", 0.0)
            min_val = item.get("min", 0.0)
            max_val = item.get("max", 999999.0)
            step = item.get("step", 1.0 if decimal == 0 else 0.01)
            prefix = item.get("prefix", "")
            suffix = item.get("suffix", "")

            # Label
            lbl = QLabel(label_text)
            lbl.setObjectName("grid_dsb_label")
            if description:
                lbl.setToolTip(description)
            self._grid.addWidget(lbl, row, 0, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)

            # Spin box container (value + suffix)
            spin_container = QHBoxLayout()
            spin_container.setContentsMargins(0, 0, 0, 0)
            spin_container.setSpacing(2)

            if decimal == 0:
                # Inteiro — usa QSpinBox
                spin = QSpinBox()
                spin.setRange(int(min_val), int(max_val))
                spin.setValue(int(default))
                spin.setSingleStep(int(step) if step >= 1 else 1)
                spin.setObjectName("grid_spinbox_int")
            else:
                # Float — usa QDoubleSpinBox
                spin = QDoubleSpinBox()
                spin.setRange(float(min_val), float(max_val))
                spin.setValue(float(default))
                spin.setDecimals(decimal)
                spin.setSingleStep(float(step))
                spin.setObjectName("grid_spinbox_float")

            spin.setFixedWidth(100)
            spin.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
            if description:
                spin.setToolTip(description)

            spin.valueChanged.connect(lambda val, k=key: self._on_changed(k, val))
            self._spinboxes[key] = spin
            spin_container.addWidget(spin)

            if suffix:
                suffix_lbl = QLabel(suffix)
                suffix_lbl.setObjectName("grid_dsb_suffix")
                spin_container.addWidget(suffix_lbl)

            if prefix:
                prefix_lbl = QLabel(prefix)
                prefix_lbl.setObjectName("grid_dsb_prefix")
                spin_container.insertWidget(0, prefix_lbl)

            self._grid.addLayout(spin_container, row, 1, Qt.AlignmentFlag.AlignLeft)

            row += 1

        # Preenche final com stretch
        self._grid.setRowStretch(row, 1)

    def _on_changed(self, key: str, value: float):
        """Propaga mudança."""
        # Callback opcional do config
        onchanged = self._config.get(key, {}).get("onchanged")
        if onchanged and callable(onchanged):
            onchanged(value)
        self.changed.emit(key, value)

    # ── Propriedades públicas ────────────────────────────────────────

    @property
    def values(self) -> Dict[str, float]:
        """Retorna dict com todos os valores atuais."""
        result = {}
        for key, spin in self._spinboxes.items():
            result[key] = spin.value()
        return result

    def get(self, key: str) -> float:
        """Retorna o valor de um campo específico."""
        spin = self._spinboxes.get(key)
        if spin is not None:
            return spin.value()
        raise KeyError(f"Campo '{key}' não encontrado no GridDoubleSpinBox")

    def set(self, key: str, value: float, block_signals: bool = False):
        """Define o valor de um campo específico."""
        spin = self._spinboxes.get(key)
        if spin is not None:
            if block_signals:
                spin.blockSignals(True)
            spin.setValue(value)
            if block_signals:
                spin.blockSignals(False)
        else:
            raise KeyError(f"Campo '{key}' não encontrado no GridDoubleSpinBox")

    def set_values(self, values: Dict[str, float], block_signals: bool = True):
        """
        Define múltiplos valores de uma vez.

        Args:
            values: Dict no formato {"key": value}
            block_signals: Se True, emite 'changed' uma única vez no final
        """
        if block_signals:
            for key in self._spinboxes:
                self._spinboxes[key].blockSignals(True)

        for key, value in values.items():
            spin = self._spinboxes.get(key)
            if spin is not None:
                spin.setValue(value)

        if block_signals:
            for key in self._spinboxes:
                self._spinboxes[key].blockSignals(False)
            # Emite uma única vez com o primeiro valor
            keys = list(values.keys())
            if keys:
                self.changed.emit(keys[0], values[keys[0]])