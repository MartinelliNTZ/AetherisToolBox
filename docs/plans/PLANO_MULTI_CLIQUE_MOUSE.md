# Plano de Ação — Modo "Multi Clique Mouse" no HotkeyPlugin

## 1. Objetivo

Adicionar ao **HotkeyPlugin** um terceiro modo de operação: **"Multi Clique Mouse"**, que ao pressionar a tecla gatilho configurada, execute N cliques do botão do mouse selecionado (esquerdo, direito, meio, X1, X2), com intervalo configurável entre cliques.

Atualmente o plugin só possui:
- **Teclar Texto** — digita uma string caractere por caractere
- **Teclar Atalho** — executa sequência de teclas N vezes

O script `metralhadora.py` serviu como prova de conceito do comportamento desejado.

---

## 2. Enum Novo: `MouseButton` em `core/enum/MouseButton.py`

Criar um Enum para centralizar os botões do mouse suportados, seguindo o padrão dos enums existentes (`ToolKey`, `CategoryTool`, etc.).

**Arquivo:** `core/enum/MouseButton.py`

```python
# -*- coding: utf-8 -*-
"""
MouseButton — Enum de botões do mouse
======================================
Centraliza os nomes dos botões do mouse em um Enum para evitar
strings soltas no código e facilitar manutenção.
"""

from __future__ import annotations

from enum import Enum


class MouseButton(str, Enum):
    """Enum com os botões do mouse suportados pelo sistema."""

    LEFT = "left"
    RIGHT = "right"
    MIDDLE = "middle"
    X1 = "x1"
    X2 = "x2"

    @classmethod
    def display_names(cls) -> list[str]:
        """Retorna lista com os nomes de exibição amigáveis."""
        return ["Left", "Right", "Middle", "X1", "X2"]

    @classmethod
    def from_name(cls, name: str) -> "MouseButton":
        """
        Retorna o enum correspondente ao nome, ou levanta ValueError.
        """
        try:
            return cls(name.lower())
        except ValueError:
            raise ValueError(
                f"'{name}' não é um MouseButton válido. "
                f"Opções: {', '.join(cls._value2member_map_.keys())}"
            )
```

**Uso nos widgets:**
```python
from core.enum.MouseButton import MouseButton

# Valores internos compatíveis com pyautogui.click(button=...)
MouseButton.LEFT.value   # "left"
MouseButton.RIGHT.value  # "right"
```

---

## 3. Widget que Precisa Ser Criado

### 3.1 `MouseButtonCapture` (NOVO) — `resources/widgets/MouseButtonCapture.py`

**Propósito:** Widget de captura de botão do mouse, análogo ao `HotkeyCaptureLine` para teclado. Permite ao usuário clicar no widget e então pressionar um botão do mouse para selecioná-lo.

**Interface esperada:**

```python
from resources.widgets.MouseButtonCapture import MouseButtonCapture

# Sem label
capture = MouseButtonCapture(default_button="left")
capture.buttonChanged.connect(self._on_button_changed)
selected = capture.captured_button()  # "left", "right", "middle", "x1", "x2"
capture.set_captured_button("right")

# Com label encapsulado
capture = MouseButtonCapture(default_button="left", label="Botão do mouse:")
```

**Comportamento:**
- Exibe nome amigável (Left, Right, Middle, X1, X2)
- Valor interno compatível com `pyautogui.click(button=...)` e com o Enum `MouseButton`
- Ao clicar, entra em modo de escuta
- Usuário clica um botão do mouse → captura
- Perde foco → sai do modo escuta
- Tab → sai sem capturar

**Armadilha a evitar:** O ato de clicar no widget NÃO deve disparar o clique no alvo. O widget precisa:
1. Entrar em modo de escuta ao ganhar foco (click)
2. Usar `pynput.mouse.Listener` para capturar o próximo clique **fora** do widget
3. Identificar qual botão foi pressionado

**Mapeamento pynput → pyautogui:**

| pynput.Button | pyautogui string | MouseButton enum |
|---|---|---|
| `Button.left` | `"left"` | `MouseButton.LEFT` |
| `Button.right` | `"right"` | `MouseButton.RIGHT` |
| `Button.middle` | `"middle"` | `MouseButton.MIDDLE` |
| `Button.x1` | `"x1"` | `MouseButton.X1` |
| `Button.x2` | `"x2"` | `MouseButton.X2` |

