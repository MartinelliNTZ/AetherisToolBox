# -*- coding: utf-8 -*-
"""
core/async/task — Implementações concretas de BaseTask
========================================================
Tasks assíncronas que executam trabalho pesado em background,
seguindo o padrão BaseTask do sistema de pipeline.

Tasks disponíveis:
    - MrkSinglePipelineTask: Processa 1 arquivo MRK (herda BaseTask)
    - DoclingPipelineTask: Converte documento via Docling (herda BaseTask)
"""

from .MrkSinglePipelineTask import MrkSinglePipelineTask
from .DoclingPipelineTask import DoclingPipelineTask

__all__ = [
    "MrkSinglePipelineTask",
    "DoclingPipelineTask",
]