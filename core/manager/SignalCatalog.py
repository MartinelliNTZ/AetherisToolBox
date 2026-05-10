# -*- coding: utf-8 -*-
"""
SignalCatalog — Catálogo central de sinais do sistema.
========================================================
Define os sinais como atributos de uma classe QObject.
O SignalManager usa este catálogo para emitir/conectar sinais.

Uso:
    # Emitir um sinal
    SignalCatalog.tool_opened.emit("Console")

    # Conectar a um sinal
    SignalCatalog.tool_opened.connect(minha_funcao)
"""

from __future__ import annotations

from PySide6.QtCore import QObject, Signal


class SignalCatalog(QObject):
    """
    Catálogo de sinais do sistema.
    Todos os sinais são definidos como class attributes (Signal(...)).

    Esta classe NÃO deve ser instanciada — use diretamente os atributos
    de classe, que são válidos sem instância.
    """

    # ── Sinais ───────────────────────────────────────────────────────

    tool_opened:      Signal = Signal(str)   # emitido quando uma ferramenta é aberta
    tool_closed:      Signal = Signal(str)   # emitido quando uma ferramenta é fechada
    tool_focused:     Signal = Signal(str)   # emitido quando uma ferramenta ganha foco
    app_startup:      Signal = Signal()      # emitido quando a aplicação inicia
    app_shutdown:     Signal = Signal()      # emitido quando a aplicação encerra
    console_message:  Signal = Signal(str)   # emitido para exibir mensagem no console