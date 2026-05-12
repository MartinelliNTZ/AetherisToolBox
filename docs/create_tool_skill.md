# Skill: Criação de Novas Ferramentas (Plugins)

Este guia descreve o processo padrão para criar e registrar uma nova ferramenta no **Aetheris ToolBox**, garantindo a integração com o sistema de logs, gerenciamento de sinais e carregamento dinâmico (Lazy Loading).

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

**Arquivo:** `plugins/minha_ferramenta/main_widget.py`
```python
from core.model.BasePlugin import BasePlugin
from PySide6.QtWidgets import QVBoxLayout, QLabel

class MinhaFerramentaWidget(BasePlugin):
    def __init__(self, parent=None):
        # O tool_key deve ser a string definida no ToolKey
        super().__init__(tool_key="MinhaFerramenta", parent=parent)
        self._setup_ui()
        self.logger.info("Ferramenta inicializada com sucesso!")

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Olá do Novo Plugin!"))

    def load_prefs(self):
        # Opcional: Carregar configurações salvas
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

1.  **Ícone**: Adicione um arquivo `.ico` com o mesmo nome da ferramenta em `resources/icons/MinhaFerramenta.ico`. O `IconManager` o encontrará automaticamente.
2.  **Menu**: O `MenuManager` lerá o `ToolType` definido no registro e adicionará o botão da ferramenta ao grupo correspondente na barra superior.

---

## ✅ Checklist de Verificação
- [ ] A chave em `ToolKey` é idêntica ao `tool_key` passado no `super().__init__`.
- [ ] O caminho do módulo no `_make_factory` usa pontos (ex: `plugins.pasta.arquivo`).
- [ ] A categoria `CategoryTool` está correta (ferramentas de análise costumam ser `CENTRAL`).
- [ ] Se a ferramenta for `BOTH`, ela será registrada no `SideWorkspace` mas poderá ser movida.
- [ ] **Preferências**: A ferramenta implementa `load_prefs()` e `save_prefs()` para persistir dados do usuário? (Obrigatório)
- [ ] 🛑 **Logs Obrigatórios**: A ferramenta deve registrar logs em pontos críticos (inicialização, início/fim de processos, capturas de erro). Ferramentas sem log não serão aceitas no core.