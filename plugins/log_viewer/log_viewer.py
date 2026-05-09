# -*- coding: utf-8 -*-
"""
LogViewerTool — Visualizador de logs do Aetheris ToolBox
==========================================================
Exibe todos os eventos de log em uma tabela com suporte a:
- Pesquisa por texto (filtra em tempo real)
- Filtro por nivel (DEBUG, INFO, WARNING, ERROR, CRITICAL)
- Ordenacao por coluna (clique no cabecalho)
- Selecao multipla (CTRL / SHIFT)
- Copiar filtro ou selecao para clipboard
- Duplo clique abre dialog de detalhes
- Cores de fonte via ColorProvider (tool, class, level)
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
    QLineEdit, QComboBox, QPushButton, QHeaderView, QLabel,
    QAbstractItemView, QDialog, QTextEdit, QVBoxLayout as QVBoxDialog,
    QHBoxLayout as QHBoxDialog, QApplication,
)
from PySide6.QtGui import QColor, QIcon, QBrush, QFont


class LogDetailDialog(QDialog):
    """
    Dialog de detalhes de um evento de log.
    Exibe todos os campos em formato texto selecionavel.
    """

    def __init__(self, event: dict, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Detalhes do Evento")
        self.setMinimumSize(600, 400)
        self.setWindowFlags(
            Qt.WindowType.Dialog |
            Qt.WindowType.WindowCloseButtonHint |
            Qt.WindowType.WindowStaysOnTopHint
        )
        self._build_ui(event)

    def _build_ui(self, event: dict) -> None:
        from utils.ColorProvider import ColorProvider

        layout = QVBoxDialog(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(8)

        # Monta texto formatado com todas as chaves do evento
        lines: List[str] = []
        for key, value in event.items():
            if isinstance(value, dict):
                value = str(value)
            if value is None:
                value = ""
            lines.append(f"{key}: {value}")

        text_content = "\n".join(lines)

        self.text_edit = QTextEdit()
        self.text_edit.setPlainText(text_content)
        self.text_edit.setReadOnly(False)  # permite selecionar e copiar
        self.text_edit.setStyleSheet(f"""
            QTextEdit {{
                background-color: #0C0C0F;
                color: {ColorProvider.text_primary()};
                border: 1px solid #1A1A20;
                border-radius: 6px;
                padding: 12px;
                font-family: 'Consolas', 'Courier New', monospace;
                font-size: 13px;
                selection-background-color: #C9A84C;
                selection-color: #08080A;
            }}
        """)
        layout.addWidget(self.text_edit, 1)

        # Botoes
        btn_layout = QHBoxDialog()
        btn_layout.addStretch()

        from resources.widgets.buttons import SimpleGhostButton

        copy_btn = SimpleGhostButton("Copiar Tudo")
        copy_btn.clicked.connect(self._copy_all)
        btn_layout.addWidget(copy_btn)

        close_btn = SimpleGhostButton("Fechar")
        close_btn.clicked.connect(self.accept)
        btn_layout.addWidget(close_btn)

        layout.addLayout(btn_layout)

        # Aplica tema escuro no dialog
        self.setStyleSheet(f"""
            QDialog {{
                background-color: #121216;
                color: {ColorProvider.text_primary()};
            }}
        """)

    def _copy_all(self) -> None:
        """Copia todo o texto para a clipboard."""
        QApplication.clipboard().setText(self.text_edit.toPlainText())


class LogViewerTool(QWidget):
    """
    Visualizador de logs com tabela, pesquisa e filtro.

    Layout:
      [Barra de ferramentas: campo busca | combo nivel | Export Filter | Export Select | Refresh]
      [Tabela: timestamp | level | tool | class | message | code]
    """

    # Colunas da tabela
    COLUMNS = ["timestamp", "level", "tool", "class", "message", "code"]

    def __init__(self, parent=None):
        super().__init__(parent)
        self._raw_events: List[dict] = []
        self._filtered_events: List[dict] = []
        self._sort_column: str = "timestamp"
        self._sort_ascending: bool = False
        self._build_ui()
        self._restore_preferences()
        self._load_and_refresh()

    def _restore_preferences(self) -> None:
        """Carrega as preferencias salvas (search_text, level_filter)."""
        from utils.Preferences import Preferences

        prefs = Preferences(section="LogViewer")

        search_text = prefs.get("search_text", "")
        if search_text:
            self.search_input.setText(search_text)

        level_filter = prefs.get("level_filter", "ALL")
        index = self.level_combo.findText(level_filter)
        if index >= 0:
            self.level_combo.setCurrentIndex(index)

    def _save_preferences(self) -> None:
        """Salva as preferencias atuais (search_text, level_filter)."""
        from utils.Preferences import Preferences

        prefs = Preferences(section="LogViewer")
        prefs.set("search_text", self.search_input.text())
        prefs.set("level_filter", self.level_combo.currentText())
        prefs.save()

    # ═════════════════════════════════════════════════════════════════════
    # Construcao da UI
    # ═════════════════════════════════════════════════════════════════════

    def _build_ui(self) -> None:
        from utils.ColorProvider import ColorProvider
        from resources.widgets.buttons import SimpleGhostButton

        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(6)

        # ── Barra de ferramentas unica ───────────────────────────────
        toolbar = QHBoxLayout()
        toolbar.setSpacing(6)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Pesquisar nos logs...")
        self.search_input.textChanged.connect(self._on_filter_changed)
        toolbar.addWidget(self.search_input, 1)

        self.level_combo = QComboBox()
        self.level_combo.addItems(["ALL", "DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"])
        self.level_combo.currentTextChanged.connect(self._on_filter_changed)
        toolbar.addWidget(self.level_combo)

        self.export_filter_btn = SimpleGhostButton("Exportar Filtro")
        self.export_filter_btn.setToolTip(
            "Copia para clipboard todos os eventos filtrados (TSV)"
        )
        self.export_filter_btn.clicked.connect(self._export_filter)
        toolbar.addWidget(self.export_filter_btn)

        self.export_selection_btn = SimpleGhostButton("Exportar Selecao")
        self.export_selection_btn.setToolTip(
            "Copia para clipboard as celulas selecionadas (TSV)"
        )
        self.export_selection_btn.clicked.connect(self._export_selection)
        toolbar.addWidget(self.export_selection_btn)

        self.refresh_btn = SimpleGhostButton("Refresh")
        self.refresh_btn.clicked.connect(self._load_and_refresh)
        toolbar.addWidget(self.refresh_btn)

        layout.addLayout(toolbar)

        # ── Tabela ────────────────────────────────────────────────────
        self.table = QTableWidget()
        self.table.setColumnCount(len(self.COLUMNS))
        self.table.setHorizontalHeaderLabels(self.COLUMNS)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectItems)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.table.setAlternatingRowColors(True)
        self.table.verticalHeader().setVisible(False)
        self.table.setSortingEnabled(False)  # manual

        self.table.cellDoubleClicked.connect(self._on_cell_double_clicked)

        # Cores do tema escuro para a tabela
        self.table.setStyleSheet(f"""
            QTableWidget {{
                background-color: #0C0C0F;
                alternate-background-color: #121216;
                border: none;
                border-radius: 8px;
                gridline-color: #1A1A20;
                color: {ColorProvider.text_primary()};
            }}
            QTableWidget::item:selected {{
                background-color: #24242B;
                color: #F0F0F0;
            }}
            QHeaderView::section {{
                background-color: #18181D;
                color: #888890;
                padding: 4px 6px;
                border: none;
                border-bottom: 2px solid #C9A84C;
                font-weight: 700;
                font-size: 11px;
                letter-spacing: 0.3px;
            }}
        """)

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
        from utils.ColorProvider import ColorProvider

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

        # Guarda os eventos filtrados para exportacao
        self._filtered_events = events

        # Preencher tabela
        self.table.setRowCount(len(events))

        for row, event in enumerate(events):
            for col, col_name in enumerate(self.COLUMNS):
                value = event.get(col_name, "")
                if isinstance(value, dict):
                    value = str(value)
                if value is None:
                    value = ""

                # Formata timestamp
                if col_name == "timestamp":
                    value = self._format_timestamp(str(value))

                item = QTableWidgetItem(str(value))
                item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)

                # Armazena dados originais no item para exportacao/detalhes
                item.setData(Qt.ItemDataRole.UserRole, event)

                # ── Cor da fonte conforme a coluna ─────────────────────
                if col_name == "level":
                    color_hex = ColorProvider.level_color(str(value))
                elif col_name == "tool":
                    color_hex = ColorProvider.tool_color(str(value))
                elif col_name == "class":
                    color_hex = ColorProvider.class_color(str(value))
                else:
                    color_hex = ColorProvider.text_primary()

                item.setForeground(QBrush(QColor(color_hex)))

                self.table.setItem(row, col, item)

        # Atualizar status
        filtered = len(events)
        total = len(self._raw_events)
        if filtered != total:
            self.status_label.setText(
                f"{filtered} de {total} evento(s) (filtrado)"
            )

    @staticmethod
    def _format_timestamp(ts: str) -> str:
        """
        Formata timestamp ISO para exibicao mais legivel.

        "2026-05-08T22:52:00.341898" → "2026-05-08 22:52:00"
        """
        if not ts:
            return ts
        # Remove milissegundos e substitui T por espaco
        ts = ts.replace("T", " ")
        if "." in ts:
            ts = ts.split(".")[0]
        return ts

    # ═════════════════════════════════════════════════════════════════════
    # Exportacao (clipboard)
    # ═════════════════════════════════════════════════════════════════════

    def _export_filter(self) -> None:
        """
        Copia todos os eventos filtrados para clipboard como TSV
        (tab-separated, cola direto no Excel).
        """
        if not self._filtered_events:
            return

        lines: List[str] = []
        # Cabecalho
        lines.append("\t".join(self.COLUMNS))

        for event in self._filtered_events:
            row_values: List[str] = []
            for col_name in self.COLUMNS:
                value = event.get(col_name, "")
                if isinstance(value, dict):
                    value = str(value)
                if value is None:
                    value = ""
                # Remove tabs internos para nao quebrar o TSV
                row_values.append(str(value).replace("\t", " "))
            lines.append("\t".join(row_values))

        text = "\n".join(lines)
        QApplication.clipboard().setText(text)

        self.status_label.setText(
            f"{len(self._filtered_events)} evento(s) copiados para clipboard (filtro)"
        )

    def _export_selection(self) -> None:
        """
        Copia as celulas selecionadas para clipboard como TSV.
        Mantem a estrutura de linhas e colunas da selecao.
        """
        selected_ranges = self.table.selectedRanges()
        if not selected_ranges:
            return

        lines: List[str] = []

        for sel_range in selected_ranges:
            for row in range(sel_range.topRow(), sel_range.bottomRow() + 1):
                row_values: List[str] = []
                for col in range(sel_range.leftColumn(), sel_range.rightColumn() + 1):
                    item = self.table.item(row, col)
                    value = item.text() if item else ""
                    row_values.append(value.replace("\t", " "))
                lines.append("\t".join(row_values))

        text = "\n".join(lines)
        QApplication.clipboard().setText(text)

        # Conta celulas
        cell_count = sum(
            (r.bottomRow() - r.topRow() + 1) * (r.rightColumn() - r.leftColumn() + 1)
            for r in selected_ranges
        )
        self.status_label.setText(
            f"{cell_count} celula(s) copiadas para clipboard (selecao)"
        )

    # ═════════════════════════════════════════════════════════════════════
    # Eventos
    # ═════════════════════════════════════════════════════════════════════

    def _on_filter_changed(self) -> None:
        """Chamado quando o texto de busca ou combo de nivel muda."""
        self._render_table()
        self._save_preferences()

    def _on_header_clicked(self, logical_index: int) -> None:
        """
        Chamado quando o usuario clica no cabecalho de uma coluna.
        Alterna a ordenacao: se ja esta ordenando por esta coluna,
        inverte a direcao; caso contrario, ordena ASC primeiro.
        """
        col_name = self.COLUMNS[logical_index]

        if self._sort_column == col_name:
            self._sort_ascending = not self._sort_ascending
        else:
            self._sort_column = col_name
            self._sort_ascending = True

        self._render_table()

    def _on_cell_double_clicked(self, row: int, col: int) -> None:
        """
        Chamado quando o usuario da duplo clique em uma celula.
        Abre o dialog de detalhes para a linha correspondente.
        """
        item = self.table.item(row, 0)  # Pega qualquer item da linha
        if item is None:
            return

        event = item.data(Qt.ItemDataRole.UserRole)
        if event is None:
            # Fallback: se nao tem dados guardados, monta do display
            event = {}
            for c, col_name in enumerate(self.COLUMNS):
                cell = self.table.item(row, c)
                event[col_name] = cell.text() if cell else ""

        dialog = LogDetailDialog(event, self)
        dialog.exec()