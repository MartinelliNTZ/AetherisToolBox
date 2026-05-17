# -*- coding: utf-8 -*-
"""
styles.py — Ponte de compatibilidade retroativa
=================================================
Redireciona imports legados para a nova estrutura modular de temas.

Uso moderno (preferido):
    from resources.styles.ThemeManager import ct
    color = ct.theme.BG_DARK
    stylesheet = AppStyles.global_stylesheet()

Uso legado (ainda funcional):
    from resources.styles.styles import Palette, AppStyles, DarkCharcoalStyle
"""

from __future__ import annotations

from resources.styles.DarkCharcoalTheme import DarkCharcoalTheme as Palette
from resources.styles.AppStyles import AppStyles


class DarkCharcoalStyle:
    """Classe de compatibilidade legada. Usar AppStyles ou ct.theme diretamente."""

    DARK_BG = Palette.BG_DARK
    PANEL_BG = Palette.BG_PANEL
    CARD_BG = Palette.BG_CARD
    INPUT_BG = Palette.BG_ELEVATED
    BORDER = Palette.BORDER
    TEXT_PRIMARY = Palette.TEXT_PRIMARY
    TEXT_SECONDARY = Palette.TEXT_SECONDARY
    ACCENT_GOLD = Palette.GOLD
    ACCENT_HOVER = Palette.GOLD_HOVER
    SUCCESS = Palette.SUCCESS
    WARNING = Palette.WARNING
    DANGER = Palette.DANGER
    INFO = "#5B9BD5"

    @classmethod
    def stylesheet(cls) -> str:
        """Retorna o stylesheet global (delega para AppStyles)."""
        return AppStyles.global_stylesheet()