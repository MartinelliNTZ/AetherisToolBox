# -*- coding: utf-8 -*-
"""
TecladorF — Plugin de automação de teclado
=============================================
Ao pressionar a tecla F, digita automaticamente uma string
caractere por caractere, com delay configurável.

Baseado no script teclador_f.py original.

Uso:
    1. Abra o plugin no Workspace
    2. Configure VALUE, startup_delay, interval_delay e HOTKEY
    3. Clique em "EXECUTAR" para ativar
    4. Pressione a tecla configurada (padrão: F) para digitar
    5. Pressione ESC para parar
"""

from __future__ import annotations

import time

from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QDoubleSpinBox, QGroupBox, QFormLayout, QMessageBox,
)

from core.model.BasePlugin import BasePlugin
from resources.widgets.SimplePrimaryButton import SimplePrimaryButton


class TecladorWorker(QThread):
    """
    Thread separada para escutar teclas e digitar.
    Não bloqueia a UI do Qt.
    """

    def __init__(
        self,
        value: str,
        hotkey: str,
        startup_delay: float,
        interval_delay: float,
        parent=None,
    ):
        super().__init__(parent)
        self._value = value
        self._hotkey = hotkey.lower()
        self._startup_delay = startup_delay
        self._interval_delay = interval_delay
        self._running = False

    def run(self):
        """
        Escuta a tecla configurada e digita a string quando pressionada.
        """
        try:
            import keyboard
            import pyautogui

            pyautogui.PAUSE = 0
            self._running = True

            print(
                f"[TecladorF] Pronto. "
                f"Tecla={self._hotkey.upper()}, "
                f"VALUE={self._value[:20]}..., "
                f"startup_delay={self._startup_delay}s, "
                f"interval_delay={self._interval_delay}s"
            )

            def type_value():
                if not self._running:
                    return
                time.sleep(self._startup_delay)
                count = 0
                for ch in self._value:
                    if not self._running:
                        break
                    pyautogui.typewrite(ch, interval=0)
                    time.sleep(self._interval_delay)
                    count += 1
                print(
                    f"[TecladorF] String digitada: "
                    f"{count} caracteres, "
                    f"tecla={self._hotkey.upper()}, "
                    f"VALUE={self._value[:30]}..."
                )

            keyboard.add_hotkey(
                self._hotkey,
                type_value,
                suppress=False,
                trigger_on_release=False,
            )
            keyboard.wait("esc")

        except ImportError as e:
            print(f"[TecladorF] ERRO: {e}. Instale: pip install pyautogui keyboard")
        except Exception as e:
            print(f"[TecladorF] ERRO inesperado: {e}")
        finally:
            self._running = False
            try:
                keyboard.unhook_all()
            except Exception:
                pass

    def stop(self):
        """Para o worker."""
        self._running = False


