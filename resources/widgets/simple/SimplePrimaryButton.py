# -*- coding: utf-8 -*-
"""
SimplePrimaryButton — Botão primário com gradiente ouro e efeito glow.
Uso: executar pipeline, ações principais.
Aplica glow dourado via QGraphicsDropShadowEffect quando o tema define
GLOW_BLUR > 0 e GLOW_ALPHA > 0.
"""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QPushButton

from resources.styles.AppStyles import AppStyles
from resources.styles.BaseStyle import BaseStyle
from resources.styles.ThemeManager import ct


class SimplePrimaryButton(QPushButton):
    """
    Botão primário com gradiente ouro e glow dourado.
    O glow é aplicado via QGraphicsDropShadowEffect usando os tokens
    GLOW_* do tema (GLOW_BLUR, GLOW_COLOR_RGB, GLOW_ALPHA).
    """

    def __init__(self, text: str = "EXECUTAR", parent=None):
        super().__init__(text, parent)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setStyleSheet(AppStyles.btn_primary_style())
        self.setMinimumWidth(180)
        self.setMinimumHeight(34)
        self._apply_glow()

    # ──────────────────────────────────────────────────────────────────
    # GLOW (efeito de brilho dourado) via QGraphicsDropShadowEffect
    # ──────────────────────────────────────────────────────────────────

    def _apply_glow(self) -> None:
        """Aplica glow dourado usando tokens GLOW_* do tema ativo."""
        t = ct.theme
        glow_color = t.GLOW_COLOR_RGB or t.ACCENT
        BaseStyle.apply_drop_shadow(
            self,
            blur=t.GLOW_BLUR,
            offset_x=t.GLOW_OFFSET_X,
            offset_y=t.GLOW_OFFSET_Y,
            color_rgb=glow_color,
            alpha=t.GLOW_ALPHA,
        )

    def update_glow(self) -> None:
        """
        Recria o efeito de glow (útil após troca de tema).
        Chame este método se o tema for alterado em tempo de execução.
        """
        self._apply_glow()
