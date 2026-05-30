# -*- coding: utf-8 -*-
"""
SimpleSelector — Linha com label, QLineEdit e botão "..." para selecionar arquivo/pasta.
Uso: campo de caminho único com seletor embutido.

QFileDialog é PROIBIDO fora de utils/ExplorerUtils.
SimpleSelector usa ExplorerUtils para todas as operações de seleção.
"""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QWidget, QHBoxLayout, QLabel, QLineEdit, QPushButton

from resources.widgets.SimpleGhostButton import SimpleGhostButton
from utils.ExplorerUtils import ExplorerUtils


class SimpleSelector(QWidget):
    """
    Linha com label, QLineEdit editável e botão "..." que abre explorador.

    Tipos de seleção (browse_mode):
        "open_file"    — 1 arquivo (leitura)
        "open_files"   — múltiplos arquivos (leitura)
        "save_file"    — 1 arquivo (salvar)
        "directory"    — 1 pasta
        "directories"  — múltiplas pastas

    Suporta suggested_path: str opcional. Se informado, um botão "📂" é
    adicionado ao lado do "..." que insere o caminho sugerido no QLineEdit.

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
        suggested_path: str = "",
        parent=None,
    ):
        super().__init__(parent)

        self._file_filter = file_filter
        self._browse_mode = browse_mode

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

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

        # ── Botão de Sugestão (ao lado do "...") ──
        if suggested_path:
            self._btn_suggest = SimpleGhostButton("📂")
            self._btn_suggest.setToolTip(f"Usar: {suggested_path}")
            self._btn_suggest.setFixedWidth(30)
            self._btn_suggest.clicked.connect(lambda: self.set_path(suggested_path))
            layout.addWidget(self._btn_suggest)

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
        # resolve_initial_dir trata:
        #   - diretório existente → retorna ele mesmo
        #   - arquivo existente   → retorna diretório pai
        #   - inválido/vazio      → retorna "" (abre em recentes)
        initial_dir = ExplorerUtils.resolve_initial_dir(current)

        if self._browse_mode == "save_file":
            path = ExplorerUtils.save_file(
                "Salvar arquivo", initial_dir, self._file_filter, self,
            )
            if path:
                self.edit.setText(path)

        elif self._browse_mode == "open_files":
            paths = ExplorerUtils.open_files(
                "Selecionar arquivos", initial_dir, self._file_filter, self,
            )
            if paths:
                self.edit.setText("; ".join(paths))

        elif self._browse_mode == "directories":
            path = ExplorerUtils.select_directory(
                "Selecionar pasta", initial_dir, self,
            )
            if path:
                self.edit.setText(path)

        else:  # "directory" ou "open_file"
            if self._browse_mode == "directory":
                path = ExplorerUtils.select_directory(
                    "Selecionar pasta", initial_dir, self,
                )
            else:
                path = ExplorerUtils.open_file(
                    "Selecionar arquivo", initial_dir, self._file_filter, self,
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