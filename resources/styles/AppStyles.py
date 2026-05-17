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
        """Botao secundario — sem borda, fundo elevado, hover com glow."""
        t = ct.theme
        return (
            f"QPushButton {{"
            f"  background-color: {t.SURFACE_3};"
            f"  color: {t.ACCENT_TEXT};"
            f"  border: none;"
            f"  border-radius: {t.BORDER_RADIUS_BUTTON}px;"
            f"  padding: {t.BUTTON_PADDING_V} {t.BUTTON_PADDING_H};"
            f"  font-weight: {t.FONT_WEIGHT_BOLD};"
            f"  font-size: {t.FONT_SIZE_SMALL}px;"
            f"}}"
            f"QPushButton:hover {{"
            f"  background-color: {t.SURFACE_4};"
            f"  color: {t.ACCENT_BRIGHT};"
            f"}}"
            f"QPushButton:pressed {{"
            f"  background-color: {t.SURFACE_2};"
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
            f"  color: white;"
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
            f"  color: white;"
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