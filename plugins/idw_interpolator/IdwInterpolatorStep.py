# -*- coding: utf-8 -*-
"""
IdwInterpolatorStep — Step que orquestra a interpolacao IDW
=============================================================
Valida parametros, cria a IdwInterpolatorTask com governor
extraido do contexto (injetado pelo PipelineRunner).

Melhorias:
- Extrai ResourceGovernor do contexto e passa para a task
- Task recebe governor para can_execute(), recommended_tile_size(), etc.
"""

from __future__ import annotations

import os as _os
from typing import Any, Optional

from core.enum.ToolKey import ToolKey
from core.governor.ResourceGovernor import ResourceGovernor
from core.papeline.BaseStep import BaseStep
from core.papeline.BaseTask import BaseTask
from core.papeline.ExecutionContext import ExecutionContext
from plugins.idw_interpolator.IdwInterpolatorTask import IdwInterpolatorTask
from utils.BaseUtil import BaseUtil


class IdwInterpolatorStep(BaseStep):
    """Step que orquestra a IdwInterpolatorTask com governor."""

    def __init__(self):
        self._logger = BaseUtil._get_logger(ToolKey.UNTRACEABLE.value, "IdwInterpolatorStep")

    def name(self) -> str:
        return "IdwInterpolatorStep"

    def should_run(self, context: ExecutionContext) -> bool:
        file_path = context.get("file_path", "")
        if not file_path or not _os.path.isfile(file_path):
            self._logger.warning("Arquivo LAS nao encontrado", code="IDW_STEP_NO_FILE")
            return False

        target = context.get("target_bands", {})
        if not any(target.values()):
            self._logger.warning("Nenhuma banda selecionada", code="IDW_STEP_NO_BANDS")
            return False

        separate = context.get("separate_bands", False)
        if not separate:
            has_rgb = target.get("r", False) and target.get("g", False) and target.get("b", False)
            has_any_rgb = target.get("r", False) or target.get("g", False) or target.get("b", False)
            if not has_rgb and has_any_rgb:
                self._logger.warning("Mosaico requer R, G e B", code="IDW_STEP_MOSAIC_INCOMPLETE")
                return False

        return True

    def create_task(self, context: ExecutionContext) -> Optional[BaseTask]:
        """Cria IdwInterpolatorTask com governor extraido do contexto."""
        governor: Optional[ResourceGovernor] = context.get("_governor", None)
        task = IdwInterpolatorTask(context.data, governor=governor)

        if governor is not None:
            self._logger.debug("Governor injetado na task", code="IDW_STEP_GOV_ATTACHED")

        return task

    def on_success(self, context: ExecutionContext, result: Any) -> None:
        self._logger.info("IDW concluido com sucesso", code="IDW_STEP_DONE")
        context.set("idw_result", result)

    def on_error(self, context: ExecutionContext, exception: Exception) -> None:
        self._logger.error("Erro na interpolacao IDW", code="IDW_STEP_ERR", error=str(exception))
