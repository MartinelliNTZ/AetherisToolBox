# -*- coding: utf-8 -*-
"""
GridPercentView — Grade horizontal de indicadores percentuais
=============================================================
Exibe valores percentuais (CPU, RAM) lado a lado com tooltip
individual por item ao passar o mouse.

Cada item tem seu proprio tooltip. O tooltip global do widget
so e usado como fallback quando o mouse esta fora de qualquer item.

Uso:
    view = GridPercentView({
        "cpu": {"label": "CPU", "value": 0.0, "tooltip": "Aguardando...",
                "callback": self._on_cpu_clicked},
        "ram": {"label": "RAM", "value": 0.0, "tooltip": "Aguardando..."},
    })
    view.set("cpu", 45.2, tooltip="CPU: 45.2% (8 cores fisicos, ...)")
    view.set("ram", 72.8, tooltip="RAM: 72.8% (23.4 GB / 32.0 GB usados)")

Sinais:
    item_clicked(key, value) — emitido ao clicar em item com callback
"""

from __future__ import annotations

from typing import Any, Callable, Dict, Optional

from PySide6.QtCore import QRect, QSize, Qt, Signal
from PySide6.QtGui import QColor, QFont, QFontMetrics, QPainter, QPen, QBrush
from PySide6.QtWidgets import QWidget

from resources.styles.AppStyles import AppStyles


class _PercentItem:
    """Item interno representando um indicador percentual."""

    __slots__ = ("label", "value", "tooltip", "callback", "rect")

    def __init__(
        self,
        label: str,
        value: float = 0.0,
        tooltip: str = "",
        callback: Optional[Callable] = None,
    ):
        self.label = label
        self.value = value
        self.tooltip = tooltip or f"{label}: {value:.1f}%"
        self.callback = callback
        self.rect = QRect()


