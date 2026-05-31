# -*- coding: utf-8 -*-
"""
PreviewPanel — Widget de pré-visualização genérico
====================================================
Exibe preview de imagens (ou futuramente vetores) selecionadas.
Usa PIL para carregar e redimensionar com KeepAspectRatio.

Suporta zoom (roda do mouse) e arrasto lateral (botão esquerdo).

Uso:
    preview = PreviewPanel(fixed_size=(480, 360))
    preview.show_preview("c:/foto.png")
    preview.clear_preview()
"""

from __future__ import annotations

from typing import Optional

from PySide6.QtCore import Qt, QPoint, QPointF
from PySide6.QtGui import QPixmap, QImage, QPainter
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

        # ── Zoom/Pan state ──────────────────────────────────────────
        self._base_pixmap: QPixmap | None = None
        self._zoom_factor: float = 1.0
        self._pan_offset: QPoint = QPoint(0, 0)
        self._is_dragging: bool = False
        self._drag_start: QPointF = QPointF(0, 0)
        self._drag_start_pan: QPoint = QPoint(0, 0)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self._label = QLabel("Nenhuma imagem selecionada")
        self._label.setObjectName("preview_label")
        self._label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._label.setMinimumSize(fixed_size[0], fixed_size[1])
        self._label.setMaximumSize(fixed_size[0], fixed_size[1])
        self._label.setWordWrap(True)
        # Permite que os eventos do mouse passem pelo label até o PreviewPanel
        self._label.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        layout.addWidget(self._label)

        self.setMouseTracking(True)

    # ── Zoom/Pan Interno ────────────────────────────────────────────

    def _update_preview(self) -> None:
        """Re-render preview with current zoom and pan."""
        if self._base_pixmap is None or self._base_pixmap.isNull():
            return

        w, h = self._fixed_size

        zoomed = self._base_pixmap.scaled(
            int(w * self._zoom_factor),
            int(h * self._zoom_factor),
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )

        zw, zh = zoomed.width(), zoomed.height()
        result = QPixmap(w, h)
        result.fill(Qt.GlobalColor.transparent)

        painter = QPainter(result)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)

        if zw <= w and zh <= h:
            # Zoomed out — center image in viewport
            off_x = (w - zw) // 2
            off_y = (h - zh) // 2
            painter.drawPixmap(off_x, off_y, zoomed)
        else:
            # Zoomed in — show portion based on pan offset
            max_sx = max(0, zw - w)
            max_sy = max(0, zh - h)
            sx = max_sx // 2 + self._pan_offset.x()
            sy = max_sy // 2 + self._pan_offset.y()
            sx = max(0, min(sx, max_sx))
            sy = max(0, min(sy, max_sy))
            painter.drawPixmap(0, 0, w, h, zoomed, sx, sy, w, h)

        painter.end()
        self._label.setPixmap(result)

    # ── Eventos ─────────────────────────────────────────────────────

    def wheelEvent(self, event):
        """Zoom in/out with mouse wheel."""
        if self._base_pixmap is None or self._base_pixmap.isNull():
            super().wheelEvent(event)
            return

        delta = event.angleDelta().y()
        if delta > 0:
            self._zoom_factor *= 1.15
        else:
            self._zoom_factor /= 1.15

        self._zoom_factor = max(0.1, min(10.0, self._zoom_factor))
        self._update_preview()
        event.accept()

    def mousePressEvent(self, event):
        """Start drag with left button."""
        if (
            event.button() == Qt.MouseButton.LeftButton
            and self._base_pixmap is not None
            and not self._base_pixmap.isNull()
        ):
            self._is_dragging = True
            self._drag_start = event.position()
            self._drag_start_pan = QPoint(self._pan_offset)
            self.setCursor(Qt.CursorShape.ClosedHandCursor)
            event.accept()
            return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        """Update pan offset while dragging."""
        if self._is_dragging:
            delta = event.position() - self._drag_start
            self._pan_offset = QPoint(
                int(self._drag_start_pan.x() + delta.x()),
                int(self._drag_start_pan.y() + delta.y()),
            )
            self._update_preview()
            event.accept()
            return
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        """End drag."""
        if event.button() == Qt.MouseButton.LeftButton and self._is_dragging:
            self._is_dragging = False
            self.setCursor(Qt.CursorShape.ArrowCursor)
            event.accept()
            return
        super().mouseReleaseEvent(event)

    def mouseDoubleClickEvent(self, event):
        """Reset zoom and pan on double-click."""
        if event.button() == Qt.MouseButton.LeftButton:
            self._zoom_factor = 1.0
            self._pan_offset = QPoint(0, 0)
            self._update_preview()
            event.accept()
            return
        super().mouseDoubleClickEvent(event)

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
            self._base_pixmap = QPixmap.fromImage(qimg)
            self._zoom_factor = 1.0
            self._pan_offset = QPoint(0, 0)
            self._update_preview()
        except Exception as e:
            self._label.setText(f"Erro ao carregar:\n{path}\n{e}")
            self._base_pixmap = None

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
            self._base_pixmap = data
            self._zoom_factor = 1.0
            self._pan_offset = QPoint(0, 0)
            self._update_preview()
        else:
            self._label.setText("Formato de preview não suportado")
            self._base_pixmap = None

    def clear_preview(self) -> None:
        """Limpa o preview e restaura o texto placeholder."""
        self._base_pixmap = None
        self._zoom_factor = 1.0
        self._pan_offset = QPoint(0, 0)
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