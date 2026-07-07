# -*- coding: utf-8 -*-
"""
HomeTool — Página inicial do Aetheris ToolBox
===============================================
Widget exibido por padrão ao abrir o software.
Apresenta um resumo visual das ferramentas disponíveis
e boas-vindas ao usuário.
"""

from __future__ import annotations

from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import (
    QLabel, QVBoxLayout, QFrame
)

from core.enum.ToolKey import ToolKey
from core.papeline import PipelineRunner
from core.papeline.step import FootballFetchStep
from plugins.BasePlugin import BasePlugin


class HomePlugin(BasePlugin):
    """
    Página inicial do Aetheris ToolBox.
    Aberta por padrão ao iniciar o software.
    Ao iniciar, executa a pipeline de fetching de futebol
    via PipelineRunner + FootballFetchStep em background.
    """

    def __init__(self, parent=None):
        super().__init__(tool_key=ToolKey.HOME.value, parent=parent)
        self._runner: PipelineRunner | None = None

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 40, 40, 40)
        layout.setSpacing(16)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

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

        # === PLACEHOLDER ===
        placeholder = QLabel(
            "Utilize as abas do Workspace para acessar\n"
            "as ferramentas disponíveis."
        )
        placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        placeholder.setStyleSheet("color: #888890; font-size: 13px;")
        layout.addWidget(placeholder)

        # Espaçador para empurrar conteúdo ao centro
        layout.addStretch(1)

        # ── Start football fetch pipeline after UI is ready ──────
        QTimer.singleShot(500, self._start_football_pipeline)

    def _start_football_pipeline(self) -> None:
        """
        Executa a pipeline de fetch de futebol em background.
        Usa QTimer.singleShot para não travar a inicialização da UI.
        """
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

    def _on_football_done(self, _context) -> None:
        """Callback when football pipeline completes successfully."""
        self.logger.info(
            "Pipeline de futebol concluída com sucesso",
            code="HOME_FOOT_DONE",
        )
        # Keep runner alive — QThread self-destructs when run() exits.
        # Setting to None would destroy it while thread is still finishing.
        # The runner will be GC'd when HomePlugin is destroyed.

    def _on_football_error(self, error_msg: str) -> None:
        """Callback when football pipeline fails."""
        self.logger.error(
            "Pipeline de futebol falhou",
            code="HOME_FOOT_ERR",
            error=error_msg,
        )
        # Same as above — keep reference alive
