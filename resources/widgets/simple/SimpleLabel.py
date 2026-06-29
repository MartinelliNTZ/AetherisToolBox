# -*- coding: utf-8 -*-
"""
SimpleLabel — Label padrão com estilo consistente.
====================================================
QLabel com fonte monospace e cor clara (E5E7EB),
ideal para mensagens auxiliares na interface.

Uso:
    from resources.widgets.SimpleLabel import SimpleLabel

    label = SimpleLabel("Pressione ESC para cancelar")
    label.setObjectName("hint_label")
"""

from __future__ import annotations

from PySide6.QtWidgets import QLabel


class SimpleLabel(QLabel):
    """
    Label padrão com fonte monospace e cor clara.
    """

    def __init__(self, text: str = "", parent=None):
        super().__init__(text, parent)
        self.setStyleSheet("color: #A1A1AA; font-family: Consolas, monospace; font-size: 12px;")