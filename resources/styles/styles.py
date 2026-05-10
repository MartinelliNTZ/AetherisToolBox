# -*- coding: utf-8 -*-
"""
Sistema Centralizado de Estilos — Aetheris Classifier v6
=========================================================
Design: Minimalista Dark Charcoal + Gold com profundidade via sombras.

Conceito:
- Sem bordas visíveis nos cards/containers
- Profundidade criada com cores de fundo em cascata (mais escuro atrás)
- Sombras sutis via gradientes e sobreposições
- Tipografia levemente ampliada (+1px) para melhor legibilidade
- Acento ouro para interatividade
"""

from __future__ import annotations
from typing import Optional


class Palette:
    """
    Paleta com 6 níveis de profundidade.
    BG_DEEPEST (fundo mais escuro) → BG_SURFACE (superfície mais clara)
    """

    # ── Fundos (profundidade: 0 = mais fundo, 5 = mais alto) ───────────
    BG_DEEPEST = "#08080A"      # Nível 0: fundo absoluto
    BG_DARK = "#0C0C0F"      # Nível 1: fundo padrão
    BG_PANEL = "#121216"      # Nível 2: painéis base
    BG_CARD = "#18181D"      # Nível 3: cards / groupbox
    BG_ELEVATED = "#1E1E24"      # Nível 4: elementos elevados
    BG_SURFACE = "#24242B"      # Nível 5: superfície (hover, focus)
    TITLE_BAR_BG = "#0A0A0D"      # Barra de título

    # ── Sombras (simulam box-shadow via gradientes) ────────────────────
    SHADOW = "#040405"      # Sombra escura sutil
    SHADOW_DEEP = "#000000"      # Sombra profunda
    GLOW = "#C9A84C15"    # Brilho dourado fraco (~8%)
    GLOW_STRONG = "#C9A84C25"    # Brilho dourado médio (~15%)

    # ── Bordas (mínimas, quase invisíveis) ─────────────────────────────
    BORDER = "#2A2A30"     # Borda sutil (quase imperceptível)
    BORDER_HOVER = "#C9A84C"     # Borda hover dourada
    DIVIDER = "#1A1A20"     # Separador / gridline

    # ── Texto ───────────────────────────────────────────────────────────
    TEXT_BRIGHT = "#F0F0F0"     # Títulos / destaque
    TEXT_PRIMARY = "#DCDCDC"     # Corpo
    TEXT_SECONDARY = "#888890"     # Subtítulo / secundário
    TEXT_MUTED = "#585860"     # Placeholder / desabilitado
    TEXT_GOLD = "#C9A84C"     # Dourado
    TEXT_GOLD_BRIGHT = "#E0C878"   # Dourado hover

    # ── Acento Ouro ─────────────────────────────────────────────────────
    GOLD = "#C9A84C"
    GOLD_HOVER = "#D4B85A"
    GOLD_ACTIVE = "#B8983E"
    GOLD_DIM = "#8A7A3A"
    GOLD_LIGHT = "#E8D08A"
    GOLD_GRADIENT = ("#C9A84C", "#B8963A")

    # ── Status ──────────────────────────────────────────────────────────
    SUCCESS = "#43A047"
    SUCCESS_HOVER = "#66BB6A"
    SUCCESS_DIM = "#2E7D32"
    WARNING = "#EF9A00"
    WARNING_HOVER = "#FFB74D"
    WARNING_DIM = "#BF6E00"
    DANGER = "#D32F2F"
    DANGER_HOVER = "#E53935"
    DANGER_DIM = "#A02020"


