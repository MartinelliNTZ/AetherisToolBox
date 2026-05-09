# -*- coding: utf-8 -*-
"""
Tool — Modelo de ferramenta com lazy loading
==============================================
Cada ferramenta (tool) no Aetheris ToolBox é representada por uma
instância de Tool, que só instancia o widget QWidget sob demanda
(lazy loading) para evitar importações desnecessárias na inicialização.
"""

from __future__ import annotations

from typing import Any, Callable, Optional

from PySide6.QtWidgets import QWidget


class Tool:
    """
    Representa uma ferramenta registrada no sistema.

    O widget QWidget real **só é criado** quando a propriedade ``widget``
    é acessada pela primeira vez. Isso permite registrar dezenas de
    ferramentas sem impacto na memória/tempo de inicialização.

    Uso:
        tool = Tool(
            name="Console",
            widget_factory=lambda: ConsoleTool(),
            tooltip="Console de execução"
        )
        w = tool.widget  # ← cria o widget aqui, na primeira vez
    """

    def __init__(
        self,
        name: str,
        widget_factory: Callable[[], QWidget],
        tooltip: str = "",
    ) -> None:
        """
        Parâmetros:
            name           : Nome visível da ferramenta (ex: "Console", "Home")
            widget_factory : Callable sem argumentos que retorna um QWidget.
                             Só será chamado quando ``self.widget`` for acessado.
            tooltip        : Texto de dica ao passar o mouse (opcional).
        """
        self._name = name
        self._factory = widget_factory
        self._tooltip = tooltip
        self._widget: Optional[QWidget] = None

    # ────────────────────────────────────────────────────────────────────────
    # Propriedades públicas
    # ────────────────────────────────────────────────────────────────────────

    @property
    def name(self) -> str:
        """Nome da ferramenta."""
        return self._name

    @property
    def widget(self) -> QWidget:
        """
        Retorna o widget da ferramenta, criando-o sob demanda (lazy).
        A factory é chamada apenas na primeira vez.
        """
        if self._widget is None:
            self._widget = self._factory()
        return self._widget

    @property
    def is_loaded(self) -> bool:
        """True se o widget já foi instanciado."""
        return self._widget is not None

    @property
    def tooltip(self) -> str:
        """Texto de dica da ferramenta."""
        return self._tooltip

    # ────────────────────────────────────────────────────────────────────────
    # Métodos úteis
    # ────────────────────────────────────────────────────────────────────────

    def to_dict(self) -> dict:
        """
        Retorna representação serializável (útil para debug).
        """
        return {
            "name": self._name,
            "tooltip": self._tooltip,
            "loaded": self.is_loaded,
        }

    def unload(self) -> None:
        """
        Descarrega o widget, liberando memória.
        Útil para ferramentas que ficam ocultas por muito tempo.
        O widget será recriado na próxima vez que ``self.widget`` for acessado.
        """
        if self._widget is not None:
            self._widget.deleteLater()
            self._widget = None

    def __repr__(self) -> str:
        return (
            f"Tool(name={self._name!r}, loaded={self.is_loaded}, "
            f"tooltip={self._tooltip!r})"
        )