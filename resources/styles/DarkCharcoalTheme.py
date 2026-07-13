# -*- coding: utf-8 -*-
"""
DarkCharcoalTheme — Tema concreto Dark Charcoal + Gold
=======================================================
Subclasse de BaseTheme com valores para o tema escuro atual.

Todos os grupos semânticos têm valores concretos.
Aliases de compatibilidade (BG_DARK, GOLD, etc.) apontam
para os mesmos valores → código legado continua funcionando.
"""

from __future__ import annotations

from resources.styles.BaseTheme import BaseTheme


class DarkCharcoalTheme(BaseTheme):
    """
    Tema Dark Charcoal + Gold — design minimalista com profundidade via sombras.
    """

    # ═══════════════════════════════════════════════════════════════════
    # 1. ACCENT — Dourado
    # ═══════════════════════════════════════════════════════════════════

    ACCENT = "#C9A84C"
    ACCENT_HOVER = "#D4B85A"
    ACCENT_ACTIVE = "#B8983E"
    ACCENT_DIM = "#8A7A3A"
    ACCENT_LIGHT = "#E8D08A"
    ACCENT_SOFT = "rgba(201,168,76,0.12)"
    ACCENT_TEXT = "#C9A84C"
    ACCENT_BRIGHT = "#E0C878"
    ACCENT_GRADIENT = ("#C9A84C", "#B8963A")

    # ═══════════════════════════════════════════════════════════════════
    # 2. SURFACE — Profundidade (0 = fundo, 5 = topo)
    # ═══════════════════════════════════════════════════════════════════

    SURFACE_0 = "#08080A"
    SURFACE_1 = "#0C0C0F"
    SURFACE_2 = "#121216"
    SURFACE_3 = "#18181D"
    SURFACE_4 = "#1E1E24"
    SURFACE_5 = "#24242B"
    TITLE_BAR = "#0A0A0D"

    # ── Gradientes de superfície (top-left → bottom-right) ─────
    # start = mais escuro (~ SURFACE_0 / SURFACE_2), end = SURFACE_4 / SURFACE_5
    # PANEL/TAB precisam contrastar com SURFACE_1 (fundo da janela)
    GRADIENT_BUTTON = ("#08080A", "#1E1E24")   # SURFACE_0 → SURFACE_4
    GRADIENT_PANEL = ("#121216", "#24242B")     # SURFACE_3 → SURFACE_5 (mais claro, contrasta com fundo)
    GRADIENT_TAB = ("#18181D", "#1E1E24")       # SURFACE_3 → SURFACE_4 (mais claro que fundo)
    GRADIENT_INPUT = ("#0C0C0F", "#1E1E24")    # SURFACE_1 → SURFACE_4

    # ═══════════════════════════════════════════════════════════════════
    # 3. TEXT — Hierarquia
    # ═══════════════════════════════════════════════════════════════════

    TEXT_HIGH = "#F0F0F0"
    TEXT_MEDIUM = "#DCDCDC"
    TEXT_LOW = "#888890"
    TEXT_DISABLED = "#585860"
    TEXT_ON_ACCENT = "#08080A"
    TEXT_ON_DANGER = "#FFFFFF"

    # ═══════════════════════════════════════════════════════════════════
    # 4. BORDER — Hierarquia
    # ═══════════════════════════════════════════════════════════════════

    BORDER_SUBTLE = "#1A1A20"
    BORDER_DEFAULT = "#2A2A30"
    BORDER_STRONG = "#3A3A44"
    BORDER_ACCENT = "#C9A84C"
    DIVIDER = "#1A1A20"

    # ═══════════════════════════════════════════════════════════════════
    # 5. SHADOW — Sombras
    # ═══════════════════════════════════════════════════════════════════

    SHADOW_SM = "#040405"
    SHADOW_MD = "#040405"
    SHADOW_LG = "#000000"
    SHADOW_XL = "#000000"
    SHADOW_ACCENT = "#C9A84C15"
    GLOW = "#C9A84C15"
    GLOW_STRONG = "#C9A84C25"

    # ═══════════════════════════════════════════════════════════════════
    # 6. RADIUS — Escala global
    # ═══════════════════════════════════════════════════════════════════

    RADIUS_XS = 2
    RADIUS_SM = 4
    RADIUS_MD = 6
    RADIUS_LG = 10
    RADIUS_XL = 16
    RADIUS_FULL = 999

    # ═══════════════════════════════════════════════════════════════════
    # 7. SPACE — Escala global de espaçamento
    # ═══════════════════════════════════════════════════════════════════

    SPACE_XXS = 2
    SPACE_XS = 4
    SPACE_SM = 8
    SPACE_MD = 12
    SPACE_LG = 16
    SPACE_XL = 24
    SPACE_2XL = 32
    SPACE_3XL = 48

    # ═══════════════════════════════════════════════════════════════════
    # 8. ICON — Tamanhos
    # ═══════════════════════════════════════════════════════════════════

    ICON_XS = 12
    ICON_SM = 16
    ICON_MD = 20
    ICON_LG = 24
    ICON_XL = 32
    TOOLBAR_ICON_SIZE = 34
    TOOLBAR_BTN_SIZE = 40
    TOOLBAR_BTN_HOVER_GROW = 4

    # ═══════════════════════════════════════════════════════════════════
    # 9. ANIMATION
    # ═══════════════════════════════════════════════════════════════════

    ANIMATION_FAST = 120
    ANIMATION_NORMAL = 180
    ANIMATION_SLOW = 260
    EASING_STANDARD = "cubic-bezier(0.4, 0, 0.2, 1)"

    # ═══════════════════════════════════════════════════════════════════
    # 10. OPACITY
    # ═══════════════════════════════════════════════════════════════════

    OPACITY_DISABLED = 0.35
    OPACITY_MUTED = 0.60
    OPACITY_HOVER = 0.85
    OPACITY_ACTIVE = 1.0

    # ═══════════════════════════════════════════════════════════════════
    # 11. LAYOUT
    # ═══════════════════════════════════════════════════════════════════

    PAGE_PADDING = 24
    SECTION_GAP = 24
    GRID_GAP = 20
    CONTENT_MAX_WIDTH = 1600

    # ═══════════════════════════════════════════════════════════════════
    # 12. ELEVATION
    # ═══════════════════════════════════════════════════════════════════

    ELEVATION_FLAT = 0
    ELEVATION_LOW = 1
    ELEVATION_MEDIUM = 2
    ELEVATION_HIGH = 3

    # ═══════════════════════════════════════════════════════════════════
    # 13. OVERLAY / Glass
    # ═══════════════════════════════════════════════════════════════════

    OVERLAY_BG = "rgba(8, 8, 10, 0.75)"
    BACKDROP_BLUR = "4px"

    # ═══════════════════════════════════════════════════════════════════
    # 14. FOCUS_RING
    # ═══════════════════════════════════════════════════════════════════

    FOCUS_RING_COLOR = "#C9A84C"
    FOCUS_RING_WIDTH = "2px"
    FOCUS_RING_OFFSET = "1px"

    # ═══════════════════════════════════════════════════════════════════
    # 15. STATUS
    # ═══════════════════════════════════════════════════════════════════

    COLOR_SUCCESS = "#43A047"
    COLOR_SUCCESS_HOVER = "#66BB6A"
    COLOR_SUCCESS_DIM = "#2E7D32"
    COLOR_WARNING = "#EF9A00"
    COLOR_WARNING_HOVER = "#FFB74D"
    COLOR_WARNING_DIM = "#BF6E00"
    COLOR_DANGER = "#D32F2F"
    COLOR_DANGER_HOVER = "#E53935"
    COLOR_DANGER_DIM = "#A02020"
    COLOR_INFO = "#5B9BD5"
    COLOR_INFO_HOVER = "#7BB8E8"
    COLOR_INFO_DIM = "#3A7CC2"

    # ═══════════════════════════════════════════════════════════════════
    # 16. FONT
    # ═══════════════════════════════════════════════════════════════════

    FONT_FAMILY_DEFAULT = "'Segoe UI', 'Inter', 'Roboto', sans-serif"
    FONT_FAMILY_MONO = "'Consolas', 'Courier New', monospace"

    FONT_SIZE_TITLE = 21
    FONT_SIZE_BIG = 16
    FONT_SIZE_NORMAL = 13
    FONT_SIZE_SMALL = 11
    FONT_SIZE_TINY = 10

    FONT_WEIGHT_NORMAL = 400
    FONT_WEIGHT_BOLD = 600
    FONT_WEIGHT_EXTRABOLD = 700
    FONT_WEIGHT_HEAVY = 800

    # ═══════════════════════════════════════════════════════════════════
    # 17. DIMENSIONS
    # ═══════════════════════════════════════════════════════════════════

    INPUT_HEIGHT = 24
    BUTTON_HEIGHT = 0
    BUTTON_HEIGHT_PRIMARY = 0
    ITEM_HEIGHT = 0
    CHECKBOX_SIZE = 16
    RADIO_SIZE = 16
    SCROLLBAR_WIDTH = 6
    SCROLLBAR_MIN_HEIGHT = 28
    TAB_HEIGHT = 0
    TAB_CLOSE_BUTTON_SIZE = 20
    CLOSE_BUTTON_BORDER_RADIUS = 3
    PROGRESS_BAR_HEIGHT = 18
    TITLE_BTN_HEIGHT = 22
    TITLE_BTN_WIDTH = 28
    TITLE_BTN_FONT_SIZE = 11
    GROUP_MARGIN_TOP = 8
    SPLITTER_HANDLE_WIDTH = 4

    # ═══════════════════════════════════════════════════════════════════
    # 18. SPECIFICS — BORDER_RADIUS (usam RADIUS semântico como base)
    # ═══════════════════════════════════════════════════════════════════

    BORDER_RADIUS_CARD = 10       # ≈ RADIUS_LG
    BORDER_RADIUS_BUTTON = 6       # ≈ RADIUS_MD
    BORDER_RADIUS_INPUT = 6        # ≈ RADIUS_MD
    BORDER_RADIUS_CHECKBOX = 3     # ≈ RADIUS_XS+1
    BORDER_RADIUS_RADIO = 0
    BORDER_RADIUS_BADGE = 4        # ≈ RADIUS_SM
    BORDER_RADIUS_PROGRESS = 5
    BORDER_RADIUS_TABLE = 8        # ≈ RADIUS_SM*2
    BORDER_RADIUS_TITLE_BTN = 3
    BORDER_RADIUS_TOOLBAR_BTN = 4   # ≈ RADIUS_SM
    BORDER_RADIUS_GHOST = 5
    BORDER_RADIUS_TOOL_SELECTOR = 6  # ≈ RADIUS_MD
    BORDER_RADIUS_SCROLLBAR = 3
    BORDER_RADIUS_SPINBOX_BTN = 2    # ≈ RADIUS_XS
    BORDER_RADIUS_TAB_CLOSE = 3
    BORDER_RADIUS_COMBO_POPUP = 4    # ≈ RADIUS_SM
    BORDER_RADIUS_MENU = 6          # ≈ RADIUS_MD
    BORDER_RADIUS_MENU_ITEM = 3
    BORDER_RADIUS_GROUP_TITLE = 4   # ≈ RADIUS_SM
    BORDER_RADIUS_DIALOG = 16       # ≈ RADIUS_XL
    MENUBAR_ITEM_BORDER_RADIUS = 1

    CHECKBOX_BORDER_WIDTH = 0
    CHECKBOX_SPACING = 8

    BADGE_PADDING_V = "3px"
    BADGE_PADDING_H = "12px"
    BADGE_LETTER_SPACING = "0.3px"

    BUTTON_PADDING_V = "2px"
    BUTTON_PADDING_H = "2px"
    BUTTON_PADDING_V_SMALL = "2px"
    BUTTON_PADDING_H_SMALL = "2px"
    BUTTON_PADDING_V_PRIMARY = "2px"
    BUTTON_PADDING_H_PRIMARY = "2px"
    BUTTON_LETTER_SPACING_NORMAL = "0.3px"
    BUTTON_LETTER_SPACING_PRIMARY = "0.5px"
    LETTER_SPACING_TITLE = "1px"
    LETTER_SPACING_BADGE = "0.3px"
    LETTER_SPACING_GROUP = "0.5px"
    LETTER_SPACING_BUTTON = "0.3px"
    LETTER_SPACING_BUTTON_PRIMARY = "0.5px"
    LETTER_SPACING_HEADER = "0.3px"
    LETTER_SPACING_TOOL_SELECTOR = "0.3px"
    LETTER_SPACING_WINDOW_TITLE = "0.3px"

    TOOLBAR_BTN_PADDING_V = "4px"
    TOOLBAR_BTN_PADDING_H = "10px"

    TOOL_SELECTOR_PADDING_V = "6px"
    TOOL_SELECTOR_PADDING_H = "4px"
    TOOL_SELECTOR_LETTER_SPACING = "0.3px"

    INPUT_PADDING_V = "2px"
    INPUT_PADDING_H = "2px"

    SPINBOX_PADDING = "3px 8px"
    SPINBOX_BTN_WIDTH = 16
    SPINBOX_BTN_MARGIN = "1px"

    COMBOBOX_PADDING = "3px 8px"
    COMBOBOX_MIN_WIDTH = 80
    COMBOBOX_DROPDOWN_WIDTH = 22
    COMBOBOX_ARROW_SIZE = "4px"
    COMBOBOX_POPUP_BORDER_RADIUS = 4

    TEXT_EDIT_PADDING = "8px"
    TEXT_EDIT_FONT_SIZE = 12

    GROUP_TITLE_LEFT = 4
    GROUP_TITLE_TOP = -2
    GROUP_TITLE_PADDING = "0 6px"
    GROUP_TITLE_BORDER_RADIUS = 4
    GROUP_TITLE_LETTER_SPACING = "0.5px"

    WINDOW_TITLE_FONT_SIZE = 11
    WINDOW_TITLE_LETTER_SPACING = "0.3px"

    TITLE_BAR_BORDER_WIDTH = "1px"
    TITLE_BAR_BORDER_COLOR = ""  # usa BG_PANEL por compatibilidade
    CARD_PADDING_V = 16
    CARD_PADDING_H = 10

    SPLITTER_HANDLE_WIDTH_H = 4
    SPLITTER_HANDLE_WIDTH_V = 4

    MENU_PADDING = "2px"
    MENU_MARGIN_V = "1px 0"
    MENU_ITEM_PADDING = "4px 16px 4px 8px"
    MENU_SEPARATOR_HEIGHT = "1px"
    MENU_SEPARATOR_MARGIN = "2px 6px"

    HEADER_FONT_SIZE = 11
    HEADER_LETTER_SPACING = "0.3px"
    TABLE_ITEM_PADDING = "3px 6px"
    HEADER_PADDING = "4px 6px"

    # ═══════════════════════════════════════════════════════════════════
    # ALIASES DE COMPATIBILIDADE RETROATIVA
    # Mapeiam nomes antigos → tokens semânticos
    # ═══════════════════════════════════════════════════════════════════

    # ── Fundos (BG_*) → SURFACE ─────────────────────────────────────
    BG_DEEPEST = SURFACE_0
    BG_DARK = SURFACE_1
    BG_PANEL = SURFACE_2
    BG_CARD = SURFACE_3
    BG_ELEVATED = SURFACE_4
    BG_SURFACE = SURFACE_5
    TITLE_BAR_BG = TITLE_BAR

    # ── Sombras → SHADOW ────────────────────────────────────────────
    SHADOW = SHADOW_SM
    SHADOW_DEEP = SHADOW_LG

    # ── Bordas → BORDER ─────────────────────────────────────────────
    BORDER = BORDER_DEFAULT
    BORDER_HOVER = BORDER_ACCENT

    # ── Texto (TEXT_*) → TEXT ───────────────────────────────────────
    TEXT_BRIGHT = TEXT_HIGH
    TEXT_PRIMARY = TEXT_MEDIUM
    TEXT_SECONDARY = TEXT_LOW
    TEXT_MUTED = TEXT_DISABLED
    TEXT_ACCENT = ACCENT_TEXT
    TEXT_ACCENT_BRIGHT = ACCENT_BRIGHT

    # ── Acento (ACCENT_COLOR_*) → ACCENT ─────────────────────────────
    ACCENT_COLOR = ACCENT
    ACCENT_COLOR_HOVER = ACCENT_HOVER
    ACCENT_COLOR_ACTIVE = ACCENT_ACTIVE
    ACCENT_COLOR_DIM = ACCENT_DIM
    ACCENT_COLOR_LIGHT = ACCENT_LIGHT
    ACCENT_COLOR_GRADIENT = ACCENT_GRADIENT

    # ── Status → COLOR_ ─────────────────────────────────────────────
    SUCCESS = COLOR_SUCCESS
    SUCCESS_HOVER = COLOR_SUCCESS_HOVER
    SUCCESS_DIM = COLOR_SUCCESS_DIM
    WARNING = COLOR_WARNING
    WARNING_HOVER = COLOR_WARNING_HOVER
    WARNING_DIM = COLOR_WARNING_DIM
    DANGER = COLOR_DANGER
    DANGER_HOVER = COLOR_DANGER_HOVER
    DANGER_DIM = COLOR_DANGER_DIM