# -*- coding: utf-8 -*-
"""
MrkSubstitutorPlugin — Substitui valores de altitude (Ellh / Lat / Lon) em arquivos MRK
==========================================================================================
Plugin que converte o script legado substituir_mrk.py em uma ferramenta Aetheris ToolBox.

Cenarios de uso:
  - Cenario 1 (Arquivo Unico): Usuario informa 1 CSV/SHP + 1 MRK especifico.
  - Cenario 2 (Lote por Pasta): Usuario informa pasta com MRKs. O nome do MRK
    (sem extensao) e a chave para buscar dados correspondentes (.gpkg > .shp > .csv).

Integracoes Obrigatorias:
  - LogUtils (self.logger) em todos os pontos criticos
  - SignalManager para progresso e console
  - Preferences para persistencia
  - MessageBox para dialogos com usuario
  - ExplorerUtils para selecao de arquivos (Contrato 17)
  - ExecutionButtons para botoes de acao (Contrato 18)
  - VectorLayerSource para leitura de dados (Contrato 25)
  - ToolKey.XXX.value para log (Contrato 26)
"""

from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Dict, List, Optional

from core.enum.ToolKey import ToolKey
from core.manager.SignalManager import SignalManager
from plugins.BasePlugin import BasePlugin
from resources.widgets.ExecutionButtons import ExecutionButtons
from resources.widgets.GridCheckBox import GridCheckBox
from resources.widgets.GridFieldMapping import GridFieldMapping
from resources.widgets.GridRadio import GridRadio
from resources.widgets.GridLabel import GridLabel
from resources.widgets.GroupPainel import GroupPainel
from resources.widgets.GridGroupPainel import GridGroupPainel
from resources.widgets.SimpleSelector import SimpleSelector
from utils.ExplorerUtils import ExplorerUtils
from utils.MessageBox import MessageBox
from utils.vector.VectorLayerSource import VectorLayerSource


# ── Constantes ─────────────────────────────────────────────────────

MODE_SINGLE = "single"
MODE_BATCH = "batch"

SCENARIO_CONFIG = {
    MODE_SINGLE: {
        "label": "Arquivo Unico",
        "description": "Processa 1 MRK com 1 arquivo de dados especifico",
        "default": True,
        "tooltip": "Informe o arquivo MRK e o arquivo de dados manualmente",
    },
    MODE_BATCH: {
        "label": "Lote por Pasta",
        "description": "Busca MRKs e dados correspondentes por chave no nome",
        "default": False,
        "tooltip": "Selecione a pasta com MRKs. O nome do MRK e a chave para buscar dados",
    },
}

