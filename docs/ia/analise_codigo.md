# 🔍 Análise de Código — Aetheris ToolBox

> **Data:** 25/05/2026  
> **Objetivo:** Identificar violações de contrato, problemas estruturais, brechas e oportunidades de otimização.  
> **Metodologia:** Análise manual dos arquivos-fonte vs. contratos em `docs/ia/contracts.md`.

---

## 🚨 VIOLAÇÕES DE CONTRATO (Críticas)

### 1. Contrato 3 — Logger: `print()` no BootStrap

**Arquivo:** `core/config/BootStrap.py` (linha 119–120)

```python
mgr.tool_opened.connect(
    lambda name: print(f"[SignalManager] Ferramenta iniciada: {name}")
)
```NAO PRECISA MECHER ISSO E PAENAS DEBUG INTERNO" MAS VC TA CORRETO E QUEBRA DE CONTRATO
NA VERSAO FINAL SERA TIRADO'''

### 2. Contrato 9 — Código Morto: chave `"module"` no ThemeManager.THEMES

**Arquivo:** `resources/styles/ThemeManager.py` (linhas 42–68)

```python
THEMES: dict[str, dict] = {
    "dark_charcoal": {
        "module": "resources.styles.DarkCharcoalTheme",  # ← NUNCA usado
        "class":  DarkCharcoalTheme,                      # ← usado diretamente
        "label":  "Dark Charcoal",
        ...
    },
    ...
}
```

**Problema:** A chave `"module"` nunca é usada em runtime. O carregamento é feito via `entry["class"]()` diretamente (linha 159). A documentação dentro do arquivo (linhas 20–22) instrui a adicionar `"module"`, mas este campo não tem função — é código morto.

**Impacto:** Baixo (apenas poluição), mas viola Contrato 9.

**Correção:** Remover a chave `"module"` de todas as entradas e atualizar a documentação interna do arquivo.

#AQUI VC ENCONTROU UM PROBLRMA A IDEIA DO MODULO E FAZER CARREGAMENTO LAZY DAS CLASSES DE 
STYLE SEM USAR O CARREMENTO DIRETO, OU SEJA SO CARREGA A STYLE QUE FOR USA USADA E NAO IMPORTA 
AS DEMAIS, PODE IMPLEMENTAR PARA MIM?

---

### 3. Contrato 4 — Preferências: instância direta de `Preferences` no `ConfigurationPlugin`

**Arquivo:** `plugins/configuration_manager/ConfigurationPlugin.py` (linhas 68–70, 75–77)

```python
def save_prefs(self):
    ...
    from utils.Preferences import Preferences          # import interno repetido
    from core.enum.ToolKey import ToolKey
    Preferences.save_tool_prefs(ToolKey.SYSTEM, self.sys_preferences)
```

O mesmo padrão se repete em `_on_theme_changed()` (linhas 75–77).

**Problema:** O `BasePlugin` já fornece `self.sys_preferences`. O contrato 4 diz _"Não instancie Preferences manualmente. Use self.preferences"_, mas `Preferences.save_tool_prefs()` é chamada estaticamente. Embora o contrato permita uso direto para quem não herda de BasePlugin, este plugin **herda** de BasePlugin — deveria usar `self.preferences` / `self.sys_preferences` e delegar o save ao `BasePlugin.force_save_prefs()` ou ao fechamento automático.

**Correção:** Remover as chamadas diretas a `Preferences.save_tool_prefs()` e sobrescrever `_on_theme_changed()` para apenas modificar `self.sys_preferences["theme"]`, deixando o `closeEvent` do BasePlugin salvar automaticamente. Ou usar `self.force_save_prefs(ToolKey.SYSTEM)`.

---
CORRETAMENETE OBSERVADO. FILHOS DE BASE PLUGIN NAO PRECISAM CHAMAR A CLASSE Preferences
retire as chamadas

### 4. Contrato 9 — Código Morto: `ConfigCarregarDialog.py` e `ConfigSalvarDialog.py`

**Arquivo:** `core/dialogs/ConfigCarregarDialog.py`, `core/dialogs/ConfigSalvarDialog.py`

**Status:** Suspeito — verificar se são importados em algum lugar.
NAO SEI AINDA, POR ENQUANTO DEIXE ELAS LA 
---

### 5. Contrato 9 — Código Morto: `utils/ColorProvider.py`

**Arquivo:** `utils/ColorProvider.py`

**Status:** Suspeito — se não for usado em lugar nenhum, viola Contrato 9.
VERIFIQUE SE consoleplugin usa color provider se nao verifique se ele nao ta fazendo as responsabilidade de colocr provider e tranfira para la 
---

## ⚠️ PROBLEMAS ESTRUTURAIS (Potencial dor de cabeça futura)

### 6. Caminho relativo no `Preferences._DEFAULT_PATH`

**Arquivo:** `utils/Preferences.py` (linha 49)

```python
_DEFAULT_PATH: Path = Path("config") / "preferences.json"
```

**Problema:** Caminho relativo ao **CWD (current working directory)**. Se a aplicação for iniciada de outro diretório (atalho, task scheduler, IDE debugging), o arquivo `config/preferences.json` não será encontrado. O `main.py` resolve corretamente com `project_root = Path(__file__).resolve().parent`, mas o `Preferences` não usa isso.

**Impacto:** ALTO — perda de configurações do usuário se CWD ≠ `project_root`.

**Correção:** Usar resolução absoluta:
```python
@classmethod
def _project_root(cls) -> Path:
    return Path(__file__).resolve().parent.parent

_DEFAULT_PATH: Path = None  # lazy init

@classmethod
def _get_path(cls) -> Path:
    if cls._DEFAULT_PATH is None:
        cls._DEFAULT_PATH = cls._project_root() / "config" / "preferences.json"
    return cls._DEFAULT_PATH
```
NAO IMPLEMENTAR NADA DEIXE COM ESTA 
---

### 7. `SignalManager()` vs `SignalManager.instance()` — dupla porta de criação

**Arquivo:** `core/manager/SignalManager.py` (linhas 34–38)

```python
def __init__(self, parent=None):
    if SignalManager._instance is not None:
        raise RuntimeError("SignalManager é singleton. Use SignalManager.instance()")
    super().__init__(parent)
    SignalManager._instance = self
```

**Problema:** Qualquer código que acidentalmente chame `SignalManager()` (sem `.instance()`) vai **travara aplicação** com RuntimeError se o singleton já existir. Mas se chamar **antes** de `instance()`, cria uma segunda "porta de entrada" que não passa pelo controle central.

**Impacto:** Médio — é frágil para um singleton crítico.

**Correção:** Redirecionar `__init__` para `instance()`:
```python
def __new__(cls, parent=None):
    if cls._instance is not None:
        return cls._instance
    return super().__new__(cls)
```
PODE IMPLEMENTAR ISSO
---

### 8. `WorkspaceManager._build()` — BOTH tools só vão para side workspace

**Arquivo:** `core/config/WorkspaceManager.py` (linhas 117–120)

```python
elif tool.category == CategoryTool.BOTH:
    self._side_workspace.register_tool(tool)   # ← SEMPRE no side
```

**Problema:** Ferramentas BOTH (como `LogViewer` e `Configuration`) são registradas **apenas** no side workspace na inicialização. O `open_tool()` (linha 167–170) mantém essa lógica: só vai para central se NÃO estiver aberta no side. Isso significa que na primeira abertura, BOTH tools sempre aparecem no side, nunca no central. O usuário precisa mover manualmente.

**Impacto:** Médio — comportamento inconsistente com a expectativa de que BOTH = pode estar em ambos, mas o padrão deveria ser configurável ou respeitar último estado.

**Correção:** Salvar em `sys_preferences` qual workspace foi o último usado para cada tool BOTH.
NAO IMPLEMENTE NADA AINDA PODE PERMANECER COMO ESTA 
---

### 9. `ExceptionHandler` importa módulos pesados no topo

**Arquivo:** `core/config/ExceptionHandler.py` (linhas 36–40)

```python
from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import QApplication
from core.config.LogUtils import LogUtils
from utils.MessageBox import MessageBox
```

**Problema:** `ExceptionHandler.install()` é chamado **antes** da `QApplication` ser criada (BootStrap linha 88). Importar `QApplication`, `QTimer`, `MessageBox` no topo do módulo não quebra porque são apenas imports, mas `MessageBox` importa `LogUtils` que importa `QWidget` etc. — uma cascata de imports que atrasa o startup e pode causar erros se houver circularidade.

**Impacto:** Baixo no momento, mas pode causar bugs sutis se o startup falhar.

**Correção:** Mover imports para dentro dos métodos que realmente precisam deles (lazy import), ou isolar as importações pesadas.
PODE FAZER ESSA OTIMIZACAO DESDE QUE RESPEITE O FUNCIONAMENTO DO PLUGIN 
---

### 10. `ConfigurationPlugin` — duplicação de save

**Arquivo:** `plugins/configuration_manager/ConfigurationPlugin.py`

Dois métodos fazem exatamente a mesma coisa:
- `save_prefs()` (linhas 63–70)
- `_on_theme_changed()` (linhas 72–81)

Ambos salvam `Preferences.save_tool_prefs(ToolKey.SYSTEM, self.sys_preferences)`. A única diferença é que `_on_theme_changed()` também dá logger.

**Impacto:** Baixo (DRY violado), médio se um dia a lógica de save mudar e só um método for atualizado.

**Correção:** `_on_theme_changed()` deveria apenas modificar `self.sys_preferences["theme"]` e chamar `self.save_prefs()`, que já faz o persist.
CONCORDO, PODE IMPLEMENTAR ISSO 
---

## ⚡ OPORTUNIDADES DE OTIMIZAÇÃO

### 11. Imports dentro de métodos vs. módulo

**Ocorre em vários arquivos:**
- `plugins/BasePlugin.py` — `from resources.widgets.PluginPage import PluginPage` dentro de `_build_ui()`
- `core/ui/ui_main.py` — `from core.config.LogUtils import LogUtils` dentro de `_build_ui()` e `_setup_resize_mode()`
- `plugins/configuration_manager/ConfigurationPlugin.py` — `from utils.Preferences import Preferences` + `from core.enum.ToolKey import ToolKey` em **dois** métodos

**Sugestão:** Mover para nível de módulo. Imports lazy dentro de métodos só se justificam para quebra de dependência circular ou lazy loading pesado. Isso não é o caso aqui — são imports leves que poluem o código e dificultam manutenção.
PODE IMPLEMENTAR A MUDANACA 
---

### 12. `BaseTheme` — herança plana com ~80 atributos

**Arquivo:** `resources/styles/BaseTheme.py`

**Problema:** ~80 atributos de classe que cada tema precisa sobrescrever. Se um tema novo esquecer de sobrescrever 1 atributo, ele fica com `""` ou `0` — sem erro em tempo de compilação, só um bug visual silencioso.

**Sugestão:** Usar `@abc.abstractmethod` ou `__init_subclass__` que valide em tempo de importação se todos os atributos foram sobrescritos:
```python
def __init_subclass__(cls, **kwargs):
    super().__init_subclass__(**kwargs)
    missing = [attr for attr in BaseTheme.__dict__
               if not attr.startswith('__') and not callable(getattr(cls, attr, None))
               and getattr(cls, attr) == getattr(BaseTheme, attr, None)]
    if missing:
        raise TypeError(f"Tema {cls.__name__} não sobrescreveu: {missing}")
```
NAO FAÇA NADA POR ENQUANTO
---

### 13. `AppStyles._THEME_COLORS_CACHE` — cache frágil

**Arquivo:** `resources/styles/AppStyles.py` (linhas 361–408)

```python
_THEME_COLORS_CACHE: dict = {}
cache_id = id(t)
if cls._THEME_COLORS_CACHE.get("_cache_id") != cache_id:
    ...
```

**Problema:** Usa `id(t)` como chave de cache. `id()` pode ser reutilizado se o objeto anterior for garbage-collected. É improvável em runtime normal, mas possível com recarga de tema.

**Sugestão:** Usar `ThemeManager.current_key` como chave, que é a string literal do tema.
CONCORDO PELNAMENTE
---

### 14. `_make_factory` em ToolRegistry — perda de tipagem

**Arquivo:** `core/config/ToolRegistry.py` (linhas 29–43)

```python
def _make_factory(module_path: str, class_name: str) -> Callable[[], QWidget]:
    def factory() -> QWidget:
        mod = __import__(module_path, fromlist=[class_name])
        cls = getattr(mod, class_name)
        return cls()
    return factory
```

**Problema:** Se o `module_path` ou `class_name` estiver errado (ex: renomeou o arquivo mas esqueceu de atualizar o registro), o erro só aparece em runtime quando a ferramenta for aberta pela primeira vez. Não há validação no startup.

**Sugestão:** Adicionar validação opcional no `register_default_tools()`:
```python
def register_default_tools(self):
    for name, tool in self._TOOLS.items():
        # Validação de factory (opcional, pode ser flag)
        if not hasattr(tool, '_validated'):
            try:
                widget = tool.widget
                widget.deleteLater()
            except Exception as e:
                _logger.error(f"Tool '{name}' falhou no factory test", ...)
```
NEGADO NAO PRECISA DESSA FUNCAO 
---

### 15. BasePlugin.closeEvent — logger chamado mesmo sem logger

**Arquivo:** `plugins/BasePlugin.py` (linhas 108–123)

```python
def closeEvent(self, event) -> None:
    self.logger.info("Ferramenta sendo fechada...")
    self.save_prefs()
    self.force_save_prefs()
    self.logger.info("Preferências persistidas ao fechar")
    SignalManager.instance().tool_closed.emit(self.tool_key)
    super().closeEvent(event)
```

**Problema:** `save_prefs()` é chamado e imediatamente depois `force_save_prefs()`. Se `save_prefs()` já persiste (como no ConfigurationPlugin), `force_save_prefs()` persiste de novo — **duplo save** desnecessário em disco.

**Sugestão:** Unificar: `save_prefs()` só atualiza o dict, `force_save_prefs()` persiste. No `closeEvent`, chamar só `force_save_prefs()`. Remover `self.save_prefs()` se ele não faz nada além de atualizar dict.
NAO FAÇA NADA DEIXE COMO ESTA 
---

## 📋 Verificações Automatizadas (OK — Sem Violações)

- ✅ **QMessageBox**: Nenhum import direto encontrado. O único uso é via `MessageBox`.
- ✅ **QFileDialog**: Nenhum import direto encontrado. Tudo via `ExplorerUtils`.
- ✅ **`except:` sem `as e`**: Nenhum caso encontrado. Todos os excepts seguem o padrão `as e`.
- ✅ **`print()` residuals**: Nenhum `print()` solto encontrado (exceto fallbacks do `main.py` e `ExceptionHandler`, que são permitidos pelo contrato).
- ✅ **`QMessageBox` imports**: Zero ocorrências fora de `utils/MessageBox.py`.

---

## 📝 Resumo Final

| Categoria | Quantidade |
|---|---|
| 🚨 Violações de Contrato | 5 |
| ⚠️ Problemas Estruturais | 5 |
| ⚡ Oportunidades de Otimização | 5 |
| ✅ Verificações Automatizadas OK | 5 |
| **Total de itens** | **20** |

---

## 🎯 Prioridade de Correção Recomendada

### 🔴 Imediata (pode causar perda de dados)
1. **Item 6** — Caminho relativo no `Preferences._DEFAULT_PATH`
2. **Item 3** — `ConfigurationPlugin` ignorando o save automático do BasePlugin

### 🟡 Alta (violações de contrato explícitas)
3. **Item 1** — `print()` no BootStrap
4. **Item 2** — chave `"module"` morta no ThemeManager
5. **Item 10** — Duplicação de save no ConfigurationPlugin
6. **Item 8** — BOTH tools sempre no side workspace

### 🟢 Média (qualidade e manutenibilidade)
7. **Item 11** — Imports dentro de métodos
8. **Item 12** — BaseTheme sem validação de herança
9. **Item 13** — Cache frágil do AppStyles
10. **Item 14** — Factory sem validação no startup
11. **Item 15** — Duplo save no closeEvent do BasePlugin

### ⚪ Baixa (cosméticos/refatoração futura)
12. **Item 7** — SignalManager com dupla porta de criação
13. **Item 4** — ConfigCarregarDialog/SalvarDialog suspeitos de código morto
14. **Item 5** — ColorProvider suspeito de código morto
15. **Item 9** — ExceptionHandler com imports pesados no topo
