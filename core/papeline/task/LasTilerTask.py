# -*- coding: utf-8 -*-
"""
LasTilerTask — Task para divisão de nuvens LAS/LAZ em partes
==============================================================
Task que divide um arquivo LAS/LAZ em varios arquivos menores
com base no numero de pontos por parte.

Utiliza LasUtil.split_las() internamente.
"""

from __future__ import annotations

import os as _os
from typing import Optional

from core.enum.ToolKey import ToolKey
from core.papeline.BaseTask import BaseTask
from utils.LasUtil import LasUtil


class LasTilerTask(BaseTask):
    """
    Task que divide um arquivo LAS/LAZ em partes.

    Args:
        file_path: Caminho do arquivo LAS/LAZ de entrada.
        output_dir: Pasta onde salvar as partes.
        pontos_por_parte: Número máximo de pontos por arquivo.
        tool_key: ToolKey para logging (opcional).
    """

    def __init__(
        self,
        file_path: str,
        output_dir: str,
        pontos_por_parte: int = 5_000_000,
        tool_key: Optional[str] = None,
    ):
        super().__init__(
            description=f"Split: {_os.path.basename(file_path)}",
            tool_key=tool_key or ToolKey.UNTRACEABLE.value,
        )
        self._file_path = file_path
        self._output_dir = output_dir
        self._pontos_por_parte = pontos_por_parte

    def _run(self) -> bool:
        """Executa o split do LAS."""
        logger = self.get_logger()

        logger.info(
            "Iniciando split",
            code="TILER_TASK_START",
            path=self._file_path,
            output=self._output_dir,
            pontos_por_parte=self._pontos_por_parte,
        )

        result = LasUtil.split_las(
            path=self._file_path,
            output_dir=self._output_dir,
            pontos_por_parte=self._pontos_por_parte,
            tool_key=self._tool_key,
        )

        if result.get("error"):
            logger.error(
                "Split falhou",
                code="TILER_TASK_ERR",
                error=result["error"],
            )
            return False

        self.result = result
        logger.info(
            "Split concluido",
            code="TILER_TASK_DONE",
            n_partes=result.get("n_partes", 0),
            n_total=result.get("n_total", 0),
        )
        return True