# -*- coding: utf-8 -*-
"""
GridCardView — Grade genérica de cards configuráveis
=====================================================
Widget 100% genérico que exibe N cards em grid, cada um com
logo opcional e lista de labels tipadas.

Tipos de label:
    - "simple":        texto normal, cor secundária
    - "simple_accent": texto normal, cor de destaque
    - "great":         texto grande (22px), cor secundária
    - "great_accent":  texto grande (22px), cor de destaque

Uso:
    from resources.widgets.GridCardView import GridCardView

    config = {
        "title": "Palmas, TO",          # opcional
        "items_per_row": 4,
        "cards": [
            {"logo": "path.png", "labels": [
                {"type": "great_accent", "text": "32°C"},
                {"type": "simple", "text": "Temperatura"},
            ]},
        ],
    }
    view = GridCardView(config)
    parent_layout.addWidget(view)
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (
    QFrame, QGridLayout, QLabel, QSizePolicy, QVBoxLayout, QWidget,
)

from resources.styles.AppStyles import AppStyles


class _CardWidget(QFrame):
    """Card individual dentro do GridCardView."""

    def __init__(
        self,
        logo: Optional[str] = None,
        labels: Optional[List[Dict[str, str]]] = None,
        parent=None,
    ):
        super().__init__(parent)
        self.setObjectName("grid_card_view_card")
        self.setFrameShape(QFrame.Shape.StyledPanel)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(4)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Logo opcional
        if logo:
            logo_label = QLabel()
            logo_label.setFixedSize(40, 40)
            logo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            pixmap = QPixmap(logo)
            if not pixmap.isNull():
                logo_label.setPixmap(
                    pixmap.scaled(36, 36, Qt.AspectRatioMode.KeepAspectRatio,
                                  Qt.TransformationMode.SmoothTransformation)
                )
            else:
                logo_label.setStyleSheet(
                    "background-color: #2A2A30; border-radius: 18px; "
                    "border: 1px solid #3A3A40;"
                )
            layout.addWidget(logo_label)

        # Labels
        self._label_widgets: list[QLabel] = []
        if labels:
            for item in labels:
                label = QLabel(item.get("text", ""))
                label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                label.setWordWrap(True)
                label.setSizePolicy(
                    QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred
                )

                label_type = item.get("type", "simple")
                if label_type == "great_accent":
                    label.setStyleSheet(
                        f"color: {AppStyles.current_theme.ACCENT}; "
                        f"font-size: 22px; font-weight: bold;"
                    )
                elif label_type == "great":
                    label.setStyleSheet(
                        f"color: {AppStyles.current_theme.TEXT_SECONDARY}; "
                        f"font-size: 22px; font-weight: bold;"
                    )
                elif label_type == "simple_accent":
                    label.setStyleSheet(
                        f"color: {AppStyles.current_theme.ACCENT}; "
                        f"font-size: 12px;"
                    )
                else:  # simple
                    label.setStyleSheet(
                        f"color: {AppStyles.current_theme.TEXT_SECONDARY}; "
                        f"font-size: 12px;"
                    )

                tooltip = item.get("tooltip")
                if tooltip:
                    label.setToolTip(tooltip)

                layout.addWidget(label)
                self._label_widgets.append(label)

        layout.addStretch(1)

    def set_label_text(self, index: int, text: str) -> None:
        """Atualiza o texto de um label pelo índice."""
        if 0 <= index < len(self._label_widgets):
            self._label_widgets[index].setText(text)


class GridCardView(QWidget):
    """
    Grade genérica de cards configuráveis.

    Parâmetros do config:
        title: str (opcional) — título exibido acima do grid
        items_per_row: int (padrão 4) — número de cards por linha
        cards: list[dict] — cada card pode ter:
            logo: str (opcional) — caminho/URL da imagem
            labels: list[dict] — cada label tem:
                type: str — "simple", "simple_accent", "great", "great_accent"
                text: str — conteúdo do label
                tooltip: str (opcional)
    """

    def __init__(
        self,
        config: Optional[Dict[str, Any]] = None,
        parent=None,
    ):
        super().__init__(parent)
        self._cards: list[_CardWidget] = []
        self._title_label: Optional[QLabel] = None
        self._grid = QGridLayout()
        self._grid.setContentsMargins(0, 0, 0, 0)
        self._grid.setSpacing(8)

        # Layout principal: título + grid
        self._main_layout = QVBoxLayout(self)
        self._main_layout.setContentsMargins(0, 0, 0, 0)
        self._main_layout.setSpacing(8)

        if config:
            self.build(config)

    def build(self, config: Dict[str, Any]) -> None:
        """Constrói ou reconstrói o grid a partir de um config."""
        # Limpa tudo
        self._clear_all()
        self._cards.clear()

        # Título opcional
        title = config.get("title")
        if title:
            self._title_label = QLabel(title)
            self._title_label.setObjectName("grid_card_view_title")
            self._title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self._title_label.setStyleSheet(
                f"color: {AppStyles.current_theme.ACCENT}; "
                f"font-size: 16px; font-weight: bold;"
            )
            self._main_layout.addWidget(self._title_label)

        items_per_row = config.get("items_per_row", 4)
        cards_data = config.get("cards", [])

        for idx, card_data in enumerate(cards_data):
            card = _CardWidget(
                logo=card_data.get("logo"),
                labels=card_data.get("labels"),
                parent=self,
            )
            row = idx // items_per_row
            col = idx % items_per_row
            self._grid.addWidget(card, row, col)
            self._cards.append(card)

        # Garante que todos os cards na mesma linha tenham a mesma altura
        # setRowStretch força o grid a distribuir espaço igual entre linhas
        total_rows = (len(cards_data) + items_per_row - 1) // items_per_row if cards_data else 0
        for r in range(total_rows):
            self._grid.setRowStretch(r, 1)

        # Todas as colunas com mesmo stretch
        for c in range(items_per_row):
            self._grid.setColumnStretch(c, 1)

        self._main_layout.addLayout(self._grid)

    def set_card_value(
        self,
        card_index: int,
        label_index: int,
        text: str,
    ) -> None:
        """Atualiza o texto de um label em um card específico."""
        if 0 <= card_index < len(self._cards):
            self._cards[card_index].set_label_text(label_index, text)

    def _clear_all(self) -> None:
        """Remove todos os widgets e o grid do layout principal."""
        # Remove título
        if self._title_label:
            self._main_layout.removeWidget(self._title_label)
            self._title_label.deleteLater()
            self._title_label = None

        # Remove grid do layout principal
        self._main_layout.removeItem(self._grid)

        # Limpa grid
        while self._grid.count():
            item = self._grid.takeAt(0)
            if item and item.widget():
                item.widget().deleteLater()