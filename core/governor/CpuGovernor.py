# -*- coding: utf-8 -*-
"""
CpuGovernor — Governanca de uso de CPU
========================================
Limita o numero maximo de workers/threads que o software pode usar
simultaneamente, evitando saturacao total da CPU.

Constante editavel:
    CPU_USAGE_LIMIT = 0.50  # 50% dos CPUs (padrao)

Uso:
    from core.governor.CpuGovernor import CpuGovernor

    workers = CpuGovernor.max_workers()  # int(32 * 0.50) = 16
    n = CpuGovernor.n_jobs()             # mesmo valor, para joblib
"""

from __future__ import annotations

import os


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
