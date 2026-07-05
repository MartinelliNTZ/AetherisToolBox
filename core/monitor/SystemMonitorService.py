# -*- coding: utf-8 -*-
"""
SystemMonitorService — Serviço de polling de CPU/RAM via psutil
================================================================
Singleton que polla CPU e RAM em intervalo configurável e emite
sinais com os dados atualizados. Usa SignalManager.system_stats_updated
para propagar as estatísticas.

Uso:
    monitor = SystemMonitorService(interval_ms=2000)
    monitor.stats_updated.connect(self._on_stats)
    monitor.start()
    # ...
    monitor.stop()

Sinais:
    stats_updated(dict) — emitido a cada ciclo:
        {
            "cpu": 45.2,
            "ram": 72.8,
            "cpu_tooltip": "CPU: 45.2% (8 cores físicos, 16 lógicos)",
            "ram_tooltip": "RAM: 72.8% (23.4 GB / 32.0 GB usados)",
        }
"""

from __future__ import annotations

from typing import Optional

import psutil
from PySide6.QtCore import QObject, QTimer, Signal

from core.config.LogUtils import LogUtils
from core.enum.ToolKey import ToolKey
from core.manager.SignalManager import SignalManager
from utils.FormatUtils import FormatUtils


class SystemMonitorService(QObject):
    """
    Serviço de monitoramento do sistema via psutil.

    Polla CPU e RAM em background via QTimer e emite stats_updated
    com os valores formatados. Também propaga via SignalManager
    para outros componentes interessados.
    """

    stats_updated = Signal(dict)

    def __init__(self, interval_ms: int = 2000, parent=None):
        super().__init__(parent)
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._poll)
        self._interval = interval_ms
        self._logger = LogUtils(
            tool=ToolKey.SYSTEM_MONITOR.value,
            class_name="SystemMonitorService",
        )

        # Cache para cpu_percent (precisa de chamada anterior para funcionar)
        psutil.cpu_percent(interval=None)

    # ── API pública ────────────────────────────────────────────────

    def start(self) -> None:
        """Inicia o polling periódico."""
        self._poll()  # primeira execução imediata
        self._timer.start(self._interval)
        self._logger.info(
            "System monitor started",
            code="MONITOR_START",
            interval_ms=self._interval,
        )

    def stop(self) -> None:
        """Para o polling."""
        self._timer.stop()
        self._logger.info("System monitor stopped", code="MONITOR_STOP")

    def poll_once(self) -> dict:
        """
        Executa uma leitura manual e retorna o dict.

        Returns:
            dict com cpu, ram, cpu_tooltip, ram_tooltip.
        """
        data = self._collect_stats()
        return data

    @property
    def is_running(self) -> bool:
        """True se o timer está ativo."""
        return self._timer.isActive()

    # ── Internos ───────────────────────────────────────────────────

    def _collect_stats(self) -> dict:
        """Coleta e formata estatísticas do sistema."""
        # CPU
        cpu = psutil.cpu_percent(interval=None)
        cpu_count_phys = psutil.cpu_count(logical=False) or 0
        cpu_count_log = psutil.cpu_count(logical=True) or 0
        cpu_tooltip = (
            f"CPU: {cpu:.1f}% "
            f"({cpu_count_phys} cores físicos, {cpu_count_log} lógicos)"
        )

        # RAM
        mem = psutil.virtual_memory()
        ram = mem.percent
        used_str = FormatUtils.format_size(mem.used)
        total_str = FormatUtils.format_size(mem.total)
        ram_tooltip = (
            f"RAM: {ram:.1f}% "
            f"({used_str} / {total_str} usados)"
        )

        return {
            "cpu": cpu,
            "ram": ram,
            "cpu_tooltip": cpu_tooltip,
            "ram_tooltip": ram_tooltip,
        }

    def _poll(self) -> None:
        """Polling interno: coleta e emite sinais."""
        try:
            data = self._collect_stats()
            self.stats_updated.emit(data)
            SignalManager.instance().system_stats_updated.emit(data)
        except Exception as e:
            self._logger.error(
                "Error polling system stats",
                code="MONITOR_POLL_ERR",
                error=str(e),
            )