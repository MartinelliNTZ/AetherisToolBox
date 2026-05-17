# -*- coding: utf-8 -*-
"""
ZeroGrausTheme — Tema Ice Glass / Frozen Crystal
================================================
Visual inspirado em gelo translúcido, superfícies cristalinas,
tons azulados e brilho frio elegante.

Objetivo:
- Sensação de tecnologia premium
- Aparência limpa e sofisticada
- Contraste excelente
- Azul-gelo luminoso que chama atenção sem cansar

Estilo:
- Deep Arctic Glass
- Frosted Panels
- Crystal Cyan Accent
"""

from __future__ import annotations

from resources.styles.BaseTheme import BaseTheme


class ZeroGrausTheme(BaseTheme):
    """
    Tema 0Graus — visual cristalino baseado em gelo e vidro.
    """

    # ═══════════════════════════════════════════════════════════════════
    # CORES — FUNDOS
    # ═══════════════════════════════════════════════════════════════════

    # Fundo mais profundo
    BG_DEEPEST = "#02060A"

    # Fundo geral
    BG_DARK = "#071018"

    # Painéis
    BG_PANEL = "#0C1824"

    # Cards
    BG_CARD = "#122131"

    # Elementos elevados
    BG_ELEVATED = "#173046"

    # Superfícies ativas
    BG_SURFACE = "#1C3E59"

    # Barra de título
    TITLE_BAR_BG = "#040B12"

    # ═══════════════════════════════════════════════════════════════════
    # SOMBRAS E GLOWS
    # ═══════════════════════════════════════════════════════════════════

    SHADOW = "#000000"
    SHADOW_DEEP = "#000000"

    # Glow sutil azul-gelo
    GLOW = "#7FE8FF18"
    GLOW_STRONG = "#7FE8FF40"

    # ═══════════════════════════════════════════════════════════════════
    # BORDAS
    # ═══════════════════════════════════════════════════════════════════

    BORDER = "#2A475D"
    BORDER_HOVER = "#8EEFFF"
    DIVIDER = "#142737"

    # ═══════════════════════════════════════════════════════════════════
    # TEXTO
    # ═══════════════════════════════════════════════════════════════════

    TEXT_BRIGHT = "#F7FDFF"
    TEXT_PRIMARY = "#DDF6FF"
    TEXT_SECONDARY = "#9CC7D8"
    TEXT_MUTED = "#5C7D90"

    # Texto em destaque
    TEXT_GOLD = "#8EEFFF"
    TEXT_GOLD_BRIGHT = "#CFFBFF"

    # ═══════════════════════════════════════════════════════════════════
    # ACENTO PRINCIPAL — CRYSTAL CYAN
    # ═══════════════════════════════════════════════════════════════════

    GOLD = "#7FE8FF"
    GOLD_HOVER = "#A6F2FF"
    GOLD_ACTIVE = "#56D8F5"
    GOLD_DIM = "#4CA7BD"
    GOLD_LIGHT = "#D9FBFF"
    GOLD_GRADIENT = ("#A6F2FF", "#56D8F5")

    # ═══════════════════════════════════════════════════════════════════
    # STATUS
    # ═══════════════════════════════════════════════════════════════════

    SUCCESS = "#2EE59D"
    SUCCESS_HOVER = "#5EF0B5"
    SUCCESS_DIM = "#1CA772"

    WARNING = "#FFC857"
    WARNING_HOVER = "#FFD87E"
    WARNING_DIM = "#D89B1D"

    DANGER = "#FF6B7A"
    DANGER_HOVER = "#FF8C98"
    DANGER_DIM = "#D94A58"

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
    # DIMENSÕES
    # ═══════════════════════════════════════════════════════════════════

    INPUT_HEIGHT = 0
    BUTTON_HEIGHT = 0
    BUTTON_HEIGHT_PRIMARY = 0
    ITEM_HEIGHT = 0
    CHECKBOX_SIZE = 16
    RADIO_SIZE = 16
    SCROLLBAR_WIDTH = 6
    TAB_HEIGHT = 0
    PROGRESS_BAR_HEIGHT = 18
    TITLE_BTN_HEIGHT = 22
    TITLE_BTN_WIDTH = 28

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

    BORDER_RADIUS_CARD = 12
    BORDER_RADIUS_BUTTON = 8
    BORDER_RADIUS_INPUT = 8
    BORDER_RADIUS_CHECKBOX = 4
    BORDER_RADIUS_RADIO = 8
    BORDER_RADIUS_BADGE = 5
    BORDER_RADIUS_PROGRESS = 6
    BORDER_RADIUS_TABLE = 10
    BORDER_RADIUS_TITLE_BTN = 4
    BORDER_RADIUS_TOOLBAR_BTN = 6
    BORDER_RADIUS_TOOL_SELECTOR = 8

    # ═══════════════════════════════════════════════════════════════════
    # CHECKBOX
    # ═══════════════════════════════════════════════════════════════════

    CHECKBOX_BORDER_WIDTH = 0
    CHECKBOX_SPACING = 8

    # ═══════════════════════════════════════════════════════════════════
    # BOTÕES — PADDING
    # ═══════════════════════════════════════════════════════════════════

    BUTTON_PADDING_V = "6px"
    BUTTON_PADDING_H = "14px"

    BUTTON_PADDING_V_SMALL = "4px"
    BUTTON_PADDING_H_SMALL = "12px"

    BUTTON_PADDING_V_PRIMARY = "6px"
    BUTTON_PADDING_H_PRIMARY = "20px"

    # ═══════════════════════════════════════════════════════════════════
    # INPUTS — PADDING
    # ═══════════════════════════════════════════════════════════════════

    INPUT_PADDING_V = "4px"
    INPUT_PADDING_H = "8px"

    # ═══════════════════════════════════════════════════════════════════
    # TABELAS
    # ═══════════════════════════════════════════════════════════════════

    TABLE_ITEM_PADDING = "3px 6px"
    HEADER_PADDING = "4px 6px"