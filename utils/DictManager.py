# -*- coding: utf-8 -*-
"""
DictManager — Catálogo centralizado de dicionários do sistema
===============================================================
Fornece dicionários padronizados para uso em widgets como GridCheckBox.

Cada entrada tem:
    label       → texto exibido
    description → tooltip/dica
    default     → valor padrão (True = checado, False = deschecado)

Cada categoria tem sua própria constante no topo do módulo.
O método `file_extensions()` mescla todas e retorna o dict completo.
"""

from __future__ import annotations

from typing import Any, Dict


# ── Backup ──
BAK_EXTENSIONS: Dict[str, Dict[str, Any]] = {
    ".bak":   {"label": ".bak",   "description": "Arquivo de backup", "default": False},
    ".lock":  {"label": ".lock",  "description": "Arquivo de lock (dependências)", "default": False},
    ".old":   {"label": ".old",   "description": "Arquivo de versão anterior", "default": False},
    ".tmp":   {"label": ".tmp",   "description": "Arquivo temporário", "default": False},
}

# ── Config / Setup ──
CONFIG_EXTENSIONS: Dict[str, Dict[str, Any]] = {
    ".cfg":   {"label": ".cfg",   "description": "Arquivo de configuração genérico", "default": True},
    ".env":   {"label": ".env",   "description": "Variáveis de ambiente", "default": True},
    ".ini":   {"label": ".ini",   "description": "Arquivo de configuração", "default": True},
    ".toml":  {"label": ".toml",  "description": "TOML (config moderno)", "default": True},
    ".yaml":  {"label": ".yaml",  "description": "YAML alternativo", "default": True},
    ".yml":   {"label": ".yml",   "description": "YAML (recursos, config)", "default": True},
}

# ── Documentos ──
DOCUMENT_EXTENSIONS: Dict[str, Dict[str, Any]] = {
    ".csv":   {"label": ".csv",   "description": "Valores separados por vírgula", "default": True},
    ".doc":   {"label": ".doc",   "description": "Microsoft Word (antigo)", "default": True},
    ".docx":  {"label": ".docx",  "description": "Microsoft Word (moderno)", "default": True},
    ".html":  {"label": ".html",  "description": "HyperText Markup Language", "default": True},
    ".json":  {"label": ".json",  "description": "JavaScript Object Notation", "default": True},
    ".log":   {"label": ".log",   "description": "Arquivo de log", "default": True},
    ".md":    {"label": ".md",    "description": "Markdown", "default": True},
    ".pdf":   {"label": ".pdf",   "description": "Adobe Portable Document", "default": True},
    ".rtf":   {"label": ".rtf",   "description": "Rich Text Format", "default": True},
    ".txt":   {"label": ".txt",   "description": "Arquivo de texto puro", "default": True},
    ".xml":   {"label": ".xml",   "description": "eXtensible Markup Language", "default": True},
}

# ── Geoprocessamento ──
GEOPROCESSOR_EXTENSIONS: Dict[str, Dict[str, Any]] = {
    ".dbf":    {"label": ".dbf",    "description": "Shapefile (atributos dBASE)", "default": True},
    ".dem":    {"label": ".dem",    "description": "Digital Elevation Model", "default": True},
    ".ecw":    {"label": ".ecw",    "description": "Enhanced Compressed Wavelet", "default": True},
    ".geojson":{"label": ".geojson","description": "GeoJSON", "default": True},
    ".gpkg":   {"label": ".gpkg",   "description": "GeoPackage", "default": True},
    ".grd":    {"label": ".grd",    "description": "Surfer Grid / DEM", "default": True},
    ".hdf":    {"label": ".hdf",    "description": "Hierarchical Data Format", "default": True},
    ".jp2":    {"label": ".jp2",    "description": "JPEG 2000", "default": True},
    ".las":    {"label": ".las",    "description": "LIDAR Point Cloud (ASPRS)", "default": True},
    ".laz":    {"label": ".laz",    "description": "LIDAR Point Cloud (comprimido)", "default": True},
    ".nc":     {"label": ".nc",     "description": "NetCDF", "default": True},
    ".prj":    {"label": ".prj",    "description": "Shapefile (projeção)", "default": True},
    ".qpj":    {"label": ".qpj",    "description": "Shapefile (projeção QGIS)", "default": True},
    ".shp":    {"label": ".shp",    "description": "Shapefile (geometria)", "default": True},
    ".shx":    {"label": ".shx",    "description": "Shapefile (índice)", "default": True},
    ".sid":    {"label": ".sid",    "description": "MrSID Image", "default": True},
    ".vrt":    {"label": ".vrt",    "description": "GDAL Virtual Raster", "default": True},
    "qmd":     {"label": ".qmd",     "description": "QGIS Project (Markdown)", "default": True},
    "cpg":     {"label": ".cpg",     "description": "Shapefile (codificação)", "default": True},
    "qix":     {"label": ".qix",     "description": "Shapefile (índice QGIS)", "default": True},
}

