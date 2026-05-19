# Skill: Criação de Novas Ferramentas (Plugins)

Este guia descreve o processo padrão para criar e registrar uma nova ferramenta no **Aetheris ToolBox**, garantindo a integração com o sistema de logs, gerenciamento de sinais, carregamento dinâmico (Lazy Loading) e reutilização de widgets.

> ⚠️ **Antes de começar**, consulte:
> - `docs/skills/widgets_skill.md` — verifique se já existe um widget pronto para sua UI
> - `docs/ia/contracts.md` (Contrato 11) — regras sobre composição de widgets
> - `docs/skills/preferences_skill.md` — obrigatório implementar load/save_prefs
> - `docs/skills/log_utils_skill.md` — obrigatório logar eventos críticos

---

## 🛠 Passo 1: Definir a Identidade da Ferramenta

Toda ferramenta precisa de uma chave única no sistema. Adicione o nome da sua ferramenta ao Enum `ToolKey`.

**Arquivo:** `core/enum/ToolKey.py`
```python
class ToolKey(str, Enum):
    ...
    MINHA_FERRAMENTA = "MinhaFerramenta"
```

---

## 🏗 Passo 2: Implementar o Widget do Plugin

Crie um novo diretório em `plugins/` e implemente sua classe herdando de `BasePlugin`. Isso garante que sua ferramenta tenha acesso automático ao `self.logger` e participe do ciclo de vida de sinais (abertura/fechamento).

**Regras de UI (Contrato 11):**
1. **NUNCA** importe widgets brutos de `PySide6.QtWidgets` sem antes verificar em `resources/widgets/`.
2. Se o componente que você precisa é composto (ex: label + campo + botão), provavelmente já existe ou deve ser criado como widget único em `resources/widgets/`.
3. Consulte `docs/skills/widgets_skill.md` para ver a lista completa de widgets disponíveis.

**Arquivo:** `plugins/minha_ferramenta/main_widget.py`
```python
from core.model.BasePlugin import BasePlugin
from resources.widgets.SimplePrimaryButton import SimplePrimaryButton  # ✅ widget reutilizável
from resources.widgets.GroupDiv import GroupDiv                          # ✅ container com título

class MinhaFerramentaWidget(BasePlugin):
    def __init__(self, parent=None):
        super().__init__(tool_key="MinhaFerramenta", parent=parent)
        self._build_ui()
        self.load_prefs()
        self.logger.info("Ferramenta inicializada com sucesso!", code="TOOL_READY")

    def _build_ui(self):
        layout = QVBoxLayout(self)
        grupo = GroupDiv("Configurações")
        # ... adicionar widgets do grupo
        layout.addWidget(grupo)

        btn = SimplePrimaryButton("EXECUTAR")
        btn.clicked.connect(self._on_executar)
        layout.addWidget(btn)

    def load_prefs(self):
        """Obrigatório — carrega preferências salvas."""
        pass

    def save_prefs(self):
        """Obrigatório — salva preferências."""
        pass
```

---

## 📝 Passo 3: Registrar no ToolRegistry

Para que a ferramenta apareça na interface, ela deve ser registrada no `ToolRegistry`. É aqui que definimos onde ela será exibida e como o Python deve importá-la.

**Arquivo:** `core/config/ToolRegistry.py`
```python
# Dentro do dicionário _TOOLS:
ToolKey.MINHA_FERRAMENTA.value: Tool(
    name=ToolKey.MINHA_FERRAMENTA.value,
    title="Minha Nova Tool",
    widget_factory=_make_factory(
        "plugins.minha_ferramenta.main_widget", "MinhaFerramentaWidget"
    ),
    tooltip="Descrição curta que aparece no menu",
    tool_type=ToolType.RASTER,      # Define o ícone e grupo na AppBar
    category=CategoryTool.CENTRAL,  # CENTRAL (Abas) ou SIDE (Painel Lateral)
),
```

---

## 🎨 Passo 4: Ícones e Interface (Opcional)

