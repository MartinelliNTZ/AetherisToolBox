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
"""

from __future__ import annotations

import os
from typing import Optional

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

        self._build(specs, title, columns)

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

        # Se dynamic_parent, registra para monitoramento
        if dynamic_parent and parent_key:
            self._dynamic_children[label] = parent_key
            self._connect_dynamic_listener(label, parent_key)

        # Botão USAR ORIGEM para outputs com parent
        btn_container: Optional[QWidget] = None
        if mode_type == "output" and parent_key:
            btn_container = self._create_origin_button(label, parent_key)

        # Conecta listener reativo de path
        if mode_type == "output" and parent_key:
            self._connect_parent_listener(label, parent_key)

        return selector, btn_container

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

    def _connect_parent_listener(self, label: str, parent_key: str):
        """Conecta callback do parent para reatividade ao mudar path."""
        parent_selector = self._selectors.get(parent_key)
        if not parent_selector:
            return

        selector = self._selectors[label]

        def on_parent_changed(parent_paths: list[str]):
            if self._self_generated.get(label, False) or not selector.get_paths():
                self._generate_output(label, parent_paths)

        parent_selector.on_path_change = on_parent_changed

    # ══════════════════════════════════════════════════════════════════
    # Dynamic Parent — adapta selection_mode do filho conforme o pai
    # ══════════════════════════════════════════════════════════════════

    def _connect_dynamic_listener(self, child_label: str, parent_key: str):
        """
        Conecta listener no parent para adaptar o filho dinamicamente.
        Quando o parent muda de tipo:
          - file (1 arquivo) → filho vira file (ignora fixed_name)
          - folder/files/folders → filho vira folder
        """
        parent_selector = self._selectors.get(parent_key)
        if not parent_selector:
            return

        def on_parent_browse(parent_paths: list[str]):
            self._apply_dynamic_mode(child_label)

        # Conecta no browse (qualquer clique de botão)
        parent_selector.on_browse_click = lambda: None
        # Usa o path_change para aplicar dinâmica
        parent_selector.on_path_change = self._make_dynamic_handler(child_label)

    def _make_dynamic_handler(self, child_label: str):
        """Factory para criar handler de path_change que aplica dinâmica."""
        def handler(paths: list[str]):
            self._apply_dynamic_mode(child_label)
        return handler

    def _apply_dynamic_mode(self, child_label: str):
        """
        Aplica o modo dinâmico no filho baseado no estado atual do parent.
        - parent file (1 arquivo) → filho file, ignora fixed_name
        - parent folder/files/folders → filho folder
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
            child_selector.selection_mode = "file"
            # Atualiza visibilidade dos botões (já está no ComplexSelector)
        else:
            # Parent é folder/files/folders → filho vira folder
            child_selector.selection_mode = "folder"

        # Atualiza o edit com hint do modo
        if child_selector.is_folder_mode():
            child_selector.edit.setPlaceholderText("Usar pasta do parent")
        else:
            child_selector.edit.setPlaceholderText("Arquivo de saída")

        # Esconde o botão 📂 se não fizer sentido com o modo atual
        if hasattr(child_selector, '_btn_suggest') and child_selector._btn_suggest.isVisible():
            # 📂 sempre visível (gera fixed_name dentro do root do projeto)
            pass

    # ══════════════════════════════════════════════════════════════════
    # Lógica de linking (USAR ORIGEM)
    # ══════════════════════════════════════════════════════════════════

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
            # Se dynamic e parent é 1 arquivo, ignora fixed_name? Não, usa fixed_name
            if dynamic and parent_selector.path_type() == "file" and parent_selector.path_count() == 1:
                # Dynamic file → usa fixed_name normalmente
                pass

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

        self._logger.info(
            f"Output gerado '{label}': {selector.path()}",
            code="GRID_OUTPUT_GENERATED",
        )

    # ══════════════════════════════════════════════════════════════════
    # Métodos de erro visual
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

        # Aplica borda vermelha usando cor do tema
        from resources.styles.ThemeManager import ct
        error_color = ct.theme.COLOR_DANGER
        edit.setStyleSheet(
            f"QLineEdit {{ border: 2px solid {error_color}; "
            f"border-radius: {ct.theme.RADIUS_SM}px; "
            f"background-color: {ct.theme.SURFACE_2}; "
            f"color: {ct.theme.TEXT_MEDIUM}; "
            f"padding: 2px 6px; }}"
        )
        edit.setToolTip(f"⚠ {message}")

        # Se duration > 0, limpa após o tempo
        if duration_ms > 0:
            from PySide6.QtCore import QTimer
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