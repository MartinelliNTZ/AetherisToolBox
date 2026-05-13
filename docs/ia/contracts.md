# 📜 Contratos do Sistema — Aetheris ToolBox

Contratos são regras imutáveis. Todo código produzido para o Aetheris ToolBox DEVE respeitar estas regras. Violações causam reject automático.

---

## 🔴 Contrato 1 — Mensagens ao Usuário

```
QMessageBox é PROIBIDO. Use MessageBox de utils.MessageBox.
```

`from PySide6.QtWidgets import QMessageBox` — proibido em todo o projeto.
Única exceção: `utils/MessageBox.py` (a própria implementação).

## 🔴 Contrato 2 — Tratamento de Exceções

```
Todo except DEVE capturar a exceção com 'as e' E logar.
```

```python
# ✅ Correto
except ValueError as e:
    logger.error("valor invalido", code="VAL_ERR", error=str(e))
```

```python
# ❌ Proibido
except:
    pass

# ❌ Proibido
except Exception:
    print("deu erro")
```

## 🔴 Contrato 3 — Logger

```
Use LogUtils (logger via BasePlugin ou LogUtils direto). Não use print().
```

Única exceção: fallbacks em `ExceptionHandler._python_excepthook` e `main.py` quando o sistema de log não está disponível (pré-startup).

## 🔴 Contrato 4 — Preferências

```
Não instancie Preferences manualmente. Use self.preferences.
```

O `BasePlugin` já fornece `self.preferences`. Ferramentas que não herdam de BasePlugin podem instanciar `Preferences` normalmente (como feito nos controllers).

## 🔴 Contrato 5 — Importação de Ferramentas

```
Sempre use ToolRegistry. Nunca importe plugins diretamente no core.
```

O carregamento dinâmico (Lazy Loading) é obrigatório. Plugins são registrados no `ToolRegistry` com caminho de módulo, não importados estaticamente.

## 🔴 Contrato 6 — Estrutura de Plugins

```
Plugin herda de BasePlugin, implementa load_prefs() e save_prefs().
```

Métodos `on_open()` e `on_close()` são opcionais. `load_prefs()` deve ser chamado no `__init__` após montar a UI.

## 🔴 Contrato 7 — Sinais

```
Use SignalManager para comunicação entre componentes. Não acople plugins diretamente.
```

Nunca um plugin deve conhecer ou importar outro plugin. Comunicação é via sinais do `SignalManager`.

## 🔴 Contrato 8 — Dependências Externas

```
Não adicione dependências novas sem registrar em requirements.txt.
```

Qualquer novo pip install DEVE ter o nome e versão adicionados ao `requirements.txt`.

## 🔴 Contrato 9 — Código Morto

```
Nenhum import, classe, função ou variável não utilizado.
```

Remove imports mortos antes de finalizar. Não deixe `print()`, comentários de debug ou código comentado.

## 🔴 Contrato 10 — Categorias de Ferramentas

```
CENTRAL → abas no topo. SIDE → painel lateral. BOTH → pode ir para ambos.
```

Definido em `CategoryTool` e no registro do `ToolRegistry`. Siga o padrão das ferramentas existentes.

## 🔴 Contrato 11 — Widgets Reutilizáveis (Composição Obrigatória)

```
NUNCA importe de PySide6.QtWidgets diretamente.
Sempre verifique em resources/widgets/ se já existe um widget pronto.
Se não existir, CRIE o widget em resources/widgets/.
```

**Regras:**
- **Abstraia componentes compostos** — se você precisa de um label + caixa de texto + botão, provavelmente isso é UM widget composto, não 3 widgets isolados. Crie uma classe em `resources/widgets/` que empacote os 3.
- **Modifique widgets existentes** para adicionar funcionalidades, desde que mantenha compatibilidade retroativa. É preferível estender um widget existente a criar um novo similar.
- **Nunca** use `QHBoxLayout` / `QVBoxLayout` solto com widgets brutos do Qt para criar o mesmo padrão que já existe em `resources/widgets/`.

