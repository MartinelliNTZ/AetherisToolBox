# -*- coding: utf-8 -*-
"""
SimpleThemeButton — Botão 100% autossuficiente com estilo vindo do tema.
=======================================================================
Diferente dos outros botões (SimplePrimaryButton, SimpleSecondaryButton),
este widget NÃO depende do AppStyles para gerar QSS. Ele importa
diretamente o singleton `theme_manager` e constrói todo o stylesheet
internamente usando os tokens do tema ativo.

Isolamento total:
  - Nenhum método do AppStyles é chamado para estilização.
  - A única importação externa de estilo é `BaseStyle.apply_drop_shadow`
    para o efeito glow (utilitário de sombra, não de estilo visual).
  - O border-radius vem exclusivamente de `theme.BORDER_RADIUS_BUTTON`.
  - Comportamentos booleanos (glow, etc.) são controlados por tokens
    do tema (GLOW_BUTTON_ENABLED, etc.).

Uso:
    btn = SimpleThemeButton("EXECUTAR")
    btn = SimpleThemeButton("SALVAR", min_width=140, shadow_enabled=True)
"""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QPushButton

from resources.styles.BaseStyle import BaseStyle
from resources.styles.ThemeManager import theme_manager


class SimpleThemeButton(QPushButton):
    """
    Botão temático autossuficiente.

    Todo o QSS é gerado internamente a partir dos tokens do tema ativo.
    Nenhuma dependência do AppStyles para estilização.

    Args:
        text: Texto exibido no botão.
        parent: Widget pai.
        min_width: Largura mínima em pixels. 0 = sem mínimo.
        min_height: Altura mínima em pixels. 0 = sem mínimo.
        shadow_enabled: Se True, aplica glow via QGraphicsDropShadowEffect
                        usando os tokens GLOW_* do tema.
    """

    def __init__(
        self,
        text: str = "BOTÃO",
        parent=None,
        *,
        min_width: int = 180,
        min_height: int = 34,
        shadow_enabled: bool = True,
        border_radius: int | None = None,
    ):
        super().__init__(text, parent)

        self._shadow_enabled = shadow_enabled
        self._border_radius = border_radius

        self.setCursor(Qt.CursorShape.PointingHandCursor)

        if min_width > 0:
            self.setMinimumWidth(min_width)
        if min_height > 0:
            self.setMinimumHeight(min_height)

        self._refresh_style()
        self._apply_glow()

    # ──────────────────────────────────────────────────────────────────
    # API PÚBLICA
    # ──────────────────────────────────────────────────────────────────

    def update_theme(self) -> None:
        """
        Reaplica o estilo e o glow (útil após troca de tema em runtime).
        Chame este método se o tema for alterado em tempo de execução.
        """
        self._refresh_style()
        self._apply_glow()

    def set_shadow_enabled(self, enabled: bool) -> None:
        """Ativa ou desativa o efeito de glow."""
        self._shadow_enabled = enabled
        self._apply_glow()

    # ──────────────────────────────────────────────────────────────────
    # INTERNOS — Geração de QSS 100% via tokens do tema
    # ──────────────────────────────────────────────────────────────────

    def _build_stylesheet(self) -> str:
        """
        Constrói o QSS completo usando APENAS tokens do tema ativo.
        Sem chamadas ao AppStyles. Sem valores hardcoded.
        """
        t = theme_manager.theme

        # Gradiente de fundo (fallback para ACCENT_GRADIENT se não houver stops)
        stops = t.GRADIENT_ACCENT_STOPS
        if stops:
            bg_gradient = BaseStyle._gradient_qss_from_stops(
                stops,
                t.GRADIENT_ACCENT_ANGLE,
                t.ACCENT_GRADIENT[0],
                t.ACCENT_GRADIENT[1],
                gradient_type=t.GRADIENT_ACCENT_TYPE,
                cx=t.GRADIENT_RADIAL_CX,
                cy=t.GRADIENT_RADIAL_CY,
                fx=t.GRADIENT_RADIAL_FX,
                fy=t.GRADIENT_RADIAL_FY,
                radius=t.GRADIENT_RADIAL_RADIUS,
            )
        else:
            bg_gradient = (
                f"qlineargradient(x1:0, y1:0, x2:0, y2:1, "
                f"stop:0 {t.ACCENT_GRADIENT[0]}, "
                f"stop:1 {t.ACCENT_GRADIENT[1]})"
            )

        # Gradiente hover (simplificado: ACCENT_HOVER -> ACCENT)
        hover_gradient = (
            f"qlineargradient(x1:0, y1:0, x2:0, y2:1, "
            f"stop:0 {t.ACCENT_HOVER}, "
            f"stop:1 {t.ACCENT})"
        )

        border_radius = self._border_radius if self._border_radius is not None else t.BORDER_RADIUS_BUTTON
        padding_v = t.BUTTON_PADDING_V_PRIMARY
        padding_h = t.BUTTON_PADDING_H_PRIMARY
        font_weight = t.BUTTON_FONT_WEIGHT_PRIMARY or t.FONT_WEIGHT_HEAVY
        font_size = t.BUTTON_FONT_SIZE_PRIMARY or t.FONT_SIZE_NORMAL
        letter_spacing = t.BUTTON_LETTER_SPACING_PRIMARY

        return (
            f"QPushButton {{"
            f"  background: {bg_gradient};"
            f"  color: {t.TEXT_ON_ACCENT};"
            f"  border: none;"
            f"  border-radius: {border_radius}px;"
            f"  padding: {padding_v}px {padding_h}px;"
            f"  font-weight: {font_weight};"
            f"  font-size: {font_size}px;"
            f"min-height: 60px;"
            f"  letter-spacing: {letter_spacing}px;"
            f"}}"
            f"QPushButton:hover {{"
            f"  background: {hover_gradient};"
            f"}}"
            f"QPushButton:pressed {{"
            f"  background: {t.ACCENT_ACTIVE};"
            f"}}"
            f"QPushButton:disabled {{"
            f"  background-color: {t.SURFACE_3};"
            f"  color: {t.TEXT_DISABLED};"
            f"  border: none;"
            f"  border-radius: {border_radius}px;"
            f"}}"
        )

    def _refresh_style(self) -> None:
        """Aplica o stylesheet gerado internamente."""
        self.setStyleSheet(self._build_stylesheet())

    def _apply_glow(self) -> None:
        """
        Aplica glow via QGraphicsDropShadowEffect usando tokens do tema.
        Controlado por GLOW_BUTTON_ENABLED e GLOW_BLUR/GLOW_ALPHA.
        """
        if not self._shadow_enabled:
            self.setGraphicsEffect(None)
            return

        t = theme_manager.theme
        if not t.GLOW_BUTTON_ENABLED:
            self.setGraphicsEffect(None)
            return

        blur = t.GLOW_BLUR
        alpha = t.GLOW_ALPHA

        if blur <= 0 or alpha <= 0:
            self.setGraphicsEffect(None)
            return

        glow_color = t.GLOW_COLOR_RGB or t.ACCENT

        BaseStyle.apply_drop_shadow(
            self,
            blur=blur,
            offset_x=t.GLOW_OFFSET_X,
            offset_y=t.GLOW_OFFSET_Y,
            color_rgb=glow_color,
            alpha=alpha,
        )