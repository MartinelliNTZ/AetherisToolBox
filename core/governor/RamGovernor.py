# -*- coding: utf-8 -*-
"""
RamGovernor — Monitoramento de RAM do sistema e processo
===========================================================
Fornece dados de RAM via psutil (já em requirements.txt).

Uso:
    from core.governor.RamGovernor import RamGovernor

    gov = RamGovernor()
    print(gov.total_system_ram())
    print(gov.used_system_ram())
    print(gov.available_system_ram())
    print(gov.process_ram())
    print(gov.percent_used())
    print(gov.percent_process())
    print(gov.snapshot())
"""

from __future__ import annotations

import os
from typing import Dict

import psutil

from utils.FormatUtils import FormatUtils


class RamGovernor:
    """
    Monitora RAM do sistema inteiro e do processo atual.

    NOTA: Para formatação legível de bytes, usar FormatUtils.format_size()
    (Contrato 22). Este governor retorna valores brutos em bytes.
    """

    def __init__(self) -> None:
        self._process = psutil.Process(os.getpid())

    # ── RAM do Sistema ───────────────────────────────────────────────

    @staticmethod
    def total_system_ram() -> int:
        """RAM física total instalada (bytes)."""
        return psutil.virtual_memory().total

    @staticmethod
    def used_system_ram() -> int:
        """RAM usada por todo o sistema (bytes)."""
        return psutil.virtual_memory().used

    @staticmethod
    def available_system_ram() -> int:
        """RAM disponível no sistema (bytes)."""
        return psutil.virtual_memory().available

    # ── RAM do Processo Atual ────────────────────────────────────────

    def process_ram(self) -> int:
        """
        RAM usada pelo processo atual (RSS, bytes).
        Inclui memória do Python + bibliotecas nativas carregadas.
        """
        return self._process.memory_info().rss

    # ── Percentuais ──────────────────────────────────────────────────

    @staticmethod
    def percent_used() -> float:
        """Percentual de RAM do sistema em uso (0.0 a 100.0)."""
        return psutil.virtual_memory().percent

    def percent_process(self) -> float:
        """Percentual de RAM do processo atual relativo ao total."""
        total = self.total_system_ram()
        if total == 0:
            return 0.0
        return (self.process_ram() / total) * 100.0

    # ── Snapshot ─────────────────────────────────────────────────────

    def snapshot(self) -> Dict[str, object]:
        """
        Retorna dicionário completo do estado atual de RAM.

        Os valores em bytes podem ser formatados com FormatUtils.format_size().
        """
        total = self.total_system_ram()
        used = self.used_system_ram()
        avail = self.available_system_ram()
        proc = self.process_ram()

        return {
            "total_bytes": total,
            "total_human": FormatUtils.format_size(total),
            "used_system_bytes": used,
            "used_system_human": FormatUtils.format_size(used),
            "available_bytes": avail,
            "available_human": FormatUtils.format_size(avail),
            "process_bytes": proc,
            "process_human": FormatUtils.format_size(proc),
            "percent_system": round(self.percent_used(), 1),
            "percent_process": round(self.percent_process(), 1),
        }