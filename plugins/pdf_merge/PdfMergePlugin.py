# -*- coding: utf-8 -*-
"""
PdfMergePlugin — Mescla arquivos em um único PDF agrupado (v1: PDFs)
=====================================================================
Arquitetura genérica de merge: um registro de handlers por extensão
(HANDLERS) anexa cada arquivo ao PdfWriter de saída. A UI é igual para
qualquer formato suportado — adicionar imagens é só registrar o handler.

Contratos seguidos:
  - Contrato 11: widgets reutilizáveis (FileListView, GridCheckBox,
                 GridComplexSelector, GridGroupPainel)
  - Contrato 18: ExecutionButtons via buttons_config no header do PluginPage
  - Contrato 20: SignalManager para HUD/ProgressBar/console

Usa:
- pypdf (import lazy) para o merge de PDFs
- FileListView para a lista de arquivos (filtro PDF)
- GridComplexSelector (mode_type="output") para a pasta de saída
- "separator" (GridCheckBox): página em branco A4 entre os PDFs
"""

from __future__ import annotations

import os
from typing import Any, Callable, Dict

from PySide6.QtCore import QTimer

from core.enum.ToolKey import ToolKey
from core.manager.SignalManager import SignalManager
from plugins.BasePlugin import BasePlugin
from resources.widgets.FileListView import FileListView
from resources.widgets.GroupPainel import GroupPainel
from resources.widgets.complex.GridComplexSelector import GridComplexSelector
from resources.widgets.grid.GridCheckBox import GridCheckBox
from resources.widgets.grid.GridGroupPainel import GridGroupPainel
from utils.MessageBox import MessageBox


# ── Filtro v1 — só PDFs. Ao adicionar imagens, mescle com IMAGE_EXTENSIONS. ──
PDF_FILTER: Dict[str, Dict[str, Any]] = {
    ".pdf": {"label": ".pdf", "description": "Adobe Portable Document", "default": True},
}


def _append_pdf(writer, pdf_path: str) -> None:
    """Handler v1 — anexa todas as páginas de um PDF ao writer."""
    writer.append(pdf_path)


# Registro de handlers — ext → função que anexa páginas ao writer.
HANDLERS: Dict[str, Callable] = {
    ".pdf": _append_pdf,
    # Futuro: ".png": _append_image, ".jpg": _append_image, ...
}


