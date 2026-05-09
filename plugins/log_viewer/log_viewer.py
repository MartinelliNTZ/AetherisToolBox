# -*- coding: utf-8 -*-
"""
LogViewerTool — Visualizador de logs do Aetheris ToolBox
==========================================================
Exibe todos os eventos de log em uma tabela com suporte a:
- Pesquisa por texto (filtra em tempo real)
- Filtro por nivel (DEBUG, INFO, WARNING, ERROR, CRITICAL)
- Ordenacao por coluna (clique no cabecalho)
- Botao Refresh para recarregar os arquivos de log

Uso:
    from plugins.log_viewer.log_viewer import LogViewerTool
    widget = LogViewerTool()
"""

from __future__ import annotations

from pathlib import Path
from typing import List

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QLineEdit, QComboBox, QPushButton, QHeaderView, QLabel, QAbstractItemView,
)
from PySide6.QtGui import QColor, QIcon


class LogViewerTool(QWidget):
    """
    Visualizador de logs com tabela, pesquisa e filtro.

    Layout:
      [Barra de ferramentas: campo busca | combo nivel | botao Refresh]
      [Tabela: timestamp | level | tool | class | message | code]
    """

    # Colunas da tabela
    COLUMNS = ["timestamp", "level", "tool", "class", "message", "code"]

    # Cores para cada nivel (background da celula level)
    LEVEL_COLORS = {
        "DEBUG": QColor("#F3F4F6"),      # cinza claro
        "INFO": QColor("#D1FAE5"),       # verde claro
        "WARNING": QColor("#FEF3C7"),    # amarelo claro
        "ERROR": QColor("#FEE2E2"),      # vermelho claro
        "CRITICAL": QColor("#FECACA"),   # vermelho mais forte
    }

    def __init__(self, parent=None):
        super().__init__(parent)
        self._raw_events: List[dict] = []
        self._sort_column: str = "timestamp"
        self._sort_ascending: bool = False
        self._build_ui()
        self._load_and_refresh()

    # ═════════════════════════════════════════════════════════════════════
    # Construcao da UI
    # ═════════════════════════════════════════════════════════════════════

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(6)

        # ── Barra de ferramentas ──────────────────────────────────────
        toolbar = QHBoxLayout()
        toolbar.setSpacing(8)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Pesquisar nos logs...")
        self.search_input.textChanged.connect(self._on_filter_changed)
        toolbar.addWidget(self.search_input, 1)

        self.level_combo = QComboBox()
        self.level_combo.addItems(["ALL", "DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"])
        self.level_combo.currentTextChanged.connect(self._on_filter_changed)
        toolbar.addWidget(self.level_combo)

        self.refresh_btn = QPushButton("Refresh")
        self.refresh_btn.clicked.connect(self._load_and_refresh)
        toolbar.addWidget(self.refresh_btn)

        layout.addLayout(toolbar)

        # ── Tabela ────────────────────────────────────────────────────
        self.table = QTableWidget()
        self.table.setColumnCount(len(self.COLUMNS))
        self.table.setHorizontalHeaderLabels(self.COLUMNS)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.table.setAlternatingRowColors(True)
        self.table.verticalHeader().setVisible(False)
        self.table.setSortingEnabled(False)  # manual

        # Configurar cabecalho para ordenacao ao clicar
        header = self.table.horizontalHeader()
        header.setSectionsClickable(True)
        header.setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        header.sectionClicked.connect(self._on_header_clicked)

        # Ajustar largura inicial
        header.resizeSection(0, 180)  # timestamp
        header.resizeSection(1, 80)   # level
        header.resizeSection(2, 100)  # tool
        header.resizeSection(3, 120)  # class
        header.resizeSection(4, 400)  # message (esticar)
        header.resizeSection(5, 100)  # code
        header.setStretchLastSection(True)

        layout.addWidget(self.table, 1)

        # ── Label de status ───────────────────────────────────────────
        self.status_label = QLabel("Carregando...")
        layout.addWidget(self.status_label)

    # ═════════════════════════════════════════════════════════════════════
    # Carregamento e renderizacao
    # ═════════════════════════════════════════════════════════════════════

    def _load_and_refresh(self) -> None:
        """Recarrega todos os arquivos .json de log/ e atualiza a tabela."""
        from core.config.LogFilter import LogFilter

        self._raw_events = LogFilter.load_all()
        self._render_table()
        self.status_label.setText(
            f"{len(self._raw_events)} evento(s) carregado(s) "
            f"de {self._count_log_files()} arquivo(s)"
        )

    def _count_log_files(self) -> int:
        """Conta quantos arquivos .json existem em log/."""
        log_dir = Path(__file__).resolve().parent.parent.parent / "log"
        if not log_dir.is_dir():
            return 0
        return sum(1 for p in log_dir.iterdir() if p.suffix.lower() == ".json")

    def _render_table(self) -> None:
        """Aplica filtros atuais, ordena e preenche a tabela."""
        from core.config.LogFilter import LogFilter

        events = self._raw_events

        # Filtro por texto
        search_text = self.search_input.text()
        if search_text:
            events = LogFilter.filter_text(events, search_text)

        # Filtro por nivel
        level = self.level_combo.currentText()
        if level != "ALL":
            events = LogFilter.filter_level(events, level)

        # Ordenacao
        events = LogFilter.sort(events, self._sort_column, self._sort_ascending)

        # Preencher tabela
        self.table.setRowCount(len(events))

        for row, event in enumerate(events):
            for col, col_name in enumerate(self.COLUMNS):
                value = event.get(col_name, "")
                if isinstance(value, dict):
                    value = str(value)
                if value is None:
                    value = ""

                item = QTableWidgetItem(str(value))
                item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)

                # Cor de fundo para coluna level
                if col_name == "level":
                    color = self.LEVEL_COLORS.get(str(value).upper())
                    if color:
                        item.setBackground(color)

                self.table.setItem(row, col, item)

        # Atualizar status
        filtered = len(events)
        total = len(self._raw_events)
        if filtered != total:
            self.status_label.setText(
                f"{filtered} de {total} evento(s) (filtrado)"
            )

    # ═════════════════════════════════════════════════════════════════════
    # Eventos
    # ═════════════════════════════════════════════════════════════════════

    def _on_filter_changed(self) -> None:
        """Chamado quando o texto de busca ou combo de nivel muda."""
        self._render_table()

    def _on_header_clicked(self, logical_index: int) -> None:
        """
        Chamado quando o usuario clica no cabecalho de uma coluna.
        Alterna a ordenacao: se ja esta ordenando por esta coluna,
        inverte a direcao; caso contrario, ordena ASC primeiro.
        """
        col_name = self.COLUMNS[logical_index]

        if self._sort_column == col_name:
            # Inverte direcao
            self._sort_ascending = not self._sort_ascending
        else:
            # Nova coluna: ASC primeiro
            self._sort_column = col_name
            self._sort_ascending = True

        self._render_table()