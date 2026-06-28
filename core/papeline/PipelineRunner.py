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
    ):
        super().__init__(parent)
        self._steps = steps
        self._context_data = context or {}
        self._engine: AsyncPipelineEngine | None = None
        self._governor: ResourceGovernor | None = None

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

        # Cria ResourceGovernor interno para monitorar RAM
        # Política padrão: GLOBAL 90% (pode ser alterada futuramente)
        self._governor = ResourceGovernor(
            policy=RamLimitPolicy(
                mode=self._DEFAULT_MODE,
                fraction=self._DEFAULT_FRACTION,
            ),
        )

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