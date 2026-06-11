# -*- coding: utf-8 -*-
"""
Preferences — Gerenciador de preferências por ferramenta
=========================================================
Métodos estáticos para salvar/carregar preferências de cada
ferramenta no arquivo config/preferences.json.

Uso:
    from utils.Preferences import Preferences
    from core.enum.ToolKey import ToolKey

    # Salvar preferências de uma tool (merge, não sobrescreve)
    Preferences.save_tool_prefs(ToolKey.CONSOLE, {"font_size": 12, "theme": "dark"})

    # Carregar preferências de uma tool
    data = Preferences.load_tool_prefs(ToolKey.CONSOLE)
    font_size = data.get("font_size", 10)
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict

from core.enum.ToolKey import ToolKey
from utils.BaseUtil import BaseUtil


class Preferences(BaseUtil):
    """
    Gerenciador de preferências estático.

    O arquivo preferences.json tem a estrutura:
    {
        "Console": {
            "font_size": 12,
            "theme": "dark"
        },
        "LogViewer": {
            "search_text": "erro"
        }
    }

    Uso exclusivamente via métodos estáticos.
    Não instancie esta classe.
    """

    _DEFAULT_PATH: Path = Path(__file__).resolve().parent.parent / "config" / "preferences.json"

    # ── API Pública ──────────────────────────────────────────────────

    @staticmethod
    def save_tool_prefs(
        tool_key: ToolKey,
        data: Dict[str, Any],
        caller_tool_key: str = ToolKey.UNTRACEABLE.value,
    ) -> None:
        """
        Salva (merge) as preferências de uma ferramenta no arquivo JSON.

        Args:
            tool_key: Chave da ferramenta (ToolKey enum)
            data: Dicionário com as preferências a salvar
            caller_tool_key: Chave da ferramenta chamadora para logging.
        """
        logger = BaseUtil._get_logger(caller_tool_key, "Preferences")
        tool_name = tool_key.value if isinstance(tool_key, ToolKey) else str(tool_key)
        all_data = Preferences._load_from_disk()

        section = all_data.get(tool_name, {})
        section.update(data)
        all_data[tool_name] = section

        Preferences._write_to_disk(all_data)
        logger.info(
            "Preferências salvas",
            code="PREFS_SAVE",
            tool=tool_name,
            keys=list(data.keys()),
        )

    @staticmethod
    def load_tool_prefs(
        tool_key: ToolKey,
        caller_tool_key: str = ToolKey.UNTRACEABLE.value,
    ) -> Dict[str, Any]:
        """
        Carrega as preferências de uma ferramenta do arquivo JSON.

        Args:
            tool_key: Chave da ferramenta (ToolKey enum)
            caller_tool_key: Chave da ferramenta chamadora para logging.

        Returns:
            Dicionário com as preferências da tool (vazio se não existir)
        """
        logger = BaseUtil._get_logger(caller_tool_key, "Preferences")
        tool_name = tool_key.value if isinstance(tool_key, ToolKey) else str(tool_key)
        all_data = Preferences._load_from_disk()
        section = all_data.get(tool_name, {})
        logger.info(
            "Preferências carregadas",
            code="PREFS_LOAD",
            tool=tool_name,
        )
        return dict(section)

    # ── Utilitários ──────────────────────────────────────────────────

    @staticmethod
    def all_data() -> Dict[str, Any]:
        """Retorna o JSON completo de todas as seções (sempre do disco)."""
        return Preferences._load_from_disk()

    @staticmethod
    def save_all(
        data: Dict[str, Any],
        caller_tool_key: str = ToolKey.UNTRACEABLE.value,
    ) -> None:
        """Sobrescreve o JSON inteiro com o dict fornecido.

        Args:
            data: Dicionário completo de preferências.
            caller_tool_key: Chave da ferramenta chamadora para logging.
        """
        logger = BaseUtil._get_logger(caller_tool_key, "Preferences")
        Preferences._write_to_disk(data)
        logger.info(
            "Todas as preferências salvas",
            code="PREFS_SAVE_ALL",
            sections=list(data.keys()),
        )

    @staticmethod
    def infer_type(value: Any) -> str:
        """Infere o tipo de preferência a partir do valor."""
        if isinstance(value, bool):
            return "bool"
        if isinstance(value, int):
            return "int"
        if isinstance(value, float):
            return "float"
        return "text"

    # ── Métodos Internos ─────────────────────────────────────────────

    @classmethod
    def _load_from_disk(cls) -> Dict[str, Any]:
        """Lê o arquivo JSON diretamente do disco."""
        path = cls._DEFAULT_PATH
        if path.is_file():
            try:
                with path.open("r", encoding="utf-8") as f:
                    loaded = json.load(f)
                return loaded if isinstance(loaded, dict) else {}
            except Exception as e:
                cls._get_logger(ToolKey.SYSTEM.value).error(
                    "Erro ao carregar preferências do disco",
                    code="PREFS_LOAD_ERR",
                    error=str(e),
                )
                return {}
        return {}

    @classmethod
    def _write_to_disk(cls, data: Dict[str, Any]) -> None:
        """Persiste o dicionário completo no arquivo JSON."""
        path = cls._DEFAULT_PATH
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)