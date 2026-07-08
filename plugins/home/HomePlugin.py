# -*- coding: utf-8 -*-
"""
HomeTool — Página inicial do Aetheris ToolBox
===============================================
Widget exibido por padrão ao abrir o software.
Apresenta um resumo visual das ferramentas disponíveis
e boas-vindas ao usuário. Exibe partidas de futebol do dia
após a pipeline de fetch ser concluída.
"""

from __future__ import annotations

from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import (
    QLabel, QVBoxLayout, QFrame,
)

from core.enum.ToolKey import ToolKey
from core.model.FootballModel import Fixture
from core.papeline import PipelineRunner
from core.papeline.step import FootballFetchStep
from plugins.BasePlugin import BasePlugin
from resources.widgets.FootballMatchWidget import FootballMatchWidget
from resources.widgets.GroupPainel import GroupPainel
from resources.widgets.ScrollableListWidget import ScrollableListWidget
from utils.JsonUtil import JsonUtil


class HomePlugin(BasePlugin):
    """
    Página inicial do Aetheris ToolBox.
    Aberta por padrão ao iniciar o software.
    Ao iniciar, executa a pipeline de fetching de futebol
    via PipelineRunner + FootballFetchStep em background.

    Quando a pipeline termina, carrega os dados filtrados
    e exibe as partidas em um GroupPainel com scroll.
    """

    def __init__(self, parent=None):
        # Init these BEFORE super() so _build_ui() populates them,
        # and the subclass init doesn't overwrite with None after.
        self._runner = None
        self._matches_container = None
        self._scroll_list = None
        super().__init__(tool_key=ToolKey.HOME.value, parent=parent)

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 40, 40, 40)
        layout.setSpacing(16)
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        # === HEADER ===
        header = QLabel("Aetheris ToolBox")
        header.setObjectName("header_title")
        header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(header)

        subtitle = QLabel("Bem-vindo! Selecione uma ferramenta nas abas acima.")
        subtitle.setObjectName("header_subtitle")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(subtitle)

        # === SEPARATOR ===
        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setFixedHeight(1)
        sep.setStyleSheet("background-color: #2A2A30; border: none;")
        layout.addWidget(sep)

        # === FOOTBALL MATCHES ===
        self._matches_container = GroupPainel("Partidas de Futebol — Hoje")
        self._scroll_list = ScrollableListWidget(spacing=6)
        self._matches_container.group_layout.addWidget(self._scroll_list)
        self._matches_container.setVisible(False)  # esconde até carregar
        layout.addWidget(self._matches_container)

        # ── Placeholder ────────────────────────────────────────────
        self._placeholder = QLabel(
            "Utilize as abas do Workspace para acessar\n"
            "as ferramentas disponíveis."
        )
        self._placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._placeholder.setStyleSheet("color: #888890; font-size: 13px;")
        layout.addWidget(self._placeholder)

        # Espaçador
        layout.addStretch(1)

        # ── Start football fetch pipeline after UI is ready ──────
        QTimer.singleShot(500, self._start_football_pipeline)

    def _start_football_pipeline(self) -> None:
        """Executa a pipeline de fetch de futebol em background."""
        if self._runner is not None and self._runner.isRunning():
            self.logger.info(
                "Football pipeline já está em execução",
                code="HOME_FOOT_SKIP",
            )
            return

        self._runner = PipelineRunner(
            steps=[FootballFetchStep()],
            tool_key=ToolKey.FOOTBALL_FETCH.value,
        )
        self._runner.finished_ok.connect(self._on_football_done)
        self._runner.failed.connect(self._on_football_error)

        self.logger.info(
            "Iniciando pipeline de fetch de futebol",
            code="HOME_FOOT_START",
        )
        self._runner.start()

    def _on_football_done(self, context) -> None:
        """Callback when football pipeline completes successfully."""
        self.logger.info(
            "Pipeline de futebol concluída com sucesso",
            code="HOME_FOOT_DONE",
        )

        # Obter caminho do JSON filtrado
        result = context.get_result("football_fetch")
        if not result:
            self.logger.warning(
                "Nenhum resultado na pipeline de futebol",
                code="HOME_FOOT_NO_RESULT",
            )
            return

        today_filtered_path = result.get("today_filtered")
        if not today_filtered_path:
            self.logger.warning(
                "Nenhum arquivo filtrado de hoje encontrado",
                code="HOME_FOOT_NO_FILE",
            )
            return

        self._load_matches(today_filtered_path)

    def _on_football_error(self, error_msg: str) -> None:
        """Callback when football pipeline fails."""
        self.logger.error(
            "Pipeline de futebol falhou",
            code="HOME_FOOT_ERR",
            error=error_msg,
        )

    # ── Match loading ──────────────────────────────────────────────

    def _load_matches(self, json_path: str) -> None:
        """
        Lê o JSON filtrado, converte para lista de Fixture
        e preenche o ScrollableListWidget com FootballMatchWidgets.
        """
        try:
            data = JsonUtil.read_json(json_path, tool_key=self.tool_key)
            if not data:
                self.logger.warning(
                    "JSON vazio ou inválido", code="HOME_FOOT_EMPTY",
                )
                return

            fixtures_data = data.get("response", [])
            if not fixtures_data:
                self.logger.info(
                    "Nenhuma partida filtrada encontrada",
                    code="HOME_FOOT_NO_MATCHES",
                )
                return

            # Converte cada item do JSON para Fixture
            fixtures: list[Fixture] = []
            for item in fixtures_data:
                fixture = Fixture.from_api_response(item)
                fixtures.append(fixture)

            self.logger.info(
                "Partidas carregadas",
                code="HOME_FOOT_MATCHES",
                count=len(fixtures),
            )

            # Preenche a UI
            self._display_matches(fixtures)

        except Exception as e:
            self.logger.error(
                "Falha ao carregar partidas",
                code="HOME_FOOT_LOAD_ERR",
                error=str(e),
            )

    def _display_matches(self, fixtures: list[Fixture]) -> None:
        """Preenche o scroll list com widgets de partida."""
        # Limpa widgets anteriores
        if self._scroll_list:
            self._scroll_list.remove_all()

        for fixture in fixtures:
            widget = FootballMatchWidget(fixture)
            self._scroll_list.add_widget(widget)

        # Mostra o container e esconde o placeholder
        self._matches_container.setVisible(True)
        self._placeholder.setVisible(False)
        self._matches_container.group_layout.parent().update()