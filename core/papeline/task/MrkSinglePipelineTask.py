# -*- coding: utf-8 -*-
"""
MrkSinglePipelineTask — Task para processamento MRK no padrão BaseTask
========================================================================
Adaptação do MrkSingleTask original para herdar de BaseTask em vez de QThread.
A lógica de processamento MRK é preservada, mas o mecanismo de execução
passa a usar o sistema de pipeline (BaseTask + AsyncPipelineEngine).

Uso na pipeline:
    class MrkProcessStep(BaseStep):
        def create_task(self, context):
            return MrkSinglePipelineTask(...)
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Dict, List, Optional

from ..BaseTask import BaseTask


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
            total = self._process_mrk(Path(self._mrk_path), self._data)
            self.result = {
                "path": self._mrk_path,
                "replacements": total,
                "output_path": str(Path(self._output_dir) / Path(self._mrk_path).name),
            }
            return True
        except Exception as e:
            self.exception = e
            return False

    # ── Processamento (mesma lógica do MrkSingleTask original) ────────

    def _process_mrk(
        self, mrk_path: Path, data: List[dict], emit_console: Optional[bool] = None
    ) -> int:
        """
        Processa UM arquivo MRK contra os dados fornecidos.
        Retorna total de substituicoes realizadas.
        """
        if emit_console is None:
            emit_console = self._emit_console

        with open(mrk_path, "r", encoding="utf-8") as f:
            mrk_lines = f.readlines()

        output_lines: List[str] = []
        total_replacements = 0
        total_lines = len(mrk_lines)
        process_count = min(total_lines, len(data))

        for idx in range(process_count):
            raw_line = mrk_lines[idx]
            line_no_nl = raw_line.rstrip("\n").rstrip("\r")
            row_data = data[idx]

            parsed = self._parse_line(line_no_nl)
            new_values: Dict[str, str] = {}
            for mrk_field, data_col in self._mapping.items():
                if mrk_field in parsed["indices"] and data_col in row_data:
                    new_val = row_data[data_col].strip()
                    old_val = parsed["replacements"][mrk_field]["value_str"]
                    if new_val and new_val != old_val:
                        new_values[mrk_field] = new_val
                        total_replacements += 1
                        if emit_console:
                            import logging
                            logging.info(
                                f"[{mrk_path.name}] L{idx+1}: "
                                f"{mrk_field} {old_val} -> {new_val}"
                            )

            if new_values:
                modified = self._build_line(
                    parsed["parts"], parsed["indices"], new_values, parsed["replacements"]
                )
                output_lines.append(modified + ("\r\n" if raw_line.endswith("\r\n") else "\n"))
            else:
                output_lines.append(raw_line)

        if total_lines > process_count:
            for idx in range(process_count, total_lines):
                output_lines.append(mrk_lines[idx])

        output_dir = Path(self._output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = output_dir / mrk_path.name
        with open(output_path, "w", encoding="utf-8") as f:
            f.writelines(output_lines)

        return total_replacements

    # ── Métodos estáticos de parsing (extraídos do MrkSingleTask) ────

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
                padded = MrkSinglePipelineTask._pad_value(
                    original_replacements[field]["value_str"], nv
                )
                match = re.match(r"^.*(," + re.escape(field) + r")$", col)
                if match:
                    parts[idx] = f"{padded}{match.group(1)}"
        return "\t".join(parts)