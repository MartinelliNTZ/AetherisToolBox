# -*- coding: utf-8 -*-
"""
AppStyles — Estilos específicos da aplicação
=============================================
Herda de BaseStyle e adiciona estilos de botões, badges, logs e menu.
Usa o tema atual via ThemeManager.
Zero valores hardcoded — tudo centralizado no tema via tokens semânticos.
"""

from __future__ import annotations

from typing import Optional

from resources.styles.BaseStyle import BaseStyle
from resources.styles.ThemeManager import ct


class AppStyles(BaseStyle):
    """
    Estilos específicos: botões (secondary, primary, danger, ghost, remove),
    badges de status, logs coloridos e menus.
    Todo estilo busca valores do tema atual via tokens semânticos.
    """

    # ────────────────────────────────────────────────────────────────────
    # BOTÕES
    # ────────────────────────────────────────────────────────────────────

    @classmethod
    def btn_secondary_style(cls) -> str:
        """Botao secundario — gradiente suave, hover com glow."""
        t = ct.theme
        grad = cls._gradient(*t.GRADIENT_BUTTON)
        return (
            f"QPushButton {{"
            f"  background: {grad};"
            f"  color: {t.ACCENT_TEXT};"
            f"  border: none;"
            f"  border-radius: {t.BORDER_RADIUS_BUTTON}px;"
            f"  padding: {t.BUTTON_PADDING_V} {t.BUTTON_PADDING_H};"
            f"  font-weight: {t.FONT_WEIGHT_BOLD};"
            f"  font-size: {t.FONT_SIZE_SMALL}px;"
            f"}}"
            f"QPushButton:hover {{"
            f"  background: {t.SURFACE_4};"
            f"  color: {t.ACCENT_BRIGHT};"
            f"}}"
            f"QPushButton:pressed {{"
            f"  background: {t.SURFACE_2};"
            f"}}"
        )

    @classmethod
    def btn_primary_style(cls) -> str:
        """Botao primario — gradiente."""
        t = ct.theme
        return (
            f"QPushButton {{"
            f"  background: qlineargradient(x1:0,y1:0,x2:1,y2:0,"
            f"    stop:0 {t.ACCENT_GRADIENT[0]}, stop:1 {t.ACCENT_GRADIENT[1]});"
            f"  color: {t.SURFACE_0};"
            f"  border: none;"
            f"  border-radius: {t.BORDER_RADIUS_BUTTON}px;"
            f"  padding: {t.BUTTON_PADDING_V_PRIMARY} {t.BUTTON_PADDING_H_PRIMARY};"
            f"  font-weight: {t.FONT_WEIGHT_HEAVY};"
            f"  font-size: {t.FONT_SIZE_NORMAL}px;"
            f"  letter-spacing: {t.BUTTON_LETTER_SPACING_PRIMARY};"
            f"}}"
            f"QPushButton:hover {{"
            f"  background: qlineargradient(x1:0,y1:0,x2:1,y2:0,"
            f"    stop:0 {t.ACCENT_HOVER}, stop:1 {t.ACCENT});"
            f"}}"
            f"QPushButton:pressed {{"
            f"  background: {t.ACCENT_ACTIVE};"
            f"}}"
            f"QPushButton:disabled {{"
            f"  background-color: {t.SURFACE_3};"
            f"  color: {t.TEXT_DISABLED};"
            f"}}"
        )

    @classmethod
    def btn_danger_style(cls) -> str:
        """Botao danger — vermelho escuro, sem borda."""
        t = ct.theme
        return (
            f"QPushButton {{"
            f"  background-color: {t.COLOR_DANGER_DIM};"
            f"  color: {t.TEXT_ON_DANGER};"
            f"  border: none;"
            f"  border-radius: {t.BORDER_RADIUS_BUTTON}px;"
            f"  padding: {t.BUTTON_PADDING_V} {t.BUTTON_PADDING_H};"
            f"  font-weight: {t.FONT_WEIGHT_EXTRABOLD};"
            f"  font-size: {t.FONT_SIZE_SMALL}px;"
            f"  letter-spacing: {t.BUTTON_LETTER_SPACING_NORMAL};"
            f"}}"
            f"QPushButton:hover {{"
            f"  background-color: {t.COLOR_DANGER};"
            f"}}"
            f"QPushButton:pressed {{"
            f"  background-color: {t.COLOR_DANGER_DIM};"
            f"}}"
            f"QPushButton:disabled {{"
            f"  background-color: {t.SURFACE_3};"
            f"  color: {t.TEXT_DISABLED};"
            f"}}"
        )

    @classmethod
    def btn_ghost_style(cls) -> str:
        """Botao ghost — invisível, aparece no hover."""
        t = ct.theme
        return (
            f"QPushButton {{"
            f"  background-color: transparent;"
            f"  color: {t.ACCENT_TEXT};"
            f"  border: none;"
            f"  border-radius: {t.BORDER_RADIUS_GHOST}px;"
            f"  padding: {t.BUTTON_PADDING_V_SMALL} {t.BUTTON_PADDING_H_SMALL};"
            f"  font-weight: {t.FONT_WEIGHT_BOLD};"
            f"  font-size: {t.FONT_SIZE_SMALL}px;"
            f"}}"
            f"QPushButton:hover {{"
            f"  background-color: {t.SURFACE_3};"
            f"}}"
            f"QPushButton:pressed {{"
            f"  background-color: {t.SURFACE_2};"
            f"}}"
        )

    @classmethod
    def btn_remove_style(cls) -> str:
        """Botao remover — preto arredondado, fonte branca, hover vermelho."""
        t = ct.theme
        return (
            f"QPushButton {{"
            f"  background-color: {t.SURFACE_3};"
            f"  color: {t.TEXT_ON_DANGER};"
            f"  border: none;"
            f"  border-radius: {t.BORDER_RADIUS_TABLE}px;"
            f"  padding: {t.BUTTON_PADDING_V_SMALL} {t.BUTTON_PADDING_H_SMALL};"
            f"  font-weight: {t.FONT_WEIGHT_BOLD};"
            f"  font-size: {t.FONT_SIZE_TINY}px;"
            f"}}"
            f"QPushButton:hover {{"
            f"  background-color: {t.COLOR_DANGER};"
            f"}}"
            f"QPushButton:pressed {{"
            f"  background-color: {t.COLOR_DANGER_DIM};"
            f"}}"
        )

    # ────────────────────────────────────────────────────────────────────
    # MENU BAR
    # ────────────────────────────────────────────────────────────────────

    @classmethod
    def menu_bar_style(cls) -> str:
        """Estilo da barra de menus."""
        t = ct.theme
        return (
            f"QMenuBar#app_menu_bar {{"
            f"  background-color: {t.TITLE_BAR};"
            f"  border: none;"
            f"  border-bottom: 1px solid {t.BORDER_DEFAULT};"
            f"  padding: 0;"
            f"  font-size: {t.FONT_SIZE_SMALL}px;"
            f"  color: {t.TEXT_LOW};"
            f"}}"
            f"QMenuBar::item {{"
            f"  background-color: transparent;"
            f"  color: {t.TEXT_LOW};"
            f"  padding: 2px 10px;"
            f"  margin: 0;"
            f"}}"
            f"QMenuBar::item:hover {{"
            f"  background-color: {t.ACCENT};"
            f"  color: {t.SURFACE_0};"
            f"  border-radius: {t.MENUBAR_ITEM_BORDER_RADIUS};"
            f"  font-weight: {t.FONT_WEIGHT_EXTRABOLD};"
            f"}}"
            f"QMenuBar::item:selected {{"
            f"  background-color: {t.ACCENT};"
            f"  color: {t.SURFACE_0};"
            f"  border-radius: {t.MENUBAR_ITEM_BORDER_RADIUS};"
            f"  font-weight: {t.FONT_WEIGHT_EXTRABOLD};"
            f"}}"
            f"QMenuBar::item:pressed {{"
            f"  background-color: {t.ACCENT_ACTIVE};"
            f"  color: {t.SURFACE_0};"
            f"  border-radius: {t.MENUBAR_ITEM_BORDER_RADIUS};"
            f"}}"
        )

    @classmethod
    def menu_dropdown_style(cls) -> str:
        """Estilo do QMenu dropdown."""
        t = ct.theme
        return (
            f"QMenu {{"
            f"  background-color: {t.SURFACE_0};"
            f"  border: 1px solid {t.BORDER_DEFAULT};"
            f"  border-radius: {t.BORDER_RADIUS_MENU}px;"
            f"  padding: {t.MENU_PADDING};"
            f"  margin: {t.MENU_MARGIN_V};"
            f"}}"
            f"QMenu::item {{"
            f"  background-color: transparent;"
            f"  color: {t.TEXT_MEDIUM};"
            f"  padding: {t.MENU_ITEM_PADDING};"
            f"  border-radius: {t.BORDER_RADIUS_MENU_ITEM}px;"
            f"  font-size: {t.FONT_SIZE_SMALL}px;"
            f"  border-left: 1px solid transparent;"
            f"}}"
            f"QMenu::item:hover {{"
            f"  background-color: {t.ACCENT};"
            f"  color: {t.SURFACE_0};"
            f"  border-left: 1px solid {t.ACCENT_HOVER};"
            f"  font-weight: {t.FONT_WEIGHT_EXTRABOLD};"
            f"}}"
            f"QMenu::item:selected {{"
            f"  background-color: {t.ACCENT_HOVER};"
            f"  color: {t.SURFACE_0};"
            f"  border-left: 1px solid {t.ACCENT};"
            f"  font-weight: {t.FONT_WEIGHT_EXTRABOLD};"
            f"}}"
            f"QMenu::item:disabled {{"
            f"  background-color: transparent;"
            f"  color: {t.TEXT_DISABLED};"
            f"  border-left: 1px solid transparent;"
            f"}}"
            f"QMenu::separator {{"
            f"  height: {t.MENU_SEPARATOR_HEIGHT};"
            f"  background: {t.DIVIDER};"
            f"  margin: {t.MENU_SEPARATOR_MARGIN};"
            f"}}"
        )

    # ────────────────────────────────────────────────────────────────────
    # BADGES
    # ────────────────────────────────────────────────────────────────────

    @classmethod
    def badge_style(cls, bg_color: str, text_color: Optional[str] = None) -> str:
        t = ct.theme
        tc = text_color or t.SURFACE_0
        return (
            f"QLabel {{"
            f"  background-color: {bg_color};"
            f"  color: {tc};"
            f"  border-radius: {t.BORDER_RADIUS_BADGE}px;"
            f"  padding: {t.BADGE_PADDING_V} {t.BADGE_PADDING_H};"
            f"  font-weight: {t.FONT_WEIGHT_HEAVY};"
            f"  font-size: {t.FONT_SIZE_TINY}px;"
            f"  letter-spacing: {t.BADGE_LETTER_SPACING};"
            f"}}"
        )

    @classmethod
    def badge_success(cls) -> str:
        return cls.badge_style(ct.theme.COLOR_SUCCESS)

    @classmethod
    def badge_running(cls) -> str:
        return cls.badge_style(ct.theme.COLOR_WARNING)

    @classmethod
    def badge_error(cls) -> str:
        return cls.badge_style(ct.theme.COLOR_DANGER)

    @classmethod
    def badge_canceled(cls) -> str:
        return cls.badge_style(ct.theme.COLOR_WARNING)

    @classmethod
    def badge_info(cls) -> str:
        return cls.badge_style(ct.theme.COLOR_INFO)

    # ────────────────────────────────────────────────────────────────────
    # DIALOG — Estilo base para QDialog
    # ────────────────────────────────────────────────────────────────────

    @classmethod
    def dialog_stylesheet(cls) -> str:
        """QSS genérico para QDialog. Nenhum hardcoded."""
        t = ct.theme
        return (
            f"QDialog {{"
            f"  background-color: {t.SURFACE_1};"
            f"  border: 1px solid {t.BORDER_DEFAULT};"
            f"  border-radius: {t.BORDER_RADIUS_DIALOG}px;"
            f"}}"
        )

    # ────────────────────────────────────────────────────────────────────
    # DIALOG CONTENT — borda fina para o content widget do BaseDialog
    # ────────────────────────────────────────────────────────────────────

    @classmethod
    def dialog_content_border_style(cls) -> str:
        """Borda sutil para o QWidget de conteúdo dentro do BaseDialog."""
        t = ct.theme
        return (
            f"QWidget#dialog_content {{"
            f"  border: 1px solid {t.BORDER_DEFAULT};"
            f"  border-radius: {t.RADIUS_SM}px;"
            f"}}"
        )

    # ────────────────────────────────────────────────────────────────────
    # ABOUT DIALOG — QSS completo para AboutDialog
    # ────────────────────────────────────────────────────────────────────

    @classmethod
    def about_dialog_stylesheet(cls) -> str:
        """QSS completo para o AboutDialog. Nenhum hardcoded."""
        t = ct.theme
        return cls.dialog_stylesheet() + (
            f"QLabel#about_title {{"
            f"  color: {t.ACCENT_TEXT};"
            f"  font-size: {t.FONT_SIZE_BIG}px;"
            f"  font-weight: {t.FONT_WEIGHT_EXTRABOLD};"
            f"  letter-spacing: {t.LETTER_SPACING_TITLE};"
            f"}}"
            f"QLabel#about_version {{"
            f"  color: {t.TEXT_LOW};"
            f"  font-size: {t.FONT_SIZE_SMALL}px;"
            f"}}"
            f"QLabel#about_desc {{"
            f"  color: {t.TEXT_MEDIUM};"
            f"  font-size: {t.FONT_SIZE_SMALL}px;"
            f"  line-height: 1.4;"
            f"}}"
            f"QLabel#about_copyright {{"
            f"  color: {t.TEXT_DISABLED};"
            f"  font-size: {t.FONT_SIZE_TINY}px;"
            f"}}"
        )

    # ────────────────────────────────────────────────────────────────────
    # HUD LOADER — cores para o HudCircularRingsLoader
    # ────────────────────────────────────────────────────────────────────

    @classmethod
    def hud_accent_color(cls) -> str:
        """Cor de acento para o HUD loader (usado em paintEvent)."""
        return ct.theme.ACCENT_TEXT

    # ────────────────────────────────────────────────────────────────────
    # VERTICAL TAB — cores para VerticalTab (paintEvent custom)
    # ────────────────────────────────────────────────────────────────────

    @classmethod
    def vertical_tab_colors(cls) -> dict[str, str]:
        """Retorna cores para pintura manual do VerticalTab.
        Usa tokens semânticos — nenhum alias antigo.
        Inclui gradientes top-left → bottom-right para backgrounds."""
        t = ct.theme
        return {
            "bg_selected":  t.ACCENT,
            "fg_selected":  t.SURFACE_0,
            "border_selected": t.ACCENT_DIM,
            "indicator":    t.ACCENT_HOVER,
            "bg_hovered":   t.SURFACE_3,
            "fg_hovered":   t.TEXT_MEDIUM,
            "border_hovered": t.BORDER_ACCENT,
            "bg_default":   t.SURFACE_0,
            "fg_default":   t.TEXT_LOW,
            "border_default": t.BORDER_DEFAULT,
            # Gradientes (start, end) para background
            "gradient_default_start": t.GRADIENT_TAB[0],
            "gradient_default_end":   t.GRADIENT_TAB[1],
            "gradient_hovered_start": t.GRADIENT_BUTTON[0],
            "gradient_hovered_end":   t.GRADIENT_BUTTON[1],
            "gradient_selected_start": "",
            "gradient_selected_end":   "",
        }

    # ────────────────────────────────────────────────────────────────────
    # TAB COLORS — cores centralizadas para QUALQUER tab (vertical/horizontal)
    #              Tanto VerticalTab quanto HorizontalTab usam o mesmo
    #              dicionário, garantindo consistência.
    #              Uso: P = AppStyles.tab_common_colors()
    #              painter.fillRect(..., QColor(P["bg_selected"]))
    # ────────────────────────────────────────────────────────────────────

    _TAB_COLORS_CACHE: dict = {}

    @classmethod
    def tab_common_colors(cls) -> dict[str, str]:
        """Retorna cores padronizadas para tabs (vertical e horizontal).
        Todas as tabs usam o mesmo schema de cores:
          - selected: fundo GOLD, texto BG_DEEPEST, border GOLD_DIM, indicator GOLD_HOVER
          - hovered:  fundo GOLD, texto BG_DEEPEST, border BORDER_HOVER
          - default:  fundo BG_DEEPEST, texto TEXT_BRIGHT, border BORDER
        Cacheado por performance."""
        t = ct.theme
        cache_key = ct.current_key
        if cls._TAB_COLORS_CACHE.get("_cache_key") != cache_key:
            cls._TAB_COLORS_CACHE = {
                "_cache_key": cache_key,
                "bg_selected":    t.GOLD,
                "fg_selected":    t.BG_DEEPEST,
                "border_selected": t.GOLD_DIM,
                "indicator":       t.GOLD_HOVER,
                "bg_hovered":     t.GOLD,
                "fg_hovered":     t.BG_DEEPEST,
                "border_hovered": t.BORDER_HOVER,
                "bg_default":     t.BG_DEEPEST,
                "fg_default":     t.TEXT_BRIGHT,
                "border_default": t.BORDER,
            }
        return cls._TAB_COLORS_CACHE

    # ────────────────────────────────────────────────────────────────────
    # THEME COLORS — cores avulsas para widgets que usam paintEvent
    #                (VerticalTab, WorkspaceTabBar, etc.)
    #                Uso: from AppStyles import theme_colors
    #                colors = AppStyles.theme_colors()
    #                painter.fillRect(..., QColor(colors["BG_DEEPEST"]))
    # ────────────────────────────────────────────────────────────────────

    _THEME_COLORS_CACHE: dict = {}

    @classmethod
    def theme_colors(cls) -> dict[str, str]:
        """Retorna um dicionário com TODAS as cores do tema atual.
        Cacheado por performance (paintEvent é chamado a 60 fps).
        Usa current_key como chave de cache (string estável)."""
        t = ct.theme
        cache_key = ct.current_key
        if cls._THEME_COLORS_CACHE.get("_cache_key") != cache_key:
            cls._THEME_COLORS_CACHE = {
                "_cache_key": cache_key,
                # Aliases de compatibilidade para widgets legados
                "BG_DEEPEST": t.BG_DEEPEST,
                "BG_DARK": t.BG_DARK,
                "BG_PANEL": t.BG_PANEL,
                "BG_CARD": t.BG_CARD,
                "BG_ELEVATED": t.BG_ELEVATED,
                "BG_SURFACE": t.BG_SURFACE,
                "TITLE_BAR_BG": t.TITLE_BAR_BG,
                "BORDER": t.BORDER,
                "BORDER_HOVER": t.BORDER_HOVER,
                "TEXT_BRIGHT": t.TEXT_BRIGHT,
                "TEXT_PRIMARY": t.TEXT_PRIMARY,
                "TEXT_SECONDARY": t.TEXT_SECONDARY,
                "TEXT_MUTED": t.TEXT_MUTED,
                "TEXT_GOLD": t.TEXT_GOLD,
                "GOLD": t.GOLD,
                "GOLD_HOVER": t.GOLD_HOVER,
                "GOLD_DIM": t.GOLD_DIM,
                "GOLD_LIGHT": t.GOLD_LIGHT,
                "GOLD_GRADIENT": t.GOLD_GRADIENT,
                # Tokens semânticos
                "ACCENT": t.ACCENT,
                "ACCENT_TEXT": t.ACCENT_TEXT,
                "ACCENT_BRIGHT": t.ACCENT_BRIGHT,
                "SURFACE_0": t.SURFACE_0,
                "SURFACE_1": t.SURFACE_1,
                "SURFACE_2": t.SURFACE_2,
                "SURFACE_3": t.SURFACE_3,
                "SURFACE_4": t.SURFACE_4,
                "SURFACE_5": t.SURFACE_5,
                "COLOR_SUCCESS": t.COLOR_SUCCESS,
                "COLOR_WARNING": t.COLOR_WARNING,
                "COLOR_DANGER": t.COLOR_DANGER,
                "COLOR_INFO": t.COLOR_INFO,
            }
        return cls._THEME_COLORS_CACHE

    # ────────────────────────────────────────────────────────────────────
    # LOG HTML
    # ────────────────────────────────────────────────────────────────────

    @classmethod
    def log_html(cls, text: str, timestamp: str,
                 color: str, ts_color: str, weight: str = "400") -> str:
        mono = ct.theme.FONT_FAMILY_MONO
        return (
            f"<span style='color:{ts_color};"
            f"font-family:{mono};"
            f"font-size:11px;font-weight:500;'>[{timestamp}]</span> "
            f"<span style='color:{color};"
            f"font-family:{mono};"
            f"font-size:12px;font-weight:{weight};'>{text}</span>"
        )

    @classmethod
    def log_link_html(cls, text: str, url: str) -> str:
        mono = ct.theme.FONT_FAMILY_MONO
        return (
            f"<span style='color:{ct.theme.TEXT_LOW};"
            f"font-family:{mono};font-size:12px;'>"
            f"{text}: <a href='{url}' style='color:{ct.theme.ACCENT};"
            f"text-decoration:none;'>abrir</a></span>"
        )

    @classmethod
    def log_section_html(cls, text: str) -> str:
        mono = ct.theme.FONT_FAMILY_MONO
        return (
            f"<span style='color:{ct.theme.ACCENT};"
            f"font-family:{mono};"
            f"font-size:12px;font-weight:700;'>{text}</span>"
        )

    # ────────────────────────────────────────────────────────────────────
    # COLLAPSIBLE — estilo para CollapsibleParams
    # ────────────────────────────────────────────────────────────────────

    @classmethod
    def collapsible_header_height(cls) -> str:
        """Altura do header do CollapsibleParams."""
        return str(ct.theme.INPUT_HEIGHT+2)

    @classmethod
    def collapsible_header_style(cls) -> str:
        """Estilo do header clicável do CollapsibleParams."""
        t = ct.theme
        return (
            f"QLabel#collapsible_header {{"
            f"  background-color: {t.SURFACE_3};"
            f"  color: {t.ACCENT_TEXT};"
            f"  padding: 6px 12px;"
            f"  border-radius: {t.RADIUS_SM}px;"
            f"  font-weight: {t.FONT_WEIGHT_BOLD};"
            f"  font-size: {t.FONT_SIZE_SMALL}px;"
            f"}}"
            f"QLabel#collapsible_header:hover {{"
            f"  background-color: {t.SURFACE_4};"
            f"}}"
        )

    @classmethod
    def collapsible_content_style(cls) -> str:
        """Estilo do container de conteúdo do CollapsibleParams."""
        t = ct.theme
        return (
            f"QWidget#collapsible_content {{"
            f"  background-color: {t.SURFACE_1};"
            f"  border: 1px solid {t.BORDER};"
            f"  border-top: none;"
            f"  border-radius: 0px 0px {t.RADIUS_SM}px {t.RADIUS_SM}px;"
            f"}}"
        )

    # ────────────────────────────────────────────────────────────────────
    # RECENT PROJECTS — estilos para RecentProjectsMenu
    # ────────────────────────────────────────────────────────────────────

    @classmethod
    def recent_project_name_style(cls, active: bool = True) -> str:
        """
        Estilo para o label do nome do projeto (RecentProjectsMenu).

        Args:
            active: Se True, nome em ACCENT_TEXT negrito. Se False,
                    nome em TEXT_MUTED itálico (projeto não encontrado).
        """
        t = ct.theme
        color = t.ACCENT_TEXT if active else t.TEXT_MUTED
        italic = "font-style: italic;" if not active else ""
        return (
            f"QLabel {{"
            f"  color: {color};"
            f"  font-weight: bold;"
            f"  {italic}"
            f"}}"
        )

    @classmethod
    def recent_project_sub_style(cls, active: bool = True) -> str:
        """
        Estilo para os labels de path e data (RecentProjectsMenu).

        Args:
            active: Se True, cor TEXT_SECONDARY. Se False,
                    mesma cor (mas o item está desabilitado visualmente).
        """
        t = ct.theme
        color = t.TEXT_SECONDARY
        return (
            f"QLabel {{"
            f"  color: {color};"
            f"}}"
        )

    @classmethod
    def recent_project_hover_style(cls) -> str:
        """
        Cor de fundo hover para o item do RecentProjectsMenu.
        Usa ACCENT com baixa opacidade simulada via SURFACE_3.
        """
        t = ct.theme
        return t.SURFACE_3

    @classmethod
    def recent_project_hover_name_style(cls) -> str:
        """
        Estilo do nome do projeto no hover (ACCENT_BRIGHT).
        """
        t = ct.theme
        return (
            f"QLabel {{"
            f"  color: {t.ACCENT_BRIGHT};"
            f"  font-weight: bold;"
            f"}}"
        )

    @classmethod
    def recent_project_hover_sub_style(cls) -> str:
        """
        Estilo do path/data no hover (TEXT_MEDIUM).
        """
        t = ct.theme
        return (
            f"QLabel {{"
            f"  color: {t.TEXT_MEDIUM};"
            f"}}"
        )

    # ────────────────────────────────────────────────────────────────────
    # TOOLBAR — tokens centralizados de tamanhos e estilos
    # Todos os métodos usam ct.theme, zero hardcoded.
    # ────────────────────────────────────────────────────────────────────

    @classmethod
    def toolbar_icon_size(cls) -> int:
        """Tamanho do ícone na toolbar (px)."""
        return ct.theme.TOOLBAR_ICON_SIZE

    @classmethod
    def toolbar_btn_size(cls) -> int:
        """Tamanho do botão na toolbar (px)."""
        return ct.theme.TOOLBAR_BTN_SIZE

    @classmethod
    def toolbar_btn_border_radius(cls) -> int:
        """Border-radius do botão da toolbar (px). Usa BORDER_RADIUS_TOOLBAR_BTN do tema."""
        return ct.theme.BORDER_RADIUS_TOOLBAR_BTN

    @classmethod
    def toolbar_btn_hover_grow(cls) -> int:
        """Pixels extras no hover para animação grow."""
        return ct.theme.TOOLBAR_BTN_HOVER_GROW

    @classmethod
    def toolbar_btn_style(cls) -> str:
        """
        QSS completo para botão da toolbar (QToolButton).
        Zero hardcoded — border-radius, cores de hover/pressed vêm do tema.
        A animação de hover grow é feita via AnimationManager, não via QSS.
        """
        t = ct.theme
        return (
            f"QToolButton {{"
            f"  background-color: transparent;"
            f"  border: none;"
            f"  border-radius: {t.BORDER_RADIUS_TOOLBAR_BTN}px;"
            f"}}"
            f"QToolButton:hover {{"
            f"  background-color: {t.SURFACE_4};"
            f"}}"
            f"QToolButton:pressed {{"
            f"  background-color: {t.SURFACE_2};"
            f"}}"
        )
