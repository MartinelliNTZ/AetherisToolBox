# -*- coding: utf-8 -*-
"""
LasCheckStep — Step that runs quality checks on LAS/LAZ point clouds
======================================================================
Runs a configurable battery of checks via context and returns
consolidated results under "check_results" key.

Checks implemented:
  1. Point Count (point_count)
  2. Bounding Box (bbox)
  3. RGB Bands (rgb)
  4. Classification (classification)
  5. Zero Coordinates (zero_coords)
  6. XY Duplicates (duplicates)
  7. Density / Gaps (density)
  8. Intensity (intensity)
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
    """Step that runs quality checks on LAS/LAZ point clouds."""

    subfolder = "lascheck"
    advance_input = False  # Only analyzes, doesn't transform

    _CHECK_NAMES: dict[str, str] = {
        "point_count": "Point Count",
        "bbox": "Bounding Box",
        "rgb": "RGB Bands",
        "classification": "Classification",
        "zero_coords": "Zero Coordinates",
        "duplicates": "XY Duplicates",
        "density": "Density / Gaps",
        "intensity": "Intensity",
    }

    def __init__(self, advance_input: bool = False, input_path: str = ""):
        self.advance_input = advance_input
        self._custom_input_path = input_path  # Step-specific input_path (optional)

    def name(self) -> str:
        return "lascheck"

    def should_run(self, context: ExecutionContext) -> bool:
        path = self._custom_input_path or context.input_path
        return bool(path)

    def create_task(self, context: ExecutionContext) -> None:
        return None

    def run_inline(self, context: ExecutionContext) -> dict[str, Any]:
        """
        Executes all checks inline (synchronous) in QThread.
        Returns dict with results.
        """
        path = self._custom_input_path or context.input_path
        tool_key = context.tool_key or ToolKey.UNTRACEABLE.value
        logger = BaseUtil._get_logger(tool_key, "LasCheckStep")
        checks_enabled: dict[str, bool] = context.get("checks_enabled", {})

        signals = SignalManager.instance()

        logger.info(
            "Starting quality checks",
            code="LASCHECK_START",
            path=path,
        )

        # Opens LAS/LAZ (tries all available LAZ backends)
        try:
            laz_backends = tuple(
                b for b in laspy.LazBackend
                if b.name in ("LazrsParallel", "Lazrs", "Laszip")
            )
            if laz_backends:
                logger.debug(
                    "Available LAZ backends",
                    code="LASCHECK_LAZ_BACKENDS",
                    backends=[b.name for b in laz_backends],
                )
            else:
                laz_backends = None
        except AttributeError:
            laz_backends = None

        try:
            las = laspy.read(path, laz_backend=laz_backends)
            logger.info(
                "File opened successfully",
                code="LASCHECK_FILE_OPEN_OK",
                path=path,
                ext=os.path.splitext(path)[1].lower(),
                total_points=len(las.points),
            )
            signals.console_message.emit(
                f"[LasCheck] File opened: {os.path.basename(path)} "
                f"({len(las.points):,} points)"
            )
        except Exception as e:
            error_msg = str(e)
            logger.error(
                "Failed to open LAS/LAZ file",
                code="LASCHECK_FILE_OPEN_ERR",
                path=path,
                error=error_msg,
            )
            if ("No LazBackend selected" in error_msg 
                or "cannot decompress" in error_msg
                or "is not available" in error_msg):
                logger.critical(
                    "LAZ backend not available even with lazrs installed",
                    code="LASCHECK_LAZ_BACKEND_FAIL",
                    path=path,
                )
                signals.console_message.emit(
                    f"[LasCheck] ERROR: Could not open .LAZ. "
                    f"Check lazrs installation (pip install lazrs)."
                )
                return {
                    "check_results": {},
                    "summary": {"pass": 0, "warning": 0, "fail": 1, "total": 0, "error": True},
                    "error_type": "laz_backend",
                    "error": (
                        "Error opening .LAZ. Install backend with:\n"
                        "  pip install lazrs\n\n"
                        "Or convert to .LAS first."
                    ),
                }
            logger.error(
                "Unknown error opening file",
                code="LASCHECK_FILE_OPEN_UNKNOWN",
                path=path,
                error=error_msg,
            )
            raise

        n_total = len(las.points)

        # Check order + mapping
        check_order = [
            "point_count", "bbox", "rgb", "classification",
            "zero_coords", "duplicates", "density", "intensity",
            "statistics",
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
            "statistics": self._check_statistics,
        }

        results: dict[str, dict] = {}
        n_checks = len(check_order)

        # Build ordered list of enabled checks (for stages)
        enabled_check_names: list[str] = [
            name for name in check_order if checks_enabled.get(name, True)
        ]
        n_enabled = len(enabled_check_names)

        logger.info(
            "Starting check execution",
            code="LASCHECK_CHECKS_START",
            total_checks=n_checks,
            enabled_checks=list(checks_enabled.keys()),
            n_enabled=n_enabled,
        )

        stage_idx = 0
        for check_name in check_order:
            enabled = checks_enabled.get(check_name, True)
            if not enabled:
                logger.debug(
                    f"Check '{check_name}' skipped (disabled)",
                    code="LASCHECK_CHECK_SKIPPED",
                    check=check_name,
                )
                results[check_name] = {
                    "status": "skipped",
                    "message": "Check disabled by user",
                    "detail": "",
                    "suggestion": "",
                }
                continue

            display = self._CHECK_NAMES.get(check_name, check_name)
            signals.hud_update.emit({
                "message": f"Checking: {display}...",
            })

            method = check_methods[check_name]
            try:
                result = method(las, n_total)
                results[check_name] = result
                logger.info(
                    f"Check '{display}' done -> {result['status']}",
                    code="LASCHECK_CHECK_DONE",
                    check=check_name,
                    status=result["status"],
                    detail=result.get("detail", ""),
                )
            except Exception as e:
                logger.error(
                    f"Error executing check '{display}'",
                    code="LASCHECK_CHECK_EXEC_ERR",
                    check=check_name,
                    error=str(e),
                    path=path,
                )
                results[check_name] = {
                    "status": "fail",
                    "message": f"Error in check: {str(e)}",
                    "detail": str(e),
                    "suggestion": "Check file integrity.",
                }

            # Notify HUD that this stage is done (Scenario 3 - Stages)
            signals.hud_stage_done.emit(stage_idx)
            stage_idx += 1

        # Consolidate statistics
        pass_count = sum(1 for r in results.values() if r.get("status") == "pass")
        warn_count = sum(1 for r in results.values() if r.get("status") == "warning")
        fail_count = sum(1 for r in results.values() if r.get("status") == "fail")

        signals.progress_update.emit(100.0)

        logger.info(
            "Checks completed",
            code="LASCHECK_DONE",
            pass_count=pass_count,
            warn_count=warn_count,
            fail_count=fail_count,
            enabled_count=n_enabled,
        )
        signals.console_message.emit(
            f"[LasCheck] Checks finished: "
            f"{pass_count} ✅ {warn_count} ⚠️ {fail_count} ❌ ({n_enabled} checks)"
        )

        return {
            "check_results": results,
            "summary": {
                "pass": pass_count,
                "warning": warn_count,
                "fail": fail_count,
                "total": n_enabled,
            },
        }

    def on_success(self, context: ExecutionContext, result: Any) -> None:
        """Merges results into context."""
        if isinstance(result, dict):
            for key, value in result.items():
                context.set(key, value)

    # ══════════════════════════════════════════════════════════════════
    # Individual checks
    # ══════════════════════════════════════════════════════════════════

    @staticmethod
    def _check_point_count(las: laspy.LasData, n_total: int) -> dict:
        if n_total == 0:
            return {
                "status": "fail",
                "message": "No points found",
                "detail": "0",
                "suggestion": "Check if the file contains valid data.",
            }
        elif n_total < 1000:
            return {
                "status": "warning",
                "message": f"Only {n_total:,} points (small cloud)",
                "detail": str(n_total),
                "suggestion": "Consider merging with other clouds for better coverage.",
            }
        return {
            "status": "pass",
            "message": f"{n_total:,} points",
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
                "message": f"Invalid BBox on axes: {', '.join(issues)}",
                "detail": f"X[{x_min:.1f}, {x_max:.1f}] Y[{y_min:.1f}, {y_max:.1f}] Z[{z_min:.1f}, {z_max:.1f}]",
                "suggestion": "Check the point cloud coordinate system.",
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
                "message": "LAS has no RGB bands",
                "detail": "",
                "suggestion": "If RGB is needed, get data with a photogrammetric camera.",
            }
        return {
            "status": "pass",
            "message": "RGB present",
            "detail": "",
            "suggestion": "",
        }

    @staticmethod
    def _check_classification(las: laspy.LasData, n_total: int) -> dict:
        if not hasattr(las, "classification"):
            return {
                "status": "warning",
                "message": "No classification field",
                "detail": "",
                "suggestion": "Run a classifier (e.g. ground, vegetation) before using.",
            }
        classes = np.unique(las.classification)
        invalid = classes[(classes < 0) | (classes > 255)]
        if len(invalid) > 0:
            return {
                "status": "fail",
                "message": f"Invalid codes: {invalid.tolist()}",
                "detail": str(invalid.tolist()),
                "suggestion": "Reclassify the cloud with specialized software.",
            }
        valid_classes = sorted(classes[classes > 0].tolist())
        return {
            "status": "pass",
            "message": f"Valid codes: {valid_classes}",
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
                "message": f"{n_zero:,} points ({(pct):.3f}%) with X=Y=Z=0",
                "detail": f"{n_zero} ({pct:.3f}%)",
                "suggestion": "Remove points with zero coordinates or check SRS.",
            }
        elif pct > 0:
            return {
                "status": "warning",
                "message": f"{n_zero:,} points ({(pct):.3f}%) with X=Y=Z=0",
                "detail": f"{n_zero} ({pct:.3f}%)",
                "suggestion": "Consider filtering invalid points.",
            }
        return {
            "status": "pass",
            "message": "No points with zero coordinates",
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
                "message": f"{dup:,} duplicates in sample ({pct:.3f}%)",
                "detail": f"{dup} ({pct:.3f}%)",
                "suggestion": "Run duplicate filter before processing.",
            }
        elif dup > 0:
            return {
                "status": "warning",
                "message": f"{dup:,} duplicates in sample ({pct:.3f}%)",
                "detail": f"{dup} ({pct:.3f}%)",
                "suggestion": "",
            }
        return {
            "status": "pass",
            "message": "No duplicates detected",
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
                "message": "Zero planar area (coplanar points?)",
                "detail": "",
                "suggestion": "Check if points have horizontal extent.",
            }

        density = n_total / area
        return {
            "status": "pass",
            "message": f"Density: {density:.2f} pts/m²",
            "detail": f"{density:.2f}",
            "suggestion": "",
        }

    @staticmethod
    def _check_intensity(las: laspy.LasData, n_total: int) -> dict:
        if not hasattr(las, "intensity"):
            return {
                "status": "warning",
                "message": "No intensity field",
                "detail": "",
                "suggestion": "Data without intensity has less spectral information.",
            }
        i_min = int(np.min(las.intensity))
        i_max = int(np.max(las.intensity))

        if i_min < 0 or i_max > 65535:
            return {
                "status": "fail",
                "message": f"Intensity out of range: [{i_min}, {i_max}]",
                "detail": f"[{i_min}, {i_max}]",
                "suggestion": "Check if intensity values are consistent.",
            }
        return {
            "status": "pass",
            "message": f"Range [{i_min}, {i_max}] (valid)",
            "detail": f"[{i_min}, {i_max}]",
            "suggestion": "",
        }

    @staticmethod
    def _check_statistics(las: laspy.LasData, n_total: int) -> dict:
        """
        Generates complete LAS statistics JSON.

        Extracts:
          - Bounding box X, Y, Z (min/max)
          - Altimetry Z (min/max, mean, P5, P95)
          - BBox area and volume
          - RGB stats per band (min, max, mean, P5, P95)
          - Point density (bbox)
          - Ideal pixel based on density:
            spacing = 1 / sqrt(density)
            ideal_pixel = max(spacing * 0.75, 0.01)
        """
        import json

        # ── Bounding Box ────────────────────────────────────────────────
        x = np.asarray(las.x, dtype=np.float64)
        y = np.asarray(las.y, dtype=np.float64)
        z = np.asarray(las.z, dtype=np.float64)

        x_min, x_max = float(np.min(x)), float(np.max(x))
        y_min, y_max = float(np.min(y)), float(np.max(y))
        z_min, z_max = float(np.min(z)), float(np.max(z))

        # ── Altimetry (mean, P5, P95) ─────────────────────────────────
        z_mean = float(np.mean(z))
        z_p5   = float(np.percentile(z, 5))
        z_p95  = float(np.percentile(z, 95))

        # ── BBox area and volume ───────────────────────────────────────
        area_bbox   = (x_max - x_min) * (y_max - y_min)
        volume_bbox = area_bbox * (z_max - z_min)

        # ── RGB stats (min, max, mean, P5, P95 per band) ──────────────
        has_rgb = hasattr(las, "red") and las.red is not None
        rgb_data = None

        if has_rgb:
            red   = np.asarray(las.red,   dtype=np.float64)
            green = np.asarray(las.green, dtype=np.float64)
            blue  = np.asarray(las.blue,  dtype=np.float64)

            rgb_data = {
                "present": True,
                "red": {
                    "min":   int(np.min(red)),
                    "max":   int(np.max(red)),
                    "mean":  float(np.mean(red)),
                    "p5":    float(np.percentile(red, 5)),
                    "p95":   float(np.percentile(red, 95)),
                },
                "green": {
                    "min":   int(np.min(green)),
                    "max":   int(np.max(green)),
                    "mean":  float(np.mean(green)),
                    "p5":    float(np.percentile(green, 5)),
                    "p95":   float(np.percentile(green, 95)),
                },
                "blue": {
                    "min":   int(np.min(blue)),
                    "max":   int(np.max(blue)),
                    "mean":  float(np.mean(blue)),
                    "p5":    float(np.percentile(blue, 5)),
                    "p95":   float(np.percentile(blue, 95)),
                },
            }

        # ── Density (bbox) and Ideal Pixel ──────────────────────────────
        density_bbox = n_total / area_bbox if area_bbox > 0 else 0.0

        if density_bbox > 0:
            spacing_m  = 1.0 / (density_bbox ** 0.5)
            spacing_cm = spacing_m * 100
            ideal_pixel_m  = max(spacing_m * 0.75, 0.01)
            ideal_pixel_cm = ideal_pixel_m * 100
            ideal_pixel_mm = ideal_pixel_m * 1000
        else:
            spacing_m  = 0.0
            spacing_cm = 0.0
            ideal_pixel_m  = 0.01
            ideal_pixel_cm = 1.0
            ideal_pixel_mm = 10.0

        # ── Complete data for JSON export ────────────────────────────────
        stats_data = {
            "point_count": n_total,
            "bounding_box": {
                "x": {"min": round(x_min, 4), "max": round(x_max, 4)},
                "y": {"min": round(y_min, 4), "max": round(y_max, 4)},
                "z": {"min": round(z_min, 4), "max": round(z_max, 4)},
            },
            "altimetry": {
                "min":   round(z_min, 4),
                "max":   round(z_max, 4),
                "mean":  round(z_mean, 4),
                "p5":    round(z_p5, 4),
                "p95":   round(z_p95, 4),
            },
            "area_bbox_m2":   round(area_bbox, 4),
            "volume_bbox_m3": round(volume_bbox, 4),
            "rgb": rgb_data if has_rgb else {"present": False},
            "density_points_per_m2": {
                "bounding_box": round(density_bbox, 4),
            },
            "ideal_pixel": {
                "spacing_m":   round(spacing_m, 6),
                "spacing_cm":  round(spacing_cm, 2),
                "conversion_factor": 0.75,
                "min_pixel_m":  0.01,
                "pixel_m":  round(ideal_pixel_m, 6),
                "pixel_cm": round(ideal_pixel_cm, 2),
                "pixel_mm": round(ideal_pixel_mm, 1),
            },
        }

        # JSON in detail for the plugin to access
        detail_json = json.dumps(stats_data, ensure_ascii=False)

        # Summary message for GridLabel display
        if has_rgb:
            r_mean = rgb_data["red"]["mean"]
            g_mean = rgb_data["green"]["mean"]
            b_mean = rgb_data["blue"]["mean"]
            msg = (
                f"Z[{z_min:.2f},{z_max:.2f}] "
                f"Rmean:{r_mean:.0f} Gmean:{g_mean:.0f} Bmean:{b_mean:.0f} "
                f"Dens:{density_bbox:.2f}pts/m² "
                f"Pixel:{ideal_pixel_cm:.2f}cm"
            )
        else:
            msg = (
                f"Z[{z_min:.2f},{z_max:.2f}] "
                f"Dens:{density_bbox:.2f}pts/m² "
                f"Pixel:{ideal_pixel_cm:.2f}cm"
            )

        return {
            "status": "pass",
            "message": msg,
            "detail": detail_json,
            "suggestion": "",
        }