```python
# ✅ Correto — usa widget existente
from resources.widgets.SimpleSelector import SimpleSelector
selector = SimpleSelector("Imagem:", file_filter="*.tif")

# ✅ Correto — cria widget composto novo em resources/widgets/
# resources/widgets/MeuWidgetComposto.py
class MeuWidgetComposto(QWidget):
    def __init__(self, ...):
        # label + lineedit + botão encapsulados aqui
        ...

# ❌ Proibido — widget bruto do Qt sem verificar se já existe
from PySide6.QtWidgets import QLabel, QLineEdit, QPushButton
# montando manualmente toda vez que precisar

# ❌ Proibido — criar widget dentro do plugin sem abstrair
class MeuPlugin(BasePlugin):
    def _build_ui(self):
        layout = QVBoxLayout(self)
        row = QHBoxLayout()  # Isso deveria ser um SimpleSelector!
        row.addWidget(QLabel("Caminho:"))
        row.addWidget(QLineEdit())
        row.addWidget(QPushButton("..."))
```

## 🔴 Contrato 12 — Documentação Reflexiva

```
Toda modificação que altere funcionalidade ou exija novo contrato
DEVE atualizar a documentação correspondente.
```

**Regras:**
- Ao criar um novo widget em `resources/widgets/`, adicione-o à skill `docs/skills/widgets_skill.md`.
- Ao criar um novo contrato, adicione-o neste arquivo e referencie no `docs/ia/agent.md`.
- Ao modificar comportamento existente, verifique se as skills e contratos ainda refletem a realidade.
- Documentação desatualizada é considerada bug.

## 🔴 Contrato 13 — ToolRegistry é a Única Fonte de Configuração de Tools

```
ToolRegistry centraliza TODAS as ferramentas.
Nenhum outro módulo cria, configura ou modifica objetos Tool.
```

**Regras:**
- `ToolRegistry._TOOLS` contém a definição completa de cada ferramenta: nome, título, factory, tool_type, category, show_in_toolbar, menu_category, etc.
- A `MainWindow` recebe a tool list PRONTA de `ToolRegistry.get_all()` — não altera nem filtra.
- O `MenuManager` recebe a tool list de `ToolRegistry.get_all()` e filtra internamente quem vai para toolbar e quem vai para menu.
- Nenhum outro módulo pode instanciar `Tool()` diretamente ou modificar propriedades de uma tool registrada.

```python
# ✅ Correto — ToolRegistry define tudo
_TOOLS = {
    "Preferences": Tool(
        name="Preferences",
        widget_factory=_make_factory(...),
        show_in_toolbar=False,
        menu_category=MenuCategory.SYSTEM,
    ),
}

# ❌ Proibido — configurar tool fora do ToolRegistry
tool.show_in_toolbar = False  # em qualquer outro lugar
```

## 🔴 Contrato 14 — MenuManager Encapsula MenuBar + Toolbar

```
MenuManager é o ÚNICO responsável por instanciar e configurar
a MenuBar e a toolbar. A MainWindow apenas POSICIONA os widgets.
```

**Regras:**
- `MenuManager.build()` constrói tanto a `MenuBar` quanto a `toolbar_widget`.
- A `MainWindow` acessa `manager.menu_bar` e `manager.toolbar_widget` como propriedades prontas.
- Sinais de clique (toolbar e menu) convergem para um único sinal: `MenuManager.tool_activated`.
- Sinais de `sair_clicked` e `sobre_clicked` são propagados pelo `MenuManager`.
- A `MainWindow` NÃO importa `MenuBar` diretamente — só se comunica via `MenuManager`.

```python
# ✅ Correto — MainWindow usa MenuManager como caixa preta
manager = MenuManager()
manager.build()
manager.tool_activated.connect(self._on_tool_activated)
manager.sair_clicked.connect(self.close)
root_layout.addWidget(manager.menu_bar)
root_layout.addWidget(manager.toolbar_widget)

# ❌ Proibido — MainWindow manipular MenuBar ou toolbar diretamente
from resources.widgets.MenuBar import MenuBar  # não deve existir no ui_main
menu_bar = MenuBar()
menu_bar.add_menu_items(...)  # isso é responsabilidade do MenuManager
```

## 🔴 Contrato 15 — MenuCategory para Ferramentas de Menu

```
Ferramentas com menu_category definido aparecem no menu suspenso.
Ferramentas SEM menu_category não vão para o menu.
```

**Regras:**
- `menu_category` é definido no `ToolRegistry._TOOLS`, não em runtime.
- `MenuCategory.SYSTEM` → menu "Sistema"
- `MenuCategory.FILE` → menu "Arquivo" (futuro)
- `MenuCategory.HELP` → menu "Ajuda" (futuro)
- Ferramentas com `show_in_toolbar=False` + `menu_category=MenuCategory.SYSTEM` só aparecem no menu, nunca na toolbar.
