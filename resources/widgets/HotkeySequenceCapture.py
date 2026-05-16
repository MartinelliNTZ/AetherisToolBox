# -*- coding: utf-8 -*-
"""
HotkeySequenceCapture — Campo de captura de sequência de teclas
=================================================================
Permite capturar uma ou mais teclas/atalhos em sequência.
Cada tecla capturada é adicionada a uma lista exibida com botões
de remover. A sequência completa pode ser recuperada como lista.

Uso:
    from resources.widgets.HotkeySequenceCapture import HotkeySequenceCapture

    capture = HotkeySequenceCapture()
    capture.sequenceChanged.connect(self._on_seq_changed)
    sequence = capture.captured_sequence()  # ["f1", "ctrl+c", "enter"]
    capture.set_captured_sequence(["f", "enter", "del"])
    capture.clear()
"""

from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QFrame,
)

from resources.widgets.HotkeyCaptureLine import HotkeyCaptureLine
from resources.widgets.SimpleGhostButton import SimpleGhostButton
from resources.widgets.SimpleLabel import SimpleLabel


class HotkeySequenceCapture(QWidget):
    """
    Captura uma sequência de teclas/atalhos.

    Comportamento:
    - Exibe um campo HotkeyCaptureLine para capturar a PRÓXIMA tecla
    - Cada tecla capturada é adicionada como item na lista abaixo
    - Cada item tem botão "×" para remover
    - Botão "Limpar" para resetar toda a sequência
    - Clique no campo ou no botão "+" para adicionar a próxima tecla

    Sinais:
        sequenceChanged(list) — emitido quando a sequência muda
    """

    sequenceChanged = Signal(list)

    def __init__(
        self,
        default_keys: list[str] | None = None,
        placeholder: str = "Clique e pressione uma tecla...",
        parent=None,
    ):
        super().__init__(parent)
        self._keys: list[str] = list(default_keys) if default_keys else []
        self._placeholder = placeholder

        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        # ── Linha: [HotkeyCaptureLine] [Adicionar] [Limpar] ──────────
        row = QHBoxLayout()
        row.setSpacing(4)

        self._capture_field = HotkeyCaptureLine(
            default_key="",
            placeholder=self._placeholder,
        )
        self._capture_field.keyChanged.connect(self._on_key_captured)
        self._capture_field.setObjectName("hsc_capture_field")
        row.addWidget(self._capture_field, 1)

        self._btn_add = SimpleGhostButton("+")
        self._btn_add.setToolTip("Adicionar próxima tecla")
        self._btn_add.setObjectName("hsc_btn_add")
        self._btn_add.clicked.connect(self._on_add_clicked)
        row.addWidget(self._btn_add)

        self._btn_clear = SimpleGhostButton("Limpar")
        self._btn_clear.setObjectName("hsc_btn_clear")
        self._btn_clear.clicked.connect(self._on_clear)
        row.addWidget(self._btn_clear)

        layout.addLayout(row)

        # ── Lista de teclas capturadas ──────────────────────────────
        self._list_container = QWidget()
        self._list_container.setObjectName("hsc_list_container")
        self._list_layout = QVBoxLayout(self._list_container)
        self._list_layout.setContentsMargins(0, 2, 0, 2)
        self._list_layout.setSpacing(2)

        # Placeholder quando vazio — SEMPRE presente no layout (índice 0)
        self._empty_label = SimpleLabel("Nenhuma tecla capturada")
        self._empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._empty_label.setObjectName("hsc_empty")
        self._list_layout.addWidget(self._empty_label)

        layout.addWidget(self._list_container, 1)

        self._refresh()

    # ── Ações ────────────────────────────────────────────────────────

    def _on_add_clicked(self):
        """Força o campo a entrar em modo de escuta."""
        self._capture_field.setFocus()
        self._capture_field._on_mouse_press(None)

    def _on_key_captured(self, key_name: str):
        """Callback quando uma tecla é capturada pelo HotkeyCaptureLine."""
        if not key_name:
            return
        self._keys.append(key_name)
        self._refresh()
        self.sequenceChanged.emit(self._keys)

    def _on_clear(self):
        """Limpa toda a sequência."""
        self._keys.clear()
        self._refresh()
        self.sequenceChanged.emit(self._keys)

    def _remove_key(self, index: int):
        """Remove uma tecla da sequência pelo índice."""
        if 0 <= index < len(self._keys):
            self._keys.pop(index)
            self._refresh()
            self.sequenceChanged.emit(self._keys)

    # ── UI Refresh ──────────────────────────────────────────────────

    def _refresh(self):
        """Atualiza a lista visual de teclas capturadas."""
        self._clear_dynamic_items()

        if not self._keys:
            self._empty_label.setVisible(True)
            return

        self._empty_label.setVisible(False)

        # Insere itens antes do empty_label (que é sempre índice 0 no layout)
        for i, key in enumerate(self._keys):
            item_widget = self._create_key_item(key, i)
            insert_pos = self._list_layout.count() - 1  # antes do empty_label
            self._list_layout.insertWidget(insert_pos, item_widget)

    def _clear_dynamic_items(self):
        """
        Remove apenas os widgets dinâmicos (key items),
        preservando o empty_label que está sempre no layout (índice 0).
        """
        idx = self._list_layout.count() - 1
        while idx >= 1:
            item = self._list_layout.takeAt(idx)
            widget = item.widget()
            if widget is not None and widget is not self._empty_label:
                widget.deleteLater()
            idx -= 1

    def _create_key_item(self, key: str, index: int) -> QWidget:
        """Cria um widget de item para uma tecla na lista."""
        from PySide6.QtWidgets import QFrame, QHBoxLayout

        from resources.widgets.SimpleRemoveButton import SimpleRemoveButton
        from resources.widgets.HotkeyCaptureLine import _to_display

        item = QFrame()
        item.setObjectName("hsc_key_item")
        item.setFrameShape(QFrame.Shape.StyledPanel)

        row = QHBoxLayout(item)
        row.setContentsMargins(6, 2, 6, 2)
        row.setSpacing(4)

        # Key name display
        display_name = _to_display(key)
        lbl = QLabel(f"{index + 1}. {display_name}")
        lbl.setObjectName("hsc_key_label")
        row.addWidget(lbl, 1)

        # Remove button
        btn_remove = SimpleRemoveButton()
        btn_remove.setObjectName("hsc_btn_remove")
        btn_remove.setFixedSize(20, 20)
        btn_remove.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_remove.clicked.connect(lambda checked=False, i=index: self._remove_key(i))
        row.addWidget(btn_remove)

        return item

    # ── API Pública ─────────────────────────────────────────────────

    def captured_sequence(self) -> list[str]:
        """Retorna a lista de teclas capturadas."""
        return list(self._keys)

    def set_captured_sequence(self, keys: list[str]):
        """Define programaticamente a sequência de teclas."""
        self._keys = list(keys)
        self._refresh()
        self.sequenceChanged.emit(self._keys)

    def clear(self):
        """Limpa a sequência."""
        self._on_clear()