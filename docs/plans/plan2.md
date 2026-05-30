# 📂 Plano de Implementação — FileManager (Explorador de Arquivos)
## Versão 2 — Revisado após revisão com o responsável do projeto

> **Nota para a IA implementadora:** Este documento é um delta do plano v1. Leia o plano v1 original junto com este. As seções aqui presentes **substituem** as correspondentes no v1. O que não está aqui permanece exatamente igual ao v1.

---

## Mudanças Aprovadas Nesta Revisão

| # | Seção Afetada | Decisão |
|---|---|---|
| 1 | Drag & Drop — comportamento de conflito | Padrão Windows: pergunta e permite renomear ou substituir |
| 2 | Multi-seleção | Padrão Windows completo para todas as operações |
| 3 | Drag externo (para QGIS) | Suportado — arquivos devem ser arrastáveis para fora da janela |
| 4 | `on_open()` / reload | **Não alterar** — sem contexto suficiente |
| 5 | Reação ao projeto ser aberto | Via `SinalManager` (mecanismo já existente no projeto) |
| 6 | Multiplataforma | Windows-only confirmado — sem guard de SO necessário |
| 7 | Preview de conteúdo | Deixar porta aberta para v2 — não hardcodar "nunca preview" |

---

## 1. Drag & Drop — Comportamento de Conflito (substitui seção 4.2 e 6.5 do v1)

### 1.1 Drop Interno (mover dentro da root_folder)

Quando um arquivo/pasta é solto em um destino onde já existe um item com o mesmo nome, exibir diálogo de conflito **idêntico ao comportamento do Windows Explorer**:

```
┌──────────────────────────────────────────────────────────┐
│  Substituir ou ignorar arquivos                          │
├──────────────────────────────────────────────────────────┤
│  O destino já contém um arquivo chamado "relatorio.txt"  │
│                                                          │
│  [Substituir arquivo no destino]                         │
│  [Ignorar este arquivo]                                  │
│  [Manter ambos os arquivos]  ← renomeia o movido         │
└──────────────────────────────────────────────────────────┘
```

**Implementação:**
- Usar `MessageBox` customizado com 3 botões (C1 — confirmações via MessageBox).
- "Manter ambos": adicionar sufixo numérico ao arquivo movido (`relatorio (2).txt`, `relatorio (3).txt`, etc.), seguindo a convenção do Windows.
- Para múltiplos arquivos em conflito: exibir opção adicional "Fazer isso para todos os conflitos" (checkbox), antes de iterar.

**No código:**
```python
# Em FileTreeWidget, sobrescrever dropEvent:
def dropEvent(self, event):
    src_path = self._get_drag_source_path(event)
    dst_dir  = self._get_drop_target_dir(event)
    dst_path = dst_dir / Path(src_path).name

    # Guarda de segurança: não mover pasta para dentro de si mesma
    if Path(src_path) in Path(dst_dir).parents or Path(src_path) == Path(dst_dir):
        event.ignore()
        return

    if dst_path.exists():
        choice = self._show_conflict_dialog(dst_path.name)
        if choice == "substituir":
            shutil.move(str(src_path), str(dst_path))
        elif choice == "manter_ambos":
            dst_path = self._resolve_name_conflict(dst_path)
            shutil.move(str(src_path), str(dst_path))
        else:  # ignorar
            event.ignore()
            return
    else:
        shutil.move(str(src_path), str(dst_path))

    self.file_moved.emit(str(src_path), str(dst_path))
    event.accept()
```

### 1.2 Drop Externo — Arrastar para fora (ex: para o QGIS)

O `QTreeView` deve suportar drag iniciado internamente que pode ser solto em **aplicações externas** (QGIS, Windows Explorer, etc.).

**Implementação:**
- `setDragDropMode(QAbstractItemView.DragDrop)` — permite tanto drag interno quanto externo.
- Sobrescrever `startDrag()` para criar um `QDrag` com `QMimeData` contendo `urls` (lista de `QUrl` com `fromLocalFile(path)`).
- Aplicações externas que aceitam arquivos (como QGIS) consomem automaticamente `QMimeData` com `urls`.

```python
def startDrag(self, supported_actions):
    selected = self.selected_paths()
    if not selected:
        return

    mime = QMimeData()
    mime.setUrls([QUrl.fromLocalFile(p) for p in selected])

    drag = QDrag(self)
    drag.setMimeData(mime)
    drag.exec(Qt.CopyAction | Qt.MoveAction)
```

> **Nota:** Drag externo usa `CopyAction` por padrão (o arquivo não é deletado da origem quando solto no QGIS). Isso é o comportamento esperado — o QGIS recebe o path, não move o arquivo.

---

## 2. Multi-seleção — Padrão Windows Completo (substitui seção 4.2 do v1)

### 2.1 Configuração do QTreeView

```python
self.setSelectionMode(QAbstractItemView.ExtendedSelection)
# ExtendedSelection = Ctrl+clique, Shift+clique, Ctrl+A — idêntico ao Windows Explorer
```

### 2.2 Operações que devem respeitar multi-seleção

| Operação | Comportamento com múltiplos selecionados |
|---|---|
| **Deletar** (Del / Context Menu) | Confirma "Excluir X itens?" → deleta todos |
| **Mover** (Drag & Drop) | Move todos os selecionados |
| **Copiar path** (se implementado) | Copia todos os paths |
| **Renomear** | Disponível apenas quando 1 item selecionado (igual ao Windows) |
| **Criar arquivo** | Ignora seleção, cria na pasta do item selecionado (ou root) |

### 2.3 Deleção em lote