---

## 4. Mudanças no HotkeyPlugin

### 4.1 Adicionar terceiro modo no `SimpleComboBox`

**Arquivo:** `plugins/hotkey/HotkeyPlugin.py`

**Local:** Dentro do `_build_ui()`, seção do `self._combo_mode`

**O que mudar:**

```python
# ANTES (2 modos)
self.MODE_TEXT = "Teclar Texto"
self.MODE_HOTKEY = "Teclar Atalho"

# DEPOIS (3 modos)
self.MODE_TEXT = "Teclar Texto"
self.MODE_HOTKEY = "Teclar Atalho"
self.MODE_MOUSE = "Multi Clique Mouse"
```

Atualizar o dicionário passado ao `SimpleComboBox`:

```python
self._combo_mode = SimpleComboBox(
    items={
        self.MODE_TEXT: self.MODE_TEXT,
        self.MODE_HOTKEY: self.MODE_HOTKEY,
        self.MODE_MOUSE: self.MODE_MOUSE,
    },
    on_item_changed=self._on_mode_changed,
    parent=self,
)
```

### 4.2 Criar `SectionPanel` para o modo Mouse

**Local:** Dentro de `_build_ui()`, após o stack de hotkey, antes do `HotkeyCaptureLine`.

**Widgets dentro do painel de mouse:**

| Widget | Chave | Descrição |
|---|---|---|
| `MouseButtonCapture` | — | Seleciona qual botão do mouse clicar |
| `GridDoubleSpinBox` | atraso | Atraso inicial (s) — **reaproveitar sincronizado** |
| `GridDoubleSpinBox` | intervalo | Intervalo entre cliques (s) |
| `GridDoubleSpinBox` | repeticoes | Número de cliques por acionamento (0 = contínuo enquanto segurar) |

**Observação:** O `atraso` inicial já existe sincronizado entre os stacks de texto e hotkey. O modo mouse também deve compartilhar o mesmo valor de `atraso`.

### 4.3 Atualizar `_update_mode_visibility()`

**Antes:**
```python
def _update_mode_visibility(self):
    mode = self._combo_mode.current_value
    is_text = mode == self.MODE_TEXT
    self._stack_text.setVisible(is_text)
    self._stack_hotkey.setVisible(not is_text)
```

**Depois:**
```python
def _update_mode_visibility(self):
    mode = self._combo_mode.current_value
    self._stack_text.setVisible(mode == self.MODE_TEXT)
    self._stack_hotkey.setVisible(mode == self.MODE_HOTKEY)
    self._stack_mouse.setVisible(mode == self.MODE_MOUSE)
```

### 4.4 Adicionar lógica em `_start_worker()` — modo mouse

**Antes do bloco `if mode == self.MODE_TEXT:`**

Inserir novo bloco:

```python
if mode == self.MODE_MOUSE:
    button = self._mouse_button_capture.captured_button()
    if not button:
        MessageBox.show_warning(
            "Selecione um botão do mouse.", title="Aviso"
        )
        return
```

**Dentro do callback `type_value()`:**

```python
if mode == self.MODE_MOUSE:
    import pyautogui
    total_clicks = int(self._grid_mouse_numbers.get("repeticoes"))
    interval = self._grid_mouse_numbers.get("intervalo")
    continuous = (total_clicks == 0)
    count = 0
    while self._running:
        if not continuous and count >= total_clicks:
            break
        pyautogui.click(button=button)
        count += 1
        if not continuous:
            progress = (count / total_clicks) * 100.0
            SignalManager.instance().progress_update.emit(progress)
        time.sleep(interval)
    QTimer.singleShot(0, lambda: self._on_mouse_done(count, button, hotkey))
```

### 4.5 Adicionar `_on_mouse_done()`

```python
def _on_mouse_done(self, count: int, button: str, hotkey: str) -> None:
    SignalManager.instance().console_message.emit(
        f"HotkeyPlugin executou {count} cliques ({button})"
        f" via tecla {hotkey.upper()}"
    )
```

