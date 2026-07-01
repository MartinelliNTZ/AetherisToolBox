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
    Step que valida que o arquivo de dados existe.
    NAO carrega dados em memoria - a carga e feita pelo MrkProcessStep
    que le diretamente do arquivo.

    Context requer:
        - "data_path": Caminho do arquivo de dados

    Context produz:
        - (apenas valida, nao carrega nada em memoria)
    """
    def name(self) -> str:
        return "mrk_load_data"

    def create_task(self, context: ExecutionContext) -> None:
        return None  # Sincrono

    def run_inline(self, context: ExecutionContext) -> Optional[bool]:
        data_path = str(context.get("data_path", ""))
        if not data_path or not Path(data_path).is_file():
            return False
        return True

    def on_success(self, context: ExecutionContext, result: Any) -> None:
        pass  # Dados serao carregados pelo MrkProcessStep direto do disco


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
        return context.has("data_path") and context.has("mrk_path")

    def create_task(self, context: ExecutionContext) -> MrkSinglePipelineTask:
        return MrkSinglePipelineTask(
            mrk_path=str(context.get("mrk_path")),
            data_path=str(context.get("data_path", "")),
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