```python
def delete_selected(self) -> bool:
    paths = self.selected_paths()
    if not paths:
        return False

    count = len(paths)
    label = f"Excluir {count} itens?" if count > 1 else f'Excluir "{Path(paths[0]).name}"?'

    confirmed = MessageBox.show_question(label, "Esta ação não pode ser desfeita.")
    if not confirmed:
        return False

    errors = []
    for path in paths:
        try:
            if Path(path).is_dir():
                shutil.rmtree(path)
            else:
                os.remove(path)
            self.file_deleted.emit(path)
        except Exception as e:
            logger.error(f"Erro ao deletar {path}: {e}")
            errors.append(path)

    if errors:
        MessageBox.show_warning(f"Não foi possível excluir {len(errors)} item(ns).")

    return len(errors) == 0
```

### 2.4 Context Menu sensível à seleção

```python
def _build_context_menu(self) -> QMenu:
    menu = QMenu(self)
    selected = self.selected_paths()
    count = len(selected)

    if count == 1:
        menu.addAction("Renomear", self.rename_selected).setShortcut("F2")

    menu.addAction(
        f"Excluir {count} itens" if count > 1 else "Excluir",
        self.delete_selected
    ).setShortcut("Del")

    menu.addSeparator()
    menu.addAction("Criar Arquivo de Texto", self._create_text_file).setShortcut("Ctrl+N")
    menu.addAction("Atualizar", self.refresh).setShortcut("F5")
    menu.addSeparator()
    menu.addAction("Abrir Local no Explorer", self._open_in_explorer)

    return menu
```

---

## 3. Reação ao Projeto Ser Aberto — Via SinalManager (substitui nota da seção 4.1 do v1)

Quando o `SaveProjectPlugin` abre um novo projeto e atualiza o `root_folder` nas `sys_preferences`, o FileManager precisa reagir e recarregar a árvore.

**Mecanismo:** conectar ao sinal correspondente do `SinalManager` (sinal já existente no projeto — não criar novo sinal).

```python
# Em FileManagerPlugin.__init__ ou _build_ui():
SinalManager.instance().projeto_alterado.connect(self._on_project_changed)

def _on_project_changed(self):
    """Chamado pelo SinalManager quando o projeto ativo muda."""
    new_root = self.sys_preferences.get("root_folder", None)
    if new_root and new_root != self._current_root:
        self._current_root = new_root
        self._update_header_label(new_root)
        self.file_tree.set_root_path(new_root)
    elif not new_root:
        self._show_no_project_message()
```

> **Atenção para a IA implementadora:** O nome exato do sinal no `SinalManager` (`projeto_alterado` é placeholder) **deve ser verificado no código existente** antes de conectar. Não assumir o nome — consultar `core/signals/SinalManager.py` ou equivalente.

---

## 4. Preview de Conteúdo — Porta Aberta para v2 (adição ao v1)

### 4.1 O que NÃO fazer agora

- Não implementar preview nesta versão.
- Não hardcodar lógica que impeça preview futura (ex: não colocar `if True: return` ou comentários "never preview").

### 4.2 Como deixar a porta aberta

- O sinal `selection_changed(path: str | None)` já existe no plano v1. Na v2, um painel de preview pode simplesmente conectar a esse sinal.
- O `FileTreeWidget` não deve ter acoplamento com nenhum widget de preview — o sinal é suficiente para desacoplar.
- Documentar no código:

```python
# selection_changed é emitido sempre que a seleção muda.
# Um futuro painel de preview pode conectar-se a este sinal
# para exibir conteúdo de .txt, .py, .md, etc.
self.selection_changed = Signal(str)  # path ou None
```

---

## 5. "Abrir Local no Explorer" — Windows Only (confirma seção 4.2 do v1)

Projeto é Windows-only. Usar diretamente:

```python
def _open_in_explorer(self):
    path = self.selected_path()
    if not path:
        return
    # Se for arquivo, abre a pasta pai com o arquivo selecionado
    if Path(path).is_file():
        subprocess.Popen(f'explorer /select,"{path}"')
    else:
        subprocess.Popen(f'explorer "{path}"')
```

Sem guards de SO, sem `platform.system()` — é Windows-only por definição do projeto.

---

## 6. Resumo das Alterações no Contrato de Métodos Públicos (atualiza seção 4.2 do v1)

Métodos que mudaram de assinatura ou comportamento em relação ao v1:

| Método | v1 | v2 |
|---|---|---|
| `delete_selected()` | deleta item selecionado | deleta **todos** os selecionados, com MessageBox em lote |
| `selected_paths()` | listado como extra | **obrigatório** — base de todas as operações |
| `startDrag()` | não mencionado | sobrescrito para emitir `QMimeData` com `urls` (suporte externo) |
| `dropEvent()` | mencionado vagamente | sobrescrito explicitamente com lógica de conflito |
| `rename_selected()` | sempre disponível | disponível apenas com 1 item selecionado |

---

## 7. O que NÃO mudou

Tudo no plano v1 que não está coberto aqui permanece **exatamente igual**, incluindo:

- Estrutura de arquivos e diretórios
- Herança de `BasePlugin`
- `QFileSystemModel` como modelo de dados
- Trava de navegação via `setRootPath` + `setRootIndex`
- Sinais `file_renamed`, `file_deleted`, `file_created`, `file_moved`, `selection_changed`
- Registro no `ToolRegistry` e `ToolKey`
- Todos os contratos C1–C17
- Ordem de implementação
- Wireframe da UI
- Fluxos 6.1 (abrir pela primeira vez), 6.2 (renomear), 6.4 (criar arquivo)