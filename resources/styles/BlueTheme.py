# -*- coding: utf-8 -*-
"""
ModernDashboardTheme
====================

Tema inspirado no dashboard:
https://dribbble.com/shots/23707627-Modern-Dashboard-UI-Design

Características visuais extraídas da referência:
- Fundo navy profundo quase preto.
- Painéis azul-escuro com leve gradiente.
- Accent azul elétrico.
- Inputs com superfície mais clara.
- Cards com cantos grandes e visual "soft".
- Texto branco com hierarquia bem definida.
- Sombras frias azuladas.
- Layout extremamente espaçado.

Este tema herda de BaseTheme e preenche os tokens mais relevantes.
"""

from __future__ import annotations

from resources.styles.BaseTheme import BaseTheme


class BlueTheme(BaseTheme):# Ajustes principais em relação à versão anterior:
# - Paleta mais clara e vibrante (azuis luminosos)
# - Menos padding
# - Heights mais compactos
# - Border radius moderado
# - Visual mais próximo do dashboard da referência


    # ==========================================================
    # ACCENT
    # ==========================================================
    ACCENT = "#1EA7FF"
    ACCENT_HOVER = "#42B8FF"
    ACCENT_ACTIVE = "#0F8CE6"
    ACCENT_DIM = "#0A5FA8"
    ACCENT_LIGHT = "#8FD6FF"
    ACCENT_SOFT = "rgba(30, 167, 255, 0.14)"
    ACCENT_TEXT = "#EAF7FF"
    ACCENT_BRIGHT = "#FFFFFF"
    ACCENT_GRADIENT = ("#2CC4FF", "#1E8BFF")

    # ==========================================================
    # SURFACES
    # ==========================================================
    SURFACE_0 = "#050B1A"
    SURFACE_1 = "#081426"
    SURFACE_2 = "#0C1D35"
    SURFACE_3 = "#102744"
    SURFACE_4 = "#183355"
    SURFACE_5 = "#21426B"
    TITLE_BAR = "#081426"

    GRADIENT_BUTTON = ("#163458", "#1E4470")
    GRADIENT_PANEL = ("#0C1D35", "#113055")
    GRADIENT_TAB = ("#102744", "#16365D")
    GRADIENT_INPUT = ("#183355", "#21426B")

    # ==========================================================
    # TEXT
    # ==========================================================
    TEXT_HIGH = "#FFFFFF"
    TEXT_MEDIUM = "#D9E9FF"
    TEXT_LOW = "#8FAFD4"
    TEXT_DISABLED = "#58739A"
    TEXT_ON_ACCENT = "#FFFFFF"
    TEXT_ON_DANGER = "#FFFFFF"

    # ==========================================================
    # BORDERS
    # ==========================================================
    BORDER_SUBTLE = "rgba(255,255,255,0.04)"
    BORDER_DEFAULT = "rgba(140,190,255,0.08)"
    BORDER_STRONG = "rgba(140,190,255,0.16)"
    BORDER_ACCENT = ACCENT
    DIVIDER = "rgba(255,255,255,0.05)"

    # ==========================================================
    # SHADOWS
    # ==========================================================
    SHADOW_SM = "rgba(0,0,0,0.16)"
    SHADOW_MD = "rgba(0,0,0,0.24)"
    SHADOW_LG = "rgba(0,0,0,0.34)"
    SHADOW_XL = "rgba(0,0,0,0.45)"
    SHADOW_ACCENT = "rgba(30,167,255,0.20)"
    GLOW = "rgba(30,167,255,0.12)"
    GLOW_STRONG = "rgba(30,167,255,0.25)"

    # ==========================================================
    # RADIUS
    # ==========================================================
    RADIUS_XS = 3
    RADIUS_SM = 6
    RADIUS_MD = 8
    RADIUS_LG = 12
    RADIUS_XL = 16
    RADIUS_FULL = 999

    # ==========================================================
    # SPACING
    # ==========================================================
    SPACE_XXS = 2
    SPACE_XS = 4
    SPACE_SM = 6
    SPACE_MD = 10
    SPACE_LG = 14
    SPACE_XL = 20
    SPACE_2XL = 28
    SPACE_3XL = 40

    # ==========================================================
    # FONT
    # ==========================================================
    FONT_FAMILY_DEFAULT = "'Segoe UI', 'Inter', sans-serif"
    FONT_FAMILY_MONO = "'Cascadia Code', 'Consolas', monospace"

    FONT_SIZE_TITLE = 32
    FONT_SIZE_BIG = 18
    FONT_SIZE_NORMAL = 12
    FONT_SIZE_SMALL = 11
    FONT_SIZE_TINY = 10

    FONT_WEIGHT_NORMAL = 400
    FONT_WEIGHT_BOLD = 600
    FONT_WEIGHT_EXTRABOLD = 700
    FONT_WEIGHT_HEAVY = 800

    # ==========================================================
    # DIMENSIONS
    # ==========================================================
    INPUT_HEIGHT = 34
    BUTTON_HEIGHT = 34
    BUTTON_HEIGHT_PRIMARY = 38
    ITEM_HEIGHT = 30
    CHECKBOX_SIZE = 16
    RADIO_SIZE = 16
    SCROLLBAR_WIDTH = 8
    SCROLLBAR_MIN_HEIGHT = 24
    TAB_HEIGHT = 32
    TAB_CLOSE_BUTTON_SIZE = 12
    CLOSE_BUTTON_BORDER_RADIUS = 6
    PROGRESS_BAR_HEIGHT = 8
    TITLE_BTN_HEIGHT = 30
    TITLE_BTN_WIDTH = 44
    TITLE_BTN_FONT_SIZE = 13
    GROUP_MARGIN_TOP = 14
    SPLITTER_HANDLE_WIDTH = 3

    # ==========================================================
    # LAYOUT
    # ==========================================================
    PAGE_PADDING = 18
    SECTION_GAP = 18
    GRID_GAP = 14
    CONTENT_MAX_WIDTH = 1600

    # ==========================================================
    # STATUS
    # ==========================================================
    COLOR_SUCCESS = "#22C55E"
    COLOR_SUCCESS_HOVER = "#34D399"
    COLOR_SUCCESS_DIM = "#14532D"

    COLOR_WARNING = "#F59E0B"
    COLOR_WARNING_HOVER = "#FBBF24"
    COLOR_WARNING_DIM = "#78350F"

    COLOR_DANGER = "#EF4444"
    COLOR_DANGER_HOVER = "#F87171"
    COLOR_DANGER_DIM = "#7F1D1D"

    COLOR_INFO = "#38BDF8"
    COLOR_INFO_HOVER = "#7DD3FC"
    COLOR_INFO_DIM = "#0C4A6E"

    # ==========================================================
    # SPECIFIC RADII
    # ==========================================================
    BORDER_RADIUS_CARD = 14
    BORDER_RADIUS_BUTTON = 999
    BORDER_RADIUS_INPUT = 8
    BORDER_RADIUS_CHECKBOX = 4
    BORDER_RADIUS_RADIO = 999
    BORDER_RADIUS_BADGE = 999
    BORDER_RADIUS_PROGRESS = 999
    BORDER_RADIUS_TABLE = 12
    BORDER_RADIUS_TITLE_BTN = 6
    BORDER_RADIUS_TOOLBAR_BTN = 999
    BORDER_RADIUS_GHOST = 999
    BORDER_RADIUS_TOOL_SELECTOR = 999
    BORDER_RADIUS_SCROLLBAR = 999
    BORDER_RADIUS_SPINBOX_BTN = 4
    BORDER_RADIUS_TAB_CLOSE = 999
    BORDER_RADIUS_COMBO_POPUP = 10
    BORDER_RADIUS_MENU = 12
    BORDER_RADIUS_MENU_ITEM = 8
    BORDER_RADIUS_GROUP_TITLE = 6
    BORDER_RADIUS_DIALOG = 16
    MENUBAR_ITEM_BORDER_RADIUS = "6px"

    # ==========================================================
    # PADDINGS
    # ==========================================================
    BADGE_PADDING_V = "2px"
    BADGE_PADDING_H = "8px"
    BADGE_LETTER_SPACING = "0.3px"

    BUTTON_PADDING_V = "2px"
    BUTTON_PADDING_H = "2px"
    BUTTON_PADDING_V_SMALL = "2px"
    BUTTON_PADDING_H_SMALL = "2px"
    BUTTON_PADDING_V_PRIMARY = "2px"
    BUTTON_PADDING_H_PRIMARY = "2px"

    BUTTON_LETTER_SPACING_NORMAL = "0.2px"
    BUTTON_LETTER_SPACING_PRIMARY = "0.4px"

    TOOLBAR_BTN_PADDING_V = "6px"
    TOOLBAR_BTN_PADDING_H = "10px"

    TOOL_SELECTOR_PADDING_V = "6px"
    TOOL_SELECTOR_PADDING_H = "10px"
    TOOL_SELECTOR_LETTER_SPACING = "0.3px"

    INPUT_PADDING_V = "6px"
    INPUT_PADDING_H = "10px"

    SPINBOX_PADDING = "4px 8px"
    SPINBOX_BTN_WIDTH = 18
    SPINBOX_BTN_MARGIN = "1px"

    COMBOBOX_PADDING = "6px 10px"
    COMBOBOX_MIN_WIDTH = 100
    COMBOBOX_DROPDOWN_WIDTH = 22
    COMBOBOX_ARROW_SIZE = "4px"
    COMBOBOX_POPUP_BORDER_RADIUS = 10

    TEXT_EDIT_PADDING = "10px"
    TEXT_EDIT_FONT_SIZE = 11

    GROUP_TITLE_LEFT = 8
    GROUP_TITLE_TOP = -6
    GROUP_TITLE_PADDING = "2px 6px"
    GROUP_TITLE_BORDER_RADIUS = 6
    GROUP_TITLE_LETTER_SPACING = "0.3px"

    HEADER_FONT_SIZE = 10
    HEADER_LETTER_SPACING = "0.3px"
    TABLE_ITEM_PADDING = "6px"
    HEADER_PADDING = "8px 10px"

    WINDOW_TITLE_FONT_SIZE = 11
    WINDOW_TITLE_LETTER_SPACING = "0.2px"

    CARD_PADDING_V = 14
    CARD_PADDING_H = 14

    MENU_PADDING = "6px"
    MENU_MARGIN_V = "4px"
    MENU_ITEM_PADDING = "6px 10px"
    MENU_SEPARATOR_HEIGHT = "1px"
    MENU_SEPARATOR_MARGIN = "4px 6px"

    CHECKBOX_BORDER_WIDTH = 1
    CHECKBOX_SPACING = 6

    # ==========================================================
    # LEGACY ALIASES
    # ==========================================================
    BG_DEEPEST = SURFACE_0
    BG_DARK = SURFACE_1
    BG_PANEL = SURFACE_2
    BG_CARD = SURFACE_3
    BG_ELEVATED = SURFACE_4
    BG_SURFACE = SURFACE_5
    TITLE_BAR_BG = TITLE_BAR

    SHADOW = SHADOW_MD
    SHADOW_DEEP = SHADOW_LG

    BORDER = BORDER_DEFAULT
    BORDER_HOVER = BORDER_STRONG

    TEXT_BRIGHT = TEXT_HIGH
    TEXT_PRIMARY = TEXT_HIGH
    TEXT_SECONDARY = TEXT_MEDIUM
    TEXT_MUTED = TEXT_LOW
    TEXT_GOLD = ACCENT_TEXT
    TEXT_GOLD_BRIGHT = ACCENT_BRIGHT

    GOLD = ACCENT
    GOLD_HOVER = ACCENT_HOVER
    GOLD_ACTIVE = ACCENT_ACTIVE
    GOLD_DIM = ACCENT_DIM
    GOLD_LIGHT = ACCENT_LIGHT
    GOLD_GRADIENT = ACCENT_GRADIENT

    SUCCESS = COLOR_SUCCESS
    SUCCESS_HOVER = COLOR_SUCCESS_HOVER
    SUCCESS_DIM = COLOR_SUCCESS_DIM

    WARNING = COLOR_WARNING
    WARNING_HOVER = COLOR_WARNING_HOVER
    WARNING_DIM = COLOR_WARNING_DIM

    DANGER = COLOR_DANGER
    DANGER_HOVER = COLOR_DANGER_HOVER
    DANGER_DIM = COLOR_DANGER_DIM

    COLOR_INFO = COLOR_INFO
    COLOR_INFO_HOVER = COLOR_INFO_HOVER
    COLOR_INFO_DIM = COLOR_INFO_DIM