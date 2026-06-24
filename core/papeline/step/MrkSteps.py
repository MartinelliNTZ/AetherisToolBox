# -*- coding: utf-8 -*-
"""
MrkSteps — Steps concretos para pipeline de processamento MRK
===============================================================
Steps que compõem uma pipeline completa de substituição MRK.

Pipeline MRK completa:
    1. MrkLoadDataStep → Carrega dados do arquivo vetorial
    2. MrkProcessStep → Processa o MRK com os dados carregados
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional

from ..ExecutionContext import ExecutionContext
from ..BaseTask import BaseTask
from ..BaseStep import BaseStep
from ..task.MrkSinglePipelineTask import MrkSinglePipelineTask


class MrkLoadDataStep(BaseStep):
    """
    Step que carrega dados de um arquivo vetorial (CSV/SHP/GPKG)
    e armazena no ExecutionContext.

    Context requer:
        - "data_path": Caminho do arquivo de dados
        - "tool_key": ToolKey para logging

    Context produz:
        - "data": Lista de dicts com registros carregados
    """
    def name(self) -> str:
        return "mrk_load_data"

    def create_task(self, context: ExecutionContext) -> BaseTask:
        return MrkLoadDataTask(
            data_path=str(context.get("data_path")),
            tool_key=str(context.get("tool_key", "MrkPipeline")),
        )

    def on_success(self, context: ExecutionContext, result: Any) -> None:
        context.set("data", result)


class MrkLoadDataTask(BaseTask):
    """
    Task para carregar dados vetoriais em background.
    """
    def __init__(self, data_path: str, tool_key: str):
        super().__init__(description=f"Carregar dados: {Path(data_path).name}")
        self._data_path = data_path
        self._tool_key = tool_key

    def _run(self) -> bool:
        try:
            from utils.vector.VectorLayerSource import VectorLayerSource
            data = VectorLayerSource.read(self._data_path, tool_key=self._tool_key)
            self.result = data
            return True
        except Exception as e:
            self.exception = e
            return False


class MrkProcessStep(BaseStep):
    """
    Step que processa UM arquivo MRK contra dados carregados no contexto.

    Context requer:
        - "data": Lista de dicts (produzido por MrkLoadDataStep)
        - "mrk_path": Caminho do arquivo .MRK
        - "mapping": Dict mapeando campo_mrk -> coluna_dados
        - "output_dir": Diretório de saída

    Context produz:
        - "replacements": Total de substituições realizadas
        - "output_path": Caminho do MRK processado
    """
    def name(self) -> str:
        return "mrk_process"

    def should_run(self, context: ExecutionContext) -> bool:
        return context.has("data") and context.has("mrk_path")

    def create_task(self, context: ExecutionContext) -> MrkSinglePipelineTask:
        return MrkSinglePipelineTask(
            mrk_path=str(context.get("mrk_path")),
            data=context.get("data", []),
            mapping=context.get("mapping", {}),
            output_dir=str(context.get("output_dir")),
            emit_console=True,
        )

    def on_success(self, context: ExecutionContext, result: Any) -> None:
        if isinstance(result, dict):
            context.set("replacements", result.get("replacements", 0))
            context.set("output_path", result.get("output_path", ""))

    def on_error(self, context: ExecutionContext, exception: Exception) -> None:
        context.add_error(exception)


class MrkFindDataStep(BaseStep):
    """
    Step que busca automaticamente o arquivo de dados correspondente
    ao MRK (mesmo diretório, mesma base de nome).

    Context requer:
        - "mrk_path": Caminho do arquivo .MRK

    Context produz:
        - "data_path": Caminho do arquivo de dados encontrado
    """
    def name(self) -> str:
        return "mrk_find_data"

    def create_task(self, context: ExecutionContext) -> None:
        return None  # Síncrono

    def run_inline(self, context: ExecutionContext) -> Optional[str]:
        mrk_path = Path(str(context.get("mrk_path", "")))
        if not mrk_path.exists():
            return None

        base_name = mrk_path.stem
        directory = mrk_path.parent
        if not directory.is_dir():
            return None

        for ext in [".gpkg", ".shp", ".csv"]:
            candidate = directory / f"{base_name}{ext}"
            if candidate.is_file():
                return str(candidate)

        # Fallback: busca por nome similar
        candidates = []
        for ext in [".gpkg", ".shp", ".csv"]:
            for f in directory.glob(f"*{ext}"):
                if f.is_file() and base_name.lower() in f.stem.lower():
                    candidates.append(f)
        if candidates:
            best = min(candidates, key=lambda p: (
                0 if p.suffix.lower() == ".gpkg"
                else 1 if p.suffix.lower() == ".shp"
                else 2
            ))
            return str(best)
        return None

    def on_success(self, context: ExecutionContext, result: Any) -> None:
        if result:
            context.set("data_path", result)