# -*- coding: utf-8 -*-
"""
LasTilerStep — Step para divisão de nuvens LAS/LAZ em partes
==============================================================
Step que divide um arquivo LAS/LAZ em varios arquivos menores
com base no numero de pontos por parte.

Context requer:
    - "file_path": Caminho do arquivo LAS/LAZ de entrada
    - "output_dir": Pasta onde salvar as partes
    - "pontos_por_parte": Número máximo de pontos por arquivo

Context produz:
    - "split_result": Dict com resultado do split
"""

from __future__ import annotations

import os as _os
from typing import Any, Optional

from ..ExecutionContext import ExecutionContext
from ..BaseStep import BaseStep
from ..BaseTask import BaseTask
from ..task.LasTilerTask import LasTilerTask


class LasTilerStep(BaseStep):
    """Step que divide um arquivo LAS/LAZ em partes."""

    def name(self) -> str:
        return "las_tiler"

    def should_run(self, context: ExecutionContext) -> bool:
        logger = self.get_logger(context)

        file_path = context.get("file_path", "")
        if not file_path or not _os.path.isfile(file_path):
            logger.warning("Arquivo LAS nao encontrado", code="TILER_STEP_NO_FILE", path=file_path)
            return False

        output_dir = context.get("output_dir", "")
        if not output_dir:
            logger.warning("Pasta de saida nao definida no contexto", code="TILER_STEP_NO_OUTPUT")
            return False

        return True

    def create_task(self, context: ExecutionContext) -> Optional[BaseTask]:
        """Cria LasTilerTask com parametros do contexto."""
        tool_key = context.get("tool_key", None)
        return LasTilerTask(
            file_path=str(context.get("file_path")),
            output_dir=str(context.get("output_dir")),
            pontos_por_parte=int(context.get("pontos_por_parte", 5_000_000)),
            tool_key=tool_key,
        )

    def on_success(self, context: ExecutionContext, result: Any) -> None:
        """Mapeia o resultado da task para o ExecutionContext."""
        logger = self.get_logger(context)

        if isinstance(result, dict):
            context.set("split_result", result)
            for key in ("n_total", "n_partes", "pontos_por_parte", "arquivos"):
                if key in result:
                    context.set(key, result[key])

        logger.info("Split concluido com sucesso", code="TILER_STEP_DONE")

    def on_error(self, context: ExecutionContext, exception: Exception) -> None:
        """Adiciona erro ao contexto."""
        logger = self.get_logger(context)
        logger.error("Erro no split", code="TILER_STEP_ERR", error=str(exception))
        context.add_error(exception)