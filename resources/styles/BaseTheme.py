# -*- coding: utf-8 -*-
"""
BaseTheme — Classe base abstrata para temas do Aetheris ToolBox
================================================================
Define TODAS as variáveis de tema: cores, fontes, dimensões, espaçamentos.

Subclasses (ex: DarkCharcoalTheme, WhiteTheme) devem sobrescrever
cada atributo com valores concretos.
"""

from __future__ import annotations


class BaseTheme:
    """Classe base para temas. Todos os atributos devem ser sobrescritos."""

    # ═══════════════════════════════════════════════════════════════════
    # CORES — Fundos (profundidade: 0 = mais fundo, 5 = mais alto)
    # ═══════════════════════════════════════════════════════════════════

    BG_DEEPEST: str = ""
    BG_DARK: str = ""
    BG_PANEL: str = ""
    BG_CARD: str = ""
    BG_ELEVATED: str = ""
    BG_SURFACE: str = ""
    TITLE_BAR_BG: str = ""

    # ── Sombras ──────────────────────────────────────────────────────
    SHADOW: str = ""
    SHADOW_DEEP: str = ""
    GLOW: str = ""
    GLOW_STRONG: str = ""

    # ── Bordas ───────────────────────────────────────────────────────
    BORDER: str = ""
    BORDER_HOVER: str = ""
    DIVIDER: str = ""

    # ── Texto ────────────────────────────────────────────────────────
    TEXT_BRIGHT: str = ""
    TEXT_PRIMARY: str = ""
    TEXT_SECONDARY: str = ""
    TEXT_MUTED: str = ""
    TEXT_GOLD: str = ""
    TEXT_GOLD_BRIGHT: str = ""

    # ── Acento Ouro ──────────────────────────────────────────────────
    GOLD: str = ""
    GOLD_HOVER: str = ""
    GOLD_ACTIVE: str = ""
    GOLD_DIM: str = ""
    GOLD_LIGHT: str = ""
    GOLD_GRADIENT: tuple[str, str] = ("", "")

    # ── Status ───────────────────────────────────────────────────────
    SUCCESS: str = ""
    SUCCESS_HOVER: str = ""
    SUCCESS_DIM: str = ""
    WARNING: str = ""
    WARNING_HOVER: str = ""
    WARNING_DIM: str = ""
    DANGER: str = ""
    DANGER_HOVER: str = ""
    DANGER_DIM: str = ""

    # ═══════════════════════════════════════════════════════════════════
    # FONTES
    # ═══════════════════════════════════════════════════════════════════

    FONT_FAMILY_DEFAULT: str = ""
    FONT_FAMILY_MONO: str = ""

    FONT_SIZE_TITLE: int = 21       # header_title
    FONT_SIZE_BIG: int = 16         # about_title
    FONT_SIZE_NORMAL: int = 13      # corpo padrão
    FONT_SIZE_SMALL: int = 11       # labels secundários, badges, tabs, headers
    FONT_SIZE_TINY: int = 10        # badges, remove_btn, tool_selector

    FONT_WEIGHT_NORMAL: int = 400
    FONT_WEIGHT_BOLD: int = 600
    FONT_WEIGHT_EXTRABOLD: int = 700
    FONT_WEIGHT_HEAVY: int = 800

    # ═══════════════════════════════════════════════════════════════════
    # DIMENSÕES — Alturas Padrão
    # ═══════════════════════════════════════════════════════════════════

    INPUT_HEIGHT: int = 0
    BUTTON_HEIGHT: int = 0
    BUTTON_HEIGHT_PRIMARY: int = 0
    ITEM_HEIGHT: int = 0
    CHECKBOX_SIZE: int = 0
    RADIO_SIZE: int = 0
    SCROLLBAR_WIDTH: int = 0
    SCROLLBAR_BORDER_RADIUS: int = 0
    SCROLLBAR_MIN_HEIGHT: int = 0
    TAB_HEIGHT: int = 0
    TAB_CLOSE_BUTTON_SIZE: int = 0
    CLOSE_BUTTON_BORDER_RADIUS: int = 0
    SPLITTER_HANDLE_WIDTH: int = 0
    PROGRESS_BAR_HEIGHT: int = 0
    TITLE_BTN_HEIGHT: int = 0
    TITLE_BTN_WIDTH: int = 0
    TITLE_BTN_FONT_SIZE: int = 0
    TITLE_BAR_BORDER_WIDTH: str = ""
    TITLE_BAR_BORDER_COLOR: str = ""

    # ═══════════════════════════════════════════════════════════════════
    # ESPAÇAMENTOS
    # ═══════════════════════════════════════════════════════════════════

    LAYOUT_V_SPACING: int = 0
    LAYOUT_H_SPACING: int = 0
    CONTENT_PADDING_V: int = 0
    CONTENT_PADDING_H: int = 0
    CARD_PADDING_V: int = 0
    CARD_PADDING_H: int = 0
    GROUP_MARGIN_TOP: int = 0

    # ═══════════════════════════════════════════════════════════════════
    # BORDAS / ARREDONDAMENTO
    # ═══════════════════════════════════════════════════════════════════

    BORDER_RADIUS_CARD: int = 0
    BORDER_RADIUS_BUTTON: int = 0
    BORDER_RADIUS_INPUT: int = 0
    BORDER_RADIUS_CHECKBOX: int = 0
    BORDER_RADIUS_RADIO: int = 0
    BORDER_RADIUS_BADGE: int = 0
    BORDER_RADIUS_PROGRESS: int = 0
    BORDER_RADIUS_TABLE: int = 0
    BORDER_RADIUS_TITLE_BTN: int = 0
    BORDER_RADIUS_TOOLBAR_BTN: int = 0
    BORDER_RADIUS_GHOST: int = 0
    BORDER_RADIUS_TOOL_SELECTOR: int = 0
    BORDER_RADIUS_SCROLLBAR: int = 0
    BORDER_RADIUS_SPINBOX_BTN: int = 0
    BORDER_RADIUS_TAB_CLOSE: int = 0
    BORDER_RADIUS_COMBO_POPUP: int = 0
    BORDER_RADIUS_MENU: int = 0
    BORDER_RADIUS_MENU_ITEM: int = 0
    BORDER_RADIUS_GROUP_TITLE: int = 0
    MENUBAR_ITEM_BORDER_RADIUS: str = ""

    # ═══════════════════════════════════════════════════════════════════
    # CHECKBOX
    # ═══════════════════════════════════════════════════════════════════

    CHECKBOX_BORDER_WIDTH: int = 0
    CHECKBOX_SPACING: int = 0

    # ═══════════════════════════════════════════════════════════════════
    # BADGE
    # ═══════════════════════════════════════════════════════════════════

    BADGE_PADDING_V: str = ""
    BADGE_PADDING_H: str = ""
    BADGE_LETTER_SPACING: str = ""

    # ═══════════════════════════════════════════════════════════════════
    # BOTÕES — Padding
    # ═══════════════════════════════════════════════════════════════════

    BUTTON_PADDING_V: str = ""
    BUTTON_PADDING_H: str = ""

    BUTTON_PADDING_V_SMALL: str = ""
    BUTTON_PADDING_H_SMALL: str = ""

    BUTTON_PADDING_V_PRIMARY: str = ""
    BUTTON_PADDING_H_PRIMARY: str = ""

    BUTTON_LETTER_SPACING_NORMAL: str = ""
    BUTTON_LETTER_SPACING_PRIMARY: str = ""

    # ═══════════════════════════════════════════════════════════════════
    # TOOLBAR
    # ═══════════════════════════════════════════════════════════════════

    TOOLBAR_BTN_PADDING_V: str = ""
    TOOLBAR_BTN_PADDING_H: str = ""

    # ═══════════════════════════════════════════════════════════════════
    # TOOL SELECTOR (Side Panel)
    # ═══════════════════════════════════════════════════════════════════

    TOOL_SELECTOR_PADDING_V: str = ""
    TOOL_SELECTOR_PADDING_H: str = ""
    TOOL_SELECTOR_LETTER_SPACING: str = ""

    # ═══════════════════════════════════════════════════════════════════
    # INPUTS — Padding
    # ═══════════════════════════════════════════════════════════════════

    INPUT_PADDING_V: str = ""
    INPUT_PADDING_H: str = ""

    # ═══════════════════════════════════════════════════════════════════
    # SPINBOX
    # ═══════════════════════════════════════════════════════════════════

    SPINBOX_PADDING: str = ""
    SPINBOX_BTN_WIDTH: int = 0
    SPINBOX_BTN_MARGIN: str = ""

    # ═══════════════════════════════════════════════════════════════════
    # COMBOBOX
    # ═══════════════════════════════════════════════════════════════════

    COMBOBOX_PADDING: str = ""
    COMBOBOX_MIN_WIDTH: int = 0
    COMBOBOX_DROPDOWN_WIDTH: int = 0
    COMBOBOX_ARROW_SIZE: str = ""
    COMBOBOX_POPUP_BORDER_RADIUS: int = 0

    # ═══════════════════════════════════════════════════════════════════
    # TEXT BROWSER / TEXT EDIT
    # ═══════════════════════════════════════════════════════════════════

    TEXT_EDIT_PADDING: str = ""
    TEXT_EDIT_FONT_SIZE: int = 0

    # ═══════════════════════════════════════════════════════════════════
    # GROUP TITLE
    # ═══════════════════════════════════════════════════════════════════

    GROUP_TITLE_LEFT: int = 0
    GROUP_TITLE_TOP: int = 0
    GROUP_TITLE_PADDING: str = ""
    GROUP_TITLE_BORDER_RADIUS: int = 0
    GROUP_TITLE_LETTER_SPACING: str = ""

    # ═══════════════════════════════════════════════════════════════════
    # WINDOW TITLE
    # ═══════════════════════════════════════════════════════════════════

    WINDOW_TITLE_FONT_SIZE: int = 0
    WINDOW_TITLE_LETTER_SPACING: str = ""

    # ═══════════════════════════════════════════════════════════════════
    # QSPLITTER
    # ═══════════════════════════════════════════════════════════════════

    SPLITTER_HANDLE_WIDTH_H: int = 0
    SPLITTER_HANDLE_WIDTH_V: int = 0

    # ═══════════════════════════════════════════════════════════════════
    # QMENU
    # ═══════════════════════════════════════════════════════════════════

    MENU_PADDING: str = ""
    MENU_MARGIN_V: str = ""
    MENU_ITEM_PADDING: str = ""
    MENU_SEPARATOR_HEIGHT: str = ""
    MENU_SEPARATOR_MARGIN: str = ""

    # ═══════════════════════════════════════════════════════════════════
    # HEADER / TABLE HEADER
    # ═══════════════════════════════════════════════════════════════════

    HEADER_FONT_SIZE: int = 0
    HEADER_LETTER_SPACING: str = ""

    # ═══════════════════════════════════════════════════════════════════
    # TABELA — Padding
    # ═══════════════════════════════════════════════════════════════════

    TABLE_ITEM_PADDING: str = ""
    HEADER_PADDING: str = ""