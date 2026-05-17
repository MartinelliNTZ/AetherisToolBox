# -*- coding: utf-8 -*-
"""
DarkCharcoalTheme — Tema concreto Dark Charcoal + Gold
=======================================================
Subclasse de BaseTheme com valores para o tema escuro atual.
"""

from __future__ import annotations

from resources.styles.BaseTheme import BaseTheme


class DarkCharcoalTheme(BaseTheme):
    """
    Tema Dark Charcoal + Gold — design minimalista com profundidade via sombras.
    """

    # ═══════════════════════════════════════════════════════════════════
    # CORES — Fundos (profundidade: 0 = mais fundo, 5 = mais alto)
    # ═══════════════════════════════════════════════════════════════════

    BG_DEEPEST = "#08080A"
    BG_DARK = "#0C0C0F"
    BG_PANEL = "#121216"
    BG_CARD = "#18181D"
    BG_ELEVATED = "#1E1E24"
    BG_SURFACE = "#24242B"
    TITLE_BAR_BG = "#0A0A0D"

    # ── Sombras ──────────────────────────────────────────────────────
    SHADOW = "#040405"
    SHADOW_DEEP = "#000000"
    GLOW = "#C9A84C15"
    GLOW_STRONG = "#C9A84C25"

    # ── Bordas ───────────────────────────────────────────────────────
    BORDER = "#2A2A30"
    BORDER_HOVER = "#C9A84C"
    DIVIDER = "#1A1A20"

    # ── Texto ────────────────────────────────────────────────────────
    TEXT_BRIGHT = "#F0F0F0"
    TEXT_PRIMARY = "#DCDCDC"
    TEXT_SECONDARY = "#888890"
    TEXT_MUTED = "#585860"
    TEXT_GOLD = "#C9A84C"
    TEXT_GOLD_BRIGHT = "#E0C878"

    # ── Acento Ouro ──────────────────────────────────────────────────
    GOLD = "#C9A84C"
    GOLD_HOVER = "#D4B85A"
    GOLD_ACTIVE = "#B8983E"
    GOLD_DIM = "#8A7A3A"
    GOLD_LIGHT = "#E8D08A"
    GOLD_GRADIENT = ("#C9A84C", "#B8963A")

    # ── Status ───────────────────────────────────────────────────────
    SUCCESS = "#43A047"
    SUCCESS_HOVER = "#66BB6A"
    SUCCESS_DIM = "#2E7D32"
    WARNING = "#EF9A00"
    WARNING_HOVER = "#FFB74D"
    WARNING_DIM = "#BF6E00"
    DANGER = "#D32F2F"
    DANGER_HOVER = "#E53935"
    DANGER_DIM = "#A02020"

    # ═══════════════════════════════════════════════════════════════════
    # FONTES
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
    # DIMENSÕES — Alturas Padrão
    # ═══════════════════════════════════════════════════════════════════

    INPUT_HEIGHT = 0
    BUTTON_HEIGHT = 0
    BUTTON_HEIGHT_PRIMARY = 0
    ITEM_HEIGHT = 0
    CHECKBOX_SIZE = 16
    RADIO_SIZE = 16
    SCROLLBAR_WIDTH = 6
    SCROLLBAR_BORDER_RADIUS = 3
    SCROLLBAR_MIN_HEIGHT = 28
    TAB_HEIGHT = 0
    TAB_CLOSE_BUTTON_SIZE = 16
    CLOSE_BUTTON_BORDER_RADIUS = 3
    SPLITTER_HANDLE_WIDTH = 4
    PROGRESS_BAR_HEIGHT = 18
    TITLE_BTN_HEIGHT = 22
    TITLE_BTN_WIDTH = 28
    TITLE_BTN_FONT_SIZE = 11
    TITLE_BAR_BORDER_WIDTH = "1px"
    TITLE_BAR_BORDER_COLOR = ""  # usa BG_PANEL por compatibilidade

    # ═══════════════════════════════════════════════════════════════════
    # ESPAÇAMENTOS
    # ═══════════════════════════════════════════════════════════════════

    LAYOUT_V_SPACING = 8
    LAYOUT_H_SPACING = 8
    CONTENT_PADDING_V = 10
    CONTENT_PADDING_H = 14
    CARD_PADDING_V = 16
    CARD_PADDING_H = 10
    GROUP_MARGIN_TOP = 8

    # ═══════════════════════════════════════════════════════════════════
    # BORDAS / ARREDONDAMENTO
    # ═══════════════════════════════════════════════════════════════════

    BORDER_RADIUS_CARD = 10
    BORDER_RADIUS_BUTTON = 6
    BORDER_RADIUS_INPUT = 6
    BORDER_RADIUS_CHECKBOX = 3
    BORDER_RADIUS_RADIO = 0
    BORDER_RADIUS_BADGE = 4
    BORDER_RADIUS_PROGRESS = 5
    BORDER_RADIUS_TABLE = 8
    BORDER_RADIUS_TITLE_BTN = 3
    BORDER_RADIUS_TOOLBAR_BTN = 4
    BORDER_RADIUS_TOOL_SELECTOR = 6
    BORDER_RADIUS_GHOST = 5
    BORDER_RADIUS_SCROLLBAR = 3
    BORDER_RADIUS_SPINBOX_BTN = 2
    BORDER_RADIUS_TAB_CLOSE = 3
    BORDER_RADIUS_COMBO_POPUP = 4
    BORDER_RADIUS_MENU = 6
    BORDER_RADIUS_MENU_ITEM = 3
    BORDER_RADIUS_GROUP_TITLE = 4
    MENUBAR_ITEM_BORDER_RADIUS = "1px 1px 8px 1px"

    # ═══════════════════════════════════════════════════════════════════
    # CHECKBOX
    # ═══════════════════════════════════════════════════════════════════

    CHECKBOX_BORDER_WIDTH = 0
    CHECKBOX_SPACING = 8

    # ═══════════════════════════════════════════════════════════════════
    # BADGE
    # ═══════════════════════════════════════════════════════════════════

    BADGE_PADDING_V = "3px"
    BADGE_PADDING_H = "12px"
    BADGE_LETTER_SPACING = "0.3px"

    # ═══════════════════════════════════════════════════════════════════
    # BOTÕES — Padding (px strings para QSS)
    # ═══════════════════════════════════════════════════════════════════

    BUTTON_PADDING_V = "6px"
    BUTTON_PADDING_H = "14px"

    BUTTON_PADDING_V_SMALL = "4px"
    BUTTON_PADDING_H_SMALL = "12px"

    BUTTON_PADDING_V_PRIMARY = "6px"
    BUTTON_PADDING_H_PRIMARY = "20px"

    BUTTON_LETTER_SPACING_NORMAL = "0.3px"
    BUTTON_LETTER_SPACING_PRIMARY = "0.5px"

    # ═══════════════════════════════════════════════════════════════════
    # TOOLBAR
    # ═══════════════════════════════════════════════════════════════════

    TOOLBAR_BTN_PADDING_V = "4px"
    TOOLBAR_BTN_PADDING_H = "10px"

    # ═══════════════════════════════════════════════════════════════════
    # TOOL SELECTOR (Side Panel)
    # ═══════════════════════════════════════════════════════════════════

    TOOL_SELECTOR_PADDING_V = "6px"
    TOOL_SELECTOR_PADDING_H = "4px"
    TOOL_SELECTOR_LETTER_SPACING = "0.3px"

    # ═══════════════════════════════════════════════════════════════════
    # INPUTS — Padding
    # ═══════════════════════════════════════════════════════════════════

    INPUT_PADDING_V = "2px"
    INPUT_PADDING_H = "2px"

    # ═══════════════════════════════════════════════════════════════════
    # SPINBOX
    # ═══════════════════════════════════════════════════════════════════

    SPINBOX_PADDING = "3px 8px"
    SPINBOX_BTN_WIDTH = 16
    SPINBOX_BTN_MARGIN = "1px"

    # ═══════════════════════════════════════════════════════════════════
    # COMBOBOX
    # ═══════════════════════════════════════════════════════════════════

    COMBOBOX_PADDING = "3px 8px"
    COMBOBOX_MIN_WIDTH = 80
    COMBOBOX_DROPDOWN_WIDTH = 22
    COMBOBOX_ARROW_SIZE = "4px"
    COMBOBOX_POPUP_BORDER_RADIUS = 4

    # ═══════════════════════════════════════════════════════════════════
    # TEXT BROWSER / TEXT EDIT
    # ═══════════════════════════════════════════════════════════════════

    TEXT_EDIT_PADDING = "8px"
    TEXT_EDIT_FONT_SIZE = 12

    # ═══════════════════════════════════════════════════════════════════
    # GROUP TITLE
    # ═══════════════════════════════════════════════════════════════════

    GROUP_TITLE_LEFT = 4
    GROUP_TITLE_TOP = -2
    GROUP_TITLE_PADDING = "0 6px"
    GROUP_TITLE_BORDER_RADIUS = 4
    GROUP_TITLE_LETTER_SPACING = "0.5px"

    # ═══════════════════════════════════════════════════════════════════
    # WINDOW TITLE
    # ═══════════════════════════════════════════════════════════════════

    WINDOW_TITLE_FONT_SIZE = 11
    WINDOW_TITLE_LETTER_SPACING = "0.3px"

    # ═══════════════════════════════════════════════════════════════════
    # QSPLITTER
    # ═══════════════════════════════════════════════════════════════════

    SPLITTER_HANDLE_WIDTH_H = 4
    SPLITTER_HANDLE_WIDTH_V = 4

    # ═══════════════════════════════════════════════════════════════════
    # QMENU
    # ═══════════════════════════════════════════════════════════════════

    MENU_PADDING = "2px"
    MENU_MARGIN_V = "1px 0"
    MENU_ITEM_PADDING = "4px 16px 4px 8px"
    MENU_SEPARATOR_HEIGHT = "1px"
    MENU_SEPARATOR_MARGIN = "2px 6px"

    # ═══════════════════════════════════════════════════════════════════
    # HEADER / TABLE HEADER
    # ═══════════════════════════════════════════════════════════════════

    HEADER_FONT_SIZE = 11
    HEADER_LETTER_SPACING = "0.3px"

    # ═══════════════════════════════════════════════════════════════════
    # TABELA — Padding
    # ═══════════════════════════════════════════════════════════════════

    TABLE_ITEM_PADDING = "3px 6px"
    HEADER_PADDING = "4px 6px"