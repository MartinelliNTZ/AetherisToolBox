# -*- coding: utf-8 -*-
"""
ComplexSelector — Seletor avançado com suporte a file/folder/files/folders.
============================================================================
NÃO usa GridRadio. O comportamento é definido pelos parâmetros:
  - allow_file / allow_folder: quais botões aparecem (🔍 / 📁)
  - multiple: se pode selecionar múltiplos itens
  - selection_mode: modo padrão ("file" ou "folder")
  - mode_type: "input" ou "output"

Lógica central:
  - O widget sempre guarda: root_path (diretório base) + selected_list (itens)
  - 🔍 clicado → seleciona arquivo(s) via ExplorerUtils
  - 📁 clicado → seleciona pasta(s) via ExplorerUtils
  - 📂 (só output) → gera path com ProjectUtil + subfolder + fixed_name
  - 📄 (só input) → ListFileDialog

Uso:
    sel = ComplexSelector(label_text="Entrada:", allow_file=True, allow_folder=True, multiple=False, selection_mode="file")

    sel.get_root_path()      # diretório base
    sel.get_selected_list()  # itens selecionados
    sel.path()               # primeiro item
    sel.path_type()          # "file" | "folder" | "files" | "folders"
"""

from __future__ import annotations

import os
from typing import Callable, Optional

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QWidget, QHBoxLayout, QLabel, QLineEdit

from core.config.LogUtils import LogUtils
from resources.widgets.dialogs.ListFileDialog import ListFileDialog
from resources.widgets.simple.SimpleSecondaryButton import SimpleSecondaryButton
from utils.ExplorerUtils import ExplorerUtils
from utils.ProjectUtil import ProjectUtil


