# -*- coding: utf-8 -*-
"""
BaseTheme — Classe base abstrata para temas do Aetheris ToolBox
================================================================
Define TODAS as variáveis de tema organizadas em grupos semânticos.

Cada tema concreto (ex: DarkCharcoalTheme, ModernBlueTheme) deve
sobrescrever todos os atributos com valores concretos.

Grupos de tokens semânticos (organizados por categoria):
    1.  ACCENT       — Cores de destaque principal
    2.  SURFACE      — Níveis de profundidade (0=fundo … 5=topo)
    3.  TEXT         — Hierarquia tipográfica
    4.  BORDER       — Hierarquia de bordas
    5.  SHADOW       — Sombras por tamanho
    6.  RADIUS       — Escala global de cantos arredondados
    7.  SPACE        — Escala global de espaçamento (px)
    8.  ICON         — Tamanhos de ícone (px)
    9.  ANIMATION    — Durações de animação (ms) + easing
    10. OPACITY      — Níveis de opacidade (0.0–1.0)
    11. LAYOUT       — Layout global (padding, gap, max-width)
    12. ELEVATION    — Níveis de elevação (z-index conceitual)
    13. OVERLAY      — Sobreposições / glass effect
    14. FOCUS_RING   — Anel de foco visual
    15. STATUS       — Cores de estado (success, warning, danger, info)
    16. FONT         — Tipografia (famílias, tamanhos, pesos)
    17. DIMENSIONS   — Alturas e tamanhos de widgets
    18. SPECIFICS    — Tokens específicos de implementação (compatibilidade)

    Aliases de compatibilidade retroativa (mapeiam nomes antigos → semânticos)
"""

from __future__ import annotations

from typing import Any


