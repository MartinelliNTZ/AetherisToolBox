# -*- coding: utf-8 -*-
"""
BaseStep — Contrato abstrato que define uma etapa da pipeline
================================================================
Cada etapa (step) da pipeline implementa este contrato.
O step pode executar uma task assíncrona (via create_task) ou
executar síncrono inline (via run_inline).

Métodos obrigatórios:
    name() → Identificador único para logs/debug
    create_task(context) → Cria BaseTask (ou None para síncrono)
    on_success(context, result) → Callback após task bem-sucedida

Métodos opcionais:
    should_run(context) → Se False, step é pulado
    on_error(context, exception) → Tratamento específico de erro
    rollback(context) → Desfazer alterações em caso de erro
    run_inline(context) → Execução síncrona (se create_task retornar None)
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Optional

from core.config.LogUtils import LogUtils
from core.enum.ToolKey import ToolKey
from .ExecutionContext import ExecutionContext
from .BaseTask import BaseTask


class BaseStep(ABC):
    """Contrato que define uma etapa da pipeline."""

    def get_logger(self, context: ExecutionContext) -> LogUtils:
        """
        Retorna um LogUtils configurado com a tool_key do contexto.

        A tool_key é extraída do ExecutionContext via:
            context.get("tool_key", ToolKey.UNTRACEABLE.value)

        O class_name usado é o nome da classe concreta do step.
        """
        tool_key = context.get("tool_key", ToolKey.UNTRACEABLE.value)
        return LogUtils(tool=tool_key, class_name=self.__class__.__name__)

    # ── Obrigatórios ────────────────────────────────────────────────

    @abstractmethod
    def name(self) -> str:
        """Identificador único para logs/debug."""
        ...

    @abstractmethod
    def create_task(self, context: ExecutionContext) -> Optional[BaseTask]:
        """
        Cria e retorna uma instância de BaseTask para trabalho assíncrono.
        Pode retornar None se o step executar inline via run_inline().
        """
        ...

    @abstractmethod
    def on_success(self, context: ExecutionContext, result: Any) -> None:
        """
        Callback executado após a task terminar com sucesso.
        Recebe o resultado da task. Use para atualizar o contexto.
        """
        ...

    # ── Opcionais ───────────────────────────────────────────────────

    def should_run(self, context: ExecutionContext) -> bool:
        """
        Se retornar False, o step é pulado automaticamente.
        Útil para steps condicionais.
        """
        return True

    def on_error(self, context: ExecutionContext, exception: Exception) -> None:
        """
        Tratamento específico de erro do step antes de falhar a pipeline.
        Opcional — implementação padrão é vazia.
        """
        pass

    def rollback(self, context: ExecutionContext) -> None:
        """
        Lógica para desfazer alterações em caso de erro.
        Não é chamado automaticamente — fica a critério de quem implementa.
        """
        pass

    def run_inline(self, context: ExecutionContext) -> Optional[Any]:
        """
        Execução síncrona inline quando create_task() retornar None.
        Se não implementado, a pipeline lançará RuntimeError quando
        create_task() retornar None e não houver run_inline().
        """
        return None

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} '{self.name()}'>"