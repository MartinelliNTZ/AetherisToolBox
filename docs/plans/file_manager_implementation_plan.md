# 📂 Plano de Implementação — FileManager (Explorador de Arquivos)

## 1. Visão Geral

Criar uma ferramenta SIDE (painel lateral) que funciona como um explorador de arquivos interno. Ela lê a `root_folder` das `sys_preferences` (definida pelo `SaveProjectPlugin`) e exibe o conteúdo daquela pasta em uma árvore/lista, permitindo operações básicas de gerenciamento de arquivos **sem sair do Aetheris ToolBox**.

### 1.1. O que NÃO faz
- Não substitui o Windows Explorer — é um visualizador/gerenciador leve interno.
- Não faz busca global, execução de arquivos, preview de conteúdo binário.
- Não usa QFileDialog — operações de deleção/rename/criação usam QInputDialog, QMenu contextual e MessageBox.

### 1.2. Dependências Externas
- Nenhuma. Usa apenas `os`, `shutil`, `pathlib` (stdlib) + `PySide6`.
- Não adiciona requirements novos (Contrato 8).

---

## 2. Arquivos que Serão Criados/Modificados

| Arquivo | Ação | Descrição |
|---|---|---|
| `plugins/file_manager/FileManagerPlugin.py` | **CRIAR** | Plugin principal (herda BasePlugin, category=SIDE) |
| `plugins/file_manager/__init__.py` | **CRIAR** | Pacote vazio |
| `resources/widgets/FileTreeWidget.py` | **CRIAR** | Widget QTreeView + QFileSystemModel customizado |
| `core/enum/ToolKey.py` | **MODIFICAR** | Adicionar `FILE_MANAGER = "FileManager"` |
| `core/config/ToolRegistry.py` | **MODIFICAR** | Adicionar registro do FileManager como SIDE |
| `docs/skills/widgets_skill.md` | **MODIFICAR** | Adicionar FileTreeWidget ao catálogo |
| `docs/skills/file_manager_skill.md` | **CRIAR** | Skill do FileManager |

---

## 3. Estrutura de Diretórios (Após Implementação)

```
plugins/file_manager/
├── __init__.py
└── FileManagerPlugin.py        # Plugin SIDE — explorador de arquivos

resources/widgets/
└── FileTreeWidget.py           # QTreeView + QFileSystemModel + ações
```

---

## 4. Arquitetura Detalhada

### 4.1. `plugins/file_manager/FileManagerPlugin.py`

**Herança:** `BasePlugin` com `sys_prefs=True`

**Ciclo de Vida:**
1. `__init__` → `super().__init__(tool_key="FileManager", sys_prefs=True, parent=parent)`
2. `_build_ui()` → constrói layout com:
   - Header com label "Explorador: <root_folder_path>"
   - ExecutionButtons com ações: "Criar Arquivo", "Atualizar"
   - FileTreeWidget (ocupando o espaço restante)
3. `load_prefs()` → lê `root_folder` de `self.sys_preferences`
4. `save_prefs()` → (vazio, não persiste nada próprio)
5. `on_open()` opcional → recarrega se root_folder mudou

**Fluxo root_folder:**
```
self.sys_preferences.get("root_folder", None)  # vindo do SaveProjectPlugin
Se None → mensagem "Nenhum projeto ativo. Use 'Gerenciar Projeto' primeiro."
Se preenchido → FileTreeWidget.set_root_path(root_folder)
```

**Métodos do Plugin:**
- `_refresh_tree()` — recarrega a árvore exibindo estado atual do disco
- `_create_text_file()` — QInputDialog pergunta nome → cria arquivo `.txt` vazio na pasta selecionada
- `_delete_selected()` — confirma com MessageBox → deleta arquivo/pasta selecionada
- `_rename_selected()` — QInputDialog pergunta novo nome → renomeia

### 4.2. `resources/widgets/FileTreeWidget.py`

**Classe:** `FileTreeWidget(QWidget)`

**Composição:**
- `QTreeView` — exibe a estrutura de diretórios
- `QFileSystemModel` — modelo nativo do Qt (já fornece ícones, tipos, tamanhos, datas)
- `filtro` — mostra apenas 1 coluna (nome) para simplicidade, ou todas (nome, tamanho, tipo, data)

**Context Menu (QMenu):**
- "Renomear" (F2)
- "Excluir" (Del)
- "Criar Arquivo de Texto" (Ctrl+N)
- "Atualizar" (F5)
- Separador
- "Abrir Local" (abre Windows Explorer na pasta)

**Drag & Drop Interno:**
- `setDragEnabled(True)`, `setAcceptDrops(True)`
- `setDragDropMode(QAbstractItemView.InternalMove)`
- Ao soltar: move o arquivo/pasta de origem para o diretório destino
- Usa `shutil.move()` para mover no sistema de arquivos real

**Métodos Públicos:**
- `set_root_path(path: str)` — define o diretório raiz no QFileSystemModel
- `refresh()` — força recarga do modelo
- `selected_path() -> str | None` — caminho completo do item selecionado
- `selected_is_directory() -> bool`
- `delete_selected() -> bool`
- `rename_selected() -> bool`
- `create_text_file(directory: str | None = None) -> bool`
- `selected_paths() -> list[str]` — multi-seleção

**Sinais:**
- `file_renamed(old_path: str, new_path: str)`
- `file_deleted(path: str)`
- `file_created(path: str)`
- `file_moved(src: str, dst: str)`
- `selection_changed(path: str | None)`

### 4.3. Modelo de Dados

Usar `QFileSystemModel` do Qt, que já gerencia:
- Listagem de arquivos/pastas
- Ícones nativos do Windows
- Nome, tamanho, tipo, data de modificação
- Monitoramento de mudanças em tempo real

