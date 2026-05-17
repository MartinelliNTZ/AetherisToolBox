# -*- coding: utf-8 -*-
"""
AppStyles — Estilos específicos da aplicação
=============================================
Herda de BaseStyle e adiciona estilos de botões, badges, logs e menu.
Usa o tema atual via ThemeManager.
"""

from __future__ import annotations

from typing import Optional

from resources.styles.BaseStyle import BaseStyle
from resources.styles.ThemeManager import ct


class AppStyles(BaseStyle):
    """
    Estilos específicos: botões (secondary, primary, danger, ghost, remove),
    badges de status, logs coloridos e menus.
    Todo estilo busca valores do tema atual.
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
            f"  background-color: {t.BG_CARD};"
            f"  color: {t.TEXT_GOLD};"
            f"  border: none;"
            f"  border-radius: {t.BORDER_RADIUS_BUTTON}px;"
            f"  padding: {t.BUTTON_PADDING_V} {t.BUTTON_PADDING_H};"
            f"  font-weight: {t.FONT_WEIGHT_BOLD};"
            f"  font-size: {t.FONT_SIZE_SMALL}px;"
            f"}}"
            f"QPushButton:hover {{"
            f"  background-color: {t.BG_ELEVATED};"
            f"  color: {t.TEXT_GOLD_BRIGHT};"
            f"}}"
            f"QPushButton:pressed {{"
            f"  background-color: {t.BG_PANEL};"
            f"}}"
        )

    @classmethod
    def btn_primary_style(cls) -> str:
        """Botao primario — gradiente ouro, sem borda."""
        t = ct.theme
        return (
            f"QPushButton {{"
            f"  background: qlineargradient(x1:0,y1:0,x2:1,y2:0,"
            f"    stop:0 {t.GOLD_GRADIENT[0]}, stop:1 {t.GOLD_GRADIENT[1]});"
            f"  color: {t.BG_DEEPEST};"
            f"  border: none;"
            f"  border-radius: {t.BORDER_RADIUS_BUTTON}px;"
            f"  padding: {t.BUTTON_PADDING_V_PRIMARY} {t.BUTTON_PADDING_H_PRIMARY};"
            f"  font-weight: {t.FONT_WEIGHT_HEAVY};"
            f"  font-size: {t.FONT_SIZE_NORMAL}px;"
            f"  letter-spacing: 0.5px;"
            f"}}"
            f"QPushButton:hover {{"
            f"  background: qlineargradient(x1:0,y1:0,x2:1,y2:0,"
            f"    stop:0 {t.GOLD_HOVER}, stop:1 {t.GOLD});"
            f"}}"
            f"QPushButton:pressed {{"
            f"  background: {t.GOLD_ACTIVE};"
            f"}}"
            f"QPushButton:disabled {{"
            f"  background-color: {t.BG_CARD};"
            f"  color: {t.TEXT_MUTED};"
            f"}}"
        )

    @classmethod
    def btn_danger_style(cls) -> str:
        """Botao danger — vermelho escuro, sem borda."""
        t = ct.theme
        return (
            f"QPushButton {{"
            f"  background-color: {t.DANGER_DIM};"
            f"  color: white;"
            f"  border: none;"
            f"  border-radius: {t.BORDER_RADIUS_BUTTON}px;"
            f"  padding: {t.BUTTON_PADDING_V} {t.BUTTON_PADDING_H};"
            f"  font-weight: {t.FONT_WEIGHT_EXTRABOLD};"
            f"  font-size: {t.FONT_SIZE_SMALL}px;"
            f"  letter-spacing: 0.3px;"
            f"}}"
            f"QPushButton:hover {{"
            f"  background-color: {t.DANGER};"
            f"}}"
            f"QPushButton:pressed {{"
            f"  background-color: {t.DANGER_DIM};"
            f"}}"
            f"QPushButton:disabled {{"
            f"  background-color: {t.BG_CARD};"
            f"  color: {t.TEXT_MUTED};"
            f"}}"
        )

    @classmethod
    def btn_ghost_style(cls) -> str:
        """Botao ghost — invisível, aparece no hover."""
        t = ct.theme
        return (
            f"QPushButton {{"
            f"  background-color: transparent;"
            f"  color: {t.TEXT_GOLD};"
            f"  border: none;"
            f"  border-radius: 5px;"
            f"  padding: {t.BUTTON_PADDING_V_SMALL} {t.BUTTON_PADDING_H_SMALL};"
            f"  font-weight: {t.FONT_WEIGHT_BOLD};"
            f"  font-size: {t.FONT_SIZE_SMALL}px;"
            f"}}"
            f"QPushButton:hover {{"
            f"  background-color: {t.BG_CARD};"
            f"}}"
            f"QPushButton:pressed {{"
            f"  background-color: {t.BG_PANEL};"
            f"}}"
        )

    @classmethod
    def btn_remove_style(cls) -> str:
        """Botao remover — preto arredondado, fonte branca, hover vermelho."""
        t = ct.theme
        return (
            f"QPushButton {{"
            f"  background-color: {t.BG_CARD};"
            f"  color: white;"
            f"  border: none;"
            f"  border-radius: {t.BORDER_RADIUS_TABLE}px;"
            f"  padding: {t.BUTTON_PADDING_V_SMALL} {t.BUTTON_PADDING_H_SMALL};"
            f"  font-weight: {t.FONT_WEIGHT_BOLD};"
            f"  font-size: {t.FONT_SIZE_TINY}px;"
            f"}}"
            f"QPushButton:hover {{"
            f"  background-color: {t.DANGER};"
            f"}}"
            f"QPushButton:pressed {{"
            f"  background-color: {t.DANGER_DIM};"
            f"}}"
        )

    # ────────────────────────────────────────────────────────────────────
    # MENU BAR
    # ────────────────────────────────────────────────────────────────────

    @classmethod
    def menu_bar_style(cls) -> str:
        """Estilo da barra de menus (Arquivo > Sair | Ajuda > Sobre)."""
        t = ct.theme
        return (
            f"QMenuBar#app_menu_bar {{"
            f"  background-color: {t.TITLE_BAR_BG};"
            f"  border: none;"
            f"  border-bottom: 1px solid {t.BORDER};"
            f"  padding: 0;"
            f"  font-size: {t.FONT_SIZE_SMALL}px;"
            f"  color: {t.TEXT_SECONDARY};"
            f"}}"
            f"QMenuBar::item {{"
            f"  background-color: transparent;"
            f"  color: {t.TEXT_SECONDARY};"
            f"  padding: 2px 10px;"
            f"  margin: 0;"
            f"}}"
            f"QMenuBar::item:hover {{"
            f"  background-color: {t.GOLD};"
            f"  color: {t.BG_DEEPEST};"
            f"  border-radius: 1px 1px 8px 1px;"
            f"  font-weight: {t.FONT_WEIGHT_EXTRABOLD};"
            f"}}"
            f"QMenuBar::item:selected {{"
            f"  background-color: {t.GOLD};"
            f"  color: {t.BG_DEEPEST};"
            f"  border-radius: 1px 1px 8px 1px;"
            f"  font-weight: {t.FONT_WEIGHT_EXTRABOLD};"
            f"}}"
            f"QMenuBar::item:pressed {{"
            f"  background-color: {t.GOLD_ACTIVE};"
            f"  color: {t.BG_DEEPEST};"
            f"  border-radius: 1px 1px 8px 1px;"
            f"}}"
        )

    @classmethod
    def menu_dropdown_style(cls) -> str:
        """Estilo do QMenu dropdown (itens do menu suspenso)."""
        t = ct.theme
        return (
            f"QMenu {{"
            f"  background-color: {t.BG_DEEPEST};"
            f"  border: 1px solid {t.BORDER};"
            f"  border-radius: 6px;"
            f"  padding: 2px;"
            f"  margin: 1px 0;"
            f"}}"
            f"QMenu::item {{"
            f"  background-color: transparent;"
            f"  color: {t.TEXT_PRIMARY};"
            f"  padding: 4px 16px 4px 8px;"
            f"  border-radius: 3px;"
            f"  font-size: {t.FONT_SIZE_SMALL}px;"
            f"  border-left: 1px solid transparent;"
            f"}}"
            f"QMenu::item:hover {{"
            f"  background-color: {t.GOLD};"
            f"  color: {t.BG_DEEPEST};"
            f"  border-left: 1px solid {t.GOLD_HOVER};"
            f"  font-weight: {t.FONT_WEIGHT_EXTRABOLD};"
            f"}}"
            f"QMenu::item:selected {{"
            f"  background-color: {t.GOLD_HOVER};"
            f"  color: {t.BG_DEEPEST};"
            f"  border-left: 1px solid {t.GOLD};"
            f"  font-weight: {t.FONT_WEIGHT_EXTRABOLD};"
            f"}}"
            f"QMenu::item:disabled {{"
            f"  background-color: transparent;"
            f"  color: {t.TEXT_MUTED};"
            f"  border-left: 1px solid transparent;"
            f"}}"
            f"QMenu::separator {{"
            f"  height: 1px;"
            f"  background: {t.DIVIDER};"
            f"  margin: 2px 6px;"
            f"}}"
        )

    # ────────────────────────────────────────────────────────────────────
    # BADGES
    # ────────────────────────────────────────────────────────────────────

    @classmethod
    def badge_style(cls, bg_color: str, text_color: Optional[str] = None) -> str:
        tc = text_color or ct.theme.BG_DEEPEST
        t = ct.theme
        return (
            f"QLabel {{"
            f"  background-color: {bg_color};"
            f"  color: {tc};"
            f"  border-radius: {t.BORDER_RADIUS_BADGE}px;"
            f"  padding: 3px 12px;"
            f"  font-weight: {t.FONT_WEIGHT_HEAVY};"
            f"  font-size: {t.FONT_SIZE_TINY}px;"
            f"  letter-spacing: 0.3px;"
            f"}}"
        )

    @classmethod
    def badge_success(cls) -> str:
        return cls.badge_style(ct.theme.SUCCESS)

    @classmethod
    def badge_running(cls) -> str:
        return cls.badge_style(ct.theme.WARNING)

    @classmethod
    def badge_error(cls) -> str:
        return cls.badge_style(ct.theme.DANGER)

    @classmethod
    def badge_canceled(cls) -> str:
        return cls.badge_style(ct.theme.WARNING)

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
            f"<span style='color:{ct.theme.TEXT_SECONDARY};"
            f"font-family:Consolas,\"Courier New\",monospace;font-size:12px;'>"
            f"{text}: <a href='{url}' style='color:{ct.theme.GOLD};"
            f"text-decoration:none;'>abrir</a></span>"
        )

    @classmethod
    def log_section_html(cls, text: str) -> str:
        return (
            f"<span style='color:{ct.theme.GOLD};"
            f"font-family:Consolas,\"Courier New\",monospace;"
            f"font-size:12px;font-weight:700;'>{text}</span>"
        )