# -*- coding: utf-8 -*-
"""
BaseTheme — Classe base abstrata para temas do Aetheris ToolBox
================================================================
Define TODAS as variáveis de tema organizadas em grupos semânticos.

Cada tema concreto (ex: DarkCharcoalTheme, ModernBlueTheme) deve
sobrescrever todos os atributos com valores concretos.

Grupos:
    ACCENT, SURFACE, TEXT, BORDER, SHADOW, RADIUS, SPACE,
    ICON, ANIMATION, OPACITY, LAYOUT, ELEVATION, OVERLAY,
    FOCUS_RING, STATUS, FONT, DIMENSIONS, SPECIFICS
"""

from __future__ import annotations


class BaseTheme:
    """Classe base para temas. Todos os atributos devem ser sobrescritos."""

    # ═══════════════════════════════════════════════════════════════════
    # 1. ACCENT — Acento principal (substitui GOLD semânticamente)
    # ═══════════════════════════════════════════════════════════════════

    ACCENT: str = ""
    ACCENT_HOVER: str = ""
    ACCENT_ACTIVE: str = ""
    ACCENT_DIM: str = ""
    ACCENT_LIGHT: str = ""
    ACCENT_SOFT: str = ""
    ACCENT_TEXT: str = ""
    ACCENT_BRIGHT: str = ""
    ACCENT_GRADIENT: tuple[str, str] = ("", "")

    # ═══════════════════════════════════════════════════════════════════
    # 2. SURFACE — Níveis de profundidade (0 = mais fundo, 5 = mais alto)
    # ═══════════════════════════════════════════════════════════════════

    SURFACE_0: str = ""       # fundo absoluto
    SURFACE_1: str = ""       # fundo padrão
    SURFACE_2: str = ""       # painéis base
    SURFACE_3: str = ""       # cards / groupbox
    SURFACE_4: str = ""       # elementos elevados
    SURFACE_5: str = ""       # superfície (hover, focus)
    TITLE_BAR: str = ""       # barra de título

    # ═══════════════════════════════════════════════════════════════════
    # 3. TEXT — Hierarquia de texto
    # ═══════════════════════════════════════════════════════════════════

    TEXT_HIGH: str = ""
    TEXT_MEDIUM: str = ""
    TEXT_LOW: str = ""
    TEXT_DISABLED: str = ""
    TEXT_ON_ACCENT: str = ""

    # ═══════════════════════════════════════════════════════════════════
    # 4. BORDER — Hierarquia de bordas
    # ═══════════════════════════════════════════════════════════════════

    BORDER_SUBTLE: str = ""
    BORDER_DEFAULT: str = ""
    BORDER_STRONG: str = ""
    BORDER_ACCENT: str = ""
    DIVIDER: str = ""

    # ═══════════════════════════════════════════════════════════════════
    # 5. SHADOW — Sombras por tamanho
    # ═══════════════════════════════════════════════════════════════════

    SHADOW_SM: str = ""
    SHADOW_MD: str = ""
    SHADOW_LG: str = ""
    SHADOW_XL: str = ""
    SHADOW_ACCENT: str = ""
    GLOW: str = ""
    GLOW_STRONG: str = ""

    # ═══════════════════════════════════════════════════════════════════
    # 6. RADIUS — Escala global de arredondamento
    # ═══════════════════════════════════════════════════════════════════

    RADIUS_XS: int = 0
    RADIUS_SM: int = 0
    RADIUS_MD: int = 0
    RADIUS_LG: int = 0
    RADIUS_XL: int = 0
    RADIUS_FULL: int = 999

    # ═══════════════════════════════════════════════════════════════════
    # 7. SPACE — Escala global de espaçamento (pixels inteiros)
    # ═══════════════════════════════════════════════════════════════════

    SPACE_XXS: int = 0
    SPACE_XS: int = 0
    SPACE_SM: int = 0
    SPACE_MD: int = 0
    SPACE_LG: int = 0
    SPACE_XL: int = 0
    SPACE_2XL: int = 0
    SPACE_3XL: int = 0

    # ═══════════════════════════════════════════════════════════════════
    # 8. ICON — Tamanhos de ícone
    # ═══════════════════════════════════════════════════════════════════

    ICON_XS: int = 0
    ICON_SM: int = 0
    ICON_MD: int = 0
    ICON_LG: int = 0
    ICON_XL: int = 0

    # ═══════════════════════════════════════════════════════════════════
    # 9. ANIMATION — Tempo de animação (ms)
    # ═══════════════════════════════════════════════════════════════════

    ANIMATION_FAST: int = 0
    ANIMATION_NORMAL: int = 0
    ANIMATION_SLOW: int = 0
    EASING_STANDARD: str = ""

    # ═══════════════════════════════════════════════════════════════════
    # 10. OPACITY — Níveis de opacidade
    # ═══════════════════════════════════════════════════════════════════

    OPACITY_DISABLED: float = 0.0
    OPACITY_MUTED: float = 0.0
    OPACITY_HOVER: float = 0.0
    OPACITY_ACTIVE: float = 0.0

    # ═══════════════════════════════════════════════════════════════════
    # 11. LAYOUT — Layout global
    # ═══════════════════════════════════════════════════════════════════

    PAGE_PADDING: int = 0
    SECTION_GAP: int = 0
    GRID_GAP: int = 0
    CONTENT_MAX_WIDTH: int = 0

    # ═══════════════════════════════════════════════════════════════════
    # 12. ELEVATION — Níveis de elevação (z-index conceitual)
    # ═══════════════════════════════════════════════════════════════════

    ELEVATION_FLAT: int = 0
    ELEVATION_LOW: int = 0
    ELEVATION_MEDIUM: int = 0
    ELEVATION_HIGH: int = 0

    # ═══════════════════════════════════════════════════════════════════
    # 13. OVERLAY — Sobreposições / Glass
    # ═══════════════════════════════════════════════════════════════════

    OVERLAY_BG: str = ""
    BACKDROP_BLUR: str = ""

    # ═══════════════════════════════════════════════════════════════════
    # 14. FOCUS_RING — Anel de foco
    # ═══════════════════════════════════════════════════════════════════

    FOCUS_RING_COLOR: str = ""
    FOCUS_RING_WIDTH: str = ""
    FOCUS_RING_OFFSET: str = ""

    # ═══════════════════════════════════════════════════════════════════
    # 15. STATUS — Cores de estado (INFO adicionado)
    # ═══════════════════════════════════════════════════════════════════

    COLOR_SUCCESS: str = ""
    COLOR_SUCCESS_HOVER: str = ""
    COLOR_SUCCESS_DIM: str = ""
    COLOR_WARNING: str = ""
    COLOR_WARNING_HOVER: str = ""
    COLOR_WARNING_DIM: str = ""
    COLOR_DANGER: str = ""
    COLOR_DANGER_HOVER: str = ""
    COLOR_DANGER_DIM: str = ""
    COLOR_INFO: str = ""
    COLOR_INFO_HOVER: str = ""
    COLOR_INFO_DIM: str = ""

    # ═══════════════════════════════════════════════════════════════════
    # 16. FONT — Tipografia
    # ═══════════════════════════════════════════════════════════════════

    FONT_FAMILY_DEFAULT: str = ""
    FONT_FAMILY_MONO: str = ""

    FONT_SIZE_TITLE: int = 0
    FONT_SIZE_BIG: int = 0
    FONT_SIZE_NORMAL: int = 0
    FONT_SIZE_SMALL: int = 0
    FONT_SIZE_TINY: int = 0

    FONT_WEIGHT_NORMAL: int = 400
    FONT_WEIGHT_BOLD: int = 600
    FONT_WEIGHT_EXTRABOLD: int = 700
    FONT_WEIGHT_HEAVY: int = 800

    # ═══════════════════════════════════════════════════════════════════
    # 17. DIMENSIONS — Alturas e tamanhos de widgets
    # ═══════════════════════════════════════════════════════════════════

    INPUT_HEIGHT: int = 0
    BUTTON_HEIGHT: int = 0
    BUTTON_HEIGHT_PRIMARY: int = 0
    ITEM_HEIGHT: int = 0
    CHECKBOX_SIZE: int = 0
    RADIO_SIZE: int = 0
    SCROLLBAR_WIDTH: int = 0
    SCROLLBAR_MIN_HEIGHT: int = 0
    TAB_HEIGHT: int = 0
    TAB_CLOSE_BUTTON_SIZE: int = 0
    CLOSE_BUTTON_BORDER_RADIUS: int = 0
    PROGRESS_BAR_HEIGHT: int = 0
    TITLE_BTN_HEIGHT: int = 0
    TITLE_BTN_WIDTH: int = 0
    TITLE_BTN_FONT_SIZE: int = 0
    GROUP_MARGIN_TOP: int = 0
    SPLITTER_HANDLE_WIDTH: int = 0

    # ═══════════════════════════════════════════════════════════════════
    # 18. SPECIFICS — Tokens específicos de implementação (não semânticos)
    #     Mantidos para compatibilidade retroativa
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

    CHECKBOX_BORDER_WIDTH: int = 0
    CHECKBOX_SPACING: int = 0

    BADGE_PADDING_V: str = ""
    BADGE_PADDING_H: str = ""
    BADGE_LETTER_SPACING: str = ""

    BUTTON_PADDING_V: str = ""
    BUTTON_PADDING_H: str = ""
    BUTTON_PADDING_V_SMALL: str = ""
    BUTTON_PADDING_H_SMALL: str = ""
    BUTTON_PADDING_V_PRIMARY: str = ""
    BUTTON_PADDING_H_PRIMARY: str = ""
    BUTTON_LETTER_SPACING_NORMAL: str = ""
    BUTTON_LETTER_SPACING_PRIMARY: str = ""

    TOOLBAR_BTN_PADDING_V: str = ""
    TOOLBAR_BTN_PADDING_H: str = ""

    TOOL_SELECTOR_PADDING_V: str = ""
    TOOL_SELECTOR_PADDING_H: str = ""
    TOOL_SELECTOR_LETTER_SPACING: str = ""

    INPUT_PADDING_V: str = ""
    INPUT_PADDING_H: str = ""

    SPINBOX_PADDING: str = ""
    SPINBOX_BTN_WIDTH: int = 0
    SPINBOX_BTN_MARGIN: str = ""

    COMBOBOX_PADDING: str = ""
    COMBOBOX_MIN_WIDTH: int = 0
    COMBOBOX_DROPDOWN_WIDTH: int = 0
    COMBOBOX_ARROW_SIZE: str = ""
    COMBOBOX_POPUP_BORDER_RADIUS: int = 0

    TEXT_EDIT_PADDING: str = ""
    TEXT_EDIT_FONT_SIZE: int = 0

    GROUP_TITLE_LEFT: int = 0
    GROUP_TITLE_TOP: int = 0
    GROUP_TITLE_PADDING: str = ""
    GROUP_TITLE_BORDER_RADIUS: int = 0
    GROUP_TITLE_LETTER_SPACING: str = ""

    WINDOW_TITLE_FONT_SIZE: int = 0
    WINDOW_TITLE_LETTER_SPACING: str = ""

    TITLE_BAR_BORDER_WIDTH: str = ""
    TITLE_BAR_BORDER_COLOR: str = ""
    CARD_PADDING_V: int = 0
    CARD_PADDING_H: int = 0

    SPLITTER_HANDLE_WIDTH_H: int = 0
    SPLITTER_HANDLE_WIDTH_V: int = 0

    MENU_PADDING: str = ""
    MENU_MARGIN_V: str = ""
    MENU_ITEM_PADDING: str = ""
    MENU_SEPARATOR_HEIGHT: str = ""
    MENU_SEPARATOR_MARGIN: str = ""

    HEADER_FONT_SIZE: int = 0
    HEADER_LETTER_SPACING: str = ""
    TABLE_ITEM_PADDING: str = ""
    HEADER_PADDING: str = ""

    # ═══════════════════════════════════════════════════════════════════
    # ALIASES DE COMPATIBILIDADE RETROATIVA
    # Mapeiam nomes antigos → semânticos. Permitem que código legado
    # continue funcionando sem alterações.
    # ═══════════════════════════════════════════════════════════════════

    # ── Fundos (antigos BG_*) → SURFACE ─────────────────────────────
    BG_DEEPEST: str = ""
    BG_DARK: str = ""
    BG_PANEL: str = ""
    BG_CARD: str = ""
    BG_ELEVATED: str = ""
    BG_SURFACE: str = ""
    TITLE_BAR_BG: str = ""

    # ── Sombras (antigas) → SHADOW ──────────────────────────────────
    SHADOW: str = ""
    SHADOW_DEEP: str = ""

    # ── Bordas (antigas) → BORDER ──────────────────────────────────
    BORDER: str = ""
    BORDER_HOVER: str = ""

    # ── Texto (antigo TEXT_*) → TEXT ────────────────────────────────
    TEXT_BRIGHT: str = ""
    TEXT_PRIMARY: str = ""
    TEXT_SECONDARY: str = ""
    TEXT_MUTED: str = ""
    TEXT_GOLD: str = ""
    TEXT_GOLD_BRIGHT: str = ""

    # ── Acento (antigo GOLD*) → ACCENT ──────────────────────────────
    GOLD: str = ""
    GOLD_HOVER: str = ""
    GOLD_ACTIVE: str = ""
    GOLD_DIM: str = ""
    GOLD_LIGHT: str = ""
    GOLD_GRADIENT: tuple[str, str] = ("", "")

    # ── Status (antigo SUCCESS/WARNING/DANGER*) → COLOR_ ────────────
    SUCCESS: str = ""
    SUCCESS_HOVER: str = ""
    SUCCESS_DIM: str = ""
    WARNING: str = ""
    WARNING_HOVER: str = ""
    WARNING_DIM: str = ""
    DANGER: str = ""
    DANGER_HOVER: str = ""
    DANGER_DIM: str = ""