class AppStyles:
    """Estilos QSS centralizados."""

    P = Palette

    @classmethod
    def global_stylesheet(cls) -> str:
        p = cls.P
        return f"""
        QMainWindow, QWidget {{
            background-color: {p.BG_DARK};
            color: {p.TEXT_PRIMARY};
            font-family: 'Segoe UI', 'Inter', 'Roboto', sans-serif;
            font-size: 13px;
        }}

        QScrollArea {{
            border: none;
            background: transparent;
        }}
        QScrollBar:vertical {{
            background: {p.BG_DARK};
            width: 6px;
            margin: 0;
        }}
        QScrollBar::handle:vertical {{
            background: {p.BG_ELEVATED};
            border-radius: 3px;
            min-height: 28px;
        }}
        QScrollBar::handle:vertical:hover {{
            background: {p.GOLD};
        }}
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
            height: 0;
        }}

        /* ===== GROUP BOX ===== */
        QGroupBox {{
            background-color: {p.BG_CARD};
            border: none;
            border-radius: 10px;
            margin-top: 8px;
            padding: 16px 10px 10px 10px;
            font-weight: 600;
        }}
        QGroupBox::title {{
            subcontrol-origin: padding;
            subcontrol-position: top left;
            left: 4px;
            top: -2px;
            padding: 0 6px;
            color: {p.TEXT_GOLD};
            font-weight: 700;
            font-size: 12px;
            letter-spacing: 0.5px;
            background-color: {p.BG_CARD};
            border-radius: 4px;
        }}

        /* ===== LABEL ===== */
        QLabel {{
            background: transparent;
            color: {p.TEXT_PRIMARY};
        }}
        QLabel#header_title {{
            font-size: 21px;
            font-weight: 700;
            color: {p.TEXT_BRIGHT};
            letter-spacing: 1px;
        }}
        QLabel#header_subtitle {{
            font-size: 12px;
            color: {p.TEXT_SECONDARY};
        }}
        QLabel#section_badge {{
            background-color: {p.GOLD};
            color: {p.BG_DEEPEST};
            border-radius: 4px;
            padding: 3px 12px;
            font-size: 10px;
            font-weight: 800;
            letter-spacing: 0.3px;
        }}

        /* ===== TITLE BAR ===== */
        QWidget#title_bar {{
            background-color: {p.TITLE_BAR_BG};
            border-bottom: 1px solid {p.BG_PANEL};
        }}
        QLabel#window_title {{
            color: {p.TEXT_MUTED};
            font-size: 11px;
            font-weight: 600;
            letter-spacing: 0.3px;
        }}
        QPushButton#title_btn, QPushButton#title_btn_close {{
            background: transparent;
            color: {p.TEXT_MUTED};
            border: none;
            border-radius: 3px;
            min-width: 28px;
            max-width: 28px;
            min-height: 22px;
            max-height: 22px;
            font-size: 11px;
        }}
        QPushButton#title_btn:hover {{
            background-color: {p.BG_CARD};
            color: {p.TEXT_PRIMARY};
        }}
        QPushButton#title_btn_close:hover {{
            background-color: {p.DANGER};
            color: white;
        }}

        /* ===== APPBAR TOOLBAR ===== */
        QWidget#appbar_toolbar {{
            background: transparent;
        }}
        QPushButton#toolbar_btn {{
            background-color: transparent;
            color: {p.TEXT_SECONDARY};
            border: none;
            border-radius: 4px;
            padding: 4px 10px;
            font-size: 11px;
            font-weight: 600;
        }}
        QPushButton#toolbar_btn:hover {{
            background-color: {p.BG_CARD};
            color: {p.TEXT_GOLD};
        }}

        /* ===== SIDE PANEL (Workspace) ===== */
        QWidget#tool_side_panel {{
            background-color: {p.BG_DEEPEST};
        }}
        QPushButton#tool_selector_btn {{
            background-color: transparent;
            color: {p.TEXT_MUTED};
            border: none;
            border-radius: 6px;
            padding: 6px 4px;
            font-size: 10px;
            font-weight: 700;
            letter-spacing: 0.3px;
        }}
        QPushButton#tool_selector_btn:hover {{
            background-color: {p.BG_PANEL};
            color: {p.TEXT_GOLD};
        }}
        QPushButton#tool_selector_btn:checked {{
            background-color: {p.GOLD};
            color: {p.BG_DEEPEST};
        }}

        /* ===== CONSOLE TOOLBAR ===== */
        QWidget#console_toolbar {{
            background-color: {p.BG_PANEL};
            border-bottom: 1px solid {p.DIVIDER};
        }}
        /* ===== WORKSPACE TABS ===== */
        QTabBar#workspace_tabs {{
            background-color: {p.TITLE_BAR_BG};
            border: none;
            padding: 0;
            font-size: 12px;
        }}
        QTabBar::tab {{
            background-color: transparent;
            color: {p.TEXT_SECONDARY};
            border: none;
            padding: 0;
            margin: 0;
            font-weight: 600;
            font-size: 11px;
        }}
        QTabBar::tab:hover {{
            background-color: {p.BG_PANEL};
            color: {p.TEXT_PRIMARY};
        }}
        QTabBar::tab:selected {{
            background-color: {p.BG_DARK};
            color: {p.TEXT_GOLD};
            border-bottom: 2px solid {p.GOLD};
        }}

        /* Close button sempre reserva espaço fixo — sem reflow no hover */
        QTabBar::close-button {{
            image: none;
            width: 16px;
            height: 16px;
            subcontrol-position: right;
            opacity: 0;
        }}
        QTabBar::tab:hover > QTabBar::close-button,
        QTabBar::tab:selected > QTabBar::close-button {{
            opacity: 1;
        }}
        QTabBar::close-button:hover {{
            background-color: {p.DANGER};
            border-radius: 3px;
        }}

        /* ===== WORKSPACE TAB CUSTOM WIDGET ===== */
        /* 
           WorkspaceTab usa paintEvent próprio com cores da Palette e corner-radius 2 8 2 2.
           Background aqui é transparent pois o painting é feito em paintEvent.
        */
        QWidget#workspace_tab {{
            background-color: transparent;
            border: none;
            padding: 0px;
        }}

        /* ===== VERTICAL TAB ===== */
        /* 
           VerticalTab usa paintEvent próprio com cores da Palette e corner-radius 2 2 8 2.
           Background aqui é transparent pois o painting é feito em paintEvent.
        */
        QWidget#vertical_tab {{
            background-color: transparent;
            border: none;
            padding: 0px;
        }}

        /* ===== WORKSPACE SEPARATOR ===== */
        QFrame#workspace_separator {{
            background-color: {p.BORDER};
            border: none;
        }}

        /* ===== SPLITTER ===== */
        QSplitter::handle {{
            background-color: {p.BORDER};
        }}
        QSplitter::handle:hover {{
            background-color: {p.GOLD};
        }}
        QSplitter#workspace_splitter::handle {{
            width: 4px;
        }}

        /* ===== LINE EDIT ===== */
        QLineEdit {{
            background-color: {p.BG_ELEVATED};
            border: none;
            border-radius: 6px;
            padding: 2px;
            color: {p.TEXT_PRIMARY};
            selection-background-color: {p.GOLD};
            selection-color: {p.BG_DEEPEST};
        }}
        QLineEdit:focus {{
            background-color: {p.BG_SURFACE};
        }}
        QLineEdit:disabled {{
            background-color: {p.BG_CARD};
            color: {p.TEXT_MUTED};
        }}

        /* ===== SPIN BOX ===== */
        QSpinBox, QDoubleSpinBox {{
            background-color: {p.BG_ELEVATED};
            border: none;
            border-radius: 6px;
            padding: 3px 8px;
            color: {p.TEXT_PRIMARY};
        }}
        QSpinBox:focus, QDoubleSpinBox:focus {{
            background-color: {p.BG_SURFACE};
        }}
        QSpinBox::up-button, QDoubleSpinBox::up-button,
        QSpinBox::down-button, QDoubleSpinBox::down-button {{
            width: 16px;
            background: {p.BG_CARD};
            border-radius: 2px;
            margin: 1px;
        }}
        QSpinBox::up-button:hover, QDoubleSpinBox::up-button:hover,
        QSpinBox::down-button:hover, QDoubleSpinBox::down-button:hover {{
            background: {p.GOLD};
        }}

        /* ===== COMBO BOX ===== */
        QComboBox {{
            background-color: {p.BG_ELEVATED};
            border: none;
            border-radius: 6px;
            padding: 3px 8px;
            color: {p.TEXT_PRIMARY};
            min-width: 80px;
        }}
        QComboBox:focus {{
            background-color: {p.BG_SURFACE};
        }}
        QComboBox:disabled {{
            background-color: {p.BG_CARD};
            color: {p.TEXT_MUTED};
        }}
        QComboBox::drop-down {{
            subcontrol-origin: padding;
            subcontrol-position: top right;
            width: 22px;
            border-left: 1px solid {p.BG_ELEVATED};
            border-top-right-radius: 6px;
            border-bottom-right-radius: 6px;
        }}
        QComboBox::down-arrow {{
            image: none;
            border-left: 4px solid transparent;
            border-right: 4px solid transparent;
            border-top: 5px solid {p.TEXT_SECONDARY};
        }}
        QComboBox QAbstractItemView {{
            background-color: {p.BG_CARD};
            border: none;
            border-radius: 4px;
            color: {p.TEXT_PRIMARY};
            selection-background-color: {p.GOLD};
            selection-color: {p.BG_DEEPEST};
            outline: none;
        }}

        /* ===== CHECK BOX ===== */
        QCheckBox {{
            spacing: 8px;
            background: transparent;
            color: {p.TEXT_PRIMARY};
        }}
        QCheckBox::indicator {{
            width: 16px;
            height: 16px;
            border-radius: 3px;
            background-color: {p.BG_ELEVATED};
        }}
        QCheckBox::indicator:checked {{
            background-color: {p.GOLD};
        }}
        QCheckBox::indicator:hover {{
            background-color: {p.BG_SURFACE};
        }}

        /* ===== TABLE ===== */
        QTableWidget {{
            background-color: {p.BG_ELEVATED};
            border: none;
            border-radius: 8px;
            gridline-color: {p.DIVIDER};
            color: {p.TEXT_PRIMARY};
        }}
        QTableWidget::item {{
            padding: 3px 6px;
        }}
        QTableWidget::item:selected {{
            background-color: {p.GOLD};
            color: {p.BG_DEEPEST};
        }}
        QHeaderView::section {{
            background-color: {p.BG_CARD};
            color: {p.TEXT_SECONDARY};
            padding: 4px 6px;
            border: none;
            border-bottom: 2px solid {p.GOLD};
            font-weight: 700;
            font-size: 11px;
            letter-spacing: 0.3px;
        }}

        /* ===== TEXT BROWSER / TEXT EDIT ===== */
        QTextBrowser, QTextEdit {{
            background-color: {p.BG_ELEVATED};
            border: none;
            border-radius: 8px;
            color: {p.TEXT_PRIMARY};
            font-family: 'Consolas', 'Courier New', monospace;
            font-size: 12px;
            padding: 8px;
            selection-background-color: {p.GOLD};
            selection-color: {p.BG_DEEPEST};
        }}

        /* ===== PROGRESS BAR ===== */
        QProgressBar {{
            border: none;
            border-radius: 5px;
            background-color: {p.BG_PANEL};
            text-align: center;
            color: {p.TEXT_PRIMARY};
            font-weight: 700;
            font-size: 11px;
            height: 18px;
        }}
        QProgressBar::chunk {{
            border-radius: 5px;
            background: qlineargradient(
                x1:0, y1:0, x2:1, y2:0,
                stop:0 {p.GOLD_GRADIENT[0]},
                stop:1 {p.GOLD_GRADIENT[1]}
            );
        }}
        """

    # ────────────────────────────────────────────────────────────────────
    # BOTÕES
    # ────────────────────────────────────────────────────────────────────

    @classmethod
    def btn_secondary_style(cls) -> str:
        """Botao secundario — sem borda, fundo elevado, hover com glow."""
        p = cls.P
        return (
            f"QPushButton {{"
            f"  background-color: {p.BG_CARD};"
            f"  color: {p.TEXT_GOLD};"
            f"  border: none;"
            f"  border-radius: 6px;"
            f"  padding: 6px 14px;"
            f"  font-weight: 600;"
            f"  font-size: 11px;"
            f"}}"
            f"QPushButton:hover {{"
            f"  background-color: {p.BG_ELEVATED};"
            f"  color: {p.TEXT_GOLD_BRIGHT};"
            f"}}"
            f"QPushButton:pressed {{"
            f"  background-color: {p.BG_PANEL};"
            f"}}"
        )

    @classmethod
    def btn_primary_style(cls) -> str:
        """Botao primario — gradiente ouro, sem borda."""
        p = cls.P
        return (
            f"QPushButton {{"
            f"  background: qlineargradient(x1:0,y1:0,x2:1,y2:0,"
            f"    stop:0 {p.GOLD_GRADIENT[0]}, stop:1 {p.GOLD_GRADIENT[1]});"
            f"  color: {p.BG_DEEPEST};"
            f"  border: none;"
            f"  border-radius: 6px;"
            f"  padding: 6px 20px;"
            f"  font-weight: 800;"
            f"  font-size: 13px;"
            f"  letter-spacing: 0.5px;"
            f"}}"
            f"QPushButton:hover {{"
            f"  background: qlineargradient(x1:0,y1:0,x2:1,y2:0,"
            f"    stop:0 {p.GOLD_HOVER}, stop:1 {p.GOLD});"
            f"}}"
            f"QPushButton:pressed {{"
            f"  background: {p.GOLD_ACTIVE};"
            f"}}"
            f"QPushButton:disabled {{"
            f"  background-color: {p.BG_CARD};"
            f"  color: {p.TEXT_MUTED};"
            f"}}"
        )

    @classmethod
    def btn_danger_style(cls) -> str:
        """Botao danger — vermelho escuro, sem borda."""
        p = cls.P
        return (
            f"QPushButton {{"
            f"  background-color: {p.DANGER_DIM};"
            f"  color: white;"
            f"  border: none;"
            f"  border-radius: 6px;"
            f"  padding: 6px 14px;"
            f"  font-weight: 700;"
            f"  font-size: 11px;"
            f"  letter-spacing: 0.3px;"
            f"}}"
            f"QPushButton:hover {{"
            f"  background-color: {p.DANGER};"
            f"}}"
            f"QPushButton:pressed {{"
            f"  background-color: {p.DANGER_DIM};"
            f"}}"
            f"QPushButton:disabled {{"
            f"  background-color: {p.BG_CARD};"
            f"  color: {p.TEXT_MUTED};"
            f"}}"
        )

    @classmethod
    def btn_ghost_style(cls) -> str:
        """Botao ghost — invisível, aparece no hover."""
        p = cls.P
        return (
            f"QPushButton {{"
            f"  background-color: transparent;"
            f"  color: {p.TEXT_GOLD};"
            f"  border: none;"
            f"  border-radius: 5px;"
            f"  padding: 4px 12px;"
            f"  font-weight: 600;"
            f"  font-size: 11px;"
            f"}}"
            f"QPushButton:hover {{"
            f"  background-color: {p.BG_CARD};"
            f"}}"
            f"QPushButton:pressed {{"
            f"  background-color: {p.BG_PANEL};"
            f"}}"
        )

    @classmethod
    def btn_remove_style(cls) -> str:
        """Botao remover — preto arredondado, fonte branca, hover vermelho."""
        p = cls.P
        return (
            f"QPushButton {{"
            f"  background-color: {p.BG_CARD};"
            f"  color: white;"
            f"  border: none;"
            f"  border-radius: 8px;"
            f"  padding: 4px 12px;"
            f"  font-weight: 600;"
            f"  font-size: 10px;"
            f"}}"
            f"QPushButton:hover {{"
            f"  background-color: {p.DANGER};"
            f"}}"
            f"QPushButton:pressed {{"
            f"  background-color: {p.DANGER_DIM};"
            f"}}"
        )

    # ────────────────────────────────────────────────────────────────────
    # BADGES
    # ────────────────────────────────────────────────────────────────────

    @classmethod
    def badge_style(cls, bg_color: str, text_color: Optional[str] = None) -> str:
        tc = text_color or cls.P.BG_DEEPEST
        return (
            f"QLabel {{"
            f"  background-color: {bg_color};"
            f"  color: {tc};"
            f"  border-radius: 4px;"
            f"  padding: 3px 12px;"
            f"  font-weight: 800;"
            f"  font-size: 10px;"
            f"  letter-spacing: 0.3px;"
            f"}}"
        )

    @classmethod
    def badge_success(cls) -> str:
        return cls.badge_style(cls.P.SUCCESS)

    @classmethod
    def badge_running(cls) -> str:
        return cls.badge_style(cls.P.WARNING)

    @classmethod
    def badge_error(cls) -> str:
        return cls.badge_style(cls.P.DANGER)

    @classmethod
    def badge_canceled(cls) -> str:
        return cls.badge_style(cls.P.WARNING)

    # ────────────────────────────────────────────────────────────────────
    # LOG HTML
    # ────────────────────────────────────────────────────────────────────

    @classmethod
    def log_html(cls, text: str, timestamp: str,
                 color: str, ts_color: str, weight: str = "400") -> str:
        return (
            f"<span style='color:{ts_color};"
            f"font-family:Consolas,\"Courier New\",monospace;"
            f"font-size:11px;font-weight:500;'>[{timestamp}]</span> "
            f"<span style='color:{color};"
            f"font-family:Consolas,\"Courier New\",monospace;"
            f"font-size:12px;font-weight:{weight};'>{text}</span>"
        )

    @classmethod
    def log_link_html(cls, text: str, url: str) -> str:
        return (
            f"<span style='color:{cls.P.TEXT_SECONDARY};"
            f"font-family:Consolas,\"Courier New\",monospace;font-size:12px;'>"
            f"{text}: <a href='{url}' style='color:{cls.P.GOLD};"
            f"text-decoration:none;'>abrir</a></span>"
        )

    @classmethod
    def log_section_html(cls, text: str) -> str:
        return (
            f"<span style='color:{cls.P.GOLD};"
            f"font-family:Consolas,\"Courier New\",monospace;"
            f"font-size:12px;font-weight:700;'>{text}</span>"
        )


