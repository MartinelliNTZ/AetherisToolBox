# -*- coding: utf-8 -*-
"""
IcoConverterPlugin — Conversor de imagens para formato ICO
=============================================================
Converte imagens (PNG, JPG, BMP, etc.) para ícones Windows (.ico)
com múltiplos tamanhos (16, 32, 48, 64, 128, 256 pixels).

Usa:
- PIL (Pillow) para processamento de imagens
- SignalManager para progresso e console (Contrato 20)
- FileListView + PreviewPanel para gestão de arquivos
- ExecutionButtons (Contrato 18) para botão CONVERTER
"""

from __future__ import annotations

import os
from typing import Dict, Any

from PySide6.QtCore import Qt, QTimer

from core.enum.ToolKey import ToolKey
from core.manager.SignalManager import SignalManager
from plugins.BasePlugin import BasePlugin
from resources.widgets.ExecutionButtons import ExecutionButtons
from resources.widgets.FileListView import FileListView
from resources.widgets.PreviewPanel import PreviewPanel
from resources.widgets.SelectorGrid import SelectorGrid
from resources.widgets.GridCheckBox import GridCheckBox
from resources.widgets.SimpleLabel import SimpleLabel
from resources.widgets.GridGroupPainel import GridGroupPainel
from resources.widgets.GroupPainel import GroupPainel
from utils.DictManager import IMAGE_EXTENSIONS
from utils.ExplorerUtils import ExplorerUtils
from utils.MessageBox import MessageBox


# ── Tamanhos de ícone disponíveis (específico do plugin) ────────────
ICO_SIZES: Dict[str, Dict[str, Any]] = {
    "16":   {"label": "16 pixels",   "description": "16x16", "default": True},
    "32":   {"label": "32 pixels",   "description": "32x32", "default": True},
    "48":   {"label": "48 pixels",   "description": "48x48", "default": True},
    "64":   {"label": "64 pixels",   "description": "64x64", "default": True},
    "128":  {"label": "128 pixels",  "description": "128x128", "default": True},
    "256":  {"label": "256 pixels",  "description": "256x256", "default": False},
}


