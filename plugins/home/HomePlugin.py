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
from PySide6.QtWidgets import QVBoxLayout

from core.enum.ToolKey import ToolKey
from core.model.FootballModel import Fixture
from core.papeline import PipelineRunner
from core.papeline.step import FootballFetchStep
from plugins.BasePlugin import BasePlugin
from resources.widgets.FootballMatchWidget import FootballMatchWidget
from resources.widgets.GroupPainel import GroupPainel
from resources.widgets.ListViewWidget import ListViewWidget
from resources.widgets.SeparatorWidget import SeparatorWidget
from resources.widgets.simple.SimpleLabel import SimpleLabel
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
        self._runner = None
        self._matches_container = None
        self._scroll_list = None
        super().__init__(tool_key=ToolKey.HOME.value, parent=parent)

    def _build_ui(self):
        # BasePlugin cria self.main_layout (PluginPage) com margins padrão.
        # Vamos sobrescrever com layout próprio para a Home.
        # Remove o PluginPage criado por BasePlugin e cria layout direto.
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(40, 40, 40, 40)
        self.main_layout.setSpacing(16)
        self.main_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        # === HEADER ===
        header = SimpleLabel("Aetheris ToolBox")
        header.setObjectName("header_title")
        header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.main_layout.addWidget(header)

        subtitle = SimpleLabel("Bem-vindo! Selecione uma ferramenta nas abas acima.")
        subtitle.setObjectName("header_subtitle")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.main_layout.addWidget(subtitle)

        # === SEPARATOR ===
        self.main_layout.addWidget(SeparatorWidget(orientation="horizontal"))

        # === FOOTBALL MATCHES ===
        self._matches_container = GroupPainel("Partidas de Futebol — Hoje")
        self._scroll_list = ListViewWidget(spacing=6, scroll=True)
        self._matches_container.group_layout.addWidget(self._scroll_list)
        self._matches_container.setVisible(False)
        self.main_layout.addWidget(self._matches_container)

        # ── Placeholder ────────────────────────────────────────────
        self._placeholder = SimpleLabel(
            "Utilize as abas do Workspace para acessar\n"
            "as ferramentas disponíveis."
        )
        self._placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._placeholder.setStyleSheet("color: #888890; font-size: 13px;")
        self.main_layout.addWidget(self._placeholder)

        # Espaçador
        self.main_layout.addStretch(1)

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
        e preenche o ListViewWidget com FootballMatchWidgets.
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

            fixtures: list[Fixture] = []
            for item in fixtures_data:
                fixture = Fixture.from_api_response(item)
                fixtures.append(fixture)

            self.logger.info(
                "Partidas carregadas",
                code="HOME_FOOT_MATCHES",
                count=len(fixtures),
            )

            self._display_matches(fixtures)

        except Exception as e:
            self.logger.error(
                "Falha ao carregar partidas",
                code="HOME_FOOT_LOAD_ERR",
                error=str(e),
            )

    def _display_matches(self, fixtures: list[Fixture]) -> None:
        """Preenche o scroll list com widgets de partida."""
        if self._scroll_list:
            self._scroll_list.remove_all()

        for fixture in fixtures:
            widget = FootballMatchWidget(fixture)
            self._scroll_list.add_widget(widget)

        self._matches_container.setVisible(True)
        self._placeholder.setVisible(False)