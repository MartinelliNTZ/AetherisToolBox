# -*- coding: utf-8 -*-
"""
MrkSubstitutorPlugin — Substitui valores em arquivos MRK
==========================================================
Usa MrkWorkerTask (QThread) para nao travar a UI.
Exibe HUDLoader durante processamento.
Batch sequencial sem recursao (loop).
A leitura de dados tambem vai para thread (worker interno).
"""

from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Optional

from PySide6.QtCore import QThread, Signal

from core.enum.ToolKey import ToolKey
from core.manager.SignalManager import SignalManager
from plugins.BasePlugin import BasePlugin
from resources.widgets.ExecutionButtons import ExecutionButtons
from resources.widgets.GridCheckBox import GridCheckBox
from resources.widgets.GridFieldMapping import GridFieldMapping
from resources.widgets.GridRadio import GridRadio
from resources.widgets.GroupPainel import GroupPainel
from resources.widgets.GridGroupPainel import GridGroupPainel
from resources.widgets.SimpleSelector import SimpleSelector
from utils.ExplorerUtils import ExplorerUtils
from utils.MessageBox import MessageBox


# ── Constantes ─────────────────────────────────────────────────────

MODE_SINGLE = "single"
MODE_BATCH = "batch"

MRK_EXTENSIONS = frozenset({".mrk"})
DATA_EXTENSIONS = frozenset({".gpkg", ".shp", ".csv"})

SCENARIO_CONFIG = {
    MODE_SINGLE: {
        "label": "Arquivo Unico",
        "description": "Processa 1 MRK com 1 arquivo de dados",
        "default": True,
    },
    MODE_BATCH: {
        "label": "Lote por Pasta",
        "description": "Busca MRKs e dados por chave no nome",
        "default": False,
    },
}

MAPPING_CONFIG = {
    "altitude": {
        "from_label": "Campo Origem:", "from_placeholder": "Ex: AbsZ",
        "to_label": "Campo MRK:", "to_placeholder": "Ex: Ellh",
        "default_from": "AbsZ", "default_to": "Ellh", "default_enabled": True,
        "tooltip": "Mapeamento de altitude",
    },
    "latitude": {
        "from_label": "Campo Origem:", "from_placeholder": "Ex: Latitude",
        "to_label": "Campo MRK:", "to_placeholder": "Ex: Lat",
        "default_from": "Latitude", "default_to": "Lat", "default_enabled": False,
        "tooltip": "Mapeamento de latitude",
    },
    "longitude": {
        "from_label": "Campo Origem:", "from_placeholder": "Ex: Longitude",
        "to_label": "Campo MRK:", "to_placeholder": "Ex: Lon",
        "default_from": "Longitude", "default_to": "Lon", "default_enabled": False,
        "tooltip": "Mapeamento de longitude",
    },
}

OUTPUT_DIR_KEY = "output_dir"
MRK_DIR_KEY = "mrk_dir"
MRK_FILE_KEY = "mrk_file"
DATA_FILE_KEY = "data_file"
MODE_KEY = "mode"
MAPPING_KEY = "mapping"
RECURSIVE_KEY = "recursive"


