# -*- coding: utf-8 -*-
"""
RasterLayerProcessing — Processamento raster pixel a pixel
============================================================
Responsavel pelo processamento raster destrutivo e operacoes pixel a pixel:
extracao de bandas, mascaras, composicao multibanda.

Uso:
    from utils.raster.RasterLayerProcessing import RasterLayerProcessing
    band_path = RasterLayerProcessing.extract_band("mosaico.tif", 1, tool_key=...)
"""

from __future__ import annotations

from typing import List, Optional

from core.enum.ToolKey import ToolKey
from utils.BaseUtil import BaseUtil


class RasterLayerProcessing(BaseUtil):
    """
    Metodos estaticos para processamento raster pixel a pixel.
    Nao reprojeta — use RasterLayerProjection para isso.
    Nao calcula estatisticas — use RasterLayerMetrics para isso.
    """

    # ── API Publica ──────────────────────────────────────────────────

    @staticmethod
    def extract_band(
        raster_path: str,
        band_num: int,
        output_path: Optional[str] = None,
        tool_key: str = ToolKey.UNTRACEABLE.value,
    ) -> str:
        """
        Extrai banda especifica para GeoTIFF.

        Args:
            raster_path: Caminho do raster
            band_num: Numero da banda (1-based)
            output_path: Caminho de saida (opcional, usa temp se None)
            tool_key: Chave da ferramenta para logging

        Returns:
            Caminho do arquivo extraido.
        """
        logger = BaseUtil._get_logger(tool_key, "RasterLayerProcessing")
        logger.info("extract_band chamado — stub", code="RASTER_PROC_STUB")
        return output_path or ""

    @staticmethod
    def create_alpha_mask(
        raster_path: str,
        nodata_value: Optional[float] = None,
        output_path: Optional[str] = None,
        tool_key: str = ToolKey.UNTRACEABLE.value,
    ) -> str:
        """
        Cria mascara alpha (byte: 0/255) a partir de NoData.

        Args:
            raster_path: Caminho do raster
            nodata_value: Valor NoData (usa do raster se None)
            output_path: Caminho de saida (opcional)
            tool_key: Chave da ferramenta para logging

        Returns:
            Caminho da mascara alpha.
        """
        logger = BaseUtil._get_logger(tool_key, "RasterLayerProcessing")
        logger.info("create_alpha_mask chamado — stub", code="RASTER_PROC_STUB")
        return output_path or ""

    @staticmethod
    def compose_multiband_raster(
        band_files: List[str],
        output_path: Optional[str] = None,
        create_alpha: bool = False,
        alpha_band_path: Optional[str] = None,
        creation_options: str = "",
        tool_key: str = ToolKey.UNTRACEABLE.value,
    ) -> str:
        """
        Compoe multiplos GeoTIFFs em raster multibanda.

        Args:
            band_files: Lista de caminhos das bandas
            output_path: Caminho de saida (opcional)
            create_alpha: Criar banda alpha
            alpha_band_path: Caminho da mascara alpha (se create_alpha)
            creation_options: Opcoes GDAL extras
            tool_key: Chave da ferramenta para logging

        Returns:
            Caminho do raster composto.
        """
        logger = BaseUtil._get_logger(tool_key, "RasterLayerProcessing")
        logger.info("compose_multiband_raster chamado — stub", code="RASTER_PROC_STUB")
        return output_path or ""

    @staticmethod
    def apply_nodata_mask(
        raster_path: str,
        mask_path: str,
        output_path: Optional[str] = None,
        tool_key: str = ToolKey.UNTRACEABLE.value,
    ) -> str:
        """
        Aplica mascara NoData em um raster.

        Args:
            raster_path: Caminho do raster
            mask_path: Caminho da mascara (byte: 0/255)
            output_path: Caminho de saida (opcional)
            tool_key: Chave da ferramenta para logging

        Returns:
            Caminho do raster com mascara aplicada.
        """
        logger = BaseUtil._get_logger(tool_key, "RasterLayerProcessing")
        logger.info("apply_nodata_mask chamado — stub", code="RASTER_PROC_STUB")
        return output_path or ""