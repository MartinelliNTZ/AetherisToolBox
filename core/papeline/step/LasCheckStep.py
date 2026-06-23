# -*- coding: utf-8 -*-
"""
LasCheckStep — Step que executa checks de qualidade em nuvens LAS/LAZ
======================================================================
Executa uma bateria de verificações configuráveis via context e retorna
resultados consolidados no context sob a chave "check_results".

Checks implementados:
  1. Contagem de Pontos (point_count)
  2. Bounding Box (bbox)
  3. Bandas RGB (rgb)
  4. Classificação (classification)
  5. Coordenadas Zero (zero_coords)
  6. Duplicatas XY (duplicates)
  7. Densidade / Gaps (density)
  8. Intensidade (intensity)
"""

from __future__ import annotations

from typing import Any

import os

import laspy
import numpy as np

from core.enum.ToolKey import ToolKey
from core.manager.SignalManager import SignalManager
from core.papeline.BaseStep import BaseStep
from core.papeline.ExecutionContext import ExecutionContext
from utils.BaseUtil import BaseUtil
from utils.LasUtil import LasUtil


class LasCheckStep(BaseStep):
    """Step que executa checks de qualidade em nuvens LAS/LAZ."""

    _CHECK_NAMES: dict[str, str] = {
        "point_count": "Contagem de Pontos",
        "bbox": "Bounding Box",
        "rgb": "Bandas RGB",
        "classification": "Classificação",
        "zero_coords": "Coordenadas Zero",
        "duplicates": "Duplicatas XY",
        "density": "Densidade / Gaps",
        "intensity": "Intensidade",
    }

    def name(self) -> str:
        return "LasCheckStep"

    def should_run(self, context: ExecutionContext) -> bool:
        return bool(context.get("file_path"))

    def create_task(self, context: ExecutionContext) -> None:
        return None

    def run_inline(self, context: ExecutionContext) -> dict[str, Any]:
        """
        Executa todos os checks inline (síncrono) na QThread.
        Retorna dict com os resultados.
        """
        tool_key = context.get("tool_key", ToolKey.UNTRACEABLE.value)
        logger = BaseUtil._get_logger(tool_key, "LasCheckStep")
        file_path: str = context.get("file_path", "")
        checks_enabled: dict[str, bool] = context.get("checks_enabled", {})

        signals = SignalManager.instance()

        logger.info(
            "Iniciando checks de qualidade",
            code="LASCHECK_START",
            path=file_path,
        )

        # Abre o LAS/LAZ (usa Lazrs como backend para .laz)
        try:
            laz_backend = laspy.LazBackend.Lazrs
        except AttributeError:
            laz_backend = None

        try:
            las = laspy.read(file_path, laz_backend=laz_backend)
            logger.info(
                "Arquivo aberto com sucesso",
                code="LASCHECK_FILE_OPEN_OK",
                path=file_path,
                ext=os.path.splitext(file_path)[1].lower(),
                total_points=len(las.points),
            )
            signals.console_message.emit(
                f"[LasCheck] Arquivo aberto: {os.path.basename(file_path)} "
                f"({len(las.points):,} pontos)"
            )
        except Exception as e:
            error_msg = str(e)
            logger.error(
                "Falha ao abrir arquivo LAS/LAZ",
                code="LASCHECK_FILE_OPEN_ERR",
                path=file_path,
                error=error_msg,
            )
            if "No LazBackend selected" in error_msg or "cannot decompress" in error_msg:
                logger.critical(
                    "Backend LAZ nao disponivel mesmo com lazrs instalado",
                    code="LASCHECK_LAZ_BACKEND_FAIL",
                    path=file_path,
                )
                signals.console_message.emit(
                    f"[LasCheck] ERRO: Nao foi possivel abrir .LAZ. "
                    f"Verifique instalacao do lazrs (pip install lazrs)."
                )
                return {
                    "check_results": {},
                    "summary": {"pass": 0, "warning": 0, "fail": 1, "total": 0, "error": True},
                    "error_type": "laz_backend",
                    "error": (
                        "Erro ao abrir .LAZ. Instale o backend com:\n"
                        "  pip install lazrs\n\n"
                        "Ou converta para .LAS primeiro."
                    ),
                }
            logger.error(
                "Erro desconhecido ao abrir arquivo",
                code="LASCHECK_FILE_OPEN_UNKNOWN",
                path=file_path,
                error=error_msg,
            )
            raise

        n_total = len(las.points)

        # Ordem dos checks + mapeamento
        check_order = [
            "point_count", "bbox", "rgb", "classification",
            "zero_coords", "duplicates", "density", "intensity",
        ]
        check_methods = {
            "point_count": self._check_point_count,
            "bbox": self._check_bbox,
            "rgb": self._check_rgb,
            "classification": self._check_classification,
            "zero_coords": self._check_zero_coords,
            "duplicates": self._check_duplicates,
            "density": self._check_density,
            "intensity": self._check_intensity,
        }

        results: dict[str, dict] = {}
        n_checks = len(check_order)
        enabled_count = 0

        logger.info(
            "Iniciando execucao dos checks",
            code="LASCHECK_CHECKS_START",
            total_checks=n_checks,
            enabled_checks=list(checks_enabled.keys()),
        )

        for idx, check_name in enumerate(check_order):
            enabled = checks_enabled.get(check_name, True)
            if not enabled:
                logger.debug(
                    f"Check '{check_name}' pulado (desabilitado)",
                    code="LASCHECK_CHECK_SKIPPED",
                    check=check_name,
                )
                results[check_name] = {
                    "status": "skipped",
                    "message": "Check desabilitado pelo usuário",
                    "detail": "",
                    "suggestion": "",
                }
                continue

            enabled_count += 1
            progress = (idx / n_checks) * 100.0
            signals.progress_update.emit(progress)

            display = self._CHECK_NAMES.get(check_name, check_name)
            signals.hud_update.emit({
                "message": f"Verificando: {display}...",
                "progress": progress,
            })

            method = check_methods[check_name]
            try:
                result = method(las, n_total)
                results[check_name] = result
                logger.info(
                    f"Check '{display}' concluido -> {result['status']}",
                    code="LASCHECK_CHECK_DONE",
                    check=check_name,
                    status=result["status"],
                    detail=result.get("detail", ""),
                )
            except Exception as e:
                logger.error(
                    f"Erro ao executar check '{display}'",
                    code="LASCHECK_CHECK_EXEC_ERR",
                    check=check_name,
                    error=str(e),
                    path=file_path,
                )
                results[check_name] = {
                    "status": "fail",
                    "message": f"Erro na verificacao: {str(e)}",
                    "detail": str(e),
                    "suggestion": "Verifique a integridade do arquivo.",
                }

        # Consolida estatísticas
        pass_count = sum(1 for r in results.values() if r.get("status") == "pass")
        warn_count = sum(1 for r in results.values() if r.get("status") == "warning")
        fail_count = sum(1 for r in results.values() if r.get("status") == "fail")

        signals.progress_update.emit(100.0)

        logger.info(
            "Checks concluidos",
            code="LASCHECK_DONE",
            pass_count=pass_count,
            warn_count=warn_count,
            fail_count=fail_count,
            enabled_count=enabled_count,
        )
        signals.console_message.emit(
            f"[LasCheck] Checks finalizados: "
            f"{pass_count} ✅ {warn_count} ⚠️ {fail_count} ❌ ({enabled_count} checks)"
        )

        return {
            "check_results": results,
            "summary": {
                "pass": pass_count,
                "warning": warn_count,
                "fail": fail_count,
                "total": enabled_count,
            },
        }

    def on_success(self, context: ExecutionContext, result: Any) -> None:
        """Mescla os resultados no context."""
        if isinstance(result, dict):
            for key, value in result.items():
                context.set(key, value)

    # ══════════════════════════════════════════════════════════════════
    # Checks individuais
    # ══════════════════════════════════════════════════════════════════

    @staticmethod
    def _check_point_count(las: laspy.LasData, n_total: int) -> dict:
        if n_total == 0:
            return {
                "status": "fail",
                "message": "Nenhum ponto encontrado",
                "detail": "0",
                "suggestion": "Verifique se o arquivo contém dados válidos.",
            }
        elif n_total < 1000:
            return {
                "status": "warning",
                "message": f"Apenas {n_total:,} pontos (nuvem pequena)",
                "detail": str(n_total),
                "suggestion": "Considere unir com outras nuvens para melhor cobertura.",
            }
        return {
            "status": "pass",
            "message": f"{n_total:,} pontos",
            "detail": str(n_total),
            "suggestion": "",
        }

    @staticmethod
    def _check_bbox(las: laspy.LasData, n_total: int) -> dict:
        x, y, z = las.x, las.y, las.z
        x_min, x_max = float(np.min(x)), float(np.max(x))
        y_min, y_max = float(np.min(y)), float(np.max(y))
        z_min, z_max = float(np.min(z)), float(np.max(z))

        issues = []
        if x_min >= x_max:
            issues.append("X")
        if y_min >= y_max:
            issues.append("Y")
        if z_min >= z_max:
            issues.append("Z")

        if issues:
            return {
                "status": "fail",
                "message": f"BBox inválida nos eixos: {', '.join(issues)}",
                "detail": f"X[{x_min:.1f}, {x_max:.1f}] Y[{y_min:.1f}, {y_max:.1f}] Z[{z_min:.1f}, {z_max:.1f}]",
                "suggestion": "Verifique o sistema de coordenadas da nuvem.",
            }

        return {
            "status": "pass",
            "message": f"X[{x_min:.1f}, {x_max:.1f}] Y[{y_min:.1f}, {y_max:.1f}] Z[{z_min:.1f}, {z_max:.1f}]",
            "detail": f"{x_min:.1f} {x_max:.1f} {y_min:.1f} {y_max:.1f} {z_min:.1f} {z_max:.1f}",
            "suggestion": "",
        }

    @staticmethod
    def _check_rgb(las: laspy.LasData, n_total: int) -> dict:
        has = (
            hasattr(las, "red")
            and hasattr(las, "green")
            and hasattr(las, "blue")
        )
        if not has:
            return {
                "status": "warning",
                "message": "LAS não possui bandas RGB",
                "detail": "",
                "suggestion": "Se precisar de RGB, obtenha dados com câmera fotogramétrica.",
            }
        return {
            "status": "pass",
            "message": "RGB presente",
            "detail": "",
            "suggestion": "",
        }

    @staticmethod
    def _check_classification(las: laspy.LasData, n_total: int) -> dict:
        if not hasattr(las, "classification"):
            return {
                "status": "warning",
                "message": "Sem campo de classificação",
                "detail": "",
                "suggestion": "Execute um classificador (ex: ground, vegetation) antes de usar.",
            }
        classes = np.unique(las.classification)
        invalid = classes[(classes < 0) | (classes > 255)]
        if len(invalid) > 0:
            return {
                "status": "fail",
                "message": f"Códigos inválidos: {invalid.tolist()}",
                "detail": str(invalid.tolist()),
                "suggestion": "Reclassifique a nuvem com software especializado.",
            }
        valid_classes = sorted(classes[classes > 0].tolist())
        return {
            "status": "pass",
            "message": f"Códigos válidos: {valid_classes}",
            "detail": str(valid_classes),
            "suggestion": "",
        }

    @staticmethod
    def _check_zero_coords(las: laspy.LasData, n_total: int) -> dict:
        mask_zero = (las.x == 0) & (las.y == 0) & (las.z == 0)
        n_zero = int(np.sum(mask_zero))
        pct = (n_zero / n_total * 100) if n_total > 0 else 0

        if pct >= 1.0:
            return {
                "status": "fail",
                "message": f"{n_zero:,} pontos ({(pct):.3f}%) com X=Y=Z=0",
                "detail": f"{n_zero} ({pct:.3f}%)",
                "suggestion": "Remova pontos com coordenadas zero ou verifique o SRS.",
            }
        elif pct > 0:
            return {
                "status": "warning",
                "message": f"{n_zero:,} pontos ({(pct):.3f}%) com X=Y=Z=0",
                "detail": f"{n_zero} ({pct:.3f}%)",
                "suggestion": "Considere filtrar pontos inválidos.",
            }
        return {
            "status": "pass",
            "message": "Nenhum ponto com coordenadas zero",
            "detail": "0",
            "suggestion": "",
        }

    @staticmethod
    def _check_duplicates(las: laspy.LasData, n_total: int) -> dict:
        sample = min(n_total, 50000)
        if n_total > sample:
            rng = np.random.default_rng()
            idx = rng.choice(n_total, sample, replace=False)
        else:
            idx = slice(None)

        coords = np.column_stack((las.x[idx], las.y[idx]))
        _, counts = np.unique(coords, axis=0, return_counts=True)
        dup = int(np.sum(counts > 1))
        pct = (dup / sample * 100) if sample > 0 else 0

        if pct > 0.1:
            return {
                "status": "fail",
                "message": f"{dup:,} duplicatas em amostra ({pct:.3f}%)",
                "detail": f"{dup} ({pct:.3f}%)",
                "suggestion": "Execute filtro de duplicatas antes de processar.",
            }
        elif dup > 0:
            return {
                "status": "warning",
                "message": f"{dup:,} duplicatas em amostra ({pct:.3f}%)",
                "detail": f"{dup} ({pct:.3f}%)",
                "suggestion": "",
            }
        return {
            "status": "pass",
            "message": "Nenhuma duplicata detectada",
            "detail": "0",
            "suggestion": "",
        }

    @staticmethod
    def _check_density(las: laspy.LasData, n_total: int) -> dict:
        x_min, x_max = float(np.min(las.x)), float(np.max(las.x))
        y_min, y_max = float(np.min(las.y)), float(np.max(las.y))
        area = (x_max - x_min) * (y_max - y_min)

        if area <= 0:
            return {
                "status": "warning",
                "message": "Área planar zero (pontos coplanares?)",
                "detail": "",
                "suggestion": "Verifique se os pontos têm extensão horizontal.",
            }

        density = n_total / area
        return {
            "status": "pass",
            "message": f"Densidade: {density:.2f} pts/m²",
            "detail": f"{density:.2f}",
            "suggestion": "",
        }

    @staticmethod
    def _check_intensity(las: laspy.LasData, n_total: int) -> dict:
        if not hasattr(las, "intensity"):
            return {
                "status": "warning",
                "message": "Sem campo de intensidade",
                "detail": "",
                "suggestion": "Dados sem intensidade têm menos informação espectral.",
            }
        i_min = int(np.min(las.intensity))
        i_max = int(np.max(las.intensity))

        if i_min < 0 or i_max > 65535:
            return {
                "status": "fail",
                "message": f"Intensidade fora do range: [{i_min}, {i_max}]",
                "detail": f"[{i_min}, {i_max}]",
                "suggestion": "Verifique se os valores de intensidade são consistentes.",
            }
        return {
            "status": "pass",
            "message": f"Range [{i_min}, {i_max}] (válido)",
            "detail": f"[{i_min}, {i_max}]",
            "suggestion": "",
        }