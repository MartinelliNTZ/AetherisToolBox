# -*- coding: utf-8 -*-
"""
DoclingSteps — Steps concretos para pipeline de conversão Docling
===================================================================
Steps que compõem uma pipeline completa de conversão de documentos
via Docling.

Pipeline Docling completa:
    1. DoclingConvertStep → Converte documento para Markdown
    2. DoclingSaveStep → Salva o Markdown em arquivo .md
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Optional

from ..ExecutionContext import ExecutionContext
from ..BaseTask import BaseTask
from ..BaseStep import BaseStep
from ..task.DoclingPipelineTask import DoclingPipelineTask


class DoclingConvertStep(BaseStep):
    """
    Step que converte um documento para Markdown via Docling.

    Context requer:
        - "file_path": Caminho do documento a converter

    Context produz:
        - "markdown": Conteúdo Markdown gerado
    """
    def __init__(self, columnar: bool = False, manual_columns: int = 0):
        super().__init__()
        self._columnar = columnar
        self._manual_columns = manual_columns

    def name(self) -> str:
        return "docling_convert"

    def create_task(self, context: ExecutionContext) -> DoclingPipelineTask:
        return DoclingPipelineTask(
            file_path=str(context.get("file_path")),
            columnar=self._columnar,
            manual_columns=self._manual_columns,
        )

    def on_success(self, context: ExecutionContext, result: Any) -> None:
        if isinstance(result, dict):
            context.set("markdown", result.get("markdown", ""))
            context.set("output_name", result.get("output_name", ""))


class DoclingSaveStep(BaseStep):
    """
    Step que salva o Markdown gerado em arquivo .md no disco.

    Context requer:
        - "markdown": Conteúdo Markdown (produzido por DoclingConvertStep)
        - "output_dir": Diretório de saída

    Context produz:
        - "saved_path": Caminho do arquivo .md salvo
    """
    def name(self) -> str:
        return "docling_save"

    def should_run(self, context: ExecutionContext) -> bool:
        return context.has("markdown") and bool(context.get("markdown"))

    def create_task(self, context: ExecutionContext) -> None:
        return None  # Síncrono

    def run_inline(self, context: ExecutionContext) -> Optional[str]:
        markdown = str(context.get("markdown", ""))
        if not markdown.strip():
            return None

        output_dir = Path(str(context.get("output_dir", ".")))
        output_dir.mkdir(parents=True, exist_ok=True)

        output_name = str(context.get("output_name", "output.md"))
        output_path = output_dir / output_name

        try:
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(markdown)
            return str(output_path)
        except Exception as e:
            context.add_error(e)
            return None

    def on_success(self, context: ExecutionContext, result: Any) -> None:
        if result:
            context.set("saved_path", result)

    def on_error(self, context: ExecutionContext, exception: Exception) -> None:
        context.add_error(exception)