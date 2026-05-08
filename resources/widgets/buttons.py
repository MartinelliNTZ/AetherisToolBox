# -*- coding: utf-8 -*-
"""
Widgets de Botão — Aetheris ToolBox
=====================================
Botões reutilizáveis pré-configurados com os estilos do sistema.
"""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QPushButton
from resources.styles.styles import AppStyles


class SimplePrimaryButton(QPushButton):
    """
    Botão primário com gradiente ouro.
    Uso: executar pipeline, ações principais.
    """

    def __init__(self, text: str = "EXECUTAR", parent=None):
        super().__init__(text, parent)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setStyleSheet(AppStyles.btn_primary_style())
        self.setMinimumWidth(180)
        self.setMinimumHeight(34)


class SimpleSecondaryButton(QPushButton):
    """
    Botão secundário com fundo escuro e texto dourado.
    Uso: Salvar Config, Carregar Config, Restaurar Padrão, etc.
    """

    def __init__(self, text: str = "Ação", parent=None):
        super().__init__(text, parent)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setStyleSheet(AppStyles.btn_secondary_style())
        self.setMinimumHeight(32)


class SimpleDangerButton(QPushButton):
    """
    Botão de perigo (vermelho).
    Uso: Cancelar, ações destrutivas.
    """

    def __init__(self, text: str = "CANCELAR", parent=None):
        super().__init__(text, parent)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setStyleSheet(AppStyles.btn_danger_style())
        self.setMinimumHeight(32)
        self.setMinimumWidth(100)


class SimpleGhostButton(QPushButton):
    """
    Botão ghost (invisível, aparece no hover).
    Uso: Adicionar Shapefile, ações sutis.
    """

    def __init__(self, text: str = "Ação", parent=None):
        super().__init__(text, parent)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setStyleSheet(AppStyles.btn_ghost_style())


class SimpleRemoveButton(QPushButton):
    """
    Botão de remover (hover vermelho).
    Uso: remover linhas de tabela.
    """

    def __init__(self, text: str = "Remover", parent=None):
        super().__init__(text, parent)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setStyleSheet(AppStyles.btn_remove_style())