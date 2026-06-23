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
from typing import Any, Dict, Optional

import laspy
import numpy as np

from core.enum.ToolKey import ToolKey
from utils.BaseUtil import BaseUtil


class LasUtil(BaseUtil):
    """
    Métodos estáticos para extração de metadados de arquivos LAS/LAZ.

    Todas as funções aceitam `tool_key: str = ToolKey.UNTRACEABLE.value`
    como parâmetro nomeado, conforme padrão BaseUtil.
    """

    # ══════════════════════════════════════════════════════════════════
    # API Pública — Metadados
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

    # ══════════════════════════════════════════════════════════════════
    # API Pública — Leitura de Arrays
    # ══════════════════════════════════════════════════════════════════

    @staticmethod
    def get_rgb_arrays(
        path: str,
        tool_key: str = ToolKey.UNTRACEABLE.value,
    ) -> Dict[str, np.ndarray]:
        """
        Lê as bandas RGB de um arquivo LAS como arrays numpy int64.

        Args:
            path: Caminho do arquivo LAS/LAZ.
            tool_key: ToolKey para logging.

        Returns:
            Dict com 'red', 'green', 'blue' (np.ndarray dtype int64)
            ou dict vazio se erro ou sem RGB.

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
            las = laspy.read(path)
            if not hasattr(las, "red") or not hasattr(las, "green") or not hasattr(las, "blue"):
                logger.warning(
                    "LAS não possui bandas RGB completas",
                    code="LAS_NO_RGB",
                    path=path,
                )
                return {}

            arrays = {
                "red": np.asarray(las.red, dtype=np.int64),
                "green": np.asarray(las.green, dtype=np.int64),
                "blue": np.asarray(las.blue, dtype=np.int64),
            }

            logger.info(
                "Arrays RGB lidos",
                code="LAS_RGB_READ",
                path=path,
                n_points=len(arrays["red"]),
            )
            return arrays

        except Exception as e:
            logger.error(
                "Erro ao ler arrays RGB do LAS",
                code="LAS_RGB_ERR",
                path=path,
                error=str(e),
            )
            return {}

    # ══════════════════════════════════════════════════════════════════
    # API Pública — Filtragem e Escrita
    # ══════════════════════════════════════════════════════════════════

    @staticmethod
    def ensure_output_dir(
        output_path: str,
        tool_key: str = ToolKey.UNTRACEABLE.value,
    ) -> bool:
        """
        Garante que o diretório do arquivo de saída existe.

        Args:
            output_path: Caminho completo do arquivo de saída.
            tool_key: ToolKey para logging.

        Returns:
            True se o diretório existe ou foi criado, False se erro.
        """
        logger = BaseUtil._get_logger(tool_key, "LasUtil")
        output_dir = os.path.dirname(output_path)
        if not output_dir:
            return True  # diretório atual sempre existe
        try:
            os.makedirs(output_dir, exist_ok=True)
            logger.debug(
                "Diretório de saída garantido",
                code="LAS_OUT_DIR",
                path=output_dir,
            )
            return True
        except Exception as e:
            logger.error(
                "Erro ao criar diretório de saída",
                code="LAS_OUT_DIR_ERR",
                path=output_dir,
                error=str(e),
            )
            return False

    @staticmethod
    def create_filtered_las(
        las: laspy.LasData,
        mask: np.ndarray,
        output_path: str,
        tool_key: str = ToolKey.UNTRACEABLE.value,
    ) -> Optional[int]:
        """
        Cria um novo arquivo LAS a partir de uma máscara booleana.

        Args:
            las: Objeto LasData original (fonte dos pontos e header).
            mask: Array booleano com True para pontos a manter.
            output_path: Caminho para salvar o novo arquivo.
            tool_key: ToolKey para logging.

        Returns:
            Número de pontos salvos, ou None se erro.
        """
        logger = BaseUtil._get_logger(tool_key, "LasUtil")
        try:
            n_pontos = int(np.sum(mask))
            if n_pontos == 0:
                logger.warning(
                    "Máscara vazia — nenhum ponto para salvar",
                    code="LAS_EMPTY_MASK",
                    output=output_path,
                )
                return 0

            las_out = laspy.LasData(las.header)
            las_out.points = las.points[mask]

            if not LasUtil.ensure_output_dir(output_path, tool_key=tool_key):
                return None

            las_out.write(output_path)

            logger.info(
                "LAS filtrado salvo",
                code="LAS_FILTER_SAVED",
                output=output_path,
                n_points=n_pontos,
            )
            return n_pontos

        except Exception as e:
            logger.error(
                "Erro ao salvar LAS filtrado",
                code="LAS_FILTER_SAVE_ERR",
                output=output_path,
                error=str(e),
            )
            return None

    @staticmethod
    def resolve_output_path(
        input_path: str,
        suffix: str = "_filtrado",
        output_dir: Optional[str] = None,
    ) -> str:
        """
        Resolve um caminho de saída com sufixo no nome do arquivo.

        Exemplo:
            input = "c:/dados/nuvem.las"
            suffix = "_filtrado"
            output_dir = "c:/saida"
            → "c:/saida/nuvem_filtrado.las"

        Se output_dir for None, usa o mesmo diretório do input.

        Args:
            input_path: Caminho do arquivo de entrada.
            suffix: Sufixo a adicionar antes da extensão.
            output_dir: Diretório de saída (None = mesmo do input).

        Returns:
            Caminho completo do arquivo de saída.
        """
        dir_origem = os.path.dirname(input_path) if output_dir is None else output_dir
        basename = os.path.splitext(os.path.basename(input_path))[0]
        ext = os.path.splitext(input_path)[1].lower()
        return os.path.join(dir_origem, f"{basename}{suffix}{ext}")

    # ══════════════════════════════════════════════════════════════════
    # API — Extração de Coordenadas (PointBoundaryPlugin)
    # ══════════════════════════════════════════════════════════════════

    @staticmethod
    def extract_points(
        path: str,
        tool_key: str = ToolKey.UNTRACEABLE.value,
        sample: int = 0,
    ) -> tuple[np.ndarray, np.ndarray, dict]:
        """
        Extrai coordenadas (x, y) de um arquivo LAS/LAZ.

        Args:
            path: Caminho do arquivo .las ou .laz.
            tool_key: ToolKey para logging.
            sample: Se > 0, retorna no máximo 'sample' pontos (amostragem uniforme).

        Returns:
            (x_array, y_array, metadata) onde metadata contém:
                - n_total: total de pontos no arquivo
                - n_extraidos: pontos extraídos (após amostragem)
                - has_rgb: se tem bandas RGB
                - crs: CRS em formato string (se disponível no header)
                - fonte: "las"
        """
        logger = BaseUtil._get_logger(tool_key, "LasUtil")
        logger.info("Extraindo pontos do LAS", code="LAS_EXTRACT_POINTS", path=path)

        las = laspy.read(path)
        n_total = len(las.points)

        x = np.asarray(las.x, dtype=np.float64)
        y = np.asarray(las.y, dtype=np.float64)

        has_rgb = hasattr(las, "red") and las.red is not None

        # Tenta extrair CRS do header
        crs = ""
        try:
            vlrs = las.header.vlrs
            for vlr in vlrs:
                if hasattr(vlr, "parsed_crs") and vlr.parsed_crs is not None:
                    crs = str(vlr.parsed_crs)
                    break
        except Exception:
            pass

        # Amostragem
        if sample > 0 and n_total > sample:
            step = max(1, n_total // sample)
            x = x[::step]
            y = y[::step]
            n_extraidos = len(x)
        else:
            n_extraidos = n_total

        metadata = {
            "n_total": n_total,
            "n_extraidos": n_extraidos,
            "has_rgb": has_rgb,
            "crs": crs,
            "fonte": "las",
        }

        logger.info(
            "Pontos extraidos do LAS",
            code="LAS_EXTRACT_DONE",
            n_total=n_total,
            n_extraidos=n_extraidos,
            has_rgb=has_rgb,
            crs=crs or "N/A",
        )
        return x, y, metadata
