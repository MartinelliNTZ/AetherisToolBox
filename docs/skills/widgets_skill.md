# Skill: Widgets Reutilizáveis (resources/widgets/)

Catálogo oficial de todos os widgets disponíveis em `resources/widgets/`. **Sempre consulte esta lista antes de criar UI nova.** Se o widget que você precisa não existe, crie-o em `resources/widgets/` e **adicione-o a esta lista** (Contrato 12).

> ⚠️ **Contrato 11**: NUNCA importe widgets brutos de `PySide6.QtWidgets` sem antes verificar se já existe um widget pronto aqui. Componentes compostos (label + campo + botão, etc.) DEVEM ser um único widget em `resources/widgets/`.

---

## 📋 Catálogo de Widgets

### `AppBar` — `app_bar.py`
Barra de título superior com:
- Ícone e título da janela
- Botões de minimizar, maximizar/restaurar, fechar (frameless)
- Suporte a arrasto da janela
- Área para toolbar de ações globais

```python
from resources.widgets.app_bar import AppBar
appbar = AppBar()
appbar.minimize_clicked.connect(self.showMinimized)
appbar.close_clicked.connect(self.close)
```

---

### `GroupDiv` — `GroupDiv.py`
Container com fundo escuro e título dourado (estilo QGroupBox). Ideal para agrupar widgets relacionados.

```python
from resources.widgets.GroupDiv import GroupDiv
grupo = GroupDiv("Configurações")
grupo.group_layout.addWidget(QLabel("Opções:"))  # QVBoxLayout interno
```

Suporta `layout_type=QGridLayout` para layout em grade.

---

### `MenuBar` — `MenuBar.py`
Barra de menus com "Arquivo > Sair" e "Ajuda > Sobre". Estilizada com o tema escuro.

```python
from resources.widgets.MenuBar import MenuBar
menu = MenuBar()
menu.sair_clicked.connect(self.close)
menu.sobre_clicked.connect(self._show_about)
```

---

### `SelectorGrid` — `SelectorGrid.py`
Grade de `SimpleSelector`s configurados por dicionário. Cria múltiplos seletores de arquivo/pasta em lote.

```python
from resources.widgets.SelectorGrid import SelectorGrid
grid = SelectorGrid({
    "Imagem Treino":   {"file_filter": "GeoTIFF (*.tif)", "default_path": "dados/treino.tif"},
    "Imagem Classif.": {"file_filter": "GeoTIFF (*.tif)"},
    "Saída":           {"file_filter": "GeoTIFF (*.tif)", "browse_mode": "save_file"},
}, title="Imagens")
grid["Imagem Treino"].path()  # acessa o caminho
```

---

### `SimpleSelector` — `SimpleSelector.py`
Linha com **label + QLineEdit + botão "..."** para selecionar arquivo/pasta. **O widget composto mais usado do sistema.**

```python
from resources.widgets.SimpleSelector import SimpleSelector
sel = SimpleSelector(
    label_text="Imagem:",
    file_filter="GeoTIFF (*.tif *.tiff)",
    browse_mode="open_file",       # open_file, open_files, save_file, directory, directories
)
sel.path()      # caminho atual
sel.paths()     # lista (multi)
sel.set_path("novo/caminho.tif")
```

---

### `SimplePrimaryButton` — `SimplePrimaryButton.py`
Botão principal com gradiente ouro. Ações principais (executar pipeline, confirmar).

```python
from resources.widgets.SimplePrimaryButton import SimplePrimaryButton
btn = SimplePrimaryButton("EXECUTAR")
btn.clicked.connect(self._on_executar)
```

---

### `SimpleSecondaryButton` — `SimpleSecondaryButton.py`
Botão secundário, fundo escuro e texto dourado. Ações auxiliares (salvar config, carregar).

```python
from resources.widgets.SimpleSecondaryButton import SimpleSecondaryButton
btn = SimpleSecondaryButton("Salvar Config")
```

---