class MrkSubstitutorPlugin(BasePlugin):
    """
    Plugin para substituir valores em arquivos MRK a partir de dados CSV/SHP/GPKG.
    """

    def __init__(self, parent=None):
        super().__init__(
            tool_key=ToolKey.MRK_SUBSTITUTOR.value,
            parent=parent,
            title="Mrk Substituidor",
        )
        self._worker: Optional[QThread] = None
        self._update_ui_for_mode()
        self.logger.info("MrkSubstitutorPlugin inicializado", code="MRK_READY")

    # ══════════════════════════════════════════════════════════════════
    # UI
    # ══════════════════════════════════════════════════════════════════

    def _build_ui(self):
        super()._build_ui()
        self._btns = ExecutionButtons(self, {
            "save_config": {"text": "SALVAR CONFIG", "callback": self._on_save_config, "type": "secondary"},
            "executar": {"text": "EXECUTAR", "callback": self._on_executar, "type": "primary"},
        })
        self.main_layout.addWidget(self._btns)

        self._grid_scenario = GridRadio(SCENARIO_CONFIG, num_columns=2)
        self._grid_scenario.changed.connect(self._on_scenario_changed)
        grp_scenario = GroupPainel("Modo de Processamento")
        grp_scenario.group_layout.addWidget(self._grid_scenario)
        self.main_layout.addWidget(grp_scenario)

        self._sel_mrk_file = SimpleSelector("Arquivo MRK:", "", placeholder="Caminho do arquivo .MRK...", browse_mode="open_file", file_filter="MRK (*.MRK *.mrk);;Todos (*.*)", label_width=140)
        self._sel_mrk_dir = SimpleSelector("Pasta MRK:", "", placeholder="Caminho da pasta com arquivos .MRK...", browse_mode="directory", label_width=140)
        self._sel_data = SimpleSelector("Dados Origem:", "", placeholder="Caminho do CSV/SHP/GPKG...", browse_mode="open_file", file_filter="Dados (*.csv *.shp *.gpkg);;CSV (*.csv);;Shapefile (*.shp);;GeoPackage (*.gpkg);;Todos (*.*)", label_width=140)
        self._sel_output = SimpleSelector("Pasta Saida:", "", placeholder="Pasta onde os MRKs serao salvos...", browse_mode="directory", label_width=140)
        self._grid_opts = GridCheckBox(config={RECURSIVE_KEY: {"label": "Vasculhar subpastas", "description": "Inclui subpastas recursivamente (modo lote)", "default": False}}, num_columns=1)

        grp_files = GroupPainel("Arquivos")
        grp_files.group_layout.addWidget(self._sel_mrk_file)
        grp_files.group_layout.addWidget(self._sel_mrk_dir)
        grp_files.group_layout.addWidget(self._sel_data)
        grp_files.group_layout.addWidget(self._sel_output)
        grp_files.group_layout.addWidget(self._grid_opts)

        self._mapping = GridFieldMapping(MAPPING_CONFIG)
        grp_map = GroupPainel("Mapeamento de Campos")
        grp_map.group_layout.addWidget(self._mapping)

        self.main_layout.addWidget(GridGroupPainel(grp_files, grp_map))

    # ══════════════════════════════════════════════════════════════════
    # Cenario
    # ══════════════════════════════════════════════════════════════════

    def _on_scenario_changed(self, mode: str):
        self._update_ui_for_mode()

    def _update_ui_for_mode(self):
        mode = self._grid_scenario.selected
        self._sel_mrk_file.setVisible(mode == MODE_SINGLE)
        self._sel_mrk_dir.setVisible(mode == MODE_BATCH)
        self._sel_data.setVisible(mode == MODE_SINGLE)

    # ══════════════════════════════════════════════════════════════════
    # Mapping
    # ══════════════════════════════════════════════════════════════════

    def _get_active_mapping(self) -> Dict[str, str]:
        mapping = {}
        for key, data in self._mapping.values.items():
            if data["enabled"]:
                dc = data["from"].strip()
                mf = data["to"].strip()
                if dc and mf:
                    mapping[mf] = dc
        return mapping

    def _find_data_file(self, mrk_path: Path) -> Optional[str]:
        """Busca arquivo de dados correspondente ao MRK (mesmo diretorio)."""
        base_name = mrk_path.stem
        directory = mrk_path.parent
        if not directory.is_dir():
            return None
        for ext in [".gpkg", ".shp", ".csv"]:
            candidate = directory / f"{base_name}{ext}"
            if candidate.is_file():
                return str(candidate)
        candidates = []
        for ext in [".gpkg", ".shp", ".csv"]:
            for f in directory.glob(f"*{ext}"):
                if f.is_file() and base_name.lower() in f.stem.lower():
                    candidates.append(f)
        if candidates:
            best = min(candidates, key=lambda p: 0 if p.suffix.lower() == ".gpkg" else 1 if p.suffix.lower() == ".shp" else 2)
            return str(best)
        return None

    # ══════════════════════════════════════════════════════════════════
    # Preferences
    # ══════════════════════════════════════════════════════════════════

    def load_prefs(self):
        self._sel_mrk_file.set_path(self.preferences.get(MRK_FILE_KEY, ""))
        self._sel_mrk_dir.set_path(self.preferences.get(MRK_DIR_KEY, ""))
        self._sel_data.set_path(self.preferences.get(DATA_FILE_KEY, ""))
        self._sel_output.set_path(self.preferences.get(OUTPUT_DIR_KEY, ""))
        mode = self.preferences.get(MODE_KEY, MODE_SINGLE)
        self._grid_scenario.set_selected(mode)
        mapping_prefs = self.preferences.get(MAPPING_KEY, {})
        if mapping_prefs:
            self._mapping.set_values(mapping_prefs, block_signals=True)
        opts = self.preferences.get("options", {})
        if opts:
            self._grid_opts.set_all(opts)
        self._update_ui_for_mode()

    def save_prefs(self):
        self.preferences[MRK_FILE_KEY] = self._sel_mrk_file.path()
        self.preferences[MRK_DIR_KEY] = self._sel_mrk_dir.path()
        self.preferences[DATA_FILE_KEY] = self._sel_data.path()
        self.preferences[OUTPUT_DIR_KEY] = self._sel_output.path()
        self.preferences[MODE_KEY] = self._grid_scenario.selected or MODE_SINGLE
        self.preferences[MAPPING_KEY] = self._mapping.all
        self.preferences["options"] = self._grid_opts.all

    # ══════════════════════════════════════════════════════════════════
    # Execucao
    # ══════════════════════════════════════════════════════════════════

    def _on_save_config(self):
        self.save_prefs()
        MessageBox.show_info("Configuracao salva!", title="Salvo")

    def _on_executar(self):
        mapping = self._get_active_mapping()
        if not mapping:
            MessageBox.show_warning("Habilite pelo menos um campo no Mapeamento.", title="Aviso")
            return
        output_dir_str = self._sel_output.path()
        if not output_dir_str:
            MessageBox.show_warning("Selecione uma pasta de saida.", title="Aviso")
            return

        self._btns.set_all_enabled(False)

        # Sinaliza inicio de execucao (ativa HUD + reseta progress)
        SignalManager.instance().execution_started.emit(self.tool_key)
        SignalManager.instance().console_message.emit(f"[{self.tool_key}] Iniciando execucao...")
        SignalManager.instance().progress_update.emit(0.0)
        SignalManager.instance().hud_show.emit({"message": "Preparando..."})

        from core.task.MrkBatchWorker import MrkBatchWorker

        output_dir = Path(output_dir_str)
        output_dir.mkdir(parents=True, exist_ok=True)

        if self._grid_scenario.selected == MODE_SINGLE:
            self._worker = self._create_single_worker(mapping, output_dir)
        else:
            self._worker = self._create_batch_worker(mapping, output_dir)

        if self._worker:
            self._worker.start()

    def _cleanup_worker(self):
        if self._worker:
            try:
                self._worker.quit()
                self._worker.wait(500)
            except Exception:
                pass
            self._worker = None
        self._btns.set_all_enabled(True)

    def _on_progress_both(self, progress: float):
        """Propaga progresso para ProgressBar e HUD simultaneamente."""
        SignalManager.instance().progress_update.emit(progress)
        SignalManager.instance().hud_update.emit({
            "message": f"Processando... {progress:.1f}%",
            "progress": progress,
        })

    # ══════════════════════════════════════════════════════════════════
    # Single Worker
    # ══════════════════════════════════════════════════════════════════

    def _create_single_worker(self, mapping: Dict[str, str], output_dir: Path):
        mrk_path_str = self._sel_mrk_file.path()
        data_path_str = self._sel_data.path()
        if not mrk_path_str or not data_path_str:
            self._cleanup_worker()
            MessageBox.show_warning("Selecione o arquivo MRK e de dados.", title="Aviso")
            return None

        from core.task.MrkBatchWorker import MrkSingleTask

        task = MrkSingleTask(
            mrk_path=mrk_path_str,
            data_path=data_path_str,
            mapping=mapping,
            output_dir=str(output_dir),
            tool_key=self.tool_key,
        )
        task.finished_ok.connect(self._on_single_done)
        task.failed.connect(self._on_worker_failed)
        task.progress_updated.connect(lambda p: self._on_progress_both(p))
        task.console_msg.connect(lambda m: SignalManager.instance().console_message.emit(f"[MrkSubst] {m}"))
        return task

    def _on_single_done(self, total: int):
        self._cleanup_worker()
        msg = f"Concluido! {total} substituicoes."
        self.logger.info(msg, code="MRK_SINGLE_DONE")
        SignalManager.instance().execution_finished.emit(self.tool_key)
        SignalManager.instance().console_message.emit(f"[MrkSubst] {msg}")
        MessageBox.show_info(msg, title="Concluido")
        self.save_prefs()

    def _on_worker_failed(self, error: str):
        self._cleanup_worker()
        self.logger.error("Erro no worker", code="MRK_WORKER_ERR", error=error)
        SignalManager.instance().execution_cancelled.emit(self.tool_key)
        SignalManager.instance().console_message.emit(f"[MrkSubst] ERRO: {error}")
        MessageBox.show_error(f"Erro: {error}", title="Erro")

    # ══════════════════════════════════════════════════════════════════
    # Batch Worker
    # ══════════════════════════════════════════════════════════════════

    def _create_batch_worker(self, mapping: Dict[str, str], output_dir: Path):
        mrk_dir_str = self._sel_mrk_dir.path()
        if not mrk_dir_str:
            self._cleanup_worker()
            MessageBox.show_warning("Selecione a pasta com MRKs.", title="Aviso")
            return None

        recursive = bool(self._grid_opts.all.get(RECURSIVE_KEY, False))
        mrk_paths = ExplorerUtils.find_files(mrk_dir_str, MRK_EXTENSIONS, recursive=recursive)

        if not mrk_paths:
            self._cleanup_worker()
            MessageBox.show_warning("Nenhum arquivo .MRK encontrado.", title="Aviso")
            return None

        SignalManager.instance().console_message.emit(f"[MrkSubst] {len(mrk_paths)} MRKs encontrados")

        from core.task.MrkBatchWorker import MrkBatchWorker

        worker = MrkBatchWorker(
            mrk_paths=mrk_paths,
            mapping=mapping,
            output_dir=str(output_dir),
            tool_key=self.tool_key,
        )
        worker.finished_ok.connect(self._on_batch_done)
        worker.failed.connect(self._on_worker_failed)
        worker.progress_updated.connect(lambda p: self._on_progress_both(p))
        worker.console_msg.connect(lambda m: SignalManager.instance().console_message.emit(f"[MrkSubst] {m}"))
        worker.hud_update_msg.connect(lambda m, p: SignalManager.instance().hud_update.emit({"message": m, "progress": p}))
        return worker

    def _on_batch_done(self, total: int, processed: int, failed: int):
        self._cleanup_worker()
        msg = f"Lote concluido! {total} substituicoes em {processed} MRKs."
        if failed:
            msg += f" {failed} falhas."
        self.logger.info(msg, code="MRK_BATCH_DONE")
        SignalManager.instance().execution_finished.emit(self.tool_key)
        SignalManager.instance().console_message.emit(f"[MrkSubst] {msg}")
        MessageBox.show_info(msg, title="Concluido")
        self.save_prefs()
