# -*- coding: utf-8 -*-
"""
HotkeyCaptureLine — Campo de captura de tecla.
================================================
QLineEdit que, ao focar, captura qualquer tecla pressionada
e exibe seu nome (F1, ESC, DEL, F, etc.) em vez de digitar texto.

Uso:
    from resources.widgets.HotkeyCaptureLine import HotkeyCaptureLine

    capture = HotkeyCaptureLine(default_key="f")
    capture.keyChanged.connect(self._on_key_changed)
    captured = capture.captured_key()  # "f", "f1", "esc", "del", etc.
"""

from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QLineEdit


# Mapeamento de Qt.Key para string compatível com a biblioteca `keyboard`
# Usa getattr para compatibilidade com diferentes versões do PySide6
_QT_KEY_TO_KEYBOARD: dict[int, str] = {}

def _safe_key(name: str, value: str) -> None:
    """Adiciona ao mapa se a constante Qt.Key existir nesta versão."""
    key = getattr(Qt.Key, name, None)
    if key is not None:
        _QT_KEY_TO_KEYBOARD[key] = value

_safe_key("Key_Escape", "esc")
_safe_key("Key_Tab", "tab")
_safe_key("Key_Backtab", "tab")
_safe_key("Key_Backspace", "backspace")
_safe_key("Key_Return", "enter")
_safe_key("Key_Enter", "enter")
_safe_key("Key_Insert", "insert")
_safe_key("Key_Delete", "del")
_safe_key("Key_Pause", "pause")
_safe_key("Key_Print", "print screen")
_safe_key("Key_Home", "home")
_safe_key("Key_End", "end")
_safe_key("Key_PageUp", "page up")
_safe_key("Key_PageDown", "page down")
_safe_key("Key_Up", "up")
_safe_key("Key_Down", "down")
_safe_key("Key_Left", "left")
_safe_key("Key_Right", "right")
_safe_key("Key_Space", "space")
_safe_key("Key_CapsLock", "caps lock")
_safe_key("Key_NumLock", "num lock")
_safe_key("Key_ScrollLock", "scroll lock")
_safe_key("Key_Menu", "menu")
_safe_key("Key_Help", "help")
_safe_key("Key_Shift", "shift")
_safe_key("Key_Control", "ctrl")
_safe_key("Key_Alt", "alt")
_safe_key("Key_Meta", "windows")
_safe_key("Key_Plus", "+")
_safe_key("Key_Minus", "-")
_safe_key("Key_Asterisk", "*")
_safe_key("Key_Slash", "/")
_safe_key("Key_Period", ".")
_safe_key("Key_Comma", ",")
_safe_key("Key_Semicolon", ";")
_safe_key("Key_Quote", "'")
_safe_key("Key_BracketLeft", "[")
_safe_key("Key_BracketRight", "]")
_safe_key("Key_Backslash", "\\")

# F1..F12
for i in range(1, 13):
    key = getattr(Qt.Key, f"Key_F{i}", None)
    if key is not None:
        _QT_KEY_TO_KEYBOARD[key] = f"f{i}"


def _qt_key_to_name(event) -> str | None:
    """Converte um QKeyEvent para o nome de tecla compatível com `keyboard`."""
    key = event.key()
    text = event.text().strip()

    # Tenta mapeamento direto por código (especiais, F1-F12, etc.)
    mapped = _QT_KEY_TO_KEYBOARD.get(key)
    if mapped is not None:
        return mapped

    # Letras: converte para minúsculo se for uma única letra
    if len(text) == 1 and text.isalpha():
        return text.lower()

    # Números do teclado principal
    if Qt.Key.Key_0 <= key <= Qt.Key.Key_9:
        return chr(key)

    return None


