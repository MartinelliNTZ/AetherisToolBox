# -*- coding: utf-8 -*-
"""
WorkspaceTab — Aba customizada para o Workspace do Aetheris ToolBox
====================================================================
Representa uma aba individual no QTabBar do Workspace, com suporte a:
  - Ícone opcional
  - Título
  - Tooltip
  - Indicador de carregamento (lazy loading)
  - Botão de fechar estilizado
  - Estado ativo/inativo

Uso:
    tab = WorkspaceTab("Ferramenta", icon=my_icon, tooltip="Descrição")
    workspace.tab_bar.addTab(tab)
"""

from __future__ import annotations

from PySide6.QtCore import Qt, Signal, QSize
from PySide6.QtGui import QIcon, QPixmap, QPainter, QColor, QFont, QFontMetrics
from PySide6.QtWidgets import QWidget, QHBoxLayout, QLabel, QPushButton, QSizePolicy


class WorkspaceTab(QWidget):
    """
    Widget customizado para representar uma aba no QTabBar do Workspace.

    Pode ser usada via QTabBar.setTabButton() ou como widget embutido
    em layouts que simulam abas.
    """

    close_requested = Signal(str)  # nome da ferramenta

    _CLOSE_SIZE = 16
    _ICON_SIZE = 18
    _FONT_SIZE = 12
    _MIN_WIDTH = 80
    _MAX_WIDTH = 200
    _PADDING = 6

    def __init__(
        self,
        title: str,
        icon: QIcon | None = None,
        tooltip: str = "",
        parent=None,
    ):
        super().__init__(parent)
        self._title = title
        self._icon = icon
        self._tooltip = tooltip
        self._is_loaded = False
        self._is_active = False

        self.setObjectName("workspace_tab")
        self.setToolTip(tooltip)
        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Expanding)

        self._build_ui()

    # ------------------------------------------------------------------
    # UI
    # ------------------------------------------------------------------

    def _build_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(self._PADDING, 2, self._PADDING, 2)
        layout.setSpacing(4)

        # -- Ícone --
        if self._icon:
            self._icon_label = QLabel()
            pixmap = self._icon.pixmap(self._ICON_SIZE, self._ICON_SIZE)
            self._icon_label.setPixmap(pixmap)
            self._icon_label.setFixedSize(self._ICON_SIZE + 2, self._ICON_SIZE + 2)
            layout.addWidget(self._icon_label)

        # -- Título --
        self._title_label = QLabel(self._title)
        self._title_label.setObjectName("workspace_tab_title")
        self._title_label.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
        font = self._title_label.font()
        font.setPointSize(self._FONT_SIZE)
        self._title_label.setFont(font)
        layout.addWidget(self._title_label)

        # -- Spacer --
        spacer = QWidget()
        spacer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        layout.addWidget(spacer)

        # -- Botão fechar --
        self._close_btn = QPushButton("\u2715")
        self._close_btn.setObjectName("workspace_tab_close")
        self._close_btn.setFixedSize(self._CLOSE_SIZE, self._CLOSE_SIZE)
        self._close_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._close_btn.setFlat(True)
        self._close_btn.clicked.connect(self._on_close_clicked)
        layout.addWidget(self._close_btn)

        # Largura mínima baseada no texto + componentes
        self._update_minimum_width()

    def _update_minimum_width(self):
        font = self._title_label.font()
        fm = QFontMetrics(font)
        text_width = fm.horizontalAdvance(self._title) + 20
        icon_width = (self._ICON_SIZE + 6) if self._icon else 0
        close_width = self._CLOSE_SIZE + 8
        total = text_width + icon_width + close_width + (self._PADDING * 2) + 10
        self.setMinimumWidth(max(total, self._MIN_WIDTH))
        self.setMaximumWidth(min(total, self._MAX_WIDTH))

    # ------------------------------------------------------------------
    # Propriedades
    # ------------------------------------------------------------------

    @property
    def title(self) -> str:
        return self._title

    @title.setter
    def title(self, value: str):
        self._title = value
        self._title_label.setText(value)
        self._update_minimum_width()

    @property
    def icon(self) -> QIcon | None:
        return self._icon

    @icon.setter
    def icon(self, value: QIcon | None):
        self._icon = value
        if self._icon and hasattr(self, "_icon_label"):
            pixmap = self._icon.pixmap(self._ICON_SIZE, self._ICON_SIZE)
            self._icon_label.setPixmap(pixmap)
        self._update_minimum_width()

    @property
    def is_loaded(self) -> bool:
        return self._is_loaded

    @is_loaded.setter
    def is_loaded(self, value: bool):
        self._is_loaded = value

    @property
    def is_active(self) -> bool:
        return self._is_active

    @is_active.setter
    def is_active(self, value: bool):
        self._is_active = value
        if value:
            self._title_label.setStyleSheet("color: #C9A84C; font-weight: bold;")
        else:
            self._title_label.setStyleSheet("color: #CCCCCC; font-weight: normal;")

    # ------------------------------------------------------------------
    # Eventos
    # ------------------------------------------------------------------

    def _on_close_clicked(self):
        self.close_requested.emit(self._title)

    def set_title(self, text: str):
        """Alias para title.setter."""
        self.title = text

    def set_icon(self, icon: QIcon):
        """Alias para icon.setter."""
        self.icon = icon

    def set_loaded(self, loaded: bool = True):
        """Marca a aba como carregada (lazy loading concluído)."""
        self._is_loaded = loaded

    def set_active(self, active: bool = True):
        """Marca a aba como ativa (selecionada)."""
        self.is_active = active