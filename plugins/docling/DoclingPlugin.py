# -*- coding: utf-8 -*-
"""
DoclingPlugin — Conversão de documentos para Markdown via Docling
==================================================================
Plugin do Aetheris ToolBox que converte PDF, imagens, Office, etc.
para Markdown usando Docling, com suporte a layout multi-coluna.

Usa:
- SignalManager para console/progress (Contrato 20)
- ExecutionButtons para botões de ação (Contrato 18)
- SelectorGrid para seleção de arquivo com filtro
- GridCheckBox + GridDoubleSpinBox para opções de colunas
- ReadOnlyTextBrowser para preview do markdown gerado
- HudCircularRingsLoader para feedback visual durante conversão
"""

from __future__ import annotations

import os
from typing import Any

from core.enum.ToolKey import ToolKey
from core.manager.SignalManager import SignalManager
from core.ui.HudCircularRingsLoader import HudCircularRingsLoader
from plugins.BasePlugin import BasePlugin
from core.task.DoclingWorkerTask import DoclingWorkerTask
from resources.widgets.ExecutionButtons import ExecutionButtons
from resources.widgets.GridCheckBox import GridCheckBox
from resources.widgets.GridDoubleSpinBox import GridDoubleSpinBox
from resources.widgets.GroupPainel import GroupPainel
from resources.widgets.ReadOnlyTextBrowser import ReadOnlyTextBrowser
from resources.widgets.SelectorGrid import SelectorGrid
from utils.ExplorerUtils import ExplorerUtils
from utils.MessageBox import MessageBox


DOCUMENT_FILTER = (
    "Documentos suportados (*.pdf *.png *.jpg *.jpeg *.tiff *.tif *.webp "
    "*.docx *.pptx *.xlsx *.html *.htm *.txt *.md);;"
    "PDF (*.pdf);;"
    "Imagens (*.png *.jpg *.jpeg *.tiff *.tif *.webp);;"
    "Office (*.docx *.pptx *.xlsx);;"
    "Todos os arquivos (*.*)"
)


