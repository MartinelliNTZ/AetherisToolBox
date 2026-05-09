# -*- coding: utf-8 -*-
"""
Preferences — Gerenciador de preferencias por ferramenta
==========================================================
Cada ferramenta (tool) pode ter suas proprias preferencias salvas
em uma secao separada dentro do arquivo JSON.

Uso:
    from utils.Preferences import Preferences

    # Criar sessao para uma tool especifica
    prefs = Preferences(section="LogViewer")
    prefs.set("search_text", "erro")
    prefs.set("level_filter", "ERROR")
    prefs.save()

    text = prefs.get("search_text", "")
    level = prefs.get("level_filter", "ALL")
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Optional


class Preferences:
    """
    Gerenciador de preferencias com suporte a secoes por ferramenta.

    O arquivo preferences.json tem a estrutura:
    {
        "LogViewer": {
            "search_text": "erro",
            "level_filter": "ERROR"
        },
        "Console": {
            "font_size": 12
        }
    }

    Cada instancia de Preferences opera dentro de uma secao (section).
    Se section for None, opera no nivel raiz (compatibilidade retroativa).
    """

    _DEFAULT_PATH: Path = Path("config") / "preferences.json"

    # Cache de classe para evitar ler o arquivo varias vezes
    _cached_data: Dict[str, Any] = {}
    _cache_loaded: bool = False

    def __init__(self, section: str | None = None):
        """
        Args:
            section: Nome da secao (geralmente ToolKey.value).
                     Se None, opera no nivel raiz.
        """
        self._section = section

    # ── Leitura e escrita ─────────────────────────────────────────────

    def get(self, key: str, default: Any = None) -> Any:
        """Retorna o valor de uma chave dentro da secao."""
        data = self._load()
        if self._section:
            section_data = data.get(self._section, {})
            return section_data.get(key, default)
        return data.get(key, default)

    def set(self, key: str, value: Any) -> None:
        """Define um valor dentro da secao (em memoria apenas)."""
        data = self._load()
        if self._section:
            if self._section not in data:
                data[self._section] = {}
            data[self._section][key] = value
        else:
            data[key] = value
        self._cached_data = data

    def save(self) -> None:
        """Persiste o cache em disco."""
        path = self._DEFAULT_PATH
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", encoding="utf-8") as f:
            json.dump(self._cached_data, f, indent=2, ensure_ascii=False)

    def load_and_get(self, key: str, default: Any = None) -> Any:
        """
        Carrega do disco (forca reload) e retorna o valor.

        Util para quando outro processo/modificou o arquivo.
        """
        self._cache_loaded = False
        return self.get(key, default)

    def to_dict(self) -> Dict[str, Any]:
        """Retorna toda a secao como dict."""
        data = self._load()
        if self._section:
            return dict(data.get(self._section, {}))
        return dict(data)

    # ── Metodos internos ──────────────────────────────────────────────

    def _load(self) -> Dict[str, Any]:
        """Carrega o arquivo JSON uma unica vez (cache)."""
        if not self._cache_loaded:
            path = self._DEFAULT_PATH
            if path.is_file():
                try:
                    with path.open("r", encoding="utf-8") as f:
                        loaded = json.load(f)
                    self._cached_data = loaded if isinstance(loaded, dict) else {}
                except Exception:
                    self._cached_data = {}
            else:
                self._cached_data = {}
            self._cache_loaded = True
        return self._cached_data