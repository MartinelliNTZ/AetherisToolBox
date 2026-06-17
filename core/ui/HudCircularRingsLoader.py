# -*- coding: utf-8 -*-
"""
HudCircularRingsLoader — Overlay de carregamento com 3 modos de progresso
===========================================================================

Modo 1 — FEEDBACK REAL:
    set_progress(percentual, mensagem) quando se tem feedback do processo.

Modo 2 — TEMPORIZADOR:
    start_timer(segundos) — a loader vai de 0% a 100% no tempo dado.
    Ideal para processos sem feedback (ex: conversao Docling).

Modo 3 — ETAPAS ESTIMADAS:
    start_staged(segundos_totais, num_etapas)
    Divide o tempo total pelas etapas. A loader sobe gradativamente ate o
    limite de cada etapa. Ao receber hud_stage_done (SignalManager), pula
    imediatamente para o proximo patamar e continua subindo.
"""

from __future__ import annotations

from PySide6.QtCore import Qt, QTimer, QRectF
from PySide6.QtGui import QColor, QFont, QLinearGradient, QPainter, QPainterPath, QPen
from PySide6.QtWidgets import QWidget

from resources.styles.AppStyles import AppStyles
from core.manager.SignalManager import SignalManager


class HudCircularRingsLoader(QWidget):
    """
    Overlay de carregamento com 3 modos de progresso.

    Modos de operacao:
        - Padrao (set_progress): controle manual.
        - Modo 2 (start_timer): progresso automatico por tempo.
        - Modo 3 (start_staged): progresso automatico por etapas.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.progress = 0.0
        self.phase = 0
        self.message = "Processando..."

        accent = AppStyles.hud_accent_color()
        accent_qcolor = QColor(accent) if QColor.isValidColor(accent) else QColor(212, 168, 83)
        bright_qcolor = QColor(232, 200, 120)
        self.rings = [
            {"radius": 82, "width": 6, "speed": 2.0, "angle": 0, "segments": 10, "seg_span": 16, "seg_gap": 18,
             "color": accent_qcolor},
            {"radius": 62, "width": 5, "speed": -3.2, "angle": 150, "segments": 2, "seg_span": 120, "seg_gap": 60,
             "color": QColor(33, 150, 243, 220)},
            {"radius": 45, "width": 4, "speed": 5.4, "angle": 45, "segments": 14, "seg_span": 10, "seg_gap": 12,
             "color": bright_qcolor},
        ]
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.setAttribute(Qt.WidgetAttribute.WA_NoSystemBackground, False)
        self.hide()
        self._animate_timer = QTimer(self)
        self._animate_timer.timeout.connect(self._animate)
        self._animate_timer.start(16)

        # Controles dos modos automaticos
        self._mode: int = 1  # 1=manual, 2=timer, 3=staged
        self._auto_timer = QTimer(self)
        self._auto_timer.timeout.connect(self._auto_tick)

        # Modo 2 (timer)
        self._timer_duration: float = 10.0   # segundos totais
        self._timer_elapsed: float = 0.0

        # Modo 3 (staged)
        self._stages_total: int = 1
        self._stage_current: int = 0
        self._stage_progress: float = 0.0
        self._stage_pct_per_stage: float = 100.0

        # Conecta sinal de etapa concluida
        SignalManager.instance().hud_stage_done.connect(self._on_stage_done)

    def set_progress(self, value: float, message: str = ""):
        """Modo 1: Define progresso manualmente (0.0 a 100.0)."""
        self._mode = 1
        self._auto_timer.stop()
        self.progress = max(0.0, min(100.0, float(value)))
        if message:
            self.message = message
        self.update()

    def start_timer(self, seconds: float, message: str = ""):
        """
        Modo 2: Inicia progresso automatico que vai de 0% a 100%
        no numero de segundos especificado.
        A progressao mostra duas casas decimais (ex: 1.23%).
        """
        self._mode = 2
        self._timer_duration = max(0.1, float(seconds))
        self._timer_elapsed = 0.0
        self.progress = 0.0
        if message:
            self.message = message
        # tick a cada 50ms para progressao suave com decimais
        self._auto_timer.start(50)
        self.update()

    def start_staged(self, total_seconds: float, num_stages: int, message: str = ""):
        """
        Modo 3: Inicia progresso automatico dividido em etapas.

        Args:
            total_seconds: Tempo total estimado em segundos.
            num_stages: Numero de etapas.
            message: Mensagem inicial.
        """
        self._mode = 3
        self._timer_duration = max(0.1, float(total_seconds))
        self._stages_total = max(1, num_stages)
        self._stage_current = 0
        self._stage_progress = 0.0
        self._stage_pct_per_stage = 100.0 / self._stages_total
        self.progress = 0.0
        if message:
            self.message = message
        # tick a cada 50ms para progressao suave com decimais
        self._auto_timer.start(50)
        self.update()

    def show_loader(self):
        """Exibe o loader."""
        self.raise_()
        self.show()
        self.update()

    def hide_loader(self):
        """Esconde o loader e para qualquer modo automatico."""
        self._auto_timer.stop()
        self._mode = 1
        self.hide()

    # ── Tick automatico ─────────────────────────────────────────────

    def _auto_tick(self):
        """Executado a cada 50ms nos modos 2 e 3."""
        tick_sec = 0.05  # 50ms

        if self._mode == 2:
            self._timer_elapsed += tick_sec
            pct = min(100.0, (self._timer_elapsed / self._timer_duration) * 100.0)
            self.progress = round(pct, 2)
            self._update_hud()
            if pct >= 100.0:
                self._auto_timer.stop()
            return

        if self._mode == 3:
            time_per_stage = self._timer_duration / self._stages_total
            self._stage_progress += tick_sec
            stage_factor = min(1.0, self._stage_progress / time_per_stage)
            base = self._stage_current * self._stage_pct_per_stage
            self.progress = round(min(100.0, base + (stage_factor * self._stage_pct_per_stage)), 2)
            self._update_hud()
            if self.progress >= 100.0:
                self._auto_timer.stop()
            return

    def _on_stage_done(self, stage_index: int):
        """
        Recebido via SignalManager quando uma etapa externa e concluida.
        Pula imediatamente para o inicio da proxima etapa.
        """
        if self._mode != 3 or not self.isVisible():
            return

        self._stage_current = min(stage_index + 1, self._stages_total - 1)
        self._stage_progress = 0.0

        self.progress = round(self._stage_current * self._stage_pct_per_stage, 2)
        self._update_hud()

        if self._stage_current >= self._stages_total - 1 and self.progress >= 100.0:
            self._auto_timer.stop()

    def _update_hud(self):
        """Atualiza o progresso no SignalManager (HUD central + ProgressBar)."""
        SignalManager.instance().hud_update.emit({
            "message": self.message,
            "progress": self.progress,
        })
        SignalManager.instance().progress_update.emit(self.progress)

    def _animate(self):
        if not self.isVisible():
            return
        self.phase = (self.phase + 1) % 360
        for ring in self.rings:
            ring["angle"] = (ring["angle"] + ring["speed"]) % 360
        self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.fillRect(self.rect(), QColor(0, 0, 0, 130))

        cx = self.width() // 2
        cy = self.height() // 2 - 20
        panel = QRectF(cx - 150, cy - 130, 300, 300)
        self._draw_panel(p, panel)

        center = panel.center().toPoint()
        for ring in self.rings:
            self._draw_ring(p, center, ring)

        accent_color = QColor(AppStyles.hud_accent_color())
        p.setPen(accent_color)
        p.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        p.drawText(QRectF(cx - 120, cy + 110, 240, 24), Qt.AlignmentFlag.AlignCenter, self.message)

        p.setPen(accent_color)
        p.setFont(QFont("Consolas", 16, QFont.Weight.Bold))
        p.drawText(QRectF(cx - 60, cy - 0, 120, 38), Qt.AlignmentFlag.AlignCenter, f"{self.progress:.2f}%")

        # Indicador de modo
        mode_labels = {1: "FEEDBACK", 2: "TIMER", 3: "ETAPAS"}
        p.setPen(QColor(140, 140, 140))
        p.setFont(QFont("Segoe UI", 8))
        p.drawText(QRectF(cx - 60, cy + 30, 120, 16), Qt.AlignmentFlag.AlignCenter, mode_labels.get(self._mode, ""))

    def _draw_panel(self, painter: QPainter, rect: QRectF):
        grad = QLinearGradient(rect.topLeft(), rect.bottomLeft())
        grad.setColorAt(0.0, QColor(37, 37, 38, 245))
        grad.setColorAt(1.0, QColor(18, 18, 18, 245))
        path = QPainterPath()
        path.addRoundedRect(rect, 22, 22)
        painter.setPen(QPen(QColor(62, 62, 66, 220), 1))
        painter.setBrush(grad)
        painter.drawPath(path)

    def _draw_ring(self, painter: QPainter, center, ring):
        painter.setBrush(Qt.BrushStyle.NoBrush)
        trail_pen = QPen(QColor(45, 45, 48, 200), ring["width"])
        painter.setPen(trail_pen)
        painter.drawEllipse(center, ring["radius"], ring["radius"])

        for i in range(ring["segments"]):
            start_deg = ring["angle"] + i * (ring["seg_span"] + ring["seg_gap"])
            start = int((90 - start_deg) * 16)
            span = -int(ring["seg_span"] * 16)
            pulse = ((self.phase + i * 17) % 120) / 120.0
            alpha = int(70 + 170 * pulse)
            c = ring["color"]
            color = QColor(c.red(), c.green(), c.blue(), alpha)
            painter.setPen(QPen(color, ring["width"], Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
            painter.drawArc(center.x() - ring["radius"], center.y() - ring["radius"], ring["radius"] * 2, ring["radius"] * 2, start, span)