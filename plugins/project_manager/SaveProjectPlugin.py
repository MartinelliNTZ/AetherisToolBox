# -*- coding: utf-8 -*-
"""
SaveProjectPlugin — Ferramenta Instantânea para Salvar Projetos (.mtl)
========================================================================
Tipo: INSTANT — não abre aba, executa ação imediata.

Ao ser clicada:
1. Se current_project existe — atualiza last_modified (modo salvar)
2. Se não existe — abre diálogo nativo "Salvar como" com filtro .mtl
     (local + nome + extensão em UMA etapa)
     ProjectUtil.create_project_safe() cuida da validação de substituição
     Cria o .mtl com metadados
3. Salva o caminho do .mtl em preferences (ToolKey.SYSTEM / current_project)
"""

from __future__ import annotations

import os

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QVBoxLayout, QLabel

from core.enum.ToolKey import ToolKey
from core.model.BasePlugin import BasePlugin
from utils.ExplorerUtils import ExplorerUtils
from utils.MessageBox import MessageBox
from utils.Preferences import Preferences
from utils.ProjectUtil import ProjectUtil


class SaveProjectPlugin(BasePlugin):
    """
    Ferramenta INSTANT: cria ou salva projetos .mtl.
    Usa o diálogo nativo "Salvar como" do Windows em uma única etapa.
    """

    _MTL_FILTER = "Projeto Aetheris (*.mtl)"

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

    # ── Fluxo principal ────────────────────────────────────────────

    def _run_project_flow(self) -> None:
        """Executa o fluxo de criação/atualização de projeto."""
        try:
            sys_prefs = Preferences(section=ToolKey.SYSTEM.value)
            current_project = sys_prefs.get("current_project", None)

            if current_project and os.path.isfile(current_project):
                self._handle_save_existing(current_project, sys_prefs)
            else:
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
            self._self_destruct()

    # ── Modo "Salvar existente" ────────────────────────────────────

    def _handle_save_existing(
        self, current_project: str, sys_prefs: Preferences
    ) -> None:
        """Atualiza o last_modified do projeto atual."""
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
            self._handle_create_new(sys_prefs)

    # ── Modo "Criar novo" ─────────────────────────────────────────

    def _handle_create_new(self, sys_prefs: Preferences) -> None:
        """
        Abre o diálogo nativo "Salvar como" com filtro .mtl.
        Tudo em UMA etapa: local + nome + extensão já inclusa.
        """
        # 1. Diálogo nativo do Windows — escolhe local e nome
        file_path = ExplorerUtils.save_file(
            title="Salvar projeto como",
            file_filter=self._MTL_FILTER,
            parent=self,
        )
        if not file_path:
            self.logger.info("Usuário cancelou a criação do projeto", code="PROJ_CANCEL")
            return

        # 2. Extrai pasta e nome do caminho completo
        folder = os.path.dirname(file_path)
        project_name = os.path.splitext(os.path.basename(file_path))[0]

        # 3. ProjectUtil cuida da validação — se já existe, pergunta
        result = ProjectUtil.create_project_safe(folder, project_name, self)
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

        # 4. Salva current_project nas preferências do sistema
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

    # ── Auto-destruição ─────────────────────────────────────────────

    def _self_destruct(self) -> None:
        """Remove o widget do workspace e chama deleteLater."""
        self.logger.info("Finalizando SaveProjectPlugin", code="PROJ_DONE")
        self.deleteLater()

    def load_prefs(self) -> None:
        """Noop — não há preferências para carregar."""
        pass

    def save_prefs(self) -> None:
        """Noop — não há preferências para persistir."""
        pass