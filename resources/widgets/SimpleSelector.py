# -*- coding: utf-8 -*-
"""
SimpleSelector — Linha com label, QLineEdit e botão "..." para selecionar arquivo/pasta.
Uso: campo de caminho único com seletor embutido.
"""

from __future__ import annotations

import os

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QWidget, QHBoxLayout, QLabel, QLineEdit, QPushButton, QFileDialog


class SimpleSelector(QWidget):
    """
    Linha com label, QLineEdit editável e botão "..." que abre explorador.

    Tipos de seleção (browse_mode):
        "open_file"    — 1 arquivo (leitura)
        "open_files"   — múltiplos arquivos (leitura)
        "save_file"    — 1 arquivo (salvar)
        "directory"    — 1 pasta
        "directories"  — múltiplas pastas

    Uso:
        sel = SimpleSelector("Imagem:", file_filter="GeoTIFF (*.tif *.tiff)",
                             browse_mode="open_file")
        sel.path()  # retorna o caminho atual
        layout.addWidget(sel)
    """

    def __init__(
        self,
        label_text: str = "",
        default_path: str = "",
        placeholder: str = "Caminho...",
        tooltip: str = "",
        file_filter: str = "Todos (*.*)",
        browse_mode: str = "open_file",
        label_width: int = 130,
        parent=None,
    ):
        super().__init__(parent)

        self._file_filter = file_filter
        self._browse_mode = browse_mode

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)

        # ── Label ──
        self.label = QLabel(label_text)
        self.label.setFixedWidth(label_width)
        if tooltip:
            self.label.setToolTip(tooltip)
        layout.addWidget(self.label)

        # ── Line Edit ──
        self.edit = QLineEdit(default_path)
        self.edit.setPlaceholderText(placeholder)
        if tooltip:
            self.edit.setToolTip(tooltip)
        layout.addWidget(self.edit, 1)

        # ── Botão "..." ──
        self.btn = QPushButton("...")
        self.btn.setObjectName("btn_secondary")
        self.btn.setFixedWidth(30)
        self.btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn.clicked.connect(self._browse)
        if tooltip:
            self.btn.setToolTip(tooltip)
        layout.addWidget(self.btn)

    # ── Lógica do seletor ─────────────────────────────────────────────

    def _browse(self):
        current = self.edit.text().strip()
        initial_dir = os.path.dirname(current) if current and os.path.exists(current) else ""

        if self._browse_mode == "save_file":
            path, _ = QFileDialog.getSaveFileName(
                self, "Salvar arquivo", initial_dir, self._file_filter
            )
            if path:
                self.edit.setText(path)

        elif self._browse_mode == "open_files":
            paths, _ = QFileDialog.getOpenFileNames(
                self, "Selecionar arquivos", initial_dir, self._file_filter
            )
            if paths:
                self.edit.setText("; ".join(paths))

        elif self._browse_mode == "directories":
            path = QFileDialog.getExistingDirectory(
                self, "Selecionar pasta", initial_dir
            )
            if path:
                self.edit.setText(path)

        else:  # "directory" ou "open_file"
            if self._browse_mode == "directory":
                path = QFileDialog.getExistingDirectory(
                    self, "Selecionar pasta", initial_dir
                )
            else:
                path, _ = QFileDialog.getOpenFileName(
                    self, "Selecionar arquivo", initial_dir, self._file_filter
                )
            if path:
                self.edit.setText(path)

    # ── Getters / Setters ─────────────────────────────────────────────

    def path(self) -> str:
        """Retorna o caminho atual (primeiro, se multi)."""
        text = self.edit.text().strip()
        if ";" in text:
            return text.split(";")[0].strip()
        return text

    def paths(self) -> list[str]:
        """Retorna lista de caminhos."""
        text = self.edit.text().strip()
        if not text:
            return []
        return [p.strip() for p in text.split(";")]

    def set_path(self, path: str):
        """Define o caminho do QLineEdit."""
        self.edit.setText(path)

    def clear(self):
        """Limpa o QLineEdit."""
        self.edit.setText("")