### `SimpleLabel` — `SimpleLabel.py`
Label padrão com fonte monospace e cor clara (#A1A1AA). Ideal para mensagens auxiliares, dicas e hints na interface.

```python
from resources.widgets.SimpleLabel import SimpleLabel

label = SimpleLabel("Pressione ESC para cancelar")
```

---

### `SimpleDangerButton` — `SimpleDangerButton.py`
Botão de perigo (fundo vermelho). Ações destrutivas (cancelar, excluir).

```python
from resources.widgets.SimpleDangerButton import SimpleDangerButton
btn = SimpleDangerButton("CANCELAR")
```

---

### `SimpleGhostButton` — `SimpleGhostButton.py`
Botão ghost (invisível, aparece no hover). Ações sutis (adicionar item).

```python
from resources.widgets.SimpleGhostButton import SimpleGhostButton
btn = SimpleGhostButton("+ Adicionar")
```

---

### `SimpleRemoveButton` — `SimpleRemoveButton.py`
Botão de remover com hover vermelho. Remover linhas de tabela, itens de lista.

```python
from resources.widgets.SimpleRemoveButton import SimpleRemoveButton
btn = SimpleRemoveButton("Remover")
```

---

### `ToolGroup` — `ToolGroup.py`
Grupo horizontal de botões de ferramentas na toolbar principal. Cria botões com ícone para cada ferramenta de uma categoria.

```python
from resources.widgets.ToolGroup import ToolGroup
group = ToolGroup(tool_type=ToolType.RASTER, tools=lista_de_tools)
group.tool_clicked.connect(self._on_tool_activated)
```

---

### `ToolSeparator` — `ToolSeparator.py`
Separador decorativo com gradiente dourado. Separa grupos de ferramentas na toolbar.

```python
from resources.widgets.ToolSeparator import ToolSeparator
separator = ToolSeparator(orientation="vertical")  # ou "horizontal"
```

---

### `VerticalTab` — `VerticalTab.py`
Aba vertical estilo Civil 3D. Texto rotacionado 90°, usada no SideWorkspace.

```python
from resources.widgets.VerticalTab import VerticalTab
tab = VerticalTab(title="Ferramentas", tooltip="Painel lateral")
tab.clicked.connect(self._on_tab_clicked)
tab.selected = True
```

---

### `WorkspaceTab` — `WorkspaceTab.py`
Aba customizada para o CentralWorkspace (abas horizontais no topo). A estilização visual vem do QSS em `styles.py`.

```python
from resources.widgets.WorkspaceTab import WorkspaceTab
tab = WorkspaceTab(title="Console", tooltip="Console do sistema")
```

---

### `HotkeyCaptureLine` — `HotkeyCaptureLine.py`
Campo de captura de teclas com label opcional encapsulado. Ao clicar, entra em modo de escuta e a próxima tecla pressionada é capturada (F1, ESC, DEL, ENTER, etc.). Ideal para configuração de atalhos de teclado.

Se ``label`` for informado, cria automaticamente um QFormLayout com o label + campo — eliminando a necessidade de criar layouts externos no plugin.

```python
from resources.widgets.HotkeyCaptureLine import HotkeyCaptureLine

# Sem label (comportamento original)
capture = HotkeyCaptureLine(default_key="f")
capture.keyChanged.connect(self._on_key_changed)
captured = capture.captured_key()  # "f", "f1", "esc", "del", etc.
capture.set_captured_key("f1")     # define programaticamente

# Com label encapsulado (elimina QFormLayout no plugin)
capture = HotkeyCaptureLine(default_key="f", label="Tecla gatilho:")
```

**Comportamento:**
- Exibe nome amigável (F1, ESC, DEL, ↑, etc.)
- Valor interno é compatível com a biblioteca `keyboard`
- Perde o foco → sai do modo escuta
- Tab → sai do modo escuta sem capturar

**Parâmetros:**
- `label: str | None` — se informado, encapsula o campo em um QFormLayout com o label

---

### `GridCheckBox` — `GridCheckBox.py`
Grade rolável de checkboxes organizados em colunas configuráveis. Cada checkbox tem label e tooltip definidos por dicionário.

```python
from resources.widgets.GridCheckBox import GridCheckBox

config = {
    ".txt": {"label": ".txt", "description": "Texto puro", "default": True},
    ".py":  {"label": ".py",  "description": "Python", "default": False},
}

grid = GridCheckBox(config, num_columns=4)
checked = grid.checked      # { ".txt": True }
unchecked = grid.unchecked  # { ".py": False }
all_states = grid.all       # { ".txt": True, ".py": False }
grid.set_all(all_states)    # restaura estados
grid.changed.connect(self._on_ext_changed)
```

---

### `ExecutionButtons` — `ExecutionButtons.py`
Container horizontal de botões de ação com suporte a múltiplos botões secundários à esquerda e primários/de perigo à direita, com stretch automático entre os grupos.

Cada botão é configurado por um dicionário com chave única, permitindo acesso direto via `buttons["chave"]`.

```python
from resources.widgets.ExecutionButtons import ExecutionButtons

buttons = ExecutionButtons(self, {
    "salvar": {
        "text": "SALVAR CONFIG",
        "callback": self._on_salvar,
        "type": "secondary",
        "description": "Salva configuração em disco",
    },
    "preview": {
        "text": "PRÉ-VISUALIZAR",
        "callback": self._on_preview,
        "type": "secondary",
    },
    "executar": {
        "text": "EXECUTAR",
        "callback": self._on_executar,
        "type": "primary",
        "description": "Inicia o pipeline",
    },
    "cancelar": {
        "text": "CANCELAR",
        "callback": self._on_cancelar,
        "type": "danger",
    },
})

# Acessa botão pela chave do config
buttons["executar"].setEnabled(False)
buttons["executar"].setText("PARAR")

# Métodos auxiliares
buttons.set_callback("executar", self._on_parar)
buttons.set_visible("cancelar", True)
buttons.set_enabled("salvar", False)
buttons.set_all_enabled(False)
```

**Tipos suportados:** `primary`, `secondary`, `danger`, `ghost`

**Sinais/Conexões:**
- Cada botão tem `clicked.connect(callback)` automaticamente pelo config
- Callback pode ser alterado em runtime via `set_callback(key, callable)`

**Chaves disponíveis:**
- `buttons.keys()` — lista de chaves
- `"chave" in buttons` — verifica existência
- `buttons.get("chave")` — retorna botão ou None

---

### `GridDoubleSpinBox` — `GridDoubleSpinBox.py`
Grade rolável de campos numéricos (QDoubleSpinBox/QSpinBox) configurados por dicionário. Agrupa múltiplos campos em grid, com label, description, sufixo/prefixo.

```python
from resources.widgets.GridDoubleSpinBox import GridDoubleSpinBox

config = {
    "intervalo": {
        "label": "Intervalo (s)",
        "description": "Tempo entre execuções",
        "decimal": 1,
        "default": 1.0,
        "min": 0.0,
        "max": 999.0,
        "step": 0.1,
        "suffix": "s",
    },
    "repeticoes": {
        "label": "Repetições",
        "decimal": 0,       # 0 = inteiro (QSpinBox)
        "default": 3,
        "min": 1,
        "max": 9999,
    },
}

grid = GridDoubleSpinBox(config)
grid.values           # {"intervalo": 1.0, "repeticoes": 3}
grid.get("intervalo") # 1.0
grid.set("repeticoes", 5)
grid.set_values({"intervalo": 2.5})
grid.changed.connect(self._on_value_changed)
```

**Sinais:**
- `changed(key, value)` — emitido quando qualquer campo muda

**Decimais:**
- `decimal=0` → cria `QSpinBox` (inteiro)
- `decimal>0` → cria `QDoubleSpinBox` com N casas decimais

---

### `GridLineEdit` — `GridLineEdit.py`
Grade rolável de campos de texto (QLineEdit) configurados por dicionário. Suporta placeholder, valor padrão, tooltip e callback.

```python
from resources.widgets.GridLineEdit import GridLineEdit

grid = GridLineEdit({
    "valor": {
        "label": "Valor",
        "description": "Texto a ser digitado",
        "default": "texto padrão",
        "placeholder": "Digite algo...",
    },
})
grid.values          # {"valor": "texto"}
grid.get("valor")    # "texto"
grid.set("valor", "novo texto")
grid.set_values({"valor": "outro"})
grid.changed.connect(self._on_value_changed)
```

---

### `HotkeySequenceCapture` — `HotkeySequenceCapture.py`
Captura uma sequência de teclas/atalhos. Cada tecla é adicionada a uma lista com botões de remover. Ideal para configurar macros de teclado multi-tecla.

```python
from resources.widgets.HotkeySequenceCapture import HotkeySequenceCapture

capture = HotkeySequenceCapture(title="Sequência de Teclas:")
capture.sequenceChanged.connect(self._on_seq_changed)
sequence = capture.captured_sequence()  # ["f1", "ctrl+c", "enter"]
capture.set_captured_sequence(["f", "enter", "del"])
capture.clear()
```

**Sinais:**
- `sequenceChanged(list)` — emitido quando a sequência é alterada

**Parâmetros:**
- `title: str | None` — label opcional exibido antes do campo de captura

---

### `PreferenceItemGrid` — `PreferenceItemGrid.py`
Grade rolável de itens de preferência editáveis. Cada linha contém: título | valor (checkbox para bool, spin para float/int, line edit para texto) | botão lixeira.

Configurado por dicionário com suporte a tipos `bool`, `float`, `int`, `text`.

```python
from resources.widgets.PreferenceItemGrid import PreferenceItemGrid

config = {
    "search_text": {
        "type": "text",
        "default": "",
        "label": "Texto de Busca",
    },
    "max_results": {
        "type": "int",
        "default": 50,
        "label": "Máx. Resultados",
        "min": 1,
        "max": 1000,
    },
}

grid = PreferenceItemGrid(config, section="MinhaFerramenta")
grid.load_values()     # carregar do disco
grid.save_values()     # salvar no disco
grid.reset_values()    # restaurar defaults
grid.clear_all()       # limpar tudo
```

---

### `PluginPage` — `PluginPage.py`
Container base padrão para todos os plugins. Fornece:
- QVBoxLayout com margins (18, 10, 18, 10) e spacing 8
- Header opcional (QLabel + QFrame separator) se `title` for informado

Usado automaticamente pelo `BasePlugin._build_ui()`.

```python
from resources.widgets.PluginPage import PluginPage

# Uso direto (raro)
page = PluginPage(title="Meu Plugin")
page.main_layout.addWidget(QLabel("conteúdo"))

# Uso via BasePlugin (padrão)
class MeuPlugin(BasePlugin):
    def _build_ui(self):
        super()._build_ui()
        self.main_layout.addWidget(QLabel("meu widget"))
```

---

### `SimpleComboBox` — `SimpleComboBox.py`
QComboBox genérico com label opcional. Aceita `Dict[str, str]` (recomendado) ou `List[str]`. Prefira **sempre** Dict — a chave é o valor interno estável, o texto é o display. Isso evita perda de índice e permite maior semântica.

```python
from resources.widgets.SimpleComboBox import SimpleComboBox

# Dict (recomendado) — valor_interno → texto_exibido
combo = SimpleComboBox(
    items={"console": "Console", "renamer": "Renomeador"},
    on_item_changed=self._on_item_changed,
    label="Ferramenta:",
)
combo.current_value   # "console"
combo.current_text    # "Console"
combo.current_value = "renamer"  # setter por valor
combo.select_first()
combo.set_items({"novo": "Novo"})

# List (menos recomendado) — texto = valor
combo = SimpleComboBox(items=["Opção A", "Opção B"])
```

---

## 🆕 Como criar um Novo Widget

1. Crie o arquivo em `resources/widgets/MeuWidget.py`
2. A classe deve herdar de `QWidget` (ou `QPushButton`, `QLabel`, etc.)
3. Siga o padrão de nomenclatura: `PascalCase` para classe, `snake_case` para arquivo
4. Use `from __future__ import annotations` no topo
5. Adicione docstring explicando o propósito e uso
6. **ATUALIZE ESTA SKILL** — adicione o novo widget ao catálogo acima (Contrato 12)

## 🛠 Como modificar um Widget Existente

- **Mantenha compatibilidade retroativa**: não quebre a assinatura dos métodos existentes
- Se precisar adicionar parâmetros novos, use valores padrão (`=None`, `=False`)
- É preferível **estender** um widget existente a criar um novo similar
- Atualize esta skill se a interface pública mudar

---

## ✅ Checklist ao criar/alterar UI

- [ ] Consultei o catálogo acima antes de importar de `PySide6.QtWidgets`?
- [ ] O componente que preciso já existe como widget composto?
- [ ] Se não existe, criei em `resources/widgets/` e atualizei esta skill?
- [ ] Se modifiquei um existente, mantive compatibilidade retroativa?

### `MenuBar` Update
O `MenuBar` agora suporta o sinal `tool_clicked` e o método `add_menu_items` para inserir dinamicamente ações de ferramentas no menu "Sistema".

```python
menu_bar = MenuBar()
menu_bar.tool_clicked.connect(self._on_tool_activated)
menu_bar.add_menu_items([("Preferences", "Gerenciador de Preferências")])
```
