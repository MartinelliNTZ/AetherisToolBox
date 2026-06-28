# -*- coding: utf-8 -*-
"""
ResourceGovernor — Orquestrador de Governança de Recursos
============================================================
Ponto único de integração para plugins/pipelines consultarem
se há recursos suficientes antes de executar tarefas pesadas.

Uso:
    from core.governor.ResourceGovernor import ResourceGovernor
    from core.governor.RamLimitPolicy import RamLimitPolicy, RamLimitMode

    policy = RamLimitPolicy(mode=RamLimitMode.GLOBAL, fraction=0.90)
    governor = ResourceGovernor(policy, tool_key="IdwInterpolator")

    # Antes de executar
    can, reason = governor.can_execute(estimated_ram=8_000_000_000)
    if not can:
        print(reason)
        return

    # Ajustar tile size
    safe_tile = governor.recommended_tile_size(10_000_000)
"""

from __future__ import annotations

import math
from typing import Dict, Optional, Tuple

from core.enum.ToolKey import ToolKey
from core.governor.RamGovernor import RamGovernor
from core.governor.RamLimitPolicy import RamLimitPolicy
from utils.BaseUtil import BaseUtil
from utils.FormatUtils import FormatUtils


class ResourceExceededError(Exception):
    """
    Exceção lançada quando os recursos são insuficientes para executar.
    """
    def __init__(self, message: str, snapshot: Optional[Dict] = None):
        super().__init__(message)
        self.snapshot = snapshot


class ResourceGovernor:
    """
    Orquestrador de decisões baseadas em recursos.

    Args:
        policy: RamLimitPolicy com a estratégia de limite.
        tool_key: ToolKey.value para logging (Contrato 26).
                  Se não fornecido, usa ToolKey.SYSTEM.value.
    """

    # Constante: bytes por ponto LAS (x, y, z + rgb ≈ 28 bytes float64)
    # Na prática numpy.float64 = 8 bytes, 4 bandas = 32 bytes
    BYTES_PER_POINT: int = 32

    # Máximo de warnings consecutivos antes de forçar cancelamento
    MAX_WARNINGS: int = 3

    def __init__(
        self,
        policy: RamLimitPolicy,
        tool_key: str = ToolKey.SYSTEM.value,
    ) -> None:
        self._policy = policy
        self._ram = RamGovernor()
        self._tool_key = tool_key
        self._warnings: int = 0

        # Logger via BaseUtil (Contrato 3 + Contrato 26)
        self._logger = BaseUtil._get_logger(self._tool_key, "ResourceGovernor")

        self._log_snapshot("ResourceGovernor inicializado")

    # ── Propriedades ─────────────────────────────────────────────────

    @property
    def policy(self) -> RamLimitPolicy:
        """Política de limite ativa."""
        return self._policy

    @property
    def warnings(self) -> int:
        """Número de warnings consecutivos."""
        return self._warnings

    @property
    def is_throttled(self) -> bool:
        """
        True se o número de warnings consecutivos excedeu MAX_WARNINGS,
        indicando que o sistema deve forçar pausa/cancelamento.
        """
        return self._warnings >= self.MAX_WARNINGS

    # ── Decisões ─────────────────────────────────────────────────────

    def can_execute(self, estimated_ram: int = 0) -> Tuple[bool, str]:
        """
        Verifica se há recursos suficientes para executar.

        Args:
            estimated_ram: RAM estimada necessária em bytes (0 = só headroom).

        Returns:
            (True, "") se pode executar.
            (False, "motivo") se não pode.
        """
        if not self._policy.is_available(estimated_ram):
            self._warnings += 1
            snap = self.snapshot()
            reason = (
                f"Memória insuficiente. "
                f"Headroom: {snap['headroom_human']}, "
                f"Limite: {snap['max_allowed_human']}, "
                f"Estimado: {snap['estimated_human']}, "
                f"Estratégia: {snap['policy_mode']} ({snap['policy_fraction']*100:.0f}%)"
            )
            self._log_warning(reason)

            if self.is_throttled:
                self._logger.error(
                    "Sistema sobrecarregado — múltiplos warnings consecutivos",
                    code="GOV_THROTTLED",
                    warnings=self._warnings,
                )

            return False, reason

        # Reset warnings se passou
        if self._warnings > 0:
            self._warnings = 0

        return True, ""

    def assert_can_execute(self, estimated_ram: int = 0) -> None:
        """
        Levanta ResourceExceededError se não puder executar.

        Raises:
            ResourceExceededError: Com snapshot do estado.
        """
        can, reason = self.can_execute(estimated_ram)
        if not can:
            raise ResourceExceededError(reason, snapshot=self.snapshot())

    # ── Ajuste de Tile ───────────────────────────────────────────────

    def recommended_tile_size(self, max_tile_points: int) -> int:
        """
        Ajusta o tamanho do tile baseado na RAM disponível.

        Quanto menor o headroom, menor o tile.
        Fórmula: tile_ajustado = max_tile_points * fator_headroom
        Onde fator_headroom = max(0.05, headroom / max_allowed_ram)

        Args:
            max_tile_points: Tamanho máximo original do tile (ex: 10_000_000).

        Returns:
            Tamanho ajustado (nunca menor que 5% do original).
        """
        max_ram = self._policy.max_allowed_ram()
        headroom = self._policy.available_headroom()

        if max_ram <= 0:
            fator = 0.05
        else:
            # Fator proporcional ao headroom disponível
            fator = max(0.05, headroom / max_ram)

        adjusted = int(max_tile_points * fator)

        # Não deixar cair abaixo de 5% do original
        min_tile = max(1, int(max_tile_points * 0.05))
        return max(min_tile, adjusted)

    # ── Snapshot ─────────────────────────────────────────────────────

    def snapshot(self, estimated_ram: int = 0) -> Dict[str, object]:
        """
        Estado completo para logging/diagnóstico.
        Inclui dados de RamGovernor + RamLimitPolicy + estimativa.
        """
        ram_snap = self._ram.snapshot()
        policy_snap = self._policy.snapshot()
        headroom = self._policy.available_headroom()

        return {
            "policy_mode": self._policy.mode.value,
            "policy_fraction": self._policy.fraction,
            "total_human": ram_snap["total_human"],
            "used_system_human": ram_snap["used_system_human"],
            "process_human": ram_snap["process_human"],
            "max_allowed_human": policy_snap.get("max_allowed_human", ""),
            "headroom_human": FormatUtils.format_size(max(0, headroom)),
            "estimated_human": FormatUtils.format_size(estimated_ram),
            "utilization_pct": policy_snap["utilization_pct"],
            "warnings": self._warnings,
            "is_throttled": self.is_throttled,
        }

    # ── Logging ──────────────────────────────────────────────────────

    def _log_snapshot(self, prefix: str = "") -> None:
        """Loga o snapshot atual em nível DEBUG."""
        snap = self.snapshot()
        msg = (
            f"{prefix} | "
            f"Sistema: {snap['used_system_human']}/{snap['total_human']} | "
            f"Processo: {snap['process_human']} | "
            f"Headroom: {snap['headroom_human']} | "
            f"Limite: {snap['policy_mode']} {snap['policy_fraction']*100:.0f}%"
        )
        self._logger.debug(msg, code="GOV_SNAPSHOT")

    def _log_warning(self, reason: str) -> None:
        """Loga warning de memória insuficiente."""
        self._logger.warning(
            reason,
            code="GOV_LOW_MEMORY",
            warnings=self._warnings,
        )