# -*- coding: utf-8 -*-
"""
MenuManager — Construtor e gestor da toolbar + barra de menus
================================================================
Responsabilidades:
  1. Ler o ToolRegistry e obter a lista completa de ferramentas
  2. Agrupar por ToolType para criar ToolGroups (toolbar)
  3. Instanciar FileMenuItem, SystemMenuItem, HelpMenuItem
  4. Montar a MenuBar com os items e conectar sinais
  5. Encapsular MenuBar, Toolbar e seus sinais em um único lugar

  A MainWindow apenas posiciona os widgets prontos.

  O MenuManager também gerencia a lógica de "Novo", "Abrir" e "Salvar como"
  do menu Arquivo, pois essas ações pertencem ao fluxo de projeto global
  (não a um plugin específico).
"""

from __future__ import annotations

import os
from typing import Dict, List, Optional

from PySide6.QtCore import Signal, QObject
from PySide6.QtWidgets import QWidget, QHBoxLayout

from core.config.LogUtils import LogUtils
from core.config.ToolRegistry import ToolRegistry
from core.enum.ToolKey import ToolKey
from core.enum.ToolType import ToolType
from core.manager.SignalManager import SignalManager
from core.menus.FileMenuItem import FileMenuItem
from core.menus.SystemMenuItem import SystemMenuItem
from core.menus.HelpMenuItem import HelpMenuItem
from core.model.Tool import Tool
from resources.widgets.MenuBar import MenuBar
from resources.widgets.ToolGroup import ToolGroup
from resources.widgets.ToolBar import ToolBar
from utils.ExplorerUtils import ExplorerUtils
from utils.MessageBox import MessageBox
from utils.Preferences import Preferences
from utils.ProjectUtil import ProjectUtil
from utils.RecentProjectsManager import RecentProjectsManager


