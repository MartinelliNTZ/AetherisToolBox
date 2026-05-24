# -*- coding: utf-8 -*-
"""
ConfigurationPlugin — Plugin de Configuração do Sistema
=========================================================
Ferramenta de sistema para configurações gerais do Aetheris ToolBox.
Inicialmente em branco, pronto para receber opções de configuração.

Tipo BOTH — pode ser exibido tanto no workspace central quanto no painel lateral.
Acessível pelo menu Sistema > Configuração.
"""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QLabel, QVBoxLayout

from plugins.BasePlugin import BasePlugin


class ConfigurationPlugin(BasePlugin):
    """
    Plugin de configuração do sistema.
    Placeholder — UI será construída conforme necessidade.
    """

    def __init__(self, parent=None):
        super().__init__(
            tool_key="Configuration",
            parent=parent,
            title="Configuração",
        )

    def _build_ui(self):
        """Constrói a UI base com placeholder."""
        super()._build_ui()

        # Placeholder inicial — será substituído por conteúdo real
        label = QLabel("Configurações do sistema em breve...")
        label.setStyleSheet("color: #888; font-size: 14px; padding: 20px;")
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.main_layout.addWidget(label)

    def load_prefs(self):
        """Carrega preferências salvas (placeholder)."""
        pass

    def save_prefs(self):
        """Salva preferências (placeholder)."""
        pass