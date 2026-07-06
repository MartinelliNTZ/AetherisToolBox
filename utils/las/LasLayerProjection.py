# -*- coding: utf-8 -*-
"""
LasLayerProjection — Utilitário para CRS e Reprojeção de LAS/LAZ
==================================================================
Classe irmã de LasLayerSource, herda de BaseUtil.
Fornece métodos para leitura de CRS e reprojeção de nuvens LAS/LAZ.

Uso:
    from utils.las.LasLayerProjection import LasLayerProjection

    crs = LasLayerProjection.get_crs("nuvem.las")
    result = LasLayerProjection.reproject_las(
        "nuvem.las", "nuvem_reprojetada.las",
        target_crs="EPSG:31983", source_crs="EPSG:4326",
    )
"""

from __future__ import annotations

import os
from typing import Any, Dict, Optional

import laspy
import numpy as np

from core.enum.ToolKey import ToolKey
from utils.BaseUtil import BaseUtil

# ── Tenta importar pyproj ──────────────────────────────────────────────
try:
    from pyproj import CRS as PyProjCRS, Transformer
    _HAS_PYPROJ = True
except ImportError:
    _HAS_PYPROJ = False


class LasLayerProjection(BaseUtil):
    """
    Métodos estáticos para leitura de CRS e reprojeção de arquivos LAS/LAZ.

    Todas as funções aceitam `tool_key: str = ToolKey.UNTRACEABLE.value`
    como parâmetro nomeado, conforme padrão BaseUtil.
    """

    # ══════════════════════════════════════════════════════════════════
    # API Pública — CRS
    # ══════════════════════════════════════════════════════════════════

    @staticmethod
    def get_crs(
        path: str,
        tool_key: str = ToolKey.UNTRACEABLE.value,
    ) -> str:
        """
        Lê o CRS (Coordinate Reference System) do header de um arquivo LAS/LAZ.

        Extrai o CRS dos VLRs (Variable Length Records) do LAS,
        tipicamente armazenado como WKT ou GeoTIFF keys.

        Args:
            path: Caminho completo para o arquivo .las ou .laz.
            tool_key: ToolKey para logging.

        Returns:
            String no formato "EPSG:XXXX" se encontrado,
            ou string vazia se não foi possível determinar o CRS.

        Raises:
            FileNotFoundError: se o arquivo não existir.
            ValueError: se a extensão não for .las/.laz.
        """
        logger = BaseUtil._get_logger(tool_key, "LasLayerProjection")

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
                vlrs = las.header.vlrs
                for vlr in vlrs:
                    parsed = getattr(vlr, "parsed_crs", None)
                    if parsed is not None:
                        crs_str = str(parsed)
                        logger.info(
                            "CRS encontrado nos VLRs do LAS",
                            code="LAS_CRS_FOUND",
                            path=path,
                            crs=crs_str,
                        )
                        return crs_str

            logger.warning(
                "Nenhum CRS encontrado nos VLRs do LAS",
                code="LAS_CRS_NOT_FOUND",
                path=path,
            )
            return ""

        except Exception as e:
            logger.error(
                "Erro ao ler CRS do LAS",
                code="LAS_CRS_ERR",
                path=path,
                error=str(e),
            )
            return ""

    # ══════════════════════════════════════════════════════════════════
    # API Pública — Reprojeção
    # ══════════════════════════════════════════════════════════════════

    @staticmethod
    def reproject_las(
        input_path: str,
        output_path: str,
        target_crs: str,
        source_crs: str = "",
        tool_key: str = ToolKey.UNTRACEABLE.value,
    ) -> Dict[str, Any]:
        """
        Reprojeta (transforma CRS) uma nuvem de pontos LAS/LAZ.

        Lê o arquivo de entrada, transforma as coordenadas X, Y, Z
        usando pyproj.Transformer e salva um novo arquivo LAS.

        Args:
            input_path: Caminho do arquivo LAS/LAZ de entrada.
            output_path: Caminho para salvar o LAS reprojetado.
            target_crs: CRS de destino (ex: "EPSG:31983").
            source_crs: CRS de origem. Se vazio, tenta detectar
                        automaticamente do header do LAS.
            tool_key: ToolKey para logging.

        Returns:
            Dicionário com:
                - n_points    : int  (pontos processados)
                - output_path : str  (caminho do arquivo salvo)
                - source_crs  : str  (CRS de origem usado)
                - target_crs  : str  (CRS de destino)
                - error       : str | None

        Raises:
            FileNotFoundError: se o arquivo de entrada não existir.
            ValueError: se extensão inválida ou pyproj não disponível.
            RuntimeError: se a transformação falhar.
        """
        logger = BaseUtil._get_logger(tool_key, "LasLayerProjection")

        # ── Validações ──────────────────────────────────────────────
        input_path = input_path.strip()
        if not os.path.isfile(input_path):
            raise FileNotFoundError(f"Arquivo não encontrado: {input_path}")

        ext = os.path.splitext(input_path)[1].lower()
        if ext not in (".las", ".laz"):
            raise ValueError(
                f"Extensão inválida '{ext}'. Esperado .las ou .laz."
            )

        if not _HAS_PYPROJ:
            raise ValueError(
                "pyproj não está instalado. "
                "Execute: pip install pyproj"
            )

        if not target_crs:
            raise ValueError("target_crs é obrigatório.")

        # ── Detecta CRS de origem se não informado ──────────────────
        if not source_crs:
            source_crs = LasLayerProjection.get_crs(input_path, tool_key=tool_key)
            if not source_crs:
                raise ValueError(
                    "CRS de origem não pôde ser detectado automaticamente. "
                    "Informe source_crs manualmente."
                )
            logger.info(
                "CRS de origem detectado automaticamente",
                code="LAS_REPROJ_SRC_AUTO",
                source_crs=source_crs,
            )

        logger.info(
            "Iniciando reprojeção LAS",
            code="LAS_REPROJ_START",
            input_path=input_path,
            output_path=output_path,
            source_crs=source_crs,
            target_crs=target_crs,
        )

        try:
            # ── Lê o LAS ────────────────────────────────────────────
            las = laspy.read(input_path)
            n_total = len(las.points)

            if n_total == 0:
                logger.warning(
                    "LAS vazio — nenhum ponto para reprojetar",
                    code="LAS_REPROJ_EMPTY",
                )
                return {
                    "n_points": 0,
                    "output_path": output_path,
                    "source_crs": source_crs,
                    "target_crs": target_crs,
                    "error": "LAS vazio",
                }

            # ── Cria o transformer ──────────────────────────────────
            src_crs_obj = PyProjCRS(source_crs)
            tgt_crs_obj = PyProjCRS(target_crs)
            transformer = Transformer.from_crs(
                src_crs_obj, tgt_crs_obj, always_xy=True
            )

            # ── Transforma coordenadas ──────────────────────────────
            x = np.asarray(las.x, dtype=np.float64)
            y = np.asarray(las.y, dtype=np.float64)
            z = np.asarray(las.z, dtype=np.float64)

            x_new, y_new, z_new = transformer.transform(x, y, z)

            # ── Atualiza os arrays no LAS ───────────────────────────
            las.x = x_new
            las.y = y_new
            las.z = z_new

            # ── Garante diretório de saída ──────────────────────────
            output_dir = os.path.dirname(output_path)
            if output_dir:
                os.makedirs(output_dir, exist_ok=True)

            # ── Salva o LAS reprojetado ─────────────────────────────
            las.write(output_path)

            result = {
                "n_points": n_total,
                "output_path": output_path,
                "source_crs": source_crs,
                "target_crs": target_crs,
                "error": None,
            }

            logger.info(
                "LAS reprojetado com sucesso",
                code="LAS_REPROJ_DONE",
                n_points=n_total,
                output_path=output_path,
                source_crs=source_crs,
                target_crs=target_crs,
            )
            return result

        except Exception as e:
            logger.error(
                "Erro ao reprojetar LAS",
                code="LAS_REPROJ_ERR",
                input_path=input_path,
                error=str(e),
            )
            return {
                "n_points": 0,
                "output_path": output_path,
                "source_crs": source_crs,
                "target_crs": target_crs,
                "error": str(e),
            }