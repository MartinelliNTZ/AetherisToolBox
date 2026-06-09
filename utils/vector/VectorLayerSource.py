# -*- coding: utf-8 -*-
"""
VectorLayerSource — I/O de camadas vetoriais (Shapefile, GeoPackage, CSV)
==========================================================================
Classe estatica unica para leitura de dados vetoriais.
Usa geopandas para .shp/.gpkg e csv.DictReader para .csv.

Uso:
    from utils.vector.VectorLayerSource import VectorLayerSource
    data = VectorLayerSource.read("dados.shp", tool_key=ToolKey.MEU_PLUGIN.value)
"""

from __future__ import annotations

import csv
import os
from typing import List

from core.enum.ToolKey import ToolKey
from utils.BaseUtil import BaseUtil


class VectorLayerSource(BaseUtil):
    """
    Metodos estaticos para leitura de camadas vetoriais.
    Converte tipos numpy para tipos nativos Python automaticamente.
    """

    _SUPPORTED_EXTENSIONS = frozenset({".shp", ".gpkg", ".csv"})

    # ── API Publica ──────────────────────────────────────────────────

    @staticmethod
    def read(path: str, tool_key: str = ToolKey.UNTRACEABLE.value) -> List[dict]:
        """
        Le um arquivo vetorial e retorna lista de dicionarios.

        Args:
            path: Caminho do arquivo (.shp, .gpkg, .csv).
            tool_key: Chave da ferramenta para logging.

        Returns:
            Lista de dicts com os dados. Cada dict = uma linha/feature.
            Vazio se arquivo invalido ou vazio.

        Raises:
            ValueError: Se extensao nao suportada.
            FileNotFoundError: Se arquivo nao existe.
        """
        logger = BaseUtil._get_logger(tool_key, "VectorLayerSource")
        logger.info(f"Lendo arquivo vetorial", code="VECTOR_READ_START", path=path)

        if not os.path.exists(path):
            logger.error("Arquivo nao encontrado", code="VECTOR_NOT_FOUND", path=path)
            raise FileNotFoundError(f"Arquivo nao encontrado: {path}")

        ext = os.path.splitext(path)[1].lower()
        if ext not in VectorLayerSource._SUPPORTED_EXTENSIONS:
            logger.error(
                "Extensao nao suportada",
                code="VECTOR_UNSUPPORTED_EXT",
                path=path,
                extension=ext,
                supported=list(VectorLayerSource._SUPPORTED_EXTENSIONS),
            )
            raise ValueError(
                f"Extensao '{ext}' nao suportada. "
                f"Use: {', '.join(VectorLayerSource._SUPPORTED_EXTENSIONS)}"
            )

        try:
            if ext == ".csv":
                data = VectorLayerSource._read_csv(path)
            else:
                data = VectorLayerSource._read_geo(path)

            logger.info(
                f"Arquivo lido com sucesso",
                code="VECTOR_READ_DONE",
                path=path,
                record_count=len(data),
            )
            return data

        except Exception as e:
            logger.error("Falha ao ler arquivo vetorial", code="VECTOR_READ_ERR", path=path, error=str(e))
            raise

    @staticmethod
    def get_driver_name(
        path: str,
        tool_key: str = ToolKey.UNTRACEABLE.value,
    ) -> str:
        """
        Retorna o nome do driver/formato baseado na extensao.

        Args:
            path: Caminho do arquivo.
            tool_key: Chave da ferramenta para logging.

        Returns:
            Nome legivel do formato: "ESRI Shapefile", "GeoPackage", "CSV", ou "Desconhecido".
        """
        logger = BaseUtil._get_logger(tool_key, "VectorLayerSource")
        ext = os.path.splitext(path)[1].lower()
        drivers = {
            ".shp": "ESRI Shapefile",
            ".gpkg": "GeoPackage",
            ".csv": "CSV",
        }
        result = drivers.get(ext, "Desconhecido")
        logger.debug("Driver obtido", code="VECTOR_DRIVER", path=path, driver=result)
        return result

    # ── Leitura Interna ──────────────────────────────────────────────

    @staticmethod
    def _read_csv(path: str) -> List[dict]:
        """Le CSV usando csv.DictReader."""
        data: List[dict] = []
        with open(path, "r", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            for row in reader:
                cleaned = {k.strip(): v.strip() if v else "" for k, v in row.items()}
                data.append(cleaned)
        return data

    @staticmethod
    def _read_geo(path: str) -> List[dict]:
        """Le Shapefile ou GeoPackage usando geopandas."""
        import geopandas as gpd
        import numpy as np

        gdf = gpd.read_file(path)

        # Remove coluna geometry
        if "geometry" in gdf.columns:
            gdf = gdf.drop(columns=["geometry"])

        # Converte tipos numpy para tipos nativos
        rows: List[dict] = []
        for _, row in gdf.iterrows():
            d = {}
            for col in gdf.columns:
                val = row[col]
                if isinstance(val, (np.integer,)):
                    d[col] = str(int(val))
                elif isinstance(val, (np.floating,)):
                    d[col] = str(float(val))
                elif isinstance(val, (np.bool_,)):
                    d[col] = str(bool(val))
                elif val is None or (isinstance(val, float) and np.isnan(val)):
                    d[col] = ""
                else:
                    d[col] = str(val)
            rows.append(d)

        return rows