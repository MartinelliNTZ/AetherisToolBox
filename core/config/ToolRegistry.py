# -*- coding: utf-8 -*-
"""
ToolRegistry — Registro centralizado de ferramentas (lazy loading)
===================================================================
Aqui ficam definidas TODAS as ferramentas do sistema.
Para adicionar uma nova, basta incluir uma entrada no metodo
``_register_defaults()``.

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

from core.enum.ToolKey import ToolKey
from core.enum.ToolType import ToolType
from core.model.Tool import Tool
from resources.IconManager import IconManager


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

    # ==================================================================
    # METODO PRINCIPAL — registra todas as ferramentas padrao
    # ==================================================================
    # Para adicionar uma NOVA ferramenta:
    #   1. Crie a classe widget em plugins/nome_da_tool/
    #   2. Adicione uma linha no dicionario _TOOL_DEFINITIONS abaixo
    #      com: nome, caminho do modulo, nome da classe, tooltip
    # ==================================================================

    # ──────────────────────────────────────────────────────────────────
    # Dicionario de definicoes de ferramentas
    # ──────────────────────────────────────────────────────────────────
    # Formato:
    #   "NomeAba": {
    #       "module": "plugins.pasta.arquivo",
    #       "class_name": "NomeDaClasse",
    #       "tooltip": "Descricao da ferramenta"
    #   }
    # ──────────────────────────────────────────────────────────────────

    _TOOL_DEFINITIONS: dict = {
        ToolKey.HOME: {
            "module": "plugins.home.home_tool",
            "class_name": "HomeTool",
            "tooltip": "Pagina inicial do Aetheris ToolBox",
            "tool_type": ToolType.SYSTEM,
            "icon_alias": "SYSTEM",
        },
        ToolKey.CONSOLE: {
            "module": "plugins.console.console_tool",
            "class_name": "ConsoleTool",
            "tooltip": "Console de execucao compartilhado",
            "tool_type": ToolType.SYSTEM,
            "icon_alias": "SYSTEM",
        },
        ToolKey.CLASSIFIER: {
            "module": "plugins.tensorflow_classifier.classification_tool",
            "class_name": "ClassificationTool",
            "tooltip": "Classificacao Raster com Redes Neurais (inativo)",
            "tool_type": ToolType.RASTER,
            "icon_alias": "RASTER",
        },
        ToolKey.LOGVIEWER: {
            "module": "plugins.log_viewer.log_viewer",
            "class_name": "LogViewerTool",
            "tooltip": "Visualizador de logs do sistema",
            "tool_type": ToolType.SYSTEM,
            "icon_alias": "SYSTEM",
        },
        # ── Exemplo de como adicionar uma nova ferramenta ─────────────
        # ToolKey.MINHA_FERRAMENTA: {
        #     "module": "plugins.minha_ferramenta.minha_ferramenta",
        #     "class_name": "MinhaFerramentaWidget",
        #     "tooltip": "Descricao da minha ferramenta",
        #     "tool_type": ToolType.VECTOR,
        #     "icon_alias": "VECTOR",
        # },
    }

    def register_default_tools(self) -> None:
        """
        Registra todas as ferramentas definidas em _TOOL_DEFINITIONS.
        Cada tool e registrada com lazy loading (factory).
        """
        for key, info in self._TOOL_DEFINITIONS.items():
            name = key.value  # ToolKey.HOME → "Home"
            if name not in self._tools:  # evita duplicatas
                tool_type = info.get("tool_type", ToolType.SYSTEM)
                icon_alias = info.get("icon_alias", "SYSTEM")
                self.register(
                    name=name,
                    widget_factory=self._make_factory(
                        info["module"], info["class_name"]
                    ),
                    tooltip=info["tooltip"],
                    tool_type=tool_type,
                    icon=IconManager.from_alias(icon_alias),
                )

    @staticmethod
    def _make_factory(module_path: str, class_name: str) -> Callable[[], QWidget]:
        """
        Retorna uma factory que importa e instancia a classe sob demanda.
        """

        def factory() -> QWidget:
            mod = __import__(module_path, fromlist=[class_name])
            cls = getattr(mod, class_name)
            return cls()

        return factory

    # ==================================================================
    # Metodos de registro (usados internamente por register_default_tools)
    # ==================================================================

    def register(
        self,
        name: str,
        widget_factory: Callable[[], QWidget],
        tooltip: str = "",
        tool_type: ToolType = ToolType.SYSTEM,
        icon: Optional[QIcon] = None,
    ) -> int:
        """
        Registra uma ferramenta no sistema com lazy loading.

        Parametros:
            name           : Nome unico da ferramenta (ex: "Home", "Console")
            widget_factory : Callable sem argumentos que retorna um QWidget.
            tooltip        : Texto de dica (opcional).
            tool_type      : Categoria visual (ToolType.SYSTEM, RASTER, etc.)
            icon           : QIcon personalizado.

        Retorna:
            Indice da ferramenta na ordem de registro.
        """
        if name in self._tools:
            raise ValueError(f"Tool '{name}' ja esta registrada.")
        tool = Tool(name=name, widget_factory=widget_factory, tooltip=tooltip,
                    tool_type=tool_type, icon=icon)
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

    def get_definitions(self) -> dict:
        """
        Retorna o dicionario de definicoes das ferramentas.
        Util para listar quais ferramentas estao disponiveis.
        """
        return dict(self._TOOL_DEFINITIONS)