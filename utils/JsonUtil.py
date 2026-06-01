# -*- coding: utf-8 -*-
"""
JsonUtil — Criação e manipulação de JSONs temporários
=======================================================
Centraliza operações de criar, ler, escrever e manipular
arquivos JSON em diretório temporário gerenciado pelo sistema.

Uso:
    from utils.JsonUtil import JsonUtil

    path = JsonUtil.create_temp_json({"key": "value"})
    data = JsonUtil.read_json(path)
    JsonUtil.write_json(path, data)
"""

from __future__ import annotations

import json
import os
import uuid
from typing import Any, Dict, Optional

from utils.ExplorerUtils import ExplorerUtils


_TEMP_DIR = "file_preview"


class JsonUtil:
    """Utilitário para criar e manipular JSONs em pasta temporária."""

    @staticmethod
    def _get_temp_dir() -> str:
        """Retorna e garante a existência do diretório temporário de JSONs."""
        config_dir = ExplorerUtils.get_plugin_config_dir(_TEMP_DIR)
        temp_dir = str(config_dir / "temp")
        os.makedirs(temp_dir, exist_ok=True)
        return temp_dir

    @staticmethod
    def create_temp_json(data: Optional[Dict[str, Any]] = None) -> str:
        """
        Cria um arquivo JSON temporário com dados iniciais.

        Args:
            data: Dicionário inicial (vazio se None).

        Returns:
            Caminho absoluto do arquivo JSON criado.
        """
        if data is None:
            data = {}

        temp_dir = JsonUtil._get_temp_dir()
        file_name = f"preview_{uuid.uuid4().hex}.json"
        file_path = os.path.join(temp_dir, file_name)

        JsonUtil.write_json(file_path, data)
        return file_path

    @staticmethod
    def read_json(file_path: str) -> Dict[str, Any]:
        """
        Lê e retorna o conteúdo de um arquivo JSON.

        Args:
            file_path: Caminho do arquivo JSON.

        Returns:
            Dicionário com os dados, ou dict vazio se não existir.
        """
        if not os.path.exists(file_path):
            return {}

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                return dict(json.load(f))
        except (json.JSONDecodeError, OSError):
            return {}

    @staticmethod
    def write_json(file_path: str, data: Dict[str, Any]) -> None:
        """
        Escreve dados em um arquivo JSON (sobrescreve).

        Args:
            file_path: Caminho do arquivo JSON.
            data: Dicionário a ser salvo.
        """
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    @staticmethod
    def update_json(file_path: str, updates: Dict[str, Any]) -> Dict[str, Any]:
        """
        Lê um JSON, aplica atualizações e salva de volta.

        Args:
            file_path: Caminho do arquivo JSON.
            updates: Dicionário com campos a atualizar/inserir.

        Returns:
            Dicionário completo após atualização.
        """
        data = JsonUtil.read_json(file_path)
        data.update(updates)
        JsonUtil.write_json(file_path, data)
        return data

    @staticmethod
    def cleanup_temp_json(file_path: str) -> None:
        """
        Remove um arquivo JSON temporário.

        Args:
            file_path: Caminho do arquivo a remover.
        """
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
        except OSError:
            pass