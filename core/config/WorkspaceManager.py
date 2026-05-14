# -*- coding: utf-8 -*-
"""
WorkspaceManager — Gestor dos workspaces Central + Side
=========================================================
Responsabilidades:
  1. Criar e gerenciar o QSplitter entre CentralWorkspace e SideWorkspace
  2. Registrar ferramentas no workspace correto (CENTRAL, SIDE, BOTH)
  3. Roteamento de ativação de ferramentas para o workspace adequado
  4. Movimentação de ferramentas BOTH entre workspaces
  5. Persistência do tamanho do SideWorkspace
  6. Gerenciamento do redimensionamento do splitter

A MainWindow recebe o widget pronto e só o posiciona no layout.
"""

from __future__ import annotations

from typing import Dict, List, Optional

from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtWidgets import QWidget, QSplitter, QVBoxLayout

from core.enum.CategoryTool import CategoryTool
from core.enum.ToolKey import ToolKey
from core.model.Tool import Tool
from core.config.LogUtils import LogUtils
from core.ui.CentralWorkspace import CentralWorkspace
from core.ui.SideWorkspace import SideWorkspace
from utils.Preferences import Preferences


class WorkspaceManager(QWidget):
    """
    Gerencia CentralWorkspace + SideWorkspace.

    Uso:
        manager = WorkspaceManager(tools)
        manager.build()
        root_layout.addWidget(manager)
                                    # ^ é o próprio splitter

    Sinais:
        tool_activated — emitido quando uma ferramenta é ativada
    """

    tool_activated = Signal(str)

    def __init__(self, tools: List[Tool], parent=None):
        super().__init__(parent)
        self._tools: List[Tool] = tools
        self._tool_map: Dict[str, Tool] = {t.name: t for t in tools}
        self._sys_prefs = Preferences(section=ToolKey.SYSTEM.value)
        self.logger = LogUtils(tool="System", class_name="WorkspaceManager")

        # Widgets internos
        self._central_workspace: Optional[CentralWorkspace] = None
        self._side_workspace: Optional[SideWorkspace] = None
        self._splitter: Optional[QSplitter] = None

        # Estado do side
        self._side_content_width: int = SideWorkspace.W_DEFAULT
        self._drag_lock: bool = True

        self._build()

    # ────────────────────────────────────────────────────────────────
    # Construção
    # ────────────────────────────────────────────────────────────────

    def _build(self) -> None:
        """Constrói o splitter com os workspaces e registra as ferramentas."""
        log = LogUtils(tool="System", class_name="WorkspaceManager")
        log.info("Construindo workspaces", code="WS_BUILD", num_tools=len(self._tools))

        self._splitter = QSplitter(Qt.Orientation.Horizontal)
        self._splitter.setHandleWidth(4)
        self._splitter.setChildrenCollapsible(False)
        self._splitter.setObjectName("workspace_splitter")

        # Layout do WorkspaceManager: só contém o splitter
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(self._splitter, 1)

        # Central
        self._central_workspace = CentralWorkspace()
        self._splitter.addWidget(self._central_workspace)

        # Side
        self._side_workspace = SideWorkspace()
        self._splitter.addWidget(self._side_workspace)

        # Restaura largura salva
        saved = self._sys_prefs.get("side_content_width", SideWorkspace.W_DEFAULT)
        self._side_content_width = saved

        # Inicializa colapsado
        self._side_workspace.collapse()
        QTimer.singleShot(0, self._init_splitter_sizes)
        self._drag_lock = True

        # Conecta sinais do side
        self._side_workspace.size_changed.connect(self._on_side_size_changed)
        self._splitter.splitterMoved.connect(self._on_splitter_moved)

        # Conecta movimentação BOTH
        self._central_workspace.tool_request_move_to_side.connect(self._move_tool_to_side)
        self._side_workspace.tool_request_move_to_central.connect(self._move_tool_to_central)

        # Registra ferramentas nos workspaces
        for tool in self._tools:
            if tool.category == CategoryTool.SIDE:
                self._side_workspace.register_tool(tool)
            elif tool.category == CategoryTool.BOTH:
                self._side_workspace.register_tool(tool)
            elif tool.name == "Home":
                self._central_workspace.register_tool(tool, focus=False)

        # Abre Home
        self._central_workspace.set_current_tool("Home")

    # ────────────────────────────────────────────────────────────────
    # API pública para a MainWindow
    # ────────────────────────────────────────────────────────────────

    @property
    def central_workspace(self) -> CentralWorkspace:
        if self._central_workspace is None:
            raise RuntimeError("WorkspaceManager não foi construído.")
        return self._central_workspace

    @property
    def side_workspace(self) -> SideWorkspace:
        if self._side_workspace is None:
            raise RuntimeError("WorkspaceManager não foi construído.")
        return self._side_workspace

    def get_tool(self, name: str) -> Optional[Tool]:
        """Retorna uma tool pelo nome."""
        return self._tool_map.get(name)

    def open_tool(self, tool_name: str) -> None:
        """
        Abre ou foca uma ferramenta no workspace correto.
        Chamado quando o usuário clica na toolbar ou menu.
        """
        tool = self._tool_map.get(tool_name)
        if not tool:
            return

        if tool.category == CategoryTool.SIDE:
            self._side_workspace.open_tool(tool)
        elif tool.category == CategoryTool.BOTH:
            if self._side_workspace.is_tool_open(tool_name):
                self._side_workspace.open_tool(tool)
            else:
                self._central_workspace.open_tool(tool)
        else:
            self._central_workspace.open_tool(tool)

        self.tool_activated.emit(tool_name)

    def switch_to_tool(self, name: str) -> bool:
        """Muda para uma ferramenta já aberta."""
        if self._central_workspace.is_tool_open(name):
            self._central_workspace.set_current_tool(name)
            return True
        if self._side_workspace.is_tool_open(name):
            self._side_workspace.expand(name, self._side_content_width)
            return True
        return False

    def switch_to_console(self) -> None:
        """Atalho para abrir o Console."""
        self.switch_to_tool("Console")

    # ────────────────────────────────────────────────────────────────
    # Redimensionamento do splitter
    # ────────────────────────────────────────────────────────────────

    def _init_splitter_sizes(self):
        """Força o splitter para estado colapsado."""
        if self._splitter is None:
            return
        try:
            self._splitter.setSizes([
                max(100, self._splitter.width() - SideWorkspace.W_TABS),
                SideWorkspace.W_TABS,
            ])
        except Exception as e:
            self.logger.error("Falha ao inicializar tamanhos do splitter", code="SPLIT_INIT_ERR", error=str(e))

    def _on_side_size_changed(self, total_width: int):
        """Ajusta os tamanhos do splitter conforme SideWorkspace."""
        if self._splitter is None:
            return

        if total_width <= SideWorkspace.W_TABS:
            self._drag_lock = True
            self._splitter.setSizes([
                self._splitter.width() - SideWorkspace.W_TABS,
                SideWorkspace.W_TABS,
            ])
            prefs = Preferences(section=ToolKey.SYSTEM.value)
            prefs.set("side_collapsed", True)
            prefs.set("side_content_width", self._side_content_width)
            prefs.save()
        else:
            self._drag_lock = False
            self._splitter.setSizes([
                self._splitter.width() - total_width,
                total_width,
            ])

    def _on_splitter_moved(self, pos: int, idx: int):
        """Salva a largura do conteúdo side quando o usuário arrasta."""
        if self._drag_lock or self._splitter is None:
            return
        sizes = self._splitter.sizes()
        if len(sizes) >= 2:
            side_total = sizes[1]
            content_w = side_total - SideWorkspace.W_TABS
            if content_w > 20:
                self._side_content_width = content_w
                prefs = Preferences(section=ToolKey.SYSTEM.value)
                prefs.set("side_collapsed", False)
                prefs.set("side_content_width", content_w)
                prefs.save()

    # ────────────────────────────────────────────────────────────────
    # Movimentação BOTH entre workspaces
    # ────────────────────────────────────────────────────────────────

    def _move_tool_to_side(self, tool_name: str):
        """Move uma ferramenta BOTH do Central para o Side."""
        tool = self._tool_map.get(tool_name)
        if not tool:
            return
        self._central_workspace.remove_tool_by_name(tool_name, keep_widget=True)
        if not self._side_workspace.is_tool_open(tool_name):
            self._side_workspace.register_tool(tool)
        self._side_workspace.expand(tool_name, self._side_content_width)

    def _move_tool_to_central(self, tool_name: str):
        """Move uma ferramenta BOTH do Side para o Central."""
        tool = self._tool_map.get(tool_name)
        if not tool:
            return
        self._side_workspace.remove_tool(tool_name)
        if not self._central_workspace.is_tool_open(tool_name):
            self._central_workspace.open_tool(tool)