# -*- coding: utf-8 -*-
"""
IdwInterpolatorTask — Task IDW com RAM Governor
=================================================
Melhorias:
- estimated_ram: n_pontos * 32 bytes
- recommended_tile_size() via governor
- _check_during_execution() entre estagios
- _log_memory_status() em cada estagio
"""

from __future__ import annotations

import glob
import json
import os as _os
import shutil
import tempfile

import numpy as np
from joblib import Parallel, delayed

from core.enum.ToolKey import ToolKey
from core.governor.ResourceGovernor import ResourceGovernor
from core.manager.SignalManager import SignalManager
from core.papeline.BaseTask import BaseTask
from utils.BaseUtil import BaseUtil
from utils.ExplorerUtils import ExplorerUtils
from utils.raster.InterpolatorUtils import InterpolatorUtils
from utils.raster.RasterLayerProcessing import RasterLayerProcessing


class IdwInterpolatorTask(BaseTask):
    """Task IDW com protecao de RAM via ResourceGovernor."""

    BYTES_PER_POINT: int = 32

    def __init__(self, context: dict, governor: ResourceGovernor | None = None):
        super().__init__(
            description=f"IDW: {_os.path.basename(context.get('file_path', ''))}",
            governor=governor,
        )
        self._ctx = context
        self._tool_key = context.get("tool_key", ToolKey.UNTRACEABLE.value)
        self._logger = BaseUtil._get_logger(self._tool_key, "IdwInterpolatorTask")
        self._temp_dir: str | None = None
        self._signals = SignalManager.instance()
        self._n_pontos: int = 0
        self._log_memory_status("init")

    @property
    def estimated_ram(self) -> int:
        """RAM estimada: n_pontos * 32 bytes."""
        n = max(self._n_pontos, self._ctx.get("pontos_por_tile", 10_000_000))
        return n * self.BYTES_PER_POINT

    def _log_memory_status(self, stage: str) -> None:
        """Loga status de RAM via governor."""
        if self._governor is not None:
            snap = self._governor.snapshot(estimated_ram=self.estimated_ram)
            self._logger.debug(
                f"[RAM] {stage}: "
                f"Sys {snap.get('used_system_human', '?')}/"
                f"{snap.get('total_human', '?')} | "
                f"Proc {snap.get('process_human', '?')} | "
                f"Headroom {snap.get('headroom_human', '?')} | "
                f"Pressao {snap.get('memory_pressure', 0):.2f}",
                code="IDW_TASK_RAM", stage=stage,
            )

    def _ajustar_tile_size(self, pontos_por_tile: int) -> int:
        """Ajusta pontos_por_tile via governor com fator paralelo."""
        if self._governor is None:
            return pontos_por_tile
        import os
        n_cpus = os.cpu_count() or 4
        ram_por_tile = max(self._n_pontos, 1) * self.BYTES_PER_POINT
        ram_paralela = ram_por_tile * min(n_cpus, 8)
        return self._governor.recommended_tile_size(
            max_tile_points=pontos_por_tile,
            estimated_ram=ram_paralela,
        )

    def _limpar_temp(self):
        if self._temp_dir and _os.path.exists(self._temp_dir):
            try:
                shutil.rmtree(self._temp_dir, ignore_errors=True)
            except Exception as e:
                self._logger.warning("Erro temp", code="IDW_TASK_TEMP_ERR", error=str(e))

    def _run(self) -> bool:
        """Pipeline IDW completo com verificacoes de RAM entre estagios."""
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
        self._log_memory_status("inicio")

        # --- Estagio 1: Leitura do LAS ---
        self._signals.hud_update.emit({"message": "Lendo LAS...", "progress": 2.0})
        self._signals.progress_update.emit(2.0)

        if not self._check_during_execution():
            self._logger.error("RAM insuficiente - leitura LAS", code="IDW_TASK_OOM_STAGE1")
            return False

        from utils.LasUtil import LasUtil
        arrays = LasUtil.extract_point_arrays(file_path, target, tool_key=self._tool_key)
        n_pontos = arrays["n_points"]
        self._n_pontos = n_pontos
        x_pts, y_pts = arrays["x"], arrays["y"]
        r_pts = arrays["red"]
        g_pts = arrays["green"]
        b_pts = arrays["blue"]
        z_pts = arrays["z"]

        self._logger.info("LAS lido: %d pontos", n_pontos, code="IDW_TASK_LAS_READ")
        self._log_memory_status("apos_leitura")

        if not self._check_during_execution():
            return False

        # --- Estagio 2: Calculo do Grid Global ---
        self._signals.hud_update.emit({"message": "Calculando grid...", "progress": 5.0})
        self._signals.progress_update.emit(5.0)

        min_x_g, max_x_g = float(np.min(x_pts)), float(np.max(x_pts))
        min_y_g, max_y_g = float(np.min(y_pts)), float(np.max(y_pts))
        width = int(np.ceil((max_x_g - min_x_g) / resol_m))
        height = int(np.ceil((max_y_g - min_y_g) / resol_m))

        from rasterio.transform import from_origin
        transform = from_origin(min_x_g, max_y_g, resol_m, resol_m)
        self._logger.info("Grid: %dx%d px", width, height, code="IDW_TASK_GRID")

        if not self._check_during_execution():
            return False

        # --- Estagio 3: Divisao em Tiles (com governor) ---
        self._signals.hud_update.emit({"message": "Dividindo tiles...", "progress": 8.0})
        self._signals.progress_update.emit(8.0)

        tile_size_ajustado = self._ajustar_tile_size(pontos_por_tile)
        if tile_size_ajustado != pontos_por_tile:
            self._logger.info("Tile ajustado: %d -> %d (por RAM)",
                              pontos_por_tile, tile_size_ajustado, code="IDW_TASK_TILE_ADJ")
            pontos_por_tile = tile_size_ajustado

        tiles = InterpolatorUtils.calcular_tiles_por_densidade(
            x_pts, y_pts, min_x_g, max_x_g, min_y_g, max_y_g,
            resol_m, pontos_por_tile, tool_key=self._tool_key,
        )
        total_tiles = len(tiles)
        self._log_memory_status("apos_tiles")

        if not self._check_during_execution():
            return False

        # --- Pasta temporaria ---
        config_dir = ExplorerUtils.get_plugin_config_dir("idw_interpolator")
        self._temp_dir = tempfile.mkdtemp(dir=config_dir, prefix="tiles_")
        for banda in ("R", "G", "B", "Z"):
            _os.makedirs(_os.path.join(self._temp_dir, banda), exist_ok=True)

        grid_bounds = (min_x_g, max_x_g, min_y_g, max_y_g)

        # --- Estagio 4: IDW Paralelo ---
        self._signals.hud_update.emit({
            "message": "Interpolando tiles (IDW)...",
            "stages": [total_tiles * 5, total_tiles],
        })
        self._signals.progress_update.emit(10.0)

        if not self._check_during_execution():
            self._limpar_temp()
            return False

        dir_r = _os.path.join(self._temp_dir, "R")
        dir_g = _os.path.join(self._temp_dir, "G")
        dir_b = _os.path.join(self._temp_dir, "B")
        dir_z = _os.path.join(self._temp_dir, "Z")

        tile_jobs = []
        for idx, (x0, x1, y0, y1, t_row, t_col) in enumerate(tiles):
            tag = f"{t_row:04d}_{t_col:04d}"
            pr = _os.path.join(dir_r, f"tile_{tag}.tif") if target.get("r", False) else ""
            pg = _os.path.join(dir_g, f"tile_{tag}.tif") if target.get("g", False) else ""
            pb = _os.path.join(dir_b, f"tile_{tag}.tif") if target.get("b", False) else ""
            pz = _os.path.join(dir_z, f"tile_{tag}.tif") if target.get("z", False) else None
            tile_jobs.append((idx, tag, (x0, x1, y0, y1), pr, pg, pb, pz))

        results = Parallel(n_jobs=-1, verbose=0)(
            delayed(InterpolatorUtils.idw_tile_para_disco)(
                idx, total_tiles, tag, tb, grid_bounds, resol_m,
                x_pts, y_pts, r_pts, g_pts, b_pts, z_pts,
                k, power, raio_max, overlap, crs_str,
                pr, pg, pb, pz, self._tool_key,
            )
            for idx, tag, tb, pr, pg, pb, pz in tile_jobs
        )

        n_ok = sum(1 for r in results if r[6] == 'OK')
        n_pulado = sum(1 for r in results if r[6] == 'PULADO')
        self._logger.info("IDW OK: %d, Pulado: %d", n_ok, n_pulado, code="IDW_TASK_IDW_DONE")
        self._log_memory_status("apos_idw")

        if self.is_cancelled or not self._check_during_execution():
            self._limpar_temp()
            return False

        # --- Estagio 5: Merge ---
        self._signals.hud_update.emit({"message": "Mesclando bandas...", "progress": 80.0})
        self._signals.progress_update.emit(80.0)

        output_dir = _os.path.dirname(output_path)
        _os.makedirs(output_dir, exist_ok=True)

        band_files = []
        merge_jobs = []

        def _add_merge(nome, src_dir, dtype):
            paths = sorted(glob.glob(_os.path.join(src_dir, "tile_*.tif")))
            if not paths:
                return
            out = _os.path.join(output_dir, f"banda_{nome}.tif")
            merge_jobs.append((nome, paths, out, dtype))
            band_files.append(out)

        if target.get("r"): _add_merge("R", dir_r, np.uint8)
        if target.get("g"): _add_merge("G", dir_g, np.uint8)
        if target.get("b"): _add_merge("B", dir_b, np.uint8)
        if target.get("z"): _add_merge("Z", dir_z, np.float32)

        Parallel(n_jobs=-1, verbose=0)(
            delayed(InterpolatorUtils.mesclar_banda)(
                nome, paths, height, width, transform, crs_str,
                out_path, dtype, self._tool_key,
            )
            for nome, paths, out_path, dtype in merge_jobs
        )

        if self.is_cancelled or not self._check_during_execution():
            self._limpar_temp()
            return False

        # --- Estagio 6: Montagem ---
        self._signals.hud_update.emit({"message": "Montando saida...", "progress": 90.0})
        self._signals.progress_update.emit(90.0)

        has_rgb = target.get("r") and target.get("g") and target.get("b")
        has_z = target.get("z", False)
        final_outputs = []

        if separate:
            final_outputs = band_files[:]
        elif has_rgb and has_z:
            RasterLayerProcessing.compose_multiband_raster(
                band_files[:3] + [band_files[3]], output_path, tool_key=self._tool_key,
            )
            final_outputs.append(output_path)
        elif has_rgb:
            RasterLayerProcessing.compose_multiband_raster(
                band_files[:3], output_path, tool_key=self._tool_key,
            )
            final_outputs.append(output_path)
        elif has_z:
            shutil.copy2(band_files[0], output_path)
            final_outputs.append(output_path)

        # --- Estagio 7: Metadados ---
        metadata = {
            "arquivo_las": file_path, "output_path": output_path,
            "parametros": {
                "resolucao_m": resol_m, "resolucao_cm": round(resol_m * 100, 2),
                "idw_k": k, "idw_power": power,
                "idw_raio_max_m": raio_max, "idw_overlap_m": overlap,
                "pontos_por_tile": pontos_por_tile,
                "crs": crs_str, "separate_bands": separate, "target_bands": target,
            },
            "grid": {"width_px": width, "height_px": height,
                     "bounds": {"x_min": min_x_g, "x_max": max_x_g,
                                "y_min": min_y_g, "y_max": max_y_g}},
            "nuvem": {"n_pontos": n_pontos},
            "tiles": {"total": total_tiles, "ok": n_ok, "pulado": n_pulado},
            "arquivos_gerados": final_outputs,
        }

        meta_path = _os.path.join(output_dir, "metadata.json")
        with open(meta_path, "w", encoding="utf-8") as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)

        self.result = metadata
        self._logger.info("Pipeline IDW concluido", code="IDW_TASK_DONE")
        self._log_memory_status("final")

        self._limpar_temp()
        self._signals.hud_update.emit({"message": "Concluido!", "progress": 100.0})
        self._signals.progress_update.emit(100.0)
        return True
