# -*- coding: utf-8 -*-
"""
IdwInterpolatorStep — Step que orquestra a interpolacao IDW
=============================================================
Step que executa a interpolacao IDW em background.

Context requer:
    - "file_path": Caminho do arquivo LAS/LAZ de entrada
    - "output_path": Caminho do GeoTIFF de saida
    - "target_bands": Dict com bandas alvo (r, g, b, z)
    - "merge_bands": Se True, gera mosaico RGB
    - "resol_m": Resolucao em metros
    - "idw_k": Numero de vizinhos
    - "idw_power": Potencia IDW
    - "idw_raio_max": Raio maximo de busca (m)
    - "idw_overlap": Sobreposicao entre tiles (m)
    - "pontos_por_tile": Pontos maximos por tile
    - "crs_str": CRS de saida
    - "eliminar_tiles": Se True, remove tiles apos processar

Context produz:
    - "idw_result": Dict com resultado completo da interpolacao
"""

from __future__ import annotations

import os as _os
from typing import Any, Optional

from core.governor.ResourceGovernor import ResourceGovernor
from core.papeline.BaseStep import BaseStep
from core.papeline.BaseTask import BaseTask
from core.papeline.ExecutionContext import ExecutionContext
from plugins.idw_interpolator.IdwInterpolatorTask import IdwInterpolatorTask


class IdwInterpolatorStep(BaseStep):
    """Step que orquestra a interpolacao IDW."""

    def name(self) -> str:
        return "idw_interpolator"

    def should_run(self, context: ExecutionContext) -> bool:
        logger = self.get_logger(context)

        file_path = context.get("file_path", "")
        if not file_path or not _os.path.isfile(file_path):
            logger.warning("Arquivo LAS nao encontrado", code="IDW_STEP_NO_FILE")
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
        """Cria IdwInterpolatorTask com parametros individuais do contexto."""
        governor: Optional[ResourceGovernor] = context.get("_governor", None)

        return IdwInterpolatorTask(
            file_path=str(context.get("file_path")),
            output_path=str(context.get("output_path")),
            target_bands=context.get("target_bands", {}),
            merge_bands=context.get("merge_bands", True),
            resol_m=context.get("resol_m", 0.01),
            idw_k=int(context.get("idw_k", 5)),
            idw_power=float(context.get("idw_power", 2.0)),
            idw_raio_max=float(context.get("idw_raio_max", 0.5)),
            idw_overlap=float(context.get("idw_overlap", 3.0)),
            pontos_por_tile=int(context.get("pontos_por_tile", 10_000_000)),
            crs_str=str(context.get("crs_str", "EPSG:31982")),
            eliminar_tiles=bool(context.get("eliminar_tiles", True)),
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