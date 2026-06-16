# -*- coding: utf-8 -*-
"""
DoclingPipelineTask — Task para conversão Docling no padrão BaseTask + QThread Worker
=====================================================================================
Arquivo unificado contendo:
  - DoclingPipelineTask (BaseTask)   → usado na pipeline assíncrona
  - DoclingWorkerTask   (QThread)    → usado diretamente pelo DoclingPlugin

Uso na pipeline:
    class DoclingConvertStep(BaseStep):
        def create_task(self, context):
            return DoclingPipelineTask(...)

Uso no plugin:
    worker = DoclingWorkerTask(file_path, ...)
    worker.finished_ok.connect(self._on_done)
    worker.start()
"""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QThread, Signal

from ..BaseTask import BaseTask
from core.enum.ToolKey import ToolKey


# ═══════════════════════════════════════════════════════════════════
# DoclingPipelineTask  (BaseTask — pipeline assíncrona)
# ═══════════════════════════════════════════════════════════════════

class DoclingPipelineTask(BaseTask):
    """
    Task para conversão de documentos via Docling.
    Herda de BaseTask para uso no sistema de pipeline assíncrono.

    Args:
        file_path: Caminho do arquivo a converter.
        columnar: Se True, preserva layout colunar.
        manual_columns: Número manual de colunas (0 = automático).
    """
    def __init__(
        self,
        file_path: str,
        *,
        columnar: bool = False,
        manual_columns: int = 0,
    ):
        super().__init__(description=f"Converter: {Path(file_path).name}")
        self._file_path = file_path
        self._columnar = columnar
        self._manual_columns = manual_columns

    # ── BaseTask ─────────────────────────────────────────────────────

    def _run(self) -> bool:
        """Executa a conversão Docling em background."""
        try:
            from plugins.docling.DoclingEngine import DoclingEngine

            md = DoclingEngine.convert(
                self._file_path,
                columnar=self._columnar,
                manual_columns=self._manual_columns,
                tool_key="DoclingPipeline",
            )
            self.result = {
                "path": self._file_path,
                "markdown": md,
                "output_name": Path(self._file_path).stem + ".md",
            }
            return True
        except FileNotFoundError as e:
            self.exception = e
            return False
        except RuntimeError as e:
            self.exception = e
            return False
        except MemoryError as e:
            self.exception = RuntimeError(f"Memória insuficiente: {e}")
            return False
        except Exception as e:
            self.exception = RuntimeError(f"Erro inesperado: {e}")
            return False


# ═══════════════════════════════════════════════════════════════════
# DoclingWorkerTask  (QThread — usado diretamente pelo plugin)
# ═══════════════════════════════════════════════════════════════════

class DoclingWorkerTask(QThread):
    """
    Worker thread para conversão de documentos via Docling.

    Sinais:
        finished_ok(str): Markdown gerado com sucesso.
        failed(str): Mensagem de erro.
    """

    finished_ok = Signal(str)
    failed = Signal(str)

    def __init__(
        self,
        file_path: str,
        *,
        columnar: bool = False,
        manual_columns: int = 0,
        tool_key: str = ToolKey.UNTRACEABLE.value,
        parent=None,
    ) -> None:
        super().__init__(parent)
        self._file_path = file_path
        self._columnar = columnar
        self._manual_columns = manual_columns
        self._tool_key = tool_key

    def run(self) -> None:
        """Executa a conversão em background."""
        try:
            from plugins.docling.DoclingEngine import DoclingEngine

            md = DoclingEngine.convert(
                self._file_path,
                columnar=self._columnar,
                manual_columns=self._manual_columns,
                tool_key=self._tool_key,
            )
            self.finished_ok.emit(md)
        except FileNotFoundError as e:
            self.failed.emit(str(e))
        except RuntimeError as e:
            self.failed.emit(str(e))
        except MemoryError as e:
            self.failed.emit(f"Memória insuficiente: {e}")
        except Exception as e:
            self.failed.emit(f"Erro inesperado: {e}")