Não reinventar a roda — `QFileSystemModel` já é um modelo completo.

### 4.4. Segurança

- Confirmar deleção com `MessageBox.show_question` (Contrato 1)
- Validar nomes de arquivo (sem caracteres inválidos: `\/:*?"<>|`)
- Não permitir navegar acima da `root_folder` (travar no root)
- Verificar permissões antes de operações

---

## 5. Wireframe da UI

```
┌─────────────────────────────────┐
│ 🔍 Explorador: C:\projetos\    │  ← QLabel com caminho
├─────────────────────────────────┤
│ [Criar Arquivo] [↻ Atualizar]   │  ← ExecutionButtons
├─────────────────────────────────┤
│ 📁 projeto_a/                   │
│   📁 src/                       │  ← QTreeView + QFileSystemModel
│     📄 main.py                  │
│     📄 utils.py                 │
│   📁 assets/                    │
│   📄 README.md                  │
│ 📁 projeto_b/                   │
│   📄 index.html                 │
│ 📄 d.mtl                        │
└─────────────────────────────────┘
```

---

## 6. Fluxo de Operações

### 6.1. Abrir o FileManager pela primeira vez
1. Usuário clica na toolbar → WorkspaceManager.open_tool("FileManager")
2. Lazy loading: ToolRegistry instancia FileManagerPlugin
3. `__init__` → `sys_prefs=True` carrega `self.sys_preferences`
4. `_build_ui()` → monta layout, ExecutionButtons, FileTreeWidget
5. `load_prefs()` → lê `root_folder` das sys_preferences
6. Se `root_folder` existe → `FileTreeWidget.set_root_path(root_folder)`
7. Se não existe → exibe label "Nenhum projeto ativo"

### 6.2. Renomear (Context Menu ou F2)
1. Usuário seleciona item → botão direito → "Renomear" (ou F2)
2. FileTreeWidget pega `selected_path()`
3. `QInputDialog.getText()` pergunta novo nome
4. Valida novo nome
5. `os.rename(old, new)` ou `shutil.move(old, new)`
6. Emite `file_renamed`
7. Atualiza árvore

### 6.3. Excluir (Context Menu ou Del)
1. Usuário seleciona item(s) → Del ou "Excluir"
2. Confirma com `MessageBox.show_question("Tem certeza?")`
3. Para pastas: `shutil.rmtree()`
4. Para arquivos: `os.remove()`
5. Emite `file_deleted`
6. Atualiza árvore

### 6.4. Criar Arquivo de Texto
1. ExecutionButtons "Criar Arquivo" ou Context Menu
2. `QInputDialog.getText()` pergunta nome (com `.txt` padrão)
3. Se não tem extensão, adiciona `.txt`
4. Cria na pasta selecionada (ou na raiz)
5. Emite `file_created`
6. Atualiza árvore

### 6.5. Mover por Drag & Drop
1. Qt `InternalMove` + `shutil.move()`
2. Se destino = subpasta da origem → cancela (evita mover pasta para dentro de si mesma)
3. Se arquivo já existe no destino → pergunta se sobrescreve
4. Emite `file_moved`

---

## 7. Registro no ToolRegistry

```python
ToolKey.FILE_MANAGER.value: Tool(
    name=ToolKey.FILE_MANAGER.value,
    title="Explorador",
    widget_factory=_make_factory(
        "plugins.file_manager.FileManagerPlugin",
        "FileManagerPlugin",
    ),
    tooltip="Explorador de arquivos interno do projeto",
    tool_type=ToolType.FOLDER,
    category=CategoryTool.SIDE,
    show_in_toolbar=True,
),
```

---

## 8. ToolKey

```python
FILE_MANAGER = "FileManager"
```

---

## 9. Contratos Respeitados

| Contrato | Como é respeitado |
|---|---|
| **C1** — MessageBox | Todas as confirmações usam `MessageBox.show_question` |
| **C2** — Exceções | Todo `except` tem `as e` e `logger.error()` |
| **C3** — Logger | Todas as operações de arquivo logam |
| **C4** — Preferências | Usa `self.sys_preferences` via BasePlugin |
| **C5** — ToolRegistry | Plugin registrado no ToolRegistry |
| **C6** — BasePlugin | Herda de BasePlugin, implementa `load_prefs()` e `save_prefs()` |
| **C7** — Sinais | Não acopla outros plugins |
| **C8** — Dependências | Nenhuma nova dependência |
| **C9** — Código morto | Nenhum import/função não utilizado |
| **C11** — Widgets | `FileTreeWidget` criado em `resources/widgets/` |
| **C12** — Documentação | Skill do FileManager + widgets_skill.md atualizados |
| **C17** — ExplorerUtils | Não usa QFileDialog — operações são internas (rename, delete, create) |

> **Nota sobre C17:** `ExplorerUtils` é usado APENAS para QFileDialog. Operações de rename, delete, create e drag & drop são manipulação direta do sistema de arquivos via `os`/`shutil`, não passam por QFileDialog. Portanto não violam C17.

---

## 10. Ordem de Implementação

1. Adicionar `FILE_MANAGER` ao `ToolKey`
2. Criar `resources/widgets/FileTreeWidget.py` (QTreeView + QFileSystemModel + ações)
3. Criar `plugins/file_manager/__init__.py`
4. Criar `plugins/file_manager/FileManagerPlugin.py` (plugin SIDE)
5. Registrar no `ToolRegistry`
6. Criar `docs/skills/file_manager_skill.md`
7. Atualizar `docs/skills/widgets_skill.md`