class GridPercentView(QWidget):
    """
    Grade horizontal de indicadores percentuais.

    Cada indicador mostra nome, valor percentual e uma barra de
    preenchimento que reflete a porcentagem atual. Suporta tooltip
    individual por item e callback ao clicar.
    """

    item_clicked = Signal(str, float)  # key, value

    # Constantes visuais — usam tokens do tema via AppStyles
    _ITEM_PADDING_H = 8   # padding horizontal interno
    _ITEM_MARGIN   = 4   # margem entre itens
    _BAR_HEIGHT    = 3   # altura da barra de preenchimento
    _ITEM_MIN_W    = 90  # largura mínima por item (2 itens = 180px)

    def __init__(
        self,
        config: Dict[str, Dict[str, Any]],
        parent: Optional[QWidget] = None,
    ):
        super().__init__(parent)
        self._items: Dict[str, _PercentItem] = {}
        self._hovered_key: Optional[str] = None

        # Altura fixa compatível com MenuBar (30px)
        self.setFixedHeight(28)
        self.setMouseTracking(True)

        # Cores via AppStyles (skill de estilos — zero hardcoded)
        self._p_colors = AppStyles.grid_percent_colors()

        # Constrói itens a partir do config
        for key, cfg in config.items():
            self._items[key] = _PercentItem(
                label=cfg.get("label", key.upper()),
                value=cfg.get("value", 0.0),
                tooltip=cfg.get("tooltip", ""),
                callback=cfg.get("callback"),
            )

        self._update_global_tooltip()

    # ── Size hints ─────────────────────────────────────────────────

    def sizeHint(self) -> QSize:
        """Largura mínima: 90px por item (CPU + RAM = 180px)."""
        n = len(self._items)
        w = n * self._ITEM_MIN_W + (n - 1) * self._ITEM_MARGIN
        return QSize(max(w, 180), 28)

    def minimumSizeHint(self) -> QSize:
        return QSize(180, 28)

    # ── API pública ────────────────────────────────────────────────

    def set(self, key: str, value: float, tooltip: Optional[str] = None) -> None:
        """
        Atualiza o valor de um indicador.

        Args:
            key: Chave do indicador (ex: "cpu").
            value: Novo valor percentual (0-100).
            tooltip: Tooltip especifico deste item. Se None, gera automatico.
        """
        item = self._items.get(key)
        if item is None:
            return
        item.value = value
        if tooltip:
            item.tooltip = tooltip
        else:
            item.tooltip = f"{item.label}: {value:.1f}%"
        self._update_global_tooltip()
        self.update()

    def get(self, key: str) -> float:
        """Retorna o valor atual de um indicador."""
        item = self._items.get(key)
        return item.value if item else 0.0

    @property
    def values(self) -> Dict[str, float]:
        """Retorna dict com todos os valores atuais."""
        return {k: v.value for k, v in self._items.items()}

    # ── Internos ───────────────────────────────────────────────────

    def _update_global_tooltip(self) -> None:
        """
        Tooltip global do widget (fallback quando mouse fora de item).
        Mostra todos os valores em uma linha.
        """
        parts = [f"{v.label}: {v.value:.1f}%" for v in self._items.values()]
        self.setToolTip("  ".join(parts))

    def _item_at(self, pos_x: int) -> Optional[str]:
        """Retorna a key do item na posição x."""
        for key, item in self._items.items():
            if item.rect.contains(int(pos_x), self.rect().center().y()):
                return key
        return None

    # ── Eventos ────────────────────────────────────────────────────

    def mouseMoveEvent(self, event):
        """
        Ao passar o mouse sobre um item, exibe o tooltip especifico
        daquele item (CPU mostra info de CPU, RAM mostra info de RAM).
        """
        key = self._item_at(event.position().x())
        if key:
            item = self._items[key]
            # Tooltip individual do item hovered
            self.setToolTip(item.tooltip)
            self.setCursor(
                Qt.PointingHandCursor if item.callback else Qt.ArrowCursor
            )
        else:
            self.setCursor(Qt.ArrowCursor)
            self._update_global_tooltip()
        self._hovered_key = key
        super().mouseMoveEvent(event)

    def leaveEvent(self, event):
        """Limpa hover ao sair."""
        self._hovered_key = None
        self._update_global_tooltip()
        self.setCursor(Qt.ArrowCursor)
        super().leaveEvent(event)

    def mousePressEvent(self, event):
        """Emite item_clicked se o item tem callback."""
        if event.button() == Qt.LeftButton:
            key = self._item_at(event.position().x())
            if key:
                item = self._items[key]
                if item.callback:
                    item.callback(key, item.value)
                    self.item_clicked.emit(key, item.value)
        super().mousePressEvent(event)

    # ── Paint ──────────────────────────────────────────────────────

    def paintEvent(self, event):
        """Desenha cada item com label, valor e barra de preenchimento."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        pc = self._p_colors
        x = self._ITEM_MARGIN
        font_label = QFont("Consolas", 10)
        font_value = QFont("Consolas", 10, QFont.Weight.Bold)

        for key, item in self._items.items():
            # Label
            painter.setFont(font_label)
            painter.setPen(QColor(pc["label_fg"]))
            label_w = painter.fontMetrics().horizontalAdvance(item.label + ": ")

            # Valor
            painter.setFont(font_value)
            val_text = f"{item.value:.0f}%"
            val_w = painter.fontMetrics().horizontalAdvance(val_text)

            item_w = label_w + val_w + self._ITEM_PADDING_H * 2
            item_h = self.height()
            item_rect = QRect(x, 0, item_w, item_h)
            item.rect = item_rect

            # Fundo do item (hover)
            if self._hovered_key == key:
                painter.fillRect(item_rect, QColor(pc["hover_bg"]))

            # Label
            painter.setFont(font_label)
            painter.setPen(QColor(pc["label_fg"]))
            painter.drawText(
                x + self._ITEM_PADDING_H, 0,
                label_w, item_h - self._BAR_HEIGHT - 4,
                Qt.AlignLeft | Qt.AlignBottom,
                item.label + ": ",
            )

            # Valor
            painter.setFont(font_value)
            val_color = pc["value_fg_hover"] if self._hovered_key == key else pc["value_fg"]
            painter.setPen(QColor(val_color))
            painter.drawText(
                x + self._ITEM_PADDING_H + label_w, 0,
                val_w, item_h - self._BAR_HEIGHT - 4,
                Qt.AlignLeft | Qt.AlignBottom,
                val_text,
            )

            # Barra de preenchimento
            bar_y = item_h - self._BAR_HEIGHT - 2
            bar_w = item_w - self._ITEM_PADDING_H * 2
            bar_rect = QRect(x + self._ITEM_PADDING_H, bar_y, bar_w, self._BAR_HEIGHT)

            # Fundo da barra
            painter.fillRect(bar_rect, QColor(pc["bar_bg"]))

            # Preenchimento proporcional
            fill_w = int(bar_w * min(item.value, 100.0) / 100.0)
            if fill_w > 0:
                fill_rect = QRect(bar_rect.x(), bar_rect.y(), fill_w, bar_rect.height())
                painter.fillRect(fill_rect, QColor(pc["bar_fill"]))

            # Borda sutil da barra
            painter.setPen(QPen(QColor(pc["bar_border"]), 1))
            painter.drawRect(bar_rect)

            x += item_w + self._ITEM_MARGIN

        painter.end()