_DISPLAY_NAMES: dict[str, str] = {
    "esc": "ESC",
    "tab": "TAB",
    "backspace": "BKSP",
    "enter": "ENTER",
    "insert": "INS",
    "del": "DEL",
    "pause": "PAUSE",
    "print screen": "PRT SCR",
    "home": "HOME",
    "end": "END",
    "page up": "PG UP",
    "page down": "PG DN",
    "caps lock": "CAPS",
    "num lock": "NUM",
    "scroll lock": "SCRL",
    "menu": "MENU",
    "help": "HELP",
    "shift": "SHIFT",
    "ctrl": "CTRL",
    "alt": "ALT",
    "windows": "WIN",
    "up": "↑",
    "down": "↓",
    "left": "←",
    "right": "→",
    "space": "ESPAÇO",
}


def _to_display(key_name: str) -> str:
    """Converte nome interno (ex: 'f1', 'del') para exibição amigável."""
    if key_name in _DISPLAY_NAMES:
        return _DISPLAY_NAMES[key_name]
    # F1-F12 e letras
    if len(key_name) == 1 and key_name.isalpha():
        return key_name.upper()
    # Números
    if len(key_name) == 1 and key_name.isdigit():
        return key_name
    # f1, f2, ...
    return key_name.upper()


class HotkeyCaptureLine(QLineEdit):
    """
    Campo de texto que captura teclas ao ganhar foco.

    Comportamento:
    - Ao clicar/focar, fica em modo de escuta.
    - A próxima tecla pressionada é capturada e exibida.
    - O texto digitado normal é bloqueado.
    - O nome exibido é amigável (F1, ESC, DEL, etc.).
    - O valor interno está no formato compatível com `keyboard`.
    """

    keyChanged = Signal(str)

    def __init__(
        self,
        default_key: str = "f",
        placeholder: str = "Clique e pressione uma tecla...",
        parent=None,
    ):
        super().__init__(parent)
        self._captured_raw = default_key
        self._listening = False

        self.setReadOnly(True)
        self.setPlaceholderText(placeholder)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setMaxLength(20)
        self._set_display(default_key)

        # Conecta clique para entrar em modo escuta
        self.mousePressEvent = self._on_mouse_press  # type: ignore[method-assign]

    # ── API Pública ──────────────────────────────────────────────────

    def captured_key(self) -> str:
        """Retorna a tecla capturada no formato compatível com `keyboard`."""
        return self._captured_raw

    def set_captured_key(self, key_name: str) -> None:
        """Define programaticamente a tecla capturada."""
        self._captured_raw = key_name
        self._set_display(key_name)
        self.keyChanged.emit(key_name)

    # ── Internos ─────────────────────────────────────────────────────

    def _set_display(self, key_name: str) -> None:
        """Atualiza o texto exibido."""
        self.setText(_to_display(key_name))

    def _on_mouse_press(self, event) -> None:
        """Entra em modo de escuta ao clicar."""
        self._listening = True
        self.setFocus()
        self.selectAll()
        # Exibe placeholder de escuta
        self.setText("...")
        self.setStyleSheet("color: #FFD700;")

    def keyPressEvent(self, event) -> None:
        """Captura a tecla quando em modo escuta."""
        if not self._listening:
            super().keyPressEvent(event)
            return

        # Ignora Tab (mudaria foco)
        if event.key() in (Qt.Key.Key_Tab, Qt.Key.Key_Backtab):
            self._listening = False
            self.setStyleSheet("")
            self._set_display(self._captured_raw)
            self.clearFocus()
            return

        key_name = _qt_key_to_name(event)
        if key_name is None:
            return  # ignora teclas não mapeáveis

        self._captured_raw = key_name
        self._listening = False
        self.setStyleSheet("")
        self._set_display(key_name)
        self.clearFocus()
        self.keyChanged.emit(key_name)

    def focusOutEvent(self, event) -> None:
        """Sai do modo escuta se perder foco."""
        if self._listening:
            self._listening = False
            self.setStyleSheet("")
            self._set_display(self._captured_raw)
        super().focusOutEvent(event)