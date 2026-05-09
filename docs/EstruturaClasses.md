# Estrutura de Classes — Aetheris ToolBox

> Documentação leve das classes atualmente ativas no projeto (excluindo o módulo TensorFlow Classifier, que foi isolado/desativado).

---

## 1. Entrada da Aplicação

### `core/window/BootStrap.py`
**Classe:** _(script único, sem classe)_
**Função:** Launcher oficial da aplicação. Antes de importar qualquer coisa, silencia os warnings do TensorFlow (`TF_CPP_MIN_LOG_LEVEL=3`). Cria a `QApplication`, aplica o tema `DarkCharcoalStyle`, instancia a `MainWindow` e exibe a janela.


---

## 2. Núcleo da Interface

### `ui_main.py`
**Classe:** `MainWindow(QMainWindow)`
**Função:** Janela principal do Aetheris ToolBox.
- **AppBar** → barra de título com controles de janela (min/max/close) e arrasto.
- **Workspace** → gerenciador de abas (QTabBar + QStackedWidget).
- **ProgressBar** → barra de progresso global no rodapé.
- Atualmente exibe duas abas: **Classifier** (UI vazia, desativada) e **Console**.
- `__getattr__` redireciona `txt_log`, `anchorClicked`, `btn_clear_console` para o `ConsoleTool`.

---

## 3. Workspace

### `core/window/workspace.py`
**Classe:** `Workspace(QWidget)`
**Função:** Área de trabalho que gerencia múltiplas ferramentas via abas.
- `QTabBar` no topo + `QStackedWidget` para alternar entre ferramentas.
- `register_tool(name, widget, tooltip)` → registra uma ferramenta e retorna seu índice.
- Cada ferramenta ganha um `QScrollArea` automático.
- Sinal `current_tool_changed(index, widget)` emitido ao trocar de aba.

---

## 4. Widgets de Interface

### `resources/widgets/app_bar.py`
**Classe:** `AppBar(QWidget)`
**Função:** Barra de título personalizada para janela frameless.
- Ícone + título "Aetheris ToolBox".
- Botões de minimizar, maximizar/restaurar, fechar.
- Suporte a arrasto da janela (drag) via eventos de mouse.
- Toolbar lateral para adicionar botões de ação (`add_tool_button`, `add_tool_widget`).

### `resources/widgets/buttons.py`
**Classes:**
| Classe | Função |
|---|---|
| `SimplePrimaryButton(QPushButton)` | Botão principal gradiente ouro (ex: Executar). |
| `SimpleSecondaryButton(QPushButton)` | Botão secundário escuro com texto dourado. |
| `SimpleDangerButton(QPushButton)` | Botão vermelho para ações destrutivas (Cancelar). |
| `SimpleGhostButton(QPushButton)` | Botão invisível que aparece no hover (ações sutis). |
| `SimpleRemoveButton(QPushButton)` | Botão de remover com hover vermelho. |

Obs: Os arquivos individuais `primary_button.py`, `secondary_button.py`, `danger_button.py` são versões soltas (legado) das mesmas classes definidas em `buttons.py` — **ambas funcionam, mas a centralizada é a recomendada**.

---

## 5. Console

### `plugins/console/console_tool.py`
**Classe:** `ConsoleTool(QWidget)`
**Função:** Console de execução compartilhado. Exibe logs formatados com HTML e suporte a links.
- Toolbar com botão `btn_clear_console` ("Limpar Console").
- `txt_log` (`QTextBrowser`) para exibição de log.
- `anchorClicked` → sinal exposto para conectar eventos de clique em links.
- `append_log(html)` → adiciona mensagem formatada.
- `clear_log()` → limpa o console.

---

## 6. Estilos e Temas

### `resources/styles/styles.py`
**Classes:**

| Classe | Função |
|---|---|
| `Palette` | Paleta de cores com 6 níveis de profundidade, cores de texto, acento ouro, cores de status (sucesso/warning/danger). |
| `AppStyles` | Métodos estáticos que geram QSS para botões, labels, groupboxes, inputs, tabelas, scrollbars, progress bar, tabs, etc. |
| `DarkCharcoalStyle` | Classe de compatibilidade legada. Mapeia constantes antigas para `Palette`. Usada por `BootStrap.py` e `HudCircularRingsLoader`. |

---

## 7. Utilitários

### `utils/Preferences.py`
**Classe:** `Preferences`
**Função:** Gerenciamento de preferências em JSON.
- `loadpreferences()` → carrega do arquivo.
- `savepreferences(data)` → salva no arquivo.
- `get(key, default)`, `set(key, value)` → acesso a chaves individuais.
- Arquivo padrão: `config/preferences.json`.

---

## 8. Componentes Aninhados (desativados junto com o Classifier)

> Mantidos no código porém sem uso ativo no momento:

| Arquivo | Classe | Função Original |
|---|---|---|
| `core/ui/hud_loader.py` | `HudCircularRingsLoader(QWidget)` | Overlay animado com anéis concêntricos (loader de progresso). |
| `plugins/tensorflow_classifier/classification_tool.py` | `ClassificationTool(QWidget)` | UI da ferramenta de classificação raster. |
| `plugins/tensorflow_classifier/main_controller.py` | `MainController` | Orquestrador da pipeline de classificação. |

---

## 9. Fluxo de Inicialização (Atual)

```
BootStrap.py
    ↓
MainWindow.__init__()
    ├── AppBar()
    ├── Workspace()
    │   ├── register_tool("Classifier",   ClassificationTool) → inativo
    │   └── register_tool("Console",      ConsoleTool)
    └── QProgressBar()
    ↓
window.show()