class MenuManager(QObject):
    """
    Constrói e gerencia a toolbar E a barra de menus.

    Uso:
        manager = MenuManager()
        manager.build()
        root_layout.addWidget(manager.menu_bar)
        root_layout.addWidget(manager.toolbar_widget)

    Sinais:
        tool_activated — emitido quando o usuário clica em uma ferramenta
                         (seja na toolbar ou no menu)
    """

    tool_activated = Signal(str)  # nome da ferramenta selecionada

    _MTL_FILTER = "Projeto Aetheris (*.mtl)"

    def __init__(self, parent=None):
        super().__init__(parent)
        self._groups: list[ToolGroup] = []
        self._menu_bar: Optional[MenuBar] = None
        self._toolbar_widget: Optional[QWidget] = None
        self._logger = LogUtils(tool=ToolKey.SYSTEM.value, class_name="MenuManager")
        self._recent_manager = RecentProjectsManager()

    # ────────────────────────────────────────────────────────────────
    # API pública
    # ────────────────────────────────────────────────────────────────

    def build(self) -> None:
        """
        Constrói a toolbar (ToolGroups) e popula o MenuBar.
        Chame este método antes de acessar .menu_bar e .toolbar_widget.
        """
        registry = ToolRegistry()
        tools = registry.get_all()

        # ── 1. Criar MenuBar ──
        self._menu_bar = MenuBar()

        # ── 2. Criar e registrar FileMenuItem ──
        self._file_item = FileMenuItem()
        self._file_item.novo_clicked.connect(self._on_novo)
        self._file_item.abrir_clicked.connect(self._on_abrir)
        self._file_item.salvar_como_clicked.connect(self._on_salvar_como)
        self._file_item.recente_clicked.connect(self._on_recente_abrir)
        self._file_item.sair_clicked.connect(self._on_sair)
        # Atualiza o submenu de recentes em tempo real via sinal dedicado
        SignalManager.instance().recent_projects_changed.connect(
            self._file_item.rebuild_recentes_from_signal
        )
        self._menu_bar.add_menu_item(self._file_item)

        # ── 3. Criar e registrar SystemMenuItem ──
        self._system_item = SystemMenuItem()
        self._system_item.refresh_tools()
        self._system_item.tool_clicked.connect(self._on_tool_clicked)
        self._menu_bar.add_menu_item(self._system_item)

        # ── 4. Criar e registrar HelpMenuItem ──
        self._help_item = HelpMenuItem()
        self._help_item.sobre_clicked.connect(self._on_sobre)
        self._menu_bar.add_menu_item(self._help_item)

        # Conecta sinal genérico do MenuBar (fallback para cliques não tratados)
        self._menu_bar.action_triggered.connect(self._on_menu_action)

        # ── 5. Criar ToolGroups (toolbar) ──
        grouped: Dict[ToolType, list[Tool]] = {}
        for tool in tools:
            if not tool.show_in_toolbar:
                continue
            tt = tool.tool_type
            if tt not in grouped:
                grouped[tt] = []
            grouped[tt].append(tool)

        self._groups.clear()
        for tool_type in ToolType:
            if tool_type in grouped and grouped[tool_type]:
                group = ToolGroup(tool_type=tool_type, tools=grouped[tool_type])
                self._groups.append(group)

        # ── 6. Montar toolbar_widget via ToolBar ──
        if self._groups:
            self._toolbar_widget = ToolBar(groups=self._groups)
            self._toolbar_widget.tool_clicked.connect(self._on_tool_clicked)
        else:
            self._toolbar_widget = QWidget()
            self._toolbar_widget.setVisible(False)

    # ────────────────────────────────────────────────────────────────
    # Widgets prontos
    # ────────────────────────────────────────────────────────────────

    @property
    def menu_bar(self) -> MenuBar:
        """Barra de menus pronta para ser adicionada ao layout."""
        if self._menu_bar is None:
            raise RuntimeError("Chame build() antes de acessar menu_bar.")
        return self._menu_bar

    @property
    def toolbar_widget(self) -> QWidget:
        """Widget da toolbar pronto para ser adicionado ao layout."""
        if self._toolbar_widget is None:
            raise RuntimeError("Chame build() antes de acessar toolbar_widget.")
        return self._toolbar_widget

    @property
    def tool_groups(self) -> list[ToolGroup]:
        """Lista dos ToolGroups criados (útil para inspeção)."""
        return list(self._groups)

    # ────────────────────────────────────────────────────────────────
    # Sinais internos (conectados pela MainWindow)
    # ────────────────────────────────────────────────────────────────

    sair_clicked = Signal()
    sobre_clicked = Signal()

    # ────────────────────────────────────────────────────────────────
    # Lógica do menu Arquivo
    # ────────────────────────────────────────────────────────────────

    def _on_novo(self) -> None:
        """Novo projeto: zera current_project e root_folder nas prefs e emite project_changed."""
        try:
            self._logger.info("Criando novo projeto em branco", code="MENU_NOVO")

            # Salva current_project e root_folder como string vazia
            Preferences.save_tool_prefs(ToolKey.SYSTEM, {
                "current_project": "",
                "root_folder": "",
            })

            # Emite sinal para FileManager recarregar com estado vazio
            SignalManager.instance().project_changed.emit()
            MessageBox.show_info(
                "Projeto em branco criado.\n"
                "Use 'Salvar como' para definir local e nome.",
                title="Novo Projeto",
            )
        except Exception as e:
            self._logger.error(
                "Erro ao criar novo projeto", code="MENU_NOVO_ERR", error=str(e),
            )
            MessageBox.show_error(
                "Erro ao criar novo projeto", title="Novo Projeto", detail=str(e),
            )

    def _on_abrir(self) -> None:
        """Abrir projeto: seleciona .mtl, carrega prefs e emite project_changed."""
        try:
            self._logger.info("Abrindo projeto existente", code="MENU_ABRIR")

            file_path = ExplorerUtils.open_file(
                title="Abrir projeto",
                file_filter=self._MTL_FILTER,
                parent=self.parent(),
            )
            if not file_path:
                return  # usuário cancelou

            # Carrega o .mtl para validar
            project_data = ProjectUtil.load_project(file_path)
            if project_data is None:
                self._logger.warning(
                    "Arquivo .mtl inválido", code="MENU_ABRIR_INVALIDO",
                    file_path=file_path,
                )
                MessageBox.show_error(
                    f"O arquivo '{file_path}' não é um projeto válido.",
                    title="Abrir Projeto",
                )
                return

            # Salva nas preferências do sistema
            sys_prefs = Preferences.load_tool_prefs(ToolKey.SYSTEM)
            sys_prefs["current_project"] = file_path
            sys_prefs["root_folder"] = os.path.dirname(file_path)
            Preferences.save_tool_prefs(ToolKey.SYSTEM, sys_prefs)

            # Atualiza last_modified
            ProjectUtil.update_last_modified(file_path)

            # Adiciona aos projetos recentes
            self._recent_manager.add_recent(file_path)

            # Emite sinal para FileManager recarregar e atualiza recentes em tempo real
            SignalManager.instance().recent_projects_changed.emit(
                self._recent_manager.get_validated()
            )
            SignalManager.instance().project_changed.emit()

            self._logger.info(
                "Projeto aberto com sucesso", code="MENU_ABRIR_OK",
                file_path=file_path,
                project_name=project_data.get("project_name", ""),
            )
            MessageBox.show_info(
                f"Projeto '{project_data.get('project_name', '')}' aberto com sucesso!",
                title="Projeto Aberto",
            )
        except Exception as e:
            self._logger.error(
                "Erro ao abrir projeto", code="MENU_ABRIR_ERR", error=str(e),
            )
            MessageBox.show_error(
                "Erro ao abrir projeto", title="Abrir Projeto", detail=str(e),
            )

    def _on_salvar_como(self) -> None:
        """Salvar como: cria novo .mtl, salva prefs e emite project_changed."""
        try:
            self._logger.info("Salvando projeto como...", code="MENU_SALVAR_COMO")

            file_path = ExplorerUtils.save_file(
                title="Salvar projeto como",
                file_filter=self._MTL_FILTER,
                parent=self.parent(),
            )
            if not file_path:
                return  # usuário cancelou

            # Extrai pasta e nome
            folder = os.path.dirname(file_path)
            project_name = os.path.splitext(os.path.basename(file_path))[0]

            # ProjectUtil cuida de verificar se já existe
            result = ProjectUtil.create_project_safe(folder, project_name)
            if result is None:
                return  # usuário cancelou a substituição

            # Salva nas preferências do sistema
            sys_prefs = Preferences.load_tool_prefs(ToolKey.SYSTEM)
            sys_prefs["current_project"] = result["file_path"]
            sys_prefs["root_folder"] = folder
            Preferences.save_tool_prefs(ToolKey.SYSTEM, sys_prefs)

            # Adiciona aos projetos recentes
            self._recent_manager.add_recent(result["file_path"])

            # Emite sinal para FileManager recarregar e atualiza recentes em tempo real
            SignalManager.instance().recent_projects_changed.emit(
                self._recent_manager.get_validated()
            )
            SignalManager.instance().project_changed.emit()

            self._logger.info(
                "Projeto salvo como", code="MENU_SALVAR_COMO_OK",
                file_path=result["file_path"],
                project_name=project_name,
            )
            MessageBox.show_info(
                f"Projeto '{project_name}' salvo com sucesso!",
                title="Projeto Salvo",
            )
        except Exception as e:
            self._logger.error(
                "Erro ao salvar projeto como", code="MENU_SALVAR_COMO_ERR",
                error=str(e),
            )
            MessageBox.show_error(
                "Erro ao salvar projeto", title="Salvar como", detail=str(e),
            )

    # ────────────────────────────────────────────────────────────────
    # Handler: projeto recente
    # ────────────────────────────────────────────────────────────────

    def _on_recente_abrir(self, file_path: str) -> None:
        """
        Abre um projeto da lista de recentes.

        Valida se o arquivo ainda existe. Se não existir (active=False),
        não faz nada (o RecentProjectsMenu já desabilita o item, mas
        este handler serve como fallback).
        """
        try:
            if not os.path.isfile(file_path):
                self._logger.warning(
                    "Projeto recente não encontrado em disco",
                    code="MENU_RECENTE_NOT_FOUND",
                    file_path=file_path,
                )
                MessageBox.show_warning(
                    f"O arquivo '{file_path}' não foi encontrado.\n"
                    "Ele será mantido na lista de recentes como inativo.",
                    title="Arquivo Não Encontrado",
                )
                return

            project_data = ProjectUtil.load_project(file_path)
            if project_data is None:
                self._logger.warning(
                    "Projeto recente inválido", code="MENU_RECENTE_INVALIDO",
                    file_path=file_path,
                )
                MessageBox.show_error(
                    f"O arquivo '{file_path}' não é um projeto válido.",
                    title="Projeto Inválido",
                )
                return

            # Salva nas preferências do sistema
            sys_prefs = Preferences.load_tool_prefs(ToolKey.SYSTEM)
            sys_prefs["current_project"] = file_path
            sys_prefs["root_folder"] = os.path.dirname(file_path)
            Preferences.save_tool_prefs(ToolKey.SYSTEM, sys_prefs)

            # Atualiza last_modified
            ProjectUtil.update_last_modified(file_path)

            # Move ao topo dos recentes
            self._recent_manager.add_recent(file_path)

            # Emite sinal para FileManager recarregar e atualiza recentes em tempo real
            SignalManager.instance().recent_projects_changed.emit(
                self._recent_manager.get_validated()
            )
            SignalManager.instance().project_changed.emit()

            self._logger.info(
                "Projeto recente aberto", code="MENU_RECENTE_OK",
                file_path=file_path,
                project_name=project_data.get("project_name", ""),
            )

        except Exception as e:
            self._logger.error(
                "Erro ao abrir projeto recente", code="MENU_RECENTE_ERR",
                error=str(e),
            )
            MessageBox.show_error(
                "Erro ao abrir projeto recente",
                title="Abrir Recente",
                detail=str(e),
            )

    # ────────────────────────────────────────────────────────────────
    # Métodos privados
    # ────────────────────────────────────────────────────────────────

    def _on_tool_clicked(self, tool_name: str):
        """Propaga o clique da toolbar ou menu."""
        self.tool_activated.emit(tool_name)

    def _on_menu_action(self, data: str):
        """
        Fallback para ações disparadas pelo MenuBar.
        Se o data for um tool_name conhecido, propaga como tool_activated.
        """
        # Apenas propaga se não foi tratado por File/System/Help
        registry = ToolRegistry()
        tool = registry.get(data)
        if tool is not None:
            self.tool_activated.emit(data)

    def _on_sair(self):
        """Propaga sair_clicked."""
        self.sair_clicked.emit()

    def _on_sobre(self):
        """Propaga sobre_clicked."""
        self.sobre_clicked.emit()
