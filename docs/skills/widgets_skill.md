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
