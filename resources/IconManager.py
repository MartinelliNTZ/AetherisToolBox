# -*- coding: utf-8 -*-
"""
IconManager — Gerenciador central de ícones do Aetheris ToolBox
=================================================================
Fornece QIcons a partir de nomes de arquivo na pasta resources/icons/.
Como atualmente só existe Aetheris.ico, todas as ferramentas usam
esse mesmo ícone por enquanto.
"""

from __future__ import annotations

import os
from pathlib import Path

from PySide6.QtGui import QIcon


class IconManager:
    """
    Gerenciador central de ícones.

    Uso:
        icon = IconManager.get("console")
        path = IconManager.path("console")
    """

    BASE_PATH = os.path.join(os.path.dirname(__file__), "icons")

    # ── Ícones disponíveis ────────────────────────────────────────────
    # Atualmente apenas um ícone genérico. Conforme novos ícones forem
    # adicionados a pasta resources/icons/, basta declarar aqui.
    DEFAULT = "Aetheris2.ico"

    # Aliases para cada ferramenta (todas apontam pro mesmo ícone)
    SYSTEM = "Aetheris.ico"
    LAYOUTS = "Aetheris.ico"
    FOLDER = "Aetheris.ico"
    VECTOR = "Aetheris.ico"
    AGRICULTURE = "Aetheris.ico"
    RASTER = "Aetheris.ico"

    # ── Métodos ───────────────────────────────────────────────────────

    @classmethod
    def get(cls, name: str) -> QIcon:
        """
        Retorna um QIcon a partir do nome do arquivo de ícone.
        Se o arquivo não existir, retorna um QIcon vazio (não quebra).
        """
        path = cls.path(name)
        return QIcon(path)

    @classmethod
    def path(cls, name: str) -> str:
        """Retorna o caminho completo do arquivo de ícone."""
        full = os.path.join(cls.BASE_PATH, name)
        if os.path.isfile(full):
            return full
        # Fallback para o ícone default
        fallback = os.path.join(cls.BASE_PATH, cls.DEFAULT)
        return fallback if os.path.isfile(fallback) else ""

    @classmethod
    def from_alias(cls, alias: str) -> QIcon:
        """
        Retorna QIcon a partir de um alias de ferramenta.
        Ex: IconManager.from_alias("Console") → ícone System
        """
        icon_file = getattr(cls, alias.upper(), cls.DEFAULT)
        return cls.get(icon_file)

    @classmethod
    def default_icon(cls) -> QIcon:
        """Retorna o ícone default do sistema."""
        return cls.get(cls.DEFAULT)