### 4.6 Atualizar `_set_inputs_enabled()`

Adicionar:
```python
self._grid_mouse_numbers.setEnabled(enabled)
self._mouse_button_capture.setEnabled(enabled)
self._stack_mouse.setEnabled(enabled)
```

### 4.7 Atualizar `load_prefs()` e `save_prefs()`

**`load_prefs()`** — adicionar:
```python
mouse_button = self.preferences.get("mouse_button")
if mouse_button is not None:
    self._mouse_button_capture.set_captured_button(mouse_button)

mouse_interval = self.preferences.get("mouse_interval")
if mouse_interval is not None:
    self._grid_mouse_numbers.set("intervalo", float(mouse_interval), block_signals=True)

mouse_repeat = self.preferences.get("mouse_repeat")
if mouse_repeat is not None:
    self._grid_mouse_numbers.set("repeticoes", float(mouse_repeat), block_signals=True)
```

**`save_prefs()`** — adicionar:
```python
self.preferences["mouse_button"] = self._mouse_button_capture.captured_button()

mouse_vals = self._grid_mouse_numbers.values
self.preferences["mouse_interval"] = mouse_vals.get("intervalo", 0.04)
self.preferences["mouse_repeat"] = mouse_vals.get("repeticoes", 1)
```

### 4.8 Atualizar `_collect_config_data()` e `_apply_config_data()`

Mesmo padrão dos outros modos: incluir `mouse_button`, `mouse_interval`, `mouse_repeat`.

---

## 5. Dependências

A funcionalidade de clique usará **`pyautogui`** (já é dependência do projeto, usada nos modos texto e atalho).

Para o widget `MouseButtonCapture` com captura real de botão do mouse, será usado **`pynput`** (mesma lib usada no script `metralhadora.py`).

**`requirements.txt`** — adicionar:
```
pynput
```

---

## 6. Documentação a Atualizar

| Arquivo | O que atualizar |
|---|---|
| `docs/skills/widgets_skill.md` | Adicionar `MouseButtonCapture` ao catálogo |
| `plugins/hotkey/HotkeyPlugin.py` | Docstring do módulo incluir menção ao modo mouse |
| `requirements.txt` | Adicionar `pynput` |

---

## 7. UI Final Esperada (resultado visual)

```
┌─────────────────────────────────────────────────┐
│  Teclador F — Automação de Teclado              │
├─────────────────────────────────────────────────┤
│  [SALVAR CONFIG]    [LER CONFIG]  [EXECUTAR]    │
├─────────────────────────────────────────────────┤
│  [Multi Clique Mouse        ▼]                  │
├─────────────────────────────────────────────────┤
│  ┌─ Configurações ─────────────────────────────┐│
│  │                                             ││
│  │  ┌─ stack_mouse ──────────────────────────┐ ││
│  │  │ Botão do mouse: [ Left ▼ ]             │ ││
│  │  │  ou via capture: [ Left   🖱️ ]         │ ││
│  │  │                                         │ ││
│  │  │ ┌─ GridDoubleSpinBox ─────────────────┐ │ ││
│  │  │ │ Atraso inicial:    [0.15s]          │ │ ││
│  │  │ │ Intervalo cliques: [0.04s]          │ │ ││
│  │  │ │ Nº de cliques:     [   1  ]         │ │ ││
│  │  │ └─────────────────────────────────────┘ │ ││
│  │  └─────────────────────────────────────────┘ ││
│  │                                             ││
│  │  Tecla gatilho: [ F ]                       ││
│  │                                             ││
│  │  ☑ Bloquear propagação (suppress)           ││
│  └─────────────────────────────────────────────┘│
└─────────────────────────────────────────────────┘
```

### Comportamento do modo mouse:

| Config | Efeito |
|---|---|
| Nº de cliques = 1 | Um clique a cada pressionamento da tecla gatilho |
| Nº de cliques = 5 | Dispara 5 cliques rápidos |
| Nº de cliques = 0 | Modo contínuo: clica enquanto a tecla estiver sendo segurada (como na `metralhadora.py`) |

### Botões do mouse suportados:

