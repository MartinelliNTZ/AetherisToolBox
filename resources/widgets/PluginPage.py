# -*- coding: utf-8 -*-
"""
PluginPage — Layout padrão para todos os plugins
=================================================
Fornece:
- QVBoxLayout com margins (18, 10, 18, 10) e spacing 8
- Header opcional (QLabel + QFrame separator) se um title for informado
- Badge de status encapsulado — o plugin chama apenas:

      self.page.set_badge(self.page.PRONTA)
      self.page.set_badge(self.page.RUNNING)
      self.page.set_badge(self.page.ERROR)
      self.page.set_badge(self.page.CANCELED)
      self.page.set_badge(self.page.INFO)

  O estilo é aplicado automaticamente conforme o estado.

Uso no BasePlugin (automático):
    class MeuPlugin(BasePlugin):
        def _build_ui(self):
            super()._build_ui()
            self.page.set_badge(self.page.ERROR)

Uso standalone:
    page = PluginPage(title="Meu Plugin")
    page.set_badge(page.PRONTA)
"""

from __future__ import annotations

from enum import Enum

from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QFrame, QHBoxLayout
from PySide6.QtCore import Qt


class _BadgeState(Enum):
    """Estados internos do badge. Acessados via constantes na classe PluginPage."""
    READY = "PRONTA"
    RUNNING = "EXECUTANDO"
    ERROR = "ERRO"
    CANCELED = "CANCELADO"
    INFO = "INFO"


class Badge(QLabel):
    """
    Selo de status usado nos plugins para indicar estado.
    O estilo visual é aplicado automaticamente via set_badge().
    """

    def __init__(self, text: str, parent=None):
        super().__init__(text, parent)
        self.setObjectName("section_badge")
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)


class PluginPage(QWidget):
    """
    Container base que aplica o layout padrão do sistema.

    Se ``title`` for informado, cria automaticamente:
        - QLabel com objectName "header_title"
        - QFrame separator com objectName "separator"

    O badge de status é configurado via set_badge(estado).
    Use as constantes da própria classe:

        self.page.set_badge(self.page.PRONTA)
        self.page.set_badge(self.page.RUNNING)
        self.page.set_badge(self.page.ERROR)
        self.page.set_badge(self.page.CANCELED)
        self.page.set_badge(self.page.INFO)

    Atributos:
        main_layout : QVBoxLayout — layout principal para adicionar widgets filhos
        header      : QWidget | None — container do header (se title foi informado)
        badge       : Badge | None — badge de status (criado sob demanda)
    """

    # Constantes públicas — o plugin usa self.page.PRONTA, self.page.ERROR etc.
    PRONTA = _BadgeState.READY
    RUNNING = _BadgeState.RUNNING
    ERROR = _BadgeState.ERROR
    CANCELED = _BadgeState.CANCELED
    INFO = _BadgeState.INFO

    # Mapeamento estado -> cor de fundo do badge
    _BADGE_COLORS = {
        _BadgeState.READY: "#27ae60",      # verde
        _BadgeState.RUNNING: "#f39c12",    # laranja
        _BadgeState.ERROR: "#e74c3c",      # vermelho
        _BadgeState.CANCELED: "#95a5a6",   # cinza
        _BadgeState.INFO: "#3498db",       # azul
    }

    def __init__(self, parent: QWidget | None = None, title: str | None = None) -> None:
        super().__init__(parent)
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(18, 10, 18, 10)
        self.main_layout.setSpacing(8)

        self.header: QWidget | None = None
        self.badge: Badge | None = None

        if title:
            self._build_header(title)

    def _build_header(self, title: str) -> None:
        """Constrói o header com título e espaço reservado para badge."""
        header = QWidget()
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_layout.setSpacing(8)

        header_title = QLabel(title)
        header_title.setObjectName("header_title")
        header_layout.addWidget(header_title, 1)

        self._header_layout = header_layout
        self._header_title = header_title

        self.main_layout.addWidget(header)

        sep = QFrame()
        sep.setObjectName("separator")
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setFixedHeight(1)
        self.main_layout.addWidget(sep)

        self.header = header

    def set_badge(self, state: _BadgeState) -> Badge:
        """
        Define o estado do badge no header, alinhado à direita.

        Args:
            state: Uma das constantes da classe:
                   page.PRONTA, page.RUNNING, page.ERROR,
                   page.CANCELED, page.INFO

        Returns:
            Badge: Instância do badge criado/atualizado.
        """
        if not hasattr(self, '_header_layout'):
            raise RuntimeError(
                "PluginPage.set_badge() requires a title to be set. "
                "Pass 'title' to PluginPage constructor."
            )

        text = state.value
        bg_color = self._BADGE_COLORS[state]

        if self.badge is None:
            self.badge = Badge(text)
            self._header_layout.addWidget(self.badge, alignment=Qt.AlignmentFlag.AlignRight)
        else:
            self.badge.setText(text)

        # Aplica o estilo encapsulado — plugin não precisa saber de AppStyles
        self.badge.setStyleSheet(
            f"QLabel {{"
            f"  background-color: {bg_color};"
            f"  color: #ffffff;"
            f"  border-radius: 4px;"
            f"  padding: 2px 10px;"
            f"  font-weight: 900;"
            f"  font-size: 10px;"
            f"  letter-spacing: 1.5px;"
            f"}}"
        )

        return self.badge

    def set_title(self, title: str) -> None:
        """
        Altera ou define o título do header.

        Se o header não existir (PluginPage foi criada sem title),
        este método o constrói dinamicamente.
        """
        if not hasattr(self, '_header_layout'):
            self._build_header(title)
        else:
            self._header_title.setText(title)

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