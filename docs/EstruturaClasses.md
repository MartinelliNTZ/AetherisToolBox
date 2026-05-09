# Estrutura de Classes — Aetheris ToolBox

> Documentação das classes ativas no projeto.
> Última atualização: 09/05/2026

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
| 2 | `_init_logging()` | Limpa logs antigos via `LogCleanup` e registra início |
| 3 | `_create_application()` | Cria `QApplication`, aplica `DarkCharcoalStyle`, fonte Segoe UI |
| 4 | `_register_tools()` | Instancia cada tool e registra no `ToolRegistry` (lazy) |
| 5 | `_create_main_window()` | Cria `MainWindow(tools=registry.get_all())` |
| 6 | `_show_and_run()` | Exibe janela e inicia `app.exec()` |

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

### `core/model/BasePlugin.py`
**Classe:** `BasePlugin(QWidget)`
**Função:** Classe base para todos os plugins (ferramentas).

**Atributos fornecidos:**
- `self.logger` → `LogUtils(tool=tool_key, class_name=ClassName)` — instanciado no `__init__`
- `self.tool_key` → nome da ferramenta (ex: `"Console"`, `"LogViewer"`)

**Métodos (override nos filhos):**
- `load_prefs()` → carrega preferências do disco e aplica nos widgets
- `save_prefs()` → lê valores dos widgets e persiste no disco

```python
from core.model.BasePlugin import BasePlugin

class ConsoleTool(BasePlugin):
    def __init__(self, parent=None):
        super().__init__(tool_key="Console", parent=parent)
        self._build_ui()
        self.load_prefs()
        self.logger.info("Carregada", code="TOOL_READY")
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
| `get_definitions()` | Dicionário de definições `_TOOL_DEFINITIONS` |

**Definições:** As tools são registradas usando `ToolKey` (enum):

```python
_TOOL_DEFINITIONS = {
    ToolKey.HOME:       {"module": "plugins.home.home_tool",         "class_name": "HomeTool"},
    ToolKey.CONSOLE:    {"module": "plugins.console.console_tool",   "class_name": "ConsoleTool"},
    ToolKey.CLASSIFIER: {"module": "plugins.tensorflow_classifier.classification_tool", "class_name": "ClassificationTool"},
    ToolKey.LOGVIEWER:  {"module": "plugins.log_viewer.log_viewer",  "class_name": "LogViewerTool"},
}
```

---

## 5. Enum de Tool Keys

### `core/enum/ToolKey.py`
**Classe:** `ToolKey(str, Enum)`

| Variável | Valor |
|---|---|
| `ToolKey.HOME` | `"Home"` |
| `ToolKey.CONSOLE` | `"Console"` |
| `ToolKey.CLASSIFIER` | `"Classifier"` |
| `ToolKey.LOGVIEWER` | `"LogViewer"` |
| `ToolKey.SYSTEM` | `"System"` |

**Métodos:**
- `display_names()` → lista com todos os valores
- `from_name(name)` → busca pelo nome ou levanta `ValueError`

---

## 6. Sistema de Log

### `core/config/LogUtils.py`
**Classe:** `LogUtils`
**Função:** Logger estruturado em JSON. **Um único arquivo `log/YYYYMMDD-HHMMSS_AetherisToolBox.json` por execução do programa** — todas as instâncias escrevem no mesmo arquivo.

```python
from core.config.LogUtils import LogUtils

