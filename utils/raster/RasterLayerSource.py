# -*- coding: utf-8 -*-
"""
RasterLayerSource — I/O de camadas raster (placeholder)
=========================================================
Placeholder para leitura futura de metadados de rasters GeoTIFF.
"""

from __future__ import annotations

from typing import Dict

from core.enum.ToolKey import ToolKey
from utils.BaseUtil import BaseUtil


class RasterLayerSource(BaseUtil):
    """
    Metodos estaticos para leitura de camadas raster.
    Placeholder — implementacao basica de metadados.
    """

    @staticmethod
    def read_metadata(
        path: str,
        tool_key: str = ToolKey.UNTRACEABLE.value,
    ) -> Dict:
        """
        Le metadados basicos de um raster GeoTIFF.

        Args:
            path: Caminho do arquivo .tif/.tiff.
            tool_key: Chave da ferramenta para logging.

        Returns:
            Dict com metadados disponiveis, ou dict vazio se nao for possivel ler.
        """
        logger = BaseUtil._get_logger(tool_key, "RasterLayerSource")
        logger.info("Leitura de raster ainda nao implementada", code="RASTER_STUB", path=path)
        return {}