MAPPING_CONFIG = {
    "altitude": {
        "from_label": "Campo Origem:",
        "from_placeholder": "Ex: AbsZ",
        "to_label": "Campo MRK:",
        "to_placeholder": "Ex: Ellh",
        "default_from": "AbsZ",
        "default_to": "Ellh",
        "default_enabled": True,
        "tooltip": "Mapeamento de altitude - campo de origem para campo Ellh no MRK",
    },
    "latitude": {
        "from_label": "Campo Origem:",
        "from_placeholder": "Ex: Latitude",
        "to_label": "Campo MRK:",
        "to_placeholder": "Ex: Lat",
        "default_from": "Latitude",
        "default_to": "Lat",
        "default_enabled": False,
        "tooltip": "Mapeamento de latitude - campo de origem para campo Lat no MRK",
    },
    "longitude": {
        "from_label": "Campo Origem:",
        "from_placeholder": "Ex: Longitude",
        "to_label": "Campo MRK:",
        "to_placeholder": "Ex: Lon",
        "default_from": "Longitude",
        "default_to": "Lon",
        "default_enabled": False,
        "tooltip": "Mapeamento de longitude - campo de origem para campo Lon no MRK",
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
        self._update_ui_for_mode()
        self.logger.info("MrkSubstitutorPlugin inicializado", code="MRK_READY")

    # ══════════════════════════════════════════════════════════════════
    # UI
    # ══════════════════════════════════════════════════════════════════

    def _build_ui(self):
        """Constroi a interface do plugin."""
        super()._build_ui()

        # ── Execution Buttons ─────────────────────────────────────────
        self._btns = ExecutionButtons(self, {
            "save_config": {
                "text": "SALVAR CONFIG",
                "callback": self._on_save_config,
                "type": "secondary",
                "description": "Salva configuracao atual nas preferencias",
            },
            "executar": {
                "text": "EXECUTAR",
                "callback": self._on_executar,
                "type": "primary",
                "description": "Executa a substituicao nos MRKs",
            },
        })
        self.main_layout.addWidget(self._btns)

        # ── Grid Radio: Cenario ──────────────────────────────────────
        self._grid_scenario = GridRadio(
            SCENARIO_CONFIG,
            num_columns=2,
        )
        self._grid_scenario.changed.connect(self._on_scenario_changed)

        grp_scenario = GroupPainel("Modo de Processamento")
        grp_scenario.group_layout.addWidget(self._grid_scenario)

        # ── Painel Pastas (coluna 0) ─────────────────────────────────
        self._sel_mrk_file = SimpleSelector(
            "Arquivo MRK:",
            "",
            placeholder="Caminho do arquivo .MRK...",
            browse_mode="open_file",
            file_filter="MRK (*.MRK *.mrk);;Todos (*.*)",
            label_width=140,
        )
        self._sel_mrk_dir = SimpleSelector(
            "Pasta MRK:",
            "",
            placeholder="Caminho da pasta com arquivos .MRK...",
            browse_mode="directory",
            label_width=140,
        )
        self._sel_data = SimpleSelector(
            "Dados Origem:",
            "",
            placeholder="Caminho do CSV/SHP/GPKG...",
            browse_mode="open_file",
            file_filter="Dados (*.csv *.shp *.gpkg);;CSV (*.csv);;Shapefile (*.shp);;GeoPackage (*.gpkg);;Todos (*.*)",
            label_width=140,
        )
        self._sel_output = SimpleSelector(
            "Pasta Saida:",
            "",
            placeholder="Pasta onde os MRKs processados serao salvos...",
            browse_mode="directory",
            label_width=140,
        )

        # Opcoes
        self._grid_opts = GridCheckBox(
            config={
                RECURSIVE_KEY: {
                    "label": "Vasculhar subpastas",
                    "description": "Inclui arquivos de subpastas recursivamente (modo lote)",
                    "default": False,
                },
            },
            num_columns=1,
        )

        grp_files = GroupPainel("Arquivos")
        grp_files.group_layout.addWidget(self._sel_mrk_file)
        grp_files.group_layout.addWidget(self._sel_mrk_dir)
        grp_files.group_layout.addWidget(self._sel_data)
        grp_files.group_layout.addWidget(self._sel_output)
        grp_files.group_layout.addWidget(self._grid_opts)

        # ── Painel Mapeamento (coluna 1) ─────────────────────────────
        self._mapping = GridFieldMapping(MAPPING_CONFIG)

        grp_map = GroupPainel("Mapeamento de Campos")
        grp_map.group_layout.addWidget(self._mapping)

        # ── Status ───────────────────────────────────────────────────
        self._grid_info = GridLabel(
            config={
                "status": {
                    "label": "Status",
                    "value": "Pronto",
                    "description": "Status atual do processamento",
                },
                "mrk_count": {
                    "label": "MRKs",
                    "value": "0 encontrados",
                },
                "data_records": {
                    "label": "Registros",
                    "value": "0",
                },
            },
            columns=1,
        )

        grp_status = GroupPainel("Status")
        grp_status.group_layout.addWidget(self._grid_info)

        # ── Grid: colunas 0 e 1 ──────────────────────────────────────
        left_painel = GroupPainel("Configuracao")
        left_painel.group_layout.addWidget(grp_files)
        left_painel.group_layout.addWidget(grp_status)

        right_painel = GroupPainel("Mapeamento")
        right_painel.group_layout.addWidget(grp_map)

        grid_painels = GridGroupPainel(grp_scenario, left_painel, right_painel)
        self.main_layout.addWidget(grid_painels)

    # ══════════════════════════════════════════════════════════════════
    # Cenario / Visibilidade
    # ══════════════════════════════════════════════════════════════════

    def _on_scenario_changed(self, mode: str):
        """Cenario mudou — atualiza visibilidade dos campos."""
        self.logger.info(f"Modo alterado: {mode}", code="MRK_MODE_CHANGE")
        self._update_ui_for_mode()

    def _update_ui_for_mode(self):
        """Atualiza visibilidade dos SimpleSelectors conforme o cenario."""
        mode = self._grid_scenario.selected
        is_batch = (mode == MODE_BATCH)
        is_single = (mode == MODE_SINGLE)

        self._sel_mrk_file.setVisible(is_single)
        self._sel_mrk_dir.setVisible(is_batch)
        self._sel_data.setVisible(is_single)

    # ══════════════════════════════════════════════════════════════════
    # Navegacao / Busca de Arquivos
    # ══════════════════════════════════════════════════════════════════

    def _get_active_mapping(self) -> Dict[str, Dict[str, str]]:
        """Retorna mapeamento ativo: {mrk_field: data_column}."""
        mapping = {}
        values = self._mapping.values
        for key, data in values.items():
            if data["enabled"]:
                data_col = data["from"].strip()
                mrk_field = data["to"].strip()
                if data_col and mrk_field:
                    mapping[mrk_field] = data_col
        return mapping

    def _find_mrk_files(self, root_path: str) -> List[Path]:
        """
        Encontra arquivos .MRK (case insensitive) no diretorio.

        Args:
            root_path: Caminho do diretorio.

        Returns:
            Lista de Paths dos arquivos .MRK encontrados.
        """
        mrk_files: List[Path] = []
        root = Path(root_path)
        if not root.is_dir():
            return mrk_files

        recursive = bool(self._grid_opts.all.get(RECURSIVE_KEY, False))
        pattern = "**/*" if recursive else "*"

        for f in root.glob(pattern):
            if f.is_file() and f.suffix.lower() == ".mrk":
                mrk_files.append(f)

        mrk_files.sort()
        return mrk_files

    def _find_data_file_for_mrk(self, mrk_path: Path, search_dir: str | None = None) -> Optional[str]:
        """
        Busca arquivo de dados correspondente a um MRK.

        Logica:
        1. Extrai base_name do MRK (sem extensao).
        2. Se search_dir for informado, busca la.
        3. Senao, busca no mesmo diretorio do MRK.
        4. Procura por: base_name.gpkg > base_name.shp > base_name.csv
        5. Se nao achar, busca qualquer arquivo contendo base_name como substring.
        6. Prioriza .gpkg > .shp > .csv.

        Args:
            mrk_path: Path do arquivo MRK.
            search_dir: Diretorio de busca (opcional).

        Returns:
            Caminho do arquivo de dados encontrado, ou None.
        """
        base_name = mrk_path.stem  # sem extensao
        directory = Path(search_dir) if search_dir else mrk_path.parent

        if not directory.is_dir():
            return None

        # Busca exata primeiro
        for ext in [".gpkg", ".shp", ".csv"]:
            candidate = directory / f"{base_name}{ext}"
            if candidate.is_file():
                self.logger.info(
                    f"Arquivo de dados encontrado para {mrk_path.name}",
                    code="MRK_DATA_FOUND",
                    data_path=str(candidate),
                )
                SignalManager.instance().console_message.emit(
                    f"[MrkSubst] Dados encontrados: {candidate.name}"
                )
                return str(candidate)

        # Busca flexivel: contem base_name como substring
        candidates: List[Path] = []
        for ext in [".gpkg", ".shp", ".csv"]:
            for f in directory.glob(f"*{ext}"):
                if f.is_file() and base_name.lower() in f.stem.lower():
                    candidates.append(f)

        if candidates:
            # Prioriza .gpkg > .shp > .csv
            def _priority(p: Path) -> int:
                ext = p.suffix.lower()
                if ext == ".gpkg":
                    return 0
                if ext == ".shp":
                    return 1
                return 2

            best = min(candidates, key=_priority)
            self.logger.info(
                f"Arquivo de dados encontrado (flex) para {mrk_path.name}",
                code="MRK_DATA_FOUND_FLEX",
                data_path=str(best),
            )
            SignalManager.instance().console_message.emit(
                f"[MrkSubst] Dados encontrados: {best.name}"
            )
            return str(best)

        self.logger.warning(
            f"Nenhum arquivo de dados encontrado para {mrk_path.name}",
            code="MRK_DATA_NOT_FOUND",
        )
        SignalManager.instance().console_message.emit(
            f"[MrkSubst] AVISO: Nenhum dado para {mrk_path.name}"
        )
        return None

    # ══════════════════════════════════════════════════════════════════
    # Logica Central (extraida do substituir_mrk.py)
    # ══════════════════════════════════════════════════════════════════

    @staticmethod
    def _parse_mrk_line(line: str) -> Dict:
        """
        Analisa uma linha do MRK (formato TSV) e retorna:
          - parts: lista das colunas
          - replacements: dict {campo: {value_str, len, idx}}
        """
        parts = line.split("\t")
        replacements: Dict[str, Dict] = {}
        indices: Dict[str, int] = {}

        for i, col in enumerate(parts):
            col_stripped = col.strip()
            for field in ["Lat", "Lon", "Ellh"]:
                pattern = rf"^(.+),{re.escape(field)}$"
                match = re.match(pattern, col_stripped)
                if match:
                    value_str = match.group(1).strip()
                    replacements[field] = {
                        "value_str": value_str,
                        "length": len(value_str),
                        "idx": i,
                    }
                    indices[field] = i
                    break

        return {
            "parts": parts,
            "replacements": replacements,
            "indices": indices,
        }

    @staticmethod
    def _pad_value(original_value: str, new_value: str) -> str:
        """
        Ajusta o novo valor para ter o MESMO comprimento do valor original,
        preservando a posicao decimal.
        """
        original_length = len(original_value)
        result = new_value

        if len(result) == original_length:
            return result

        if "." in original_value:
            if "." in result:
                original_parts = original_value.split(".")
                new_parts = result.split(".")
                original_decimals = len(original_parts[1]) if len(original_parts) > 1 else 0
                new_decimals = len(new_parts[1]) if len(new_parts) > 1 else 0

                if new_decimals < original_decimals:
                    result = result + "0" * (original_decimals - new_decimals)
                elif new_decimals > original_decimals:
                    result = new_parts[0] + "." + new_parts[1][:original_decimals]

                if len(result) < original_length:
                    diff = original_length - len(result)
                    result = result + "0" * diff
            else:
                original_parts = original_value.split(".")
                original_decimals = len(original_parts[1]) if len(original_parts) > 1 else 0
                result = result + "." + "0" * original_decimals
                if len(result) < original_length:
                    diff = original_length - len(result)
                    result = result + "0" * diff

            if len(result) > original_length:
                result = result[:original_length]

            return result

        if len(result) < original_length:
            result = result + "0" * (original_length - len(result))
        elif len(result) > original_length:
            result = result[:original_length]

        return result

    @staticmethod
    def _build_mrk_line(parts: List[str], indices: Dict, new_values: Dict,
                        original_replacements: Dict) -> str:
        """Reconstroi a linha do MRK preservando a tabulacao."""
        for field, new_value in new_values.items():
            if field in indices:
                idx = indices[field]
                col_original = parts[idx].strip()
                original_value = original_replacements[field]["value_str"]
                padded = MrkSubstitutorPlugin._pad_value(original_value, new_value)

                match = re.match(r"^.*(," + re.escape(field) + r")$", col_original)
                if match:
                    suffix = match.group(1)
                    parts[idx] = f"{padded}{suffix}"

        return "\t".join(parts)

    def _process_mrk(self, mrk_path: Path, data: List[dict],
                     mapping: Dict[str, str], output_dir: Path) -> int:
        """
        Processa um arquivo MRK com os dados fornecidos.

        Args:
            mrk_path: Path do arquivo MRK.
            data: Lista de dicts com os dados (do VectorLayerSource).
            mapping: Dict {mrk_field: data_column} (ex: {"Ellh": "AbsZ"}).
            output_dir: Diretorio de saida.

        Returns:
            Numero de substituicoes realizadas.
        """
        # Le MRK
        with open(mrk_path, "r", encoding="utf-8") as f:
            mrk_lines = f.readlines()

        output_lines: List[str] = []
        total_replacements = 0
        total_mrk_lines = len(mrk_lines)
        total_data_lines = len(data)
        process_count = min(total_mrk_lines, total_data_lines)

        for idx in range(process_count):
            raw_line = mrk_lines[idx]
            line_no_nl = raw_line.rstrip("\n").rstrip("\r")
            row_data = data[idx]

            parsed = self._parse_mrk_line(line_no_nl)
            parts = parsed["parts"]
            replacements = parsed["replacements"]
            indices = parsed["indices"]

            new_values: Dict[str, str] = {}
            for mrk_field, data_column in mapping.items():
                if mrk_field in indices and data_column in row_data:
                    new_val = row_data[data_column].strip()
                    old_val = replacements[mrk_field]["value_str"]
                    if new_val and new_val != old_val:
                        new_values[mrk_field] = new_val
                        total_replacements += 1
                        self.logger.info(
                            f"[{mrk_path.name}] Linha {idx + 1}: "
                            f"{mrk_field}: '{old_val}' (len={len(old_val)}) -> "
                            f"'{new_val}' (len={len(new_val)})",
                            code="MRK_REPLACE",
                        )
                        SignalManager.instance().console_message.emit(
                            f"[MrkSubst] {mrk_path.name} L{idx+1}: {mrk_field} {old_val} -> {new_val}"
                        )

            if new_values:
                modified = self._build_mrk_line(parts, indices, new_values, replacements)
                if raw_line.endswith("\r\n"):
                    output_lines.append(modified + "\r\n")
                else:
                    output_lines.append(modified + "\n")
            else:
                output_lines.append(raw_line)

        # Copia linhas restantes se MRK tem mais linhas que dados
        if total_mrk_lines > process_count:
            for idx in range(process_count, total_mrk_lines):
                output_lines.append(mrk_lines[idx])

        # Garante diretorio de saida
        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = output_dir / mrk_path.name

        with open(output_path, "w", encoding="utf-8") as f:
            f.writelines(output_lines)

        self.logger.info(
            f"Arquivo gerado: {output_path.name} | Substituicoes: {total_replacements}",
            code="MRK_DONE",
        )
        SignalManager.instance().console_message.emit(
            f"[MrkSubst] {output_path.name} -> {total_replacements} substituicoes"
        )

        return total_replacements

    # ══════════════════════════════════════════════════════════════════
    # Execucao
    # ══════════════════════════════════════════════════════════════════

    def _on_save_config(self):
        """Salva configuracao atual nas preferencias."""
        self.save_prefs()
        MessageBox.show_info("Configuracao salva com sucesso!", title="Salvo")

    def _on_executar(self):
        """Executa a substituicao nos MRKs."""
        self.logger.info("Iniciando execucao", code="MRK_EXEC_START")
        SignalManager.instance().console_message.emit("[MrkSubst] Iniciando processamento...")

        # Valida mapeamento
        mapping = self._get_active_mapping()
        if not mapping:
            MessageBox.show_warning(
                "Nenhum mapeamento ativo. Habilite pelo menos um campo no Mapeamento de Campos.",
                title="Aviso",
            )
            return

        # Valida pasta de saida
        output_dir_str = self._sel_output.path()
        if not output_dir_str:
            MessageBox.show_warning("Selecione uma pasta de saida.", title="Aviso")
            return
        output_dir = Path(output_dir_str)
        output_dir.mkdir(parents=True, exist_ok=True)

        mode = self._grid_scenario.selected
        total_replacements = 0
        total_mrks = 0

        try:
            if mode == MODE_SINGLE:
                total_replacements = self._exec_single(mapping, output_dir)
            else:
                total_replacements = self._exec_batch(mapping, output_dir)

            # Atualiza status
            self._grid_info.set("status", "Concluido")
            self._grid_info.set("mrk_count", f"{total_mrks} processados")

            msg = f"Processamento concluido! Total de substituicoes: {total_replacements}"
            self.logger.info(msg, code="MRK_EXEC_DONE")
            SignalManager.instance().console_message.emit(f"[MrkSubst] {msg}")
            SignalManager.instance().progress_update.emit(100.0)
            MessageBox.show_info(msg, title="Concluido")

        except Exception as e:
            self.logger.error("Erro durante execucao", code="MRK_EXEC_ERR", error=str(e))
            SignalManager.instance().console_message.emit(
                f"[MrkSubst] ERRO: {str(e)}"
            )
            MessageBox.show_error(f"Erro durante execucao: {str(e)}", title="Erro")

        self.save_prefs()

    def _exec_single(self, mapping: Dict[str, str], output_dir: Path) -> int:
        """Executa no modo arquivo unico (Cenario 1)."""
        mrk_path_str = self._sel_mrk_file.path()
        data_path_str = self._sel_data.path()

        if not mrk_path_str:
            MessageBox.show_warning("Selecione o arquivo MRK.", title="Aviso")
            return 0
        if not data_path_str:
            MessageBox.show_warning("Selecione o arquivo de dados.", title="Aviso")
            return 0

        mrk_path = Path(mrk_path_str)
        if not mrk_path.is_file():
            MessageBox.show_warning(f"Arquivo MRK nao encontrado: {mrk_path_str}", title="Erro")
            return 0

        self._grid_info.set("mrk_count", "1 encontrado")
        self._grid_info.set("status", "Carregando dados...")
        SignalManager.instance().console_message.emit(f"[MrkSubst] Carregando: {data_path_str}")

        data = VectorLayerSource.read(data_path_str, tool_key=self.tool_key)
        self._grid_info.set("data_records", str(len(data)))

        self._grid_info.set("status", "Processando...")
        SignalManager.instance().progress_update.emit(10.0)

        total = self._process_mrk(mrk_path, data, mapping, output_dir)
        SignalManager.instance().progress_update.emit(100.0)
        return total

    def _exec_batch(self, mapping: Dict[str, str], output_dir: Path) -> int:
        """Executa no modo lote por pasta (Cenario 2)."""
        mrk_dir_str = self._sel_mrk_dir.path()

        if not mrk_dir_str:
            MessageBox.show_warning("Selecione a pasta com arquivos MRK.", title="Aviso")
            return 0

        mrk_files = self._find_mrk_files(mrk_dir_str)
        if not mrk_files:
            MessageBox.show_warning(
                "Nenhum arquivo .MRK encontrado na pasta especificada.",
                title="Aviso",
            )
            return 0

        self._grid_info.set("mrk_count", f"{len(mrk_files)} encontrados")
        self._grid_info.set("status", "Processando lote...")
        SignalManager.instance().console_message.emit(
            f"[MrkSubst] {len(mrk_files)} MRKs encontrados"
        )

        total_replacements = 0
        total_mrks = len(mrk_files)

        for idx, mrk_path in enumerate(mrk_files):
            # Progresso
            pct = (idx / total_mrks) * 90.0 + 10.0
            SignalManager.instance().progress_update.emit(pct)

            # Busca dados correspondentes
            data_path = self._find_data_file_for_mrk(mrk_path)
            if data_path is None:
                continue

            SignalManager.instance().console_message.emit(
                f"[MrkSubst] Processando {mrk_path.name}..."
            )

            try:
                data = VectorLayerSource.read(data_path, tool_key=self.tool_key)
                total = self._process_mrk(mrk_path, data, mapping, output_dir)
                total_replacements += total
            except Exception as e:
                self.logger.error(
                    f"Erro ao processar {mrk_path.name}",
                    code="MRK_BATCH_ERR",
                    error=str(e),
                )
                SignalManager.instance().console_message.emit(
                    f"[MrkSubst] ERRO em {mrk_path.name}: {str(e)}"
                )

        return total_replacements

    # ══════════════════════════════════════════════════════════════════
    # Preferences
    # ══════════════════════════════════════════════════════════════════

    def load_prefs(self):
        """Carrega preferencias salvas."""
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
        """Salva preferencias atuais."""
        self.preferences[MRK_FILE_KEY] = self._sel_mrk_file.path()
        self.preferences[MRK_DIR_KEY] = self._sel_mrk_dir.path()
        self.preferences[DATA_FILE_KEY] = self._sel_data.path()
        self.preferences[OUTPUT_DIR_KEY] = self._sel_output.path()
        self.preferences[MODE_KEY] = self._grid_scenario.selected or MODE_SINGLE
        self.preferences[MAPPING_KEY] = self._mapping.all
        self.preferences["options"] = self._grid_opts.all