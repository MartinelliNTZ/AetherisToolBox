# -*- coding: utf-8 -*-
"""
ToastNotification — Notificação toast estilo Android
======================================================
Exibe uma mensagem temporária que aparece, fade out e se auto-destrói,
sem travar a UI (QTimer não-bloqueante).

Uso:
    ToastNotification.show("Configurações salvas com sucesso!")
    ToastNotification.show("Erro ao salvar", is_error=True)
"""

from __future__ import annotations

from PySide6.QtCore import QPoint, QPropertyAnimation, Qt, QTimer
from PySide6.QtGui import QColor, QFont, QPainter, QPalette
from PySide6.QtWidgets import QApplication, QLabel, QVBoxLayout, QWidget


class _ToastWidget(QWidget):
    """Widget interno do toast — sobrepoe a janela principal com fade out."""

    DURATION_MS = 2500       # tempo visível antes de iniciar fade
    FADE_DURATION_MS = 500   # duração do fade out
    MARGIN_BOTTOM = 60       # distância do bottom da parent window

    def __init__(
        self,
        text: str,
        parent: QWidget | None = None,
        is_error: bool = False,
    ):
        super().__init__(parent)

        self._is_ready = False  # impede fade antes de show()

        # ── configurações de janela ──
        self.setWindowFlags(
            Qt.WindowType.Tool
            | Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)

        # ── fundo e texto ──
        bg_color = "#C0392B" if is_error else "#2D2D2D"
        text_color = "#FFFFFF"
        border_color = "#E74C3C" if is_error else "#555555"

        self._label = QLabel(text, self)
        self._label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._label.setWordWrap(True)
        self._label.setStyleSheet(
            f"""
            QLabel {{
                background-color: {bg_color};
                color: {text_color};
                border: 1px solid {border_color};
                border-radius: 8px;
                padding: 12px 24px;
                font-size: 13px;
                font-weight: 600;
            }}
            """
        )

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.addWidget(self._label)
        self.setLayout(layout)

        self.adjustSize()

        # ── fade out animation ──
        self._fade_anim = QPropertyAnimation(self, b"windowOpacity")
        self._fade_anim.setDuration(self.FADE_DURATION_MS)
        self._fade_anim.setStartValue(1.0)
        self._fade_anim.setEndValue(0.0)
        self._fade_anim.finished.connect(self.close)

        # ── timer para iniciar fade out ──
        self._timer = QTimer(self)
        self._timer.setSingleShot(True)
        self._timer.timeout.connect(self._start_fade)
        self._timer.start(self.DURATION_MS)

        # Reposiciona ao redimensionar a parent
        if parent:
            try:
                parent.installEventFilter(self)
            except Exception:
                pass

    def showEvent(self, event):
        """Marca como pronto ao exibir."""
        super().showEvent(event)
        self._is_ready = True

    def _start_fade(self):
        """Inicia o fade out (apenas se já foi exibido)."""
        if self._is_ready:
            self._fade_anim.start()

    def _reposition(self):
        """Centraliza na parte inferior da parent window."""
        parent = self.parent()
        if parent and parent.isVisible():
            parent_rect = parent.geometry()
            x = parent_rect.x() + (parent_rect.width() - self.width()) // 2
            y = parent_rect.y() + parent_rect.height() - self.height() - self.MARGIN_BOTTOM
            self.move(QPoint(x, y))

    def eventFilter(self, obj, event):
        """Reajusta posição quando parent redimensiona."""
        if obj is self.parent() and event.type() == event.Type.Resize:
            QTimer.singleShot(0, self._reposition)
        return super().eventFilter(obj, event)


class ToastNotification:
    """
    Notificação toast estilo Android.

    Métodos estáticos:
        show(text, is_error=False, parent=None)
    """

    _instance: _ToastWidget | None = None

    @classmethod
    def show(cls, text: str, is_error: bool = False, parent: QWidget | None = None):
        """
        Exibe uma notificação toast na tela.

        Args:
            text: Mensagem a exibir.
            is_error: True para estilo vermelho (erro), False para padrão.
            parent: Widget pai (opcional — usa janela ativa se omitido).
        """
        # Fecha toast anterior se existir
        cls.dismiss()

        if parent is None:
            parent = _find_active_window()

        widget = _ToastWidget(text, parent=parent, is_error=is_error)
        widget._reposition()
        widget.show()
        cls._instance = widget

    @classmethod
    def dismiss(cls):
        """Fecha o toast atual se existir."""
        if cls._instance is not None:
            try:
                cls._instance.close()
            except RuntimeError:
                pass
            cls._instance = None


def _find_active_window() -> QWidget | None:
    """Retorna a janela principal ativa."""
    app = QApplication.instance()
    if app is None:
        return None
    for widget in app.topLevelWidgets():
        if widget.isVisible() and widget.windowTitle():
            return widget
    return None