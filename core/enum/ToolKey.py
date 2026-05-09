# -*- coding: utf-8 -*-
"""
ToolKey — Enum de chaves das ferramentas do sistema
=====================================================
Centraliza os nomes das ferramentas em um Enum para evitar
strings soltas no código e facilitar manutenção.

Uso:
    from core.enum.ToolKey import ToolKey

    ToolKey.HOME.value          # "Home"
    ToolKey.CONSOLE.value       # "Console"
    ToolKey.CLASSIFIER.value    # "Classifier"
    ToolKey.SYSTEM.value        # "System"

    # Iterar sobre todas:
    for key in ToolKey:
        print(key.value)
"""

from __future__ import annotations

from enum import Enum, auto


class ToolKey(str, Enum):
    """Enum com as chaves de todas as ferramentas registradas."""

    HOME = "Home"
    CONSOLE = "Console"
    CLASSIFIER = "Classifier"
    SYSTEM = "System"

    # ── Método utilitário ──────────────────────────────────────────────

    @classmethod
    def display_names(cls) -> list[str]:
        """Retorna lista com os nomes de todas as ferramentas."""
        return [item.value for item in cls]

    @classmethod
    def from_name(cls, name: str) -> "ToolKey":
        """
        Retorna o enum correspondente ao nome, ou levanta ValueError.

        Exemplo:
            ToolKey.from_name("Console")  # ToolKey.CONSOLE
        """
        try:
            return cls(name)
        except ValueError:
            raise ValueError(
                f"'{name}' não é uma ToolKey válida. "
                f"Opções: {', '.join(cls.display_names())}"
            )