class BaseTheme:
    """Classe base abstrata para temas. Todos os atributos devem ser sobrescritos
    pelos temas concretos.

    Attributes:
        ── ACCENT ───────────────────────────────────────────
        ACCENT: Cor principal de destaque (botões, links, seleção).
        ACCENT_HOVER: Hover / foco do accent.
        ACCENT_ACTIVE: Estado pressed / ativo.
        ACCENT_DIM: Versão escurecida / muted do accent.
        ACCENT_LIGHT: Versão clara (badges, highlights sutis).
        ACCENT_SOFT: Versão translucent rgba para backgrounds.
        ACCENT_TEXT: Cor para texto sobre superfície escura com accent.
        ACCENT_BRIGHT: Versão brilhante (glow, hover highlight).
        ACCENT_GRADIENT: Par (start, stop) para gradientes lineares.

        ── SURFACE ─────────────────────────────────────────
        SURFACE_0: Fundo absoluto (backdrop), profundidade 0.
        SURFACE_1: Fundo padrão da janela, profundidade 1.
        SURFACE_2: Painéis base / side panels, profundidade 2.
        SURFACE_3: Cards / groupbox / áreas elevadas, profundidade 3.
        SURFACE_4: Inputs, tabelas, elementos interativos, profundidade 4.
        SURFACE_5: Superfície hover / focus, profundidade 5.
        TITLE_BAR: Cor de fundo da barra de título da janela.

        ── TEXT ────────────────────────────────────────────
        TEXT_HIGH: Títulos, labels de alta importância.
        TEXT_MEDIUM: Corpo padrão, texto principal.
        TEXT_LOW: Secundário, metadados, texto auxiliar.
        TEXT_DISABLED: Widget desabilitado, baixo contraste.
        TEXT_ON_ACCENT: Texto sobre fundo ACCENT.
        TEXT_ON_DANGER: Texto sobre fundo danger (close btn, btn_danger).

        ── BORDER ──────────────────────────────────────────
        BORDER_SUBTLE: Linhas muito sutis (divisores leves).
        BORDER_DEFAULT: Borda padrão de widgets.
        BORDER_STRONG: Borda de destaque (foco, validação).
        BORDER_ACCENT: Borda com cor de acento.
        DIVIDER: Separadores (linhas horizontais/verticais).
        BORDER_GRADIENT_STOPS: Stops para borda gradiente ("efeito foil").
        BORDER_GRADIENT_WIDTH: Largura da borda gradiente.

        ── SHADOW ──────────────────────────────────────────
        SHADOW_SM: Sombra pequena (string com tom/alpha).
        SHADOW_MD: Sombra média (string com tom/alpha).
        SHADOW_LG: Sombra grande (string com tom/alpha).
        SHADOW_XL: Sombra extra grande (string com tom/alpha).
        SHADOW_ACCENT: Sombra com cor de acento (glow em string).
        GLOW: Brilho sutil (string cor+alpha).
        GLOW_STRONG: Brilho forte (string cor+alpha).
        SHADOW_BLUR_SM/MD/LG/XL: Blur radius numérico para drop shadow.
        SHADOW_OFFSET_Y_SM/MD/LG: Offset vertical da sombra (px).
        SHADOW_COLOR_RGB: Cor base da sombra sem alfa (#RRGGBB).
        SHADOW_COLOR_ALPHA: Alfa da sombra (0-255, 0=invisível).
        GLOW_BLUR: Blur radius do glow (px).
        GLOW_OFFSET_X/Y: Offset do glow (px).
        GLOW_COLOR_RGB: Cor do glow (#RRGGBB). Vazio = usa ACCENT.
        GLOW_ALPHA: Alfa do glow (0-255, 0=invisível).
        GLOW_STRONG_BLUR/ALPHA: Blur e alfa do glow forte.

        ── RADIUS ──────────────────────────────────────────
        RADIUS_XS: 2px (checkbox, scrollbar, spin btn).
        RADIUS_SM: 4px (badge, toolbar btn).
        RADIUS_MD: 6px (button, input, menu).
        RADIUS_LG: 10px (card, table, progress).
        RADIUS_XL: 16px (diálogos, painéis).
        RADIUS_FULL: 999px (círculo/pill).

        ── SPACE ───────────────────────────────────────────
        SPACE_XXS: 2px (micro espaçamento).
        SPACE_XS: 4px (muito pequeno).
        SPACE_SM: 8px (pequeno).
        SPACE_MD: 12px (médio).
        SPACE_LG: 16px (grande).
        SPACE_XL: 24px (extra grande).
        SPACE_2XL: 32px (seção).
        SPACE_3XL: 48px (seção grande).

        ── ICON ────────────────────────────────────────────
        ICON_XS: 12px (tiny indicator).
        ICON_SM: 16px (menu item).
        ICON_MD: 20px (botão padrão).
        ICON_LG: 24px (seção, header).
        ICON_XL: 32px (featured, empty state).
        TOOLBAR_ICON_SIZE: Tamanho do ícone na toolbar (px).

        ── ANIMATION ───────────────────────────────────────
        ANIMATION_FAST: 120ms (hover, micro-interações).
        ANIMATION_NORMAL: 180ms (transições padrão).
        ANIMATION_SLOW: 260ms (expansão, colapso).
        EASING_STANDARD: Curva de easing (ex: cubic-bezier).

        ── OPACITY ─────────────────────────────────────────
        OPACITY_DISABLED: Opacidade de widget desabilitado.
        OPACITY_MUTED: Opacidade de texto/elemento secundário.
        OPACITY_HOVER: Opacidade de feedback hover.
        OPACITY_ACTIVE: Opacidade de estado ativo/pressed.

        ── LAYOUT ──────────────────────────────────────────
        PAGE_PADDING: Padding externo da página (px).
        SECTION_GAP: Espaçamento entre seções (px).
        GRID_GAP: Gap em layouts grid (px).
        CONTENT_MAX_WIDTH: Largura máxima do conteúdo (px).

        ── ELEVATION ───────────────────────────────────────
        ELEVATION_FLAT: Z-index flat (0).
        ELEVATION_LOW: Z-index baixo (1).
        ELEVATION_MEDIUM: Z-index médio (2).
        ELEVATION_HIGH: Z-index alto (3).

        ── OVERLAY ─────────────────────────────────────────
        OVERLAY_BG: Cor de fundo de modais/dialogs (rgba).
        BACKDROP_BLUR: Valor de desfoque do backdrop (ex: '4px').

        ── FOCUS_RING ──────────────────────────────────────
        FOCUS_RING_COLOR: Cor do anel de foco.
        FOCUS_RING_WIDTH: Espessura do anel (ex: '2px').
        FOCUS_RING_OFFSET: Distância do elemento (ex: '1px').

        ── STATUS ──────────────────────────────────────────
        COLOR_SUCCESS: Verde - operação bem-sucedida.
        COLOR_SUCCESS_HOVER: Hover do success.
        COLOR_SUCCESS_DIM: Versão escurecida do success.
        COLOR_WARNING: Amarelo/laranja - atenção.
        COLOR_WARNING_HOVER: Hover do warning.
        COLOR_WARNING_DIM: Versão escurecida do warning.
        COLOR_DANGER: Vermelho - erro/perigo.
        COLOR_DANGER_HOVER: Hover do danger.
        COLOR_DANGER_DIM: Versão escurecida do danger.
        COLOR_INFO: Azul - informação.
        COLOR_INFO_HOVER: Hover do info.
        COLOR_INFO_DIM: Versão escurecida do info.

        ── FONT ────────────────────────────────────────────
        FONT_FAMILY_DEFAULT: Família de fonte padrão.
        FONT_FAMILY_MONO: Família de fonte monoespaçada.
        FONT_FAMILY_DISPLAY: Fonte display/serif (vazio=usa DEFAULT).
        FONT_LETTER_SPACING_DISPLAY: Letter-spacing numérico para display.
        FONT_SIZE_TITLE: Tamanho da fonte de título (px).
        FONT_SIZE_BIG: Tamanho da fonte grande (px).
        FONT_SIZE_NORMAL: Tamanho da fonte normal (px).
        FONT_SIZE_SMALL: Tamanho da fonte pequena (px).
        FONT_SIZE_TINY: Tamanho da fonte muito pequena (px).
        FONT_WEIGHT_NORMAL: Peso normal (400).
        FONT_WEIGHT_BOLD: Peso bold (600).
        FONT_WEIGHT_EXTRABOLD: Peso extra bold (700).
        FONT_WEIGHT_HEAVY: Peso heavy (800).

        ── DIMENSIONS ──────────────────────────────────────
        INPUT_HEIGHT: Altura de inputs (px).
        BUTTON_HEIGHT: Altura de botões standard (px).
        BUTTON_HEIGHT_PRIMARY: Altura de botões primários (px).
        ITEM_HEIGHT: Altura de itens de lista (px).
        CHECKBOX_SIZE: Largura/altura do checkbox (px).
        RADIO_SIZE: Largura/altura do radio button (px).
        SCROLLBAR_WIDTH: Largura da scrollbar vertical (px).
        SCROLLBAR_MIN_HEIGHT: Altura mínima do handle da scrollbar (px).
        TAB_HEIGHT: Altura de tabs (px).
        TAB_CLOSE_BUTTON_SIZE: Tamanho do botão fechar tab (px).
        CLOSE_BUTTON_BORDER_RADIUS: Border-radius do botão fechar (px).
        PROGRESS_BAR_HEIGHT: Altura da progress bar (px).
        TITLE_BTN_HEIGHT: Altura dos botões da title bar (px).
        TITLE_BTN_WIDTH: Largura dos botões da title bar (px).
        TITLE_BTN_FONT_SIZE: Tamanho da fonte dos botões da title bar (px).
        TOOLBAR_BTN_SIZE: Tamanho do botão da toolbar (px).
        TOOLBAR_BTN_HOVER_GROW: Pixels extras no hover (animação grow).
        GROUP_MARGIN_TOP: Margem superior do groupbox (px).
        SPLITTER_HANDLE_WIDTH: Largura do handle do splitter (px).

        ── SPECIFICS (border radius) ───────────────────────
        BORDER_RADIUS_CARD: Border-radius de cards.
        BORDER_RADIUS_BUTTON: Border-radius de botões.
        BORDER_RADIUS_INPUT: Border-radius de inputs.
        BORDER_RADIUS_CHECKBOX: Border-radius de checkbox.
        BORDER_RADIUS_RADIO: Border-radius de radio button.
        BORDER_RADIUS_BADGE: Border-radius de badges.
        BORDER_RADIUS_PROGRESS: Border-radius de progress bar.
        BORDER_RADIUS_TABLE: Border-radius de tabelas.
        BORDER_RADIUS_TITLE_BTN: Border-radius dos botões title bar.
        BORDER_RADIUS_TOOLBAR_BTN: Border-radius dos botões toolbar.
        BORDER_RADIUS_GHOST: Border-radius do botão ghost.
        BORDER_RADIUS_TOOL_SELECTOR: Border-radius do seletor de tool.
        BORDER_RADIUS_SCROLLBAR: Border-radius da scrollbar.
        BORDER_RADIUS_SPINBOX_BTN: Border-radius dos botões spinbox.
        BORDER_RADIUS_TAB_CLOSE: Border-radius do botão fechar tab.
        BORDER_RADIUS_COMBO_POPUP: Border-radius do popup combobox.
        BORDER_RADIUS_MENU: Border-radius do menu dropdown.
        BORDER_RADIUS_MENU_ITEM: Border-radius dos itens de menu.
        BORDER_RADIUS_GROUP_TITLE: Border-radius do título groupbox.
        BORDER_RADIUS_DIALOG: Border-radius de diálogos.
        MENUBAR_ITEM_BORDER_RADIUS: Border-radius dos itens da menubar.

        ── SPECIFICS (checkbox) ────────────────────────────
        CHECKBOX_BORDER_WIDTH: Largura da borda do checkbox (px).
        CHECKBOX_SPACING: Espaçamento entre checkbox e label (px).

        ── SPECIFICS (badge) ───────────────────────────────
        BADGE_PADDING_V: Padding vertical do badge.
        BADGE_PADDING_H: Padding horizontal do badge.
        BADGE_LETTER_SPACING: Letter-spacing do badge.
        BADGE_OUTLINE_ENABLED: Se True, usa badge outline.
        BADGE_OUTLINE_BORDER_WIDTH: Largura da borda do badge outline.
        BADGE_OUTLINE_BG_ALPHA: Alfa do fundo translúcido do badge outline.

        ── SPECIFICS (button) ──────────────────────────────
        BUTTON_PADDING_V: Padding vertical de botão padrão.
        BUTTON_PADDING_H: Padding horizontal de botão padrão.
        BUTTON_PADDING_V_SMALL: Padding vertical de botão pequeno.
        BUTTON_PADDING_H_SMALL: Padding horizontal de botão pequeno.
        BUTTON_PADDING_V_PRIMARY: Padding vertical de botão primário.
        BUTTON_PADDING_H_PRIMARY: Padding horizontal de botão primário.
        BUTTON_LETTER_SPACING_NORMAL: Letter-spacing de botão normal.
        BUTTON_LETTER_SPACING_PRIMARY: Letter-spacing de botão primário.

        ── SPECIFICS (toolbar) ─────────────────────────────
        TOOLBAR_BTN_PADDING_V: Padding vertical do botão toolbar.
        TOOLBAR_BTN_PADDING_H: Padding horizontal do botão toolbar.

        ── SPECIFICS (tool selector) ───────────────────────
        TOOL_SELECTOR_PADDING_V: Padding vertical do seletor de tool.
        TOOL_SELECTOR_PADDING_H: Padding horizontal do seletor de tool.
        TOOL_SELECTOR_LETTER_SPACING: Letter-spacing do seletor de tool.

        ── SPECIFICS (input) ───────────────────────────────
        INPUT_PADDING_V: Padding vertical de input.
        INPUT_PADDING_H: Padding horizontal de input.

        ── SPECIFICS (spinbox) ─────────────────────────────
        SPINBOX_PADDING: Padding do spinbox.
        SPINBOX_BTN_WIDTH: Largura dos botões do spinbox (px).
        SPINBOX_BTN_MARGIN: Margem dos botões do spinbox.

        ── SPECIFICS (combobox) ────────────────────────────
        COMBOBOX_PADDING: Padding do combobox.
        COMBOBOX_MIN_WIDTH: Largura mínima do combobox (px).
        COMBOBOX_DROPDOWN_WIDTH: Largura do dropdown button (px).
        COMBOBOX_ARROW_SIZE: Tamanho da seta do combobox.
        COMBOBOX_POPUP_BORDER_RADIUS: Border-radius do popup combobox.

        ── SPECIFICS (text edit) ───────────────────────────
        TEXT_EDIT_PADDING: Padding do text edit.
        TEXT_EDIT_FONT_SIZE: Tamanho da fonte do text edit (px).

        ── SPECIFICS (groupbox) ────────────────────────────
        GROUP_TITLE_LEFT: Offset horizontal do título (px).
        GROUP_TITLE_TOP: Offset vertical do título (px).
        GROUP_TITLE_PADDING: Padding do título.
        GROUP_TITLE_BORDER_RADIUS: Border-radius do título (px).
        GROUP_TITLE_LETTER_SPACING: Letter-spacing do título.

        ── SPECIFICS (letter spacing) ──────────────────────
        LETTER_SPACING_TITLE: Letter-spacing de títulos grandes.
        LETTER_SPACING_BADGE: Letter-spacing de badges.
        LETTER_SPACING_GROUP: Letter-spacing de título groupbox.
        LETTER_SPACING_BUTTON: Letter-spacing de botão normal.
        LETTER_SPACING_BUTTON_PRIMARY: Letter-spacing de botão primário.
        LETTER_SPACING_HEADER: Letter-spacing de cabeçalho de tabela.
        LETTER_SPACING_TOOL_SELECTOR: Letter-spacing de seletor de tool.
        LETTER_SPACING_WINDOW_TITLE: Letter-spacing de título da janela.

        ── SPECIFICS (window title) ────────────────────────
        WINDOW_TITLE_FONT_SIZE: Tamanho da fonte do título da janela (px).
        WINDOW_TITLE_LETTER_SPACING: Letter-spacing do título da janela.

        ── SPECIFICS (title bar) ───────────────────────────
        TITLE_BAR_BORDER_WIDTH: Largura da borda da title bar.
        TITLE_BAR_BORDER_COLOR: Cor da borda da title bar (vazio=usa BG_PANEL).

        ── SPECIFICS (card) ────────────────────────────────
        CARD_PADDING_V: Padding vertical de card (px).
        CARD_PADDING_H: Padding horizontal de card (px).

        ── SPECIFICS (splitter) ────────────────────────────
        SPLITTER_HANDLE_WIDTH_H: Largura do handle horizontal (px).
        SPLITTER_HANDLE_WIDTH_V: Largura do handle vertical (px).

        ── SPECIFICS (menu) ────────────────────────────────
        MENU_PADDING: Padding do menu dropdown.
        MENU_MARGIN_V: Margem vertical do menu.
        MENU_ITEM_PADDING: Padding dos itens de menu.
        MENU_SEPARATOR_HEIGHT: Altura do separador de menu.
        MENU_SEPARATOR_MARGIN: Margem do separador de menu.

        ── SPECIFICS (table) ───────────────────────────────
        HEADER_FONT_SIZE: Tamanho da fonte do cabeçalho (px).
        HEADER_LETTER_SPACING: Letter-spacing do cabeçalho.
        TABLE_ITEM_PADDING: Padding dos itens de tabela.
        HEADER_PADDING: Padding do cabeçalho.

        ── GRADIENT CONFIG ─────────────────────────────────
        GRADIENT_BUTTON: Par (start,end) para gradiente de botão secundário.
        GRADIENT_PANEL: Par (start,end) para gradiente de painéis.
        GRADIENT_TAB: Par (start,end) para gradiente de tabs.
        GRADIENT_INPUT: Par (start,end) para gradiente de inputs.
        GRADIENT_ACCENT_TYPE: Tipo de gradiente acento (GradientType ou None=LINEAR).
        GRADIENT_ACCENT_STOPS: Stops multi-stop para gradiente acento.
        GRADIENT_ACCENT_ANGLE: Ângulo do gradiente acento (graus).
        GRADIENT_BUTTON_TYPE: Tipo de gradiente de botão secundário.
        GRADIENT_BUTTON_STOPS: Stops multi-stop para botão secundário.
        GRADIENT_BUTTON_ANGLE: Ângulo do gradiente de botão secundário.
        GRADIENT_TAB_TYPE: Tipo de gradiente de tab.
        GRADIENT_TAB_STOPS: Stops multi-stop para tab.
        GRADIENT_TAB_ANGLE: Ângulo do gradiente de tab.
        GLOW_BUTTON_ENABLED: Se True, ativa glow em botões secundários.
        GLOW_TAB_ENABLED: Se True, ativa glow em tabs selecionadas.
        GRADIENT_RADIAL_CX/CY: Centro do gradiente radial (0.0-1.0).
        GRADIENT_RADIAL_FX/FY: Ponto focal do gradiente radial (0.0-1.0).
        GRADIENT_RADIAL_RADIUS: Raio do gradiente radial (0.0-1.0).
        GRADIENT_CONICAL_CX/CY: Centro do gradiente cônico (0.0-1.0).
        GRADIENT_CONICAL_ANGLE: Ângulo inicial do gradiente cônico.

        ── ALIASES DE COMPATIBILIDADE ──────────────────────
        BG_DEEPEST: Alias → SURFACE_0 (fundo absoluto).
        BG_DARK: Alias → SURFACE_1 (fundo padrão).
        BG_PANEL: Alias → SURFACE_2 (painéis base).
        BG_CARD: Alias → SURFACE_3 (cards).
        BG_ELEVATED: Alias → SURFACE_4 (elementos elevados).
        BG_SURFACE: Alias → SURFACE_5 (superfície hover).
        TITLE_BAR_BG: Alias → TITLE_BAR (barra de título).
        SHADOW: Alias → SHADOW_SM (sombra pequena).
        SHADOW_DEEP: Alias → SHADOW_LG (sombra profunda).
        BORDER: Alias → BORDER_DEFAULT (borda padrão).
        BORDER_HOVER: Alias → BORDER_ACCENT (borda hover).
        TEXT_BRIGHT: Alias → TEXT_HIGH (títulos).
        TEXT_PRIMARY: Alias → TEXT_MEDIUM (corpo).
        TEXT_SECONDARY: Alias → TEXT_LOW (secundário).
        TEXT_MUTED: Alias → TEXT_DISABLED (desabilitado).
        TEXT_ACCENT: Alias → ACCENT_TEXT (texto accent).
        TEXT_ACCENT_BRIGHT: Alias → ACCENT_BRIGHT (texto accent brilhante).
        ACCENT_COLOR: Alias → ACCENT (cor accent).
        ACCENT_COLOR_HOVER: Alias → ACCENT_HOVER.
        ACCENT_COLOR_ACTIVE: Alias → ACCENT_ACTIVE.
        ACCENT_COLOR_DIM: Alias → ACCENT_DIM.
        ACCENT_COLOR_LIGHT: Alias → ACCENT_LIGHT.
        ACCENT_COLOR_GRADIENT: Alias → ACCENT_GRADIENT.
        SUCCESS: Alias → COLOR_SUCCESS.
        SUCCESS_HOVER: Alias → COLOR_SUCCESS_HOVER.
        SUCCESS_DIM: Alias → COLOR_SUCCESS_DIM.
        WARNING: Alias → COLOR_WARNING.
        WARNING_HOVER: Alias → COLOR_WARNING_HOVER.
        WARNING_DIM: Alias → COLOR_WARNING_DIM.
        DANGER: Alias → COLOR_DANGER.
        DANGER_HOVER: Alias → COLOR_DANGER_HOVER.
        DANGER_DIM: Alias → COLOR_DANGER_DIM.
    """

    # ═══════════════════════════════════════════════════════════════════
    # 1. ACCENT — Cores de destaque principal
    # ═══════════════════════════════════════════════════════════════════

    ACCENT: str = ""
    """Cor principal de destaque (botões, links, seleção). Ex: '#C9A84C' (dourado)."""

    ACCENT_HOVER: str = ""
    """Hover / foco do accent. Ex: '#D4B85A'."""

    ACCENT_ACTIVE: str = ""
    """Estado pressed / ativo. Ex: '#B8983E'."""

    ACCENT_DIM: str = ""
    """Versão escurecida / muted do accent. Ex: '#8A7A3A'."""

    ACCENT_LIGHT: str = ""
    """Versão clara (badges, highlights sutis). Ex: '#E8D08A'."""

    ACCENT_SOFT: str = ""
    """Versão translucent rgba para backgrounds. Ex: 'rgba(201,168,76,0.12)'."""

    ACCENT_TEXT: str = ""
    """Cor para texto sobre superfície escura com cor de acento. Ex: '#C9A84C'."""

    ACCENT_BRIGHT: str = ""
    """Versão brilhante (glow, hover highlight). Ex: '#E0C878'."""

    ACCENT_GRADIENT: tuple[str, str] = ("", "")
    """Par (start, stop) para gradientes lineares de acento."""

    # ═══════════════════════════════════════════════════════════════════
    # 2. SURFACE — Níveis de profundidade (0 = mais fundo, 5 = mais alto)
    # ═══════════════════════════════════════════════════════════════════

    SURFACE_0: str = ""
    """Fundo absoluto (backdrop), profundidade 0. Ex: '#08080A'."""

    SURFACE_1: str = ""
    """Fundo padrão da janela, profundidade 1. Ex: '#0C0C0F'."""

    SURFACE_2: str = ""
    """Painéis base / side panels, profundidade 2. Ex: '#121216'."""

    SURFACE_3: str = ""
    """Cards / groupbox / áreas elevadas, profundidade 3. Ex: '#18181D'."""

    SURFACE_4: str = ""
    """Inputs, tabelas, elementos interativos, profundidade 4. Ex: '#1E1E24'."""

    SURFACE_5: str = ""
    """Superfície hover / focus, profundidade 5. Ex: '#24242B'."""

    TITLE_BAR: str = ""
    """Cor de fundo da barra de título da janela. Ex: '#0A0A0D'."""

    # ── Gradientes de superfície (top-left → bottom-right) ─────

    GRADIENT_BUTTON: tuple[str, str] = ("", "")
    """Par (start, end) para gradiente de botões secundários / ghost."""

    GRADIENT_PANEL: tuple[str, str] = ("", "")
    """Par (start, end) para gradiente de side panels, tool panels."""

    GRADIENT_TAB: tuple[str, str] = ("", "")
    """Par (start, end) para gradiente de tabs (não selecionadas)."""

    GRADIENT_INPUT: tuple[str, str] = ("", "")
    """Par (start, end) para gradiente de inputs, combo, spin."""

    # ── Gradiente rico (3+ stops) ──

    GRADIENT_ACCENT_TYPE: "GradientType" = None
    """Tipo de gradiente para elementos de acento. None = LINEAR (compatibilidade)."""

    GRADIENT_ACCENT_STOPS: tuple = ()
    """Tupla de (posicao_float, cor_hex) ordenada para gradiente multi-stop acento."""

    GRADIENT_ACCENT_ANGLE: int = 45
    """Ângulo do gradiente linear de acento (graus)."""

    GRADIENT_BUTTON_TYPE: "GradientType" = None
    """Tipo de gradiente para botões secundários. None = usa GRADIENT_BUTTON (2-stop)."""

    GRADIENT_BUTTON_STOPS: tuple = ()
    """Stops multi-stop para gradiente de botão secundário."""

    GRADIENT_BUTTON_ANGLE: int = 45
    """Ângulo do gradiente de botão secundário (graus)."""

    GRADIENT_TAB_TYPE: "GradientType" = None
    """Tipo de gradiente para fundo de tabs. None = usa GRADIENT_TAB (2-stop)."""

    GRADIENT_TAB_STOPS: tuple = ()
    """Stops multi-stop para gradiente de fundo de tabs."""

    GRADIENT_TAB_ANGLE: int = 45
    """Ângulo do gradiente de tabs (graus)."""

    GLOW_BUTTON_ENABLED: bool = False
    """Se True, ativa glow (QGraphicsDropShadowEffect) em botões secundários."""

    GLOW_TAB_ENABLED: bool = False
    """Se True, ativa glow (borda brilhante) em tabs selecionadas."""

    GRADIENT_RADIAL_CX: float = 0.5
    """Centro X do gradiente radial (0.0-1.0)."""

    GRADIENT_RADIAL_CY: float = 0.5
    """Centro Y do gradiente radial (0.0-1.0)."""

    GRADIENT_RADIAL_FX: float = 0.5
    """Ponto focal X do gradiente radial (0.0-1.0)."""

    GRADIENT_RADIAL_FY: float = 0.5
    """Ponto focal Y do gradiente radial (0.0-1.0)."""

    GRADIENT_RADIAL_RADIUS: float = 0.5
    """Raio do gradiente radial (0.0-1.0)."""

    GRADIENT_CONICAL_CX: float = 0.5
    """Centro X do gradiente cônico (0.0-1.0)."""

    GRADIENT_CONICAL_CY: float = 0.5
    """Centro Y do gradiente cônico (0.0-1.0)."""

    GRADIENT_CONICAL_ANGLE: float = 0.0
    """Ângulo inicial do gradiente cônico (graus)."""

    # ═══════════════════════════════════════════════════════════════════
    # 3. TEXT — Hierarquia de texto
    # ═══════════════════════════════════════════════════════════════════

    TEXT_HIGH: str = ""
    """Títulos, labels de alta importância. Ex: '#F0F0F0'."""

    TEXT_MEDIUM: str = ""
    """Corpo padrão, texto principal. Ex: '#DCDCDC'."""

    TEXT_LOW: str = ""
    """Secundário, metadados, texto auxiliar. Ex: '#888890'."""

    TEXT_DISABLED: str = ""
    """Widget desabilitado, baixo contraste. Ex: '#585860'."""

    TEXT_ON_ACCENT: str = ""
    """Texto sobre fundo ACCENT. Ex: '#08080A' (preto sobre dourado)."""

    TEXT_ON_DANGER: str = ""
    """Texto sobre fundo danger (close btn, btn_danger). Ex: '#FFFFFF'."""

    # ═══════════════════════════════════════════════════════════════════
    # 4. BORDER — Hierarquia de bordas
    # ═══════════════════════════════════════════════════════════════════

    BORDER_SUBTLE: str = ""
    """Linhas muito sutis (divisores leves). Ex: '#1A1A20'."""

    BORDER_DEFAULT: str = ""
    """Borda padrão de widgets. Ex: '#2A2A30'."""

    BORDER_STRONG: str = ""
    """Borda de destaque (foco, validação). Ex: '#3A3A44'."""

    BORDER_ACCENT: str = ""
    """Borda com cor de acento. Ex: '#C9A84C'."""

    DIVIDER: str = ""
    """Separadores (linhas horizontais/verticais). Ex: '#1A1A20'."""

    BORDER_GRADIENT_STOPS: tuple = ()
    """Stops para borda gradiente ('efeito foil'). Tupla vazia = desligado."""

    BORDER_GRADIENT_WIDTH: float = 1.0
    """Largura da borda gradiente (px)."""

    # ═══════════════════════════════════════════════════════════════════
    # 5. SHADOW — Sombras
    # ═══════════════════════════════════════════════════════════════════

    SHADOW_SM: str = ""
    """Sombra pequena. String com cor+alpha. Ex: '#040405'."""

    SHADOW_MD: str = ""
    """Sombra média. String com cor+alpha."""

    SHADOW_LG: str = ""
    """Sombra grande. String com cor+alpha. Ex: '#000000'."""

    SHADOW_XL: str = ""
    """Sombra extra grande. String com cor+alpha."""

    SHADOW_ACCENT: str = ""
    """Sombra com cor de acento (glow em string). Ex: '#C9A84C15'."""

    GLOW: str = ""
    """Brilho sutil. String cor+alpha para QSS. Ex: '#C9A84C15'."""

    GLOW_STRONG: str = ""
    """Brilho forte. String cor+alpha para QSS. Ex: '#C9A84C25'."""

    SHADOW_BLUR_SM: int = 0
    """Blur radius da sombra pequena para QGraphicsDropShadowEffect (px)."""

    SHADOW_BLUR_MD: int = 0
    """Blur radius da sombra média para QGraphicsDropShadowEffect (px)."""

    SHADOW_BLUR_LG: int = 0
    """Blur radius da sombra grande para QGraphicsDropShadowEffect (px)."""

    SHADOW_BLUR_XL: int = 0
    """Blur radius da sombra extra grande para QGraphicsDropShadowEffect (px)."""

    SHADOW_OFFSET_Y_SM: int = 0
    """Offset vertical da sombra pequena (px)."""

    SHADOW_OFFSET_Y_MD: int = 0
    """Offset vertical da sombra média (px)."""

    SHADOW_OFFSET_Y_LG: int = 0
    """Offset vertical da sombra grande (px)."""

    SHADOW_COLOR_RGB: str = "#000000"
    """Cor base da sombra sem alfa (#RRGGBB)."""

    SHADOW_COLOR_ALPHA: int = 0
    """Alfa da sombra (0-255). 0 = sombra invisível."""

    GLOW_BLUR: int = 0
    """Blur radius do glow (px). 0 = desligado."""

    GLOW_OFFSET_X: int = 0
    """Offset X do glow (px)."""

    GLOW_OFFSET_Y: int = 0
    """Offset Y do glow (px)."""

    GLOW_COLOR_RGB: str = ""
    """Cor do glow (#RRGGBB). Vazio = usa ACCENT do tema."""

    GLOW_ALPHA: int = 0
    """Alfa do glow (0-255). 0 = glow invisível."""

    GLOW_STRONG_BLUR: int = 0
    """Blur radius do glow forte (px)."""

    GLOW_STRONG_ALPHA: int = 0
    """Alfa do glow forte (0-255)."""

    # ═══════════════════════════════════════════════════════════════════
    # 6. RADIUS — Escala global de arredondamento (pixels)
    # ═══════════════════════════════════════════════════════════════════

    RADIUS_XS: int = 0
    """2px. Usado em: checkbox, scrollbar, spin btn."""

    RADIUS_SM: int = 0
    """4px. Usado em: badge, toolbar btn."""

    RADIUS_MD: int = 0
    """6px. Usado em: button, input, menu."""

    RADIUS_LG: int = 0
    """10px. Usado em: card, table, progress."""

    RADIUS_XL: int = 0
    """16px. Usado em: diálogos, painéis."""

    RADIUS_FULL: int = 999
    """999px (círculo/pill). Usado em: radio button, pill badges."""

    # ═══════════════════════════════════════════════════════════════════
    # 7. SPACE — Escala global de espaçamento (pixels inteiros)
    # ═══════════════════════════════════════════════════════════════════

    SPACE_XXS: int = 0
    """2px. Micro espaçamento entre elementos."""

    SPACE_XS: int = 0
    """4px. Espaçamento muito pequeno."""

    SPACE_SM: int = 0
    """8px. Espaçamento pequeno."""

    SPACE_MD: int = 0
    """12px. Espaçamento médio."""

    SPACE_LG: int = 0
    """16px. Espaçamento grande."""

    SPACE_XL: int = 0
    """24px. Espaçamento extra grande."""

    SPACE_2XL: int = 0
    """32px. Espaçamento de seção."""

    SPACE_3XL: int = 0
    """48px. Espaçamento de seção grande."""

    # ═══════════════════════════════════════════════════════════════════
    # 8. ICON — Tamanhos de ícone (pixels)
    # ═══════════════════════════════════════════════════════════════════

    ICON_XS: int = 0
    """12px. Tiny indicator."""

    ICON_SM: int = 0
    """16px. Menu item."""

    ICON_MD: int = 0
    """20px. Botão padrão."""

    ICON_LG: int = 0
    """24px. Seção, header."""

    ICON_XL: int = 0
    """32px. Featured, empty state."""

    TOOLBAR_ICON_SIZE: int = 0
    """Tamanho do ícone na toolbar (px). Ex: 20px."""

    # ═══════════════════════════════════════════════════════════════════
    # 9. ANIMATION — Durações de animação (ms) + easing
    # ═══════════════════════════════════════════════════════════════════

    ANIMATION_FAST: int = 0
    """120ms. Hover, micro-interações."""

    ANIMATION_NORMAL: int = 0
    """180ms. Transições padrão."""

    ANIMATION_SLOW: int = 0
    """260ms. Expansão, colapso."""

    EASING_STANDARD: str = ""
    """Curva de easing. Ex: 'cubic-bezier(0.4, 0, 0.2, 1)'."""

    # ═══════════════════════════════════════════════════════════════════
    # 10. OPACITY — Níveis de opacidade (0.0 = transparente, 1.0 = opaco)
    # ═══════════════════════════════════════════════════════════════════

    OPACITY_DISABLED: float = 0.0
    """Opacidade de widget desabilitado. Ex: 0.35."""

    OPACITY_MUTED: float = 0.0
    """Opacidade de texto/elemento secundário. Ex: 0.60."""

    OPACITY_HOVER: float = 0.0
    """Opacidade de feedback hover. Ex: 0.85."""

    OPACITY_ACTIVE: float = 0.0
    """Opacidade de estado ativo/pressed. Ex: 1.0."""

    # ═══════════════════════════════════════════════════════════════════
    # 11. LAYOUT — Layout global
    # ═══════════════════════════════════════════════════════════════════

    PAGE_PADDING: int = 0
    """Padding externo da página (px). Ex: 24."""

    SECTION_GAP: int = 0
    """Espaçamento entre seções (px). Ex: 24."""

    GRID_GAP: int = 0
    """Gap em layouts grid (px). Ex: 20."""

    CONTENT_MAX_WIDTH: int = 0
    """Largura máxima do conteúdo (px). Ex: 1600."""

    # ═══════════════════════════════════════════════════════════════════
    # 12. ELEVATION — Níveis de elevação (z-index conceitual)
    # ═══════════════════════════════════════════════════════════════════

    ELEVATION_FLAT: int = 0
    """Elevação flat (z-index 0)."""

    ELEVATION_LOW: int = 0
    """Elevação baixa (z-index 1)."""

    ELEVATION_MEDIUM: int = 0
    """Elevação média (z-index 2)."""

    ELEVATION_HIGH: int = 0
    """Elevação alta (z-index 3)."""

    # ═══════════════════════════════════════════════════════════════════
    # 13. OVERLAY — Sobreposições / Glass effect
    # ═══════════════════════════════════════════════════════════════════

    OVERLAY_BG: str = ""
    """Cor de fundo de modais/dialogs (rgba). Ex: 'rgba(8,8,10,0.75)'."""

    BACKDROP_BLUR: str = ""
    """Valor de desfoque do backdrop. Ex: '4px'."""

    # ═══════════════════════════════════════════════════════════════════
    # 14. FOCUS_RING — Anel de foco visual
    # ═══════════════════════════════════════════════════════════════════

    FOCUS_RING_COLOR: str = ""
    """Cor do anel de foco. Ex: '#C9A84C'."""

    FOCUS_RING_WIDTH: str = ""
    """Espessura do anel. Ex: '2px'."""

    FOCUS_RING_OFFSET: str = ""
    """Distância do elemento. Ex: '1px'."""

    # ═══════════════════════════════════════════════════════════════════
    # 15. STATUS — Cores de estado semântico
    # ═══════════════════════════════════════════════════════════════════

    COLOR_SUCCESS: str = ""
    """Verde - operação bem-sucedida. Ex: '#43A047'."""

    COLOR_SUCCESS_HOVER: str = ""
    """Hover do success. Ex: '#66BB6A'."""

    COLOR_SUCCESS_DIM: str = ""
    """Versão escurecida do success. Ex: '#2E7D32'."""

    COLOR_WARNING: str = ""
    """Amarelo/laranja - atenção. Ex: '#EF9A00'."""

    COLOR_WARNING_HOVER: str = ""
    """Hover do warning. Ex: '#FFB74D'."""

    COLOR_WARNING_DIM: str = ""
    """Versão escurecida do warning. Ex: '#BF6E00'."""

    COLOR_DANGER: str = ""
    """Vermelho - erro/perigo. Ex: '#D32F2F'."""

    COLOR_DANGER_HOVER: str = ""
    """Hover do danger. Ex: '#E53935'."""

    COLOR_DANGER_DIM: str = ""
    """Versão escurecida do danger. Ex: '#A02020'."""

    COLOR_INFO: str = ""
    """Azul - informação. Ex: '#5B9BD5'."""

    COLOR_INFO_HOVER: str = ""
    """Hover do info. Ex: '#7BB8E8'."""

    COLOR_INFO_DIM: str = ""
    """Versão escurecida do info. Ex: '#3A7CC2'."""

    # ═══════════════════════════════════════════════════════════════════
    # 16. FONT — Tipografia
    # ═══════════════════════════════════════════════════════════════════

    FONT_FAMILY_DEFAULT: str = ""
    """Família de fonte padrão. Ex: \"'Segoe UI', 'Inter', 'Roboto', sans-serif\"."""

    FONT_FAMILY_MONO: str = ""
    """Família de fonte monoespaçada. Ex: \"'Consolas', 'Courier New', monospace\"."""

    FONT_FAMILY_DISPLAY: str = ""
    """Fonte display/serif para títulos editoriais. Vazio = usa DEFAULT."""

    FONT_LETTER_SPACING_DISPLAY: int = 0
    """Letter-spacing numérico para QFont.setLetterSpacing (pixels). 0 = sem extra."""

    FONT_SIZE_TITLE: int = 0
    """Tamanho da fonte de título (px). Ex: 21."""

    FONT_SIZE_BIG: int = 0
    """Tamanho da fonte grande (px). Ex: 16."""

    FONT_SIZE_NORMAL: int = 0
    """Tamanho da fonte normal (px). Ex: 13."""

    FONT_SIZE_SMALL: int = 0
    """Tamanho da fonte pequena (px). Ex: 11."""

    FONT_SIZE_TINY: int = 0
    """Tamanho da fonte muito pequena (px). Ex: 10."""

    FONT_WEIGHT_NORMAL: int = 400
    """Peso normal (400)."""

    FONT_WEIGHT_BOLD: int = 600
    """Peso bold (600)."""

    FONT_WEIGHT_EXTRABOLD: int = 700
    """Peso extra bold (700)."""

    FONT_WEIGHT_HEAVY: int = 800
    """Peso heavy (800)."""

    # ═══════════════════════════════════════════════════════════════════
    # 17. DIMENSIONS — Alturas e tamanhos de widgets
    # ═══════════════════════════════════════════════════════════════════

    INPUT_HEIGHT: int = 0
    """Altura de inputs (px). Ex: 24."""

    BUTTON_HEIGHT: int = 0
    """Altura de botões standard (px)."""

    BUTTON_HEIGHT_PRIMARY: int = 0
    """Altura de botões primários (px)."""

    ITEM_HEIGHT: int = 0
    """Altura de itens de lista (px)."""

    CHECKBOX_SIZE: int = 0
    """Largura/altura do checkbox (px). Ex: 16."""

    RADIO_SIZE: int = 0
    """Largura/altura do radio button (px). Ex: 16."""

    SCROLLBAR_WIDTH: int = 0
    """Largura da scrollbar vertical (px). Ex: 6."""

    SCROLLBAR_MIN_HEIGHT: int = 0
    """Altura mínima do handle da scrollbar (px). Ex: 28."""

    TAB_HEIGHT: int = 0
    """Altura de tabs (px)."""

    TAB_CLOSE_BUTTON_SIZE: int = 0
    """Tamanho do botão fechar tab (px). Ex: 20."""

    CLOSE_BUTTON_BORDER_RADIUS: int = 0
    """Border-radius do botão fechar (px). Ex: 3."""

    PROGRESS_BAR_HEIGHT: int = 0
    """Altura da progress bar (px). Ex: 18."""

    TITLE_BTN_HEIGHT: int = 0
    """Altura dos botões da title bar (px). Ex: 22."""

    TITLE_BTN_WIDTH: int = 0
    """Largura dos botões da title bar (px). Ex: 28."""

    TITLE_BTN_FONT_SIZE: int = 0
    """Tamanho da fonte dos botões da title bar (px). Ex: 11."""

    TOOLBAR_BTN_SIZE: int = 0
    """Tamanho do botão da toolbar (px). Ex: 40."""

    TOOLBAR_BTN_HOVER_GROW: int = 0
    """Pixels extras no hover (animação grow). Ex: 4."""

    GROUP_MARGIN_TOP: int = 0
    """Margem superior do groupbox (px). Ex: 8."""

    SPLITTER_HANDLE_WIDTH: int = 0
    """Largura do handle do splitter (px). Ex: 4."""

    # ═══════════════════════════════════════════════════════════════════
    # 18. SPECIFICS — Tokens específicos de implementação
    # ═══════════════════════════════════════════════════════════════════

    # ── Border Radius específicos ──

    BORDER_RADIUS_CARD: int = 0
    """Border-radius de cards (px). ≈ RADIUS_LG."""

    BORDER_RADIUS_BUTTON: int = 0
    """Border-radius de botões (px). ≈ RADIUS_MD."""

    BORDER_RADIUS_INPUT: int = 0
    """Border-radius de inputs (px). ≈ RADIUS_MD."""

    BORDER_RADIUS_CHECKBOX: int = 0
    """Border-radius de checkbox (px). ≈ RADIUS_XS+1."""

    BORDER_RADIUS_RADIO: int = 0
    """Border-radius de radio button (px). Usar 0 ou RADIUS_FULL."""

    BORDER_RADIUS_BADGE: int = 0
    """Border-radius de badges (px). ≈ RADIUS_SM."""

    BORDER_RADIUS_PROGRESS: int = 0
    """Border-radius de progress bar (px)."""

    BORDER_RADIUS_TABLE: int = 0
    """Border-radius de tabelas (px). ≈ RADIUS_SM*2."""

    BORDER_RADIUS_TITLE_BTN: int = 0
    """Border-radius dos botões da title bar (px)."""

    BORDER_RADIUS_TOOLBAR_BTN: int = 0
    """Border-radius dos botões da toolbar (px). ≈ RADIUS_SM."""

    BORDER_RADIUS_GHOST: int = 0
    """Border-radius do botão ghost (px)."""

    BORDER_RADIUS_TOOL_SELECTOR: int = 0
    """Border-radius do seletor de tool (px). ≈ RADIUS_MD."""

    BORDER_RADIUS_SCROLLBAR: int = 0
    """Border-radius da scrollbar (px). ≈ RADIUS_XS."""

    BORDER_RADIUS_SPINBOX_BTN: int = 0
    """Border-radius dos botões do spinbox (px). ≈ RADIUS_XS."""

    BORDER_RADIUS_TAB_CLOSE: int = 0
    """Border-radius do botão fechar tab (px)."""

    BORDER_RADIUS_COMBO_POPUP: int = 0
    """Border-radius do popup combobox (px). ≈ RADIUS_SM."""

    BORDER_RADIUS_MENU: int = 0
    """Border-radius do menu dropdown (px). ≈ RADIUS_MD."""

    BORDER_RADIUS_MENU_ITEM: int = 0
    """Border-radius dos itens de menu (px). ≈ RADIUS_XS+1."""

    BORDER_RADIUS_GROUP_TITLE: int = 0
    """Border-radius do título groupbox (px). ≈ RADIUS_SM."""

    BORDER_RADIUS_DIALOG: int = 0
    """Border-radius de diálogos (px). ≈ RADIUS_XL."""

    MENUBAR_ITEM_BORDER_RADIUS: int = 0
    """Border-radius dos itens da menubar (px)."""

    # ── Checkbox ──

    CHECKBOX_BORDER_WIDTH: int = 0
    """Largura da borda do checkbox (px)."""

    CHECKBOX_SPACING: int = 0
    """Espaçamento entre checkbox e label (px). Ex: 8."""

    # ── Badge ──

    BADGE_PADDING_V: str = ""
    """Padding vertical do badge. Ex: '3px'."""

    BADGE_PADDING_H: str = ""
    """Padding horizontal do badge. Ex: '12px'."""

    BADGE_LETTER_SPACING: str = ""
    """Letter-spacing do badge. Ex: '0.3px'."""

    BADGE_OUTLINE_ENABLED: bool = False
    """Se True, usa badge outline (borda+translúcido) em vez de preenchido."""

    BADGE_OUTLINE_BORDER_WIDTH: int = 1
    """Largura da borda do badge outline (px)."""

    BADGE_OUTLINE_BG_ALPHA: int = 0
    """Alfa do fundo translúcido do badge outline (0-255)."""

    # ── Button ──

    BUTTON_PADDING_V: str = ""
    """Padding vertical de botão padrão. Ex: '2px'."""

    BUTTON_PADDING_H: str = ""
    """Padding horizontal de botão padrão. Ex: '2px'."""

    BUTTON_PADDING_V_SMALL: str = ""
    """Padding vertical de botão pequeno. Ex: '2px'."""

    BUTTON_PADDING_H_SMALL: str = ""
    """Padding horizontal de botão pequeno. Ex: '2px'."""

    BUTTON_PADDING_V_PRIMARY: str = ""
    """Padding vertical de botão primário. Ex: '2px'."""

    BUTTON_PADDING_H_PRIMARY: str = ""
    """Padding horizontal de botão primário. Ex: '2px'."""

    BUTTON_LETTER_SPACING_NORMAL: str = ""
    """Letter-spacing de botão normal. Ex: '0.3px'."""

    BUTTON_LETTER_SPACING_PRIMARY: str = ""
    """Letter-spacing de botão primário. Ex: '0.5px'."""

    # ── Toolbar ──

    TOOLBAR_BTN_PADDING_V: str = ""
    """Padding vertical do botão toolbar. Ex: '4px'."""

    TOOLBAR_BTN_PADDING_H: str = ""
    """Padding horizontal do botão toolbar. Ex: '10px'."""

    # ── Tool Selector ──

    TOOL_SELECTOR_PADDING_V: str = ""
    """Padding vertical do seletor de tool. Ex: '6px'."""

    TOOL_SELECTOR_PADDING_H: str = ""
    """Padding horizontal do seletor de tool. Ex: '4px'."""

    TOOL_SELECTOR_LETTER_SPACING: str = ""
    """Letter-spacing do seletor de tool. Ex: '0.3px'."""

    # ── Input ──

    INPUT_PADDING_V: str = ""
    """Padding vertical de input. Ex: '2px'."""

    INPUT_PADDING_H: str = ""
    """Padding horizontal de input. Ex: '2px'."""

    # ── SpinBox ──

    SPINBOX_PADDING: str = ""
    """Padding do spinbox. Ex: '3px 8px'."""

    SPINBOX_BTN_WIDTH: int = 0
    """Largura dos botões do spinbox (px). Ex: 16."""

    SPINBOX_BTN_MARGIN: str = ""
    """Margem dos botões do spinbox. Ex: '1px'."""

    # ── ComboBox ──

    COMBOBOX_PADDING: str = ""
    """Padding do combobox. Ex: '3px 8px'."""

    COMBOBOX_MIN_WIDTH: int = 0
    """Largura mínima do combobox (px). Ex: 80."""

    COMBOBOX_DROPDOWN_WIDTH: int = 0
    """Largura do dropdown button (px). Ex: 22."""

    COMBOBOX_ARROW_SIZE: str = ""
    """Tamanho da seta do combobox. Ex: '4px'."""

    COMBOBOX_POPUP_BORDER_RADIUS: int = 0
    """Border-radius do popup combobox (px). Ex: 4."""

    # ── TextEdit / TextBrowser ──

    TEXT_EDIT_PADDING: str = ""
    """Padding do text edit. Ex: '8px'."""

    TEXT_EDIT_FONT_SIZE: int = 0
    """Tamanho da fonte do text edit (px). Ex: 12."""

    # ── GroupBox ──

    GROUP_TITLE_LEFT: int = 0
    """Offset horizontal do título do groupbox (px). Ex: 4."""

    GROUP_TITLE_TOP: int = 0
    """Offset vertical do título do groupbox (px). Ex: -2."""

    GROUP_TITLE_PADDING: str = ""
    """Padding do título do groupbox. Ex: '0 6px'."""

    GROUP_TITLE_BORDER_RADIUS: int = 0
    """Border-radius do título do groupbox (px). Ex: 4."""

    GROUP_TITLE_LETTER_SPACING: str = ""
    """Letter-spacing do título do groupbox. Ex: '0.5px'."""

    # ── Letter Spacing ──

    LETTER_SPACING_TITLE: str = ""
    """Letter-spacing de títulos grandes (header_title). Ex: '1px'."""

    LETTER_SPACING_BADGE: str = ""
    """Letter-spacing de badges. Ex: '0.3px'."""

    LETTER_SPACING_GROUP: str = ""
    """Letter-spacing de título de groupbox. Ex: '0.5px'."""

    LETTER_SPACING_BUTTON: str = ""
    """Letter-spacing de botão normal. Ex: '0.3px'."""

    LETTER_SPACING_BUTTON_PRIMARY: str = ""
    """Letter-spacing de botão primário. Ex: '0.5px'."""

    LETTER_SPACING_HEADER: str = ""
    """Letter-spacing de cabeçalho de tabela. Ex: '0.3px'."""

    LETTER_SPACING_TOOL_SELECTOR: str = ""
    """Letter-spacing de seletor de tool. Ex: '0.3px'."""

    LETTER_SPACING_WINDOW_TITLE: str = ""
    """Letter-spacing de título da janela. Ex: '0.3px'."""

    # ── Window Title ──

    WINDOW_TITLE_FONT_SIZE: int = 0
    """Tamanho da fonte do título da janela (px). Ex: 11."""

    WINDOW_TITLE_LETTER_SPACING: str = ""
    """Letter-spacing do título da janela. Ex: '0.3px'."""

    # ── Title Bar ──

    TITLE_BAR_BORDER_WIDTH: str = ""
    """Largura da borda da title bar. Ex: '1px'."""

    TITLE_BAR_BORDER_COLOR: str = ""
    """Cor da borda da title bar. Vazio = usa BG_PANEL."""

    # ── Card ──

    CARD_PADDING_V: int = 0
    """Padding vertical de card (px). Ex: 16."""

    CARD_PADDING_H: int = 0
    """Padding horizontal de card (px). Ex: 10."""

    # ── Splitter ──

    SPLITTER_HANDLE_WIDTH_H: int = 0
    """Largura do handle do splitter horizontal (px). Ex: 4."""

    SPLITTER_HANDLE_WIDTH_V: int = 0
    """Largura do handle do splitter vertical (px). Ex: 4."""

    # ── Menu ──

    MENU_PADDING: str = ""
    """Padding do menu dropdown. Ex: '2px'."""

    MENU_MARGIN_V: str = ""
    """Margem vertical do menu. Ex: '1px 0'."""

    MENU_ITEM_PADDING: str = ""
    """Padding dos itens de menu. Ex: '4px 16px 4px 8px'."""

    MENU_SEPARATOR_HEIGHT: str = ""
    """Altura do separador de menu. Ex: '1px'."""

    MENU_SEPARATOR_MARGIN: str = ""
    """Margem do separador de menu. Ex: '2px 6px'."""

    # ── Table / Header ──

    HEADER_FONT_SIZE: int = 0
    """Tamanho da fonte do cabeçalho de tabela (px). Ex: 11."""

    HEADER_LETTER_SPACING: str = ""
    """Letter-spacing do cabeçalho de tabela. Ex: '0.3px'."""

    TABLE_ITEM_PADDING: str = ""
    """Padding dos itens de tabela. Ex: '3px 6px'."""

    HEADER_PADDING: str = ""
    """Padding do cabeçalho de tabela. Ex: '4px 6px'."""

    # ═══════════════════════════════════════════════════════════════════
    # ALIASES DE COMPATIBILIDADE RETROATIVA
    # ═══════════════════════════════════════════════════════════════════

    # ── Fundos (BG_*) → SURFACE ──

    BG_DEEPEST: str = ""
    """Alias de compatibilidade → SURFACE_0 (fundo absoluto / backdrop)."""

    BG_DARK: str = ""
    """Alias de compatibilidade → SURFACE_1 (fundo padrão da janela)."""

    BG_PANEL: str = ""
    """Alias de compatibilidade → SURFACE_2 (painéis base / side panels)."""

    BG_CARD: str = ""
    """Alias de compatibilidade → SURFACE_3 (cards / groupbox)."""

    BG_ELEVATED: str = ""
    """Alias de compatibilidade → SURFACE_4 (elementos elevados / inputs)."""

    BG_SURFACE: str = ""
    """Alias de compatibilidade → SURFACE_5 (superfície hover / focus)."""

    TITLE_BAR_BG: str = ""
    """Alias de compatibilidade → TITLE_BAR (barra de título da janela)."""

    # ── Sombras (SHADOW*) → SHADOW ──

    SHADOW: str = ""
    """Alias de compatibilidade → SHADOW_SM (sombra pequena)."""

    SHADOW_DEEP: str = ""
    """Alias de compatibilidade → SHADOW_LG (sombra grande/profunda)."""

    # ── Bordas (BORDER*) → BORDER ──

    BORDER: str = ""
    """Alias de compatibilidade → BORDER_DEFAULT (borda padrão de widgets)."""

    BORDER_HOVER: str = ""
    """Alias de compatibilidade → BORDER_ACCENT (borda com cor de acento no hover)."""

    # ── Texto (TEXT_*) → TEXT / ACCENT ──

    TEXT_BRIGHT: str = ""
    """Alias de compatibilidade → TEXT_HIGH (títulos, labels importantes)."""

    TEXT_PRIMARY: str = ""
    """Alias de compatibilidade → TEXT_MEDIUM (corpo padrão)."""

    TEXT_SECONDARY: str = ""
    """Alias de compatibilidade → TEXT_LOW (secundário, metadados)."""

    TEXT_MUTED: str = ""
    """Alias de compatibilidade → TEXT_DISABLED (widget desabilitado)."""

    TEXT_ACCENT: str = ""
    """Alias de compatibilidade → ACCENT_TEXT (texto sobre fundo escuro com cor de acento)."""

    TEXT_ACCENT_BRIGHT: str = ""
    """Alias de compatibilidade → ACCENT_BRIGHT (versão brilhante do texto de acento)."""

    # ── Acento (ACCENT_COLOR_*) → ACCENT ──

    ACCENT_COLOR: str = ""
    """Alias de compatibilidade → ACCENT (cor principal de destaque)."""

    ACCENT_COLOR_HOVER: str = ""
    """Alias de compatibilidade → ACCENT_HOVER (hover / foco)."""

    ACCENT_COLOR_ACTIVE: str = ""
    """Alias de compatibilidade → ACCENT_ACTIVE (pressed / ativo)."""

    ACCENT_COLOR_DIM: str = ""
    """Alias de compatibilidade → ACCENT_DIM (versão escurecida / muted)."""

    ACCENT_COLOR_LIGHT: str = ""
    """Alias de compatibilidade → ACCENT_LIGHT (versão clara / highlights)."""

    ACCENT_COLOR_GRADIENT: tuple[str, str] = ("", "")
    """Alias de compatibilidade → ACCENT_GRADIENT (par start/stop para gradientes)."""

    # ── Status (SUCCESS/WARNING/DANGER*) → COLOR_ ──

    SUCCESS: str = ""
    """Alias de compatibilidade → COLOR_SUCCESS (verde - operação bem-sucedida)."""

    SUCCESS_HOVER: str = ""
    """Alias de compatibilidade → COLOR_SUCCESS_HOVER."""

    SUCCESS_DIM: str = ""
    """Alias de compatibilidade → COLOR_SUCCESS_DIM."""

    WARNING: str = ""
    """Alias de compatibilidade → COLOR_WARNING (amarelo/laranja - atenção)."""

    WARNING_HOVER: str = ""
    """Alias de compatibilidade → COLOR_WARNING_HOVER."""

    WARNING_DIM: str = ""
    """Alias de compatibilidade → COLOR_WARNING_DIM."""

    DANGER: str = ""
    """Alias de compatibilidade → COLOR_DANGER (vermelho - erro/perigo)."""

    DANGER_HOVER: str = ""
    """Alias de compatibilidade → COLOR_DANGER_HOVER."""

    DANGER_DIM: str = ""
    """Alias de compatibilidade → COLOR_DANGER_DIM."""