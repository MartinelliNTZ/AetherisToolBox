# Estrutura de Classes — Aetheris ToolBox

> Documentação leve das classes atualmente ativas no projeto.

---

## 1. Ponto de Entrada

### `main.py` (raiz do projeto)
**Função:** Único executável. Duplo clique → `python main.py`.
- Insere a raiz do projeto no `sys.path`.
- Chama `BootStrap().run()` — singleton que orquestra toda a inicialização.

---

## 2. Bootstrap (Singleton)

### `core/config/BootStrap.py`
**Classe:** `BootStrap` (singleton)
**Função:** Centraliza toda a inicialização da aplicação em etapas:

| Etapa | Método | Descrição |
|---|---|---|
| 1 | `_setup_environment()` | Configura `TF_CPP_MIN_LOG_LEVEL=3`, filtra warnings |
| 2 | `_create_application()` | Cria `QApplication`, aplica `DarkCharcoalStyle`, fonte Segoe UI |
| 3 | `_register_tools()` | Instancia cada tool e registra no `ToolRegistry` (lazy) |
| 4 | `_create_main_window()` | Cria `MainWindow(tools=registry.get_all())` |
| 5 | `_show_and_run()` | Exibe janela e inicia `app.exec()` |

**Propriedades de acesso:**
- `BootStrap().window` → `MainWindow`
- `BootStrap().application` → `QApplication`

---

## 3. Modelo de Ferramenta

### `core/model/Tool.py`
**Classe:** `Tool`
**Função:** Representa uma ferramenta com **lazy loading**.
- `name` → nome visível
- `widget` → property que **só instancia o QWidget na primeira vez** que é acessada
- `tooltip` → texto de dica
- `is_loaded` → True se o widget já foi criado
- `unload()` → libera o widget da memória
- `to_dict()` → representação serializável

```python
tool = Tool(name="Console", widget_factory=lambda: ConsoleTool())
w = tool.widget  # só cria aqui
```

---

## 4. Registro de Ferramentas

### `core/config/tool_registry.py`
**Classe:** `ToolRegistry` (singleton)
**Função:** Registro centralizado de todas as ferramentas. Usa `Tool` objects.

| Método | Descrição |
|---|---|
| `register(name, widget_factory, tooltip)` | Adiciona ferramenta (lazy), retorna índice |
| `unregister(name)` | Remove pelo nome, descarrega widget |
| `get_all()` | Lista de objetos `Tool` na ordem de registro |
| `get(name)` | Busca por nome |
| `count()` | Quantidade de tools |
| `names()` | Lista de nomes |

**Onde registrar uma nova tool:** em `BootStrap._register_tools()`.

---

## 5. Núcleo da Interface

### `core/ui/ui_main.py`
**Classe:** `MainWindow(QMainWindow)`
**Função:** Janela principal que recebe `List[Tool]` via construtor.

```python
MainWindow(tools=List[Tool])
```

**Layout:**
- **AppBar** → barra de título frameless (min/max/close + drag)
- **Workspace** → QTabBar + QStackedWidget (tools via objetos Tool)
- **ProgressBar** → barra global no rodapé

**Métodos:**
- `get_tool(name)` → objeto `Tool` pelo nome
- `switch_to_tool(name)` → muda para aba específica
- `switch_to_console()` → atalho para aba Console

---

## 6. Workspace

### `core/ui/workspace.py`
**Classe:** `Workspace(QWidget)`
**Função:** Área de trabalho que gerencia ferramentas via abas com **lazy loading**.

- `register_tool(tool: Tool)` → registra um objeto `Tool`. O widget **só é instanciado** quando a aba é selecionada pela primeira vez.
- Placeholder `QWidget` até o primeiro acesso, depois substituído pelo widget real + `QScrollArea`.
- Sinal `current_tool_changed(index, widget)` ao trocar de aba.

---

## 7. Ferramentas

### `plugins/home/home_tool.py`
**Classe:** `HomeTool(QWidget)`
**Função:** Página inicial do software. Exibida por padrão ao abrir (aba ativa #0).
- Título "Aetheris ToolBox"
- Subtítulo + separador + placeholder informativo

### `plugins/console/console_tool.py`
**Classe:** `ConsoleTool(QWidget)`
**Função:** Console de execução compartilhado.
- `btn_clear_console` → limpa logs
- `txt_log` → `QTextBrowser` com HTML
- `anchorClicked` → sinal para links
- `append_log(html)`, `clear_log()`

---

## 8. Widgets de Interface

### `resources/widgets/app_bar.py`
**Classe:** `AppBar(QWidget)`
**Função:** Barra de título frameless. Ícone, título, botões min/max/close, toolbar lateral, suporte a arrasto.

### `resources/widgets/buttons.py`
| Classe | Função |
|---|---|
| `SimplePrimaryButton(QPushButton)` | Gradiente ouro — ações principais |
| `SimpleSecondaryButton(QPushButton)` | Escuro + texto dourado |
| `SimpleDangerButton(QPushButton)` | Vermelho — ações destrutivas |
| `SimpleGhostButton(QPushButton)` | Invisível, aparece no hover |
| `SimpleRemoveButton(QPushButton)` | Hover vermelho — remover |

> Arquivos soltos `primary_button.py`, `secondary_button.py`, `danger_button.py` são legado.

---

## 9. Estilos e Temas

### `resources/styles/styles.py`
| Classe | Função |
|---|---|
| `Palette` | Paleta 6 níveis de profundidade + acento ouro + status |
| `AppStyles` | Geração de QSS global e por componente |
| `DarkCharcoalStyle` | Compatibilidade legada |

---

## 10. Utilitários

### `utils/Preferences.py`
**Classe:** `Preferences`
**Função:** Gerencia configurações em JSON (`config/preferences.json`).

---

## 11. Componentes Desativados

> Preservados para rejunção futura:

| Arquivo | Classe | Função Original |
|---|---|---|
| `core/ui/hud_loader.py` | `HudCircularRingsLoader` | Overlay loader animado |
| `plugins/tensorflow_classifier/classification_tool.py` | `ClassificationTool` | UI de classificação raster |
| `plugins/tensorflow_classifier/main_controller.py` | `MainController` | Orquestrador da pipeline TF |

---

## 12. Fluxo de Inicialização (Atual)

```
main.py
    ↓
BootStrap().run()
    ├── _setup_environment()       → TF_CPP_MIN_LOG_LEVEL=3
    ├── _create_application()      → QApplication + DarkCharcoalStyle
    ├── _register_tools()          → ToolRegistry (lazy)
    │       ├── Tool("Home",       factory=HomeTool)
    │       ├── Tool("Console",    factory=ConsoleTool)
    │       └── Tool("Classifier", factory=ClassificationTool) [inativo]
    ├── _create_main_window()      → MainWindow(tools=registry.get_all())
    │       ├── AppBar()
    │       ├── Workspace()
    │       │   ├── [0] "Home"      → carregado na inicializacao
    │       │   ├── [1] "Console"   → carregado sob demanda
    │       │   └── [2] "Classifier" → carregado sob demanda
    │       └── QProgressBar()
    └── _show_and_run()            → window.show() + app.exec()