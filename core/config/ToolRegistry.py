# -*- coding: utf-8 -*-
"""
ToolRegistry — Registro centralizado de ferramentas (lazy loading)
===================================================================
Aqui ficam definidas TODAS as ferramentas do sistema.
Cada ferramenta é um objeto Tool com lazy loading via widget_factory.

Uso:
    registry = ToolRegistry()
    registry.register_default_tools()
    tools = registry.get_all()       # lista de objetos Tool
    widget = tools[0].widget          # lazy: cria aqui
"""

from __future__ import annotations

from typing import Callable, List, Optional

from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QWidget

from core.enum.CategoryTool import CategoryTool
from core.enum.ToolKey import ToolKey
from core.enum.ToolType import ToolType
from core.model.Tool import Tool


def _make_factory(module_path: str, class_name: str) -> Callable[[], QWidget]:
    """
    Retorna uma factory que importa e instancia a classe sob demanda.
    Função no nível do módulo para ser usada na definição do dict _TOOLS.
    """

    def factory() -> QWidget:
        mod = __import__(module_path, fromlist=[class_name])
        cls = getattr(mod, class_name)
        return cls()

    return factory


class ToolRegistry:
    """
    Singleton que mantém o registro de todas as ferramentas disponiveis.

    Cada tool e um objeto Tool com lazy loading via widget_factory.
    """

    _instance: ToolRegistry | None = None

    def __new__(cls) -> ToolRegistry:
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._tools: dict[str, Tool] = {}
            cls._instance._order: list[str] = []
        return cls._instance

    # ══════════════════════════════════════════════════════════════════
    # Definição direta de todas as ferramentas como objetos Tool
    # ══════════════════════════════════════════════════════════════════
    # Para adicionar uma NOVA ferramenta:
    #   1. Crie a classe widget em plugins/nome_da_tool/
    #   2. Adicione uma entrada no dict _TOOLS abaixo
    #      com Tool() contendo name, title, widget_factory, etc.
    # ══════════════════════════════════════════════════════════════════

    _TOOLS: dict[str, Tool] = {
        ToolKey.HOME.value: Tool(
            name=ToolKey.HOME.value,
            title="Home",
            widget_factory=_make_factory(
                "plugins.home.HomePlugin", "HomeTool"
            ),
            tooltip="Pagina inicial do Aetheris ToolBox",
            tool_type=ToolType.SYSTEM,
            category=CategoryTool.CENTRAL,
        ),
        ToolKey.CONSOLE.value: Tool(
            name=ToolKey.CONSOLE.value,
            title="Console",
            widget_factory=_make_factory(
                "plugins.console.ConsolePlugin", "ConsoleTool"
            ),
            tooltip="Console de execucao compartilhado",
            tool_type=ToolType.SYSTEM,
            category=CategoryTool.SIDE,
        ),
        ToolKey.LOGVIEWER.value: Tool(
            name=ToolKey.LOGVIEWER.value,
            title="LogViewer",
            widget_factory=_make_factory(
                "plugins.log_viewer.log_viewer", "LogViewerTool"
            ),
            tooltip="Visualizador de logs do sistema",
            tool_type=ToolType.SYSTEM,
            category=CategoryTool.BOTH,
        ),
        ToolKey.CLASSIFIER.value: Tool(
            name=ToolKey.CLASSIFIER.value,
            title="TensorFlow Classifier",
            widget_factory=_make_factory(
                "plugins.tensorflow_classifier.classification_tool",
                "ClassificationTool",
            ),
            tooltip="Classificacao Raster com Redes Neurais (inativo)",
            tool_type=ToolType.RASTER,
            category=CategoryTool.CENTRAL,
        ),
        ToolKey.TECLADOR_F.value: Tool(
            name=ToolKey.TECLADOR_F.value,
            title="Teclador F",
            widget_factory=_make_factory(
                "plugins.teclador_f.TecladorF", "TecladorF"
            ),
            tooltip="Automacao de teclado: digita uma string ao pressionar F",
            tool_type=ToolType.FOLDER,
            category=CategoryTool.CENTRAL,
        ),
    }

    def register_default_tools(self) -> None:
        """Registra todas as ferramentas definidas em _TOOLS."""
        for name, tool in self._TOOLS.items():
            if name not in self._tools:  # evita duplicatas
                self._tools[name] = tool
                self._order.append(name)

    # ==================================================================
    # Metodos de registro direto
    # ==================================================================

    def register(
        self,
        name: str,
        widget_factory: Callable[[], QWidget],
        *,
        title: str | None = None,
        tooltip: str = "",
        tool_type: ToolType = ToolType.SYSTEM,
        category: CategoryTool = CategoryTool.CENTRAL,
        icon: Optional[QIcon] = None,
    ) -> int:
        """
        Registra uma ferramenta no sistema com lazy loading.

        Parametros:
            name           : Chave unica da ferramenta (ex: "Home", "Console")
            widget_factory : Callable sem argumentos que retorna um QWidget.
            title          : Nome exibido nas abas/titulos. Se None, usa name.
            tooltip        : Texto de dica (opcional).
            tool_type      : Categoria visual (ToolType.SYSTEM, RASTER, etc.)
            category       : Onde exibir (WORKSPACE ou SIDE).
            icon           : QIcon personalizado.

        Retorna:
            Indice da ferramenta na ordem de registro.
        """
        if name in self._tools:
            raise ValueError(f"Tool '{name}' ja esta registrada.")
        tool = Tool(
            name=name,
            title=title or name,
            widget_factory=widget_factory,
            tooltip=tooltip,
            tool_type=tool_type,
            category=category,
            icon=icon,
        )
        self._tools[name] = tool
        self._order.append(name)
        return len(self._order) - 1

    def unregister(self, name: str) -> bool:
        """Remove uma ferramenta pelo nome. Retorna True se removeu."""
        tool = self._tools.pop(name, None)
        if tool is None:
            return False
        tool.unload()
        self._order.remove(name)
        return True

    # ==================================================================
    # Consulta
    # ==================================================================

    def get_all(self) -> List[Tool]:
        """Retorna lista de objetos Tool na ordem de registro."""
        return [self._tools[name] for name in self._order]

    def get(self, name: str) -> Optional[Tool]:
        """Retorna um objeto Tool pelo nome, ou None."""
        return self._tools.get(name)

    def count(self) -> int:
        """Quantidade de ferramentas registradas."""
        return len(self._tools)

    def names(self) -> List[str]:
        """Lista dos nomes de todas as ferramentas na ordem de registro."""
        return list(self._order)