# -*- coding: utf-8 -*-
"""
DictManager — Catálogo centralizado de dicionários do sistema
===============================================================
Fornece dicionários padronizados para uso em widgets como GridCheckBox.

Cada entrada tem:
    label       → texto exibido
    description → tooltip/dica
    default     → valor padrão (True = checado, False = deschecado)
"""

from __future__ import annotations

from typing import Any, Dict, List


class DictManager:
    """
    Métodos estáticos que retornam dicionários padronizados.
    """

    @staticmethod
    def file_extensions() -> Dict[str, Dict[str, Any]]:
        """
        Extensões comuns do Windows + processamento.

        Retorna:
            { ".ext": { "label": "...", "description": "...", "default": bool } }
        """
        return {
            # ── Documentos ──
            ".txt":   {"label": ".txt",   "description": "Arquivo de texto puro", "default": True},
            ".rtf":   {"label": ".rtf",   "description": "Rich Text Format", "default": True},
            ".doc":   {"label": ".doc",   "description": "Microsoft Word (antigo)", "default": True},
            ".docx":  {"label": ".docx",  "description": "Microsoft Word (moderno)", "default": True},
            ".pdf":   {"label": ".pdf",   "description": "Adobe Portable Document", "default": True},
            ".csv":   {"label": ".csv",   "description": "Valores separados por vírgula", "default": True},
            ".json":  {"label": ".json",  "description": "JavaScript Object Notation", "default": True},
            ".xml":   {"label": ".xml",   "description": "eXtensible Markup Language", "default": True},
            ".md":    {"label": ".md",    "description": "Markdown", "default": True},
            ".log":   {"label": ".log",   "description": "Arquivo de log", "default": True},
            ".html":  {"label": ".html",  "description": "HyperText Markup Language", "default": True},

            # ── Planilhas ──
            ".xls":   {"label": ".xls",   "description": "Microsoft Excel (antigo)", "default": True},
            ".xlsx":  {"label": ".xlsx",  "description": "Microsoft Excel (moderno)", "default": True},

            # ── Imagens / Raster ──
            ".tif":   {"label": ".tif",   "description": "Tagged Image File (GeoTIFF)", "default": True},
            ".tiff":  {"label": ".tiff",  "description": "Tagged Image File Format", "default": True},
            ".png":   {"label": ".png",   "description": "Portable Network Graphics", "default": True},
            ".jpg":   {"label": ".jpg",   "description": "JPEG Image", "default": True},
            ".jpeg":  {"label": ".jpeg",  "description": "JPEG Image (alternativo)", "default": True},
            ".bmp":   {"label": ".bmp",   "description": "Bitmap Image", "default": True},
            ".gif":   {"label": ".gif",   "description": "Graphics Interchange Format", "default": True},
            ".svg":   {"label": ".svg",   "description": "Scalable Vector Graphics", "default": True},
            ".ico":   {"label": ".ico",   "description": "Windows Icon", "default": False},

            # ── Geoprocessamento ──
            ".shp":   {"label": ".shp",   "description": "Shapefile (geometria)", "default": True},
            ".shx":   {"label": ".shx",   "description": "Shapefile (índice)", "default": True},
            ".dbf":   {"label": ".dbf",   "description": "Shapefile (atributos dBASE)", "default": True},
            ".prj":   {"label": ".prj",   "description": "Shapefile (projeção)", "default": True},
            ".qpj":   {"label": ".qpj",   "description": "Shapefile (projeção QGIS)", "default": True},
            ".geojson": {"label": ".geojson", "description": "GeoJSON", "default": True},
            ".gpkg":  {"label": ".gpkg",  "description": "GeoPackage", "default": True},
            ".grd":   {"label": ".grd",   "description": "Surfer Grid / DEM", "default": True},
            ".dem":   {"label": ".dem",   "description": "Digital Elevation Model", "default": True},
            ".las":   {"label": ".las",   "description": "LIDAR Point Cloud (ASPRS)", "default": True},
            ".laz":   {"label": ".laz",   "description": "LIDAR Point Cloud (comprimido)", "default": True},
            ".hdf":   {"label": ".hdf",   "description": "Hierarchical Data Format", "default": True},
            ".nc":    {"label": ".nc",    "description": "NetCDF", "default": True},
            ".ecw":   {"label": ".ecw",   "description": "Enhanced Compressed Wavelet", "default": True},
            ".jp2":   {"label": ".jp2",   "description": "JPEG 2000", "default": True},
            ".sid":   {"label": ".sid",   "description": "MrSID Image", "default": True},
            ".vrt":   {"label": ".vrt",   "description": "GDAL Virtual Raster", "default": True},

            # ── Programação ──
            ".py":    {"label": ".py",    "description": "Python source", "default": True},
            ".js":    {"label": ".js",    "description": "JavaScript source", "default": True},
            ".ts":    {"label": ".ts",    "description": "TypeScript source", "default": True},
            ".css":   {"label": ".css",   "description": "Cascading Style Sheets", "default": True},
            ".qss":   {"label": ".qss",   "description": "Qt Style Sheet", "default": True},
            ".cpp":   {"label": ".cpp",   "description": "C++ source", "default": False},
            ".h":     {"label": ".h",     "description": "C/C++ header", "default": False},
            ".bat":   {"label": ".bat",   "description": "Windows batch script", "default": True},
            ".ps1":   {"label": ".ps1",   "description": "PowerShell script", "default": True},

            # ── Config / Outros ──
            ".ini":   {"label": ".ini",   "description": "Arquivo de configuração", "default": True},
            ".cfg":   {"label": ".cfg",   "description": "Arquivo de configuração genérico", "default": True},
            ".yml":   {"label": ".yml",   "description": "YAML (recursos, config)", "default": True},
            ".yaml":  {"label": ".yaml",  "description": "YAML alternativo", "default": True},
            ".toml":  {"label": ".toml",  "description": "TOML (config moderno)", "default": True},
            ".env":   {"label": ".env",   "description": "Variáveis de ambiente", "default": True},
            ".lock":  {"label": ".lock",  "description": "Arquivo de lock (dependências)", "default": False},
            ".tmp":   {"label": ".tmp",   "description": "Arquivo temporário", "default": False},
            ".bak":   {"label": ".bak",   "description": "Arquivo de backup", "default": False},
            ".old":   {"label": ".old",   "description": "Arquivo de versão anterior", "default": False},

            # ── Keras / ML ──
            ".keras": {"label": ".keras", "description": "Keras modelo salvo", "default": True},
            ".h5":    {"label": ".h5",    "description": "HDF5 (modelos Keras/TF)", "default": True},
            ".pt":    {"label": ".pt",    "description": "PyTorch model", "default": True},
            ".pth":   {"label": ".pth",   "description": "PyTorch model (alternativo)", "default": True},
            ".onnx":  {"label": ".onnx",  "description": "Open Neural Network Exchange", "default": True},
        }