# -*- coding: utf-8 -*-
"""
BaseTask — Wrapper para execução de trabalho pesado em background
==================================================================
Classe base para tasks que executam trabalho em thread separada.
Fornece mecanismo de captura de exceções, callbacks de sucesso/erro
e resultado tipado.

A implementação concreta deve sobrescrever _run() com a lógica real.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Callable, Optional


class BaseTask(ABC):
    """
    Wrapper para execução de trabalho pesado em background thread.

    Fluxo interno:
        1. run() é executado em thread separada
        2. run() chama _run() com a lógica real
        3. Se _run() lançar exceção, captura em self.exception, retorna False
        4. Se _run() retornar True, self.result contém o resultado
        5. finished(success) é chamado na thread principal
        6. success=True → dispara on_success(self.result)
        7. success=False → dispara on_error(self.exception)

    Attributes:
        description: Descrição da task para logs/debug
        exception: Exceção capturada durante execução (None se bem-sucedido)
        result: Resultado produzido por _run()
        on_success: Callback opcional: on_success(result)
        on_error: Callback opcional: on_error(exception)
    """
    def __init__(self, description: str):
        self.description: str = description
        self.exception: Optional[Exception] = None
        self.result: Any = None
        self.on_success: Optional[Callable[[Any], None]] = None
        self.on_error: Optional[Callable[[Exception], None]] = None
        self._is_cancelled: bool = False

    @abstractmethod
    def _run(self) -> bool:
        """
        Lógica pesada executada em background.
        Deve retornar True se bem-sucedido, False se falhou.
        Define self.result com o resultado produzido.
        """
        ...

    def run(self) -> bool:
        """
        Método principal executado em thread separada.
        Não sobrescrever — sobrescreva _run().
        """
        try:
            if self._is_cancelled:
                return False
            success = self._run()
            return success
        except Exception as e:
            self.exception = e
            return False

    def finished(self, success: bool) -> None:
        """
        Chamado na thread principal após run() terminar.
        Dispara on_success ou on_error conforme o resultado.
        """
        if success:
            if self.on_success:
                self.on_success(self.result)
        else:
            if self.on_error:
                self.on_error(self.exception)
            else:
                import logging
                logging.warning(
                    f"[BaseTask] Task '{self.description}' error "
                    f"sem callback: {self.exception}"
                )

    def cancel(self) -> None:
        """Marca a task para cancelamento cooperativo."""
        self._is_cancelled = True

    @property
    def is_cancelled(self) -> bool:
        """True se a task foi marcada para cancelamento."""
        return self._is_cancelled

    def __repr__(self) -> str:
        status = "ok" if self.exception is None else f"error: {self.exception}"
        return f"<BaseTask '{self.description}' [{status}]>"