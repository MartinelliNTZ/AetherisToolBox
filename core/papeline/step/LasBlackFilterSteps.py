# -*- coding: utf-8 -*-
"""
LasBlackFilterSteps — Steps concretos para pipeline de filtro LAS
====================================================================
Steps que compõem uma pipeline completa de filtragem de pontos pretos
em arquivos LAS/LAZ.

Pipeline completa:
    1. LasBlackFilterStep → Filtra pontos pretos e gera arquivos LAS
"""

from __future__ import annotations

from typing import Any

from ..ExecutionContext import ExecutionContext
from ..BaseStep import BaseStep
from ..task.LasBlackFilterTask import LasBlackFilterTask


class LasBlackFilterStep(BaseStep):
    """
    Step que filtra pontos pretos de um arquivo LAS/LAZ.

    Context requer:
        - "file_path": Caminho do arquivo LAS/LAZ de entrada
        - "limiar": Valor máximo de R/G/B para considerar preto (0–255)
        - "output_limpo": Caminho para salvar o LAS filtrado
        - "output_pretos": Caminho para salvar pontos pretos ("" se não salvar)

    Context produz:
        - "n_removidos": Quantidade de pontos removidos
        - "n_mantidos": Quantidade de pontos mantidos
        - "n_pretos": Quantidade de pontos pretos salvos
        - "n_total": Total de pontos no original
        - "output_limpo": Caminho do LAS filtrado gerado
        - "output_pretos": Caminho do LAS de pretos ("" se não salvou)
    """

    def name(self) -> str:
        return "las_black_filter"

    def create_task(self, context: ExecutionContext) -> LasBlackFilterTask:
        """Cria a task de filtragem com parâmetros do contexto."""
        return LasBlackFilterTask(
            file_path=str(context.get("file_path")),
            limiar=int(context.get("limiar", 0)),
            salvar_pretos=bool(context.get("salvar_pretos", False)),
            output_limpo=str(context.get("output_limpo", "")),
            output_pretos=str(context.get("output_pretos", "")),
        )

    def on_success(self, context: ExecutionContext, result: Any) -> None:
        """Mapeia o resultado da task para o ExecutionContext."""
        if isinstance(result, dict):
            for key in ("n_total", "n_removidos", "n_mantidos", "n_pretos",
                        "output_limpo", "output_pretos"):
                context.set(key, result.get(key))

    def on_error(self, context: ExecutionContext, exception: Exception) -> None:
        """Adiciona erro ao contexto."""
        context.add_error(exception)