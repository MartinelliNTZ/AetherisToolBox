# -*- coding: utf-8 -*-
"""
SimpleSelector — Linha com label, QLineEdit e botão "..." para selecionar arquivo/pasta.
Uso: campo de caminho único com seletor embutido.

QFileDialog é PROIBIDO fora de utils/ExplorerUtils.
SimpleSelector usa ExplorerUtils para todas as operações de seleção.

O botão 📂 (suggested_path) funciona da seguinte forma:
  - O plugin passa um PATH RELATIVO (ex: "vetores/black_points_filter")
  - Quando o botão 📂 é clicado, o SimpleSelector busca o root_folder
    do projeto ativo via ProjectUtil.get_root_folder()
  - Concatena root_folder + path_relativo e insere no QLineEdit
"""

from __future__ import annotations

import os
from typing import Callable, Optional

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QWidget, QHBoxLayout, QLabel, QLineEdit

from core.config.LogUtils import LogUtils
from resources.widgets.SimpleSecondaryButton import SimpleSecondaryButton
from utils.ExplorerUtils import ExplorerUtils
from utils.ProjectUtil import ProjectUtil


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
    adicionado ao lado do "..." que, ao ser clicado, busca o root_folder
    do projeto ativo e concatena com o path relativo recebido.

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
        self._suggested_rel_path: str = ""  # path relativo recebido do plugin

        # Logger para rastreio
        self._logger = LogUtils(tool="SimpleSelector", class_name="SimpleSelector")

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

        # ── Botão "..." (selecionar) ──
        self.btn = SimpleSecondaryButton("...")
        self.btn.setFixedWidth(30)
        self.btn.setToolTip("Selecionar pasta manualmente")
        self.btn.clicked.connect(self._browse)
        layout.addWidget(self.btn)

        # ── Botão de Caminho Padrão (depois do "...") ──
        # Sempre criado e sempre conectado ao callback.
        # Invisível por padrão — fica visível quando set_suggested_path() for chamado.
        self._btn_suggest = SimpleSecondaryButton("📂")
        self._btn_suggest.setFixedWidth(30)
        self._btn_suggest.setVisible(bool(suggested_path))
        self._btn_suggest.clicked.connect(self._on_suggest_clicked)
        if suggested_path:
            self._suggested_rel_path = suggested_path
            self._btn_suggest.setToolTip(f"Usar pasta do projeto: {suggested_path}")
            self._logger.info(
                f"Botão 📂 criado com path relativo: {suggested_path}",
                code="SUGGEST_CREATED",
            )
        else:
            self._btn_suggest.setToolTip("Usar pasta do projeto")
            self._logger.info(
                "Botão 📂 criado sem path relativo inicial",
                code="SUGGEST_CREATED_EMPTY",
            )
        layout.addWidget(self._btn_suggest)

    # ── Lógica do seletor ─────────────────────────────────────────────

    def _browse(self):
        current = self.edit.text().strip()
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

    def _on_suggest_clicked(self):
        """
        Callback do botão 📂.
        Busca o root_folder do projeto ativo e concatena com o path relativo.
        """
        self._logger.info(
            f"Botão 📂 clicado. Path relativo: {self._suggested_rel_path}",
            code="SUGGEST_CLICKED",
        )

        if not self._suggested_rel_path:
            self._logger.warning(
                "Path relativo vazio — botão não fará nada",
                code="SUGGEST_EMPTY",
            )
            return

        # Busca root_folder do projeto ativo
        root_folder = ProjectUtil.get_root_folder()
        self._logger.info(
            f"root_folder obtido: {root_folder}",
            code="SUGGEST_ROOT",
        )

        if not root_folder:
            self._logger.warning(
                "Nenhum projeto ativo (root_folder vazio)",
                code="SUGGEST_NO_PROJECT",
            )
            return

        # Concatena root_folder + path relativo
        full_path = os.path.join(root_folder, self._suggested_rel_path)
        self._logger.info(
            f"Caminho completo gerado: {full_path}",
            code="SUGGEST_PATH",
        )

        self.edit.setText(full_path)

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

    def set_suggested_path(self, suggested_rel_path: str):
        """
        Define o path relativo para o botão 📂.

        O plugin DEVE passar um PATH RELATIVO (ex: "vetores/black_points_filter").
        Quando o botão for clicado, o SimpleSelector busca o root_folder
        do projeto ativo e concatena com este path relativo.

        Se suggested_rel_path for vazio, esconde o botão.
        Se for válido, mostra o botão e atualiza o tooltip.
        """
        self._logger.info(
            f"set_suggested_path chamado com: '{suggested_rel_path}'",
            code="SET_SUGGESTED",
        )

        if suggested_rel_path:
            self._suggested_rel_path = suggested_rel_path
            self._btn_suggest.setToolTip(
                f"Usar pasta do projeto: {suggested_rel_path}"
            )
            self._btn_suggest.setVisible(True)
            self._logger.info(
                f"Botão 📂 ativado com path relativo: {suggested_rel_path}",
                code="SUGGEST_ACTIVATED",
            )
        else:
            self._suggested_rel_path = ""
            self._btn_suggest.setVisible(False)
            self._logger.info(
                "Botão 📂 desativado (path vazio)",
                code="SUGGEST_DEACTIVATED",
            )

    def set_suggested_callback(self, callback: Callable[[], None], tooltip: str = ""):
        """
        Permite que o plugin defina um callback personalizado para o botão 📂,
        em vez do comportamento padrão de buscar o projeto.

        Args:
            callback: Função sem argumentos a ser chamada quando o botão for clicado.
            tooltip: Tooltip opcional para o botão.
        """
        self._logger.info(
            "Callback personalizado registrado para botão 📂",
            code="SUGGEST_CALLBACK",
        )
        try:
            self._btn_suggest.clicked.disconnect()
        except TypeError:
            pass
        self._btn_suggest.clicked.connect(callback)
        if tooltip:
            self._btn_suggest.setToolTip(tooltip)
        self._btn_suggest.setVisible(True)

    def set_path(self, path: str):
        """Define o caminho do QLineEdit."""
        self._logger.info(
            f"set_path chamado: {path[:80]}...",
            code="SET_PATH",
        )
        self.edit.setText(path)

    def clear(self):
        """Limpa o QLineEdit."""
        self._logger.info("clear() chamado", code="CLEAR")
        self.edit.setText("")