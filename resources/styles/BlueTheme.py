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


class BlueTheme(BaseTheme):
    # ==========================================================
    # ACCENT
    # ==========================================================
    ACCENT = "#4F7DFF"
    ACCENT_HOVER = "#6B93FF"
    ACCENT_ACTIVE = "#3B67E8"
    ACCENT_DIM = "#2C4DB4"
    ACCENT_LIGHT = "#AFC3FF"
    ACCENT_SOFT = "rgba(79, 125, 255, 0.16)"
    ACCENT_TEXT = "#DCE7FF"
    ACCENT_BRIGHT = "#C8D7FF"
    ACCENT_GRADIENT = ("#6F98FF", "#4F7DFF")

    # ==========================================================
    # SURFACES
    # ==========================================================
    SURFACE_0 = "#050A16"   # backdrop
    SURFACE_1 = "#081223"   # janela principal
    SURFACE_2 = "#0C1830"   # sidebars/toolbars
    SURFACE_3 = "#10203D"   # cards
    SURFACE_4 = "#1A2D4F"   # inputs
    SURFACE_5 = "#243A63"   # hover/focus
    TITLE_BAR = "#07111F"

    GRADIENT_BUTTON = ("#14284A", "#1B345E")
    GRADIENT_PANEL = ("#0A1427", "#0E1B33")
    GRADIENT_TAB = ("#0F1D38", "#16294A")
    GRADIENT_INPUT = ("#1A2D4F", "#21375E")

    # ==========================================================
    # TEXT
    # ==========================================================
    TEXT_HIGH = "#FFFFFF"
    TEXT_MEDIUM = "#D5E2FF"
    TEXT_LOW = "#8FA8D8"
    TEXT_DISABLED = "#51688E"
    TEXT_ON_ACCENT = "#FFFFFF"
    TEXT_ON_DANGER = "#FFFFFF"

    # ==========================================================
    # BORDERS
    # ==========================================================
    BORDER_SUBTLE = "rgba(255,255,255,0.03)"
    BORDER_DEFAULT = "rgba(120,160,255,0.08)"
    BORDER_STRONG = "rgba(120,160,255,0.18)"
    BORDER_ACCENT = ACCENT
    DIVIDER = "rgba(255,255,255,0.05)"

    # ==========================================================
    # SHADOWS
    # ==========================================================
    SHADOW_SM = "rgba(0,0,0,0.18)"
    SHADOW_MD = "rgba(0,0,0,0.28)"
    SHADOW_LG = "rgba(0,0,0,0.42)"
    SHADOW_XL = "rgba(0,0,0,0.55)"
    SHADOW_ACCENT = "rgba(79,125,255,0.35)"
    GLOW = "rgba(79,125,255,0.18)"
    GLOW_STRONG = "rgba(79,125,255,0.35)"

    # ==========================================================
    # RADIUS
    # ==========================================================
    RADIUS_XS = 4
    RADIUS_SM = 8
    RADIUS_MD = 12
    RADIUS_LG = 18
    RADIUS_XL = 24
    RADIUS_FULL = 999

    # ==========================================================
    # SPACING
    # ==========================================================
    SPACE_XXS = 2
    SPACE_XS = 4
    SPACE_SM = 8
    SPACE_MD = 12
    SPACE_LG = 16
    SPACE_XL = 24
    SPACE_2XL = 32
    SPACE_3XL = 48

    # ==========================================================
    # ICONS
    # ==========================================================
    ICON_XS = 12
    ICON_SM = 16
    ICON_MD = 20
    ICON_LG = 24
    ICON_XL = 32

    # ==========================================================
    # ANIMATION
    # ==========================================================
    ANIMATION_FAST = 120
    ANIMATION_NORMAL = 180
    ANIMATION_SLOW = 260
    EASING_STANDARD = "cubic-bezier(0.4, 0.0, 0.2, 1)"

    # ==========================================================
    # OPACITY
    # ==========================================================
    OPACITY_DISABLED = 0.45
    OPACITY_MUTED = 0.65
    OPACITY_HOVER = 0.92
    OPACITY_ACTIVE = 1.0

    # ==========================================================
    # LAYOUT
    # ==========================================================
    PAGE_PADDING = 24
    SECTION_GAP = 24
    GRID_GAP = 20
    CONTENT_MAX_WIDTH = 1600

    # ==========================================================
    # ELEVATION
    # ==========================================================
    ELEVATION_FLAT = 0
    ELEVATION_LOW = 1
    ELEVATION_MEDIUM = 2
    ELEVATION_HIGH = 3

    # ==========================================================
    # OVERLAY
    # ==========================================================
    OVERLAY_BG = "rgba(5, 10, 22, 0.80)"
    BACKDROP_BLUR = "8px"

    # ==========================================================
    # FOCUS RING
    # ==========================================================
    FOCUS_RING_COLOR = "rgba(79,125,255,0.35)"
    FOCUS_RING_WIDTH = "2px"
    FOCUS_RING_OFFSET = "1px"

    # ==========================================================
    # STATUS COLORS
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
    # FONT
    # ==========================================================
    FONT_FAMILY_DEFAULT = "'Segoe UI', 'Inter', sans-serif"
    FONT_FAMILY_MONO = "'Cascadia Code', 'Consolas', monospace"

    FONT_SIZE_TITLE = 38
    FONT_SIZE_BIG = 20
    FONT_SIZE_NORMAL = 13
    FONT_SIZE_SMALL = 12
    FONT_SIZE_TINY = 11

    FONT_WEIGHT_NORMAL = 400
    FONT_WEIGHT_BOLD = 600
    FONT_WEIGHT_EXTRABOLD = 700
    FONT_WEIGHT_HEAVY = 800

    # ==========================================================
    # DIMENSIONS
    # ==========================================================
    INPUT_HEIGHT = 40
    BUTTON_HEIGHT = 40
    BUTTON_HEIGHT_PRIMARY = 44
    ITEM_HEIGHT = 34
    CHECKBOX_SIZE = 18
    RADIO_SIZE = 18
    SCROLLBAR_WIDTH = 10
    SCROLLBAR_MIN_HEIGHT = 30
    TAB_HEIGHT = 36
    TAB_CLOSE_BUTTON_SIZE = 14
    CLOSE_BUTTON_BORDER_RADIUS = 7
    PROGRESS_BAR_HEIGHT = 10
    TITLE_BTN_HEIGHT = 32
    TITLE_BTN_WIDTH = 46
    TITLE_BTN_FONT_SIZE = 14
    GROUP_MARGIN_TOP = 18
    SPLITTER_HANDLE_WIDTH = 4

    # ==========================================================
    # BORDER RADIUS MAPPINGS
    # ==========================================================
    BORDER_RADIUS_CARD = RADIUS_XL
    BORDER_RADIUS_BUTTON = RADIUS_FULL
    BORDER_RADIUS_INPUT = RADIUS_MD
    BORDER_RADIUS_CHECKBOX = 5
    BORDER_RADIUS_RADIO = RADIUS_FULL
    BORDER_RADIUS_BADGE = RADIUS_FULL
    BORDER_RADIUS_PROGRESS = RADIUS_FULL
    BORDER_RADIUS_TABLE = RADIUS_LG
    BORDER_RADIUS_TITLE_BTN = RADIUS_SM
    BORDER_RADIUS_TOOLBAR_BTN = RADIUS_FULL
    BORDER_RADIUS_GHOST = RADIUS_FULL
    BORDER_RADIUS_TOOL_SELECTOR = RADIUS_FULL
    BORDER_RADIUS_SCROLLBAR = RADIUS_FULL
    BORDER_RADIUS_SPINBOX_BTN = RADIUS_SM
    BORDER_RADIUS_TAB_CLOSE = RADIUS_FULL
    BORDER_RADIUS_COMBO_POPUP = RADIUS_LG
    BORDER_RADIUS_MENU = RADIUS_LG
    BORDER_RADIUS_MENU_ITEM = RADIUS_MD
    BORDER_RADIUS_GROUP_TITLE = RADIUS_SM
    BORDER_RADIUS_DIALOG = RADIUS_XL
    MENUBAR_ITEM_BORDER_RADIUS = "8px"

    # ==========================================================
    # PADDING / LETTER SPACING
    # ==========================================================
    CHECKBOX_BORDER_WIDTH = 1
    CHECKBOX_SPACING = 8

    BADGE_PADDING_V = "3px"
    BADGE_PADDING_H = "10px"
    BADGE_LETTER_SPACING = "0.4px"

    BUTTON_PADDING_V = "10px"
    BUTTON_PADDING_H = "18px"
    BUTTON_PADDING_V_SMALL = "6px"
    BUTTON_PADDING_H_SMALL = "10px"
    BUTTON_PADDING_V_PRIMARY = "12px"
    BUTTON_PADDING_H_PRIMARY = "24px"
    BUTTON_LETTER_SPACING_NORMAL = "0.2px"
    BUTTON_LETTER_SPACING_PRIMARY = "0.6px"

    TOOLBAR_BTN_PADDING_V = "8px"
    TOOLBAR_BTN_PADDING_H = "12px"

    TOOL_SELECTOR_PADDING_V = "8px"
    TOOL_SELECTOR_PADDING_H = "12px"
    TOOL_SELECTOR_LETTER_SPACING = "0.5px"

    INPUT_PADDING_V = "8px"
    INPUT_PADDING_H = "12px"

    SPINBOX_PADDING = "6px 10px"
    SPINBOX_BTN_WIDTH = 18
    SPINBOX_BTN_MARGIN = "2px"

    COMBOBOX_PADDING = "8px 12px"
    COMBOBOX_MIN_WIDTH = 120
    COMBOBOX_DROPDOWN_WIDTH = 24
    COMBOBOX_ARROW_SIZE = "4px"
    COMBOBOX_POPUP_BORDER_RADIUS = RADIUS_LG

    TEXT_EDIT_PADDING = "12px"
    TEXT_EDIT_FONT_SIZE = 12

    GROUP_TITLE_LEFT = 10
    GROUP_TITLE_TOP = -8
    GROUP_TITLE_PADDING = "2px 8px"
    GROUP_TITLE_BORDER_RADIUS = RADIUS_SM
    GROUP_TITLE_LETTER_SPACING = "0.4px"

    LETTER_SPACING_TITLE = "-0.5px"
    LETTER_SPACING_BADGE = "0.4px"
    LETTER_SPACING_GROUP = "0.4px"
    LETTER_SPACING_BUTTON = "0.2px"
    LETTER_SPACING_BUTTON_PRIMARY = "0.6px"
    LETTER_SPACING_HEADER = "0.4px"
    LETTER_SPACING_TOOL_SELECTOR = "0.5px"
    LETTER_SPACING_WINDOW_TITLE = "0.2px"

    WINDOW_TITLE_FONT_SIZE = 12
    WINDOW_TITLE_LETTER_SPACING = "0.2px"

    TITLE_BAR_BORDER_WIDTH = "1px"
    TITLE_BAR_BORDER_COLOR = BORDER_SUBTLE

    CARD_PADDING_V = 20
    CARD_PADDING_H = 20

    SPLITTER_HANDLE_WIDTH_H = 4
    SPLITTER_HANDLE_WIDTH_V = 4

    MENU_PADDING = "8px"
    MENU_MARGIN_V = "6px"
    MENU_ITEM_PADDING = "8px 14px"
    MENU_SEPARATOR_HEIGHT = "1px"
    MENU_SEPARATOR_MARGIN = "6px 8px"

    HEADER_FONT_SIZE = 11
    HEADER_LETTER_SPACING = "0.5px"
    TABLE_ITEM_PADDING = "8px"
    HEADER_PADDING = "10px 12px"

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