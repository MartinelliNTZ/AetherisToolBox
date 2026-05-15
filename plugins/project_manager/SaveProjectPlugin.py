# -*- coding: utf-8 -*-
"""
ProjectManagerPlugin — Ferramenta Instantânea de Gerenciamento de Projetos
===========================================================================
Tipo: INSTANT — não abre aba, executa ação imediata.

Ao ser clicada:
1. Abre o explorador para selecionar uma pasta (via ExplorerUtils)
2. Solicita o nome do projeto via QInputDialog
3. Cria/atualiza um arquivo .mtl na pasta escolhida
4. Salva o caminho do .mtl em preferences (ToolKey.SYSTEM / current_project)
5. Se current_project já existir, apenas atualiza last_modified
"""

from __future__ import annotations

import os
from pathlib import Path

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QInputDialog, QVBoxLayout, QLabel

from core.enum.ToolKey import ToolKey
from core.model.BasePlugin import BasePlugin
from utils.ExplorerUtils import ExplorerUtils
from utils.MessageBox import MessageBox
from utils.Preferences import Preferences
from utils.ProjectUtil import ProjectUtil


class SaveProjectPlugin(BasePlugin):
    """
    Ferramenta INSTANT: gerencia projetos .mtl.
    Não persiste como aba no workspace — executa e encerra.
    """

    def __init__(self, parent=None):
        super().__init__(tool_key=ToolKey.SAVE_PROJECT.value, parent=parent)

        # Widget vazio (placeholder) — nunca será exibido como aba
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        placeholder = QLabel("")
        placeholder.setVisible(False)
        layout.addWidget(placeholder)

        # Executa o fluxo principal no próximo ciclo do event loop
        QTimer.singleShot(0, self._run_project_flow)

    # ──────────────────────────────────────────────────────────────────
    # Fluxo principal
    # ──────────────────────────────────────────────────────────────────

    def _run_project_flow(self) -> None:
        """
        Executa o fluxo de criação/atualização de projeto.
        """
        try:
            # 1. Verifica se já existe um current_project nas preferências
            sys_prefs = Preferences(section=ToolKey.SYSTEM.value)
            current_project = sys_prefs.get("current_project", None)

            if current_project and os.path.isfile(current_project):
                # Modo "salvar" — apenas atualiza last_modified
                self._handle_save_existing(current_project, sys_prefs)
            else:
                # Modo "criar" — abre explorador e pede nome
                self._handle_create_new(sys_prefs)

        except Exception as e:
            self.logger.error(
                "Erro no fluxo do gerenciador de projetos",
                code="PROJ_FLOW_ERR",
                error=str(e),
            )
            MessageBox.show_error(
                "Erro ao gerenciar projeto",
                title="Gerenciador de Projetos",
                detail=str(e),
            )
        finally:
            # Auto-destrói o widget
            self._self_destruct()

    # ── Modo "Salvar existente" ─────────────────────────────────────

    def _handle_save_existing(
        self, current_project: str, sys_prefs: Preferences
    ) -> None:
        """
        Atualiza o last_modified do projeto atual.
        """
        result = ProjectUtil.update_last_modified(current_project)
        if result is not None:
            self.logger.info(
                "Projeto atualizado",
                code="PROJ_SAVE",
                file_path=current_project,
                project_name=result.get("project_name", ""),
            )
            MessageBox.show_info(
                f"Projeto '{result.get('project_name', '')}' salvo com sucesso!",
                title="Projeto Salvo",
            )
        else:
            self.logger.warning(
                "Falha ao atualizar projeto existente",
                code="PROJ_SAVE_ERR",
                file_path=current_project,
            )
            # Se falhou, tenta criar novo
            self._handle_create_new(sys_prefs)

    # ── Modo "Criar novo" ──────────────────────────────────────────

    def _handle_create_new(self, sys_prefs: Preferences) -> None:
        """
        Abre explorador para selecionar pasta e pede nome do projeto.
        """
        # 1. Selecionar pasta
        folder = ExplorerUtils.select_directory(
            title="Selecionar pasta para o projeto",
            parent=self,
        )
        if not folder:
            self.logger.info("Usuário cancelou a seleção de pasta", code="PROJ_CANCEL")
            return

        # 2. Pedir nome do projeto
        name, ok = QInputDialog.getText(
            self,
            "Nome do Projeto",
            "Digite o nome do projeto:",
            text=os.path.basename(folder),
        )
        if not ok or not name.strip():
            self.logger.info("Usuário cancelou o nome do projeto", code="PROJ_CANCEL")
            return

        project_name = name.strip()

        # 3. Criar o arquivo .mtl
        # Valida se já existe um .mtl com esse nome na pasta
        mtl_path = Path(folder) / f"{project_name}{ProjectUtil.EXTENSION}"
        if mtl_path.is_file():
            confirm = MessageBox.show_question(
                f"Já existe um projeto '{project_name}' nesta pasta.\nDeseja sobrescrever?",
                title="Projeto Existente",
                buttons=MessageBox.YES_NO,
                default_button=MessageBox.NO,
            )
            if confirm != MessageBox.YES:
                return

        result = ProjectUtil.create_project(folder, project_name)
        if result is None:
            self.logger.error(
                "Falha ao criar arquivo de projeto",
                code="PROJ_CREATE_ERR",
                folder=folder,
                project_name=project_name,
            )
            MessageBox.show_error(
                f"Falha ao criar projeto '{project_name}' em:\n{folder}",
                title="Erro ao Criar Projeto",
            )
            return

        # 4. Salvar current_project nas preferências do sistema
        sys_prefs.set("current_project", result["file_path"])
        sys_prefs.save()

        self.logger.info(
            "Projeto criado com sucesso",
            code="PROJ_CREATED",
            file_path=result["file_path"],
            project_name=project_name,
        )
        MessageBox.show_info(
            f"Projeto '{project_name}' criado com sucesso!\n\n"
            f"Localização: {result['file_path']}",
            title="Projeto Criado",
        )

    # ── Auto-destruição ──────────────────────────────────────────────

    def _self_destruct(self) -> None:
        """
        Remove o widget do workspace e chama deleteLater.
        """
        self.logger.info("Finalizando ProjectManagerPlugin", code="PROJ_DONE")
        self.deleteLater()

    def load_prefs(self) -> None:
        """Noop — não há preferências para carregar."""
        pass

    def save_prefs(self) -> None:
        """Noop — não há preferências para persistir."""
        pass