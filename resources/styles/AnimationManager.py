# -*- coding: utf-8 -*-
"""
AnimationManager — Gerenciador central de animações Qt
========================================================
Cria e gerencia animações via QPropertyAnimation com suporte
a hover grow, bounce, opacidade e qualquer propriedade numérica.

Uso:
    from resources.styles.AnimationManager import AnimationManager

    # Hover grow em qualquer widget
    AnimationManager.animate_hover_grow(meu_botao)

    # Animação custom
    anim = AnimationManager.animate_property(
        widget, b"minimumSize", QSize(32, 32), QSize(36, 36), duration=150
    )
"""

from __future__ import annotations

from PySide6.QtCore import QPropertyAnimation, QEasingCurve, QSize
from PySide6.QtWidgets import QWidget

from resources.styles.ThemeManager import ct


class AnimationManager:
    """
    Gerador de animações reutilizáveis.

    Todos os métodos são estáticos — não é necessário instanciar.
    """

    # ── Animações Genéricas ───────────────────────────────────────

    @staticmethod
    def animate_property(
        widget: QWidget,
        property_name: bytes,
        start_value,
        end_value,
        duration: int | None = None,
        easing: QEasingCurve.Type = QEasingCurve.Type.OutCubic,
    ) -> QPropertyAnimation:
        """
        Cria e inicia uma QPropertyAnimation no widget.

        Args:
            widget: Widget alvo.
            property_name: Propriedade Qt a animar (ex: b"minimumSize").
            start_value: Valor inicial.
            end_value: Valor final.
            duration: Duração em ms. Se None, usa ANIMATION_NORMAL do tema.
            easing: Curva de easing.

        Returns:
            A instância da QPropertyAnimation já iniciada.
        """
        duration = duration or ct.theme.ANIMATION_NORMAL
        anim = QPropertyAnimation(widget, property_name)
        anim.setDuration(duration)
        anim.setStartValue(start_value)
        anim.setEndValue(end_value)
        anim.setEasingCurve(easing)
        anim.start()
        return anim

    # ── Hover Grow ────────────────────────────────────────────────

    _HOVER_GROW_REGISTRY: dict[int, list[QPropertyAnimation]] = {}

    @classmethod
    def animate_hover_grow(
        cls,
        widget: QWidget,
        grow_px: int | None = None,
        duration: int | None = None,
    ) -> None:
        """
        Configura animação de aumentar o widget ao passar o mouse.

        Instala event filters de enter/leave no widget para animar
        o tamanho de ``base_size`` para ``base_size + grow_px``.

        Args:
            widget: Widget alvo (deve ter setFixedSize()).
            grow_px: Quantos pixels aumentar. Se None, usa TOOLBAR_BTN_HOVER_GROW do tema.
            duration: Duração em ms. Se None, usa ANIMATION_FAST do tema.
        """
        grow_px = grow_px if grow_px is not None else ct.theme.TOOLBAR_BTN_HOVER_GROW
        duration = duration if duration is not None else ct.theme.ANIMATION_FAST
        from PySide6.QtCore import QEvent
        from PySide6.QtCore import QTimer  # noqa: F401

        original = widget.property("_hover_base_size")
        if original is None:
            original = widget.size()
            widget.setProperty("_hover_base_size", original)

        def _enter():
            w = original.width() + grow_px
            h = original.height() + grow_px
            cls.animate_property(
                widget, b"minimumSize", widget.minimumSize(), QSize(w, h),
                duration=duration,
            )
            cls.animate_property(
                widget, b"maximumSize", widget.maximumSize(), QSize(w, h),
                duration=duration,
            )

        def _leave():
            w = original.width()
            h = original.height()
            cls.animate_property(
                widget, b"minimumSize", widget.minimumSize(), QSize(w, h),
                duration=duration,
            )
            cls.animate_property(
                widget, b"maximumSize", widget.maximumSize(), QSize(w, h),
                duration=duration,
            )

        # Usa event filter via lambda para não precisar subclasse
        widget._hover_grow_enter = lambda e=None: _enter() if e is None or e.type() == QEvent.Type.Enter else None
        widget._hover_grow_leave = lambda e=None: _leave() if e is None or e.type() == QEvent.Type.Leave else None
        widget.enterEvent = widget._hover_grow_enter
        widget.leaveEvent = widget._hover_grow_leave

    # ── Bounce ────────────────────────────────────────────────────

    @classmethod
    def animate_bounce(
        cls,
        widget: QWidget,
        property_name: bytes,
        start_value,
        peak_value,
        end_value,
        duration: int | None = None,
    ) -> list[QPropertyAnimation]:
        """
        Cria uma animação bounce (vai ao pico e retorna).

        Retorna lista com duas animações: forward e backward.
        """
        duration = duration or ct.theme.ANIMATION_SLOW
        half = duration // 2

        fwd = QPropertyAnimation(widget, property_name)
        fwd.setDuration(half)
        fwd.setStartValue(start_value)
        fwd.setEndValue(peak_value)
        fwd.setEasingCurve(QEasingCurve.Type.OutQuad)
        fwd.finished.connect(lambda: cls._bounce_back(widget, property_name, peak_value, end_value, half))
        fwd.start()
        return [fwd]

    @classmethod
    def _bounce_back(cls, widget, prop, peak, end, duration):
        anim = QPropertyAnimation(widget, prop)
        anim.setDuration(duration)
        anim.setStartValue(peak)
        anim.setEndValue(end)
        anim.setEasingCurve(QEasingCurve.Type.InQuad)
        anim.start()

    # ── Limpeza ───────────────────────────────────────────────────

    @classmethod
    def clear_hover_grow(cls, widget: QWidget) -> None:
        """Remove a animação hover grow do widget (restaura event handlers)."""
        if hasattr(widget, "_hover_grow_enter"):
            del widget._hover_grow_enter
        if hasattr(widget, "_hover_grow_leave"):
            del widget._hover_grow_leave
        base = widget.property("_hover_base_size")
        if base:
            widget.setFixedSize(base)