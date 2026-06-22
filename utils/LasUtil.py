# -*- coding: utf-8 -*-
"""
LasUtil — Utilitário para arquivos LAS/LAZ
============================================
Fornece métodos estáticos para leitura de metadados de arquivos
LAS/LAZ, como contagem de pontos, verificação de bandas RGB, etc.

Uso:
    from utils.LasUtil import LasUtil

    info = LasUtil.get_info("c:/dados/nuvem.las")
    print(info["point_count"])   # 1_234_567
    print(info["has_rgb"])       # True
"""

from __future__ import annotations

import os
from typing import Any, Dict

import laspy
import numpy as np

from core.config.LogUtils import LogUtils
from core.enum.ToolKey import ToolKey
from utils.BaseUtil import BaseUtil


class LasUtil(BaseUtil):
    """
    Métodos estáticos para extração de metadados de arquivos LAS/LAZ.

    Todas as funções aceitam `tool_key: str = ToolKey.UNTRACEABLE.value`
    como parâmetro nomeado, conforme padrão BaseUtil.
    """

    # ══════════════════════════════════════════════════════════════════
    # API Pública
    # ══════════════════════════════════════════════════════════════════

    @staticmethod
    def get_info(
        path: str,
        tool_key: str = ToolKey.UNTRACEABLE.value,
    ) -> Dict[str, Any]:
        """
        Retorna metadados básicos de um arquivo LAS/LAZ.

        Args:
            path: Caminho completo para o arquivo .las ou .laz.
            tool_key: ToolKey para logging.

        Returns:
            Dicionário com:
                - path           : str
                - point_count    : int
                - has_rgb        : bool
                - dimension_names: list[str] (nomes das dimensões)
                - error          : str | None (se houve falha)

        Raises:
            FileNotFoundError: se o arquivo não existir.
            ValueError: se a extensão não for .las/.laz.
        """
        logger = BaseUtil._get_logger(tool_key, "LasUtil")

        # Validações
        path = path.strip()
        if not os.path.isfile(path):
            raise FileNotFoundError(f"Arquivo não encontrado: {path}")

        ext = os.path.splitext(path)[1].lower()
        if ext not in (".las", ".laz"):
            raise ValueError(
                f"Extensão inválida '{ext}'. Esperado .las ou .laz."
            )

        try:
            with laspy.open(path) as las:
                point_count = las.header.point_count
                dim_names = list(las.header.point_format.dimension_names)
                has_rgb = "red" in dim_names

            info: Dict[str, Any] = {
                "path": path,
                "point_count": point_count,
                "has_rgb": has_rgb,
                "dimension_names": dim_names,
                "error": None,
            }

            logger.info(
                "Metadados LAS obtidos",
                code="LAS_INFO",
                path=path,
                point_count=point_count,
                has_rgb=has_rgb,
            )
            return info

        except Exception as e:
            logger.error(
                "Erro ao ler metadados LAS",
                code="LAS_INFO_ERR",
                path=path,
                error=str(e),
            )
            return {
                "path": path,
                "point_count": 0,
                "has_rgb": False,
                "dimension_names": [],
                "error": str(e),
            }

    @staticmethod
    def get_point_count(
        path: str,
        tool_key: str = ToolKey.UNTRACEABLE.value,
    ) -> int:
        """
        Retorna apenas o número total de pontos do arquivo LAS.

        Args:
            path: Caminho do arquivo.
            tool_key: ToolKey para logging.

        Returns:
            Número total de pontos (0 se erro).
        """
        try:
            info = LasUtil.get_info(path, tool_key=tool_key)
            return info.get("point_count", 0)
        except Exception:
            return 0

    @staticmethod
    def has_rgb(
        path: str,
        tool_key: str = ToolKey.UNTRACEABLE.value,
    ) -> bool:
        """
        Verifica se o arquivo LAS possui bandas RGB.

        Args:
            path: Caminho do arquivo.
            tool_key: ToolKey para logging.

        Returns:
            True se tem bandas 'red', 'green', 'blue'.
        """
        try:
            info = LasUtil.get_info(path, tool_key=tool_key)
            return info.get("has_rgb", False)
        except Exception:
            return False

    @staticmethod
    def get_bounding_box(
        path: str,
        tool_key: str = ToolKey.UNTRACEABLE.value,
        sample_size: int = 10000,
    ) -> Dict[str, float]:
        """
        Retorna bounding box aproximada (lendo amostra de pontos).

        Args:
            path: Caminho do arquivo.
            tool_key: ToolKey para logging.
            sample_size: Nº máximo de pontos para amostragem.

        Returns:
            Dict com 'x_min', 'x_max', 'y_min', 'y_max', 'z_min', 'z_max'
            ou dict vazio se erro.
        """
        logger = BaseUtil._get_logger(tool_key, "LasUtil")
        try:
            info = LasUtil.get_info(path, tool_key=tool_key)
            if info.get("error"):
                return {}

            las_read = laspy.read(path, count=min(sample_size, info["point_count"]))
            if len(las_read.points) == 0:
                return {}

            bbox = {
                "x_min": float(np.min(las_read.x)),
                "x_max": float(np.max(las_read.x)),
                "y_min": float(np.min(las_read.y)),
                "y_max": float(np.max(las_read.y)),
                "z_min": float(np.min(las_read.z)),
                "z_max": float(np.max(las_read.z)),
            }
            logger.info("Bounding box calculada", code="LAS_BBOX", **bbox)
            return bbox

        except Exception as e:
            logger.error(
                "Erro ao calcular bounding box",
                code="LAS_BBOX_ERR",
                error=str(e),
            )
            return {}