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
    progress_update:  Signal = Signal(float) # emitido para atualizar a barra de progresso (0-100)
    progress_reset:   Signal = Signal()      # emitido para resetar a barra de progresso
    project_changed:  Signal = Signal()      # emitido quando o projeto ativo é salvo/criado
    hud_show:         Signal = Signal(dict)  # emitido para exibir HUD loader: {"message": str}
    hud_update:       Signal = Signal(dict)  # emitido para atualizar HUD: {"message": str, "progress": float}
    hud_hide:         Signal = Signal()      # emitido para esconder HUD loader
    execution_started: Signal = Signal(str)  # emitido quando plugin inicia execução: tool_name
    execution_finished: Signal = Signal(str) # emitido quando plugin finaliza execução: tool_name
    execution_cancelled: Signal = Signal(str) # emitido quando plugin cancela execução: tool_name
