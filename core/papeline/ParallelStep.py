# -*- coding: utf-8 -*-
"""
ParallelStep — Step que executa múltiplos substeps em paralelo
================================================================
Permite rodar N steps concorrentemente. Cada substep cria sua
task, e todas as tasks rodam simultaneamente via ThreadPoolExecutor.

Uso:
    parallel = ParallelStep(
        steps=[StepA(), StepB(), StepC()],
        name="processar_lote",
        max_workers=4,
    )
    pipeline = AsyncPipelineEngine(
        steps=[parallel, StepFinalizar()],
        ...
    )
"""

from __future__ import annotations

import concurrent.futures
import threading
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

from .ExecutionContext import ExecutionContext
from .BaseStep import BaseStep
from core.governor.CpuGovernor import CpuGovernor
from .BaseTask import BaseTask


class ParallelTask(BaseTask):
    """
    Task que executa múltiplas subtasks em paralelo.

    Cada substep cria sua task, e todas rodam concorrentemente.
    O resultado é um dict: {"step_name": result, ...}
    Falhas individuais não param as outras (a menos que propagate_errors=True).
    """
    def __init__(
        self,
        steps: List[BaseStep],
        context: ExecutionContext,
        *,
        max_workers: int = None,
        propagate_errors: bool = False,
        description: str = "parallel",
    ):
        super().__init__(description=description)
        self._steps = steps
        self._context = context
        self._max_workers = min(
            max_workers or len(steps),
            CpuGovernor.max_workers(),
        )
        self._propagate_errors = propagate_errors

    def _run(self) -> bool:
        results: Dict[str, Any] = {}
        errors: Dict[str, Exception] = {}

        def _run_step(step: BaseStep) -> tuple[str, Any, Optional[Exception]]:
            """Executa um step e retorna (name, result, exception)."""
            try:
                if self._is_cancelled:
                    return step.name(), None, None

                if not step.should_run(self._context):
                    return step.name(), "SKIPPED", None

                task = step.create_task(self._context)
                if task is None:
                    result = step.run_inline(self._context)
                    step.on_success(self._context, result)
                    return step.name(), result, None

                task.on_success = lambda r, s=step: s.on_success(self._context, r)
                task.on_error = lambda e, s=step: s.on_error(self._context, e)
                success = task.run()
                if success:
                    return step.name(), task.result, None
                else:
                    exc = task.exception or RuntimeError(f"Step '{step.name()}' falhou")
                    step.on_error(self._context, exc)
                    return step.name(), None, exc
            except Exception as e:
                step.on_error(self._context, e)
                return step.name(), None, e

        with concurrent.futures.ThreadPoolExecutor(
            max_workers=self._max_workers, thread_name_prefix="parallel"
        ) as executor:
            futures = {
                executor.submit(_run_step, step): step
                for step in self._steps
            }

            for future in concurrent.futures.as_completed(futures):
                if self._is_cancelled:
                    break
                name, result, error = future.result()
                if error is not None:
                    errors[name] = error
                else:
                    results[name] = result

        # Se algum step falhou, decidir se propaga erro
        all_ok = len(errors) == 0
        if not all_ok and self._propagate_errors:
            self.exception = RuntimeError(
                f"Steps com erro: {', '.join(errors.keys())}"
            )
            return False

        self.result = {"results": results, "errors": errors}
        return True


class ParallelStep(BaseStep):
    """
    Step que agrupa N substeps executados em paralelo.

    Args:
        steps: Lista de steps a executar concorrentemente.
        name: Nome do step (para logs).
        max_workers: Máximo de threads simultâneas (default = len(steps)).
        propagate_errors: Se True, falha em qualquer substep para o step inteiro.
    """
    def __init__(
        self,
        steps: List[BaseStep],
        *,
        name: str = "parallel",
        max_workers: int = None,
        propagate_errors: bool = False,
    ):
        super().__init__()
        self._steps = steps
        self._name = name
        self._max_workers = max_workers
        self._propagate_errors = propagate_errors

    def name(self) -> str:
        return self._name

    def create_task(self, context: ExecutionContext) -> ParallelTask:
        return ParallelTask(
            steps=self._steps,
            context=context,
            max_workers=self._max_workers,
            propagate_errors=self._propagate_errors,
            description=f"parallel({len(self._steps)} steps)",
        )

    def on_success(self, context: ExecutionContext, result: Any) -> None:
        if isinstance(result, dict):
            context.set(f"{self._name}_results", result.get("results", {}))
            context.set(f"{self._name}_errors", result.get("errors", {}))

    def on_error(self, context: ExecutionContext, exception: Exception) -> None:
        context.add_error(exception)