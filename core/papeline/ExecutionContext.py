# -*- coding: utf-8 -*-
"""
ExecutionContext — Estado compartilhado entre steps da pipeline
================================================================
Container de estado que permite que steps compartilhem dados
sem acoplamento direto. Também carrega estado de cancelamento e erros.
"""

from __future__ import annotations

from typing import Any


class ExecutionContext:
    """
    Container de estado compartilhado entre todos os steps da pipeline.

    Métodos principais:
        set(key, value) → Armazena valor (fluent, retorna self)
        get(key, default=None) → Recupera valor
        has(key) → Verifica se chave existe
        require(keys) → Lança KeyError se alguma chave obrigatória faltar
        add_error(exc) → Adiciona erro à lista
        has_errors() → True se houve erro
        cancel() → Marca como cancelado
        is_cancelled() → True se foi cancelado
        clear() → Reseta todo o estado
    """

    INPUT_PATH = "input_path"
    """Chave padrão para o caminho do arquivo de entrada."""
    OUTPUT_PATH = "output_path"
    """Chave padrão para o caminho do arquivo de saída."""
    TOOL_KEY = "tool_key"
    """Chave padrão para a ferramenta."""

    def __init__(self, initial_data: dict = None):
        self._data: dict = initial_data.copy() if initial_data else {}
        self._errors: list[Exception] = []
        self._is_cancelled: bool = False

    # ── Getters / Setters ───────────────────────────────────────────

    def set(self, key: str, value: Any) -> ExecutionContext:
        """Armazena valor no contexto. Retorna self para fluent interface."""
        self._data[key] = value
        return self

    def get(self, key: str, default: Any = None) -> Any:
        """Recupera valor do contexto."""
        return self._data.get(key, default)

    def has(self, key: str) -> bool:
        """Verifica se chave existe no contexto."""
        return key in self._data

    def require(self, keys: list[str]) -> None:
        """Lança KeyError se alguma chave obrigatória estiver faltando."""
        missing = [k for k in keys if k not in self._data]
        if missing:
            raise KeyError(f"Chaves obrigatórias ausentes: {missing}")

    # ── Erros ───────────────────────────────────────────────────────

    def add_error(self, exc: Exception) -> None:
        """Adiciona erro à lista de erros."""
        self._errors.append(exc)

    def get_errors(self) -> list[Exception]:
        """Retorna cópia da lista de erros."""
        return self._errors.copy()

    def has_errors(self) -> bool:
        """True se houve algum erro."""
        return len(self._errors) > 0

    # ── Cancelamento ────────────────────────────────────────────────

    def cancel(self) -> None:
        """Marca o contexto como cancelado."""
        self._is_cancelled = True

    def is_cancelled(self) -> bool:
        """True se foi cancelado."""
        return self._is_cancelled

    # ── Reset ───────────────────────────────────────────────────────

    def clear(self) -> None:
        """Reseta todo o estado (dados, erros, cancelamento)."""
        self._data.clear()
        self._errors.clear()
        self._is_cancelled = False

    @property
    def data(self) -> dict:
        """Retorna o dicionário interno de dados (compatibilidade com código legado)."""
        return self._data

    def __repr__(self) -> str:
        return (
            f"<ExecutionContext "
            f"data={len(self._data)} keys, "
            f"errors={len(self._errors)}, "
            f"cancelled={self._is_cancelled}>"
        )
