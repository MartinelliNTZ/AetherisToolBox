# -*- coding: utf-8 -*-
"""
IdwInterpolatorStep — Step que orquestra a interpolação IDW
=============================================================
Valida parâmetros, cria a IdwInterpolatorTask e coleta resultados.
"""

from __future__ import annotations

import os
from typing import Any, Optional

from core.enum.ToolKey import ToolKey
from core.papeline.BaseStep import BaseStep
from core.papeline.BaseTask import BaseTask
from core.papeline.ExecutionContext import ExecutionContext
from plugins.idw_interpolator.IdwInterpolatorTask import IdwInterpolatorTask
from utils.BaseUtil import BaseUtil


class IdwInterpolatorStep(BaseStep):
    """
    Step que orquestra a IdwInterpolatorTask.

    Valida parâmetros de entrada, instancia a task e coleta resultados.
    """

    def __init__(self):
        self._logger = BaseUtil._get_logger(ToolKey.UNTRACEABLE.value, "IdwInterpolatorStep")

    def name(self) -> str:
        return "IdwInterpolatorStep"

    def should_run(self, context: ExecutionContext) -> bool:
        """Só executa se houver arquivo LAS e bandas selecionadas."""
        file_path = context.get("file_path", "")
        if not file_path or not os.path.isfile(file_path):
            self._logger.warning("Arquivo LAS nao encontrado", code="IDW_STEP_NO_FILE")
            return False

        target = context.get("target_bands", {})
        if not any(target.values()):
            self._logger.warning("Nenhuma banda selecionada", code="IDW_STEP_NO_BANDS")
            return False

        # Valida mosaico: se não separar bandas, precisa de RGB completo
        separate = context.get("separate_bands", False)
        if not separate:
            has_rgb = target.get("r", False) and target.get("g", False) and target.get("b", False)
            has_any_rgb = target.get("r", False) or target.get("g", False) or target.get("b", False)
            if not has_rgb and has_any_rgb:
                self._logger.warning(
                    "Mosaico requer R, G e B simultaneamente",
                    code="IDW_STEP_MOSAIC_INCOMPLETE",
                )
                return False

        return True

    def create_task(self, context: ExecutionContext) -> Optional[BaseTask]:
        """Cria a IdwInterpolatorTask com os parâmetros do contexto."""
        return IdwInterpolatorTask(context.data)

    def on_success(self, context: ExecutionContext, result: Any) -> None:
        """Callback após task bem-sucedida — armazena resultado no contexto."""
        self._logger.info("IDW concluido com sucesso", code="IDW_STEP_DONE")
        context["idw_result"] = result

    def on_error(self, context: ExecutionContext, exception: Exception) -> None:
        """Tratamento de erro do step."""
        self._logger.error(
            "Erro na interpolacao IDW",
            code="IDW_STEP_ERR",
            error=str(exception),
        )