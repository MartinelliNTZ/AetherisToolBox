# -*- coding: utf-8 -*-
"""
IdwInterpolatorTask — Task que executa a interpolação IDW em background
=========================================================================
Executa os Estágios 4-7 do pipeline IDW:
  - Estágio 4: Interpolação IDW paralela (joblib)
  - Estágio 5: Mescla tiles em bandas completas
  - Estágio 6: Montagem da saída (mosaico ou separado)
  - Estágio 7: Metadados JSON
"""

from __future__ import annotations

import glob
import json
import os
import shutil
import tempfile
import time

import numpy as np
from joblib import Parallel, delayed

from core.enum.ToolKey import ToolKey
from core.manager.SignalManager import SignalManager
from core.papeline.BaseTask import BaseTask
from utils.BaseUtil import BaseUtil
from utils.ExplorerUtils import ExplorerUtils
from utils.raster.InterpolatorUtils import InterpolatorUtils
from utils.raster.RasterLayerProcessing import RasterLayerProcessing


class IdwInterpolatorTask(BaseTask):
    """
    Task que executa a interpolação IDW completa em background.

    Parâmetros (context dict):
        file_path           — caminho do LAS
        output_path         — caminho do raster de saída
        target_bands        — {"r": bool, "g": bool, "b": bool, "z": bool}
        separate_bands      — bool
        resol_m             — resolução em metros
        idw_k, idw_power, idw_raio_max, idw_overlap
        pontos_por_tile
        crs_str
        tool_key
    """

    def __init__(self, context: dict):
        super().__init__(
            description=f"IDW Interpolation: {os.path.basename(context.get('file_path', ''))}"
        )
        self._ctx = context
        self._tool_key = context.get("tool_key", ToolKey.UNTRACEABLE.value)
        self._logger = BaseUtil._get_logger(self._tool_key, "IdwInterpolatorTask")
        self._temp_dir: str | None = None
        self._signals = SignalManager.instance()

    def _run(self) -> bool:
        """Executa o pipeline IDW completo."""
        ctx = self._ctx
        file_path = ctx["file_path"]
        output_path = ctx["output_path"]
        target = ctx["target_bands"]
        separate = ctx.get("separate_bands", False)
        resol_m = ctx["resol_m"]
        k = ctx.get("idw_k", 5)
        power = ctx.get("idw_power", 2.0)
        raio_max = ctx.get("idw_raio_max", 0.5)
        overlap = ctx.get("idw_overlap", 3.0)
        pontos_por_tile = ctx.get("pontos_por_tile", 10_000_000)
        crs_str = ctx.get("crs_str", "EPSG:31982")

        self._logger.info("Iniciando pipeline IDW", code="IDW_TASK_START", path=file_path)

        # ── Estágio 1: Leitura do LAS ────────────────────────────────
        self._signals.hud_update.emit({"message": "Lendo LAS...", "progress": 2.0})
        self._signals.progress_update.emit(2.0)

        from utils.LasUtil import LasUtil
        arrays = LasUtil.extract_point_arrays(file_path, target, tool_key=self._tool_key)
        n_pontos = arrays["n_points"]
        x_pts, y_pts = arrays["x"], arrays["y"]
        r_pts = arrays["red"]
        g_pts = arrays["green"]
        b_pts = arrays["blue"]
        z_pts = arrays["z"]

        self._logger.info(
            "LAS lido com sucesso",
            code="IDW_TASK_LAS_READ",
            n_pontos=n_pontos,
        )

        # ── Estágio 2: Cálculo do Grid Global ────────────────────────
        self._signals.hud_update.emit({"message": "Calculando grid...", "progress": 5.0})
        self._signals.progress_update.emit(5.0)

        min_x_g, max_x_g = float(np.min(x_pts)), float(np.max(x_pts))
        min_y_g, max_y_g = float(np.min(y_pts)), float(np.max(y_pts))

        width = int(np.ceil((max_x_g - min_x_g) / resol_m))
        height = int(np.ceil((max_y_g - min_y_g) / resol_m))

        from rasterio.transform import from_origin
        transform = from_origin(min_x_g, max_y_g, resol_m, resol_m)

        self._logger.info(
            "Grid calculado",
            code="IDW_TASK_GRID",
            width=width,
            height=height,
            resol_cm=resol_m * 100,
        )

        # ── Estágio 3: Divisão em Tiles ──────────────────────────────
        self._signals.hud_update.emit({"message": "Dividindo tiles...", "progress": 8.0})
        self._signals.progress_update.emit(8.0)

        tiles = InterpolatorUtils.calcular_tiles_por_densidade(
            x_pts, y_pts,
            min_x_g, max_x_g, min_y_g, max_y_g,
            resol_m, pontos_por_tile,
            tool_key=self._tool_key,
        )
        total_tiles = len(tiles)

        # ── Pasta temporária para tiles ──────────────────────────────
        config_dir = ExplorerUtils.get_plugin_config_dir("idw_interpolator")
        self._temp_dir = tempfile.mkdtemp(dir=config_dir, prefix="tiles_")
        tiles_r = os.path.join(self._temp_dir, "R")
        tiles_g = os.path.join(self._temp_dir, "G")
        tiles_b = os.path.join(self._temp_dir, "B")
        tiles_z = os.path.join(self._temp_dir, "Z")
        os.makedirs(tiles_r, exist_ok=True)
        os.makedirs(tiles_g, exist_ok=True)
        os.makedirs(tiles_b, exist_ok=True)
        os.makedirs(tiles_z, exist_ok=True)

        grid_bounds = (min_x_g, max_x_g, min_y_g, max_y_g)

        # ── Estágio 4: Interpolação IDW Paralela ─────────────────────
        self._signals.hud_update.emit({
            "message": "Interpolando tiles (IDW)...",
            "stages": [total_tiles * 5, total_tiles],
        })
        self._signals.progress_update.emit(10.0)

        tile_jobs = []
        for idx, (x0, x1, y0, y1, t_row, t_col) in enumerate(tiles):
            tag = f"{t_row:04d}_{t_col:04d}"
            pr = os.path.join(tiles_r, f"tile_{tag}.tif") if target.get("r", False) else ""
            pg = os.path.join(tiles_g, f"tile_{tag}.tif") if target.get("g", False) else ""
            pb = os.path.join(tiles_b, f"tile_{tag}.tif") if target.get("b", False) else ""
            pz = os.path.join(tiles_z, f"tile_{tag}.tif") if target.get("z", False) else None
            tile_jobs.append((idx, tag, (x0, x1, y0, y1), pr, pg, pb, pz))

        results = Parallel(n_jobs=-1, verbose=0)(
            delayed(InterpolatorUtils.idw_tile_para_disco)(
                idx, total_tiles, tag, tb, grid_bounds, resol_m,
                x_pts, y_pts, r_pts, g_pts, b_pts, z_pts,
                k, power, raio_max, overlap, crs_str,
                pr, pg, pb, pz,
                self._tool_key,
            )
            for idx, tag, tb, pr, pg, pb, pz in tile_jobs
        )

        n_ok = sum(1 for r in results if r[6] == 'OK')
        n_pulado = sum(1 for r in results if r[6] == 'PULADO')
        self._logger.info(
            "IDW concluido",
            code="IDW_TASK_IDW_DONE",
            ok=n_ok,
            pulado=n_pulado,
        )

        if self.is_cancelled:
            self._limpar_temp()
            return False

        # ── Estágio 5: Mescla Tiles → Bandas Completas ───────────────
        self._signals.hud_update.emit({"message": "Mesclando bandas...", "progress": 80.0})
        self._signals.progress_update.emit(80.0)

        output_dir = os.path.dirname(output_path)
        os.makedirs(output_dir, exist_ok=True)

        band_files = []
        merge_jobs = []

        if target.get("r", False):
            paths_r = sorted(glob.glob(os.path.join(tiles_r, "tile_*.tif")))
            out_r = os.path.join(output_dir, "banda_R.tif")
            merge_jobs.append(("R", paths_r, out_r, np.uint8))
            band_files.append(out_r)

        if target.get("g", False):
            paths_g = sorted(glob.glob(os.path.join(tiles_g, "tile_*.tif")))
            out_g = os.path.join(output_dir, "banda_G.tif")
            merge_jobs.append(("G", paths_g, out_g, np.uint8))
            band_files.append(out_g)

        if target.get("b", False):
            paths_b = sorted(glob.glob(os.path.join(tiles_b, "tile_*.tif")))
            out_b = os.path.join(output_dir, "banda_B.tif")
            merge_jobs.append(("B", paths_b, out_b, np.uint8))
            band_files.append(out_b)

        if target.get("z", False):
            paths_z = sorted(glob.glob(os.path.join(tiles_z, "tile_*.tif")))
            out_z = os.path.join(output_dir, "banda_Z.tif")
            merge_jobs.append(("Z", paths_z, out_z, np.float32))
            band_files.append(out_z)

        # Mescla em paralelo (bandas independentes)
        Parallel(n_jobs=-1, verbose=0)(
            delayed(InterpolatorUtils.mesclar_banda)(
                nome, paths, height, width, transform, crs_str,
                out_path, dtype, self._tool_key,
            )
            for nome, paths, out_path, dtype in merge_jobs
        )

        if self.is_cancelled:
            self._limpar_temp()
            return False

        # ── Estágio 6: Montagem da Saída ─────────────────────────────
        self._signals.hud_update.emit({"message": "Montando saída...", "progress": 90.0})
        self._signals.progress_update.emit(90.0)

        has_rgb = target.get("r", False) and target.get("g", False) and target.get("b", False)
        has_z = target.get("z", False)
        final_outputs = []

        if separate:
            # Modo separado: cada banda já está em banda_X.tif
            for bf in band_files:
                final_outputs.append(bf)
            self._logger.info("Saida em modo separado", code="IDW_TASK_SEPARATE")
        else:
            # Modo mosaico
            if has_rgb and not has_z:
                # Só RGB → mosaico_rgb.tif
                rgb_files = band_files[:3]
                RasterLayerProcessing.compose_multiband_raster(
                    rgb_files, output_path, tool_key=self._tool_key,
                )
                final_outputs.append(output_path)
            elif has_z and not has_rgb:
                # Só Z → copia banda_Z.tif para output_path
                shutil.copy2(band_files[0], output_path)
                final_outputs.append(output_path)
            elif has_rgb and has_z:
                # RGB + Z → 4 bandas
                rgb_files = band_files[:3]
                z_file = band_files[3]
                RasterLayerProcessing.compose_multiband_raster(
                    rgb_files + [z_file], output_path, tool_key=self._tool_key,
                )
                final_outputs.append(output_path)

        # ── Estágio 7: Metadados JSON ────────────────────────────────
        metadata = {
            "arquivo_las": file_path,
            "output_path": output_path,
            "parametros": {
                "resolucao_m": resol_m,
                "resolucao_cm": round(resol_m * 100, 2),
                "idw_k": k,
                "idw_power": power,
                "idw_raio_max_m": raio_max,
                "idw_overlap_m": overlap,
                "pontos_por_tile": pontos_por_tile,
                "crs": crs_str,
                "separate_bands": separate,
                "target_bands": target,
            },
            "grid": {
                "width_px": width,
                "height_px": height,
                "bounds": {
                    "x_min": min_x_g, "x_max": max_x_g,
                    "y_min": min_y_g, "y_max": max_y_g,
                },
            },
            "nuvem": {
                "n_pontos": n_pontos,
            },
            "tiles": {
                "total": total_tiles,
                "ok": n_ok,
                "pulado": n_pulado,
            },
            "arquivos_gerados": final_outputs,
        }

        meta_path = os.path.join(output_dir, "metadata.json")
        with open(meta_path, "w", encoding="utf-8") as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)

        self.result = metadata
        self._logger.info("Pipeline IDW concluido", code="IDW_TASK_DONE")

        # Limpa temp
        self._limpar_temp()

        self._signals.hud_update.emit({"message": "Concluído!", "progress": 100.0})
        self._signals.progress_update.emit(100.0)
        return True

    def _limpar_temp(self):
        """Remove pasta temporária de tiles."""
        if self._temp_dir and os.path.exists(self._temp_dir):
            try:
                shutil.rmtree(self._temp_dir, ignore_errors=True)
                self._logger.debug("Temp limpo", code="IDW_TASK_TEMP_CLEAN")
            except Exception as e:
                self._logger.warning(
                    "Erro ao limpar temp",
                    code="IDW_TASK_TEMP_ERR",
                    error=str(e),
                )