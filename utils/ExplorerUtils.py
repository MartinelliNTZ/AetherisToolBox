# -*- coding: utf-8 -*-
"""
ExplorerUtils — Única classe responsável por buscar arquivos/pastas no SO
==========================================================================
Centraliza todas as chamadas a QFileDialog. Nenhum outro módulo deve
chamar QFileDialog diretamente.

Uso:
    from utils.ExplorerUtils import ExplorerUtils

    path = ExplorerUtils.open_file("Selecionar imagem", filter="GeoTIFF (*.tif)")
    paths = ExplorerUtils.open_files("Selecionar arquivos", filter="CSV (*.csv)")
    save = ExplorerUtils.save_file("Salvar como", filter="JSON (*.json)")
    folder = ExplorerUtils.select_directory("Selecionar pasta")
    folders = ExplorerUtils.select_directories("Selecionar pastas")
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import List, Optional, Tuple

from PySide6.QtWidgets import QFileDialog, QWidget


class ExplorerUtils:
    """
    Métodos estáticos para todas as operações de seleção de arquivo/pasta.
    """

    # ── Modos únicos ────────────────────────────────────────────────

    @staticmethod
    def open_file(
        title: str = "Selecionar arquivo",
        initial_dir: str = "",
        file_filter: str = "Todos (*.*)",
        parent: Optional[QWidget] = None,
    ) -> str:
        """
        Abre diálogo para selecionar UM arquivo para leitura.

        Returns:
            Caminho do arquivo selecionado, ou string vazia se cancelado.
        """
        path, _ = QFileDialog.getOpenFileName(
            parent, title, initial_dir, file_filter,
        )
        return path or ""

    @staticmethod
    def save_file(
        title: str = "Salvar arquivo",
        initial_dir: str = "",
        file_filter: str = "Todos (*.*)",
        parent: Optional[QWidget] = None,
    ) -> str:
        """
        Abre diálogo para selecionar UM arquivo para salvar.

        Returns:
            Caminho do arquivo, ou string vazia se cancelado.
        """
        path, _ = QFileDialog.getSaveFileName(
            parent, title, initial_dir, file_filter,
        )
        return path or ""

    @staticmethod
    def select_directory(
        title: str = "Selecionar pasta",
        initial_dir: str = "",
        parent: Optional[QWidget] = None,
    ) -> str:
        """
        Abre diálogo para selecionar UMA pasta.

        Returns:
            Caminho da pasta, ou string vazia se cancelado.
        """
        path = QFileDialog.getExistingDirectory(
            parent, title, initial_dir,
        )
        return path or ""

    # ── Modos múltiplos ─────────────────────────────────────────────

    @staticmethod
    def open_files(
        title: str = "Selecionar arquivos",
        initial_dir: str = "",
        file_filter: str = "Todos (*.*)",
        parent: Optional[QWidget] = None,
    ) -> List[str]:
        """
        Abre diálogo para selecionar MÚLTIPLOS arquivos para leitura.

        Returns:
            Lista de caminhos, ou lista vazia se cancelado.
        """
        paths, _ = QFileDialog.getOpenFileNames(
            parent, title, initial_dir, file_filter,
        )
        return list(paths)

    @staticmethod
    def select_directories(
        title: str = "Selecionar pastas",
        initial_dir: str = "",
        parent: Optional[QWidget] = None,
    ) -> List[str]:
        """
        Abre diálogo para selecionar MÚLTIPLAS pastas.
        Nota: QFileDialog nativo não suporta multi-pasta diretamente.
        Esta implementação retorna uma pasta por vez (usuário escolhe uma).

        Returns:
            Lista com um caminho de pasta, ou vazia.
        """
        path = QFileDialog.getExistingDirectory(
            parent, title, initial_dir,
        )
        return [path] if path else []

    # ── Config Directory ────────────────────────────────────────────

    @staticmethod
    def get_plugin_config_dir(plugin_name: str) -> Path:
        """
        Retorna e garante a existência do diretório de config de um plugin.

        Estrutura: ``config/data/<plugin_name>/``

        Args:
            plugin_name: Nome do plugin (ex: "hotkey", "renamer").

        Returns:
            Path do diretório (já criado).
        """
        config_dir = Path("config/data") / plugin_name
        config_dir.mkdir(parents=True, exist_ok=True)
        return config_dir

    # ── Busca de Arquivos ───────────────────────────────────────────

    @staticmethod
    def find_files(
        root_path: str,
        extensions: frozenset[str],
        recursive: bool = False,
    ) -> List[str]:
        """
        Busca arquivos por extensao em um diretorio (generico).

        Args:
            root_path: Caminho do diretorio raiz.
            extensions: Conjunto de extensoes (ex: frozenset({".mrk", ".MRK"})).
            recursive: Se True, vasculha subpastas recursivamente.

        Returns:
            Lista de caminhos absolutos dos arquivos encontrados, ordenados.
            Vazia se diretorio invalido ou nenhum arquivo encontrado.
        """
        if not root_path:
            return []
        root = Path(root_path)
        if not root.is_dir():
            return []

        results: List[str] = []
        pattern = "**/*" if recursive else "*"
        for f in root.glob(pattern):
            if f.is_file() and f.suffix.lower() in extensions:
                results.append(str(f.resolve()))

        results.sort()
        return results

    # ── Default Paths ──────────────────────────────────────────────

    @staticmethod
    def get_default_path(category: str, root_folder: str = "") -> str:
        """
        Retorna caminho padrão para uma categoria baseado na root_folder.
        Use DefaultPathCategory enum para evitar strings soltas.

        Categorias: "vector", "raster", "ico", "image", "documents"

        Se root_folder vazio, retorna "" (botão de sugestão não aparece).
        """
        from core.enum.DefaultPathCategory import DefaultPathCategory
        paths = {
            DefaultPathCategory.VECTOR:    "vector",
            DefaultPathCategory.RASTER:    "raster",
            DefaultPathCategory.ICO:       "ico",
            DefaultPathCategory.IMAGE:     "image",
            DefaultPathCategory.DOCUMENTS: "documents",
        }
        sub = paths.get(category, "")
        if not sub or not root_folder:
            return ""
        return os.path.join(root_folder, sub)

    @staticmethod
    def ensure_directory(path: str) -> str:
        """
        Garante que um diretório existe. Se não existir, cria.
        Se path for vazio, retorna vazio.

        Args:
            path: Caminho do diretório.

        Returns:
            O mesmo path, ou vazio se vazio.
        """
        if not path:
            return ""
        os.makedirs(path, exist_ok=True)
        return path

    # ── Utilitário ──────────────────────────────────────────────────

    @staticmethod
    def resolve_initial_dir(current_path: str) -> str:
        """
        Retorna o diretório base de um caminho, se ele existir.
        Útil para definir o initial_dir dos diálogos.

        Args:
            current_path: Caminho atual (arquivo ou pasta).

        Returns:
            - Se for um diretório existente → o próprio diretório.
            - Se for um arquivo existente → o diretório pai.
            - Se não existir ou vazio → string vazia (abre em recentes).
        """
        if not current_path:
            return ""
        if os.path.isdir(current_path):
            return current_path
        parent = os.path.dirname(current_path)
        if parent and os.path.exists(parent):
            return parent
        return ""
