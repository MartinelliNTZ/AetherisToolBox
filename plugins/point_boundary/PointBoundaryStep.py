# -*- coding: utf-8 -*-
"""
PointBoundaryStep — Step que cria a PointBoundaryTask para execução em QThread
================================================================================
Step do pipeline que orquestra a extração de pontos e geração do limite
via PointBoundaryTask em background thread.
"""

from __future__ import annotations

from typing import Any, Optional

from core.papeline.BaseStep import BaseStep
from core.papeline.BaseTask import BaseTask
from core.papeline.ExecutionContext import ExecutionContext
from .PointBoundaryTask import PointBoundaryTask


class PointBoundaryStep(BaseStep):
    """Step que cria a Task de geração de limite de pontos."""

    def name(self) -> str:
        return "PointBoundaryStep"

    def should_run(self, context: ExecutionContext) -> bool:
        """Só executa se houver file_path definido."""
        return bool(context.get("file_path"))

    def create_task(self, context: ExecutionContext) -> Optional[BaseTask]:
        """
        Cria a PointBoundaryTask com os parâmetros do context.
        """
        return PointBoundaryTask(
            file_path=context.get("file_path", ""),
            ratio_inicial=context.get("ratio_inicial", 0.10),
            ratio_step=context.get("ratio_step", 0.01),
            limiar_escada=context.get("limiar_escada", 12.0),
            suavisacao=context.get("suavisacao", 20.0),
            n_amostras=context.get("n_amostras", 100_000),
            crs=context.get("crs", "EPSG:31982"),
            output_dir=context.get("output_dir", ""),
            output_path=context.get("output_path", ""),
            salvar_intermediarios=context.get("salvar_intermediarios", False),
            tool_key=context.get("tool_key", "Untraceable"),
            csv_x_field=context.get("csv_x_field", "x"),
            csv_y_field=context.get("csv_y_field", "y"),
        )

    def on_success(self, context: ExecutionContext, result: Any) -> None:
        """Mescla os resultados da Task no context."""
        if isinstance(result, dict):
            for key, value in result.items():
                context.set(key, value)