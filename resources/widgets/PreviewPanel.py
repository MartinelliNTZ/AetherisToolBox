# -*- coding: utf-8 -*-
"""
PreviewPanel — Widget de pré-visualização genérico
====================================================
Exibe preview de arquivos com detecção automática de tipo.

Utiliza GroupPainel como container externo e delega o conteúdo
para o widget apropriado conforme a extensão do arquivo:

- Imagens → ImagePreviewPanel (zoom, pan, mouse/key 7)
- Texto  → TextPreviewWidget (editor com Copiar/Salvar)

Novos tipos podem ser registrados via register_handler().

Uso:
    preview = PreviewPanel(title="Pré-Visualização")
    preview.show_preview("c:/foto.png")
    preview.clear_preview()

    # Registrar handler customizado
    from resources.widgets.PreviewPanel import register_handler
    register_handler(frozenset({".xyz"}), factory_fn)
"""

from __future__ import annotations

import os
from typing import Callable, Optional

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel

from resources.widgets.GroupPainel import GroupPainel
from resources.widgets.ImagePreviewPanel import ImagePreviewPanel
from resources.widgets.TextPreviewWidget import TextPreviewWidget
from utils.DictManager import IMAGE_EXTENSIONS, TEXT_EXTENSIONS


# ── Registry de Handlers ─────────────────────────────────────────────
_HANDLERS: list[tuple[frozenset[str], Callable[[str], QWidget]]] = []


def _image_factory(path: str) -> QWidget:
    """Cria ImagePreviewPanel carregado com a imagem."""
    panel = ImagePreviewPanel(fixed_size=None)
    panel.show_preview(path)
    return panel


def _text_factory(path: str) -> QWidget:
    """Cria TextPreviewWidget carregado com o arquivo."""
    widget = TextPreviewWidget()
    widget.load_file(path)
    return widget


def register_handler(
    extensions: frozenset[str],
    factory: Callable[[str], QWidget],
) -> None:
    """
    Registra um handler para um conjunto de extensões.

    Args:
        extensions: Conjunto de extensões (ex: frozenset({".png", ".jpg"}))
        factory: Função que recebe (path: str) e retorna um QWidget
    """
    _HANDLERS.append((extensions, factory))


def _detect_handler(path: str) -> Callable[[str], QWidget] | None:
    """Retorna a factory do handler para a extensão do arquivo."""
    _, ext = os.path.splitext(path)
    ext = ext.lower()
    for extensions, factory in _HANDLERS:
        if ext in extensions:
            return factory
    return None


# ── Registro dos handlers padrão ─────────────────────────────────────
register_handler(frozenset(IMAGE_EXTENSIONS.keys()), _image_factory)
register_handler(frozenset(TEXT_EXTENSIONS.keys()), _text_factory)


class PreviewPanel(QWidget):
    """
    Painel de pré-visualização genérico.

    Detecta automaticamente o tipo do arquivo pela extensão
    e delega para o handler apropriado dentro de um GroupPainel.

    Parâmetros:
        title: Título exibido no GroupPainel.
               Padrão "Pré-Visualização".
    """

    def __init__(self, title: str = "Pré-Visualização", parent=None):
        super().__init__(parent)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self._group = GroupPainel(title)
        layout.addWidget(self._group)

        # Placeholder
        self._placeholder = QLabel("Nenhum arquivo selecionado")
        self._placeholder.setObjectName("preview_placeholder")
        self._placeholder.setAlignment(
            self._placeholder.alignment() | Qt.AlignmentFlag.AlignCenter
        )
        self._placeholder.setWordWrap(True)
        self._group.group_layout.addWidget(self._placeholder, 1)

        # Widget interno gerenciado pelo handler
        self._handler_widget: QWidget | None = None

    # ── API Pública ─────────────────────────────────────────────────

    def show_preview(self, path: str) -> None:
        """
        Carrega e exibe preview do arquivo.
        Detecta automaticamente o tipo pela extensão.
        """
        self.clear_preview()
        if not path:
            return

        factory = _detect_handler(path)
        if factory is None:
            self._placeholder.setText(
                f"Tipo de arquivo não suportado:\n{path}"
            )
            return

        try:
            widget = factory(path)
            self._handler_widget = widget
            # Substitui placeholder pelo widget do handler
            self._group.group_layout.removeWidget(self._placeholder)
            self._placeholder.setParent(None)
            self._group.group_layout.addWidget(widget, 1)
        except Exception as e:
            self._placeholder.setText(f"Erro ao carregar:\n{path}\n{e}")

    def clear_preview(self) -> None:
        """Limpa o preview e restaura o texto placeholder."""
        if self._handler_widget:
            self._group.group_layout.removeWidget(self._handler_widget)
            self._handler_widget.setParent(None)
            self._handler_widget.deleteLater()
            self._handler_widget = None

        self._placeholder.setText("Nenhum arquivo selecionado")
        self._group.group_layout.addWidget(self._placeholder, 1)