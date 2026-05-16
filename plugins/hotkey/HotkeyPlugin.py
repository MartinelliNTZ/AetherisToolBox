# -*- coding: utf-8 -*-
"""
HotkeyPlugin — Plugin de automação de teclado
===============================================
Ao pressionar a tecla configurada, executa a operação configurada:
- Modo "Teclar Texto": digita automaticamente uma string caractere por caractere
- Modo "Teclar Atalho": executa uma sequência de teclas/atalhos N vezes

Uso:
    1. Abra o plugin no Workspace
    2. Configure o modo, valor, atraso inicial, intervalo e tecla de atalho
    3. Clique em "EXECUTAR" para ativar
    4. Pressione a tecla configurada (padrão: F) para executar
    5. Clique em "PARAR" para interromper
"""

from __future__ import annotations

import time

from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QGroupBox, QFormLayout, QFrame, QComboBox,
)

from core.config.LogUtils import LogUtils
from core.model.BasePlugin import BasePlugin
from core.manager.SignalManager import SignalManager
from core.enum.ToolKey import ToolKey
from resources.widgets.SimplePrimaryButton import SimplePrimaryButton
from resources.widgets.HotkeyCaptureLine import HotkeyCaptureLine
from resources.widgets.HotkeySequenceCapture import HotkeySequenceCapture
from resources.widgets.GridCheckBox import GridCheckBox
from resources.widgets.GridDoubleSpinBox import GridDoubleSpinBox


