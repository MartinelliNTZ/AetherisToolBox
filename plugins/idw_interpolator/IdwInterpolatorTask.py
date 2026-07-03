# -*- coding: utf-8 -*-
"""
IdwInterpolatorTask — Task para interpolacao IDW de nuvens LAS/LAZ
====================================================================
Task que executa a interpolacao IDW em grid regular.

Utiliza InterpolatorUtils internamente.
"""

from __future__ import annotations

import glob
import json
import os as _os
import shutil
from typing import Optional

import numpy as np
from joblib import Parallel, delayed

from core.governor.CpuGovernor import CpuGovernor
from core.governor.ResourceGovernor import ResourceGovernor
from core.manager.SignalManager import SignalManager
from core.papeline.BaseTask import BaseTask
from utils.raster.InterpolatorUtils import InterpolatorUtils
from utils.raster.RasterLayerProcessing import RasterLayerProcessing


class IdwInterpolatorTask(BaseTask):
    """Task IDW com protecao de RAM via ResourceGovernor."""

    BYTES_PER_POINT: int = 32
    MAX_TILE_PIXELS: int = 10_000_000
    BYTES_PER_TILE_PIXEL: int = 64

    def __init__(
        self,
        file_path: str,
        output_path: str,
        target_bands: dict,
        merge_bands: bool = True,
        resol_m: float = 0.01,
        idw_k: int = 5,
        idw_power: float = 2.0,
        idw_raio_max: float = 0.5,
        idw_overlap: float = 3.0,
        pontos_por_tile: int = 10_000_000,
        crs_str: str = "EPSG:31982",
        eliminar_tiles: bool = True,
        governor: Optional[ResourceGovernor] = None,
    ):
        super().__init__(
            description=f"IDW: {_os.path.basename(file_path)}",
            governor=governor,
        )
        self._file_path = file_path
        self._output_path = output_path
        self._target_bands = target_bands
        self._merge_bands = merge_bands
        self._resol_m = resol_m
        self._idw_k = idw_k
        self._idw_power = idw_power
        self._idw_raio_max = idw_raio_max
        self._idw_overlap = idw_overlap
        self._pontos_por_tile = pontos_por_tile
        self._crs_str = crs_str
        self._eliminar_tiles = eliminar_tiles
        self._temp_dir: str | None = None
        self._n_pontos: int = 0

    @property
    def estimated_ram(self) -> int:
        """RAM estimada: n_pontos * 32 bytes."""
        n = max(self._n_pontos, self._pontos_por_tile)
        return n * self.BYTES_PER_POINT

    def _log_memory_status(self, stage: str, estimated_ram_extra: int = 0) -> None:
        """Loga status de RAM via governor."""
        if self._governor is not None:
            snap = self._governor.snapshot(estimated_ram=self.estimated_ram + estimated_ram_extra)
            self.get_logger().debug(
                f"[RAM] {stage}: "
                f"Sys {snap.get('used_system_human', '?')}/"
                f"{snap.get('total_human', '?')} | "
                f"Proc {snap.get('process_human', '?')} | "
                f"Headroom {snap.get('headroom_human', '?')} | "
                f"Pressao {snap.get('memory_pressure', 0):.2f}",
                code="IDW_TASK_RAM", stage=stage,
            )

    def _estimar_ram_por_tile(self, tile_pixels: int, n_bandas: int) -> int:
        """
        Estima RAM necessaria para processar UM tile via idw_tile_para_disco.
        Inclui meshgrid, query_pts, cKDTree dist/idx, pesos, arrays de banda.

        Args:
            tile_pixels: tile_h * tile_w (numero de pixels do tile)
            n_bandas: numero de bandas a interpolar (1-4)

        Returns:
            RAM estimada em bytes para um tile.
        """
        k = self._idw_k
        bytes_por_pixel = 8 + 8 + 16 + k * 8 + k * 8 + k * 8
        bytes_por_pixel += n_bandas * k * 8
        return tile_pixels * bytes_por_pixel

    def _check_pixel_ram(self, width: int, height: int, n_cpus: int, n_bandas: int) -> bool:
        """
        Verifica se ha RAM suficiente para processar tiles no grid.
        Calcula o tile pixel size minimo (MAX_TILE_PIXELS) e estima RAM
        total com paralelismo.

        Returns:
            True se ok, False se RAM insuficiente.
        """
        if self._governor is None:
            return True
        total_pixels = width * height
        n_tiles_min = max(1, (total_pixels + self.MAX_TILE_PIXELS - 1) // self.MAX_TILE_PIXELS)
        tile_pixels = (total_pixels + n_tiles_min - 1) // n_tiles_min
        ram_por_tile = self._estimar_ram_por_tile(tile_pixels, n_bandas)
        ram_paralela = ram_por_tile * min(n_cpus, 8)
        can, reason = self._governor.can_execute(estimated_ram=ram_paralela)
        if not can:
            self.get_logger().error(
                "RAM insuficiente para tiles no grid",
                code="IDW_TASK_OOM_PIXEL",
                width=width, height=height,
                tile_pixels=tile_pixels,
                ram_por_tile=ram_por_tile,
                ram_paralela=ram_paralela,
                reason=reason,
            )
            return False
        return True

    def _ajustar_tile_size(self, pontos_por_tile: int) -> int:
        """Ajusta pontos_por_tile via governor com fator paralelo."""
        if self._governor is None:
            return pontos_por_tile
        n_cpus = CpuGovernor.max_workers()
        ram_por_tile = max(self._n_pontos, 1) * self.BYTES_PER_POINT
        ram_paralela = ram_por_tile * min(n_cpus, 8)
        return self._governor.recommended_tile_size(
            max_tile_points=pontos_por_tile,
            estimated_ram=ram_paralela,
        )

    def _limpar_temp(self):
        """Remove as subpastas de tiles se eliminar_tiles estiver ativo."""
        if not self._temp_dir or not _os.path.isdir(self._temp_dir):
            return
        if not self._eliminar_tiles:
            self.get_logger().info(
                "Tiles mantidos (eliminar_tiles=desligado)",
                code="IDW_TASK_KEEP_TILES",
            )
            return
        for sub in ("r", "g", "b", "z"):
            subp = _os.path.join(self._temp_dir, sub)
            if _os.path.isdir(subp):
                try:
                    shutil.rmtree(subp, ignore_errors=True)
                    self.get_logger().debug(
                        f"Subpasta de tiles removida: {sub}",
                        code="IDW_TASK_TILE_CLEAN",
                        subfolder=sub,
                    )
                except Exception as e:
                    self.get_logger().warning(
                        f"Falha ao limpar subpasta {sub}",
                        code="IDW_TASK_TILE_CLEAN_ERR",
                        error=str(e),
                    )
        self.get_logger().info(
            f"Tiles temporarios removidos",
            code="IDW_TASK_TEMP_CLEAN_DONE",
            temp_dir=self._temp_dir,
        )

    def _run(self) -> bool:
        """Pipeline IDW completo com verificacoes de RAM entre estagios."""
        logger = self.get_logger()
        signals = SignalManager.instance()

        file_path = self._file_path
        output_path = self._output_path
        target = self._target_bands
        merge_bands = self._merge_bands
        resol_m = self._resol_m
        k = self._idw_k
        power = self._idw_power
        raio_max = self._idw_raio_max
        overlap = self._idw_overlap
        pontos_por_tile = self._pontos_por_tile
        crs_str = self._crs_str

        logger.info("Iniciando pipeline IDW", code="IDW_TASK_START", path=file_path)
        self._log_memory_status("inicio")

        # --- Estagio 1: Leitura do LAS ---
        signals.hud_update.emit({"message": "Lendo LAS..."})
        signals.progress_update.emit(0.0)

        if not self._check_during_execution():
            logger.error("RAM insuficiente - leitura LAS", code="IDW_TASK_OOM_STAGE1")
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

        logger.info(f"LAS lido: {n_pontos} pontos", code="IDW_TASK_LAS_READ")
        self._log_memory_status("apos_leitura")

        signals.hud_update.emit({"message": "Calculando grid..."})

        if not self._check_during_execution():
            return False

        # --- Estagio 2: Calculo do Grid Global ---
        signals.hud_update.emit({"message": "Calculando grid..."})

        min_x_g, max_x_g = float(np.min(x_pts)), float(np.max(x_pts))
        min_y_g, max_y_g = float(np.min(y_pts)), float(np.max(y_pts))
        width = int(np.ceil((max_x_g - min_x_g) / resol_m))
        height = int(np.ceil((max_y_g - min_y_g) / resol_m))

        from rasterio.transform import from_origin
        transform = from_origin(min_x_g, max_y_g, resol_m, resol_m)
        logger.info(f"Grid: {width}x{height} px", code="IDW_TASK_GRID")

        signals.hud_update.emit({"message": "Dividindo tiles..."})

        if not self._check_during_execution():
            return False

        # --- Verificacao de RAM por pixel do grid (anti-OOM meshgrid) ---
        n_cpus = CpuGovernor.max_workers()
        n_bandas = sum(1 for b in ('r', 'g', 'b', 'z') if target.get(b, False))
        n_bandas = max(1, n_bandas)
        if not self._check_pixel_ram(width, height, n_cpus, n_bandas):
            logger.error("RAM insuficiente para processar grid", code="IDW_TASK_OOM_GRID")
            return False

        # --- Estagio 3: Divisao em Tiles (com governor) ---
        signals.hud_update.emit({"message": "Dividindo tiles..."})

        tile_size_ajustado = self._ajustar_tile_size(pontos_por_tile)
        if tile_size_ajustado != pontos_por_tile:
            logger.info(f"Tile ajustado: {pontos_por_tile} -> {tile_size_ajustado} (por RAM)",
                        code="IDW_TASK_TILE_ADJ")
            pontos_por_tile = tile_size_ajustado

        tiles = InterpolatorUtils.calcular_tiles_por_densidade(
            x_pts, y_pts, min_x_g, max_x_g, min_y_g, max_y_g,
            resol_m, pontos_por_tile, tool_key=self._tool_key,
            max_tile_pixels=self.MAX_TILE_PIXELS,
        )
        total_tiles = len(tiles)
        self._log_memory_status("apos_tiles")

        if not self._check_during_execution():
            return False

        # --- Pasta de saida com subpastas por banda (MINUSCULAS) ---
        basename_out = _os.path.splitext(_os.path.basename(output_path))[0]
        output_dir = _os.path.dirname(output_path)
        interp_dir = _os.path.join(output_dir, "Interpolator")
        self._temp_dir = interp_dir
        for banda in ("r", "g", "b", "z"):
            banda_dir = _os.path.join(interp_dir, banda)
            _os.makedirs(banda_dir, exist_ok=True)
            logger.info(
                f"Pasta criada: {banda_dir}",
                code="IDW_TASK_DIR_CREATED",
                banda=banda,
                path=banda_dir,
            )

        logger.info(
            f"Pastas de saida preparadas",
            code="IDW_TASK_OUTPUT_DIRS",
            output_final=output_path,
            tiles_temp=interp_dir,
            basename=basename_out,
        )

        signals.hud_update.emit({"message": "Interpolando tiles (IDW)..."})

        grid_bounds = (min_x_g, max_x_g, min_y_g, max_y_g)

        # --- Estagio 4: IDW Paralelo ---
        signals.hud_update.emit({"message": "Interpolando tiles (IDW)..."})
        signals.progress_update.emit(45.0)

        if not self._check_during_execution():
            self._limpar_temp()
            return False

        dir_r = _os.path.join(self._temp_dir, "r")
        dir_g = _os.path.join(self._temp_dir, "g")
        dir_b = _os.path.join(self._temp_dir, "b")
        dir_z = _os.path.join(self._temp_dir, "z")

        tile_jobs = []
        for idx, (x0, x1, y0, y1, t_row, t_col) in enumerate(tiles):
            tag = f"{t_row:04d}_{t_col:04d}"
            pr = _os.path.join(dir_r, f"tile_{tag}.tif") if target.get("r", False) else ""
            pg = _os.path.join(dir_g, f"tile_{tag}.tif") if target.get("g", False) else ""
            pb = _os.path.join(dir_b, f"tile_{tag}.tif") if target.get("b", False) else ""
            pz = _os.path.join(dir_z, f"tile_{tag}.tif") if target.get("z", False) else None
            tile_jobs.append((idx, tag, (x0, x1, y0, y1), pr, pg, pb, pz))

        results = Parallel(n_jobs=CpuGovernor.n_jobs(), verbose=0)(
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
        logger.info(f"IDW OK: {n_ok}, Pulado: {n_pulado}", code="IDW_TASK_IDW_DONE")
        self._log_memory_status("apos_idw")

        signals.hud_update.emit({"message": "Mesclando bandas..."})

        if self.is_cancelled or not self._check_during_execution():
            self._limpar_temp()
            return False

        # --- Estagio 5: Merge ---
        signals.hud_update.emit({"message": "Mesclando bandas..."})

        band_files = []
        merge_jobs = []

        def _add_merge(modo, src_dir, dtype):
            paths = sorted(glob.glob(_os.path.join(src_dir, "tile_*.tif")))
            if not paths:
                return
            out = _os.path.join(interp_dir, f"{basename_out}_{modo}.tif")
            merge_jobs.append((modo, paths, out, dtype))
            band_files.append(out)

        if target.get("r"): _add_merge("R", dir_r, np.uint8)
        if target.get("g"): _add_merge("G", dir_g, np.uint8)
        if target.get("b"): _add_merge("B", dir_b, np.uint8)
        if target.get("z"): _add_merge("Z", dir_z, np.float32)

        Parallel(n_jobs=CpuGovernor.n_jobs(), verbose=0)(
            delayed(InterpolatorUtils.mesclar_banda)(
                nome, paths, height, width, transform, crs_str,
                out_path, dtype, self._tool_key,
                nodata=0 if dtype == np.uint8 else -9999.0,
            )
            for nome, paths, out_path, dtype in merge_jobs
        )

        signals.hud_update.emit({"message": "Montando saida..."})

        if self.is_cancelled or not self._check_during_execution():
            self._limpar_temp()
            return False

        # --- Estagio 6: Montagem ---
        signals.hud_update.emit({"message": "Montando saida..."})

        has_rgb = target.get("r") and target.get("g") and target.get("b")
        has_z = target.get("z", False)
        final_outputs = list(band_files)

        if merge_bands and has_rgb:
            merged_path = output_path
            _os.makedirs(_os.path.dirname(merged_path), exist_ok=True)
            RasterLayerProcessing.compose_multiband_raster(
                band_files[:3], merged_path, tool_key=self._tool_key,
                nodata=0,
            )
            final_outputs.append(merged_path)
            logger.info(
                f"Mosaico RGB gerado",
                code="IDW_TASK_MOSAIC_DONE",
                output=merged_path,
                bandas="R,G,B",
            )
        elif merge_bands and not has_rgb:
            logger.warning(
                f"Mosaico nao gerado: requer R, G e B simultaneamente",
                code="IDW_TASK_MOSAIC_SKIP",
                target_checked=[k for k, v in target.items() if v],
            )

        signals.hud_update.emit({"message": "Salvando metadados..."})

        # --- Estagio 7: Metadados ---
        metadata = {
            "arquivo_las": file_path, "output_path": str(output_path),
            "parametros": {
                "resolucao_m": resol_m, "resolucao_cm": round(resol_m * 100, 2),
                "idw_k": k, "idw_power": power,
                "idw_raio_max_m": raio_max, "idw_overlap_m": overlap,
                "pontos_por_tile": pontos_por_tile,
                "crs": crs_str, "merge_bands": merge_bands, "target_bands": target,
            },
            "grid": {"width_px": width, "height_px": height,
                     "bounds": {"x_min": min_x_g, "x_max": max_x_g,
                                "y_min": min_y_g, "y_max": max_y_g}},
            "nuvem": {"n_pontos": n_pontos},
            "tiles": {"total": total_tiles, "ok": n_ok, "pulado": n_pulado},
            "arquivos_gerados": final_outputs,
        }

        meta_path = _os.path.join(interp_dir, "metadata.json")
        with open(meta_path, "w", encoding="utf-8") as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)

        self.result = metadata
        logger.info(
            f"Pipeline IDW concluido com sucesso",
            code="IDW_TASK_DONE",
            output_paths=final_outputs,
            grid_size=f"{width}x{height}",
            tiles_total=total_tiles,
            tiles_ok=n_ok,
        )
        SignalManager.instance().console_message.emit(
            f"[IDW] Sucesso! Saida: {_os.path.dirname(output_path)}"
        )
        out_link = output_dir.replace(chr(92), "/")
        band_link = interp_dir.replace(chr(92), "/")
        SignalManager.instance().console_html.emit(
            f"<span style='color:#4FC3F7;'>&#x2713; Mosaico: </span>"
            f"<a href='file:///{out_link}' style='color:#4FC3F7;'>{output_dir}</a>"
        )
        SignalManager.instance().console_html.emit(
            f"<span style='color:#4FC3F7;'>&#x2713; Bandas: </span>"
            f"<a href='file:///{band_link}' style='color:#4FC3F7;'>{interp_dir}</a>"
        )
        self._log_memory_status("final")

        signals.progress_update.emit(100.0)
        signals.hud_update.emit({"message": "Concluido!"})

        self._limpar_temp()
        return True