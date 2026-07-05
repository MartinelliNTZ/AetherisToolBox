# -*- coding: utf-8 -*-
"""
CpuGovernor — Governanca de uso de CPU
========================================
Limita o numero maximo de workers/threads que o software pode usar
simultaneamente, evitando saturacao total da CPU.

v2: Adiciona metodos de consulta de uso de CPU (cpu_percent, cpu_count,
cpu_tooltip) para centralizar dados do sistema no ResourceGovernor.

Constante editavel:
    CPU_USAGE_LIMIT = 0.50  # 50% dos CPUs (padrao)

Uso:
    from core.governor.CpuGovernor import CpuGovernor

    workers = CpuGovernor.max_workers()  # int(32 * 0.50) = 16
    n = CpuGovernor.n_jobs()             # mesmo valor, para joblib
    pct = CpuGovernor.cpu_percent()      # 45.2
    tip = CpuGovernor.cpu_tooltip()      # "CPU: 45.2% (8 cores, ...)"
"""

from __future__ import annotations

import os

import psutil


class CpuGovernor:
    """
    Governa o uso maximo de CPUs pelo software.

    Metodos de classe — nao requer instanciacao.

    Attributes:
        CPU_USAGE_LIMIT: Fracao dos CPUs totais que o software pode usar
                         (0.0 a 1.0). Padrao: 0.50 (50%).
    """

    CPU_USAGE_LIMIT: float = 0.25  # <<< EDITAVEL: 0.0 a 1.0

    @classmethod
    def max_workers(cls) -> int:
        """
        Retorna o numero maximo de workers permitido.

        Calculo: int(total_cpus * CPU_USAGE_LIMIT), minimo 1.

        Returns:
            int: Numero maximo de workers (>= 1).
        """
        total = os.cpu_count() or 4
        return max(1, int(total * cls.CPU_USAGE_LIMIT))

    @classmethod
    def n_jobs(cls) -> int:
        """
        Retorna n_jobs para joblib.Parallel (evitar usar -1).

        Returns:
            int: Mesmo valor de max_workers().
        """
        return cls.max_workers()

    # ── v2: Consulta de uso real da CPU ─────────────────────────────

    @classmethod
    def cpu_percent(cls) -> float:
        """
        Uso atual da CPU em percentual (0.0 a 100.0).

        Nota: A primeira chamada pode retornar 0.0 pois o psutil
        precisa de uma amostra anterior. Faca uma chamada dummy
        no startup se precisar de valores precisos desde o inicio.

        Returns:
            float: Percentual de uso da CPU (ultimo intervalo).
        """
        return psutil.cpu_percent(interval=None)

    @classmethod
    def cpu_count_physical(cls) -> int:
        """Numero de nucleos fisicos da CPU."""
        return psutil.cpu_count(logical=False) or 0

    @classmethod
    def cpu_count_logical(cls) -> int:
        """Numero de nucleos logicos (threads) da CPU."""
        return psutil.cpu_count(logical=True) or 0

    @classmethod
    def cpu_tooltip(cls) -> str:
        """
        Tooltip formatado com uso atual e contagem de nucleos.

        Returns:
            str: Ex: "CPU: 45.2% (8 cores fisicos, 16 logicos)"
        """
        pct = cls.cpu_percent()
        phys = cls.cpu_count_physical()
        log = cls.cpu_count_logical()
        return (
            f"CPU: {pct:.1f}% "
            f"({phys} cores fisicos, {log} logicos)"
        )