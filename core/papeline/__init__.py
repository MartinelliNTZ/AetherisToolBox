# -*- coding: utf-8 -*-
"""
core/async — Sistema de Pipeline Assíncrono
============================================
Pipeline sequencial assíncrono composto por etapas (Steps) que são
executadas uma após a outra. Cada etapa pode executar uma tarefa
pesada em background thread e, ao finalizar, chama callbacks.

Componentes:
    - ExecutionContext: Estado compartilhado entre steps
    - BaseStep: Contrato abstrato para etapas da pipeline
    - BaseTask: Wrapper para execução em background thread
    - AsyncPipelineEngine: Orquestrador da execução sequencial
"""

from .ExecutionContext import ExecutionContext
from .BaseTask import BaseTask
from .BaseStep import BaseStep
from .AsyncPipelineEngine import AsyncPipelineEngine

__all__ = [
    "ExecutionContext",
    "BaseTask",
    "BaseStep",
    "AsyncPipelineEngine",
]