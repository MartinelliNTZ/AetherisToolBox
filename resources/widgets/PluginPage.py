# -*- coding: utf-8 -*-
"""
PluginPage — Layout padrão para todos os plugins
=================================================
Fornece:
- QVBoxLayout com margins (18, 10, 18, 10) e spacing 8
- Header opcional (QLabel + QFrame separator) se um title for informado

Uso no BasePlugin (automático):
    class MeuPlugin(BasePlugin):
        def _build_ui(self):
            super()._build_ui()
            # self.main_layout disponível para adicionar widgets
            self.main_layout.addWidget(...)

Uso standalone:
    page = PluginPage(title="Meu Plugin")
    page.main_layout.addWidget(QLabel("conteúdo"))
"""

from __future__ import annotations

from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QFrame


class PluginPage(QWidget):
    """
    Container base que aplica o layout padrão do sistema.

    Se ``title`` for informado, cria automaticamente:
        - QLabel com objectName "header_title"
        - QFrame separator com objectName "separator"

    Atributos:
        main_layout : QVBoxLayout — layout principal para adicionar widgets filhos
    """

    def __init__(self, parent: QWidget | None = None, title: str | None = None) -> None:
        super().__init__(parent)
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(18, 10, 18, 10)
        self.main_layout.setSpacing(8)

        if title:
            header = QLabel(title)
            header.setObjectName("header_title")
            self.main_layout.addWidget(header)

            sep = QFrame()
            sep.setObjectName("separator")
            sep.setFrameShape(QFrame.Shape.HLine)
            sep.setFixedHeight(1)
            self.main_layout.addWidget(sep)

    def add_widget(self, widget: QWidget, stretch: int = 0) -> None:
        """Atalho para adicionar widget ao main_layout."""
        self.main_layout.addWidget(widget, stretch)

    def add_widgets(self, *widgets: QWidget, stretch: int = 0) -> None:
        """
        Adiciona múltiplos widgets ao main_layout de uma só vez.

        Args:
            *widgets: Widgets a serem adicionados (ordem sequencial)
            stretch: Fator de esticamento aplicado a todos

        Exemplo:
            page.add_widgets(QLabel("A"), QLineEdit(), QPushButton("OK"))
        """
        for widget in widgets:
            self.main_layout.addWidget(widget, stretch)
