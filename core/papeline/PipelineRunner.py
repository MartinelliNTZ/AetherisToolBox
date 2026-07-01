# -*- coding: utf-8 -*-
"""
PipelineRunner — Executa AsyncPipelineEngine em QThread sem travar UI
======================================================================
Wrapper QThread que chama engine.start_non_blocking() em background.
Fornece sinais Qt para os plugins se conectarem.

Cria automaticamente um ResourceGovernor interno para monitorar
e limitar o uso de RAM, evitando OOM. O plugin não precisa saber
da existência do governor.

Uso no plugin:
    runner = PipelineRunner(
        steps=[DoclingConvertStep(columnar=True)],
        context={"file_path": path},
        parent=self,
    )
    runner.start()
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from PySide6.QtCore import QThread, Signal

from core.governor.RamLimitPolicy import RamLimitPolicy, RamLimitMode
from core.governor.CpuGovernor import CpuGovernor
from core.governor.ResourceGovernor import ResourceGovernor
from .ExecutionContext import ExecutionContext
from .BaseStep import BaseStep
from .AsyncPipelineEngine import AsyncPipelineEngine


class PipelineRunner(QThread):
    """
    Executa uma pipeline em QThread, sem travar a UI.

    Cria internamente um ResourceGovernor com política padrão
    (GLOBAL 90%) que monitora RAM e pode bloquear a execução
    se os recursos forem insuficientes.

    Sinais:
        finished_ok(object): ExecutionContext ao finalizar com sucesso.
        failed(str): Mensagem de erro.
    """

    finished_ok = Signal(object)  # ExecutionContext
    failed = Signal(str)

    # Política padrão do governor
    _DEFAULT_MODE = RamLimitMode.GLOBAL
    _DEFAULT_FRACTION = 0.90

    def __init__(
        self,
        steps: List[BaseStep],
        context: Optional[Dict[str, Any]] = None,
        *,
        parent=None,
        governor: Optional[ResourceGovernor] = None,
        governor_mode: RamLimitMode = _DEFAULT_MODE,
        governor_fraction: float = _DEFAULT_FRACTION,
    ):
        super().__init__(parent)
        self._steps = steps
        self._context_data = context or {}
        self._engine: AsyncPipelineEngine | None = None
        self._governor: Optional[ResourceGovernor] = governor
        self._governor_mode = governor_mode
        self._governor_fraction = governor_fraction

    @property
    def engine(self) -> AsyncPipelineEngine | None:
        return self._engine

    def cancel(self) -> None:
        """
        Cancela a execução da pipeline em andamento.
        Delega para AsyncPipelineEngine.cancel() que faz cancelamento
        cooperativo (marca flag + cancela task atual).
        """
        if self._engine is not None:
            self._engine.cancel()

    def run(self) -> None:
        """Executa a pipeline em background thread."""
        ctx = ExecutionContext(self._context_data)

        # Injeta referencia do governor no contexto para steps/tasks
        # A task concreta pode extrair via context.get("_governor") e usar:
        #   - can_execute(estimated_ram) para bloqueio proativo
        #   - check_during_execution() para verificacao periodica
        #   - recommended_tile_size() para ajustar tiles

        # Cria ResourceGovernor (custom ou padrao GLOBAL 90%)
        if self._governor is None:
            self._governor = ResourceGovernor(
                policy=RamLimitPolicy(
                    mode=self._governor_mode,
                    fraction=self._governor_fraction,
                ),
            )

        # Disponibiliza governor para steps/tasks via contexto
        ctx.set("_governor", self._governor)

        # Disponibiliza CpuGovernor para steps/tasks que queiram consultar
        ctx.set("_cpu_governor", CpuGovernor)

        self._engine = AsyncPipelineEngine(
            steps=self._steps,
            context=ctx,
            on_finished=lambda c: self.finished_ok.emit(c),
            on_error=lambda errors: self.failed.emit(
                str(errors[-1] if errors else "Erro desconhecido")
            ),
            governor=self._governor,
        )
        self._engine.start_non_blocking()

        # Mantém a thread viva até a pipeline terminar
        while self._engine.is_running:
            self.msleep(50)

        self._engine = None
        self._governor = None