# -*- coding: utf-8 -*-
"""
DoclingWorker — QThread para conversão Docling em background
=============================================================
Executa DoclingEngine.convert() em thread separada e emite sinais
com o resultado. Pronto para uso com SignalManager no plugin.

Uso:
    worker = DoclingWorker(file_path, columnar=True, manual_columns=0)
    worker.finished_ok.connect(self._on_done)
    worker.failed.connect(self._on_error)
    worker.start()
"""

from __future__ import annotations

from PySide6.QtCore import QThread, Signal

from core.enum.ToolKey import ToolKey


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