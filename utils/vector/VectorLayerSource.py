# -*- coding: utf-8 -*-
"""
VectorLayerSource — I/O de camadas vetoriais (Shapefile, GeoPackage, CSV)
==========================================================================
Classe estatica unica para leitura de dados vetoriais.
Usa geopandas para .shp/.gpkg e csv.DictReader para .csv.

Responsabilidades:
    - Carregar, salvar, validar, clonar camadas vetoriais
    - I/O de arquivos (Shapefile, GeoPackage, CSV)
    - Validacao de camadas com regras padronizadas
    - Exportacao para GPKG temporario
    - Gerenciamento de conflitos de nomes

Uso:
    from utils.vector.VectorLayerSource import VectorLayerSource
    data = VectorLayerSource.read("dados.shp", tool_key=ToolKey.MEU_PLUGIN.value)
    saved = VectorLayerSource.save_vector_layer(layer, save_to_folder=True, ...)
"""

from __future__ import annotations

import csv
import os
from typing import Any, List, Optional, Tuple

from core.enum.ToolKey import ToolKey
from utils.BaseUtil import BaseUtil


class VectorLayerSource(BaseUtil):
    """
    Metodos estaticos para I/O de camadas vetoriais.
    Converte tipos numpy para tipos nativos Python automaticamente.
    Nao transforma geometrias — use VectorLayerGeometry para isso.
    """

    _SUPPORTED_EXTENSIONS = frozenset({".shp", ".gpkg", ".csv"})

    # ── API Publica — Leitura ────────────────────────────────────────

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
        logger.info("Lendo arquivo vetorial", code="VECTOR_READ_START", path=path)

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
                "Arquivo lido com sucesso",
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

    # ── API Publica — Salvamento ─────────────────────────────────────

    @staticmethod
    def save_vector_layer(
        layer: Any,
        save_to_folder: bool = True,
        output_path: Optional[str] = None,
        output_name: Optional[str] = None,
        decision: str = "rename",
        external_tool_key: str = ToolKey.UNTRACEABLE.value,
    ) -> Any:
        """
        Salva camada (memoria ou disco).
        decision: "rename" ou "overwrite".

        Args:
            layer: QgsVectorLayer
            save_to_folder: Salvar em pasta
            output_path: Caminho de saida
            output_name: Nome de saida
            decision: "rename" ou "overwrite"
            external_tool_key: Chave da ferramenta para logging

        Returns:
            QgsVectorLayer ou None.
        """
        logger = BaseUtil._get_logger(external_tool_key, "VectorLayerSource")
        logger.info("save_vector_layer chamado — stub", code="VECTOR_SAVE_STUB")
        return None

    @staticmethod
    def save_layer_to_path(
        layer: Any,
        output_path: str,
        tool_key: str = ToolKey.UNTRACEABLE.value,
        decision: str = "rename",
    ) -> Optional[str]:
        """
        Salva e retorna caminho efetivo.

        Args:
            layer: QgsVectorLayer
            output_path: Caminho de saida
            tool_key: Chave da ferramenta para logging
            decision: "rename" ou "overwrite"

        Returns:
            Caminho efetivo ou None.
        """
        logger = BaseUtil._get_logger(tool_key, "VectorLayerSource")
        logger.info("save_layer_to_path chamado — stub", code="VECTOR_SAVE_STUB")
        return output_path

    @staticmethod
    def save_and_load_layer(
        layer: Any,
        output_path: str,
        tool_key: str = ToolKey.UNTRACEABLE.value,
        decision: str = "rename",
    ) -> Any:
        """
        Salva e retorna camada carregada.

        Args:
            layer: QgsVectorLayer
            output_path: Caminho de saida
            tool_key: Chave da ferramenta para logging
            decision: "rename" ou "overwrite"

        Returns:
            QgsVectorLayer ou None.
        """
        logger = BaseUtil._get_logger(tool_key, "VectorLayerSource")
        logger.info("save_and_load_layer chamado — stub", code="VECTOR_SAVE_STUB")
        return None

    # ── API Publica — Carregamento ───────────────────────────────────

    @staticmethod
    def load_existing_vector_layer(
        file_path: str,
        tool_key: str = ToolKey.UNTRACEABLE.value,
    ) -> Any:
        """
        Carrega camada de arquivo existente.

        Args:
            file_path: Caminho do arquivo
            tool_key: Chave da ferramenta para logging

        Returns:
            QgsVectorLayer ou None.
        """
        logger = BaseUtil._get_logger(tool_key, "VectorLayerSource")
        logger.info("load_existing_vector_layer chamado — stub", code="VECTOR_LOAD_STUB")
        return None

    # ── API Publica — Utilitarios ────────────────────────────────────

    @staticmethod
    def get_layer_file_size(
        layer: Any,
        tool_key: str = ToolKey.UNTRACEABLE.value,
    ) -> int:
        """
        Tamanho do datasource em bytes.

        Args:
            layer: QgsVectorLayer
            tool_key: Chave da ferramenta para logging

        Returns:
            Tamanho em bytes.
        """
        logger = BaseUtil._get_logger(tool_key, "VectorLayerSource")
        logger.info("get_layer_file_size chamado — stub", code="VECTOR_UTIL_STUB")
        return 0

    @staticmethod
    def get_extension(
        path: str,
        tool_key: str = ToolKey.UNTRACEABLE.value,
    ) -> str:
        """
        Extensao normalizada do caminho.

        Args:
            path: Caminho do arquivo
            tool_key: Chave da ferramenta para logging

        Returns:
            Extensao em lowercase.
        """
        return os.path.splitext(path)[1].lower()

    @staticmethod
    def export_temp_layer(
        layer: Any,
        prefix: str = "temp",
        external_tool_key: str = ToolKey.UNTRACEABLE.value,
    ) -> Optional[str]:
        """
        Exporta para GPKG temporario.

        Args:
            layer: QgsVectorLayer
            prefix: Prefixo do nome
            external_tool_key: Chave da ferramenta para logging

        Returns:
            Caminho do GPKG temporario ou None.
        """
        logger = BaseUtil._get_logger(external_tool_key, "VectorLayerSource")
        logger.info("export_temp_layer chamado — stub", code="VECTOR_UTIL_STUB")
        return None

    @staticmethod
    def delete_shapefile_set(
        base_path: str,
        retries: int = 3,
        delay: float = 0.5,
        tool_key: str = ToolKey.UNTRACEABLE.value,
    ) -> bool:
        """
        Remove conjunto de arquivos SHP.

        Args:
            base_path: Caminho base do shapefile
            retries: Tentativas de remocao
            delay: Delay entre tentativas
            tool_key: Chave da ferramenta para logging

        Returns:
            True se removido com sucesso.
        """
        logger = BaseUtil._get_logger(tool_key, "VectorLayerSource")
        logger.info("delete_shapefile_set chamado — stub", code="VECTOR_UTIL_STUB")
        return False

    @staticmethod
    def generate_incremental_path(
        path: str,
        tool_key: str = ToolKey.UNTRACEABLE.value,
    ) -> str:
        """
        Gera caminho incremental (arquivo_1, _2, ...).

        Args:
            path: Caminho base
            tool_key: Chave da ferramenta para logging

        Returns:
            Caminho incremental.
        """
        logger = BaseUtil._get_logger(tool_key, "VectorLayerSource")
        logger.info("generate_incremental_path chamado — stub", code="VECTOR_UTIL_STUB")
        return path

    # ── API Publica — Validacao ──────────────────────────────────────

    @staticmethod
    def validate_layer(
        layer: Any,
        expected_geometry: Any = None,
        require_editable: bool = False,
        tool_key: str = ToolKey.UNTRACEABLE.value,
    ) -> Tuple[bool, str]:
        """
        Valida camada com regras padronizadas.

        Args:
            layer: QgsVectorLayer
            expected_geometry: QgsWkbTypes esperado (opcional)
            require_editable: Exige modo de edicao
            tool_key: Chave da ferramenta para logging

        Returns:
            (valido, mensagem).
        """
        logger = BaseUtil._get_logger(tool_key, "VectorLayerSource")
        logger.info("validate_layer chamado — stub", code="VECTOR_VALIDATE_STUB")
        return (False, "Nao implementado")

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