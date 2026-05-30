# -*- coding: utf-8 -*-
"""
PreviewPanel — Widget de pré-visualização genérico
====================================================
Exibe preview de imagens (ou futuramente vetores) selecionadas.
Usa PIL para carregar e redimensionar com KeepAspectRatio.

Genérico: hoje funciona com fotos (PIL → QImage),
amanhã pode receber vetores via set_preview_data().

Uso:
    preview = PreviewPanel(fixed_size=(480, 360))
    preview.show_preview("c:/foto.png")
    preview.clear_preview()
"""

from __future__ import annotations

from typing import Optional

from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap, QImage
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel


class PreviewPanel(QWidget):
    """
    Painel de pré-visualização genérico.

    Parâmetros:
        fixed_size: tuple (largura, altura) — tamanho fixo do preview.
                    Padrão (480, 360).
        preview_type: str — tipo de preview ("image" para fotos,
                     futuro "vector", "shp", etc.)
    """

    def __init__(
        self,
        fixed_size: tuple[int, int] = (480, 360),
        preview_type: str = "image",
        parent=None,
    ):
        super().__init__(parent)
        self._preview_type = preview_type
        self._fixed_size = fixed_size

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self._label = QLabel("Nenhuma imagem selecionada")
        self._label.setObjectName("preview_label")
        self._label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._label.setMinimumSize(fixed_size[0], fixed_size[1])
        self._label.setMaximumSize(fixed_size[0], fixed_size[1])
        self._label.setStyleSheet(
            "background-color: #1e1e1e; border: 1px solid #333; color: #666;"
            "font-size: 12px;"
        )
        self._label.setWordWrap(True)
        layout.addWidget(self._label)

    # ── API Pública ─────────────────────────────────────────────────

    def show_preview(self, path: str) -> None:
        """
        Carrega e exibe preview de uma imagem do caminho informado.

        Args:
            path: Caminho completo do arquivo de imagem.
        """
        if not path:
            self.clear_preview()
            return

        try:
            from PIL import Image as PILImage
            from io import BytesIO

            img = PILImage.open(path)
            w, h = self._fixed_size
            img.thumbnail((w, h), PILImage.LANCZOS)
            bio = BytesIO()
            img.convert("RGBA").save(bio, format="PNG")
            qimg = QImage.fromData(bio.getvalue())
            pix = QPixmap.fromImage(qimg)
            self._label.setPixmap(
                pix.scaled(w, h, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            )
        except Exception as e:
            self._label.setText(f"Erro ao carregar:\n{path}\n{e}")

    def set_preview_data(self, data) -> None:
        """
        Aceita dados de preview pré-processados (QPixmap ou QImage).
        Útil para tipos não-imagem (vetores, etc.) no futuro.

        Args:
            data: QPixmap ou QImage com o conteúdo a exibir.
        """
        if isinstance(data, QImage):
            data = QPixmap.fromImage(data)
        if isinstance(data, QPixmap):
            w, h = self._fixed_size
            self._label.setPixmap(
                data.scaled(w, h, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            )
        else:
            self._label.setText("Formato de preview não suportado")

    def clear_preview(self) -> None:
        """Limpa o preview e restaura o texto placeholder."""
        self._label.setText("Nenhuma imagem selecionada")
        self._label.setPixmap(QPixmap())

    @property
    def preview_type(self) -> str:
        """Retorna o tipo de preview configurado."""
        return self._preview_type

    @preview_type.setter
    def preview_type(self, value: str) -> None:
        """Altera o tipo de preview em runtime."""
        self._preview_type = value