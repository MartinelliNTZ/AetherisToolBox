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
    18. GRADIENT     — Configurações de gradiente multi-stop, tipo e ângulo
    19. SPECIFICS    — Tokens específicos de implementação (compatibilidade)

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
    """FUNDO de botões primários e links ativos.
    Cor principal de destaque da interface.
    Usado em: botão primário, links clicáveis, indicador de tab selecionada, checkbox marcado."""

    ACCENT_HOVER: str = ""
    """FUNDO de botão primário quando o mouse passa por cima (hover).
    Tom mais claro que ACCENT para feedback visual."""

    ACCENT_ACTIVE: str = ""
    """FUNDO de botão primário quando está sendo pressionado (click).
    Tom mais escuro que ACCENT para simular profundidade."""

    ACCENT_DIM: str = ""
    """BORDA e INDICADOR de elementos de acento em estado desabilitado ou muted.
    Usado como borda de tab selecionada, versão menos chamativa do accent."""

    ACCENT_LIGHT: str = ""
    """FUNDO de badges e highlights sutis.
    Versão clara do accent para elementos que precisam de destaque discreto."""

    ACCENT_SOFT: str = ""
    """FUNDO translúcido para hover e backgrounds de elementos com accent.
    Usa rgba para criar uma camada suave sobre superfícies escuras.
    Usado em: badge outline (fundo translúcido), overlay sutil."""

    ACCENT_TEXT: str = ""
    """COR do TEXTO que fica sobre fundo escuro com detalhes em accent.
    Usado em: labels de tool group, textos de botões ghost, títulos de groupbox."""

    ACCENT_BRIGHT: str = ""
    """COR de GLOW e HOVER highlight para textos sobre accent.
    Versão mais clara e brilhante do ACCENT_TEXT.
    Usado em: hover de botões secundários e ghost para efeito de iluminação."""

    ACCENT_GRADIENT: tuple[str, str] = ("", "")
    """GRADIENTE LINEAR de 2 cores para fundo de botões primários.
    Par (cor_inicio, cor_fim) — gradiente top-left → bottom-right."""

    # ═══════════════════════════════════════════════════════════════════
    # 2. SURFACE — Níveis de profundidade (0 = mais fundo, 5 = mais alto)
    # ═══════════════════════════════════════════════════════════════════

    SURFACE_0: str = ""
    """FUNDO mais profundo da hierarquia (backdrop/absoluto).
    Aparece em: fundo atrás de modais (fora do dialog), menus dropdown,
    fundo de áreas que precisam parecer 'cavadas' na tela."""

    SURFACE_1: str = ""
    """FUNDO padrão da janela principal (nível base).
    Cor principal de fundo da aplicação — a maior área visual."""

    SURFACE_2: str = ""
    """FUNDO de painéis laterais e barras secundárias.
    Usado em: side panels, console toolbar, tool panels.
    Um nível acima do fundo da janela para criar contraste sutil."""

    SURFACE_3: str = ""
    """FUNDO de cards, groupbox e áreas elevadas.
    Elementos que precisam parecer 'flutuando' sobre a superfície base.
    Usado em: cartões de conteúdo, QGroupBox, botão ghost hover."""

    SURFACE_4: str = ""
    """FUNDO de inputs, tabelas e elementos interativos.
    Áreas onde o usuário interage diretamente: campos de texto,
    combobox, spinbox, células de tabela, checkbox indicator."""

    SURFACE_5: str = ""
    """FUNDO de hover/focus em elementos interativos.
    Usado quando o mouse passa sobre inputs, botões com hover,
    e quando um campo recebe foco do teclado."""

    TITLE_BAR: str = ""
    """FUNDO da barra de título da janela (topo).
    Também usado como fundo da barra de menus principal."""

    # ── Gradientes de superfície (top-left → bottom-right) ─────

    GRADIENT_BUTTON: tuple[str, str] = ("", "")
    """GRADIENTE de fundo para botões secundários e ghost.
    Par (cor_inicio, cor_fim) — gradiente sutil top-left → bottom-right."""

    GRADIENT_PANEL: tuple[str, str] = ("", "")
    """GRADIENTE de fundo para side panels e tool panels.
    Aplicado em QWidget#tool_side_panel e QGroupBox."""

    GRADIENT_TAB: tuple[str, str] = ("", "")
    """GRADIENTE de fundo para tabs NÃO selecionadas.
    Aplicado em QTabBar::tab."""

    GRADIENT_INPUT: tuple[str, str] = ("", "")
    """GRADIENTE de fundo para inputs, combobox e spinbox.
    Aplicado em QLineEdit, QComboBox, QSpinBox."""

    # ── Gradiente rico (3+ stops) ──

    GRADIENT_ACCENT_TYPE: "GradientType" = None
    """TIPO de gradiente para elementos de acento (botão primário).
    Valores: GradientType.LINEAR (padrão), RADIAL, CONICAL.
    None = usa LINEAR para compatibilidade.
    ⚠ CONICAL só funciona em paintEvent custom, NÃO em QSS."""

    GRADIENT_ACCENT_STOPS: tuple = ()
    """STOPS multi-cor para gradiente de botão primário.
    Tupla de (posição_float 0.0-1.0, cor_hex) ordenada.
    Vazio = usa ACCENT_GRADIENT (2 stops) como fallback."""

    GRADIENT_ACCENT_ANGLE: int = 45
    """ÂNGULO do gradiente linear de acento em graus.
    0 = left→right, 45 = top-left→bottom-right, 90 = top→bottom."""

    GRADIENT_BUTTON_TYPE: "GradientType" = None
    """TIPO de gradiente para botões secundários.
    None = usa GRADIENT_BUTTON (2-stop) compatibilidade.
    ⚠ CONICAL só funciona em paintEvent custom."""

    GRADIENT_BUTTON_STOPS: tuple = ()
    """STOPS multi-cor para gradiente de botão secundário.
    Formato: (pos_float, cor_hex). Vazio = usa GRADIENT_BUTTON."""

    GRADIENT_BUTTON_ANGLE: int = 45
    """ÂNGULO do gradiente de botão secundário em graus."""

    GRADIENT_TAB_TYPE: "GradientType" = None
    """TIPO de gradiente para fundo de tabs.
    None = usa GRADIENT_TAB (2-stop). ⚠ CONICAL apenas paintEvent."""

    GRADIENT_TAB_STOPS: tuple = ()
    """STOPS multi-cor para gradiente de fundo de tabs.
    Vazio = usa GRADIENT_TAB (2-stop)."""

    GRADIENT_TAB_ANGLE: int = 45
    """ÂNGULO do gradiente de tabs em graus."""

    GLOW_BUTTON_ENABLED: bool = False
    """ATIVA/DESATIVA o efeito de brilho (QGraphicsDropShadowEffect)
    em botões secundários quando o mouse passa por cima.
    True = botões secundários ganham glow suave no hover."""

    GLOW_TAB_ENABLED: bool = False
    """ATIVA/DESATIVA o efeito de borda brilhante em tabs selecionadas.
    True = tab selecionada ganha brilho extra na borda inferior."""

    GRADIENT_RADIAL_CX: float = 0.5
    """Centro X do gradiente radial (0.0=esquerda, 0.5=centro, 1.0=direita)."""

    GRADIENT_RADIAL_CY: float = 0.5
    """Centro Y do gradiente radial (0.0=topo, 0.5=centro, 1.0=base)."""

    GRADIENT_RADIAL_FX: float = 0.5
    """Ponto focal X do gradiente radial — onde a cor começa a irradiar."""

    GRADIENT_RADIAL_FY: float = 0.5
    """Ponto focal Y do gradiente radial."""

    GRADIENT_RADIAL_RADIUS: float = 0.5
    """RAIO do gradiente radial (0.0=apenas centro, 1.0=toda a área)."""

    GRADIENT_CONICAL_CX: float = 0.5
    """Centro X do gradiente cônico (0.0-1.0). Apenas para paintEvent."""

    GRADIENT_CONICAL_CY: float = 0.5
    """Centro Y do gradiente cônico (0.0-1.0). Apenas para paintEvent."""

    GRADIENT_CONICAL_ANGLE: float = 0.0
    """Ângulo inicial do gradiente cônico em graus. Apenas para paintEvent."""

    # ═══════════════════════════════════════════════════════════════════
    # 3. TEXT — Hierarquia de texto
    # ═══════════════════════════════════════════════════════════════════

    TEXT_HIGH: str = ""
    """COR do TEXTO para títulos e labels de alta importância.
    Usado em: header_title (título de seção), texto de tab default."""

    TEXT_MEDIUM: str = ""
    """COR do TEXTO para corpo padrão e texto principal.
    Usado em: labels comuns, parágrafos, itens de menu, células de tabela."""

    TEXT_LOW: str = ""
    """COR do TEXTO para metadados, texto auxiliar e secundário.
    Usado em: subtítulos, itens de menu inativos, texto de header de tabela."""

    TEXT_DISABLED: str = ""
    """COR do TEXTO para widgets desabilitados (baixo contraste).
    Usado em: botões desabilitados, inputs desabilitados, labels inativas."""

    TEXT_ON_ACCENT: str = ""
    """COR do TEXTO que fica SOBRE o fundo ACCENT (botão primário).
    Deve ter alto contraste com ACCENT."""

    TEXT_ON_DANGER: str = ""
    """COR do TEXTO que fica SOBRE o fundo COLOR_DANGER.
    Usado em: botão fechar (title_btn_close), botão danger."""

    # ═══════════════════════════════════════════════════════════════════
    # 4. BORDER — Hierarquia de bordas
    # ═══════════════════════════════════════════════════════════════════

    BORDER_SUBTLE: str = ""
    """BORDA muito sutil para divisores leves.
    Usado em: linhas de separação discretas, bar_border no GridPercentView."""

    BORDER_DEFAULT: str = ""
    """BORDA padrão da maioria dos widgets.
    Usado em: QMenu, QDialog, QGroupBox borda, separador workspace."""

    BORDER_STRONG: str = ""
    """BORDA de destaque — foco, validação, hover forte.
    Usado em: elementos que precisam de borda mais visível."""

    BORDER_ACCENT: str = ""
    """BORDA com cor de acento para hover em elementos interativos.
    Usado em: hover de tabs (borda), hover de itens de menu."""

    DIVIDER: str = ""
    """LINHAS SEPARADORAS (horizontais/verticais) entre seções.
    Usado em: separador de menu, gridline-color de tabela, divisor de toolbar."""

    BORDER_GRADIENT_STOPS: tuple = ()
    """STOPS para borda em GRADIENTE ('efeito foil').
    Tupla de (pos_float, cor_hex). Vazio = desligado (borda sólida)."""

    BORDER_GRADIENT_WIDTH: float = 1.0
    """LARGURA da borda gradiente em pixels."""

    # ═══════════════════════════════════════════════════════════════════
    # 5. SHADOW — Sombras
    # ═══════════════════════════════════════════════════════════════════

    SHADOW_SM: str = ""
    """SOMBRA PEQUENA — string com cor+alpha para QSS.
    Usado em widgets que precisam de sombra sutil via box-shadow CSS."""

    SHADOW_MD: str = ""
    """SOMBRA MÉDIA — string cor+alpha para QSS."""

    SHADOW_LG: str = ""
    """SOMBRA GRANDE — string cor+alpha para QSS."""

    SHADOW_XL: str = ""
    """SOMBRA EXTRA GRANDE — string cor+alpha para QSS."""

    SHADOW_ACCENT: str = ""
    """SOMBRA com COR DE ACENTO para glow em QSS.
    Efeito de brilho ao redor de elementos de acento."""

    GLOW: str = ""
    """BRILHO SUTIL — string cor+alpha para glow em QSS.
    Efeito de iluminação suave ao redor de elementos."""

    GLOW_STRONG: str = ""
    """BRILHO FORTE — string cor+alpha para glow intenso em QSS."""

    SHADOW_BLUR_SM: int = 0
    """DESFOQUE da sombra pequena em pixels para QGraphicsDropShadowEffect."""

    SHADOW_BLUR_MD: int = 0
    """DESFOQUE da sombra média em pixels para QGraphicsDropShadowEffect."""

    SHADOW_BLUR_LG: int = 0
    """DESFOQUE da sombra grande em pixels para QGraphicsDropShadowEffect."""

    SHADOW_BLUR_XL: int = 0
    """DESFOQUE da sombra extra grande em pixels para QGraphicsDropShadowEffect."""

    SHADOW_OFFSET_Y_SM: int = 0
    """DESLOCAMENTO VERTICAL da sombra pequena (px). Positivo = sombra para baixo."""

    SHADOW_OFFSET_Y_MD: int = 0
    """DESLOCAMENTO VERTICAL da sombra média (px)."""

    SHADOW_OFFSET_Y_LG: int = 0
    """DESLOCAMENTO VERTICAL da sombra grande (px)."""

    SHADOW_COLOR_RGB: str = "#000000"
    """COR BASE da sombra sem alfa em formato #RRGGBB.
    Para QGraphicsDropShadowEffect programático."""

    SHADOW_COLOR_ALPHA: int = 0
    """ALFA (opacidade) da sombra (0-255). 0 = invisível."""

    GLOW_BLUR: int = 0
    """DESFOQUE do glow em pixels para QGraphicsDropShadowEffect.
    0 = glow desligado."""

    GLOW_OFFSET_X: int = 0
    """DESLOCAMENTO HORIZONTAL do glow em pixels."""

    GLOW_OFFSET_Y: int = 0
    """DESLOCAMENTO VERTICAL do glow em pixels."""

    GLOW_COLOR_RGB: str = ""
    """COR do glow em #RRGGBB. Vazio = usa ACCENT do tema como fallback."""

    GLOW_ALPHA: int = 0
    """ALFA do glow (0-255). 0 = glow invisível."""

    GLOW_STRONG_BLUR: int = 0
    """DESFOQUE do glow forte em pixels."""

    GLOW_STRONG_ALPHA: int = 0
    """ALFA do glow forte (0-255)."""

    # ═══════════════════════════════════════════════════════════════════
    # 6. RADIUS — Escala global de arredondamento (pixels)
    # ═══════════════════════════════════════════════════════════════════

    RADIUS_XS: int = 0
    """CANTO ARREDONDADO extra pequeno (2px).
    Aplicado em: checkbox, scrollbar handle, spinbox buttons."""

    RADIUS_SM: int = 0
    """CANTO ARREDONDADO pequeno (4px).
    Aplicado em: badges, toolbar buttons, group title."""

    RADIUS_MD: int = 0
    """CANTO ARREDONDADO médio (6px).
    Aplicado em: botões padrão, inputs, menus dropdown."""

    RADIUS_LG: int = 0
    """CANTO ARREDONDADO grande (10px).
    Aplicado em: cards, tabelas, progress bar."""

    RADIUS_XL: int = 0
    """CANTO ARREDONDADO extra grande (16px).
    Aplicado em: diálogos, painéis grandes."""

    RADIUS_FULL: int = 999
    """CANTO ARREDONDADO total (999px) — círculo/pílula.
    Aplicado em: radio button, badges em formato pill."""

    # ═══════════════════════════════════════════════════════════════════
    # 7. SPACE — Escala global de espaçamento (pixels inteiros)
    # ═══════════════════════════════════════════════════════════════════

    SPACE_XXS: int = 0
    """ESPAÇAMENTO micro (2px). Entre elementos muito próximos."""

    SPACE_XS: int = 0
    """ESPAÇAMENTO muito pequeno (4px)."""

    SPACE_SM: int = 0
    """ESPAÇAMENTO pequeno (8px). Ex: entre botões adjacentes."""

    SPACE_MD: int = 0
    """ESPAÇAMENTO médio (12px). Ex: padding interno de cards."""

    SPACE_LG: int = 0
    """ESPAÇAMENTO grande (16px). Ex: entre seções de formulário."""

    SPACE_XL: int = 0
    """ESPAÇAMENTO extra grande (24px). Ex: margem entre seções."""

    SPACE_2XL: int = 0
    """ESPAÇAMENTO de seção (32px). Ex: antes/depois de grupos grandes."""

    SPACE_3XL: int = 0
    """ESPAÇAMENTO de seção grande (48px). Ex: padding de página."""

    # ═══════════════════════════════════════════════════════════════════
    # 8. ICON — Tamanhos de ícone (pixels)
    # ═══════════════════════════════════════════════════════════════════

    ICON_XS: int = 0
    """ÍCONE extra pequeno (12px). Indicadores tiny, bullets, status dots."""

    ICON_SM: int = 0
    """ÍCONE pequeno (16px). Itens de menu, ícones em listas."""

    ICON_MD: int = 0
    """ÍCONE médio (20px). Botão padrão, toolbar."""

    ICON_LG: int = 0
    """ÍCONE grande (24px). Seção, header de grupo, ícone de tab."""

    ICON_XL: int = 0
    """ÍCONE extra grande (32px). Featured, empty state, ícone principal."""

    TOOLBAR_ICON_SIZE: int = 0
    """ÍCONE da TOOLBAR em pixels."""

    # ═══════════════════════════════════════════════════════════════════
    # 9. ANIMATION — Durações de animação (ms) + easing
    # ═══════════════════════════════════════════════════════════════════

    ANIMATION_FAST: int = 0
    """DURAÇÃO de animação RÁPIDA em milissegundos (aprox. 120ms).
    Usado em: hover de botões, micro-interações, feedback de clique."""

    ANIMATION_NORMAL: int = 0
    """DURAÇÃO de animação NORMAL em milissegundos (aprox. 180ms).
    Usado em: transições padrão, fade in/out, mudança de cor."""

    ANIMATION_SLOW: int = 0
    """DURAÇÃO de animação LENTA em milissegundos (aprox. 260ms).
    Usado em: expansão/colapso de painéis, abertura de menus."""

    EASING_STANDARD: str = ""
    """CURVA de easing (aceleração/desaceleração) para animações."""

    # ═══════════════════════════════════════════════════════════════════
    # 10. OPACITY — Níveis de opacidade (0.0 = transparente, 1.0 = opaco)
    # ═══════════════════════════════════════════════════════════════════

    OPACITY_DISABLED: float = 0.0
    """OPACIDADE de widgets desabilitados.
    Ex: 0.35 = botão desabilitado fica 65% transparente."""

    OPACITY_MUTED: float = 0.0
    """OPACIDADE de texto/elementos secundários.
    Ex: 0.60 = metadados e labels secundários."""

    OPACITY_HOVER: float = 0.0
    """OPACIDADE de feedback hover.
    Ex: 0.85 = elemento fica ligeiramente mais opaco no hover."""

    OPACITY_ACTIVE: float = 0.0
    """OPACIDADE de estado ativo/pressionado.
    Ex: 1.0 = totalmente opaco quando ativo."""

    # ═══════════════════════════════════════════════════════════════════
    # 11. LAYOUT — Layout global
    # ═══════════════════════════════════════════════════════════════════

    PAGE_PADDING: int = 0
    """PADDING externo da página em pixels.
    Espaço entre a borda da janela e o conteúdo principal."""

    SECTION_GAP: int = 0
    """ESPAÇAMENTO entre seções da página em pixels.
    Distância vertical entre grupos de conteúdo."""

    GRID_GAP: int = 0
    """GAP (espaçamento entre células) em layouts grid."""

    CONTENT_MAX_WIDTH: int = 0
    """LARGURA MÁXIMA do conteúdo da página em pixels.
    Impede que o conteúdo se estique demais em monitores largos."""

    # ═══════════════════════════════════════════════════════════════════
    # 12. ELEVATION — Níveis de elevação (z-index conceitual)
    # ═══════════════════════════════════════════════════════════════════

    ELEVATION_FLAT: int = 0
    """ELEVAÇÃO flat — z-index 0. Elementos no nível do plano de fundo."""

    ELEVATION_LOW: int = 0
    """ELEVAÇÃO baixa — z-index 1. Elementos ligeiramente acima do fundo."""

    ELEVATION_MEDIUM: int = 0
    """ELEVAÇÃO média — z-index 2. Cards, menus, popups."""

    ELEVATION_HIGH: int = 0
    """ELEVAÇÃO alta — z-index 3. Modais, dialogs, overlays."""

    # ═══════════════════════════════════════════════════════════════════
    # 13. OVERLAY — Sobreposições / Glass effect
    # ═══════════════════════════════════════════════════════════════════

    OVERLAY_BG: str = ""
    """FUNDO de sobreposição (backdrop) de modais e diálogos.
    Cor semi-transparente que cobre a tela atrás de um dialog modal."""

    BACKDROP_BLUR: str = ""
    """DESFOQUE do backdrop (efeito vidro) em CSS.
    Ex: '4px' — desfoque sutil atrás do modal."""

    # ═══════════════════════════════════════════════════════════════════
    # 14. FOCUS_RING — Anel de foco visual
    # ═══════════════════════════════════════════════════════════════════

    FOCUS_RING_COLOR: str = ""
    """COR do anel de foco (indicador visual de teclado).
    Aparece ao redor de inputs e botões quando focados via Tab."""

    FOCUS_RING_WIDTH: str = ""
    """ESPESSURA do anel de foco em CSS."""

    FOCUS_RING_OFFSET: str = ""
    """DISTÂNCIA do anel de foco em relação ao elemento (CSS).
    Valor positivo = anel afastado da borda."""

    # ═══════════════════════════════════════════════════════════════════
    # 15. STATUS — Cores de estado semântico
    # ═══════════════════════════════════════════════════════════════════

    COLOR_SUCCESS: str = ""
    """VERDE — indica operação bem-sucedida.
    Usado em: badge success (badge verde), feedback positivo."""

    COLOR_SUCCESS_HOVER: str = ""
    """VERDE claro — hover do success."""

    COLOR_SUCCESS_DIM: str = ""
    """VERDE escuro — versão escurecida do success."""

    COLOR_WARNING: str = ""
    """AMARELO/LARANJA — indica atenção ou warning.
    Usado em: badge running (em execução), badge canceled."""

    COLOR_WARNING_HOVER: str = ""
    """LARANJA claro — hover do warning."""

    COLOR_WARNING_DIM: str = ""
    """LARANJA escuro — versão escurecida do warning."""

    COLOR_DANGER: str = ""
    """VERMELHO — indica erro, perigo, ação destrutiva.
    Usado em: badge error, botão danger, botão fechar (close)."""

    COLOR_DANGER_HOVER: str = ""
    """VERMELHO claro — hover do danger."""

    COLOR_DANGER_DIM: str = ""
    """VERMELHO escuro — versão escurecida do danger. Fundo de botão danger."""

    COLOR_INFO: str = ""
    """AZUL — indica informação.
    Usado em: badge info, dicas, notificações informativas."""

    COLOR_INFO_HOVER: str = ""
    """AZUL claro — hover do info."""

    COLOR_INFO_DIM: str = ""
    """AZUL escuro — versão escurecida do info."""

    # ═══════════════════════════════════════════════════════════════════
    # 16. FONT — Tipografia
    # ═══════════════════════════════════════════════════════════════════

    FONT_FAMILY_DEFAULT: str = ""
    """FAMÍLIA de fonte PADRÃO para toda a interface.
    Lista de fallback separada por vírgulas."""

    FONT_FAMILY_MONO: str = ""
    """FAMÍLIA de fonte MONOESPAÇADA (código, logs, números)."""

    FONT_FAMILY_DISPLAY: str = ""
    """FAMÍLIA de fonte DISPLAY/SERIF para títulos editoriais.
    Vazio = usa FONT_FAMILY_DEFAULT como fallback."""

    FONT_LETTER_SPACING_DISPLAY: int = 0
    """ESPAÇAMENTO entre letras (letter-spacing) em pixels para fonte display.
    Aplica-se via QFont.setLetterSpacing. 0 = sem espaço extra."""

    FONT_SIZE_TITLE: int = 0
    """TAMANHO da fonte de título em pixels.
    Usado em: header_title (título principal da seção)."""

    FONT_SIZE_BIG: int = 0
    """TAMANHO da fonte GRANDE em pixels.
    Usado em: about_title, textos de destaque."""

    FONT_SIZE_NORMAL: int = 0
    """TAMANHO da fonte NORMAL em pixels.
    Usado em: corpo de texto, botões primários, labels."""

    FONT_SIZE_SMALL: int = 0
    """TAMANHO da fonte PEQUENA em pixels.
    Usado em: botões secundários, header de tabela, menu items, badges."""

    FONT_SIZE_TINY: int = 0
    """TAMANHO da fonte MUITO PEQUENA em pixels.
    Usado em: tool selector, copyright, window title, badges."""

    FONT_WEIGHT_NORMAL: int = 400
    """PESO da fonte NORMAL (400 — regular)."""

    FONT_WEIGHT_BOLD: int = 600
    """PESO da fonte BOLD (600 — semi-bold/negrito médio)."""

    FONT_WEIGHT_EXTRABOLD: int = 700
    """PESO da fonte EXTRA BOLD (700 — bold)."""

    FONT_WEIGHT_HEAVY: int = 800
    """PESO da fonte HEAVY (800 — extra bold, maior peso)."""

    # ═══════════════════════════════════════════════════════════════════
    # 17. DIMENSIONS — Alturas e tamanhos de widgets
    # ═══════════════════════════════════════════════════════════════════

    INPUT_HEIGHT: int = 0
    """ALTURA de campos de input (QLineEdit) em pixels.
    Controla a altura visual de todos os inputs de texto."""

    BUTTON_HEIGHT: int = 0
    """ALTURA de botões padrão (QPushButton) em pixels."""

    BUTTON_HEIGHT_PRIMARY: int = 0
    """ALTURA de botões primários em pixels."""

    ITEM_HEIGHT: int = 0
    """ALTURA de itens de lista em pixels.
    Controla a altura de cada linha em QListWidget, QComboBox dropdown."""

    CHECKBOX_SIZE: int = 0
    """LARGURA/ALTURA do checkbox (quadrado) em pixels."""

    RADIO_SIZE: int = 0
    """LARGURA/ALTURA do radio button (círculo) em pixels."""

    SCROLLBAR_WIDTH: int = 0
    """LARGURA da scrollbar vertical em pixels."""

    SCROLLBAR_MIN_HEIGHT: int = 0
    """ALTURA MÍNIMA do pegador (handle) da scrollbar em pixels."""

    TAB_HEIGHT: int = 0
    """ALTURA das abas (tabs) em pixels."""

    TAB_CLOSE_BUTTON_SIZE: int = 0
    """TAMANHO (largura=altura) do botão fechar (X) da tab em pixels."""

    CLOSE_BUTTON_BORDER_RADIUS: int = 0
    """AREDONDAMENTO do botão fechar na tab em pixels."""

    PROGRESS_BAR_HEIGHT: int = 0
    """ALTURA da barra de progresso (QProgressBar) em pixels."""

    TITLE_BTN_HEIGHT: int = 0
    """ALTURA dos botões de janela (minimizar, maximizar, fechar) em pixels."""

    TITLE_BTN_WIDTH: int = 0
    """LARGURA dos botões de janela em pixels."""

    TITLE_BTN_FONT_SIZE: int = 0
    """TAMANHO da fonte (ícone) dos botões de janela em pixels."""

    TOOLBAR_BTN_SIZE: int = 0
    """TAMANHO (largura=altura) do botão da toolbar em pixels."""

    TOOLBAR_BTN_HOVER_GROW: int = 0
    """PIXELS EXTRAS que o botão da toolbar cresce no hover.
    Simula animação de crescimento ao passar o mouse."""

    GROUP_MARGIN_TOP: int = 0
    """MARGEM SUPERIOR do QGroupBox em pixels.
    Espaço reservado para o título do groupbox."""

    SPLITTER_HANDLE_WIDTH: int = 0
    """LARGURA do pegador do QSplitter em pixels.
    Barra que o usuário arrasta para redimensionar painéis."""

    # ═══════════════════════════════════════════════════════════════════
    # 18. SPECIFICS — Tokens específicos de implementação
    # ═══════════════════════════════════════════════════════════════════

    # ── Border Radius específicos ──

    BORDER_RADIUS_CARD: int = 0
    """AREDONDAMENTO de CARDS."""

    BORDER_RADIUS_BUTTON: int = 0
    """AREDONDAMENTO de BOTÕES."""

    BORDER_RADIUS_INPUT: int = 0
    """AREDONDAMENTO de INPUTS."""

    BORDER_RADIUS_CHECKBOX: int = 0
    """AREDONDAMENTO do CHECKBOX."""

    BORDER_RADIUS_RADIO: int = 0
    """AREDONDAMENTO do RADIO BUTTON. Usar 0 ou RADIUS_FULL."""

    BORDER_RADIUS_BADGE: int = 0
    """AREDONDAMENTO de BADGES."""

    BORDER_RADIUS_PROGRESS: int = 0
    """AREDONDAMENTO da PROGRESS BAR."""

    BORDER_RADIUS_TABLE: int = 0
    """AREDONDAMENTO de TABELAS."""

    BORDER_RADIUS_TITLE_BTN: int = 0
    """AREDONDAMENTO dos botões da title bar."""

    BORDER_RADIUS_TOOLBAR_BTN: int = 0
    """AREDONDAMENTO dos botões da toolbar."""

    BORDER_RADIUS_GHOST: int = 0
    """AREDONDAMENTO do botão GHOST."""

    BORDER_RADIUS_TOOL_SELECTOR: int = 0
    """AREDONDAMENTO do seletor de tool."""

    BORDER_RADIUS_SCROLLBAR: int = 0
    """AREDONDAMENTO da SCROLLBAR."""

    BORDER_RADIUS_SPINBOX_BTN: int = 0
    """AREDONDAMENTO dos botões do SPINBOX."""

    BORDER_RADIUS_TAB_CLOSE: int = 0
    """AREDONDAMENTO do botão fechar tab."""

    BORDER_RADIUS_MENU: int = 0
    """AREDONDAMENTO do MENU DROPDOWN."""

    BORDER_RADIUS_MENU_ITEM: int = 0
    """AREDONDAMENTO dos ITENS DE MENU."""

    BORDER_RADIUS_GROUP_TITLE: int = 0
    """AREDONDAMENTO do TÍTULO DO GROUPBOX."""

    BORDER_RADIUS_DIALOG: int = 0
    """AREDONDAMENTO de DIÁLOGOS."""

    MENUBAR_ITEM_BORDER_RADIUS: int = 0
    """AREDONDAMENTO dos itens da MENUBAR."""

    @property
    def BORDER_RADIUS_COMBO_POPUP(self) -> int:
        """Alias de compatibilidade → COMBOBOX_POPUP_BORDER_RADIUS (border-radius do popup combobox)."""
        return self.COMBOBOX_POPUP_BORDER_RADIUS

    # ── Checkbox ──

    CHECKBOX_BORDER_WIDTH: int = 0
    """LARGURA da BORDA do quadrado do checkbox em pixels."""

    CHECKBOX_SPACING: int = 0
    """ESPAÇAMENTO entre o checkbox e o texto ao lado em pixels."""

    # ── Badge ──

    BADGE_PADDING_V: str = ""
    """PADDING VERTICAL interno do badge em CSS.
    Espaço acima/abaixo do texto dentro do badge."""

    BADGE_PADDING_H: str = ""
    """PADDING HORIZONTAL interno do badge em CSS.
    Espaço à esquerda/direita do texto dentro do badge."""

    BADGE_LETTER_SPACING: str = ""
    """ESPAÇAMENTO entre letras (letter-spacing) do texto do badge em CSS."""

    BADGE_OUTLINE_ENABLED: bool = False
    """Se True, badges usam estilo outline (borda + fundo translúcido).
    Se False, usam estilo preenchido (fundo sólido)."""

    BADGE_OUTLINE_BORDER_WIDTH: int = 1
    """ESPESSURA da borda do badge outline em pixels."""

    BADGE_OUTLINE_BG_ALPHA: int = 0
    """ALFA do fundo translúcido do badge outline (0-255).
    0 = completamente transparente, 255 = sólido."""

    # ── Button ──

    BUTTON_PADDING_V: str = ""
    """PADDING VERTICAL de botão padrão em CSS."""

    BUTTON_PADDING_H: str = ""
    """PADDING HORIZONTAL de botão padrão em CSS."""

    BUTTON_PADDING_V_SMALL: str = ""
    """PADDING VERTICAL de botão pequeno em CSS."""

    BUTTON_PADDING_H_SMALL: str = ""
    """PADDING HORIZONTAL de botão pequeno em CSS."""

    BUTTON_PADDING_V_PRIMARY: str = ""
    """PADDING VERTICAL de botão primário em CSS."""

    BUTTON_PADDING_H_PRIMARY: str = ""
    """PADDING HORIZONTAL de botão primário em CSS."""

    BUTTON_LETTER_SPACING_NORMAL: str = ""
    """LETTER-SPACING do texto de botão normal em CSS."""

    BUTTON_LETTER_SPACING_PRIMARY: str = ""
    """LETTER-SPACING do texto de botão primário em CSS."""

    # ── Toolbar ──

    TOOLBAR_BTN_PADDING_V: str = ""
    """PADDING VERTICAL do botão da toolbar em CSS."""

    TOOLBAR_BTN_PADDING_H: str = ""
    """PADDING HORIZONTAL do botão da toolbar em CSS."""

    # ── Tool Selector ──

    TOOL_SELECTOR_PADDING_V: str = ""
    """PADDING VERTICAL do seletor de tool (ferramenta ativa) em CSS."""

    TOOL_SELECTOR_PADDING_H: str = ""
    """PADDING HORIZONTAL do seletor de tool em CSS."""

    TOOL_SELECTOR_LETTER_SPACING: str = ""
    """LETTER-SPACING do texto do seletor de tool em CSS."""

    # ── Input ──

    INPUT_PADDING_V: str = ""
    """PADDING VERTICAL de campos de input em CSS."""

    INPUT_PADDING_H: str = ""
    """PADDING HORIZONTAL de campos de input em CSS."""

    # ── SpinBox ──

    SPINBOX_PADDING: str = ""
    """PADDING do spinbox (valor + setas) em CSS."""

    SPINBOX_BTN_WIDTH: int = 0
    """LARGURA dos botões de seta do spinbox em pixels."""

    SPINBOX_BTN_MARGIN: str = ""
    """MARGEM dos botões de seta do spinbox em CSS."""

    # ── ComboBox ──

    COMBOBOX_PADDING: str = ""
    """PADDING do combobox em CSS."""

    COMBOBOX_MIN_WIDTH: int = 0
    """LARGURA MÍNIMA do combobox em pixels."""

    COMBOBOX_DROPDOWN_WIDTH: int = 0
    """LARGURA do botão de dropdown (seta) do combobox em pixels."""

    COMBOBOX_ARROW_SIZE: str = ""
    """TAMANHO da seta do combobox (triângulo) em CSS."""

    COMBOBOX_POPUP_BORDER_RADIUS: int = 0
    """AREDONDAMENTO do POPUP do combobox (lista suspensa) em pixels."""

    # ── TextEdit / TextBrowser ──

    TEXT_EDIT_PADDING: str = ""
    """PADDING do editor de texto (QTextEdit) em CSS."""

    TEXT_EDIT_FONT_SIZE: int = 0
    """TAMANHO da fonte no editor de texto em pixels."""

    # ── GroupBox ──

    GROUP_TITLE_LEFT: int = 0
    """DESLOCAMENTO HORIZONTAL do título do groupbox em pixels.
    Move o título para a esquerda/direita em relação à borda."""

    GROUP_TITLE_TOP: int = 0
    """DESLOCAMENTO VERTICAL do título do groupbox em pixels.
    Valor negativo = sobe o título para alinhar com a borda superior."""

    GROUP_TITLE_PADDING: str = ""
    """PADDING do título do groupbox em CSS."""

    GROUP_TITLE_BORDER_RADIUS: int = 0
    """AREDONDAMENTO do título do groupbox em pixels."""

    GROUP_TITLE_LETTER_SPACING: str = ""
    """LETTER-SPACING do título do groupbox em CSS."""

    # ── Letter Spacing ──

    LETTER_SPACING_TITLE: str = ""
    """LETTER-SPACING de títulos grandes (header_title) em CSS."""

    LETTER_SPACING_BADGE: str = ""
    """LETTER-SPACING de badges em CSS."""

    LETTER_SPACING_GROUP: str = ""
    """LETTER-SPACING de título de groupbox em CSS."""

    LETTER_SPACING_BUTTON: str = ""
    """LETTER-SPACING de botão normal em CSS."""

    LETTER_SPACING_BUTTON_PRIMARY: str = ""
    """LETTER-SPACING de botão primário em CSS."""

    LETTER_SPACING_HEADER: str = ""
    """LETTER-SPACING de cabeçalho de tabela em CSS."""

    LETTER_SPACING_TOOL_SELECTOR: str = ""
    """LETTER-SPACING de seletor de tool em CSS."""

    LETTER_SPACING_WINDOW_TITLE: str = ""
    """LETTER-SPACING de título da janela em CSS."""

    # ── Window Title ──

    WINDOW_TITLE_FONT_SIZE: int = 0
    """TAMANHO da fonte do título da janela (na title bar) em pixels."""

    WINDOW_TITLE_LETTER_SPACING: str = ""
    """LETTER-SPACING do título da janela em CSS."""

    # ── Title Bar ──

    TITLE_BAR_BORDER_WIDTH: str = ""
    """LARGURA da borda inferior da title bar em CSS."""

    TITLE_BAR_BORDER_COLOR: str = ""
    """COR da borda inferior da title bar.
    Vazio = usa SURFACE_2 (BG_PANEL) como fallback."""

    # ── Card ──

    CARD_PADDING_V: int = 0
    """PADDING VERTICAL de cards em pixels."""

    CARD_PADDING_H: int = 0
    """PADDING HORIZONTAL de cards em pixels."""

    # ── Splitter ──

    SPLITTER_HANDLE_WIDTH_H: int = 0
    """LARGURA do pegador do SPLITTER HORIZONTAL em pixels."""

    SPLITTER_HANDLE_WIDTH_V: int = 0
    """LARGURA do pegador do SPLITTER VERTICAL em pixels."""

    # ── Menu ──

    MENU_PADDING: str = ""
    """PADDING interno do menu dropdown em CSS."""

    MENU_MARGIN_V: str = ""
    """MARGEM vertical do menu dropdown (espaço externo) em CSS."""

    MENU_ITEM_PADDING: str = ""
    """PADDING de cada item do menu em CSS."""

    MENU_SEPARATOR_HEIGHT: str = ""
    """ALTURA da linha separadora do menu em CSS."""

    MENU_SEPARATOR_MARGIN: str = ""
    """MARGEM da linha separadora do menu em CSS."""

    # ── Table / Header ──

    HEADER_FONT_SIZE: int = 0
    """TAMANHO da fonte do cabeçalho de tabela em pixels."""

    HEADER_LETTER_SPACING: str = ""
    """LETTER-SPACING do cabeçalho de tabela em CSS."""

    TABLE_ITEM_PADDING: str = ""
    """PADDING das células da tabela em CSS."""

    HEADER_PADDING: str = ""
    """PADDING das células do cabeçalho em CSS."""

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