class PdfMergePlugin(BasePlugin):

    def __init__(self, parent=None):
        super().__init__(
            tool_key=ToolKey.PDF_MERGE.value,
            parent=parent,
            title="Merge PDF",
            buttons_config={
                "merge": {
                    "text": "MESCLAR",
                    "callback": self._on_merge,
                    "type": "primary",
                    "description": "Gera um único PDF com todos os arquivos da lista",
                },
            },
        )
        self.logger.info("Merge PDF inicializado", code="PDF_MERGE_READY")
        self.page.set_badge(self.page.PRONTA)

    def _build_ui(self):
        super()._build_ui()

        # ── Lista de arquivos (somente PDFs na v1) ───────────────────
        self._file_list = FileListView(
            file_filter=PDF_FILTER,
            accept_dirs=True,
        )
        self._file_list.files_changed.connect(self._on_files_changed)

        grp_arquivos = GroupPainel("Arquivos")
        grp_arquivos.group_layout.addWidget(self._file_list)
        self.main_layout.addWidget(GridGroupPainel(grp_arquivos))

        # ── Opções ──────────────────────────────────────────────────
        self._grid_opts = GridCheckBox(
            config={
                "separator": {
                    "label": "Página em branco entre arquivos",
                    "description": "Insere uma página A4 vazia entre cada PDF",
                    "default": False,
                },
            },
            num_columns=1,
        )
        grp_opts = GroupPainel("Opções")
        grp_opts.group_layout.addWidget(self._grid_opts)
        self.main_layout.addWidget(GridGroupPainel(grp_opts))

        # ── Pasta de Saída — GridComplexSelector (output) ───────────
        self._sel_saida = GridComplexSelector(
            {
                "Saída": {
                    "mode_type": "output",
                    "file_filter": "PDF (*.pdf)",
                    "allow_folder": True,
                    "allow_file": False,
                    "multiple": False,
                    "show_suggest_button": True,
                    "subfolder": "pdfmerge",
                    "placeholder": "Onde salvar o PDF mesclado...",
                },
            },
            title="Pasta de Saída",
        )
        self.main_layout.addWidget(self._sel_saida)

    # ── Signals ─────────────────────────────────────────────────────

    def _on_files_changed(self, count: int):
        if count > 0:
            self.page.set_badge(self.page.PRONTA)

    # ── Merge ───────────────────────────────────────────────────────

    def _on_merge(self):
        paths = self._file_list.get_ordered_paths()
        if not paths:
            MessageBox.show_warning("Nenhum PDF na lista.", title="Aviso")
            return

        output_dir = self._sel_saida["Saída"].path()
        if not output_dir:
            MessageBox.show_warning("Selecione a pasta de saída.", title="Aviso")
            return

        result = MessageBox.show_question(
            f"Mesclar {len(paths)} PDF(s) em um único arquivo?\nPasta: {output_dir}",
            title="Confirmar",
        )
        if result != MessageBox.YES:
            self.logger.info("Merge cancelado", code="PDF_MERGE_CANCELLED")
            return

        self.logger.info("Iniciando merge", code="PDF_MERGE_START", count=len(paths))
        SignalManager.instance().console_message.emit(f"Mesclando {len(paths)} PDF(s)...")
        self.page.set_badge(self.page.RUNNING)
        self.page.buttons.set_enabled("merge", False)

        SignalManager.instance().execution_started.emit(self.tool_key)
        SignalManager.instance().hud_show.emit({"message": "Mesclando PDFs..."})

        QTimer.singleShot(0, lambda: self._run_merge(paths, output_dir))

    def _run_merge(self, paths, output_dir):
        from pypdf import PdfWriter   # lazy (mantém startup rápido)

        total = len(paths)
        ok_count = 0
        total_pages = 0
        base_inicial = os.path.splitext(os.path.basename(paths[0]))[0]
        base_final = os.path.splitext(os.path.basename(paths[-1]))[0]
        out_path = os.path.join(output_dir, f"{base_inicial}_a_{base_final}.pdf")

        try:
            os.makedirs(output_dir, exist_ok=True)

            writer = PdfWriter()
            for idx, pdf_path in enumerate(paths, start=1):
                try:
                    count_before = len(writer.pages)
                    self._append_file(writer, pdf_path)   # dispatcher genérico
                    total_pages += len(writer.pages) - count_before
                    ok_count += 1

                    if self._grid_opts.is_item_checked("separator") and idx < total:
                        writer.add_blank_page(width=595.28, height=841.89)  # A4 pts

                    self.logger.info(f"Anexado: {pdf_path}", code="PDF_MERGE_APPENDED")
                except Exception as e:
                    self.logger.error(
                        f"Falha ao anexar {pdf_path}",
                        code="PDF_MERGE_APPEND_ERR",
                        error=str(e),
                    )
                    SignalManager.instance().console_message.emit(
                        f"Erro: {os.path.basename(pdf_path)} — {e}"
                    )

                pct = (idx / total) * 100.0
                SignalManager.instance().progress_update.emit(pct)
                SignalManager.instance().hud_update.emit({
                    "message": f"Mesclando {idx}/{total}...",
                    "progress": pct,
                })

            with open(out_path, "wb") as f:
                writer.write(f)

            self.logger.info(
                "Merge finalizado",
                code="PDF_MERGE_DONE",
                ok=ok_count,
                pages=total_pages,
            )
            msg = f"Merge concluído! {ok_count} PDF(s), {total_pages} página(s)."
            SignalManager.instance().console_message.emit(msg)

            if ok_count == total:
                self.page.set_badge(self.page.PRONTA)
                self.output_message(output_dir, label="Pasta de Saída")
                MessageBox.show_info(
                    f"Sucesso! PDF gerado com {total_pages} página(s).",
                    title="Concluído",
                )
            else:
                self.page.set_badge(self.page.ERROR)
                MessageBox.show_warning(
                    f"Concluído com {total - ok_count} erro(s).",
                    title="Aviso",
                )
        except Exception as e:
            self.logger.error("Erro fatal no merge", code="PDF_MERGE_FATAL", error=str(e))
            SignalManager.instance().console_message.emit(f"Erro fatal: {e}")
            self.page.set_badge(self.page.ERROR)
        finally:
            SignalManager.instance().hud_hide.emit()
            SignalManager.instance().execution_finished.emit(self.tool_key)
            SignalManager.instance().progress_update.emit(0.0)
            self.page.buttons.set_enabled("merge", True)
            self.save_prefs()

    # ── Handlers de formato (genérico) ──────────────────────────────

    def _append_file(self, writer, file_path: str) -> None:
        """Dispatcher genérico: resolve o handler pela extensão."""
        ext = os.path.splitext(file_path)[1].lower()
        handler = HANDLERS.get(ext)
        if handler is None:
            raise ValueError(f"Formato não suportado: {ext}")
        handler(writer, file_path)

    # ── Preferências (Contrato 6 — obrigatório) ─────────────────────

    def load_prefs(self):
        paths = self.preferences.get("paths", [])
        if paths:
            self._file_list.add_files(paths)   # dispara files_changed sozinho
        out = self.preferences.get("output_dir", "")
        if out:
            self._sel_saida["Saída"].set_path(out)
        opts = self.preferences.get("options", {})
        if opts:
            self._grid_opts.set_all(opts)

    def save_prefs(self):
        self.preferences["paths"] = self._file_list.get_ordered_paths()  # ordem atual
        self.preferences["output_dir"] = self._sel_saida["Saída"].path()
        self.preferences["options"] = self._grid_opts.all