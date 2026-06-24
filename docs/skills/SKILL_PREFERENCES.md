# Skill: Gerenciamento de Preferências (Preferences)

O sistema de preferências permite que cada ferramenta salve e recupere seu estado (configurações, últimos valores inseridos, filtros, etc.) de forma persistente em um arquivo JSON (`config/preferences.json`).

## 🛠️ Regra Geral

O uso do sistema de preferências é **obrigatório** para todas as ferramentas do Aetheris ToolBox.

- O `BasePlugin` inicializa automaticamente a variável `self.preferences`.
- Você **não** deve declarar ou instanciar `Preferences` no construtor da sua ferramenta.
- Você **deve** obrigatoriamente sobrescrever os métodos `load_prefs()` e `save_prefs()`.

## 📂 Como implementar

### 1. Carregamento (`load_prefs`)
Deve ser chamado no `__init__` da sua ferramenta, **após** a construção da interface (`_build_ui`), para que os valores recuperados possam ser aplicados aos widgets.

```python
def load_prefs(self) -> None:
    # O self.preferences já está disponível via BasePlugin
    # Recupera valores salvos. Se não existir, usa o default fornecido.
    texto = self.preferences.get("ultimo_comando", "")
    self._edit_comando.setText(texto)
    
    self.logger.debug("Preferências carregadas")
```

### 2. Persistência (`save_prefs`)
Deve ser chamado sempre que houver uma alteração importante (ex: clique em "Executar", alteração de parâmetros críticos ou fechamento da ferramenta).

```python
def save_prefs(self) -> None:
    # Define os valores no cache de memória
    self.preferences.set("ultimo_comando", self._edit_comando.text())
    self.preferences.set("execucoes_total", 42)
    
    # IMPORTANTE: Você deve chamar o save() para persistir no arquivo físico
    self.preferences.save()
    self.logger.info("Preferências salvas com sucesso")
```

## 🚀 Exemplo de Uso (Padrão TecladorF)

```python
class MinhaTool(BasePlugin):
    def __init__(self, parent=None):
        super().__init__(tool_key="MinhaTool", parent=parent)
        self._build_ui()
        self.load_prefs() # Obrigatório no init

    def _on_executar(self):
        self.save_prefs() # Salva antes de rodar a lógica
        self._processar()
```

## ✅ O que persistir?

Para melhorar a experiência do usuário (UX), sempre salve:
- Caminhos de arquivos e pastas selecionados recentemente.
- Valores numéricos em SpinBoxes.
- Textos em LineEdits que não sejam senhas.
- Estados de CheckBoxes e RadioButtons.
- Filtros de visualização ativos.

---