class DoclingPlugin(BasePlugin):

    def __init__(self, parent=None):
        super().__init__(
            tool_key=ToolKey.DOCLING.value,
            parent=parent,
            title="Docling → Markdown",
        )
        self._worker: DoclingWorkerTask | None = None
        self._current_markdown: str = ""
        self.logger.info("DoclingPlugin inicializado", code="DOCLING_READY")
        self.page.set_badge(self.page.PRONTA)

    def _build_ui(self):
        super()._build_ui()

        # ── HUD Loader (overlay) ──────────────────────────────────────
        self._loader = HudCircularRingsLoader(self)
        self._loader.setGeometry(0, 0, self.width(), self.height())

        # ── ExecutionButtons ──────────────────────────────────────────
        self._btns = ExecutionButtons(self)
        self._btns.setup({
            "converter": {
                "text": "CONVERTER",
                "callback": self._on_converter,
                "type": "primary",
                "description": "Converte o documento para Markdown",
            },
            "salvar": {
                "text": "SALVAR MD",
                "callback": self._on_salvar,
                "type": "secondary",
                "description": "Salva o Markdown gerado em arquivo .md",
            },
        })
        self.main_layout.addWidget(self._btns)

        # ── SelectorGrid: Arquivo de Entrada ──────────────────────────
        self._sel_grid = SelectorGrid(
            specs={
                "Documento": {
                    "file_filter": DOCUMENT_FILTER,
                    "browse_mode": "open_file",
                    "placeholder": "Selecione um documento para converter...",
                },
            },
            title="Arquivo de Entrada",
        )
        self.main_layout.addWidget(self._sel_grid)

        # ── Opções de layout ──────────────────────────────────────────
        self._grid_col_opts = GridCheckBox(
            config={
                "columnar": {
                    "label": "Separar por colunas (telas / IDE multi-painéis)",
                    "description": "Usa posição horizontal dos blocos de texto para detectar colunas",
                    "default": False,
                },
            },
            num_columns=1,
        )
        self._grid_col_opts.changed.connect(self._on_columnar_changed)

        self._grid_cols = GridDoubleSpinBox(
            config={
                "num_cols": {
                    "label": "Nº colunas",
                    "description": "0 = automático, 2-6 = forçar número",
                    "decimal": 0,
                    "default": 0,
                    "min": 0,
                    "max": 6,
                    "step": 1,
                    "suffix": "",
                },
            },
        )
        self._grid_cols.set_enabled("num_cols", False)

        grp_opts = GroupPainel("Opções de Layout")
        grp_opts.group_layout.addWidget(self._grid_col_opts)
        grp_opts.group_layout.addWidget(self._grid_cols)
        self.main_layout.addWidget(grp_opts)

        # ── Preview do Markdown ───────────────────────────────────────
        self._txt_preview = ReadOnlyTextBrowser(
            placeholder="Markdown gerado aparece aqui...",
        )
        grp_preview = GroupPainel("Pré-Visualização")
        grp_preview.group_layout.addWidget(self._txt_preview)
        self.main_layout.addWidget(grp_preview, 1)

    # ── Eventos ─────────────────────────────────────────────────────

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._loader.setGeometry(0, 0, self.width(), self.height())

    # ── Slots ───────────────────────────────────────────────────────

    def _on_columnar_changed(self, key: str, value: Any):
        """Habilita/desabilita o spin de colunas conforme checkbox."""
        if key == "columnar":
            enabled = bool(value)
            self._grid_cols.set_enabled("num_cols", enabled)

    def _on_converter(self):
        """Valida e dispara a conversão."""
        if self._worker is not None and self._worker.isRunning():
            MessageBox.show_warning(
                "Já existe uma conversão em andamento.", title="Aguarde"
            )
            return

        sel = self._sel_grid.get("Documento")
        file_path = sel.path() if sel else ""

        if not file_path or not os.path.isfile(file_path):
            MessageBox.show_warning(
                "Selecione um arquivo válido primeiro.", title="Arquivo"
            )
            return

        columnar = bool(self._grid_col_opts.all.get("columnar", False))
        manual_cols = int(self._grid_cols.values.get("num_cols", 0))

        self._current_markdown = ""
        self._txt_preview.clear_content()
        self.page.set_badge(self.page.RUNNING)
        self._btns.set_enabled("converter", False)
        self._loader.show_loader()
        self._loader.set_progress(0, "Inicializando conversão...")

        SignalManager.instance().console_message.emit(
            f"Convertendo: {os.path.basename(file_path)}"
        )
        self.logger.info(
            "Iniciando conversão",
            code="CONVERT_START",
            file=file_path,
            columnar=columnar,
            cols=manual_cols,
        )

        self._worker = DoclingWorkerTask(
            file_path,
            columnar=columnar,
            manual_columns=manual_cols,
            tool_key=self.tool_key,
            parent=self,
        )
        self._worker.finished_ok.connect(self._on_done)
        self._worker.failed.connect(self._on_error)
        self._worker.finished.connect(self._on_worker_finished)
        self._worker.start()

    def _on_done(self, markdown: str):
        """Recebe o Markdown gerado e exibe no preview."""
        self._current_markdown = markdown
        self._txt_preview.setPlainText(markdown)
        SignalManager.instance().console_message.emit(
            "Conversão concluída com sucesso!"
        )
        SignalManager.instance().progress_update.emit(100.0)
        self.page.set_badge(self.page.PRONTA)
        self.logger.info("Markdown gerado", code="CONVERT_DONE")

    def _on_error(self, message: str):
        """Exibe erro da conversão."""
        self.logger.error("Falha na conversão", code="CONVERT_ERR", error=message)
        SignalManager.instance().console_message.emit(
            f"Erro na conversão: {message}"
        )
        self._current_markdown = ""
        self._txt_preview.clear_content()
        self.page.set_badge(self.page.ERROR)
        MessageBox.show_critical(
            f"Erro na conversão:\n{message}", title="Erro"
        )

    def _on_worker_finished(self):
        """Limpa estado do worker."""
        self._worker = None
        self._loader.hide_loader()
        self._btns.set_enabled("converter", True)
        SignalManager.instance().progress_update.emit(0.0)

    def _on_salvar(self):
        """Salva o Markdown gerado em arquivo .md."""
        if not self._current_markdown.strip():
            MessageBox.show_warning(
                "Não há Markdown para salvar.", title="Salvar"
            )
            return

        path = ExplorerUtils.save_file(
            "Salvar Markdown",
            file_filter="Markdown (*.md);;Todos (*.*)",
            parent=self,
        )
        if not path:
            return

        try:
            with open(path, "w", encoding="utf-8") as f:
                f.write(self._current_markdown)
            SignalManager.instance().console_message.emit(
                f"Markdown salvo: {path}"
            )
            self.logger.info("Arquivo salvo", code="SAVE_DONE", path=path)
        except Exception as e:
            self.logger.error("Erro ao salvar", code="SAVE_ERR", error=str(e))
            MessageBox.show_critical(
                f"Erro ao salvar arquivo:\n{e}", title="Erro"
            )

    # ── Preferências ─────────────────────────────────────────────────

    def load_prefs(self):
        """Carrega preferências salvas."""
        file_path = self.preferences.get("file_path", "")
        if file_path:
            sel = self._sel_grid.get("Documento")
            if sel:
                sel.set_path(file_path)

        states = self.preferences.get("options", {})
        if states:
            self._grid_col_opts.set_all(states)

        cols = self.preferences.get("num_cols", 0)
        self._grid_cols.set_values({"num_cols": cols})
        if cols > 0 or states.get("columnar", False):
            self._grid_cols.set_enabled("num_cols", True)

    def save_prefs(self):
        """Salva preferências atuais."""
        sel = self._sel_grid.get("Documento")
        file_path = sel.path() if sel else ""
        self.preferences["file_path"] = file_path
        self.preferences["options"] = self._grid_col_opts.all
        self.preferences["num_cols"] = int(self._grid_cols.values.get("num_cols", 0))