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

import json
import random
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict

from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QGroupBox,
    QDialog, QListWidget, QPushButton, QHBoxLayout, QLineEdit,
)

from core.enum.ToolKey import ToolKey
from core.model.BasePlugin import BasePlugin
from core.manager.SignalManager import SignalManager
from resources.widgets.ExecutionButtons import ExecutionButtons
from resources.widgets.HotkeyCaptureLine import HotkeyCaptureLine, _to_display
from resources.widgets.HotkeySequenceCapture import HotkeySequenceCapture
from resources.widgets.GridCheckBox import GridCheckBox
from resources.widgets.GridDoubleSpinBox import GridDoubleSpinBox
from resources.widgets.GridLineEdit import GridLineEdit
from resources.widgets.SimpleComboBox import SimpleComboBox


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
        super().__init__(
            tool_key=ToolKey.HOTKEY_PLUGIN.value,
            parent=parent,
            title="Teclador F — Automação de Teclado",
        )
        self._running = False
        self._hotkey_handler = None
        self._update_mode_visibility()
        self.logger.info("HotkeyPlugin carregado", code="TOOL_READY")

    def _build_ui(self):
        """Sobrescreve _build_ui do BasePlugin."""
        super()._build_ui()

        # ── Botões de Ação ────────────────────────────────────────────
        self._btns = ExecutionButtons(self)
        self._btns.setup({
            "salvar": {
                "text": "SALVAR CONFIG",
                "callback": self._on_salvar_config,
                "type": "secondary",
                "description": "Salva a configuração atual em disco",
            },
            "ler": {
                "text": "LER CONFIG",
                "callback": self._on_ler_config,
                "type": "secondary",
                "description": "Carrega uma configuração salva anteriormente",
            },
            "executar": {
                "text": "EXECUTAR",
                "callback": self._on_executar,
                "type": "primary",
                "description": "Inicia a execução com a tecla configurada",
            },
        })
        self.main_layout.addWidget(self._btns)

        # ── Seletor de Modo (SimpleComboBox) ──────────────────────────
        self._combo_mode = SimpleComboBox(
            items={self.MODE_TEXT: self.MODE_TEXT, self.MODE_HOTKEY: self.MODE_HOTKEY},
            on_item_changed=self._on_mode_changed,
            parent=self,
        )
        self.main_layout.addWidget(self._combo_mode)

        # ── Configurações ─────────────────────────────────────────────
        config_group = QGroupBox("Configurações")
        config_layout = QVBoxLayout(config_group)

        # ── Stack de modos ────────────────────────────────────────────
        self._stack_text = QWidget()
        self._stack_text.setObjectName("stack_text")
        text_layout = QVBoxLayout(self._stack_text)
        text_layout.setContentsMargins(0, 0, 0, 0)

        # Modo Texto — GridLineEdit
        self._grid_text = GridLineEdit(
            config={
                "valor": {
                    "label": "Valor",
                    "description": "Texto a ser digitado",
                    "default": self.DEFAULT_VALUE,
                    "placeholder": "Texto a ser digitado...",
                },
            },
        )
        self._grid_text.changed.connect(self._mark_dirty)
        text_layout.addWidget(self._grid_text)

        # Modo Texto — GridDoubleSpinBox (atraso inicial e intervalo)
        self._grid_text_numbers = GridDoubleSpinBox(
            config={
                "atraso": {
                    "label": "Atraso inicial",
                    "description": "Tempo de espera antes de começar (s)",
                    "decimal": 1,
                    "default": self.DEFAULT_STARTUP_DELAY,
                    "suffix": "s",
                },
                "intervalo": {
                    "label": "Intervalo entre caracteres",
                    "description": "Tempo entre digitar cada caractere (s)",
                    "decimal": 2,
                    "default": self.DEFAULT_INTERVAL_DELAY,
                    "suffix": "s",
                },
            },
        )
        self._grid_text_numbers.changed.connect(self._mark_dirty)
        text_layout.addWidget(self._grid_text_numbers)

        # ── Stack: Modo Atalho ────────────────────────────────────────
        self._stack_hotkey = QWidget()
        self._stack_hotkey.setObjectName("stack_hotkey")
        hotkey_layout = QVBoxLayout(self._stack_hotkey)
        hotkey_layout.setContentsMargins(0, 0, 0, 0)
        hotkey_layout.setSpacing(6)

        # Sequência de teclas (com title embutido)
        self._edit_sequence = HotkeySequenceCapture(
            title="Sequência de Teclas:",
        )
        self._edit_sequence.sequenceChanged.connect(self._on_sequence_changed)
        self._edit_sequence.setObjectName("sequence_capture")
        hotkey_layout.addWidget(self._edit_sequence)

        # Modo Atalho — GridDoubleSpinBox: atraso, intervalo, aleatoriedade, repetições
        self._grid_hotkey_numbers = GridDoubleSpinBox(
            config={
                "atraso": {
                    "label": "Atraso inicial",
                    "description": "Tempo de espera antes de começar (s)",
                    "decimal": 1,
                    "default": self.DEFAULT_STARTUP_DELAY,
                    "suffix": "s",
                },
                "intervalo": {
                    "label": "Intervalo entre teclas",
                    "description": "Tempo base entre pressionar cada tecla (s). "
                                   "O valor final será intervalo + aleatório(0, aleatoriedade).",
                    "decimal": 2,
                    "default": self.DEFAULT_SEQUENCE_INTERVAL,
                    "suffix": "s",
                },
                "aleatoriedade": {
                    "label": "Aleatoriedade",
                    "description": "Fator aleatório adicionado ao intervalo (0 = desligado). "
                                   "Ex: intervalo=1, aleatoriedade=1 → delay entre 1.00 e 2.00s.",
                    "decimal": 2,
                    "default": 0.0,
                    "suffix": "s",
                },
                "repeticoes": {
                    "label": "Número de vezes",
                    "description": "Quantas vezes repetir a sequência inteira",
                    "decimal": 0,
                    "default": self.DEFAULT_SEQUENCE_REPEAT,
                },
            },
        )
        self._grid_hotkey_numbers.changed.connect(self._mark_dirty)
        self._grid_hotkey_numbers.setObjectName("grid_hotkey_numeric")
        hotkey_layout.addWidget(self._grid_hotkey_numbers)

        # Adiciona stacks ao config group
        config_layout.addWidget(self._stack_text)
        config_layout.addWidget(self._stack_hotkey)

        # ── Tecla de atalho (comum aos dois modos) ────────────────────
        self._edit_hotkey = HotkeyCaptureLine(
            default_key=self.DEFAULT_HOTKEY,
            label="Tecla gatilho:",
        )
        self._edit_hotkey.keyChanged.connect(self._mark_dirty)
        config_layout.addWidget(self._edit_hotkey)

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

        self.main_layout.addWidget(config_group, 1)

    # ── Modo ──────────────────────────────────────────────────────────

    def _on_sequence_changed(self, keys: list[str]):
        """Quando a sequência de teclas muda, exibe no console."""
        if not keys:
            SignalManager.instance().console_message.emit(
                "HotkeyPlugin sequência limpa"
            )
        else:
            display = ", ".join(_to_display(k) for k in keys)
            SignalManager.instance().console_message.emit(
                f"HotkeyPlugin sequência ({len(keys)}): {display}"
            )
        self._mark_dirty()

    def _on_mode_changed(self, mode: str):
        """Atualiza visibilidade dos stacks conforme o modo."""
        self._update_mode_visibility()
        self._mark_dirty()

    def _update_mode_visibility(self):
        """Exibe/esconde os stacks conforme o modo selecionado."""
        mode = self._combo_mode.current_value
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

        mode = self._combo_mode.current_value

        # Validação conforme o modo
        if mode == self.MODE_TEXT:
            value = self._grid_text.get("valor").strip()
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

        # Reseta a barra de progresso
        SignalManager.instance().progress_update.emit(0.0)

        # Monta callback conforme o modo
        if mode == self.MODE_TEXT:
            value = self._grid_text.get("valor").strip()
            startup_delay = self._grid_text_numbers.get("atraso")
            interval_delay = self._grid_text_numbers.get("intervalo")
        else:
            startup_delay = self._grid_hotkey_numbers.get("atraso")
            interval_delay = self._grid_hotkey_numbers.get("intervalo")
            aleatoriedade = self._grid_hotkey_numbers.get("aleatoriedade")
            repeat_count = int(self._grid_hotkey_numbers.get("repeticoes"))

        def type_value():
            """Callback chamado pela keyboard library na thread de hook."""
            if not self._running:
                return
            time.sleep(startup_delay)

            if mode == self.MODE_TEXT:
                count = 0
                total_chars = len(value)
                for ch in value:
                    if not self._running:
                        break
                    try:
                        import pyautogui
                        pyautogui.typewrite(ch, interval=0)
                    except Exception:
                        break
                    count += 1
                    progress = (count / total_chars) * 100.0
                    SignalManager.instance().progress_update.emit(progress)
                    time.sleep(interval_delay)
                QTimer.singleShot(0, lambda: self._on_typed(count, hotkey))
            else:
                import pyautogui

                total_steps = repeat_count * len(sequence)
                step_index = 0

                for rep in range(repeat_count):
                    if not self._running:
                        break
                    for key_name in sequence:
                        if not self._running:
                            break
                        try:
                            display_name = _to_display(key_name)
                            SignalManager.instance().console_message.emit(
                                f"HotkeyPlugin pressionando: {display_name} "
                                f"(loop {rep + 1}/{repeat_count})"
                            )
                            if "+" in key_name.strip("+"):
                                parts = key_name.replace(" ", "").split("+")
                                pyautogui.hotkey(*parts)
                            else:
                                pyautogui.press(key_name)
                        except Exception as e:
                            self.logger.error(
                                "Erro ao pressionar tecla",
                                code="KEY_SEND_ERR",
                                key=key_name,
                                error=str(e),
                            )
                            SignalManager.instance().console_message.emit(
                                f"HotkeyPlugin erro ao pressionar {key_name}: {e}"
                            )
                            break
                        step_index += 1
                        progress = (step_index / total_steps) * 100.0
                        SignalManager.instance().progress_update.emit(progress)
                        actual_delay = interval_delay + random.uniform(0.0, aleatoriedade)
                        time.sleep(actual_delay)
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
            SignalManager.instance().progress_update.emit(0.0)
            return
        except Exception as e:
            self.logger.error("Falha ao registrar hotkey", code="HOTKEY_ERR", error=str(e))
            SignalManager.instance().console_message.emit(
                f"HotkeyPlugin erro ao registrar hotkey: {e}"
            )
            SignalManager.instance().progress_update.emit(0.0)
            return

        self._running = True
        self._btns["executar"].setText("PARAR")
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
        self._btns["executar"].setText("EXECUTAR")
        self._set_inputs_enabled(True)
        SignalManager.instance().progress_update.emit(100.0)
        QTimer.singleShot(500, lambda: SignalManager.instance().progress_update.emit(0.0))

        SignalManager.instance().console_message.emit("HotkeyPlugin parado")
        self.logger.info("HotkeyPlugin parado", code="WORKER_STOP")

    def _set_inputs_enabled(self, enabled: bool):
        """Habilita/desabilita inputs durante execução."""
        self._grid_text.setEnabled(enabled)
        self._grid_text_numbers.setEnabled(enabled)
        self._edit_hotkey.setEnabled(enabled)
        self._edit_sequence.setEnabled(enabled)
        self._grid_hotkey_numbers.setEnabled(enabled)
        self._grid_suppress.setEnabled(enabled)
        self._combo_mode.setEnabled(enabled)

    # ── Preferences ─────────────────────────────────────────────────

    def load_prefs(self) -> None:
        """Carrega preferências salvas e aplica nos widgets."""
        saved_mode = self.preferences.get("mode")
        if saved_mode is not None:
            self._combo_mode.current_value = saved_mode

        value = self.preferences.get("value")
        if value is not None:
            self._grid_text.set("valor", value, block_signals=True)

        hotkey = self.preferences.get("hotkey")
        if hotkey is not None:
            self._edit_hotkey.set_captured_key(hotkey)

        sequence = self.preferences.get("sequence")
        if sequence is not None and isinstance(sequence, list):
            self._edit_sequence.set_captured_sequence(sequence)

        seq_interval = self.preferences.get("seq_interval")
        if seq_interval is not None:
            self._grid_hotkey_numbers.set("intervalo", float(seq_interval), block_signals=True)

        aleatoriedade = self.preferences.get("aleatoriedade")
        if aleatoriedade is not None:
            self._grid_hotkey_numbers.set("aleatoriedade", float(aleatoriedade), block_signals=True)

        seq_repeat = self.preferences.get("seq_repeat")
        if seq_repeat is not None:
            self._grid_hotkey_numbers.set("repeticoes", float(seq_repeat), block_signals=True)

        atraso = self.preferences.get("atraso")
        if atraso is not None:
            self._grid_text_numbers.set("atraso", float(atraso), block_signals=True)
            self._grid_hotkey_numbers.set("atraso", float(atraso), block_signals=True)

        suppress = self.preferences.get("suppress")
        if suppress is not None:
            self._grid_suppress.set_all({"suppress": bool(suppress)})

    def save_prefs(self) -> None:
        """Lê os widgets e persiste as preferências."""
        self.preferences["mode"] = self._combo_mode.current_value
        self.preferences["value"] = self._grid_text.get("valor")
        self.preferences["hotkey"] = self._edit_hotkey.captured_key()
        self.preferences["suppress"] = bool(
            self._grid_suppress.all.get("suppress", True)
        )

        vals = self._grid_hotkey_numbers.values
        text_vals = self._grid_text_numbers.values
        self.preferences["atraso"] = vals.get("atraso", self.DEFAULT_STARTUP_DELAY)
        self.preferences["text_intervalo"] = text_vals.get("intervalo", self.DEFAULT_INTERVAL_DELAY)
        self.preferences["seq_interval"] = vals.get("intervalo", self.DEFAULT_SEQUENCE_INTERVAL)
        self.preferences["aleatoriedade"] = vals.get("aleatoriedade", 0.0)
        self.preferences["seq_repeat"] = vals.get("repeticoes", self.DEFAULT_SEQUENCE_REPEAT)

        self.preferences["sequence"] = self._edit_sequence.captured_sequence()

    # ── Config Dir ─────────────────────────────────────────────────

    @staticmethod
    def _get_config_dir() -> Path:
        """Retorna o diretório config/data/hotkey/."""
        config_dir = Path("config/data/hotkey")
        config_dir.mkdir(parents=True, exist_ok=True)
        return config_dir

    def _collect_config_data(self) -> dict:
        """Coleta todos os parâmetros atuais do plugin em um dicionário."""
        vals = self._grid_hotkey_numbers.values
        return {
            "mode": self._combo_mode.current_value,
            "value": self._grid_text.get("valor"),
            "hotkey": self._edit_hotkey.captured_key(),
            "suppress": bool(self._grid_suppress.all.get("suppress", True)),
            "atraso": vals.get("atraso", self.DEFAULT_STARTUP_DELAY),
            "intervalo": vals.get("intervalo", self.DEFAULT_SEQUENCE_INTERVAL),
            "aleatoriedade": vals.get("aleatoriedade", 0.0),
            "repeticoes": int(vals.get("repeticoes", self.DEFAULT_SEQUENCE_REPEAT)),
            "sequence": self._edit_sequence.captured_sequence(),
        }

    def _apply_config_data(self, data: dict):
        """Aplica os parâmetros de um dicionário nos widgets do plugin."""
        mode = data.get("mode", self.MODE_TEXT)
        self._combo_mode.current_value = mode

        value = data.get("value")
        if value is not None:
            self._grid_text.set("valor", value, block_signals=True)

        hotkey = data.get("hotkey")
        if hotkey is not None:
            self._edit_hotkey.set_captured_key(hotkey)

        suppress = data.get("suppress")
        if suppress is not None:
            self._grid_suppress.set_all({"suppress": bool(suppress)})

        atraso = data.get("atraso")
        if atraso is not None:
            self._grid_text_numbers.set("atraso", float(atraso), block_signals=True)
            self._grid_hotkey_numbers.set("atraso", float(atraso), block_signals=True)

        intervalo = data.get("intervalo")
        if intervalo is not None:
            self._grid_hotkey_numbers.set("intervalo", float(intervalo), block_signals=True)

        aleatoriedade_val = data.get("aleatoriedade")
        if aleatoriedade_val is not None:
            self._grid_hotkey_numbers.set("aleatoriedade", float(aleatoriedade_val), block_signals=True)

        repeticoes = data.get("repeticoes")
        if repeticoes is not None:
            self._grid_hotkey_numbers.set("repeticoes", float(repeticoes), block_signals=True)

        sequence = data.get("sequence")
        if sequence is not None and isinstance(sequence, list):
            self._edit_sequence.set_captured_sequence(sequence)

    # ── Salvar / Ler Config ────────────────────────────────────────

    def _on_salvar_config(self):
        """
        Abre um diálogo para inserir um nome e salva a config atual
        em config/data/hotkey/<nome>.json.
        Se o arquivo já existir, pergunta se deseja substituir.
        """
        from utils.MessageBox import MessageBox

        dlg = QDialog(self)
        dlg.setWindowTitle("Salvar Configuração")
        dlg.setFixedSize(400, 140)

        v_layout = QVBoxLayout(dlg)
        v_layout.setSpacing(12)

        label = QLabel("Nome da configuração:")
        v_layout.addWidget(label)

        edit_nome = QLineEdit()
        edit_nome.setPlaceholderText("Ex: config_meu_jogo")
        v_layout.addWidget(edit_nome)

        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        btn_cancelar = QPushButton("Cancelar")
        btn_cancelar.clicked.connect(dlg.reject)
        btn_layout.addWidget(btn_cancelar)
        btn_salvar = QPushButton("Salvar")
        btn_salvar.clicked.connect(dlg.accept)
        btn_layout.addWidget(btn_salvar)
        v_layout.addLayout(btn_layout)

        if dlg.exec() != QDialog.DialogCode.Accepted:
            return

        nome = edit_nome.text().strip()
        if not nome:
            MessageBox.show_warning("O nome não pode estar vazio.", title="Aviso")
            return

        config_dir = self._get_config_dir()
        filepath = config_dir / f"{nome}.json"

        if filepath.exists():
            substituir = MessageBox.show_question(
                f"O arquivo '{nome}.json' já existe.\nDeseja substituir?",
                title="Substituir?",
            )
            if not substituir:
                return

        data = self._collect_config_data()
        data["_saved_at"] = datetime.now().isoformat()

        try:
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            self.logger.info("Config salva", code="CONFIG_SAVED", name=nome)
            SignalManager.instance().console_message.emit(
                f"HotkeyPlugin config salva: {nome}.json"
            )
            MessageBox.show_info(f"Configuração '{nome}' salva com sucesso!", title="Salvo")
        except Exception as e:
            self.logger.error("Erro ao salvar config", code="CONFIG_SAVE_ERR", error=str(e))
            MessageBox.show_error(f"Erro ao salvar configuração:\n{e}", title="Erro")

    def _on_ler_config(self):
        """
        Abre uma janela listando todos os arquivos .json dentro de
        config/data/hotkey/ com nome e data. Ao selecionar um, carrega
        a configuração nos widgets.
        """
        from utils.MessageBox import MessageBox

        config_dir = self._get_config_dir()
        json_files = sorted(config_dir.glob("*.json"))

        if not json_files:
            MessageBox.show_info(
                "Nenhuma configuração salva encontrada.\n"
                "Use 'SALVAR CONFIG' para criar uma.",
                title="Nenhuma Config",
            )
            return

        dlg = QDialog(self)
        dlg.setWindowTitle("Carregar Configuração")
        dlg.resize(500, 400)

        v_layout = QVBoxLayout(dlg)
        v_layout.setSpacing(8)

        label = QLabel("Selecione uma configuração para carregar:")
        v_layout.addWidget(label)

        list_widget = QListWidget()
        for fp in json_files:
            nome = fp.stem
            mtime = datetime.fromtimestamp(fp.stat().st_mtime)
            data_str = mtime.strftime("%d/%m/%Y %H:%M:%S")
            list_widget.addItem(f"{nome}  [{data_str}]")
        v_layout.addWidget(list_widget)

        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        btn_cancelar = QPushButton("Cancelar")
        btn_cancelar.clicked.connect(dlg.reject)
        btn_layout.addWidget(btn_cancelar)
        btn_carregar = QPushButton("Carregar")
        btn_carregar.clicked.connect(dlg.accept)
        btn_layout.addWidget(btn_carregar)
        v_layout.addLayout(btn_layout)

        if dlg.exec() != QDialog.DialogCode.Accepted:
            return

        current_row = list_widget.currentRow()
        if current_row < 0:
            return

        selected_file = json_files[current_row]

        try:
            with open(selected_file, "r", encoding="utf-8") as f:
                data = json.load(f)

            self._apply_config_data(data)
            self.save_prefs()

            self.logger.info("Config carregada", code="CONFIG_LOADED", name=selected_file.stem)
            SignalManager.instance().console_message.emit(
                f"HotkeyPlugin config carregada: {selected_file.stem}.json"
            )
            MessageBox.show_info(
                f"Configuração '{selected_file.stem}' carregada com sucesso!",
                title="Carregado",
            )
        except Exception as e:
            self.logger.error("Erro ao carregar config", code="CONFIG_LOAD_ERR", error=str(e))
            MessageBox.show_error(f"Erro ao carregar configuração:\n{e}", title="Erro")

    # ── Dirty tracking ──────────────────────────────────────────────

    _dirty: bool = False

    def _mark_dirty(self) -> None:
        """Marca que as preferências precisam ser salvas."""
        self._dirty = True