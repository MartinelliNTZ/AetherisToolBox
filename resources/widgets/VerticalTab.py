# -*- coding: utf-8 -*-
"""
VerticalTab — Aba vertical estilo Civil 3D
==========================================
Texto renderizado rotacionado 90° via paintEvent.
Sem QLabel — controle total sobre aparência.
"""

from __future__ import annotations

from PySide6.QtCore    import Qt, Signal, QRect, QSize
from PySide6.QtGui     import QPainter, QPen, QColor, QFont, QFontMetrics
from PySide6.QtWidgets import QWidget


class VerticalTab(QWidget):
    """
    Aba vertical clicável com texto rotacionado 90° (bottom → top),
    estilo painel lateral do Civil 3D / AutoCAD.

    Emite `clicked` com o nome da aba ao ser pressionada.
    """

    clicked = Signal()

    _WIDTH  = 36
    _HEIGHT = 120   # ajuste conforme o tamanho do texto esperado

    def __init__(
        self,
        title:   str,
        tooltip: str = "",
        icon=None,          # QIcon opcional (futuro)
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
        self.setMinimumHeight(self._HEIGHT)
        self.setSizeHint = lambda: QSize(self._WIDTH, self._HEIGHT)  # type: ignore
        self.setCursor(Qt.CursorShape.PointingHandCursor)

        # Rastreia hover sem filtro de evento
        self.setMouseTracking(True)

    # ── Pintura ──────────────────────────────────────────────────────

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setRenderHint(QPainter.RenderHint.TextAntialiasing)

        w, h = self.width(), self.height()

        # ── Fundo ──────────────────────────────────────────────────
        if self._selected:
            bg = QColor("#1e90ff")          # azul destaque
            fg = QColor("#ffffff")
            border = QColor("#005fcc")
        elif self._hovered:
            bg = QColor("#2a2d2e")          # cinza hover (tema escuro)
            fg = QColor("#cccccc")
            border = QColor("#3c3f41")
        else:
            bg = QColor("#1e1e1e")          # fundo padrão tema escuro
            fg = QColor("#9d9d9d")
            border = QColor("#2d2d2d")

        painter.fillRect(0, 0, w, h, bg)

        # Borda esquerda como indicador de seleção
        if self._selected:
            painter.fillRect(0, 0, 3, h, QColor("#005fcc"))

        # Borda direita sutil
        painter.setPen(QPen(border, 1))
        painter.drawLine(w - 1, 0, w - 1, h)

        # ── Texto rotacionado ──────────────────────────────────────
        font = QFont("Segoe UI", 8)
        font.setWeight(QFont.Weight.Medium if self._selected else QFont.Weight.Normal)
        painter.setFont(font)
        painter.setPen(QPen(fg))

        # Salva, translada para o centro, rotaciona -90° e desenha
        painter.save()
        painter.translate(w / 2, h / 2)
        painter.rotate(-90)

        fm   = QFontMetrics(font)
        text = fm.elidedText(self._title, Qt.TextElideMode.ElideRight, h - 16)
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
            self.update()   # repaint sem style().unpolish()

    # ── Tamanho ideal ────────────────────────────────────────────────

    def sizeHint(self) -> QSize:
        fm = QFontMetrics(QFont("Segoe UI", 8))
        needed_h = fm.horizontalAdvance(self._title) #+ 24   # texto + padding
        return QSize(self._WIDTH, max(self._HEIGHT, needed_h))