# -*- coding: utf-8 -*-
"""
ThemeManager — Gerenciador central de temas
=============================================
Mantém a instância única do tema atual.
Qualquer módulo do sistema importa `ct` (current_theme) deste manager
para acessar cores, fontes, dimensões e espaçamentos centralizados.

Uso:
    from resources.styles.ThemeManager import ct
    bg = ct.BG_DARK
    btn_h = ct.BUTTON_HEIGHT
"""

from __future__ import annotations

from resources.styles.BaseTheme import BaseTheme
from resources.styles.DarkCharcoalTheme import DarkCharcoalTheme
from resources.styles.ZeroGrausTheme import ZeroGrausTheme


class ThemeManager:
    """
    Gerenciador singleton de tema.
    Para alternar o tema, mude `current_theme_class` para outra
    subclasse de BaseTheme e reinicie (ou recarregue) a UI.
    """

    # ── Altere esta linha para trocar de tema ─────────────────────
    #$current_theme_class: type[BaseTheme] = DarkCharcoalTheme
    current_theme_class: type[BaseTheme] = ZeroGrausTheme
    # ──────────────────────────────────────────────────────────────

    _instance: ThemeManager | None = None

    def __new__(cls) -> ThemeManager:
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._theme = cls.current_theme_class()
        return cls._instance

    @property
    def theme(self) -> BaseTheme:
        """Retorna a instância do tema atual."""
        return self._theme

    def reload_theme(self) -> None:
        """Recria a instância do tema a partir da class configurada."""
        self._theme = self.current_theme_class()


# ── Singleton pré-instanciado para importação direta ──────────────
# Uso: from resources.styles.ThemeManager import ct
ct = ThemeManager()