# Skill: Comunicação via SignalManager

O **SignalManager** é um Singleton que centraliza a comunicação entre diferentes partes do sistema (MainWindow, Workspaces e Plugins). Ele permite que uma ferramenta envie informações para outra (como mensagens de log para o Console) sem que elas precisem conhecer a existência uma da outra.

## 📡 Sinais Comuns do Sistema

| Sinal | Descrição | Uso Típico |
| :--- | :--- | :--- |
| `console_message` | Envia uma string para o plugin de Console. | Notificar o usuário sobre o status de um processo. |
| `progress_update` | Atualiza a barra de progresso global na MainWindow. | Indicar a evolução de tarefas longas. |
| `tool_opened` | Emitido quando um `BasePlugin` é instanciado. | O core usa para registrar a ferramenta na UI. |
| `tool_request_move` | Solicita a movimentação de uma ferramenta entre abas e lateral. | Alternar visualização de ferramentas `BOTH`. |

## 📤 Como Emitir Sinais (de um Plugin)

Para enviar uma mensagem para o Console ou atualizar o progresso, utilize a instância global do `SignalManager`. Não é necessário importar a ferramenta de destino.

```python
from core.manager.SignalManager import SignalManager

def minha_funcao_longa(self):
    signals = SignalManager.instance()
    
    # Enviando mensagem para o Console
    signals.console_message.emit("Iniciando processamento de dados...")
    
    # Atualizando a barra de progresso (0 a 100)
    signals.progress_update.emit(50) 
```

## 📥 Como Escutar Sinais (Inscrição)

Geralmente, o "Core" do sistema já escuta os sinais principais. Se você estiver criando uma ferramenta que precisa reagir a eventos globais (como um LogViewer customizado), conecte o sinal no `__init__`.

```python
from core.manager.SignalManager import SignalManager

class MeuReceptor(BasePlugin):
    def __init__(self, parent=None):
        super().__init__(tool_key="Receptor", parent=parent)
        
        # Conectando ao sinal de mensagens
        SignalManager.instance().console_message.connect(self._ao_receber_mensagem)

    def _ao_receber_mensagem(self, msg: str):
        print(f"Eu ouvi: {msg}")
```

## ⚠️ Regras de Ouro

1. **Desconexão Automática**: O `SignalManager` é um Singleton de vida longa. Se você conectar um sinal a um método de um widget, certifique-se de que a destruição do widget não cause erros de referência (o Qt costuma gerenciar isso, mas em threads é crítico).
2. **Não abuse**: Use sinais para comunicação *inter-plugins*. Para comunicação *interna* da sua ferramenta (botão clicado -> função), use sinais e slots locais do próprio widget.
3. **Thread Safety**: Sinais do PySide6/Qt são seguros para threads. Você pode emitir um sinal de dentro de um `QThread` (Worker) e a UI será atualizada corretamente no loop principal.

---

## 🚀 Exemplo Real (TecladorF)

No `TecladorF.py`, o worker utiliza o sinal para avisar o usuário que a automação está pronta:
```python
SignalManager.instance().console_message.emit(
    f"TecladorF pronto — tecla {self._hotkey.upper()}"
)
```