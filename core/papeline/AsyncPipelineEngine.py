# -*- coding: utf-8 -*-
"""
AsyncPipelineEngine — Orquestrador da execução sequencial dos steps
=====================================================================
Gerencia a execução sequencial dos steps, controlando o fluxo de
inicialização, callbacks de sucesso/erro e cancelamento.

Dois modos de execução:
  - Blocking (padrão): usa thread.join(), adequado para CLI/testes
  - Non-blocking: via PipelineRunner, usa QThread + callbacks
                  sem travar a UI (adequado para plugins Qt)
"""

from __future__ import annotations

import threading
from typing import Any, Callable, List, Optional

from core.governor.ResourceGovernor import ResourceGovernor
from .ExecutionContext import ExecutionContext
from .BaseStep import BaseStep
from .BaseTask import BaseTask


class AsyncPipelineEngine:
    """
    Orquestrador principal do pipeline assíncrono.

    Args:
        steps: Lista de steps a executar sequencialmente.
        context: ExecutionContext compartilhado.
        on_finished: Callback opcional quando pipeline termina com sucesso.
        on_error: Callback opcional quando ocorre erro.
        on_cancelled: Callback opcional quando pipeline é cancelada.
    """
    def __init__(
        self,
        steps: List[BaseStep],
        context: ExecutionContext,
        *,
        on_finished: Optional[Callable[[ExecutionContext], None]] = None,
        on_error: Optional[Callable[[List[Exception]], None]] = None,
        on_cancelled: Optional[Callable[[ExecutionContext], None]] = None,
        governor: Optional[ResourceGovernor] = None,
    ):
        self._steps = steps
        self._context = context
        self._on_finished = on_finished
        self._on_error = on_error
        self._on_cancelled = on_cancelled

        self._current_index: int = 0
        self._current_task: Optional[BaseTask] = None
        self._is_running: bool = False
        self._is_cancelled: bool = False
        self._lock = threading.Lock()
        self._governor = governor

    # ── Propriedades ───────────────────────────────────────────────

    @property
    def is_running(self) -> bool:
        return self._is_running

    @property
    def context(self) -> ExecutionContext:
        return self._context

    # ── Início ─────────────────────────────────────────────────────

    def start(self) -> None:
        """
        Inicia a pipeline em modo BLOCKING.
        Cada task roda em thread separada, mas a engine espera
        com join(). Adequado para CLI, testes e scripts.
        """
        if self._is_running:
            raise RuntimeError("Pipeline já está em execução.")

        self._is_running = True
        self._current_index = 0
        self._is_cancelled = False
        self._run_loop(blocking=True)

    def start_non_blocking(self) -> None:
        """
        Inicia a pipeline em modo NON-BLOCKING.
        A engine NÃO faz join() — as tasks disparam callbacks
        e a pipeline avança automaticamente.
        Use com PipelineRunner para rodar em QThread.
        """
        if self._is_running:
            raise RuntimeError("Pipeline já está em execução.")

        self._is_running = True
        self._current_index = 0
        self._is_cancelled = False
        self._run_loop(blocking=False)

    # ── Loop principal ─────────────────────────────────────────────

    def _run_loop(self, blocking: bool) -> None:
        """
        Executa os steps sequencialmente.

        Args:
            blocking: Se True, usa thread.join() (bloqueia).
                      Se False, callbacks disparam avanço automaticamente.
        """
        while self._is_running and not self._is_cancelled:
            # Verifica cancelamento
            if self._context.is_cancelled():
                self._finish_cancelled()
                return

            # Verifica recursos do sistema (governor)
            if self._governor is not None:
                can, reason = self._governor.can_execute()
                if not can:
                    self._context.add_error(RuntimeError(reason))
                    self._finish_error()
                    return

            # Verifica se acabaram os steps
            if self._current_index >= len(self._steps):
                self._finish_success()
                return

            step = self._steps[self._current_index]

            # Verifica se o step deve executar
            if not step.should_run(self._context):
                self._current_index += 1
                continue

            try:
                task = step.create_task(self._context)

                if task is None:
                    # Step síncrono inline
                    result = step.run_inline(self._context)
                    if result is not None or True:
                        try:
                            step.on_success(self._context, result)
                            self._current_index += 1
                            continue
                        except Exception as e:
                            self._handle_task_error(step, e)
                            return
                    else:
                        raise RuntimeError(
                            f"Step '{step.name()}' retornou None de create_task() "
                            f"e não implementa run_inline()."
                        )

                # Task assíncrona
                self._current_task = task
                task.on_success = lambda result: self._handle_task_success(step, result)
                task.on_error = lambda exc: self._handle_task_error(step, exc)

                if blocking:
                    # Modo blocking: executa e espera
                    success = task.run()
                    task.finished(success)
                else:
                    # Modo non-blocking: dispara thread e sai
                    # O callback finished() chama _handle_task_success/error
                    # que por sua vez chama _run_loop() de novo
                    self._run_task_non_blocking(task)
                    return  # Sai do while — callbacks retomam

            except Exception as e:
                self._handle_task_error(step, e)
                return

    def _run_task_non_blocking(self, task: BaseTask) -> None:
        """
        Dispara task em thread separada SEM fazer join().
        Quando a thread terminar, chama task.finished() que
        dispara on_success/on_error, que avançam a pipeline.
        """
        def _worker(t: BaseTask, engine: AsyncPipelineEngine):
            try:
                success = t.run()
                t.finished(success)
            except Exception:
                pass

        thread = threading.Thread(target=_worker, args=(task, self), daemon=True,
                                  name=f"task-{task.description}")
        thread.start()

    # ── Callbacks de Task (usados em modo non-blocking) ────────────

    def _handle_task_success(self, step: BaseStep, result: Any) -> None:
        """Callback quando uma task termina com sucesso."""
        try:
            step.on_success(self._context, result)
            self._current_index += 1
            self._current_task = None
            # Continua o loop
            self._run_loop(blocking=False)
        except Exception as e:
            self._handle_task_error(step, e)

    def _handle_task_error(self, step: Optional[BaseStep], exception: Exception) -> None:
        """Callback quando uma task falha."""
        if step is not None:
            step.on_error(self._context, exception)

        self._context.add_error(exception)
        self._current_task = None
        self._finish_error()

    # ── Finalizações ───────────────────────────────────────────────

    def _finish_success(self) -> None:
        """Pipeline concluída com sucesso."""
        self._is_running = False
        self._current_task = None

        if self._on_finished:
            self._on_finished(self._context)

    def _finish_error(self) -> None:
        """Pipeline interrompida por erro."""
        self._is_running = False
        self._current_task = None

        if self._on_error:
            self._on_error(self._context.get_errors())

    def _finish_cancelled(self) -> None:
        """Pipeline cancelada pelo usuário."""
        self._is_running = False
        self._current_task = None

        if self._on_cancelled:
            self._on_cancelled(self._context)

    # ── Cancelamento ───────────────────────────────────────────────

    def cancel(self) -> None:
        """Cancela a execução da pipeline (cancelamento cooperativo)."""
        self._is_cancelled = True
        self._context.cancel()

        if self._current_task is not None:
            self._current_task.cancel()

    def __repr__(self) -> str:
        return (
            f"<AsyncPipelineEngine "
            f"steps={len(self._steps)}, "
            f"current={self._current_index}, "
            f"running={self._is_running}, "
            f"cancelled={self._is_cancelled}>"
        )