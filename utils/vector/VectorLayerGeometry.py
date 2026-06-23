# -*- coding: utf-8 -*-
"""
VectorLayerGeometry — Transformacoes geometricas de camadas vetoriais
======================================================================
Responsavel por transformacoes geometricas: buffer, explode, merge,
criacao de camadas de pontos/linhas, calculo de azimute, etc.
Altera geometrias, converte tipos, aplica operacoes topologicas.

Uso:
    from utils.vector.VectorLayerGeometry import VectorLayerGeometry
    point_layer = VectorLayerGeometry.create_point_layer_from_dicts(...)
"""

from __future__ import annotations

from typing import Any, Callable, Dict, List, Optional, Tuple

from core.enum.ToolKey import ToolKey
from utils.BaseUtil import BaseUtil


class VectorLayerGeometry(BaseUtil):
    """
    Metodos estaticos para transformacoes geometricas de camadas vetoriais.
    Nao calcula metricas — use VectorLayerMetrics para isso.
    Nao reprojeta — use VectorLayerProjection para isso.
    """

    # ── API Publica ──────────────────────────────────────────────────

    @staticmethod
    def calculate_point_azimuth(point_a: Any, point_b: Any) -> float:
        """
        Calcula azimute 0-360 graus (norte=0, leste=90).

        Args:
            point_a: QgsPointXY / QgsPoint
            point_b: QgsPointXY / QgsPoint

        Returns:
            Azimute em graus.
        """
        return 0.0

    @staticmethod
    def angular_difference_degrees(angle_a: float, angle_b: float) -> float:
        """
        Menor diferenca angular absoluta entre dois angulos.

        Args:
            angle_a: Angulo A em graus
            angle_b: Angulo B em graus

        Returns:
            Diferenca absoluta em graus.
        """
        diff = abs(angle_a - angle_b) % 360
        return min(diff, 360 - diff)

    @staticmethod
    def circular_mean_degrees(values: List[float]) -> float:
        """
        Media circular em graus.

        Args:
            values: Lista de angulos em graus

        Returns:
            Media circular.
        """
        import math
        if not values:
            return 0.0
        sin_sum = sum(math.sin(math.radians(v)) for v in values)
        cos_sum = sum(math.cos(math.radians(v)) for v in values)
        return math.degrees(math.atan2(sin_sum, cos_sum)) % 360

    @staticmethod
    def measure_distance_between_points(
        point_a: Any,
        point_b: Any,
        crs: Any = None,
    ) -> float:
        """
        Distancia entre pontos (elipsoidal se CRS informado).

        Args:
            point_a: QgsPointXY / QgsPoint
            point_b: QgsPointXY / QgsPoint
            crs: QgsCoordinateReferenceSystem (opcional)

        Returns:
            Distancia em metros ou unidades do CRS.
        """
        return 0.0

    @staticmethod
    def get_representative_point(geometry: Any) -> Any:
        """
        Ponto representativo de Point/MultiPoint.

        Args:
            geometry: QgsGeometry

        Returns:
            QgsPointXY ou None.
        """
        return None

    @staticmethod
    def create_point_layer_from_dicts(
        points: List[Dict[str, Any]],
        name: str,
        field_specs: List[Tuple[str, Any]],
        geometry_keys: Tuple[str, str],
        extra_fields: Optional[List[str]] = None,
        tool_key: str = ToolKey.UNTRACEABLE.value,
    ) -> Any:
        """
        Cria camada de pontos em memoria a partir de dicts.
        geometry_keys=(x_key, y_key)

        Args:
            points: Lista de dicts com dados
            name: Nome da camada
            field_specs: Especificacao dos campos [(nome, tipo), ...]
            geometry_keys: Chaves para coordenadas (x_key, y_key)
            extra_fields: Campos extras a incluir
            tool_key: Chave da ferramenta para logging

        Returns:
            QgsVectorLayer ou None.
        """
        logger = BaseUtil._get_logger(tool_key, "VectorLayerGeometry")
        logger.info("create_point_layer_from_dicts chamado — stub", code="GEOM_STUB")
        return None

    @staticmethod
    def create_line_layer_from_points(
        points: List[Any],
        order_by_field: str,
        name: str,
        group_by_fields: Optional[List[str]] = None,
        attribute_fields: Optional[List[str]] = None,
        tool_key: str = ToolKey.UNTRACEABLE.value,
    ) -> Any:
        """
        Cria linha(s) em memoria a partir de QgsFeature Point.

        Args:
            points: Lista de QgsFeature
            order_by_field: Campo para ordenacao dos pontos
            name: Nome da camada
            group_by_fields: Campos para agrupar linhas
            attribute_fields: Campos de atributos a incluir
            tool_key: Chave da ferramenta para logging

        Returns:
            QgsVectorLayer ou None.
        """
        logger = BaseUtil._get_logger(tool_key, "VectorLayerGeometry")
        logger.info("create_line_layer_from_points chamado — stub", code="GEOM_STUB")
        return None

    @staticmethod
    def merge_memory_layers(
        layers: List[Any],
        crs_authid: str,
        layer_name: str,
        tool_key: str = ToolKey.UNTRACEABLE.value,
    ) -> Any:
        """
        Mescla camadas de memoria em uma unica camada.

        Args:
            layers: Lista de QgsVectorLayer
            crs_authid: CRS auth id (ex: "EPSG:31983")
            layer_name: Nome da camada resultante
            tool_key: Chave da ferramenta para logging

        Returns:
            QgsVectorLayer ou None.
        """
        logger = BaseUtil._get_logger(tool_key, "VectorLayerGeometry")
        logger.info("merge_memory_layers chamado — stub", code="GEOM_STUB")
        return None

    @staticmethod
    def create_buffer_geometry(
        layer: Any,
        distance: float,
        output_path: Optional[str] = None,
        segments: int = 10,
        dissolve: bool = False,
        external_tool_key: str = ToolKey.UNTRACEABLE.value,
    ) -> Any:
        """
        Buffer ao redor das geometrias (via processing).

        Args:
            layer: QgsVectorLayer
            distance: Distancia do buffer em unidades da camada
            output_path: Caminho de saida (opcional)
            segments: Segmentos para arredondamento
            dissolve: Dissolver buffers sobrepostos
            external_tool_key: Chave da ferramenta para logging

        Returns:
            QgsVectorLayer ou None.
        """
        logger = BaseUtil._get_logger(external_tool_key, "VectorLayerGeometry")
        logger.info("create_buffer_geometry chamado — stub", code="GEOM_STUB")
        return None

    @staticmethod
    def create_buffer_to_path_safe(
        input_path: str,
        output_path: str,
        distance: float,
        segments: int = 10,
        dissolve: bool = False,
        external_tool_key: str = ToolKey.UNTRACEABLE.value,
    ) -> str:
        """
        Buffer usando arquivo fisico (seguro para QgsTask).

        Args:
            input_path: Caminho do arquivo de entrada
            output_path: Caminho do arquivo de saida
            distance: Distancia do buffer
            segments: Segmentos para arredondamento
            dissolve: Dissolver buffers sobrepostos
            external_tool_key: Chave da ferramenta para logging

        Returns:
            output_path.
        """
        logger = BaseUtil._get_logger(external_tool_key, "VectorLayerGeometry")
        logger.info("create_buffer_to_path_safe chamado — stub", code="GEOM_STUB")
        return output_path

    @staticmethod
    def explode_lines_to_path_safe(
        layer: Any,
        output_path: str,
        external_tool_key: str = ToolKey.UNTRACEABLE.value,
    ) -> str:
        """
        Explode linhas manualmente (thread-safe, compativel QgsTask).

        Args:
            layer: QgsVectorLayer
            output_path: Caminho do arquivo de saida
            external_tool_key: Chave da ferramenta para logging

        Returns:
            output_path.
        """
        logger = BaseUtil._get_logger(external_tool_key, "VectorLayerGeometry")
        logger.info("explode_lines_to_path_safe chamado — stub", code="GEOM_STUB")
        return output_path

    @staticmethod
    def get_layer_type(
        layer: Any,
        tool_key: str = ToolKey.UNTRACEABLE.value,
    ) -> Optional[int]:
        """
        Retorna tipo da geometria (QgsWkbTypes.PointGeometry etc).

        Args:
            layer: QgsVectorLayer
            tool_key: Chave da ferramenta para logging

        Returns:
            Inteiro do tipo WKB ou None.
        """
        logger = BaseUtil._get_logger(tool_key, "VectorLayerGeometry")
        logger.info("get_layer_type chamado — stub", code="GEOM_STUB")
        return None

    @staticmethod
    def get_selected_features(
        layer: Any,
        tool_key: str = ToolKey.UNTRACEABLE.value,
    ) -> Tuple[Any, str]:
        """
        Materializa feicoes selecionadas em nova camada.

        Args:
            layer: QgsVectorLayer
            tool_key: Chave da ferramenta para logging

        Returns:
            (QgsVectorLayer, str) — camada e nome.
        """
        logger = BaseUtil._get_logger(tool_key, "VectorLayerGeometry")
        logger.info("get_selected_features chamado — stub", code="GEOM_STUB")
        return (None, "")

    @staticmethod
    def singleparts_to_multparts(
        layer: Any,
        feedback: Any = None,
        only_selected: bool = False,
        tool_key: str = ToolKey.UNTRACEABLE.value,
    ) -> bool:
        """
        Converte singlepart para multipart (processamento batch).

        Args:
            layer: QgsVectorLayer
            feedback: QgsProcessingFeedback (opcional)
            only_selected: Apenas feicoes selecionadas
            tool_key: Chave da ferramenta para logging

        Returns:
            True se sucesso.
        """
        logger = BaseUtil._get_logger(tool_key, "VectorLayerGeometry")
        logger.info("singleparts_to_multparts chamado — stub", code="GEOM_STUB")
        return False