| Valor interno (Enum) | Display |
|---|---|
| `MouseButton.LEFT` → `"left"` | Left (Esquerdo) |
| `MouseButton.RIGHT` → `"right"` | Right (Direito) |
| `MouseButton.MIDDLE` → `"middle"` | Middle (Meio) |
| `MouseButton.X1` → `"x1"` | X1 (Botão lateral 1) |
| `MouseButton.X2` → `"x2"` | X2 (Botão lateral 2) |

---

## 8. Checklist de Implementação

- [x] **Criar** `core/enum/MouseButton.py` — Enum `MouseButton` (LEFT, RIGHT, MIDDLE, X1, X2)
- [x] **Criar** `resources/widgets/MouseButtonCapture.py` com classe `MouseButtonCapture`
  - [x] Suporte a label encapsulado (QFormLayout)
  - [x] Modo de captura com pynput
  - [x] Sinal `buttonChanged(str)`
  - [x] Métodos `captured_button()`, `set_captured_button(button)`
- [x] **Atualizar** `docs/skills/widgets_skill.md` com o novo widget
- [x] **Adicionar** `pynput` ao `requirements.txt`
- [x] **Modificar** `HotkeyPlugin.py`:
  - [x] Adicionar constante `MODE_MOUSE = "Multi Clique Mouse"`
  - [x] Adicionar `SimpleComboBox` com 3 modos
  - [x] Criar `SectionPanel("stack_mouse")` com `MouseButtonCapture` + `GridDoubleSpinBox`
  - [x] Atualizar `_update_mode_visibility()` para 3 vias
  - [x] Adicionar lógica de validação e execução no `_start_worker()`
  - [x] Adicionar callback `_on_mouse_done()`
  - [x] Atualizar `_set_inputs_enabled()`
  - [x] Atualizar `load_prefs()` e `save_prefs()`
  - [x] Atualizar `_collect_config_data()` e `_apply_config_data()`
- [x] **Verificar** compilação dos 3 arquivos sem erros
- [ ] **Testar** (pendente — runtime):
  - [ ] Modo mouse com left button + 1 click
  - [ ] Modo mouse com right button + 5 clicks
  - [ ] Modo mouse com middle button + 0 (contínuo)
  - [ ] Salvar/carregar config preserva configurações do modo mouse
  - [ ] Alternar entre modos não corrompe valores
  - [ ] Parar execução no meio do ciclo

---

## 9. Observações Técnicas

### 9.1 Sincronização do `atraso inicial`

Atualmente `atraso` é sincronizado entre texto e hotkey via `load_prefs()`. O modo mouse deve seguir o mesmo padrão: ler da mesma chave `"atraso"`.

### 9.2 Modo contínuo vs único

O modo contínuo (repeticoes=0) é análogo ao comportamento da `metralhadora.py`: clica enquanto o usuário segura a tecla gatilho. Requer que o listener detecte tanto `on_press` (iniciar) quanto `on_release` (parar).

**Implementação atual do HotkeyPlugin usa `keyboard.add_hotkey` com callback único.** Para suporte a segurar tecla, será necessário:
- Opção A: Usar `keyboard.on_press`/`keyboard.on_release` separados (mais preciso)
- Opção B: No modo contínuo, fazer o loop rodar até que a tecla seja solta (verificar com `keyboard.is_pressed(hotkey)` dentro do loop)

### 9.3 Captura de botão do mouse via pynput

O `MouseButtonCapture` usará `pynput.mouse.Listener` em modo de captura única:
1. Widget perde foco ou usuário clica no botão de captura
2. Um listener é registrado para capturar o próximo clique
3. O clique é convertido para string compatível com pyautogui
4. Listener é removido imediatamente

---

## 10. Riscos

| Risco | Mitigação |
|---|---|
| pynput conflitar com keyboard lib | Testar em paralelo; ambas são hooks globais, mas em threads separadas |
| Captura de botão do mouse pode ser acidental | Só ativar captura explicitamente (clicar no widget), timeout de 5s |
| Modo contínuo pode travar se tecla não for solta | Adicionar fallback de segurança (ESC para cancelar, ou timeout) |
| pyautogui.click pode não funcionar em alguns jogos/apps | Mesma limitação dos modos existentes; documentar |