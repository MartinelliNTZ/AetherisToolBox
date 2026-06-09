# -*- coding: utf-8 -*-
"""
MrkWorkerTask — QThread para processamento MRK em background
=============================================================
Executa a substituicao em thread separada para nao travar a UI.
Emite sinais de progresso, console e resultado.

Uso:
    worker = MrkWorkerTask(mrk_path, data, mapping, output_dir, tool_key)
    worker.finished_ok.connect(self._on_done)
    worker.failed.connect(self._on_error)
    worker.progress_updated.connect(self._on_progress)
    worker.console_msg.connect(self._on_console)
    worker.start()
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Dict, List

from PySide6.QtCore import QThread, Signal

from core.config.LogUtils import LogUtils
from core.enum.ToolKey import ToolKey


class MrkWorkerTask(QThread):
    """
    Worker thread para processar substituicao em arquivos MRK.

    Sinais:
        finished_ok(int): Total de substituicoes realizadas.
        failed(str): Mensagem de erro.
        progress_updated(float): Progresso 0.0-100.0.
        console_msg(str): Mensagem para o console.
    """

    finished_ok = Signal(int)
    failed = Signal(str)
    progress_updated = Signal(float)
    console_msg = Signal(str)

    def __init__(
        self,
        mrk_path: str,
        data: List[dict],
        mapping: Dict[str, str],
        output_dir: str,
        *,
        tool_key: str = ToolKey.UNTRACEABLE.value,
        parent=None,
    ) -> None:
        super().__init__(parent)
        self._mrk_path = mrk_path
        self._data = data
        self._mapping = mapping
        self._output_dir = output_dir
        self._tool_key = tool_key
        self._logger = LogUtils(tool=tool_key, class_name="MrkWorkerTask")

    def run(self) -> None:
        """Executa o processamento em background."""
        try:
            total = self._process()
            self.finished_ok.emit(total)
        except Exception as e:
            self._logger.error("Falha no worker", code="MRK_WORKER_ERR", error=str(e))
            self.failed.emit(str(e))

    # ── Logica Central ────────────────────────────────────────────

    @staticmethod
    def _parse_line(line: str) -> Dict:
        """Analisa uma linha do MRK (TSV) e retorna partes, replacements, indices."""
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

        return {"parts": parts, "replacements": replacements, "indices": indices}

    @staticmethod
    def _pad_value(original_value: str, new_value: str) -> str:
        """Ajusta o novo valor para ter o MESMO comprimento do original."""
        original_length = len(original_value)
        result = new_value

        if len(result) == original_length:
            return result

        if "." in original_value:
            if "." in result:
                orig_parts = original_value.split(".")
                new_parts = result.split(".")
                orig_dec = len(orig_parts[1]) if len(orig_parts) > 1 else 0
                new_dec = len(new_parts[1]) if len(new_parts) > 1 else 0

                if new_dec < orig_dec:
                    result = result + "0" * (orig_dec - new_dec)
                elif new_dec > orig_dec:
                    result = new_parts[0] + "." + new_parts[1][:orig_dec]

                if len(result) < original_length:
                    result = result + "0" * (original_length - len(result))
            else:
                orig_parts = original_value.split(".")
                orig_dec = len(orig_parts[1]) if len(orig_parts) > 1 else 0
                result = result + "." + "0" * orig_dec
                if len(result) < original_length:
                    result = result + "0" * (original_length - len(result))

            if len(result) > original_length:
                result = result[:original_length]
            return result

        if len(result) < original_length:
            result = result + "0" * (original_length - len(result))
        elif len(result) > original_length:
            result = result[:original_length]
        return result

    @staticmethod
    def _build_line(parts: List[str], indices: Dict, new_values: Dict,
                    original_replacements: Dict) -> str:
        """Reconstroi a linha do MRK preservando tabulacao."""
        for field, new_value in new_values.items():
            if field in indices:
                idx = indices[field]
                col_orig = parts[idx].strip()
                orig_val = original_replacements[field]["value_str"]
                padded = MrkWorkerTask._pad_value(orig_val, new_value)

                match = re.match(r"^.*(," + re.escape(field) + r")$", col_orig)
                if match:
                    suffix = match.group(1)
                    parts[idx] = f"{padded}{suffix}"

        return "\t".join(parts)

    def _process(self) -> int:
        """Processa o MRK e retorna total de substituicoes."""
        mrk_path = Path(self._mrk_path)
        output_dir = Path(self._output_dir)

        # Le MRK
        with open(mrk_path, "r", encoding="utf-8") as f:
            mrk_lines = f.readlines()

        output_lines: List[str] = []
        total_replacements = 0
        total_lines = len(mrk_lines)
        total_data = len(self._data)
        process_count = min(total_lines, total_data)

        for idx in range(process_count):
            # Progresso
            pct = ((idx + 1) / total_lines) * 100.0 if total_lines > 0 else 100.0
            self.progress_updated.emit(pct)

            raw_line = mrk_lines[idx]
            line_no_nl = raw_line.rstrip("\n").rstrip("\r")
            row_data = self._data[idx]

            parsed = self._parse_line(line_no_nl)
            parts = parsed["parts"]
            replacements = parsed["replacements"]
            indices = parsed["indices"]

            new_values: Dict[str, str] = {}
            for mrk_field, data_column in self._mapping.items():
                if mrk_field in indices and data_column in row_data:
                    new_val = row_data[data_column].strip()
                    old_val = replacements[mrk_field]["value_str"]
                    if new_val and new_val != old_val:
                        new_values[mrk_field] = new_val
                        total_replacements += 1
                        self.console_msg.emit(
                            f"[{mrk_path.name}] L{idx+1}: {mrk_field} {old_val} -> {new_val}"
                        )

            if new_values:
                modified = self._build_line(parts, indices, new_values, replacements)
                output_lines.append(modified + ("\r\n" if raw_line.endswith("\r\n") else "\n"))
            else:
                output_lines.append(raw_line)

        # Linhas restantes
        if total_lines > process_count:
            for idx in range(process_count, total_lines):
                output_lines.append(mrk_lines[idx])

        # Salva
        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = output_dir / mrk_path.name
        with open(output_path, "w", encoding="utf-8") as f:
            f.writelines(output_lines)

        self._logger.info(
            "MRK processado",
            code="MRK_PROCESS_DONE",
            path=mrk_path.name,
            replacements=total_replacements,
        )
        self.console_msg.emit(
            f"[MrkSubst] {output_path.name} -> {total_replacements} substituicoes"
        )
        return total_replacements