1. **Ícone**: Adicione um arquivo `.ico` com o mesmo nome da ferramenta em `resources/icons/MinhaFerramenta.ico`. O `IconManager` o encontrará automaticamente.
2. **Menu**: O `MenuManager` lerá o `ToolType` definido no registro e adicionará o botão da ferramenta ao grupo correspondente na barra superior.

---

## ✅ Checklist de Verificação
- [ ] A chave em `ToolKey` é idêntica ao `tool_key` passado no `super().__init__`.
- [ ] O caminho do módulo no `_make_factory` usa pontos (ex: `plugins.pasta.arquivo`).
- [ ] A categoria `CategoryTool` está correta (ferramentas de análise costumam ser `CENTRAL`).
- [ ] Se a ferramenta for `BOTH`, ela será registrada no `SideWorkspace` mas poderá ser movida.
- [ ] **Widgets reutilizáveis**: consultei `docs/skills/widgets_skill.md` antes de criar UI? (Contrato 11)
- [ ] **Preferências**: A ferramenta implementa `load_prefs()` e `save_prefs()` para persistir dados do usuário? (Obrigatório)
- [ ] 🛑 **Logs Obrigatórios**: A ferramenta deve registrar logs em pontos críticos (inicialização, início/fim de processos, capturas de erro). Ferramentas sem log não serão aceitas no core.
- [ ] **Documentação**: se criei um widget novo, atualizei `docs/skills/widgets_skill.md`? (Contrato 12)

---

## ⚡ Ferramentas INSTANT (Ação Imediata)

Ferramentas do tipo `INSTANT` não abrem abas no workspace. Elas executam uma ação imediata (abrir diálogo, processar algo, etc.) e se auto-destroem.

### Quando usar

- Operações que não precisam de UI persistente (ex: criar projeto, exportar, salvar snapshot).
- Ações que abrem diálogos modais e depois encerram.

### Como criar

1. **CategoryTool**: já existe `CategoryTool.INSTANT = "instant"`.
2. **Widget**: herde de `BasePlugin`, use `QTimer.singleShot(0, self._run)` para executar a ação após o `__init__`.
3. **Auto-destruição**: chame `self.deleteLater()` ao final.

```python
from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QVBoxLayout, QLabel

class MinhaInstantTool(BasePlugin):
    def __init__(self, parent=None):
        super().__init__(tool_key="MinhaInstant", parent=parent)
        # Placeholder invisível
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        placeholder = QLabel("")
        placeholder.setVisible(False)
        layout.addWidget(placeholder)
        # Executa no próximo ciclo do event loop
        QTimer.singleShot(0, self._run)

    def _run(self) -> None:
        try:
            # ... ação principal ...
            pass
        except Exception as e:
            self.logger.error("Erro", code="INSTANT_ERR", error=str(e))
        finally:
            self.deleteLater()

    def load_prefs(self): pass
    def save_prefs(self): pass
```

### Registro no ToolRegistry

```python
ToolKey.MINHA_INSTANT.value: Tool(
    name=ToolKey.MINHA_INSTANT.value,
    title="Minha Ação Instantânea",
    widget_factory=_make_factory(
        "plugins.minha_instant.MinhaInstantPlugin",
        "MinhaInstantPlugin",
    ),
    tooltip="Descrição curta",
    tool_type=ToolType.FOLDER,
    category=CategoryTool.INSTANT,
    show_in_toolbar=True,
),
```

### Comportamento no WorkspaceManager

- Ferramentas `INSTANT` **não** são registradas em `CentralWorkspace` nem `SideWorkspace`.
- Quando o usuário clica no botão da toolbar, o `WorkspaceManager.open_tool()` acessa `tool.widget` (lazy loading), o que instancia o plugin, executa a ação e o widget se auto-destrói.
- Nenhuma aba é criada. Nenhum estado é mantido.

### Requisitos

- [ ] **QTimer.singleShot**: use para adiar a execução para depois do `__init__`.
- [ ] **self.deleteLater()**: chame no `finally` para garantir limpeza.
- [ ] **Logger**: registre início, fim e erros.
- [ ] **MessageBox**: use para feedback ao usuário.
