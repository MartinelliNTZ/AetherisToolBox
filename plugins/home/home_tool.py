# -*- coding: utf-8 -*-
"""
HomeTool — Página inicial do Aetheris ToolBox
===============================================
Widget exibido por padrão ao abrir o software.
Apresenta um resumo visual das ferramentas disponíveis
e boas-vindas ao usuário.
"""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QLabel, QVBoxLayout, QFrame
)

from core.model.BasePlugin import BasePlugin


class HomeTool(BasePlugin):
    """
    Página inicial do Aetheris ToolBox.
    Aberta por padrão ao iniciar o software.
    """

    def __init__(self, parent=None):
        super().__init__(tool_key="Home", parent=parent)
        self._build_ui()

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