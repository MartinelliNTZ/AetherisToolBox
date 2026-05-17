# -*- coding: utf-8 -*-
"""
BaseStyle — Estilos globais base do sistema
=============================================
Usa o tema atual (`ct` = CurrentTheme do ThemeManager) para gerar
o stylesheet global do Qt que abrange todo o sistema.
Zero valores hardcoded — tudo centralizado no tema via tokens semânticos.
"""

from __future__ import annotations

from resources.styles.ThemeManager import ct


class BaseStyle:
    """
    Classe base que gera o stylesheet global usando o tema ativo.
    Não instanciar — usar métodos de classe diretamente.
    """

    @classmethod
    def global_stylesheet(cls) -> str:
        """Gera o QSS global completo usando o tema atual. Sem hardcoded."""
        t = ct.theme
        return f"""
        QMainWindow, QWidget {{
            background-color: {t.SURFACE_1};
            color: {t.TEXT_MEDIUM};
            font-family: {t.FONT_FAMILY_DEFAULT};
            font-size: {t.FONT_SIZE_NORMAL}px;
        }}

        QScrollArea {{
            border: none;
            background: transparent;
        }}
        QScrollBar:vertical {{
            background: {t.SURFACE_1};
            width: {t.SCROLLBAR_WIDTH}px;
            margin: 0;
        }}
        QScrollBar::handle:vertical {{
            background: {t.SURFACE_4};
            border-radius: {t.BORDER_RADIUS_SCROLLBAR}px;
            min-height: {t.SCROLLBAR_MIN_HEIGHT}px;
        }}
        QScrollBar::handle:vertical:hover {{
            background: {t.ACCENT};
        }}
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
            height: 0;
        }}

        /* ===== GROUP BOX ===== */
        QGroupBox {{
            background-color: {t.SURFACE_3};
            border: none;
            border-radius: {t.BORDER_RADIUS_CARD}px;
            margin-top: {t.GROUP_MARGIN_TOP}px;
            padding: {t.CARD_PADDING_V}px {t.CARD_PADDING_H}px {t.CARD_PADDING_H}px {t.CARD_PADDING_H}px;
            font-weight: {t.FONT_WEIGHT_BOLD};
        }}
        QGroupBox::title {{
            subcontrol-origin: padding;
            subcontrol-position: top left;
            left: {t.GROUP_TITLE_LEFT}px;
            top: {t.GROUP_TITLE_TOP}px;
            padding: {t.GROUP_TITLE_PADDING};
            color: {t.ACCENT_TEXT};
            font-weight: {t.FONT_WEIGHT_EXTRABOLD};
            font-size: {t.FONT_SIZE_SMALL}px;
            letter-spacing: {t.GROUP_TITLE_LETTER_SPACING};
            background-color: {t.SURFACE_3};
            border-radius: {t.BORDER_RADIUS_GROUP_TITLE}px;
        }}

        /* ===== LABEL ===== */
        QLabel {{
            background: transparent;
            color: {t.TEXT_MEDIUM};
        }}
        QLabel#header_title {{
            font-size: {t.FONT_SIZE_TITLE}px;
            font-weight: {t.FONT_WEIGHT_EXTRABOLD};
            color: {t.TEXT_HIGH};
            letter-spacing: 1px;
        }}
        QLabel#header_subtitle {{
            font-size: {t.FONT_SIZE_SMALL}px;
            color: {t.TEXT_LOW};
        }}
        QLabel#section_badge {{
            background-color: {t.ACCENT};
            color: {t.SURFACE_0};
            border-radius: {t.BORDER_RADIUS_BADGE}px;
            padding: {t.BADGE_PADDING_V} {t.BADGE_PADDING_H};
            font-size: {t.FONT_SIZE_TINY}px;
            font-weight: {t.FONT_WEIGHT_HEAVY};
            letter-spacing: {t.BADGE_LETTER_SPACING};
        }}

        /* ===== TITLE BAR ===== */
        QWidget#title_bar {{
            background-color: {t.TITLE_BAR};
            border-bottom: 1px solid {t.SURFACE_2};
        }}
        QLabel#window_title {{
            color: {t.TEXT_DISABLED};
            font-size: {t.WINDOW_TITLE_FONT_SIZE}px;
            font-weight: {t.FONT_WEIGHT_BOLD};
            letter-spacing: {t.WINDOW_TITLE_LETTER_SPACING};
        }}
        QPushButton#title_btn, QPushButton#title_btn_close {{
            background: transparent;
            color: {t.TEXT_DISABLED};
            border: none;
            border-radius: {t.BORDER_RADIUS_TITLE_BTN}px;
            min-width: {t.TITLE_BTN_WIDTH}px;
            max-width: {t.TITLE_BTN_WIDTH}px;
            min-height: {t.TITLE_BTN_HEIGHT}px;
            max-height: {t.TITLE_BTN_HEIGHT}px;
            font-size: {t.TITLE_BTN_FONT_SIZE}px;
        }}
        QPushButton#title_btn:hover {{
            background-color: {t.SURFACE_3};
            color: {t.TEXT_MEDIUM};
        }}
        QPushButton#title_btn_close:hover {{
            background-color: {t.COLOR_DANGER};
            color: white;
        }}

        /* ===== APPBAR TOOLBAR ===== */
        QWidget#appbar_toolbar {{
            background: transparent;
        }}
        QPushButton#toolbar_btn {{
            background-color: transparent;
            color: {t.TEXT_LOW};
            border: none;
            border-radius: {t.BORDER_RADIUS_TOOLBAR_BTN}px;
            padding: {t.TOOLBAR_BTN_PADDING_V} {t.TOOLBAR_BTN_PADDING_H};
            font-size: {t.FONT_SIZE_SMALL}px;
            font-weight: {t.FONT_WEIGHT_BOLD};
        }}
        QPushButton#toolbar_btn:hover {{
            background-color: {t.SURFACE_3};
            color: {t.ACCENT_TEXT};
        }}

        /* ===== SIDE PANEL (Workspace) ===== */
        QWidget#tool_side_panel {{
            background-color: {t.SURFACE_0};
        }}
        QPushButton#tool_selector_btn {{
            background-color: transparent;
            color: {t.TEXT_DISABLED};
            border: none;
            border-radius: {t.BORDER_RADIUS_TOOL_SELECTOR}px;
            padding: {t.TOOL_SELECTOR_PADDING_V} {t.TOOL_SELECTOR_PADDING_H};
            font-size: {t.FONT_SIZE_TINY}px;
            font-weight: {t.FONT_WEIGHT_EXTRABOLD};
            letter-spacing: {t.TOOL_SELECTOR_LETTER_SPACING};
        }}
        QPushButton#tool_selector_btn:hover {{
            background-color: {t.SURFACE_2};
            color: {t.ACCENT_TEXT};
        }}
        QPushButton#tool_selector_btn:checked {{
            background-color: {t.ACCENT};
            color: {t.SURFACE_0};
        }}

        /* ===== CONSOLE TOOLBAR ===== */
        QWidget#console_toolbar {{
            background-color: {t.SURFACE_2};
            border-bottom: 1px solid {t.DIVIDER};
        }}
        /* ===== WORKSPACE TABS ===== */
        QTabBar#workspace_tabs {{
            background-color: {t.TITLE_BAR};
            border: none;
            padding: 0;
            font-size: {t.FONT_SIZE_SMALL}px;
        }}
        QTabBar::tab {{
            background-color: transparent;
            color: {t.TEXT_LOW};
            border: none;
            padding: 0;
            margin: 0;
            font-weight: {t.FONT_WEIGHT_BOLD};
            font-size: {t.FONT_SIZE_SMALL}px;
        }}
        QTabBar::tab:hover {{
            background-color: {t.SURFACE_2};
            color: {t.TEXT_MEDIUM};
        }}
        QTabBar::tab:selected {{
            background-color: {t.SURFACE_1};
            color: {t.ACCENT_TEXT};
            border-bottom: 2px solid {t.ACCENT};
        }}

        QTabBar::close-button {{
            image: none;
            width: {t.TAB_CLOSE_BUTTON_SIZE}px;
            height: {t.TAB_CLOSE_BUTTON_SIZE}px;
            subcontrol-position: right;
            opacity: 0;
        }}
        QTabBar::tab:hover > QTabBar::close-button,
        QTabBar::tab:selected > QTabBar::close-button {{
            opacity: 1;
        }}
        QTabBar::close-button:hover {{
            background-color: {t.COLOR_DANGER};
            border-radius: {t.CLOSE_BUTTON_BORDER_RADIUS}px;
        }}

        QWidget#workspace_tab {{
            background-color: transparent;
            border: none;
            padding: 0px;
        }}

        QWidget#vertical_tab {{
            background-color: transparent;
            border: none;
            padding: 0px;
        }}

        QFrame#workspace_separator {{
            background-color: {t.BORDER_DEFAULT};
            border: none;
        }}

        /* ===== SPLITTER ===== */
        QSplitter::handle {{
            background-color: {t.BORDER_DEFAULT};
        }}
        QSplitter::handle:hover {{
            background-color: {t.ACCENT};
        }}
        QSplitter#workspace_splitter::handle {{
            width: {t.SPLITTER_HANDLE_WIDTH}px;
        }}

        /* ===== LINE EDIT ===== */
        QLineEdit {{
            background-color: {t.SURFACE_4};
            border: none;
            border-radius: {t.BORDER_RADIUS_INPUT}px;
            padding: {t.INPUT_PADDING_V} {t.INPUT_PADDING_H};
            color: {t.TEXT_MEDIUM};
            selection-background-color: {t.ACCENT};
            selection-color: {t.SURFACE_0};
        }}
        QLineEdit:focus {{
            background-color: {t.SURFACE_5};
        }}
        QLineEdit:disabled {{
            background-color: {t.SURFACE_3};
            color: {t.TEXT_DISABLED};
        }}

        /* ===== SPIN BOX ===== */
        QSpinBox, QDoubleSpinBox {{
            background-color: {t.SURFACE_4};
            border: none;
            border-radius: {t.BORDER_RADIUS_INPUT}px;
            padding: {t.SPINBOX_PADDING};
            color: {t.TEXT_MEDIUM};
        }}
        QSpinBox:focus, QDoubleSpinBox:focus {{
            background-color: {t.SURFACE_5};
        }}
        QSpinBox::up-button, QDoubleSpinBox::up-button,
        QSpinBox::down-button, QDoubleSpinBox::down-button {{
            width: {t.SPINBOX_BTN_WIDTH}px;
            background: {t.SURFACE_3};
            border-radius: {t.BORDER_RADIUS_SPINBOX_BTN}px;
            margin: {t.SPINBOX_BTN_MARGIN};
        }}
        QSpinBox::up-button:hover, QDoubleSpinBox::up-button:hover,
        QSpinBox::down-button:hover, QDoubleSpinBox::down-button:hover {{
            background: {t.ACCENT};
        }}

        /* ===== COMBO BOX ===== */
        QComboBox {{
            background-color: {t.SURFACE_4};
            border: none;
            border-radius: {t.BORDER_RADIUS_INPUT}px;
            padding: {t.COMBOBOX_PADDING};
            color: {t.TEXT_MEDIUM};
            min-width: {t.COMBOBOX_MIN_WIDTH}px;
        }}
        QComboBox:focus {{
            background-color: {t.SURFACE_5};
        }}
        QComboBox:disabled {{
            background-color: {t.SURFACE_3};
            color: {t.TEXT_DISABLED};
        }}
        QComboBox::drop-down {{
            subcontrol-origin: padding;
            subcontrol-position: top right;
            width: {t.COMBOBOX_DROPDOWN_WIDTH}px;
            border-left: 1px solid {t.SURFACE_4};
            border-top-right-radius: {t.BORDER_RADIUS_INPUT}px;
            border-bottom-right-radius: {t.BORDER_RADIUS_INPUT}px;
        }}
        QComboBox::down-arrow {{
            image: none;
            border-left: {t.COMBOBOX_ARROW_SIZE} solid transparent;
            border-right: {t.COMBOBOX_ARROW_SIZE} solid transparent;
            border-top: 5px solid {t.TEXT_LOW};
        }}
        QComboBox QAbstractItemView {{
            background-color: {t.SURFACE_3};
            border: none;
            border-radius: {t.COMBOBOX_POPUP_BORDER_RADIUS}px;
            color: {t.TEXT_MEDIUM};
            selection-background-color: {t.ACCENT};
            selection-color: {t.SURFACE_0};
            outline: none;
        }}

        /* ===== CHECK BOX ===== */
        QCheckBox {{
            spacing: {t.CHECKBOX_SPACING}px;
            background: transparent;
            color: {t.TEXT_MEDIUM};
        }}
        QCheckBox::indicator {{
            width: {t.CHECKBOX_SIZE}px;
            height: {t.CHECKBOX_SIZE}px;
            border-radius: {t.BORDER_RADIUS_CHECKBOX}px;
            background-color: {t.SURFACE_4};
        }}
        QCheckBox::indicator:checked {{
            background-color: {t.ACCENT};
        }}
        QCheckBox::indicator:hover {{
            background-color: {t.SURFACE_5};
        }}

        /* ===== TABLE ===== */
        QTableWidget {{
            background-color: {t.SURFACE_4};
            border: none;
            border-radius: {t.BORDER_RADIUS_TABLE}px;
            gridline-color: {t.DIVIDER};
            color: {t.TEXT_MEDIUM};
        }}
        QTableWidget::item {{
            padding: {t.TABLE_ITEM_PADDING};
        }}
        QTableWidget::item:selected {{
            background-color: {t.ACCENT};
            color: {t.SURFACE_0};
        }}
        QHeaderView::section {{
            background-color: {t.SURFACE_3};
            color: {t.TEXT_LOW};
            padding: {t.HEADER_PADDING};
            border: none;
            border-bottom: 2px solid {t.ACCENT};
            font-weight: {t.FONT_WEIGHT_EXTRABOLD};
            font-size: {t.HEADER_FONT_SIZE}px;
            letter-spacing: {t.HEADER_LETTER_SPACING};
        }}

        /* ===== TEXT BROWSER / TEXT EDIT ===== */
        QTextBrowser, QTextEdit {{
            background-color: {t.SURFACE_4};
            border: none;
            border-radius: {t.BORDER_RADIUS_TABLE}px;
            color: {t.TEXT_MEDIUM};
            font-family: {t.FONT_FAMILY_MONO};
            font-size: {t.TEXT_EDIT_FONT_SIZE}px;
            padding: {t.TEXT_EDIT_PADDING};
            selection-background-color: {t.ACCENT};
            selection-color: {t.SURFACE_0};
        }}

        /* ===== PROGRESS BAR ===== */
        QProgressBar {{
            border: none;
            border-radius: {t.BORDER_RADIUS_PROGRESS}px;
            background-color: {t.SURFACE_2};
            text-align: center;
            color: {t.TEXT_MEDIUM};
            font-weight: {t.FONT_WEIGHT_EXTRABOLD};
            font-size: {t.FONT_SIZE_SMALL}px;
            height: {t.PROGRESS_BAR_HEIGHT}px;
        }}
        QProgressBar::chunk {{
            border-radius: {t.BORDER_RADIUS_PROGRESS}px;
            background: qlineargradient(
                x1:0, y1:0, x2:1, y2:0,
                stop:0 {t.ACCENT_GRADIENT[0]},
                stop:1 {t.ACCENT_GRADIENT[1]}
            );
        }}
        """