# ═══════════════════════════════════════════════════════════════════════════
# COMPATIBILIDADE RETROATIVA — DarkCharcoalStyle (legado)
# Mantido para nao quebrar imports de launcher.py, hud_loader.py, etc.
# Mapeia constantes antigas para as novas do Palette.
# ═══════════════════════════════════════════════════════════════════════════

class DarkCharcoalStyle:
    """Classe de compatibilidade legada. Usar AppStyles ou Palette diretamente."""

    DARK_BG = Palette.BG_DARK
    PANEL_BG = Palette.BG_PANEL
    CARD_BG = Palette.BG_CARD
    INPUT_BG = Palette.BG_ELEVATED
    BORDER = Palette.BORDER
    TEXT_PRIMARY = Palette.TEXT_PRIMARY
    TEXT_SECONDARY = Palette.TEXT_SECONDARY
    ACCENT_GOLD = Palette.GOLD
    ACCENT_HOVER = Palette.GOLD_HOVER
    SUCCESS = Palette.SUCCESS
    WARNING = Palette.WARNING
    DANGER = Palette.DANGER
    INFO = "#5B9BD5"

    @classmethod
    def stylesheet(cls) -> str:
        """Retorna o stylesheet global (delega para AppStyles)."""
        return AppStyles.global_stylesheet()
