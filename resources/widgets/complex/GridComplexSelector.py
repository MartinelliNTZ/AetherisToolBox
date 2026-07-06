# -*- coding: utf-8 -*-
"""
GridComplexSelector — Grade de ComplexSelectors configurados por dicionário,
com suporte a linking entre selectores e dynamic_parent.

Uso:
    grid = GridComplexSelector({
        "Entrada": {
            "file_filter": "LAS/LAZ (*.las *.laz)",
            "mode_type": "input",
            "allow_file": True,
            "allow_folder": True,
            "multiple": False,
            "show_project_button": True,
        },
        "Saída": {
            "mode_type": "output",
            "parent": "Entrada",
            "dynamic_parent": True,    # Segue modo do parent
            "allow_file": True,        # Modo file
            "allow_folder": True,      # Modo folder
            "fixed_name": "resultado.gpkg",  # Ignorado se dynamic_parent ativo com folder
            "show_suggest_button": True,
        },
    })

    grid["Entrada"].path()
    grid["Entrada"].get_root_path()
    grid["Entrada"].path_type()
    grid.use_origin("Saída")

    # Para plugins que precisam reagir a mudanças nas entradas:
    # (GridComplexSelector gerencia parent-child internamente)
    grid.set_on_input_changed(meu_callback)  # callback(label, paths)
    # Ou para um selector específico:
    grid.set_on_changed("Entrada", meu_callback)  # callback(paths)
"""

from __future__ import annotations

import os
from typing import Callable, Optional

from PySide6.QtWidgets import (
    QWidget, QGridLayout, QVBoxLayout, QHBoxLayout, QLineEdit,
)
from PySide6.QtCore import QTimer

from resources.widgets.GroupPainel import GroupPainel
from resources.widgets.complex.ComplexSelector import ComplexSelector
from resources.widgets.simple.SimpleSecondaryButton import SimpleSecondaryButton
from resources.styles.AppStyles import AppStyles

from core.config.LogUtils import LogUtils