class IcoConverterPlugin(BasePlugin):
    """
    Conversor de imagens para formato ICO do Windows.
    """

    def __init__(self, parent=None):
        super().__init__(
            tool_key=ToolKey.ICO_CONVERTER.value,
            parent=parent,
            sys_prefs=True,  # precisa de sys_preferences para root_folder + project_path
            title="Conversor ICO",
            show_project_path=True,
        )
        self.logger.info("Conversor ICO inicializado", code="ICO_READY")
        self.page.set_badge(self.page.PRONTA)

    # ── UI ──────────────────────────────────────────────────────────

    def _build_ui(self):
        super()._build_ui()

        # ── Preview Panel ─────────────────────────────────────────────
        self._preview = PreviewPanel(fixed_size=(480, 360))

        # ── FileListView (com preview conectado automaticamente) ──────
        self._file_list = FileListView(
            file_filter=IMAGE_EXTENSIONS,
            accept_dirs=True,
            preview_widget=self._preview,
        )
        self._file_list.files_changed.connect(self._on_files_changed)

        # ── ExecutionButtons (só o CONVERTER) ─────────────────────────
        self._btns = ExecutionButtons(self)
        self._btns.setup({
            "convert": {
                "text": "CONVERTER",
                "callback": self._on_convert,
                "type": "primary",
                "description": "Converte todas as imagens da lista para ICO",
            },
        })
        self.main_layout.addWidget(self._btns)

        # ── Grid: Arquivos + Preview ──────────────────────────────────
        grp_arquivos = GroupPainel("Arquivos")
        grp_arquivos.group_layout.addWidget(self._file_list)

        grp_preview = GroupPainel("Pré-Visualização")
        grp_preview.group_layout.addWidget(self._preview)

        grid_paineis = GridGroupPainel(grp_arquivos, grp_preview)
        self.main_layout.addWidget(grid_paineis)

        # ── Tamanhos do Ícone ─────────────────────────────────────────
        self._grid_sizes = GridCheckBox(ICO_SIZES, num_columns=3)
        grp_tamanhos = GroupPainel("Tamanhos do Ícone")
        grp_tamanhos.group_layout.addWidget(self._grid_sizes)
        self.main_layout.addWidget(grp_tamanhos)

        # ── Profundidade de bits ──────────────────────────────────────
        lbl_bits = SimpleLabel("Profundidade de bits: 32 bits (RGBA com transparência alfa)")
        self.main_layout.addWidget(lbl_bits)

        # ── Pasta de Saída ────────────────────────────────────────────
        # Tenta obter sugestão de caminho
        suggested_ico = ""
        if self.sys_preferences:
            root = self.sys_preferences.get("root_folder", "")
            if root:
                suggested_ico = ExplorerUtils.get_default_path("ico", root)

        self._selector_grid = SelectorGrid(
            specs={
                "Pasta de Saída": {
                    "label_text": "Pasta de Saída:",
                    "placeholder": "Onde salvar os arquivos .ICO...",
                    "browse_mode": "directory",
                    "label_width": 120,
                },
            },
            title="Pasta de Saída",
            suggested_paths={"Pasta de Saída": suggested_ico} if suggested_ico else None,
        )
        self.main_layout.addWidget(self._selector_grid)

        # ── Opções ────────────────────────────────────────────────────
        self._grid_opts = GridCheckBox(
            config={
                "subfolders": {
                    "label": "Vasculhar subpastas",
                    "description": "Inclui arquivos de subpastas recursivamente ao adicionar pastas",
                    "default": False,
                },
                "save_in_origin": {
                    "label": "Salvar ICOs na origem",
                    "description": "Cada .ICO salvo na mesma pasta da imagem que o gerou. Ignora pasta de saída.",
                    "default": False,
                },
            },
            num_columns=2,
        )
        grp_opts = GroupPainel("Opções")
        grp_opts.group_layout.addWidget(self._grid_opts)
        self.main_layout.addWidget(grp_opts)

        # ── Passa pasta do projeto para a lista se disponível ─────────
        if self.sys_preferences:
            root = self.sys_preferences.get("root_folder", "")
            if root:
                # Verifica se existem pastas comuns de imagens
                candidates = [
                    os.path.join(root, "image"),
                    os.path.join(root, "images"),
                    os.path.join(root, "raster"),
                    root,
                ]
                for folder in candidates:
                    if os.path.isdir(folder):
                        self._file_list.add_files([folder])
                        break

    # ── Signals ─────────────────────────────────────────────────────

    def _on_files_changed(self, count: int):
        """Atualiza badge quando arquivos são adicionados/removidos."""
        if count > 0:
            self.page.set_badge(self.page.PRONTA)

    # ── Conversão ───────────────────────────────────────────────────

    def _on_convert(self):
        """Inicia o processo de conversão."""
        paths = self._file_list.get_ordered_paths()
        if not paths:
            MessageBox.show_warning(
                "Nenhuma imagem na lista. Adicione arquivos ou pastas primeiro.",
                title="Aviso",
            )
            return

        # Coleta tamanhos selecionados
        sizes_checked = self._grid_sizes.checked
        if not sizes_checked:
            MessageBox.show_warning(
                "Selecione ao menos um tamanho de ícone.",
                title="Aviso",
            )
            return

        sizes = sorted(int(k) for k in sizes_checked)

        # Determina pasta de saída
        save_in_origin = self._grid_opts.is_item_checked("save_in_origin")
        output_dir = ""
        if not save_in_origin:
            output_dir = self._selector_grid["Pasta de Saída"].path()
            if not output_dir:
                MessageBox.show_warning(
                    "Selecione uma pasta de saída ou marque 'Salvar ICOs na origem'.",
                    title="Aviso",
                )
                return

        # Confirma
        result = MessageBox.show_question(
            f"Converter {len(paths)} imagem(ns) para ICO?\n"
            f"Tamanhos: {', '.join(str(s) for s in sizes)}px\n"
            f"{'Salvando na mesma pasta das imagens' if save_in_origin else f'Pasta: {output_dir}'}",
            title="Confirmar Conversão",
        )
        if result != MessageBox.YES:
            self.logger.info("Conversão cancelada pelo usuário", code="ICO_CONVERT_CANCELLED")
            return

        # Inicia conversão
        self.logger.info(
            "Iniciando conversão",
            code="ICO_CONVERT_START",
            count=len(paths),
            sizes=sizes,
        )
        SignalManager.instance().console_message.emit(
            f"Iniciando conversão de {len(paths)} imagem(ns)..."
        )
        self.page.set_badge(self.page.RUNNING)
        self._btns.set_enabled("convert", False)

        # Usa QTimer para não travar a UI
        QTimer.singleShot(0, lambda: self._run_conversion(paths, sizes, output_dir, save_in_origin))

    def _run_conversion(
        self,
        paths: list[str],
        sizes: list[int],
        output_dir: str,
        save_in_origin: bool,
    ) -> None:
        """Executa a conversão em lotes (single-thread, não-bloqueante via QTimer)."""
        from PIL import Image

        total = len(paths)
        ok_count = 0
        err_count = 0

        try:
            for idx, img_path in enumerate(paths, start=1):
                try:
                    # Determina diretório de saída
                    if save_in_origin:
                        out_dir = os.path.dirname(img_path)
                    else:
                        out_dir = output_dir

                    self._generate_ico(img_path, sizes, out_dir)
                    ok_count += 1
                    self.logger.info(f"ICO gerado: {img_path}", code="ICO_GENERATED")

                except Exception as e:
                    err_count += 1
                    self.logger.error(
                        f"Erro ao processar {img_path}",
                        code="ICO_CONVERT_ERR",
                        error=str(e),
                    )
                    SignalManager.instance().console_message.emit(
                        f"Erro ao processar {os.path.basename(img_path)}: {e}"
                    )

                # Progresso
                progress = (idx / total) * 100.0
                SignalManager.instance().progress_update.emit(progress)

            # Finalizado
            self.logger.info(
                "Conversão finalizada",
                code="ICO_CONVERT_DONE",
                ok=ok_count,
                err=err_count,
            )
            msg = f"Conversão finalizada! {ok_count} ícone(s) gerado(s)."
            if err_count:
                msg += f" {err_count} erro(s)."
            SignalManager.instance().console_message.emit(msg)

            if err_count == 0:
                self.page.set_badge(self.page.PRONTA)
                msg_success = f"Conversão concluída com sucesso! {ok_count} ícone(s) gerado(s)."
                if ok_count > 0:
                    msg_success += f"\nSalvo em: {output_dir if not save_in_origin else 'pastas originais'}"
                MessageBox.show_info(msg_success, title="Concluído")
            else:
                self.page.set_badge(self.page.ERROR)

        except Exception as e:
            self.logger.error("Erro durante conversão", code="ICO_CONVERT_FATAL", error=str(e))
            SignalManager.instance().console_message.emit(f"Erro fatal: {e}")
            self.page.set_badge(self.page.ERROR)
        finally:
            self._btns.set_enabled("convert", True)
            SignalManager.instance().progress_update.emit(0.0)
            self.save_prefs()

    @staticmethod
    def _generate_ico(image_path: str, sizes: list[int], output_dir: str) -> str:
        """
        Gera um arquivo .ICO a partir de uma imagem.

        Args:
            image_path: Caminho da imagem de origem.
            sizes: Lista de tamanhos (ex: [16, 32, 48]).
            output_dir: Pasta onde salvar o .ICO.

        Returns:
            Caminho do arquivo .ICO gerado.
        """
        from PIL import Image

        img = Image.open(image_path).convert("RGBA")
        sizes_tuples = [(s, s) for s in sorted(sizes)]
        base_name = os.path.splitext(os.path.basename(image_path))[0]
        out_path = os.path.join(output_dir, f"{base_name}.ico")
        img.save(out_path, format="ICO", sizes=sizes_tuples)
        return out_path

    # ── Preferências ─────────────────────────────────────────────────

    def load_prefs(self):
        """Carrega preferências salvas."""
        # Restaura tamanhos
        sizes_states = self.preferences.get("sizes", {})
        if sizes_states:
            self._grid_sizes.set_all(sizes_states)

        # Restaura pasta de saída
        output_dir = self.preferences.get("output_dir", "")
        if output_dir:
            self._selector_grid["Pasta de Saída"].set_path(output_dir)

        # Restaura opções
        opts = self.preferences.get("options", {})
        if opts:
            self._grid_opts.set_all(opts)

    def save_prefs(self):
        """Salva preferências atuais."""
        self.preferences["sizes"] = self._grid_sizes.all
        self.preferences["output_dir"] = self._selector_grid["Pasta de Saída"].path()
        self.preferences["options"] = self._grid_opts.all