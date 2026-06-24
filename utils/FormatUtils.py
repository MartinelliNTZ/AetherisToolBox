# -*- coding: utf-8 -*-
"""
FormatUtils — Utilitários de formatação de dados
===================================================
Fornece formatação de tamanho de arquivo e datas de forma
centralizada para todo o sistema.

Uso:F
    from utils.FormatUtils import FormatUtils

    size_str = FormatUtils.format_size(1024)
    date_str = FormatUtils.format_date(1234567890.0)
"""

from __future__ import annotations

from datetime import datetime

from core.enum.ToolKey import ToolKey
from utils.BaseUtil import BaseUtil


class FormatUtils(BaseUtil):
    """Utilitários de formatação de dados."""

    @staticmethod
    def format_size(
        size_bytes: int,
        tool_key: str = ToolKey.UNTRACEABLE.value,
    ) -> str:
        """Formata bytes para string legível (B, KB, MB, GB).

        Args:
            size_bytes: Tamanho em bytes.
            tool_key: Chave da ferramenta para logging.
        """
        logger = BaseUtil._get_logger(tool_key, "FormatUtils")
        if size_bytes < 1024:
            result = f"{size_bytes} B"
        elif size_bytes < 1024 ** 2:
            result = f"{size_bytes / 1024:.1f} KB"
        elif size_bytes < 1024 ** 3:
            result = f"{size_bytes / 1024 ** 2:.1f} MB"
        else:
            result = f"{size_bytes / 1024 ** 3:.2f} GB"
        logger.debug("Tamanho formatado", code="FMT_SIZE", bytes=size_bytes, result=result)
        return result

    @staticmethod
    def format_date(
        timestamp: float,
        tool_key: str = ToolKey.UNTRACEABLE.value,
    ) -> str:
        """Formata timestamp Unix para string de data dd/mm/AAAA HH:MM:SS.

        Args:
            timestamp: Timestamp Unix.
            tool_key: Chave da ferramenta para logging.
        """
        logger = BaseUtil._get_logger(tool_key, "FormatUtils")
        result = datetime.fromtimestamp(timestamp).strftime("%d/%m/%Y %H:%M:%S")
        logger.debug("Data formatada", code="FMT_DATE", timestamp=timestamp, result=result)
        return result