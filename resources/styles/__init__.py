# -*- coding: utf-8 -*-
"""
resources/styles — Sistema de estilos e temas do Aetheris ToolBox
=================================================================

Estrutura:
    BaseTheme      : Classe base abstrata com TODAS as variáveis de tema
    DarkCharcoalTheme : Tema concreto (Dark Charcoal + Gold)
    ThemeManager   : Singleton que mantém o tema ativo
    BaseStyle      : Estilos globais Qt usando o tema
    AppStyles      : Herda BaseStyle + botões, badges, logs, menus

Uso moderno (preferido):
    from resources.styles.ThemeManager import ct
    color = ct.theme.GOLD
    stylesheet = AppStyles.global_stylesheet()

Compatibilidade retroativa:
    from resources.styles.styles import Palette, AppStyles
    # Funciona normalmente — styles.py redireciona para a nova estrutura
"""

from resources.styles.AppStyles import AppStyles
from resources.styles.BaseStyle import BaseStyle
from resources.styles.BaseTheme import BaseTheme
from resources.styles.DarkCharcoalTheme import DarkCharcoalTheme
from resources.styles.ThemeManager import ThemeManager, ct