logger = LogUtils(tool="Console", class_name="ConsoleTool")
logger.info("Sistema inicializado")
logger.warning("Memoria baixa", code="MEM_LOW", free_mb=128)
logger.error("Falha ao conectar", code="CONN_ERR")
```

**Níveis:** `DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL`
```
DEBUG     #9CA3AF  (cinza)
INFO      #10B981  (verde)
WARNING   #F59E0B  (âmbar)
ERROR     #DC2626  (vermelho)
CRITICAL  #991B1B  (vermelho escuro)
```

### `core/config/LogCleanup.py`
**Classe:** `LogCleanup`
**Função:** Mantém apenas os N arquivos `.json` mais recentes em `log/`.

```python
LogCleanup.run(max_files=5)  # mantém só os 5 mais recentes
```

### `core/config/LogFilter.py`
**Classe:** `LogFilter`
**Função:** Utilitário estático para carregar, filtrar e ordenar eventos de log.

| Método | Descrição |
|---|---|
| `load_all()` | Carrega todos os eventos de todos os `.json` em `log/` |
| `filter_text(events, search)` | Filtra por texto (case-insensitive, varre todos os campos) |
| `filter_level(events, level)` | Filtra por nível exato |
| `sort(events, column, ascending)` | Ordena por coluna (timestamp, level, etc.) |

---

## 7. Diálogos

### `core/dialogs/LogDetailDialog.py`
**Classe:** `LogDetailDialog(QDialog)`
**Função:** Dialog de detalhes de um evento de log com texto selecionável e copiável.

```python
from core.dialogs.LogDetailDialog import LogDetailDialog
dialog = LogDetailDialog({"level": "INFO", "message": "OK"}, parent=self)
dialog.exec()
```

---

## 8. Color Provider

### `utils/ColorProvider.py`
**Classe:** `ColorProvider`
**Função:** Cores de fonte consistentes para visualização de logs.

| Método | Descrição |
|---|---|
| `level_color(level)` | Cor do nível (DEBUG=#9CA3AF, INFO=#10B981, etc.) |
| `tool_color(tool_name)` | Cor única por ferramenta (hash consistente, 10 cores na paleta) |
| `class_color(class_name)` | Cor única por classe (hash consistente, paleta diferente das tools) |
| `text_primary()` | Cor padrão `#DCDCDC` |

---

## 9. Núcleo da Interface

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

### `core/ui/workspace.py`
**Classe:** `Workspace(QWidget)`
**Função:** Área de trabalho que gerencia ferramentas via abas com **lazy loading**.

- `register_tool(tool: Tool)` → registra um objeto `Tool`. O widget **só é instanciado** quando a aba é selecionada pela primeira vez.
- Placeholder `QWidget` até o primeiro acesso, depois substituído pelo widget real + `QScrollArea`.
- Sinal `current_tool_changed(index, widget)` ao trocar de aba.

---

## 10. Ferramentas (Plugins)

