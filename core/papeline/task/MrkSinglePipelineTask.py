# -*- coding: utf-8 -*-
"""
MrkSinglePipelineTask — Tasks para processamento MRK (BaseTask + QThread Workers)
=================================================================================
Arquivo unificado contendo:
  - MrkSinglePipelineTask (BaseTask)  → usado na pipeline assíncrona
  - MrkSingleTask         (QThread)   → processa 1 MRK com dados já fornecidos
  - MrkBatchWorker        (QThread)   → processa N MRKs em lote sequencial

Uso na pipeline:
    class MrkProcessStep(BaseStep):
        def create_task(self, context):
            return MrkSinglePipelineTask(...)

Uso no plugin:
    task = MrkSingleTask(mrk_path, data_path, mapping, output_dir)
    task.finished_ok.connect(self._on_single_done)
    task.start()

    worker = MrkBatchWorker(mrk_paths, mapping, output_dir)
    worker.finished_ok.connect(self._on_batch_done)
    worker.start()
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Dict, List

from PySide6.QtCore import QThread, Signal

from ..BaseTask import BaseTask
from core.config.LogUtils import LogUtils
from core.enum.ToolKey import ToolKey


# ═══════════════════════════════════════════════════════════════════
# MrkSinglePipelineTask  (BaseTask — pipeline assíncrona)
# ═══════════════════════════════════════════════════════════════════

class MrkSinglePipelineTask(BaseTask):
    """
    Processa UM arquivo MRK contra dados fornecidos.
    Herda de BaseTask para uso no sistema de pipeline assíncrono.

    A lógica de substituição (parse + pad + write) é a mesma do
    MrkSingleTask original, mas sem dependência de QThread/Signals.

    Args:
        mrk_path: Caminho do arquivo .MRK.
        data: Lista de dicts com dados de substituicao.
        mapping: Mapeamento campo_mrk -> coluna_dados.
        output_dir: Diretório de saída para o MRK processado.
        emit_console: Se True, registra mensagens via logger.
    """
    def __init__(
        self,
        mrk_path: str,
        data: List[dict],
        mapping: Dict[str, str],
        output_dir: str,
        *,
        emit_console: bool = True,
    ):
        super().__init__(description=f"Processar MRK: {Path(mrk_path).name}")
        self._mrk_path = mrk_path
        self._data = data
        self._mapping = mapping
        self._output_dir = output_dir
        self._emit_console = emit_console

    # ── BaseTask ─────────────────────────────────────────────────────

    def _run(self) -> bool:
        """Executa o processamento MRK em background."""
        try:
            total = MrkSingleTask._process_mrk_static(
                Path(self._mrk_path), self._data, self._mapping,
                self._output_dir, emit_console=self._emit_console,
            )
            self.result = {
                "path": self._mrk_path,
                "replacements": total,
                "output_path": str(Path(self._output_dir) / Path(self._mrk_path).name),
            }
            return True
        except Exception as e:
            self.exception = e
            return False


# ═══════════════════════════════════════════════════════════════════
# MrkSingleTask  (QThread — processa 1 MRK)
# ═══════════════════════════════════════════════════════════════════

class MrkSingleTask(QThread):
    """
    Processa UM arquivo MRK.
    Le os dados do arquivo + processa em background.

    Sinais:
        finished_ok(int): Total de substituicoes realizadas.
        failed(str): Mensagem de erro.
        progress_updated(float): Progresso 0.0-100.0.
        console_msg(str): Mensagem para o console.
    """

    finished_ok = Signal(int)      # total de substituicoes
    failed = Signal(str)
    progress_updated = Signal(float)
    console_msg = Signal(str)

    def __init__(
        self,
        mrk_path: str,
        data_path: str,
        mapping: Dict[str, str],
        output_dir: str,
        *,
        tool_key: str = ToolKey.UNTRACEABLE.value,
        parent=None,
    ):
        super().__init__(parent)
        self._mrk_path = mrk_path
        self._data_path = data_path
        self._mapping = mapping
        self._output_dir = output_dir
        self._tool_key = tool_key
        self._logger = LogUtils(tool=tool_key, class_name="MrkSingleTask")

    def run(self):
        try:
            from utils.vector.VectorLayerSource import VectorLayerSource

            self.console_msg.emit(f"Carregando dados: {Path(self._data_path).name}")
            data = VectorLayerSource.read(self._data_path, tool_key=self._tool_key)
            self.console_msg.emit(f"Dados carregados: {len(data)} registros")

            total = self._process_mrk(Path(self._mrk_path), data)
            self.finished_ok.emit(total)
        except Exception as e:
            self._logger.error("Falha no single task", code="MRK_SINGLE_ERR", error=str(e))
            self.failed.emit(str(e))

    def _process_mrk(
        self, mrk_path: Path, data: List[dict], emit_console: bool = True
    ) -> int:
        """
        Processa UM arquivo MRK contra os dados fornecidos.
        Delega ao método estático e emite progresso.
        """
        with open(mrk_path, "r", encoding="utf-8") as f:
            mrk_lines = f.readlines()

        result = self._process_mrk_static(
            mrk_path, data, self._mapping, self._output_dir,
            emit_console=emit_console,
            console_emitter=self.console_msg.emit,
            progress_emitter=lambda idx, t: self.progress_updated.emit(
                ((idx + 1) / t) * 100.0 if t > 0 else 100.0
            ),
        )
        self._logger.info(
            "MRK processado",
            code="MRK_PROCESS_DONE",
            path=mrk_path.name,
            replacements=result,
        )
        return result

    # ── Método estático de processamento (compartilhado) ────────────

    @staticmethod
    def _process_mrk_static(
        mrk_path: Path, data: List[dict], mapping: Dict[str, str],
        output_dir: str, *,
        emit_console: bool = True,
        console_emitter=None,
        progress_emitter=None,
    ) -> int:
        """
        Processa UM arquivo MRK contra os dados fornecidos.
        Método estático compartilhado entre MrkSinglePipelineTask,
        MrkSingleTask e MrkBatchWorker.

        Returns:
            Total de substituicoes realizadas.
        """
        with open(mrk_path, "r", encoding="utf-8") as f:
            mrk_lines = f.readlines()

        output_lines: List[str] = []
        total_replacements = 0
        total_lines = len(mrk_lines)
        process_count = min(total_lines, len(data))

        for idx in range(process_count):
            if progress_emitter:
                progress_emitter(idx, total_lines)

            raw_line = mrk_lines[idx]
            line_no_nl = raw_line.rstrip("\n").rstrip("\r")
            row_data = data[idx]

            parsed = MrkSingleTask._parse_line(line_no_nl)
            new_values: Dict[str, str] = {}
            for mrk_field, data_col in mapping.items():
                if mrk_field in parsed["indices"] and data_col in row_data:
                    new_val = row_data[data_col].strip()
                    old_val = parsed["replacements"][mrk_field]["value_str"]
                    if new_val and new_val != old_val:
                        new_values[mrk_field] = new_val
                        total_replacements += 1
                        if emit_console and console_emitter:
                            console_emitter(
                                f"[{mrk_path.name}] L{idx+1}: {mrk_field} {old_val} -> {new_val}"
                            )

            if new_values:
                modified = MrkSingleTask._build_line(
                    parsed["parts"], parsed["indices"], new_values, parsed["replacements"]
                )
                output_lines.append(modified + ("\r\n" if raw_line.endswith("\r\n") else "\n"))
            else:
                output_lines.append(raw_line)

        if total_lines > process_count:
            for idx in range(process_count, total_lines):
                output_lines.append(mrk_lines[idx])

        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        output_file = output_path / mrk_path.name
        with open(output_file, "w", encoding="utf-8") as f:
            f.writelines(output_lines)

        return total_replacements

    # ── Métodos estáticos de parsing ─────────────────────────────────

    @staticmethod
    def _parse_line(line: str) -> Dict:
        """Analisa uma linha do MRK (TSV) e retorna partes, replacements, indices."""
        parts = line.split("\t")
        replacements: Dict[str, Dict] = {}
        indices: Dict[str, int] = {}
        for i, col in enumerate(parts):
            col_stripped = col.strip()
            for field in ["Lat", "Lon", "Ellh"]:
                match = re.match(rf"^(.+),{re.escape(field)}$", col_stripped)
                if match:
                    vs = match.group(1).strip()
                    replacements[field] = {"value_str": vs, "length": len(vs), "idx": i}
                    indices[field] = i
                    break
        return {"parts": parts, "replacements": replacements, "indices": indices}

    @staticmethod
    def _pad_value(original: str, new_val: str) -> str:
        """Ajusta o novo valor para ter o MESMO comprimento do original."""
        ol = len(original)
        r = new_val
        if len(r) == ol:
            return r
        if "." in original:
            if "." in r:
                op, np_ = original.split("."), r.split(".")
                od = len(op[1]) if len(op) > 1 else 0
                nd = len(np_[1]) if len(np_) > 1 else 0
                if nd < od:
                    r += "0" * (od - nd)
                elif nd > od:
                    r = np_[0] + "." + np_[1][:od]
                if len(r) < ol:
                    r += "0" * (ol - len(r))
            else:
                od = len(original.split(".")[1]) if "." in original else 0
                r += "." + "0" * od
                if len(r) < ol:
                    r += "0" * (ol - len(r))
            return r[:ol]
        if len(r) < ol:
            r += "0" * (ol - len(r))
        return r[:ol]

    @staticmethod
    def _build_line(
        parts: List[str],
        indices: Dict,
        new_values: Dict,
        original_replacements: Dict,
    ) -> str:
        """Reconstroi a linha do MRK preservando tabulacao."""
        for field, nv in new_values.items():
            if field in indices:
                idx = indices[field]
                col = parts[idx].strip()
                padded = MrkSingleTask._pad_value(
                    original_replacements[field]["value_str"], nv
                )
                match = re.match(r"^.*(," + re.escape(field) + r")$", col)
                if match:
                    parts[idx] = f"{padded}{match.group(1)}"
        return "\t".join(parts)


# ═══════════════════════════════════════════════════════════════════
# MrkBatchWorker  (QThread — processa N MRKs em lote)
# ═══════════════════════════════════════════════════════════════════

class MrkBatchWorker(QThread):
    """
    Processa N arquivos MRK em lote (sequencial, loop).
    Apenas orquestracao — delega processamento individual ao MrkSingleTask.

    Sinais:
        finished_ok(int, int, int): total_subst, processed, failed.
        failed(str): Mensagem de erro.
        progress_updated(float): Progresso 0.0-100.0.
        console_msg(str): Mensagem para o console.
        hud_update_msg(str, float): message, progress.
    """

    finished_ok = Signal(int, int, int)  # total_subst, processed, failed
    failed = Signal(str)
    progress_updated = Signal(float)
    console_msg = Signal(str)
    hud_update_msg = Signal(str, float)  # message, progress

    def __init__(
        self,
        mrk_paths: List[str],
        mapping: Dict[str, str],
        output_dir: str,
        *,
        tool_key: str = ToolKey.UNTRACEABLE.value,
        parent=None,
    ):
        super().__init__(parent)
        self._mrk_paths = mrk_paths
        self._mapping = mapping
        self._output_dir = output_dir
        self._tool_key = tool_key
        self._logger = LogUtils(tool=tool_key, class_name="MrkBatchWorker")

    def run(self):
        try:
            total_subst = 0
            processed = 0
            failed_count = 0
            total = len(self._mrk_paths)

            self._logger.info(
                "Iniciando lote",
                code="BATCH_START",
                total=total,
            )

            for idx, mrk_path_str in enumerate(self._mrk_paths):
                pct = (idx / total) * 100.0 if total > 0 else 0.0
                self.progress_updated.emit(pct)

                mrk_path = Path(mrk_path_str)
                self.hud_update_msg.emit(
                    f"Processando {idx+1}/{total}: {mrk_path.name}", pct
                )

                # Busca dados correspondentes
                data_path = self._find_data_file(mrk_path)
                if data_path is None:
                    self.console_msg.emit(
                        f"[LOTE] Sem dados para {mrk_path.name}, pulando."
                    )
                    self._logger.warning(
                        "Dados nao encontrados para MRK",
                        code="BATCH_NO_DATA",
                        mrk=mrk_path.name,
                    )
                    processed += 1
                    continue

                self.console_msg.emit(f"[LOTE] Dados: {Path(data_path).name}")

                # Le dados (na thread)
                from utils.vector.VectorLayerSource import VectorLayerSource

                data = VectorLayerSource.read(data_path, tool_key=self._tool_key)

                # Processa via método estático compartilhado
                subst = MrkSingleTask._process_mrk_static(
                    mrk_path, data, self._mapping, self._output_dir,
                    emit_console=False,
                )
                total_subst += subst
                processed += 1

            self.progress_updated.emit(100.0)
            self._logger.info(
                "Lote concluido",
                code="BATCH_DONE",
                total_subst=total_subst,
                processed=processed,
                failed=failed_count,
            )
            self.finished_ok.emit(total_subst, processed, failed_count)

        except Exception as e:
            self._logger.error("Falha no lote", code="BATCH_ERR", error=str(e))
            self.failed.emit(str(e))

    # ── Busca de dados ───────────────────────────────────────────────

    @staticmethod
    def _find_data_file(mrk_path: Path) -> str | None:
        """
        Busca arquivo de dados correspondente ao MRK (mesmo diretorio).
        Prioridade: .gpkg > .shp > .csv.
        """
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
            best = min(
                candidates,
                key=lambda p: (
                    0 if p.suffix.lower() == ".gpkg"
                    else 1 if p.suffix.lower() == ".shp"
                    else 2
                ),
            )
            return str(best)
        return None