class ComplexSelector(QWidget):
    """
    Seletor avançado com suporte a file/folder/files/folders.

    Diferente do SimpleSelector, NÃO usa GridRadio. O comportamento
    é definido pelos parâmetros allow_file, allow_folder, multiple,
    selection_mode e mode_type na criação.

    O widget sempre armazena:
      - root_path: diretório base da seleção
      - selected_list: lista de itens selecionados (paths completos)
    """

    def __init__(
        self,
        label_text: str = "",
        default_path: str = "",
        placeholder: str = "Caminho...",
        tooltip: str = "",
        file_filter: str = "Todos (*.*)",
        label_width: int = 130,
        # ── Controle de modo ──
        allow_file: bool = True,
        allow_folder: bool = False,
        multiple: bool = False,
        selection_mode: str = "file",   # "file" | "folder"
        # ── Controle de botões ──
        show_suggest_button: bool = False,
        show_project_button: bool = False,
        suggested_path: str = "",
        # ── Output config ──
        mode_type: str = "input",  # "input" | "output"
        fixed_name: str = "",
        subfolder: str = "",
        parent=None,
    ):
        super().__init__(parent)

        # Validação
        if not allow_file and not allow_folder:
            allow_file = True

        # Sanitiza selection_mode
        if selection_mode not in ("file", "folder"):
            selection_mode = "file"
        if selection_mode == "folder" and not allow_folder:
            selection_mode = "file"
        if selection_mode == "file" and not allow_file:
            selection_mode = "folder"

        self._file_filter = file_filter
        self._allow_file = allow_file
        self._allow_folder = allow_folder
        self._multiple = multiple
        self._selection_mode = selection_mode
        self._show_suggest_button = show_suggest_button
        self._show_project_button = show_project_button
        self._suggested_rel_path: str = suggested_path
        self._mode_type = mode_type
        self._fixed_name = fixed_name
        self._subfolder = subfolder

        # Estado interno
        self._root_path: str = ""
        self._selected_list: list[str] = []

        # Logger
        self._logger = LogUtils(tool="ComplexSelector", class_name="ComplexSelector")

        # Callbacks públicos
        self.on_path_change = None    # callback(paths: list[str])
        self.on_browse_click = None   # callback()
        self.on_suggest_click = None  # callback()

        # Constrói UI
        self._build_ui(label_text, placeholder, tooltip, label_width)

        # Se default_path foi passado, inicializa
        if default_path:
            self.set_path(default_path)

    # ══════════════════════════════════════════════════════════════════
    # UI
    # ══════════════════════════════════════════════════════════════════

    def _build_ui(self, label_text, placeholder, tooltip, label_width):
        """Constrói o layout."""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        # Label
        self._label = QLabel(label_text)
        self._label.setFixedWidth(label_width)
        if tooltip:
            self._label.setToolTip(tooltip)
        layout.addWidget(self._label)

        # QLineEdit (sempre read-only)
        self._edit = QLineEdit()
        self._edit.setPlaceholderText(placeholder)
        if tooltip:
            self._edit.setToolTip(tooltip)
        self._edit.setReadOnly(True)
        layout.addWidget(self._edit, 1)

        # Botões
        self._add_buttons(layout)

        # Atualiza display
        self._update_display()

    def _add_buttons(self, layout):
        """Adiciona botões conforme configuração."""
        # ── 🔍 (file) ──
        if self._allow_file:
            self._btn_file = SimpleSecondaryButton("🔍")
            self._btn_file.setFixedWidth(32)
            self._btn_file.setToolTip(
                "Selecionar arquivos" if self._multiple else "Selecionar arquivo"
            )
            self._btn_file.clicked.connect(self._browse_file)
            layout.addWidget(self._btn_file)

        # ── 📁 (folder) ──
        if self._allow_folder:
            self._btn_folder = SimpleSecondaryButton("📁")
            self._btn_folder.setFixedWidth(32)
            self._btn_folder.setToolTip(
                "Selecionar pastas" if self._multiple else "Selecionar pasta"
            )
            self._btn_folder.clicked.connect(self._browse_folder)
            layout.addWidget(self._btn_folder)

        # ── 📂 (suggested — só output) ──
        if self._mode_type == "output" and self._show_suggest_button:
            self._btn_suggest = SimpleSecondaryButton("📂")
            self._btn_suggest.setFixedWidth(30)
            self._btn_suggest.setToolTip("Usar pasta do projeto")
            self._btn_suggest.clicked.connect(self._on_suggest_clicked)
            layout.addWidget(self._btn_suggest)

        # ── 📄 (project — só input) ──
        if self._mode_type == "input" and self._show_project_button:
            self._btn_project = SimpleSecondaryButton("📄")
            self._btn_project.setFixedWidth(30)
            self._btn_project.setToolTip("Selecionar arquivo do projeto")
            self._btn_project.clicked.connect(self._on_project_clicked)
            layout.addWidget(self._btn_project)

    # ══════════════════════════════════════════════════════════════════
    # Display
    # ══════════════════════════════════════════════════════════════════

    def _update_display(self):
        """Atualiza o QLineEdit conforme o estado atual."""
        if not self._selected_list:
            self._edit.setText("")
            return

        if not self._multiple:
            # Mostra o path completo
            self._edit.setText(self._selected_list[0])
        else:
            # Mostra contagem
            count = len(self._selected_list)
            if count == 0:
                self._edit.setText("Nenhum item selecionado")
            elif count == 1:
                self._edit.setText("1 item selecionado")
            else:
                self._edit.setText(f"{count} itens selecionados")

    # ══════════════════════════════════════════════════════════════════
    # Handlers de busca
    # ══════════════════════════════════════════════════════════════════

    def _browse_file(self):
        """Busca arquivo(s) — disparado pelo 🔍.
        Em modo input: usa open_file/open_files.
        Em modo output: usa save_file.
        """
        self._logger.info("🔍 clicado", code="COMPLEX_FILE_CLICKED")
        if self.on_browse_click:
            self.on_browse_click()

        initial_dir = ExplorerUtils.resolve_initial_dir(
            self._root_path or (self._selected_list[0] if self._selected_list else "")
        )

        if self._mode_type == "output":
            # Output: diálogo de salvar
            path = ExplorerUtils.save_file(
                "Salvar arquivo", initial_dir, self._file_filter, self,
            )
            if path:
                self._root_path = os.path.dirname(path)
                self._selected_list = [path]
                self._update_display()
                self._emit_path_change()
        elif self._multiple:
            paths = ExplorerUtils.open_files(
                "Selecionar arquivos", initial_dir, self._file_filter, self,
            )
            if paths:
                self._root_path = os.path.dirname(paths[0]) if paths else ""
                self._selected_list = list(paths)
                self._update_display()
                self._emit_path_change()
        else:
            path = ExplorerUtils.open_file(
                "Selecionar arquivo", initial_dir, self._file_filter, self,
            )
            if path:
                self._root_path = os.path.dirname(path)
                self._selected_list = [path]
                self._update_display()
                self._emit_path_change()

    def _browse_folder(self):
        """Busca pasta(s) — disparado pelo 📁."""
        self._logger.info("📁 clicado", code="COMPLEX_FOLDER_CLICKED")
        if self.on_browse_click:
            self.on_browse_click()

        initial_dir = ExplorerUtils.resolve_initial_dir(
            self._root_path or (self._selected_list[0] if self._selected_list else "")
        )

        if self._multiple:
            paths = ExplorerUtils.select_directories(
                "Selecionar pastas", initial_dir, self,
            )
            if paths:
                self._root_path = paths[0] if paths else ""
                self._selected_list = list(paths)
                self._update_display()
                self._emit_path_change()
        else:
            path = ExplorerUtils.select_directory(
                "Selecionar pasta", initial_dir, self,
            )
            if path:
                self._root_path = path
                self._selected_list = [path]
                self._update_display()
                self._emit_path_change()

    # ══════════════════════════════════════════════════════════════════
    # 📄 (project — só input)
    # ══════════════════════════════════════════════════════════════════

    def _on_project_clicked(self):
        """Abre ListFileDialog com as extensões do filtro."""
        self._logger.info("📄 clicado", code="COMPLEX_PROJECT_CLICKED")

        root_folder = ProjectUtil.get_root_folder()
        if not root_folder:
            self._logger.warning("Nenhum projeto ativo", code="COMPLEX_NO_PROJECT")
            return

        extensions = self._parse_extensions_from_filter(self._file_filter)
        if not extensions:
            self._logger.warning("Nenhuma extensão extraída", code="COMPLEX_NO_EXT")
            return

        dialog = ListFileDialog(
            extensions=extensions,
            multi_select=self._multiple,
            parent=self,
        )
        if dialog.exec():
            paths = dialog.selected_paths
            if paths:
                self._root_path = os.path.dirname(paths[0]) if paths else ""
                self._selected_list = list(paths)
                self._update_display()
                self._emit_path_change()

    @staticmethod
    def _parse_extensions_from_filter(file_filter: str) -> list[str]:
        """Extrai extensões de um filtro de arquivo."""
        import re
        match = re.search(r'\(([^)]+)\)', file_filter)
        if not match:
            return []
        parts = match.group(1).split()
        exts = [p.strip().lower() for p in parts if p.startswith("*")]
        return [e.replace("*", "") for e in exts if e.replace("*", "")]

    # ══════════════════════════════════════════════════════════════════
    # 📂 (suggested — só output)
    # ══════════════════════════════════════════════════════════════════

    def _on_suggest_clicked(self):
        """
        Gera path de saída: ProjectUtil.get_root_folder() + subfolder + fixed_name.
        Ex: C:/projeto/lasvectorconverter/lasvectorconverted.gpkg
        """
        self._logger.info("📂 clicado (output)", code="COMPLEX_SUGGEST_CLICKED")
        if self.on_suggest_click:
            self.on_suggest_click()

        root_folder = ProjectUtil.get_root_folder()
        if not root_folder:
            self._logger.warning("Nenhum projeto ativo", code="COMPLEX_NO_PROJECT")
            return

        if self._subfolder:
            output_dir = os.path.join(root_folder, self._subfolder)
        else:
            output_dir = root_folder

        if self._fixed_name:
            output_path = os.path.join(output_dir, self._fixed_name)
        else:
            output_path = output_dir

        self._root_path = output_dir
        self._selected_list = [output_path]
        self._update_display()
        self._emit_path_change()

        self._logger.info(
            f"Output: {output_path}",
            code="COMPLEX_SUGGEST_PATH",
            root=root_folder,
            subfolder=self._subfolder,
            fixed_name=self._fixed_name,
        )

    # ══════════════════════════════════════════════════════════════════
    # Callback
    # ══════════════════════════════════════════════════════════════════

    def _emit_path_change(self):
        """Dispara callback de path change."""
        if self.on_path_change:
            self.on_path_change(self._selected_list)

    # ══════════════════════════════════════════════════════════════════
    # API Pública
    # ══════════════════════════════════════════════════════════════════

    def get_root_path(self) -> str:
        """Retorna o diretório base da seleção."""
        return self._root_path

    def get_selected_list(self) -> list[str]:
        """Retorna a lista de itens selecionados (paths completos)."""
        return self._selected_list.copy()

    def get_paths(self) -> list[str]:
        """Atalho para get_selected_list()."""
        return self.get_selected_list()

    def get_path(self, index: int = 0) -> str:
        """Retorna um path específico pelo índice."""
        if 0 <= index < len(self._selected_list):
            return self._selected_list[index]
        return ""

    def path(self) -> str:
        """Retorna o primeiro path (compatível com SimpleSelector)."""
        return self.get_path(0)

    def paths(self) -> list[str]:
        """Retorna lista de paths (compatível com SimpleSelector)."""
        return self.get_paths()

    def path_type(self) -> str:
        """
        Retorna o tipo do modo atual baseado em selection_mode e multiple:
        - single + file  → "file"
        - single + folder → "folder"
        - multi + file   → "files"
        - multi + folder → "folders"
        """
        if self._multiple:
            return f"{self._selection_mode}s"
        return self._selection_mode

    def path_count(self) -> int:
        """Número de paths selecionados."""
        return len(self._selected_list)

    def is_multi(self) -> bool:
        return self._multiple

    def is_single(self) -> bool:
        return not self._multiple

    def is_folder_mode(self) -> bool:
        return self._selection_mode == "folder"

    def is_file_mode(self) -> bool:
        return self._selection_mode == "file"

    def set_path(self, path: str):
        """Define um path único."""
        if path:
            self._root_path = os.path.dirname(path) if os.path.isfile(path) else path
            self._selected_list = [path]
        else:
            self._root_path = ""
            self._selected_list = []
        self._update_display()
        self._emit_path_change()

    def set_paths(self, paths: list[str]):
        """Define múltiplos paths."""
        if paths:
            first = paths[0]
            self._root_path = os.path.dirname(first) if os.path.isfile(first) else first
            self._selected_list = list(paths)
        else:
            self._root_path = ""
            self._selected_list = []
        self._update_display()
        self._emit_path_change()

    def clear(self):
        """Limpa tudo."""
        self._root_path = ""
        self._selected_list = []
        self._update_display()
        self._emit_path_change()

    def exists(self) -> bool:
        p = self.path()
        return bool(p) and os.path.exists(p)

    def is_file(self) -> bool:
        p = self.path()
        return bool(p) and os.path.isfile(p)

    def is_dir(self) -> bool:
        p = self.path()
        return bool(p) and os.path.isdir(p)

    def basename(self) -> str:
        return os.path.basename(self.path())

    def dirname(self) -> str:
        return os.path.dirname(self.path())

    def extension(self) -> str:
        return os.path.splitext(self.path())[1].lower()

    def has_extension(self, *exts: str) -> bool:
        if not self._selected_list:
            return False
        ext = self.extension()
        return any(ext == e.lower() for e in exts)

    # ── Configuração ────────────────────────────────────────────────

    def set_suggested_path(self, suggested_rel_path: str):
        """Define o path relativo para o botão 📂."""
        self._suggested_rel_path = suggested_rel_path

    def set_suggested_callback(self, callback: Callable[[], None], tooltip: str = ""):
        """Define callback personalizado para 📂."""
        if hasattr(self, '_btn_suggest'):
            try:
                self._btn_suggest.clicked.disconnect()
            except TypeError:
                pass
            self._btn_suggest.clicked.connect(callback)
            if tooltip:
                self._btn_suggest.setToolTip(tooltip)

    @property
    def file_filter(self) -> str:
        return self._file_filter

    @file_filter.setter
    def file_filter(self, value: str) -> None:
        self._file_filter = value
        self._logger.info(f"file_filter: '{value}'", code="COMPLEX_FILE_FILTER_CHANGED")

    @property
    def edit(self) -> QLineEdit:
        return self._edit

    @property
    def mode_type(self) -> str:
        return self._mode_type

    @property
    def selection_mode(self) -> str:
        return self._selection_mode

    @selection_mode.setter
    def selection_mode(self, value: str) -> None:
        if value in ("file", "folder"):
            self._selection_mode = value