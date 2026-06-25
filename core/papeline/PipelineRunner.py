# -*- coding: utf-8 -*-
"""
PipelineRunner — Executa AsyncPipelineEngine em QThread sem travar UI
======================================================================
Wrapper QThread que chama engine.start_non_blocking() em background.
Fornece sinais Qt para os plugins se conectarem.

Uso no plugin:
    runner = PipelineRunner(
        steps=[DoclingConvertStep(columnar=True)],
        context={"file_path": path},
        on_finished=self._on_done,
        on_error=self._on_error,
        parent=self,
    )
    runner.start()
"""

from __future__ import annotations

from typing import Any, Callable, Dict, List, Optional

from PySide6.QtCore import QThread, Signal

from .ExecutionContext import ExecutionContext
from .BaseStep import BaseStep
from .AsyncPipelineEngine import AsyncPipelineEngine


class PipelineRunner(QThread):
    """
    Executa uma pipeline em QThread, sem travar a UI.

    Sinais:
        finished_ok(object): ExecutionContext ao finalizar com sucesso.
        failed(str): Mensagem de erro.
    """

    finished_ok = Signal(object)  # ExecutionContext
    failed = Signal(str)

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

        self._engine = AsyncPipelineEngine(
            steps=self._steps,
            context=ctx,
            on_finished=lambda c: self.finished_ok.emit(c),
            on_error=lambda errors: self.failed.emit(
                str(errors[-1] if errors else "Erro desconhecido")
            ),
        )
        self._engine.start_non_blocking()

        # Mantém a thread viva até a pipeline terminar
        while self._engine.is_running:
            self.msleep(50)

        self._engine = None
