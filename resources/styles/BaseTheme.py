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
    """Classe base para temas. Todos os atributos devem ser sobrescritos."""

    # ═══════════════════════════════════════════════════════════════════
    # 1. ACCENT — Cores de destaque principal
    #    Define a identidade visual do tema (dourado, ciano, azul, etc.)
    #    ACCENT        → cor principal (botões, links, seleção)
    #    ACCENT_HOVER  → hover / foco
    #    ACCENT_ACTIVE → pressed / ativo
    #    ACCENT_DIM    → versão escurecida / muted
    #    ACCENT_LIGHT  → versão clara (badges, highlights sutis)
    #    ACCENT_SOFT   → versão translucent (rgba) para backgrounds
    #    ACCENT_TEXT   → cor para texto sobre superfície escura
    #    ACCENT_BRIGHT → versão brilhante (glow, hover highlight)
    #    ACCENT_GRADIENT → par (start, stop) para gradientes lineares
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
    #    SURFACE_0 → fundo absoluto (backdrop)
    #    SURFACE_1 → fundo padrão da janela
    #    SURFACE_2 → painéis base / side panels
    #    SURFACE_3 → cards / groupbox / áreas elevadas
    #    SURFACE_4 → inputs, tabelas, elementos interativos
    #    SURFACE_5 → hover / focus state
    #    TITLE_BAR → barra de título da janela
    # ═══════════════════════════════════════════════════════════════════

    SURFACE_0: str = ""       # fundo absoluto
    SURFACE_1: str = ""       # fundo padrão
    SURFACE_2: str = ""       # painéis base
    SURFACE_3: str = ""       # cards / groupbox
    SURFACE_4: str = ""       # elementos elevados
    SURFACE_5: str = ""       # superfície (hover, focus)
    TITLE_BAR: str = ""       # barra de título

    # ── Gradientes de superfície (top-left → bottom-right) ─────
    # Cada gradiente é uma tupla (start_color, end_color).
    # start_color = versão mais escura, end_color = versão mais clara.
    # Direção: x1:0,y1:0 → x2:1,y2:1 (canto superior esquerdo → inferior direito)
    GRADIENT_BUTTON: tuple[str, str] = ("", "")  # botões secundários / ghost
    GRADIENT_PANEL: tuple[str, str] = ("", "")   # side panels, tool panels
    GRADIENT_TAB: tuple[str, str] = ("", "")     # tabs (não selecionadas)
    GRADIENT_INPUT: tuple[str, str] = ("", "")   # inputs, combo, spin

    # ── Gradiente rico (3+ stops) para uso em QPainter/QLinearGradient e/ou QSS ──
    # Formato: tupla de (posicao_float_0_a_1, cor_hex_str), ordenada por posição.
    # Tupla vazia = recurso desligado, componente deve usar ACCENT_GRADIENT (2 stops) como fallback.

    # Tipo de gradiente para elementos de acento (botões, progress, etc.)
    # Valores possíveis: GradientType.LINEAR | GradientType.RADIAL | GradientType.CONICAL
    # Padrão = LINEAR (compatibilidade retroativa total)
    GRADIENT_ACCENT_TYPE: "GradientType" = None  # noqa: F821 — resolvido em __init_subclass__
    GRADIENT_ACCENT_STOPS: tuple = ()
    GRADIENT_ACCENT_ANGLE: int = 45   # graus; 45 = comportamento atual (top-left → bottom-right)

    # ── Parâmetros específicos para gradientes RADIAL e CONICAL ──────────
    # Radial: ponto focal (fx,fy) e raio como fração 0.0–1.0
    GRADIENT_RADIAL_CX: float = 0.5
    GRADIENT_RADIAL_CY: float = 0.5
    GRADIENT_RADIAL_FX: float = 0.5
    GRADIENT_RADIAL_FY: float = 0.5
    GRADIENT_RADIAL_RADIUS: float = 0.5

    # Conical: centro (cx,cy) e ângulo inicial em graus
    GRADIENT_CONICAL_CX: float = 0.5
    GRADIENT_CONICAL_CY: float = 0.5
    GRADIENT_CONICAL_ANGLE: float = 0.0

    # ═══════════════════════════════════════════════════════════════════
    # 3. TEXT — Hierarquia de texto
    #    TEXT_HIGH      → títulos, labels importantes
    #    TEXT_MEDIUM    → corpo padrão
    #    TEXT_LOW       → secundário, metadados
    #    TEXT_DISABLED  → widget desabilitado
    #    TEXT_ON_ACCENT → texto sobre fundo ACCENT
    # ═══════════════════════════════════════════════════════════════════

    TEXT_HIGH: str = ""
    TEXT_MEDIUM: str = ""
    TEXT_LOW: str = ""
    TEXT_DISABLED: str = ""
    TEXT_ON_ACCENT: str = ""
    TEXT_ON_DANGER: str = ""   # texto sobre fundo danger (ex: close btn, btn_danger)

    # ═══════════════════════════════════════════════════════════════════
    # 4. BORDER — Hierarquia de bordas
    #    BORDER_SUBTLE  → linhas muito sutis (divisores leves)
    #    BORDER_DEFAULT → borda padrão de widgets
    #    BORDER_STRONG  → borda de destaque (foco, validação)
    #    BORDER_ACCENT  → borda com cor de acento
    #    DIVIDER        → separadores (linhas horizontais/verticais)
    #
    #    Abaixo: tokens para borda em gradiente ("efeito foil")
    #    Tupla vazia = sem gradiente, componente deve usar BORDER_ACCENT
    #    (cor sólida) como fallback.
    # ═══════════════════════════════════════════════════════════════════

    BORDER_SUBTLE: str = ""
    BORDER_DEFAULT: str = ""
    BORDER_STRONG: str = ""
    BORDER_ACCENT: str = ""
    DIVIDER: str = ""

    # ── Borda em gradiente ("efeito foil") ────────────────────────
    BORDER_GRADIENT_STOPS: tuple = ()
    BORDER_GRADIENT_WIDTH: float = 1.0

    # ═══════════════════════════════════════════════════════════════════
    # 5. SHADOW — Sombras por tamanho (usadas em QGraphicsDropShadowEffect)
    #    SHADOW_SM/D/LG/XL → string com tom (cor) da sombra, estilo legado
    #    SHADOW_ACCENT  → sombra com cor de acento (glow) — string legado
    #    GLOW / GLOW_STRONG → brilho legado como string (cor+alpha)
    #
    #    Abaixo: versões numéricas discretas para QGraphicsDropShadowEffect
    #    (blur radius, offset, cor rgb + canal alfa separado).
    #    blur=0 ou alpha=0 ⇒ efeito desligado, tema antigo não muda visualmente.
    # ═══════════════════════════════════════════════════════════════════

    SHADOW_SM: str = ""
    SHADOW_MD: str = ""
    SHADOW_LG: str = ""
    SHADOW_XL: str = ""
    SHADOW_ACCENT: str = ""
    GLOW: str = ""
    GLOW_STRONG: str = ""

    # ── Sombra estruturada (uso em QGraphicsDropShadowEffect, não em QSS) ──
    SHADOW_BLUR_SM: int = 0
    SHADOW_BLUR_MD: int = 0
    SHADOW_BLUR_LG: int = 0
    SHADOW_BLUR_XL: int = 0
    SHADOW_OFFSET_Y_SM: int = 0
    SHADOW_OFFSET_Y_MD: int = 0
    SHADOW_OFFSET_Y_LG: int = 0
    SHADOW_COLOR_RGB: str = "#000000"   # cor base, sem alfa
    SHADOW_COLOR_ALPHA: int = 0          # 0-255, 0 = sombra invisível

    # ── Glow (brilho) estruturado ──
    GLOW_BLUR: int = 0
    GLOW_OFFSET_X: int = 0
    GLOW_OFFSET_Y: int = 0
    GLOW_COLOR_RGB: str = ""             # se vazio, cai no ACCENT do tema
    GLOW_ALPHA: int = 0                  # 0-255, 0 = glow invisível
    GLOW_STRONG_BLUR: int = 0
    GLOW_STRONG_ALPHA: int = 0

    # ═══════════════════════════════════════════════════════════════════
    # 6. RADIUS — Escala global de arredondamento (pixels)
    #    RADIUS_XS   → 2px  (checkbox, scrollbar, spin btn)
    #    RADIUS_SM   → 4px  (badge, toolbar btn)
    #    RADIUS_MD   → 6px  (button, input, menu)
    #    RADIUS_LG   → 10px (card, table, progress)
    #    RADIUS_XL   → 16px (diálogos, painéis)
    #    RADIUS_FULL → 999  (círculo / pill)
    # ═══════════════════════════════════════════════════════════════════

    RADIUS_XS: int = 0
    RADIUS_SM: int = 0
    RADIUS_MD: int = 0
    RADIUS_LG: int = 0
    RADIUS_XL: int = 0
    RADIUS_FULL: int = 999

    # ═══════════════════════════════════════════════════════════════════
    # 7. SPACE — Escala global de espaçamento (pixels inteiros)
    #    Usada para padding, margin, gap entre elementos.
    #    SPACE_XXS →  2px   (micro espaçamento)
    #    SPACE_XS  →  4px   (muito pequeno)
    #    SPACE_SM  →  8px   (pequeno)
    #    SPACE_MD  → 12px   (médio)
    #    SPACE_LG  → 16px   (grande)
    #    SPACE_XL  → 24px   (extra grande)
    #    SPACE_2XL → 32px   (seção)
    #    SPACE_3XL → 48px   (seção grande)
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
    # 8. ICON — Tamanhos de ícone (pixels)
    #    ICON_XS → 12px (tiny indicator)
    #    ICON_SM → 16px (menu item)
    #    ICON_MD → 20px (botão padrão)
    #    ICON_LG → 24px (seção, header)
    #    ICON_XL → 32px (featured, empty state)
    #    TOOLBAR_ICON_SIZE → tamanho do ícone na toolbar (ex: 20px)
    # ═══════════════════════════════════════════════════════════════════

    ICON_XS: int = 0
    ICON_SM: int = 0
    ICON_MD: int = 0
    ICON_LG: int = 0
    ICON_XL: int = 0
    TOOLBAR_ICON_SIZE: int = 0

    # ═══════════════════════════════════════════════════════════════════
    # 9. ANIMATION — Durações de animação (ms) + easing
    #    ANIMATION_FAST   → 120ms (hover, micro-interações)
    #    ANIMATION_NORMAL → 180ms (transições padrão)
    #    ANIMATION_SLOW   → 260ms (expansão, colapso)
    #    EASING_STANDARD  → curva de easing (ex: cubic-bezier)
    # ═══════════════════════════════════════════════════════════════════

    ANIMATION_FAST: int = 0
    ANIMATION_NORMAL: int = 0
    ANIMATION_SLOW: int = 0
    EASING_STANDARD: str = ""

    # ═══════════════════════════════════════════════════════════════════
    # 10. OPACITY — Níveis de opacidade (0.0 = transparente, 1.0 = opaco)
    #     OPACITY_DISABLED → widget desabilitado
    #     OPACITY_MUTED    → texto/elemento secundário
    #     OPACITY_HOVER    → feedback hover
    #     OPACITY_ACTIVE   → estado ativo/pressed
    # ═══════════════════════════════════════════════════════════════════

    OPACITY_DISABLED: float = 0.0
    OPACITY_MUTED: float = 0.0
    OPACITY_HOVER: float = 0.0
    OPACITY_ACTIVE: float = 0.0

    # ═══════════════════════════════════════════════════════════════════
    # 11. LAYOUT — Layout global
    #     PAGE_PADDING      → padding externo da página
    #     SECTION_GAP       → espaçamento entre seções
    #     GRID_GAP          → gap em layouts grid
    #     CONTENT_MAX_WIDTH → largura máxima do conteúdo (px)
    # ═══════════════════════════════════════════════════════════════════

    PAGE_PADDING: int = 0
    SECTION_GAP: int = 0
    GRID_GAP: int = 0
    CONTENT_MAX_WIDTH: int = 0

    # ═══════════════════════════════════════════════════════════════════
    # 12. ELEVATION — Níveis de elevação (z-index conceitual)
    #     Usado para determinar profundidade visual.
    # ═══════════════════════════════════════════════════════════════════

    ELEVATION_FLAT: int = 0
    ELEVATION_LOW: int = 0
    ELEVATION_MEDIUM: int = 0
    ELEVATION_HIGH: int = 0

    # ═══════════════════════════════════════════════════════════════════
    # 13. OVERLAY — Sobreposições / Glass effect
    #     OVERLAY_BG   → cor de fundo de modais/dialogs (rgba)
    #     BACKDROP_BLUR → valor de desfoque (ex: "4px")
    # ═══════════════════════════════════════════════════════════════════

    OVERLAY_BG: str = ""
    BACKDROP_BLUR: str = ""

    # ═══════════════════════════════════════════════════════════════════
    # 14. FOCUS_RING — Anel de foco visual
    #     Usado em inputs e botões para acessibilidade.
    #     FOCUS_RING_COLOR  → cor do anel
    #     FOCUS_RING_WIDTH  → espessura (ex: "2px")
    #     FOCUS_RING_OFFSET → distância do elemento (ex: "1px")
    # ═══════════════════════════════════════════════════════════════════

    FOCUS_RING_COLOR: str = ""
    FOCUS_RING_WIDTH: str = ""
    FOCUS_RING_OFFSET: str = ""

    # ═══════════════════════════════════════════════════════════════════
    # 15. STATUS — Cores de estado semântico
    #     success → verde (operação bem-sucedida)
    #     warning → amarelo/laranja (atenção)
    #     danger  → vermelho (erro, perigo)
    #     info    → azul (informação)
    #     Cada cor tem variantes: _HOVER, _DIM
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
    #     Famílias, tamanhos e pesos tipográficos.
    # ═══════════════════════════════════════════════════════════════════

    FONT_FAMILY_DEFAULT: str = ""
    FONT_FAMILY_MONO: str = ""

    # ── Fonte display/serif para títulos editoriais ──────────────
    # Vazio = usa FONT_FAMILY_DEFAULT como fallback.
    FONT_FAMILY_DISPLAY: str = ""

    # Letter-spacing numérico para QFont.setLetterSpacing (widgets
    # com paintEvent customizado). 0 = sem espaçamento extra.
    # Diferente de LETTER_SPACING_TITLE que é string CSS.
    FONT_LETTER_SPACING_DISPLAY: int = 0

    FONT_SIZE_TITLE: int = 0
    FONT_SIZE_BIG: int = 0
    FONT_SIZE_NORMAL: int = 0
    FONT_SIZE_SMALL: int = 0
    FONT_SIZE_TINY: int = 0

    # Nota: FONT_WEIGHT_NORMAL/BOLD/EXTRABOLD/HEAVY são constantes
    # globais de design (pesos de fonte não variam por tema).
    # Mantidos aqui para documentação e consistência de override.
    FONT_WEIGHT_NORMAL: int = 400
    FONT_WEIGHT_BOLD: int = 600
    FONT_WEIGHT_EXTRABOLD: int = 700
    FONT_WEIGHT_HEAVY: int = 800

    # ═══════════════════════════════════════════════════════════════════
    # 17. DIMENSIONS — Alturas e tamanhos de widgets
    #     Valores em pixels para dimensões fixas de componentes.
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
    TOOLBAR_BTN_SIZE: int = 0
    TOOLBAR_BTN_HOVER_GROW: int = 0   # pixels extras no hover (animação grow)
    GROUP_MARGIN_TOP: int = 0
    SPLITTER_HANDLE_WIDTH: int = 0

    # ═══════════════════════════════════════════════════════════════════
    # 18. SPECIFICS — Tokens específicos de implementação (não semânticos)
    #     Mantidos para compatibilidade retroativa com QSS existente.
    #     Novos temas devem mapear estes valores a partir dos tokens
    #     semânticos (RADIUS_XS..LG, SPACE_XXS..3XL, etc.).
    # ═══════════════════════════════════════════════════════════════════

    # ── Border Radius específicos (mapear de RADIUS_*) ────────────
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
    BORDER_RADIUS_DIALOG: int = 0    # ≈ RADIUS_XL (about dialog, modals)
    # Nota: MENUBAR_ITEM_BORDER_RADIUS era str; padronizado para int como os demais.
    # O px é concatenado no uso em AppStyles.menu_bar_style().
    MENUBAR_ITEM_BORDER_RADIUS: int = 0

    # ── Checkbox ─────────────────────────────────────────────────
    CHECKBOX_BORDER_WIDTH: int = 0
    CHECKBOX_SPACING: int = 0

    # ── Badge ────────────────────────────────────────────────────
    BADGE_PADDING_V: str = ""
    BADGE_PADDING_H: str = ""
    BADGE_LETTER_SPACING: str = ""

    # ── Badge Outline (variante contorno) ────────────────────────
    # False = usa o badge preenchido de sempre.
    BADGE_OUTLINE_ENABLED: bool = False
    BADGE_OUTLINE_BORDER_WIDTH: int = 1
    BADGE_OUTLINE_BG_ALPHA: int = 0   # 0-255, alfa do fundo translúcido (usa ACCENT_SOFT/ACCENT como base)

    # ── Button ───────────────────────────────────────────────────
    BUTTON_PADDING_V: str = ""
    BUTTON_PADDING_H: str = ""
    BUTTON_PADDING_V_SMALL: str = ""
    BUTTON_PADDING_H_SMALL: str = ""
    BUTTON_PADDING_V_PRIMARY: str = ""
    BUTTON_PADDING_H_PRIMARY: str = ""
    BUTTON_LETTER_SPACING_NORMAL: str = ""
    BUTTON_LETTER_SPACING_PRIMARY: str = ""

    # ── Toolbar ──────────────────────────────────────────────────
    TOOLBAR_BTN_PADDING_V: str = ""
    TOOLBAR_BTN_PADDING_H: str = ""

    # ── Tool Selector ────────────────────────────────────────────
    TOOL_SELECTOR_PADDING_V: str = ""
    TOOL_SELECTOR_PADDING_H: str = ""
    TOOL_SELECTOR_LETTER_SPACING: str = ""

    # ── Input ────────────────────────────────────────────────────
    INPUT_PADDING_V: str = ""
    INPUT_PADDING_H: str = ""

    # ── SpinBox ──────────────────────────────────────────────────
    SPINBOX_PADDING: str = ""
    SPINBOX_BTN_WIDTH: int = 0
    SPINBOX_BTN_MARGIN: str = ""

    # ── ComboBox ─────────────────────────────────────────────────
    COMBOBOX_PADDING: str = ""
    COMBOBOX_MIN_WIDTH: int = 0
    COMBOBOX_DROPDOWN_WIDTH: int = 0
    COMBOBOX_ARROW_SIZE: str = ""
    COMBOBOX_POPUP_BORDER_RADIUS: int = 0

    # ── TextEdit / TextBrowser ───────────────────────────────────
    TEXT_EDIT_PADDING: str = ""
    TEXT_EDIT_FONT_SIZE: int = 0

    # ── GroupBox ─────────────────────────────────────────────────
    GROUP_TITLE_LEFT: int = 0
    GROUP_TITLE_TOP: int = 0
    GROUP_TITLE_PADDING: str = ""
    GROUP_TITLE_BORDER_RADIUS: int = 0
    GROUP_TITLE_LETTER_SPACING: str = ""

    # ── Letter Spacing ───────────────────────────────────────────
    LETTER_SPACING_TITLE: str = ""       # títulos grandes (header_title)
    LETTER_SPACING_BADGE: str = ""       # badge
    LETTER_SPACING_GROUP: str = ""       # título de group box
    LETTER_SPACING_BUTTON: str = ""      # botão normal
    LETTER_SPACING_BUTTON_PRIMARY: str = ""  # botão primário
    LETTER_SPACING_HEADER: str = ""      # cabeçalho de tabela
    LETTER_SPACING_TOOL_SELECTOR: str = ""  # seletor de ferramenta
    LETTER_SPACING_WINDOW_TITLE: str = ""    # título da janela

    # ── Window Title ─────────────────────────────────────────────
    WINDOW_TITLE_FONT_SIZE: int = 0
    WINDOW_TITLE_LETTER_SPACING: str = ""

    # ── Title Bar ────────────────────────────────────────────────
    TITLE_BAR_BORDER_WIDTH: str = ""
    TITLE_BAR_BORDER_COLOR: str = ""

    # ── Card ─────────────────────────────────────────────────────
    CARD_PADDING_V: int = 0
    CARD_PADDING_H: int = 0

    # ── Splitter ─────────────────────────────────────────────────
    SPLITTER_HANDLE_WIDTH_H: int = 0
    SPLITTER_HANDLE_WIDTH_V: int = 0

    # ── Menu ─────────────────────────────────────────────────────
    MENU_PADDING: str = ""
    MENU_MARGIN_V: str = ""
    MENU_ITEM_PADDING: str = ""
    MENU_SEPARATOR_HEIGHT: str = ""
    MENU_SEPARATOR_MARGIN: str = ""

    # ── Table / Header ───────────────────────────────────────────
    HEADER_FONT_SIZE: int = 0
    HEADER_LETTER_SPACING: str = ""
    TABLE_ITEM_PADDING: str = ""
    HEADER_PADDING: str = ""

    # ═══════════════════════════════════════════════════════════════════
    # ALIASES DE COMPATIBILIDADE RETROATIVA
    # Mapeiam nomes antigos → tokens semânticos. Permitem que código
    # legado continue funcionando sem alterações.
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