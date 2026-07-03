# -*- coding: utf-8 -*-
"""
IdwInterpolatorStep — Step que interpola arquivos LAS via IDW
================================================================
Step que recebe um diretorio com arquivos LAS (de quem quer que os
tenha produzido) e executa interpolacao IDW, gerando rasters.

NAO sabe o que sao tiles. So le do contexto:
    - "input_dir": Diretorio com arquivos .las/.laz a interpolar

Context requer:
    - "input_dir": Diretorio com arquivos LAS
    - "output_path": Caminho do GeoTIFF de saida
    - "target_bands": Dict com bandas alvo (r, g, b, z)
    - "resol_m": Resolucao em metros

Context produz:
    - "idw_result": Dict com resultado completo da interpolacao
"""

from __future__ import annotations

import glob
import os as _os
from typing import Any, Optional

from core.governor.ResourceGovernor import ResourceGovernor
from core.papeline.BaseStep import BaseStep
from core.papeline.BaseTask import BaseTask
from core.papeline.ExecutionContext import ExecutionContext
from plugins.idw_interpolator.IdwInterpolatorTask import IdwInterpolatorTask


class IdwInterpolatorStep(BaseStep):
    """Step que interpola arquivos LAS via IDW."""

    def name(self) -> str:
        return "idw_interpolator"

    def should_run(self, context: ExecutionContext) -> bool:
        logger = self.get_logger(context)

        input_dir = context.get("input_dir", "")
        if not input_dir or not _os.path.isdir(input_dir):
            logger.warning("Diretorio de entrada nao encontrado", code="IDW_STEP_NO_DIR")
            return False

        las_files = sorted(
            glob.glob(_os.path.join(input_dir, "*.las"))
            + glob.glob(_os.path.join(input_dir, "*.laz"))
        )
        if not las_files:
            logger.warning("Nenhum arquivo LAS encontrado no diretorio", code="IDW_STEP_NO_FILES")
            return False

        target = context.get("target_bands", {})
        if not any(target.values()):
            logger.warning("Nenhuma banda selecionada", code="IDW_STEP_NO_BANDS")
            return False

        merge = context.get("merge_bands", True)
        if merge:
            has_rgb = target.get("r", False) and target.get("g", False) and target.get("b", False)
            has_any_rgb = target.get("r", False) or target.get("g", False) or target.get("b", False)
            if not has_rgb and has_any_rgb:
                logger.warning("Mosaico requer R, G e B", code="IDW_STEP_MOSAIC_INCOMPLETE")
                return False

        return True

    def create_task(self, context: ExecutionContext) -> Optional[BaseTask]:
        """Cria IdwInterpolatorTask a partir do diretorio de entrada."""
        governor: Optional[ResourceGovernor] = context.get("_governor", None)

        return IdwInterpolatorTask(
            input_dir=str(context.get("input_dir")),
            output_path=str(context.get("output_path")),
            target_bands=context.get("target_bands", {}),
            merge_bands=context.get("merge_bands", True),
            resol_m=context.get("resol_m", 0.01),
            idw_k=int(context.get("idw_k", 5)),
            idw_power=float(context.get("idw_power", 2.0)),
            idw_raio_max=float(context.get("idw_raio_max", 0.5)),
            idw_overlap=float(context.get("idw_overlap", 3.0)),
            crs_str=str(context.get("crs_str", "EPSG:31982")),
            eliminar_tiles=bool(context.get("eliminar_tiles", True)),
            salvar_las=bool(context.get("salvar_las", False)),
            governor=governor,
        )

    def on_success(self, context: ExecutionContext, result: Any) -> None:
        """Mapeia o resultado da task para o ExecutionContext."""
        logger = self.get_logger(context)

        if isinstance(result, dict):
            context.set("idw_result", result)
            for key in ("grid", "parametros", "tiles", "arquivos_gerados"):
                if key in result:
                    context.set(key, result[key])

        logger.info("IDW concluido com sucesso", code="IDW_STEP_DONE")

    def on_error(self, context: ExecutionContext, exception: Exception) -> None:
        """Adiciona erro ao contexto."""
        logger = self.get_logger(context)
        logger.error("Erro na interpolacao IDW", code="IDW_STEP_ERR", error=str(exception))
        context.add_error(exception)