class HotkeyPlugin(BasePlugin):
    """
    Plugin de automação: executa ação ao pressionar uma tecla.
    Usa keyboard library diretamente (sem QThread) — a biblioteca
    já gerencia suas próprias threads para hooks globais.
    """

    # ── Valores padrão ────────────────────────────────────────────────
    DEFAULT_VALUE = "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"
    DEFAULT_HOTKEY = "f"
    DEFAULT_STARTUP_DELAY = 0.15
    DEFAULT_INTERVAL_DELAY = 0.01
    DEFAULT_SEQUENCE_INTERVAL = 1.0
    DEFAULT_SEQUENCE_REPEAT = 3

    MODE_TEXT = "Teclar Texto"
    MODE_HOTKEY = "Teclar Atalho"

    def __init__(self, parent=None):
        super().__init__(tool_key=ToolKey.TECLADOR_F.value, parent=parent)
        self._running = False
        self._hotkey_handler = None
        self._build_ui()
        self.load_prefs()
        self._update_mode_visibility()
        self.logger.info("HotkeyPlugin carregado", code="TOOL_READY")

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 10, 18, 10)
        layout.setSpacing(8)

        # ── Título ────────────────────────────────────────────────────
        title = QLabel("Teclador F — Automação de Teclado")
        title.setObjectName("header_title")
        layout.addWidget(title)

        # ── Separator ──
        sep = QFrame()
        sep.setObjectName("separator")
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setFixedHeight(1)
        layout.addWidget(sep)

        # ── Botões de Ação ────────────────────────────────────────────
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(6)
        btn_layout.addStretch()
        self._btn_executar = SimplePrimaryButton("EXECUTAR")
        self._btn_executar.clicked.connect(self._on_executar)
        btn_layout.addWidget(self._btn_executar)
        layout.addLayout(btn_layout)

        # ── Seletor de Modo ───────────────────────────────────────────
        self._combo_mode = QComboBox()
        self._combo_mode.addItem(self.MODE_TEXT)
        self._combo_mode.addItem(self.MODE_HOTKEY)
        self._combo_mode.setObjectName("mode_selector")
        self._combo_mode.currentTextChanged.connect(self._on_mode_changed)
        layout.addWidget(self._combo_mode)

        # ── Configurações ─────────────────────────────────────────────
        config_group = QGroupBox("Configurações")
        config_layout = QVBoxLayout(config_group)

        # ── Stack de modos ────────────────────────────────────────────
        self._stack_text = QWidget()
        self._stack_text.setObjectName("stack_text")
        text_layout = QVBoxLayout(self._stack_text)
        text_layout.setContentsMargins(0, 0, 0, 0)

        # Modo Texto — form
        text_form = QFormLayout()

        # Valor
        self._edit_value = QLineEdit(self.DEFAULT_VALUE)
        self._edit_value.setPlaceholderText("Texto a ser digitado...")
        self._edit_value.textChanged.connect(self._mark_dirty)
        text_form.addRow("Valor:", self._edit_value)

        text_layout.addLayout(text_form)

        # ── Stack: Modo Atalho ────────────────────────────────────────
        self._stack_hotkey = QWidget()
        self._stack_hotkey.setObjectName("stack_hotkey")
        hotkey_layout = QVBoxLayout(self._stack_hotkey)
        hotkey_layout.setContentsMargins(0, 0, 0, 0)
        hotkey_layout.setSpacing(6)

        # Sequência de teclas
        seq_label = QLabel("Sequência de Teclas:")
        seq_label.setObjectName("subsection_label")
        hotkey_layout.addWidget(seq_label)

        self._edit_sequence = HotkeySequenceCapture()
        self._edit_sequence.sequenceChanged.connect(self._mark_dirty)
        self._edit_sequence.setObjectName("sequence_capture")
        hotkey_layout.addWidget(self._edit_sequence)

        # GridDoubleSpinBox: atraso, intervalo, repetições
        self._grid_numbers = GridDoubleSpinBox(
            config={
                "atraso": {
                    "label": "Atraso inicial",
                    "description": "Tempo de espera antes de começar (s)",
                    "decimal": 1,
                    "default": self.DEFAULT_STARTUP_DELAY,
                    "min": 0.0,
                    "max": 30.0,
                    "step": 0.1,
                    "suffix": "s",
                },
                "intervalo": {
                    "label": "Intervalo entre teclas",
                    "description": "Tempo entre pressionar cada tecla da sequência (s)",
                    "decimal": 1,
                    "default": self.DEFAULT_SEQUENCE_INTERVAL,
                    "min": 0.0,
                    "max": 60.0,
                    "step": 0.1,
                    "suffix": "s",
                },
                "repeticoes": {
                    "label": "Número de vezes",
                    "description": "Quantas vezes repetir a sequência inteira",
                    "decimal": 0,
                    "default": self.DEFAULT_SEQUENCE_REPEAT,
                    "min": 1,
                    "max": 9999,
                    "step": 1,
                },
            },
        )
        self._grid_numbers.changed.connect(self._mark_dirty)
        self._grid_numbers.setObjectName("grid_numeric")
        hotkey_layout.addWidget(self._grid_numbers)

        # Adiciona stacks ao config group
        config_layout.addWidget(self._stack_text)
        config_layout.addWidget(self._stack_hotkey)

        # ── Tecla de atalho (comum aos dois modos) ────────────────────
        hotkey_form = QFormLayout()
        self._edit_hotkey = HotkeyCaptureLine(default_key=self.DEFAULT_HOTKEY)
        self._edit_hotkey.keyChanged.connect(self._mark_dirty)
        hotkey_form.addRow("Tecla gatilho:", self._edit_hotkey)
        config_layout.addLayout(hotkey_form)

        # ── Grid: Bloquear propagação ────────────────────────────────
        self._grid_suppress = GridCheckBox(
            config={
                "suppress": {
                    "label": "Bloquear propagação (suppress)",
                    "description": (
                        "Impede que a tecla de atalho seja transmitida "
                        "para outros programas. Ative se a tecla estiver "
                        "acionando comandos indesejados no app em foco."
                    ),
                    "default": True,
                },
            },
            num_columns=1,
        )
        self._grid_suppress.setObjectName("group_suppress")
        self._grid_suppress.changed.connect(self._mark_dirty)
        config_layout.addWidget(self._grid_suppress)

        layout.addWidget(config_group, 1)

    # ── Modo ──────────────────────────────────────────────────────────

    def _on_mode_changed(self, mode: str):
        """Atualiza visibilidade dos stacks conforme o modo."""
        self._update_mode_visibility()
        self._mark_dirty()

    def _update_mode_visibility(self):
        """Exibe/esconde os stacks conforme o modo selecionado."""
        mode = self._combo_mode.currentText()
        is_text = mode == self.MODE_TEXT
        self._stack_text.setVisible(is_text)
        self._stack_hotkey.setVisible(not is_text)

    # ── Ações ─────────────────────────────────────────────────────────

    def _on_executar(self):
        """Inicia ou para o worker."""
        if self._running:
            self._stop_worker()
        else:
            self._start_worker()

    def _start_worker(self):
        """Valida e registra o hook de teclado global."""
        from utils.MessageBox import MessageBox

        mode = self._combo_mode.currentText()

        # Validação conforme o modo
        if mode == self.MODE_TEXT:
            value = self._edit_value.text().strip()
            if not value:
                MessageBox.show_warning("Valor não pode estar vazio.", title="Aviso")
                return

        hotkey = self._edit_hotkey.captured_key()
        if not hotkey:
            MessageBox.show_warning("Tecla gatilho não pode estar vazia.", title="Aviso")
            return

        if mode == self.MODE_HOTKEY:
            sequence = self._edit_sequence.captured_sequence()
            if not sequence:
                MessageBox.show_warning(
                    "Sequência de teclas não pode estar vazia. "
                    "Adicione pelo menos uma tecla.",
                    title="Aviso",
                )
                return

        suppress = bool(self._grid_suppress.all.get("suppress", True))

        # Fecha hooks anteriores se houver
        self._clean_hooks()

        # Monta callback conforme o modo
        if mode == self.MODE_TEXT:
            value = self._edit_value.text().strip()
            startup_delay = self.DEFAULT_STARTUP_DELAY
            interval_delay = self.DEFAULT_INTERVAL_DELAY
        else:
            startup_delay = self._grid_numbers.get("atraso")
            interval_delay = self._grid_numbers.get("intervalo")
            repeat_count = int(self._grid_numbers.get("repeticoes"))

        def type_value():
            """Callback chamado pela keyboard library na thread de hook."""
            if not self._running:
                return
            time.sleep(startup_delay)

            if mode == self.MODE_TEXT:
                # Modo texto: digita caractere por caractere
                count = 0
                for ch in value:
                    if not self._running:
                        break
                    try:
                        import pyautogui
                        pyautogui.typewrite(ch, interval=0)
                    except Exception:
                        break
                    time.sleep(interval_delay)
                    count += 1
                QTimer.singleShot(0, lambda: self._on_typed(count, hotkey))
            else:
                # Modo atalho: executa sequência N vezes
                import pyautogui
                from keyboard import send as kb_send

                for rep in range(repeat_count):
                    if not self._running:
                        break
                    for key_name in sequence:
                        if not self._running:
                            break
                        try:
                            # Tenta como combinação (ex: ctrl+c) ou tecla única
                            if "+" in key_name.strip("+"):
                                # Combinação como ctrl+c, alt+tab
                                pyautogui.hotkey(*key_name.replace(" ", "").split("+"))
                            else:
                                kb_send(key_name)
                        except Exception as e:
                            self.logger.error(
                                "Erro ao pressionar tecla",
                                code="KEY_SEND_ERR",
                                key=key_name,
                                error=str(e),
                            )
                            break
                        time.sleep(interval_delay)
                    if not self._running:
                        break

                QTimer.singleShot(
                    0,
                    lambda: self._on_sequence_done(repeat_count, len(sequence), hotkey),
                )

        try:
            import keyboard
            self._hotkey_handler = keyboard.add_hotkey(
                hotkey,
                type_value,
                suppress=suppress,
                trigger_on_release=False,
            )
        except ImportError as e:
            self.logger.error("Bibliotecas nao encontradas", code="IMPORT_ERR", error=str(e))
            SignalManager.instance().console_message.emit(
                f"HotkeyPlugin erro: {e}. Instale: pip install pyautogui keyboard"
            )
            return
        except Exception as e:
            self.logger.error("Falha ao registrar hotkey", code="HOTKEY_ERR", error=str(e))
            SignalManager.instance().console_message.emit(
                f"HotkeyPlugin erro ao registrar hotkey: {e}"
            )
            return

        self._running = True
        self._btn_executar.setText("PARAR")
        self._set_inputs_enabled(False)
        self.save_prefs()

        SignalManager.instance().console_message.emit(
            f"HotkeyPlugin iniciado — modo {mode}, "
            f"tecla {hotkey.upper()}"
        )
        self.logger.info(
            "HotkeyPlugin iniciado",
            code="WORKER_START",
            mode=mode,
            hotkey=hotkey.upper(),
            startup_delay=startup_delay,
            suppress=suppress,
        )

    def _on_typed(self, count: int, hotkey: str) -> None:
        """Recebe notificação na thread da UI após digitação (modo texto)."""
        if count > 0:
            SignalManager.instance().console_message.emit(
                f"HotkeyPlugin digitou {count} caracteres (tecla {hotkey.upper()})"
            )

    def _on_sequence_done(self, repeats: int, keys_count: int, hotkey: str) -> None:
        """Recebe notificação na thread da UI após executar sequência (modo atalho)."""
        if repeats > 0:
            SignalManager.instance().console_message.emit(
                f"HotkeyPlugin executou {repeats}x sequência de {keys_count} teclas "
                f"(tecla {hotkey.upper()})"
            )

    def _stop_worker(self):
        """Remove o hook de teclado."""
        self._running = False
        self._clean_hooks()
        self._on_executar_finished()

    def _clean_hooks(self):
        """Remove hooks registrados."""
        try:
            import keyboard
            if self._hotkey_handler is not None:
                try:
                    keyboard.remove_hotkey(self._hotkey_handler)
                except Exception:
                    pass
                self._hotkey_handler = None
            keyboard.unhook_all()
        except ImportError:
            pass

    def _on_executar_finished(self):
        """Callback quando a execução termina."""
        self._btn_executar.setText("EXECUTAR")
        self._set_inputs_enabled(True)

        SignalManager.instance().console_message.emit("HotkeyPlugin parado")
        self.logger.info("HotkeyPlugin parado", code="WORKER_STOP")

    def _set_inputs_enabled(self, enabled: bool):
        """Habilita/desabilita inputs durante execução."""
        self._edit_value.setEnabled(enabled)
        self._edit_hotkey.setEnabled(enabled)
        self._edit_sequence.setEnabled(enabled)
        self._grid_numbers.setEnabled(enabled)
        self._grid_suppress.setEnabled(enabled)
        self._combo_mode.setEnabled(enabled)

    # ── Preferences ─────────────────────────────────────────────────

    def load_prefs(self) -> None:
        """Carrega preferências salvas e aplica nos widgets."""
        # Modo
        saved_mode = self.preferences.get("mode")
        if saved_mode is not None:
            idx = self._combo_mode.findText(saved_mode)
            if idx >= 0:
                self._combo_mode.setCurrentIndex(idx)

        # Modo texto
        value = self.preferences.get("value")
        if value is not None:
            self._edit_value.setText(value)

        # Tecla gatilho
        hotkey = self.preferences.get("hotkey")
        if hotkey is not None:
            self._edit_hotkey.set_captured_key(hotkey)

        # Atraso e intervalo (modo texto) — compatibilidade retroativa
        startup_delay = self.preferences.get("startup_delay")
        if startup_delay is not None:
            self._grid_numbers.set("atraso", float(startup_delay), block_signals=True)

        interval_delay = self.preferences.get("interval_delay")
        if interval_delay is not None:
            pass  # manter default do grid

        # Modo atalho — campos específicos
        sequence = self.preferences.get("sequence")
        if sequence is not None and isinstance(sequence, list):
            self._edit_sequence.set_captured_sequence(sequence)

        seq_interval = self.preferences.get("seq_interval")
        if seq_interval is not None:
            self._grid_numbers.set("intervalo", float(seq_interval), block_signals=True)

        seq_repeat = self.preferences.get("seq_repeat")
        if seq_repeat is not None:
            self._grid_numbers.set("repeticoes", float(seq_repeat), block_signals=True)

        atraso = self.preferences.get("atraso")
        if atraso is not None:
            self._grid_numbers.set("atraso", float(atraso), block_signals=True)

        suppress = self.preferences.get("suppress")
        if suppress is not None:
            self._grid_suppress.set_all({"suppress": bool(suppress)})

    def save_prefs(self) -> None:
        """Lê os widgets e persiste as preferências."""
        self.preferences["mode"] = self._combo_mode.currentText()
        self.preferences["value"] = self._edit_value.text()
        self.preferences["hotkey"] = self._edit_hotkey.captured_key()
        self.preferences["suppress"] = bool(
            self._grid_suppress.all.get("suppress", True)
        )

        # Salva todos os valores do GridDoubleSpinBox
        vals = self._grid_numbers.values
        self.preferences["atraso"] = vals.get("atraso", self.DEFAULT_STARTUP_DELAY)
        self.preferences["seq_interval"] = vals.get("intervalo", self.DEFAULT_SEQUENCE_INTERVAL)
        self.preferences["seq_repeat"] = vals.get("repeticoes", self.DEFAULT_SEQUENCE_REPEAT)

        self.preferences["sequence"] = self._edit_sequence.captured_sequence()

    # ── Dirty tracking ──────────────────────────────────────────────

    _dirty: bool = False

    def _mark_dirty(self) -> None:
        """Marca que as preferências precisam ser salvas."""
        self._dirty = True