class GridComplexSelector(QWidget):
    """
    Grade de ComplexSelectors configurados por dicionário.

    Suporta mode_type="input"/"output" com parent linking.
    dynamic_parent: filho adapta selection_mode conforme o pai.

    Para plugins que precisam de callback quando o path de um selector mudar,
    use set_on_path_change(label, callback) — isso NÃO quebra o chaining
    interno de linking/dynamic_parent.
    """

    _KEYS_RESERVED = frozenset({
        "label_text", "parent", "mode_type",
        "dynamic_parent", "suffix", "extension",
    })

    def __init__(
        self,
        specs: dict[str, dict],
        title: Optional[str] = None,
        columns: int = 1,
        parent=None,
    ):
        super().__init__(parent)

        self._logger = LogUtils(tool="GridComplexSelector", class_name="GridComplexSelector")

        self._selectors: dict[str, ComplexSelector] = {}
        self._link_meta: dict[str, dict] = {}
        self._origin_buttons: dict[str, SimpleSecondaryButton] = {}
        self._self_generated: dict[str, bool] = {}
        self._dynamic_children: dict[str, str] = {}  # child_label -> parent_label
        # Armazena callbacks registrados via set_on_path_change()
        self._user_callbacks: dict[str, Optional[Callable]] = {}
        # Flag para evitar loop de regeneração
        self._generating_output: set[str] = set()

        self._build(specs, title, columns)

    # ══════════════════════════════════════════════════════════════════
    # API Pública para Callbacks (simplificada — plugin não precisa
    # saber de parent-child relationships)
    # ══════════════════════════════════════════════════════════════════

    def set_on_input_changed(self, callback: Optional[Callable[[str, list[str]], None]]):
        """
        Registra callback para quando QUALQUER selector de entrada mudar.

        O GridComplexSelector descobre automaticamente quais selectores
        são entradas (mode_type != "output") e conecta o callback a todos.
        O plugin NÃO precisa saber de parent-child relationships.

        Args:
            callback: Função que recebe (label, paths).
                     label → nome do selector que mudou (ex: "Entrada 1")
                     paths → list[str] com os paths selecionados.
                     Passe None para limpar todos os callbacks de entrada.
        """
        for label, selector in self._selectors.items():
            meta = self._link_meta.get(label, {})
            if meta.get("mode_type") == "output":
                continue  # Pula outputs
            # Embrulha o callback para que o wrapper (que só passa paths)
            # consiga chamar corretamente com (label, paths)
            if callback is not None:
                self._user_callbacks[label] = lambda paths, _label=label: callback(_label, paths)
            else:
                self._user_callbacks[label] = None
            if not getattr(selector, '_grid_wrapper_installed', False):
                self._install_user_callback_wrapper(label, selector)

    def set_on_changed(self, label: str, callback: Optional[Callable[[list[str]], None]]):
        """
        Registra callback para quando o path de um selector específico mudar.

        Diferente de fazer grid[label].on_path_change = callback diretamente,
        este método NÃO quebra o chaining interno de linking/dynamic_parent.
        O callback será chamado APÓS a lógica interna do GridComplexSelector.

        Args:
            label: Nome do selector (ex: "Entrada").
            callback: Função que recebe list[str] com os paths.
                     Passe None para limpar o callback.
        """
        self._user_callbacks[label] = callback
        selector = self._selectors.get(label)
        if selector and not getattr(selector, '_grid_wrapper_installed', False):
            self._install_user_callback_wrapper(label, selector)

    def _install_user_callback_wrapper(self, label: str, selector: ComplexSelector):
        """Instala um wrapper em on_path_change que preserva o chaining."""
        original_cb = selector.on_path_change

        def wrapper(paths: list[str]):
            # 1. Chama o wrapper de linking se existir (instalado pelo Grid)
            if original_cb:
                original_cb(paths)
            # 2. Chama o callback do usuário DEPOIS da lógica interna
            user_cb = self._user_callbacks.get(label)
            if user_cb and user_cb is not original_cb:
                # Se for set_on_input_changed, passa (label, paths)
                # Se for set_on_changed, passa só paths
                user_cb(paths)

        selector.on_path_change = wrapper
        selector._grid_wrapper_installed = True  # type: ignore[attr-defined]

    # ══════════════════════════════════════════════════════════════════
    # Build
    # ══════════════════════════════════════════════════════════════════

    def _build(self, specs: dict[str, dict], title: Optional[str], columns: int):
        if title:
            container = GroupPainel(title)
            outer = QVBoxLayout(self)
            outer.setContentsMargins(0, 0, 0, 0)
            outer.setSpacing(0)
            outer.addWidget(container)
            inner = container.group_layout
        else:
            inner = QVBoxLayout(self)
            inner.setContentsMargins(0, 0, 0, 0)
            inner.setSpacing(6)

        inner.setSpacing(6)
        inner.setContentsMargins(6, 6, 6, 6)

        if columns <= 1:
            for label, kwargs in specs.items():
                self._create_selector_row(inner, label, kwargs)
        else:
            grid = QGridLayout()
            grid.setSpacing(6)
            grid.setContentsMargins(6, 6, 6, 6)
            for i, (label, kwargs) in enumerate(specs.items()):
                row = i // columns
                col = i % columns
                selector, btn_container = self._build_selector_row(label, kwargs)
                grid.addWidget(selector, row * 2, col)
                if btn_container:
                    grid.addWidget(btn_container, row * 2 + 1, col)
            grid_wrapper = QWidget()
            grid_wrapper.setLayout(grid)
            inner.addWidget(grid_wrapper)

    def _create_selector_row(self, parent_layout, label: str, kwargs: dict):
        selector, btn_container = self._build_selector_row(label, kwargs)
        parent_layout.addWidget(selector)
        if btn_container:
            parent_layout.addWidget(btn_container)

    def _build_selector_row(self, label: str, kwargs: dict):
        """Constrói um ComplexSelector + botão USAR ORIGEM (se necessário)."""
        mode_type = kwargs.get("mode_type", "input")
        parent_key = kwargs.get("parent", "")
        dynamic_parent = kwargs.get("dynamic_parent", False)

        # Extrai parâmetros de linking
        suffix = kwargs.get("suffix", "")
        extension = kwargs.get("extension", "")
        subfolder = kwargs.get("subfolder", "")
        fixed_name = kwargs.get("fixed_name", "")

        # Remove chaves reservadas
        clean_kwargs = {
            k: v for k, v in kwargs.items()
            if k not in self._KEYS_RESERVED
        }

        if "label_text" not in clean_kwargs:
            clean_kwargs["label_text"] = label

        # Se for output com parent, set mode_type
        if mode_type == "output" and parent_key:
            clean_kwargs["mode_type"] = "output"
            if subfolder:
                clean_kwargs["subfolder"] = subfolder
            if fixed_name:
                clean_kwargs["fixed_name"] = fixed_name
            # Output sempre mostra 📂
            clean_kwargs["show_suggest_button"] = True

        selector = ComplexSelector(parent=self, **clean_kwargs)
        self._selectors[label] = selector

        # Armazena metadados de linking
        if parent_key:
            self._link_meta[label] = {
                "parent": parent_key,
                "suffix": suffix,
                "extension": extension,
                "subfolder": subfolder,
                "mode_type": mode_type,
                "fixed_name": fixed_name,
                "dynamic_parent": dynamic_parent,
            }
            self._self_generated[label] = False

        # Se for output com parent, instala listener unificado
        # (substitui _connect_dynamic_listener + _connect_parent_listener)
        if mode_type == "output" and parent_key:
            self._connect_output_listener(label, parent_key, dynamic_parent)

        # Botão USAR ORIGEM para outputs com parent
        btn_container: Optional[QWidget] = None
        if mode_type == "output" and parent_key:
            btn_container = self._create_origin_button(label, parent_key)

        return selector, btn_container

    # ══════════════════════════════════════════════════════════════════
    # Listener Unificado (Item 3: substitui os dois listeners separados)
    # ══════════════════════════════════════════════════════════════════

    def _connect_output_listener(self, child_label: str, parent_key: str, dynamic_parent: bool = False):
        """
        Único listener para output com parent.
        Substitui _connect_dynamic_listener + _connect_parent_listener.

        Instala um wrapper no on_path_change do parent que:
          1. Chama callback do usuário (se registrado via set_on_path_change)
          2. Aplica modo dinâmico (se dynamic_parent)
          3. Gera novo output automaticamente
        """
        parent_selector = self._selectors.get(parent_key)
        if not parent_selector:
            return

        child_selector = self._selectors.get(child_label)
        if not child_selector:
            return

        # Salva callback original (pode ser de outra chamada ou None)
        # IMPORTANTE: se o plugin já registrou via set_on_path_change,
        # esse callback original é do wrapper do usuário, não o raw
        original_cb = parent_selector.on_path_change

        def unified_handler(paths: list[str]):
            # 1. Chama callback original (wrapper do usuário ou None)
            if original_cb:
                original_cb(paths)

            # 2. Se dynamic_parent, aplica modo no filho
            if dynamic_parent:
                self._apply_dynamic_mode(child_label)

            # 3. Gera output se necessário
            if child_label not in self._generating_output:
                should_generate = (
                    self._self_generated.get(child_label, False)
                    or not child_selector.get_paths()
                )
                if should_generate:
                    self._generate_output(child_label, paths)

        parent_selector.on_path_change = unified_handler

    # ══════════════════════════════════════════════════════════════════
    # Dynamic Parent — adapta selection_mode do filho conforme o pai
    # ══════════════════════════════════════════════════════════════════

    def _apply_dynamic_mode(self, child_label: str):
        """
        Aplica o modo dinâmico no filho baseado no estado atual do parent.
        - parent file (1 arquivo) → filho: allow_file=True, allow_folder=False
        - parent folder/files/folders → filho: allow_file=False, allow_folder=True
        """
        meta = self._link_meta.get(child_label)
        if not meta:
            return

        parent_key = meta.get("parent", "")
        parent_selector = self._selectors.get(parent_key)
        child_selector = self._selectors.get(child_label)

        if not parent_selector or not child_selector:
            return

        parent_type = parent_selector.path_type()
        parent_count = parent_selector.path_count()

        # Determina modo do filho
        if parent_type == "file" and parent_count == 1:
            # Parent é 1 arquivo → filho vira file (permite salvar outro arquivo)
            child_selector.set_mode(allow_file=True, allow_folder=False, selection_mode="file")
            child_selector.edit.setPlaceholderText("Arquivo de saída")
        else:
            # Parent é folder/files/folders → filho vira folder
            child_selector.set_mode(allow_file=False, allow_folder=True, selection_mode="folder")
            child_selector.edit.setPlaceholderText("Pasta de saída")

        self._logger.info(
            f"Dynamic mode aplicado: '{child_label}' → "
            f"file={child_selector.allow_file}, folder={child_selector.allow_folder}, "
            f"mode={child_selector.selection_mode}",
            code="GRID_DYNAMIC_APPLIED",
        )

    # ══════════════════════════════════════════════════════════════════
    # Lógica de linking (USAR ORIGEM)
    # ══════════════════════════════════════════════════════════════════

    def _create_origin_button(self, label: str, parent_key: str) -> QWidget:
        container = QWidget()
        h_layout = QHBoxLayout(container)
        h_layout.setContentsMargins(0, 0, 0, 2)
        h_layout.setSpacing(4)

        h_layout.addStretch(1)

        btn = SimpleSecondaryButton("USAR ORIGEM")
        self._origin_buttons[label] = btn
        h_layout.addWidget(btn)

        btn.clicked.connect(lambda: self._on_use_origin(label))

        return container

    def _on_use_origin(self, label: str):
        meta = self._link_meta.get(label)
        if not meta:
            self._logger.warning(
                f"'{label}' não tem metadados de linking",
                code="GRID_NO_LINK_META",
            )
            return

        parent_key = meta["parent"]
        parent_selector = self._selectors.get(parent_key)
        if not parent_selector:
            self._logger.warning(
                f"Parent '{parent_key}' não encontrado",
                code="GRID_PARENT_NOT_FOUND",
            )
            return

        parent_paths = parent_selector.get_paths()
        if not parent_paths:
            self._logger.warning(
                f"Parent '{parent_key}' vazio",
                code="GRID_PARENT_EMPTY",
            )
            return

        self._generate_output(label, parent_paths)
        self._self_generated[label] = True

    def _generate_output(self, label: str, parent_paths: list[str]):
        """Gera path de output baseado no parent."""
        if label in self._generating_output:
            return  # Evita recursão
        self._generating_output.add(label)

        try:
            meta = self._link_meta.get(label)
            if not meta:
                return

            parent_selector = self._selectors.get(meta["parent"])
            if not parent_selector:
                return

            selector = self._selectors[label]
            parent_path = parent_paths[0] if parent_paths else ""

            if not parent_path:
                return

            parent_dir = os.path.dirname(parent_path) if os.path.isfile(parent_path) else parent_path
            subfolder = meta.get("subfolder", "")
            fixed_name = meta.get("fixed_name", "")
            dynamic = meta.get("dynamic_parent", False)

            parent_type = parent_selector.path_type()
            parent_count = parent_selector.path_count()

            # ── Dynamic mode: decide comportamento baseado no parent ──
            if dynamic:
                if parent_type == "file" and parent_count == 1:
                    # 1 arquivo → output = dirname/subfolder/fixed_name
                    if subfolder:
                        output_path = os.path.join(parent_dir, subfolder, fixed_name)
                    else:
                        output_path = os.path.join(parent_dir, fixed_name)
                    selector.set_path(output_path)
                    selector.set_mode(allow_file=True, allow_folder=False, selection_mode="file")
                    selector.edit.setPlaceholderText("Arquivo de saída")
                else:
                    # folder/files/folders → output = parent_path/subfolder (ignora fixed_name)
                    if subfolder:
                        output_path = os.path.join(parent_path, subfolder)
                    else:
                        output_path = os.path.join(parent_path, "converted")
                    selector.set_path(output_path)
                    selector.set_mode(allow_file=False, allow_folder=True, selection_mode="folder")
                    selector.edit.setPlaceholderText("Pasta de saída")
            else:
                # ── Modo normal (sem dynamic) ──
                if parent_selector.is_folder_mode():
                    # Modo pasta: output = parent_path / subfolder
                    if subfolder:
                        output_path = os.path.join(parent_path, subfolder)
                    else:
                        output_path = os.path.join(parent_path, "converted")
                    selector.set_path(output_path)
                    selector.selection_mode = "folder"
                else:
                    # Modo file/files: output = dirname / subfolder / fixed_name
                    if subfolder:
                        output_path = os.path.join(parent_dir, subfolder, fixed_name)
                    else:
                        output_path = os.path.join(parent_dir, fixed_name)
                    selector.set_path(output_path)
                    selector.selection_mode = "file"

                # Atualiza hint
                if selector.is_folder_mode():
                    selector.edit.setPlaceholderText("Pasta de saída")
                else:
                    selector.edit.setPlaceholderText("Arquivo de saída")

            # Marca como auto-gerado (Item 7.2: setar _self_generated)
            self._self_generated[label] = True

            self._logger.info(
                f"Output gerado '{label}': {selector.path()} "
                f"(dynamic={dynamic}, mode={selector.selection_mode})",
                code="GRID_OUTPUT_GENERATED",
            )
        finally:
            self._generating_output.discard(label)

    # ══════════════════════════════════════════════════════════════════
    # Métodos de erro visual  (Item 2: removido import ct)
    # ══════════════════════════════════════════════════════════════════

    def show_error(self, label: str, message: str, duration_ms: int = 3000):
        """
        Exibe erro visual no selector (borda vermelha + tooltip).
        Usa AppStyles para estilização consistente com o tema.

        Args:
            label: Chave do selector.
            message: Mensagem de erro.
            duration_ms: Tempo em ms antes de limpar (0 = permanente).
        """
        selector = self._selectors.get(label)
        if not selector:
            return

        edit = selector.edit
        if not edit:
            return

        # Salva stylesheet original
        if not hasattr(edit, '_saved_stylesheet'):
            edit._saved_stylesheet = edit.styleSheet()

        # Aplica borda vermelha usando AppStyles (Item 2: sem import ct)
        colors = AppStyles.theme_colors()
        error_color = colors.get("COLOR_DANGER", "#FF4444")
        radius = colors.get("RADIUS_SM", 4)
        surface_2 = colors.get("SURFACE_2", "#2D2D2D")
        text_medium = colors.get("TEXT_MEDIUM", "#CCCCCC")

        edit.setStyleSheet(
            f"QLineEdit {{ border: 2px solid {error_color}; "
            f"border-radius: {radius}px; "
            f"background-color: {surface_2}; "
            f"color: {text_medium}; "
            f"padding: 2px 6px; }}"
        )
        edit.setToolTip(f"⚠ {message}")

        # Se duration > 0, limpa após o tempo (Item 5: QTimer já importado)
        if duration_ms > 0:
            QTimer.singleShot(duration_ms, lambda: self._clear_error(edit))

    def _clear_error(self, edit: QLineEdit):
        """Limpa o estilo de erro de um QLineEdit."""
        if hasattr(edit, '_saved_stylesheet'):
            edit.setStyleSheet(edit._saved_stylesheet)
        else:
            edit.setStyleSheet("")

    # ══════════════════════════════════════════════════════════════════
    # API Pública
    # ══════════════════════════════════════════════════════════════════

    def get(self, label: str) -> Optional[ComplexSelector]:
        return self._selectors.get(label)

    def __getitem__(self, label: str) -> ComplexSelector:
        return self._selectors[label]

    def __contains__(self, label: str) -> bool:
        return label in self._selectors

    def items(self):
        return self._selectors.items()

    def selectors(self) -> dict[str, ComplexSelector]:
        return self._selectors.copy()

    def paths(self) -> dict[str, str]:
        return {label: sel.path() for label, sel in self._selectors.items()}

    def all_paths(self) -> list[str]:
        return [sel.path() for sel in self._selectors.values() if sel.path()]

    def get_input(self) -> dict[str, ComplexSelector]:
        inputs = {}
        for label, sel in self._selectors.items():
            meta = self._link_meta.get(label, {})
            if meta.get("mode_type") != "output":
                inputs[label] = sel
        return inputs

    def get_output(self) -> dict[str, ComplexSelector]:
        outputs = {}
        for label, sel in self._selectors.items():
            meta = self._link_meta.get(label, {})
            if meta.get("mode_type") == "output":
                outputs[label] = sel
        return outputs

    def use_origin(self, label: str):
        self._on_use_origin(label)

    def use_origin_all(self):
        for label in self._origin_buttons:
            self._on_use_origin(label)

    def refresh_links(self):
        for label, meta in self._link_meta.items():
            parent_key = meta["parent"]
            parent_selector = self._selectors.get(parent_key)
            if parent_selector and parent_selector.get_paths():
                self._generate_output(label, parent_selector.get_paths())

    def has_linked(self, label: str) -> bool:
        return label in self._link_meta

    def get_parent_of(self, label: str) -> Optional[str]:
        meta = self._link_meta.get(label)
        return meta.get("parent") if meta else None

    def is_dynamic(self, label: str) -> bool:
        """Verifica se um selector tem dynamic_parent ativo."""
        meta = self._link_meta.get(label, {})
        return meta.get("dynamic_parent", False)