# ── Imagens / Raster ──
IMAGE_EXTENSIONS: Dict[str, Dict[str, Any]] = {
    ".bmp":   {"label": ".bmp",   "description": "Bitmap Image", "default": True},
    ".gif":   {"label": ".gif",   "description": "Graphics Interchange Format", "default": True},
    ".ico":   {"label": ".ico",   "description": "Windows Icon", "default": False},
    ".jpeg":  {"label": ".jpeg",  "description": "JPEG Image (alternativo)", "default": True},
    ".jpg":   {"label": ".jpg",   "description": "JPEG Image", "default": True},
    ".png":   {"label": ".png",   "description": "Portable Network Graphics", "default": True},
    ".svg":   {"label": ".svg",   "description": "Scalable Vector Graphics", "default": True},
    ".tif":   {"label": ".tif",   "description": "Tagged Image File (GeoTIFF)", "default": True},
    ".tiff":  {"label": ".tiff",  "description": "Tagged Image File Format", "default": True},
}

# ── Keras / ML ──
KERAS_EXTENSIONS: Dict[str, Dict[str, Any]] = {
    ".h5":    {"label": ".h5",    "description": "HDF5 (modelos Keras/TF)", "default": True},
    ".keras": {"label": ".keras", "description": "Keras modelo salvo", "default": True},
    ".onnx":  {"label": ".onnx",  "description": "Open Neural Network Exchange", "default": True},
    ".pt":    {"label": ".pt",    "description": "PyTorch model", "default": True},
    ".pth":   {"label": ".pth",   "description": "PyTorch model (alternativo)", "default": True},
}

# ── Programação ──
PROGRAMMING_EXTENSIONS: Dict[str, Dict[str, Any]] = {
    ".bat":   {"label": ".bat",   "description": "Windows batch script", "default": True},
    ".cpp":   {"label": ".cpp",   "description": "C++ source", "default": False},
    ".css":   {"label": ".css",   "description": "Cascading Style Sheets", "default": True},
    ".h":     {"label": ".h",     "description": "C/C++ header", "default": False},
    ".js":    {"label": ".js",    "description": "JavaScript source", "default": True},
    ".ps1":   {"label": ".ps1",   "description": "PowerShell script", "default": True},
    ".py":    {"label": ".py",    "description": "Python source", "default": True},
    ".qss":   {"label": ".qss",   "description": "Qt Style Sheet", "default": True},
    ".ts":    {"label": ".ts",    "description": "TypeScript source", "default": True},
}

# ── Planilhas ──
SPREADSHEET_EXTENSIONS: Dict[str, Dict[str, Any]] = {
    ".xls":   {"label": ".xls",   "description": "Microsoft Excel (antigo)", "default": True},
    ".xlsx":  {"label": ".xlsx",  "description": "Microsoft Excel (moderno)", "default": True},
}

# ── Texto editável (abre como bloco de notas) ─────────────────────────
TEXT_EXTENSIONS: Dict[str, Dict[str, Any]] = {
    ".bat":   {"label": ".bat",   "description": "Windows batch script", "default": True},
    ".cfg":   {"label": ".cfg",   "description": "Arquivo de configuração genérico", "default": True},
    ".cpp":   {"label": ".cpp",   "description": "C++ source", "default": True},
    ".css":   {"label": ".css",   "description": "Cascading Style Sheets", "default": True},
    ".csv":   {"label": ".csv",   "description": "Valores separados por vírgula", "default": True},
    ".env":   {"label": ".env",   "description": "Variáveis de ambiente", "default": True},
    ".h":     {"label": ".h",     "description": "C/C++ header", "default": True},
    ".html":  {"label": ".html",  "description": "HyperText Markup Language", "default": True},
    ".ini":   {"label": ".ini",   "description": "Arquivo de configuração", "default": True},
    ".js":    {"label": ".js",    "description": "JavaScript source", "default": True},
    ".json":  {"label": ".json",  "description": "JavaScript Object Notation", "default": True},
    ".log":   {"label": ".log",   "description": "Arquivo de log", "default": True},
    ".md":    {"label": ".md",    "description": "Markdown", "default": True},
    ".ps1":   {"label": ".ps1",   "description": "PowerShell script", "default": True},
    ".py":    {"label": ".py",    "description": "Python source", "default": True},
    ".qss":   {"label": ".qss",   "description": "Qt Style Sheet", "default": True},
    ".rtf":   {"label": ".rtf",   "description": "Rich Text Format", "default": True},
    ".toml":  {"label": ".toml",  "description": "TOML (config moderno)", "default": True},
    ".ts":    {"label": ".ts",    "description": "TypeScript source", "default": True},
    ".txt":   {"label": ".txt",   "description": "Arquivo de texto puro", "default": True},
    ".xml":   {"label": ".xml",   "description": "eXtensible Markup Language", "default": True},
    ".yaml":  {"label": ".yaml",  "description": "YAML alternativo", "default": True},
    ".yml":   {"label": ".yml",   "description": "YAML (recursos, config)", "default": True},
}


class DictManager:
    """
    Métodos estáticos que retornam dicionários padronizados.

    As constantes de módulo (ex: DOCUMENT_EXTENSIONS) podem ser usadas
    individualmente; o método `file_extensions()` mescla todas.
    """

    @staticmethod
    def file_extensions() -> Dict[str, Dict[str, Any]]:
        """
        Retorna o catálogo completo de extensões mesclando todas
        as constantes de categoria.

        Retorna:
            { ".ext": { "label": "...", "description": "...", "default": bool } }
        """
        return {
            **BAK_EXTENSIONS,
            **CONFIG_EXTENSIONS,
            **DOCUMENT_EXTENSIONS,
            **GEOPROCESSOR_EXTENSIONS,
            **IMAGE_EXTENSIONS,
            **KERAS_EXTENSIONS,
            **PROGRAMMING_EXTENSIONS,
            **SPREADSHEET_EXTENSIONS,
        }