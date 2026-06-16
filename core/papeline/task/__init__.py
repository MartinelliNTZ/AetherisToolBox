# -*- coding: utf-8 -*-
"""
core/async/task — Implementações concretas de BaseTask
========================================================
Tasks assíncronas que executam trabalho pesado em background,
seguindo o padrão BaseTask do sistema de pipeline.

Tasks disponíveis:
    - MrkSinglePipelineTask: Processa 1 arquivo MRK (herda BaseTask)
    - MrkSingleTask:         QThread para processar 1 MRK com dados
    - MrkBatchWorker:        QThread para processar N MRKs em lote
    - DoclingPipelineTask:   Converte documento via Docling (herda BaseTask)
    - DoclingWorkerTask:     QThread para conversão Docling
"""

from .MrkSinglePipelineTask import (
    MrkSinglePipelineTask,
    MrkSingleTask,
    MrkBatchWorker,
)
from .DoclingPipelineTask import (
    DoclingPipelineTask,
    DoclingWorkerTask,
)

__all__ = [
    "MrkSinglePipelineTask",
    "MrkSingleTask",
    "MrkBatchWorker",
    "DoclingPipelineTask",
    "DoclingWorkerTask",
]