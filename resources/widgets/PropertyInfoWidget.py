# -*- coding: utf-8 -*-
"""
PropertyInfoWidget — Exibe propriedades básicas de um arquivo
===============================================================
Mostra nome, tamanho, caminho (clicável), diretório, extensão,
datas de criação e modificação.

O widget recebe um dicionário de dados (enriquecido via
BasicExtractor.enrich_json) e exibe os campos selecionados.

Uso:
    widget = PropertyInfoWidget(parent=self)
    widget.load_data({
        "name": "arquivo.txt",
        "size_formatted": "1.2 KB",
        "extension_name": "TXT",
        "path": "c:/pasta/arquivo.txt",
        "directory": "c:/pasta",
        "created": "01/06/2026 12:00:00",
        "modified": "01/06/2026 14:30:00",
    })
"""

from __future__ import annotations

import os
from typing import Any, Dict, Optional
from urllib.parse import quote

from PySide6.QtCore import Qt
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import QFormLayout, QLabel, QVBoxLayout, QWidget

from core.config.LogUtils import LogUtils
from core.enum.ToolKey import ToolKey

_logger = LogUtils(tool=ToolKey.UNTRACEABLE.value, class_name="PropertyInfoWidget")


class PropertyInfoWidget(QWidget):
    """
    Exibe metadados básicos de um arquivo em layout de formulário.
    O caminho do arquivo aparece como link clicável.
    """

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self._file_path = ""

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        # ── Formulário de propriedades ──────────────────────────
        form = QWidget()
        form_layout = QFormLayout(form)
        form_layout.setContentsMargins(0, 0, 0, 0)
        form_layout.setSpacing(6)
        form_layout.setLabelAlignment(Qt.AlignmentFlag.AlignLeft)

        self._name_label = self._add_row("Nome:", form_layout)
        self._size_label = self._add_row("Tamanho:", form_layout)
        self._type_label = self._add_row("Tipo:", form_layout)
        self._path_label = self._add_clickable_path_row("Caminho:", form_layout)
        self._dir_label = self._add_row("Diretório:", form_layout)
        self._created_label = self._add_row("Criado em:", form_layout)
        self._modified_label = self._add_row("Modificado em:", form_layout)

        layout.addWidget(form)
        _logger.info(
            "Formulário de propriedades criado",
            code="PROP_FORM_OK",
            has_parent=parent is not None,
        )

        # ── Seção colapsável ────────────────────────────────────
        from resources.widgets.CollapsibleParams import CollapsibleParams

        self._extra_section = CollapsibleParams(
            title="Informações Avançadas",
            collapsed=True,
            parent=self,
        )
        self._extra_section.content_layout.addWidget(
            QLabel("Configurações adicionais em breve.")
        )
        layout.addWidget(self._extra_section)

        _logger.info(
            "Seção colapsável adicionada ao layout",
            code="COLLAPSE_ADDED",
            layout_count=layout.count(),
        )

    def load_data(self, data: Dict[str, Any]) -> None:
        """
        Carrega dados de um dicionário (enriquecido via BasicExtractor).

        Args:
            data: Dicionário com chaves name, size_formatted, extension_name,
                  path, directory, created, modified.
        """
        _logger.info(
            "Carregando dados no PropertyInfoWidget",
            code="PROP_LOAD_DATA",
            has_name="name" in data,
            has_path="path" in data,
        )

        self._name_label.setText(data.get("name", "—"))
        self._size_label.setText(data.get("size_formatted", "—"))
        self._type_label.setText(data.get("extension_name", "—"))

        file_path = data.get("path", "")
        self._file_path = file_path
        if file_path:
            self._set_clickable_path(file_path)
        else:
            self._path_label.setText("—")

        self._dir_label.setText(data.get("directory", "—"))
        self._created_label.setText(data.get("created", "—"))
        self._modified_label.setText(data.get("modified", "—"))

        _logger.info(
            "Dados carregados no PropertyInfoWidget",
            code="PROP_DATA_DONE",
            file_path=file_path,
        )

    def _add_row(self, label: str, layout: QFormLayout) -> QLabel:
        """Adiciona uma linha label + valor ao layout."""
        value = QLabel("—")
        value.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextSelectableByMouse
        )
        value.setStyleSheet("color: #E5E7EB; font-size: 12px;")
        layout.addRow(f'<span style="color:#A1A1AA;font-size:12px;">{label}</span>', value)
        return value

    def _add_clickable_path_row(self, label: str, layout: QFormLayout) -> QLabel:
        """Adiciona linha de caminho com link clicável."""
        value = QLabel("—")
        value.setTextInteractionFlags(
            Qt.TextInteractionFlag.LinksAccessibleByMouse
        )
        value.setOpenExternalLinks(False)
        value.linkActivated.connect(self._on_path_clicked)
        layout.addRow(f'<span style="color:#A1A1AA;font-size:12px;">{label}</span>', value)
        return value

    def _set_clickable_path(self, file_path: str) -> None:
        """Define o texto HTML do caminho como link clicável."""
        normalized = file_path.replace("\\", "/")
        file_uri = f"file:///{quote(normalized, safe='/:@!$&()*+,;=')}"
        html = (
            f'<a href="{file_uri}" '
            f'style="color:#3B82F6;text-decoration:underline;font-size:12px;">'
            f"{normalized}</a>"
        )
        self._path_label.setText(html)

    def _on_path_clicked(self, url: str) -> None:
        """
        Abre o local do arquivo no Explorer.
        Se for arquivo, seleciona-o (abre a pasta pai com o arquivo selecionado).
        """
        file_path = self._file_path
        if not file_path:
            return

        directory = os.path.dirname(file_path)
        if not directory or not os.path.exists(directory):
            return

        QDesktopServices.openUrl(f"file:///{os.path.normpath(directory).replace(os.sep, '/')}")