class TecladorF(BasePlugin):
    """
    Plugin de automação: digita uma string ao pressionar uma tecla.
    """

    # ── Valores padrão ────────────────────────────────────────────────
    DEFAULT_VALUE = "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"
    DEFAULT_HOTKEY = "f"
    DEFAULT_STARTUP_DELAY = 0.15
    DEFAULT_INTERVAL_DELAY = 0.01

    def __init__(self, parent=None):
        super().__init__(tool_key="TecladorF", parent=parent)
        self._worker: TecladorWorker | None = None
        self._running = False
        self._build_ui()
        self.logger.info("TecladorF carregado", code="TOOL_READY")

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

        # ── Título ────────────────────────────────────────────────────
        title = QLabel("Teclador F — Automação de Teclado")
        title.setObjectName("header_title")
        layout.addWidget(title)

        subtitle = QLabel(
            "Digita automaticamente uma string ao pressionar uma tecla.\n"
            "Use com cuidado — é uma automação de teclado."
        )
        subtitle.setObjectName("header_subtitle")
        layout.addWidget(subtitle)

        # ── Configurações ─────────────────────────────────────────────
        config_group = QGroupBox("Configurações")
        form = QFormLayout(config_group)

        # VALUE
        self._edit_value = QLineEdit(self.DEFAULT_VALUE)
        self._edit_value.setPlaceholderText("String a ser digitada...")
        form.addRow("VALUE:", self._edit_value)

        # HOTKEY
        self._edit_hotkey = QLineEdit(self.DEFAULT_HOTKEY)
        self._edit_hotkey.setMaxLength(1)
        self._edit_hotkey.setPlaceholderText("Tecla de atalho (ex: f)")
        form.addRow("HOTKEY:", self._edit_hotkey)

        # Startup Delay
        self._spin_startup = QDoubleSpinBox()
        self._spin_startup.setRange(0.0, 5.0)
        self._spin_startup.setSingleStep(0.05)
        self._spin_startup.setValue(self.DEFAULT_STARTUP_DELAY)
        self._spin_startup.setDecimals(3)
        form.addRow("Startup Delay (s):", self._spin_startup)

        # Interval Delay
        self._spin_interval = QDoubleSpinBox()
        self._spin_interval.setRange(0.0, 1.0)
        self._spin_interval.setSingleStep(0.005)
        self._spin_interval.setValue(self.DEFAULT_INTERVAL_DELAY)
        self._spin_interval.setDecimals(4)
        form.addRow("Interval Delay (s):", self._spin_interval)

        layout.addWidget(config_group)

        # ── Botão Executar ────────────────────────────────────────────
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        self._btn_executar = SimplePrimaryButton("EXECUTAR")
        self._btn_executar.clicked.connect(self._on_executar)
        btn_layout.addWidget(self._btn_executar)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)

        layout.addStretch()

    # ── Ações ─────────────────────────────────────────────────────────

    def _on_executar(self):
        """Inicia ou para o worker."""
        if self._running:
            self._stop_worker()
        else:
            self._start_worker()

    def _start_worker(self):
        """Valida e inicia o worker em thread separada."""
        value = self._edit_value.text().strip()
        if not value:
            QMessageBox.warning(self, "Aviso", "VALUE não pode estar vazio.")
            return

        hotkey = self._edit_hotkey.text().strip().lower()
        if not hotkey:
            QMessageBox.warning(self, "Aviso", "HOTKEY não pode estar vazia.")
            return

        startup_delay = self._spin_startup.value()
        interval_delay = self._spin_interval.value()

        self._worker = TecladorWorker(
            value=value,
            hotkey=hotkey,
            startup_delay=startup_delay,
            interval_delay=interval_delay,
        )
        self._worker.finished.connect(self._on_worker_finished)
        self._worker.start()

        self._btn_executar.setText("PARAR")
        self._set_inputs_enabled(False)

        print(
            f"[TecladorF] Worker iniciado: "
            f"VALUE={value[:30]}..., "
            f"tecla={hotkey.upper()}, "
            f"startup_delay={startup_delay}s, "
            f"interval_delay={interval_delay}s"
        )
        self.logger.info(
            "TecladorF iniciado",
            code="WORKER_START",
            value_length=len(value),
            value_preview=value[:30],
            hotkey=hotkey.upper(),
            startup_delay=startup_delay,
            interval_delay=interval_delay,
        )

    def _stop_worker(self):
        """Para o worker."""
        if self._worker:
            self._worker.stop()
            self._worker.quit()
            self._worker.wait(2000)
        self._on_worker_finished()

    def _on_worker_finished(self):
        """Callback quando o worker termina."""
        self._running = False
        self._worker = None
        self._btn_executar.setText("EXECUTAR")
        self._set_inputs_enabled(True)

        print("[TecladorF] Worker parado.")
        self.logger.info("TecladorF parado", code="WORKER_STOP")

    def _set_inputs_enabled(self, enabled: bool):
        """Habilita/desabilita inputs durante execução."""
        self._edit_value.setEnabled(enabled)
        self._edit_hotkey.setEnabled(enabled)
        self._spin_startup.setEnabled(enabled)
        self._spin_interval.setEnabled(enabled)