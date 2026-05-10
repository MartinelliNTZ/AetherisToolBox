# -*- coding: utf-8 -*-
"""
VerticalTab — Aba vertical estilo Civil 3D
==========================================
Texto renderizado rotacionado 90° via paintEvent.
Sem QLabel — controle total sobre aparência.

Cores vindas de Palette (styles.py) para consistência com o tema.
Padding reduzido em relação ao WorkspaceTab por ser vertical.
"""

from __future__ import annotations

from PySide6.QtCore    import Qt, Signal, QRect, QSize
from PySide6.QtGui     import QPainter, QPen, QColor, QFont, QFontMetrics
from PySide6.QtWidgets import QWidget, QSizePolicy

from resources.styles.styles import Palette


class VerticalTab(QWidget):
    """
    Aba vertical clicável com texto rotacionado 90° (bottom → top),
    estilo painel lateral do Civil 3D / AutoCAD.

    Emite `clicked` ao ser pressionada.
    """

    clicked = Signal()

    _WIDTH  = 24               # espessura da aba (largura real na tela)
    _HEIGHT = 80               # altura inicial (vira largura do texto após rotação -90°)

    def __init__(
        self,
        title:   str,
        tooltip: str = "",
        icon=None,              # QIcon opcional (futuro)
        parent=None,
    ):
        super().__init__(parent)
        self._title    = title
        self._selected = False
        self._hovered  = False
        self._icon     = icon

        self.setObjectName("vertical_tab")
        if tooltip:
            self.setToolTip(tooltip)

        self.setFixedWidth(self._WIDTH)
        self.setFixedHeight(self._HEIGHT)
        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

        # Rastreia hover sem filtro de evento
        self.setMouseTracking(True)

    # ── Pintura ──────────────────────────────────────────────────────

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setRenderHint(QPainter.RenderHint.TextAntialiasing)

        w, h = self.width(), self.height()
        P    = Palette

        # ── Fundo ──────────────────────────────────────────────────
        if self._selected:
            bg     = QColor(P.GOLD)
            fg     = QColor(P.TEXT_BRIGHT)
            border = QColor(P.GOLD_DIM)
        elif self._hovered:
            bg     = QColor(P.BG_PANEL)
            fg     = QColor(P.TEXT_PRIMARY)
            border = QColor(P.BORDER_HOVER)
        else:
            bg     = QColor(P.BG_DEEPEST)
            fg     = QColor(P.TEXT_SECONDARY)
            border = QColor(P.BORDER)

        painter.fillRect(0, 0, w, h, bg)

        # Indicador de seleção — borda esquerda dourada
        if self._selected:
            painter.fillRect(0, 0, 3, h, QColor(P.GOLD_HOVER))

        # Borda direita sutil
        painter.setPen(QPen(border, 1))
        painter.drawLine(w - 1, 0, w - 1, h)

        # ── Texto rotacionado ──────────────────────────────────────
        font = QFont("Segoe UI", 8)
        font.setWeight(QFont.Weight.Medium if self._selected else QFont.Weight.Normal)
        painter.setFont(font)
        painter.setPen(QPen(fg))

        # Translada para o centro, rotaciona -90° e desenha
        painter.save()
        painter.translate(w / 2, h / 2)
        painter.rotate(-90)

        fm   = QFontMetrics(font)
        # Padding vertical reduzido (8px em vez de 16)
        text = fm.elidedText(self._title, Qt.TextElideMode.ElideRight, h - 8)
        tw   = fm.horizontalAdvance(text)
        th   = fm.height()

        # Rect centralizado no espaço já rotacionado
        painter.drawText(
            QRect(-tw // 2, -th // 2, tw, th),
            Qt.AlignmentFlag.AlignCenter,
            text,
        )
        painter.restore()

        painter.end()

    # ── Eventos de mouse ────────────────────────────────────────────

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit()
            event.accept()
        else:
            super().mousePressEvent(event)

    def enterEvent(self, event):
        self._hovered = True
        self.update()
        super().enterEvent(event)

    def leaveEvent(self, event):
        self._hovered = False
        self.update()
        super().leaveEvent(event)

    # ── Propriedades ────────────────────────────────────────────────

    @property
    def title(self) -> str:
        return self._title

    @title.setter
    def title(self, value: str):
        self._title = value
        self.update()

    @property
    def selected(self) -> bool:
        return self._selected

    @selected.setter
    def selected(self, value: bool):
        if self._selected != value:
            self._selected = value
            self.update()

    # ── Tamanho ideal ────────────────────────────────────────────────

    def sizeHint(self) -> QSize:
        fm = QFontMetrics(QFont("Segoe UI", 8))
        needed_h = fm.horizontalAdvance(self._title) + 8   # texto + padding reduzido
        return QSize(self._WIDTH, max(self._HEIGHT, needed_h))