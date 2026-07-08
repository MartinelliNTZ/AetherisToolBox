# -*- coding: utf-8 -*-
"""
ScrollableListWidget — Lista rolável genérica e reutilizável
==============================================================
Container com QScrollArea que aceita adicionar/remover widgets
dinamicamente. Similar a um RecyclerView.

Uso:
    from resources.widgets.ScrollableListWidget import ScrollableListWidget

    scroll = ScrollableListWidget()
    scroll.add_widget(MeuWidget())
    scroll.add_widget(OutroWidget())
    scroll.remove_all()
    scroll.count()  # número de widgets
"""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QScrollArea,
)


class ScrollableListWidget(QWidget):
    """
    Lista rolável genérica.

    Gerencia uma QScrollArea com layout vertical interno.
    Widgets filhos são adicionados ao `content_layout` e organizados
    verticalmente com espaçamento configurável.
    """

    def __init__(
        self,
        spacing: int = 8,
        margins: tuple[int, int, int, int] = (0, 0, 0, 0),
        parent=None,
    ):
        super().__init__(parent)

        # ── Scroll area ────────────────────────────────────────────
        self._scroll_area = QScrollArea()
        self._scroll_area.setWidgetResizable(True)
        self._scroll_area.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )
        self._scroll_area.setVerticalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAsNeeded
        )
        self._scroll_area.setFrameShape(QScrollArea.Shape.NoFrame)

        # ── Content widget ─────────────────────────────────────────
        self._content = QWidget()
        self.content_layout = QVBoxLayout(self._content)
        self.content_layout.setSpacing(spacing)
        self.content_layout.setContentsMargins(*margins)
        self.content_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        self._scroll_area.setWidget(self._content)

        # ── Outer layout ───────────────────────────────────────────
        self._outer_layout = QVBoxLayout(self)
        self._outer_layout.setContentsMargins(0, 0, 0, 0)
        self._outer_layout.setSpacing(0)
        self._outer_layout.addWidget(self._scroll_area)

    # ── Public API ─────────────────────────────────────────────────

    def add_widget(self, widget: QWidget, stretch: int = 0) -> None:
        """Adiciona um widget ao final da lista."""
        self.content_layout.addWidget(widget, stretch)

    def insert_widget(self, index: int, widget: QWidget) -> None:
        """Insere um widget em uma posição específica."""
        self.content_layout.insertWidget(index, widget)

    def remove_widget(self, widget: QWidget) -> None:
        """Remove um widget específico da lista."""
        self.content_layout.removeWidget(widget)
        widget.setParent(None)

    def remove_all(self) -> None:
        """Remove todos os widgets da lista."""
        while self.content_layout.count():
            item = self.content_layout.takeAt(0)
            if item and item.widget():
                item.widget().setParent(None)

    def count(self) -> int:
        """Retorna o número de widgets na lista."""
        return self.content_layout.count()

    def scroll_to_top(self) -> None:
        """Rola a lista para o topo."""
        self._scroll_area.verticalScrollBar().setValue(0)

    def scroll_to_bottom(self) -> None:
        """Rola a lista para o final."""
        scrollbar = self._scroll_area.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())