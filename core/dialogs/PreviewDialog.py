# -*- coding: utf-8 -*-
"""
PreviewDialog — Diálogo genérico de pré-visualização
======================================================
Exibe uma lista de itens em um QTextEdit somente leitura,
com título dinâmico contendo a contagem de itens.

Uso:
    PreviewDialog.exec_preview(
        items=[("orig.txt", "novo.txt"), ...],
        title="Pré-Visualização",
        parent=self,
    )
"""

from __future__ import annotations

from typing import List, Tuple

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QTextEdit, QPushButton, QHBoxLayout,
)


class PreviewDialog(QDialog):
    """
    Diálogo modal de pré-visualização.

    Exibe uma lista de pares (original → novo) em um QTextEdit
    somente leitura, com um botão Fechar.
    """

    def __init__(
        self,
        items: List[Tuple[str, str]],
        title: str = "Pré-Visualização",
        parent=None,
        max_preview: int = 50,
    ):
        super().__init__(parent)
        self.setWindowTitle(f"{title} — {len(items)} itens")
        self.resize(600, 400)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)

        # Monta texto
        lines = [f"{orig} → {novo}" for orig, novo in items[:max_preview]]
        if len(items) > max_preview:
            lines.append(f"... e mais {len(items) - max_preview} item(ns)")
        text = "\n".join(lines)

        te = QTextEdit(text)
        te.setReadOnly(True)
        layout.addWidget(te)

        # Botão fechar
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        btn = QPushButton("Fechar")
        btn.clicked.connect(self.accept)
        btn_layout.addWidget(btn)
        layout.addLayout(btn_layout)

    @staticmethod
    def exec_preview(
        items: List[Tuple[str, str]],
        title: str = "Pré-Visualização",
        parent=None,
    ) -> None:
        """
        Atalho para criar, executar e descartar o diálogo.

        Args:
            items: Lista de tuplas (original, novo)
            title: Título do diálogo
            parent: Widget pai
        """
        dlg = PreviewDialog(items=items, title=title, parent=parent)
        dlg.exec()