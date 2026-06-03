# -*- coding: utf-8 -*-
"""
MrkBatchWorker — Workers em QThread para processamento MRK em background
=========================================================================
- MrkSingleTask: processa 1 MRK com dados ja fornecidos (leitura na thread)
- MrkBatchWorker: processa N MRKs em lote sequencial (loop, sem recursao)

Ambos executam leitura de dados + substituicao em thread separada.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Dict, List

from PySide6.QtCore import QThread, Signal

from core.enum.ToolKey import ToolKey


class MrkSingleTask(QThread):
    """
    Processa UM arquivo MRK.
    Le os dados do arquivo + processa em background.
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

    def run(self):
        try:
            from utils.vector.VectorLayerSource import VectorLayerSource

            self.console_msg.emit(f"Carregando dados: {Path(self._data_path).name}")
            data = VectorLayerSource.read(self._data_path, tool_key=self._tool_key)
            self.console_msg.emit(f"Dados carregados: {len(data)} registros")

            total = self._process_mrk(Path(self._mrk_path), data)
            self.finished_ok.emit(total)
        except Exception as e:
            self.failed.emit(str(e))

    def _process_mrk(self, mrk_path: Path, data: List[dict]) -> int:
        with open(mrk_path, "r", encoding="utf-8") as f:
            mrk_lines = f.readlines()

        output_lines: List[str] = []
        total_replacements = 0
        total_lines = len(mrk_lines)
        process_count = min(total_lines, len(data))

        for idx in range(process_count):
            pct = ((idx + 1) / total_lines) * 100.0 if total_lines > 0 else 100.0
            self.progress_updated.emit(pct)

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
                        self.console_msg.emit(
                            f"[{mrk_path.name}] L{idx+1}: {mrk_field} {old_val} -> {new_val}"
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

        self.console_msg.emit(f"{output_path.name} -> {total_replacements} substituicoes")
        return total_replacements

    @staticmethod
    def _parse_line(line: str) -> Dict:
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
    def _build_line(parts: List[str], indices: Dict, new_values: Dict,
                    original_replacements: Dict) -> str:
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


class MrkBatchWorker(QThread):
    """
    Processa N arquivos MRK em lote (sequencial, loop).
    Tudo em background: leitura de dados + substituicao.
    """

    finished_ok = Signal(int, int, int)  # total_subst, processed, failed
    failed = Signal(str)
    progress_updated = Signal(float)
    console_msg = Signal(str)
    hud_update_msg = Signal(str)

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

    def run(self):
        try:
            total_subst = 0
            processed = 0
            failed = 0
            total = len(self._mrk_paths)

            for idx, mrk_path_str in enumerate(self._mrk_paths):
                if total > 0:
                    self.progress_updated.emit((idx / total) * 100.0)

                mrk_path = Path(mrk_path_str)
                self.hud_update_msg.emit(
                    f"Processando {idx+1}/{total}: {mrk_path.name}"
                )

                # Busca dados correspondentes
                data_path = self._find_data_file(mrk_path)
                if data_path is None:
                    self.console_msg.emit(f"[LOTE] Sem dados para {mrk_path.name}, pulando.")
                    processed += 1
                    continue

                self.console_msg.emit(f"[LOTE] Dados: {Path(data_path).name}")

                # Le dados (na thread)
                from utils.vector.VectorLayerSource import VectorLayerSource
                data = VectorLayerSource.read(data_path, tool_key=self._tool_key)

                # Processa este MRK
                st = MrkSingleTask(
                    mrk_path=str(mrk_path),
                    data_path=data_path,
                    mapping=self._mapping,
                    output_dir=self._output_dir,
                    tool_key=self._tool_key,
                )

                # Para reutilizar a logica de processamento, fazemos inline
                subst = self._process_single(mrk_path, data)
                total_subst += subst
                processed += 1

            self.progress_updated.emit(100.0)
            self.finished_ok.emit(total_subst, processed, failed)

        except Exception as e:
            self.failed.emit(str(e))

    def _find_data_file(self, mrk_path: Path) -> str | None:
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

    def _process_single(self, mrk_path: Path, data: List[dict]) -> int:
        """Processa UM MRK com dados ja carregados. Retorna total de substituicoes."""
        from core.task.MrkWorkerTask import MrkWorkerTask

        # Reusa a logica do MrkSingleTask internamente
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

            parsed = MrkSingleTask._parse_line(line_no_nl)
            new_values: Dict[str, str] = {}
            for mrk_field, data_col in self._mapping.items():
                if mrk_field in parsed["indices"] and data_col in row_data:
                    new_val = row_data[data_col].strip()
                    old_val = parsed["replacements"][mrk_field]["value_str"]
                    if new_val and new_val != old_val:
                        new_values[mrk_field] = new_val
                        total_replacements += 1

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

        output_dir = Path(self._output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = output_dir / mrk_path.name
        with open(output_path, "w", encoding="utf-8") as f:
            f.writelines(output_lines)

        return total_replacements