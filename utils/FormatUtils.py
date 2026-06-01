# -*- coding: utf-8 -*-
"""
FormatUtils — Utilitários de formatação de dados
===================================================
Fornece formatação de tamanho de arquivo e datas de forma
centralizada para todo o sistema.

Uso:
    from utils.FormatUtils import FormatUtils

    size_str = FormatUtils.format_size(1024)
    date_str = FormatUtils.format_date(1234567890.0)
"""

from __future__ import annotations

from datetime import datetime


class FormatUtils:
    """Utilitários de formatação de dados."""

    @staticmethod
    def format_size(size_bytes: int) -> str:
        """Formata bytes para string legível (B, KB, MB, GB)."""
        if size_bytes < 1024:
            return f"{size_bytes} B"
        elif size_bytes < 1024 ** 2:
            return f"{size_bytes / 1024:.1f} KB"
        elif size_bytes < 1024 ** 3:
            return f"{size_bytes / 1024 ** 2:.1f} MB"
        else:
            return f"{size_bytes / 1024 ** 3:.2f} GB"

    @staticmethod
    def format_date(timestamp: float) -> str:
        """Formata timestamp Unix para string de data dd/mm/AAAA HH:MM:SS."""
        return datetime.fromtimestamp(timestamp).strftime("%d/%m/%Y %H:%M:%S")