### `plugins/home/home_tool.py`
**Classe:** `HomeTool(QWidget)`
**Função:** Página inicial do software. Exibida por padrão ao abrir (aba ativa #0).

### `plugins/console/console_tool.py`
**Classe:** `ConsoleTool(BasePlugin)`
**Função:** Console de execução compartilhado.
- `self.logger` → `LogUtils(tool="Console", class_name="ConsoleTool")`
- `append_log(html)`, `clear_log()`
- `load_prefs()` / `save_prefs()` — override vazio (sem preferências por enquanto)

### `plugins/log_viewer/log_viewer.py`
**Classe:** `LogViewerTool(BasePlugin)`
**Função:** Visualizador de logs com tabela, pesquisa e filtro.

**Layout:**
```
[Busca | Nivel ▼ | Exportar Filtro | Exportar Seleção | Refresh]
┌────────────────────────────────────────────────────────────────┐
│ timestamp          │ level │ tool    │ class      │ message    │
│ 2026-05-08 22:52   │ INFO  │ System  │ BootStrap  │ Inicial... │
└────────────────────────────────────────────────────────────────┘
```

**Funcionalidades:**
- Pesquisa por texto (filtra em tempo real)
- Filtro por nível (ALL, DEBUG, INFO, WARNING, ERROR, CRITICAL)
- Ordenação por coluna (clique no cabeçalho — alterna ASC/DESC)
- Seleção múltipla (CTRL / SHIFT)
- "Exportar Filtro" → copia eventos filtrados como TSV para clipboard
- "Exportar Seleção" → copia células selecionadas como TSV
- Duplo clique → `LogDetailDialog` com detalhes do evento
- Cores de fonte via `ColorProvider` (tool, class, level)
- Fundo escuro (`#0C0C0F`, alternado `#121216`)
- `load_prefs()` / `save_prefs()` — persiste search_text e level_filter

### `plugins/tensorflow_classifier/classification_tool.py`
**Classe:** `ClassificationTool(QWidget)`
**Função:** UI de classificação raster com redes neurais (inativo — preservado para rejunção futura).

---

## 11. Widgets de Interface

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

---

## 12. Estilos e Temas

### `resources/styles/styles.py`
| Classe | Função |
|---|---|
| `Palette` | Paleta 6 níveis de profundidade + acento ouro + status |
| `AppStyles` | Geração de QSS global e por componente |
| `DarkCharcoalStyle` | Compatibilidade legada (delega para `AppStyles`) |

---

## 13. Utilitários

### `utils/Preferences.py`
**Classe:** `Preferences`
**Função:** Gerencia preferências em `config/preferences.json` com suporte a seções por ferramenta.

```python
# Acesso antigo (raiz):
prefs = Preferences()
prefs.set("theme", "dark")
prefs.save()

# Novo — por ferramenta:
prefs = Preferences(section="LogViewer")
prefs.set("search_text", "erro")
prefs.set("level_filter", "ERROR")
prefs.save()

text = prefs.get("search_text", "")
```

**Estrutura do arquivo:**
```json
{
  "LogViewer": {
    "search_text": "",
    "level_filter": "ALL"
  },
  "Console": {
    "font_size": 12
  }
}
```

---

## 14. Fluxo de Inicialização (Atual)

```
main.py
    ↓
BootStrap().run()
    ├── _setup_environment()       → TF_CPP_MIN_LOG_LEVEL=3, warnings
    ├── _init_logging()            → LogCleanup + LogUtils("System", "BootStrap")
    │       └── LogCleanup.run(max_files=5)
    ├── _create_application()      → QApplication + DarkCharcoalStyle
    ├── _register_tools()          → ToolRegistry (lazy)
    │       ├── Tool("Home",       factory=HomeTool)
    │       ├── Tool("Console",    factory=ConsoleTool)
    │       ├── Tool("Classifier", factory=ClassificationTool) [inativo]
    │       └── Tool("LogViewer",  factory=LogViewerTool)
    ├── _create_main_window()      → MainWindow(tools=registry.get_all())
    │       ├── AppBar()
    │       ├── Workspace()
    │       │   ├── [0] "Home"      → carregado sob demanda
    │       │   ├── [1] "Console"   → carregado sob demanda
    │       │   ├── [2] "Classifier" → carregado sob demanda
    │       │   └── [3] "LogViewer" → carregado sob demanda
    │       ├── QProgressBar()
    │       └── logger.info("Construindo interface")
    └── _show_and_run()            → window.show() + app.exec()
        └── gera log/YYYYMMDD-HHMMSS_AetherisToolBox.json
```

---

## 15. Estrutura de Diretórios

```
AetherisToolBox/
├── main.py                     ← Ponto de entrada
├── core/
│   ├── config/
│   │   ├── BootStrap.py        ← Singleton de inicialização
│   │   ├── LogCleanup.py       ← Limpeza de logs antigos
│   │   ├── LogFilter.py        ← Carregar, filtrar, ordenar logs
│   │   ├── LogUtils.py         ← Logger JSON (um arquivo por execução)
│   │   └── tool_registry.py    ← Registro centralizado de ferramentas
│   ├── dialogs/
│   │   └── LogDetailDialog.py  ← Dialog de detalhes de log
│   ├── enum/
│   │   └── ToolKey.py          ← Enum com chaves das ferramentas
│   ├── model/
│   │   ├── BasePlugin.py       ← Classe base para plugins
│   │   └── Tool.py             ← Modelo de ferramenta (lazy loading)
│   └── ui/
│       ├── ui_main.py          ← Janela principal
│       └── workspace.py        ← Gerenciador de abas (lazy)
├── plugins/
│   ├── console/console_tool.py     ← Console de execução
│   ├── home/home_tool.py           ← Página inicial
│   ├── log_viewer/log_viewer.py    ← Visualizador de logs
│   └── tensorflow_classifier/      ← Classificação raster (inativo)
├── resources/
│   ├── styles/styles.py        ← Paleta + Estilos QSS
│   └── widgets/
│       ├── app_bar.py          ← Barra de título frameless
│       └── buttons.py          ← Botões reutilizáveis
└── utils/
    ├── ColorProvider.py        ← Cores consistentes (level, tool, class)
    ├── Preferences.py          ← Preferências por ferramenta (JSON)
    └── log/                    ← Arquivos de log (.json)