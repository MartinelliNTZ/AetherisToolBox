# Skill: Comunicação e Mensageria (MessageBox · SignalManager · Console · Progress · HUD · LogUtils)

Esta skill descreve as formas oficiais de comunicação no Aetheris ToolBox, quando usá-las e como elas se diferenciam:

- **MessageBox**: diálogo para interação direta com o usuário (erros, confirmações, inputs simples).
- **SignalManager**: canal exclusivo para comunicação entre *ferramentas* (plugins/core).
- **ConsolePlugin**: interface orientada ao usuário para mensagens, progresso e alertas.
- **ProgressBar (ui_main)**: barra de progresso central usada por todas as ferramentas.
- **HUDLoader**: indicador para operações longas; uso opcional quando apropriado.
- **LogUtils**: logging estruturado e diagnóstico para desenvolvedores.

## MessageBox — Interação com o usuário

Use sempre `utils.MessageBox` para qualquer diálogo com o usuário. Exemplos de uso:

- Erro/alerta: `MessageBox.show_error("Falha ao abrir arquivo", detail=traceback_text)`
- Confirmação: `if MessageBox.show_question("Deseja continuar?") == MessageBox.YES: ...`
- Informação: `MessageBox.show_info("Processo concluído")`

Recomendações:
- Forneça `detail` ao exibir exceções (traceback) para permitir suporte/diagnóstico.
- Antes de mostrar um diálogo de erro, faça log via `self.logger.error(..., error=str(e))`.
- Nunca importe `QMessageBox` diretamente.

## SignalManager — Comunicação entre ferramentas

O `SignalManager` é o canal oficial para mensagens entre plugins e entre plugins ↔ core. Devido à sua abrangência, **não** use `SignalManager` para comunicação entre widgets internos do mesmo plugin — use sinais/slots locais.

Sinais comuns:
- `console_message(str)` — mensagem orientada ao usuário (ConsolePlugin).
- `progress_update(float)` — progresso global (0.0–100.0) para a ProgressBar da `MainWindow`.
- `hud_show(dict)` / `hud_update(dict)` / `hud_hide()` — para uso do HUDLoader (opcional).
- `tool_opened(str)` — notificação de abertura de ferramenta.

Emitir sinais (ex.):

```python
from core.manager.SignalManager import SignalManager

signals = SignalManager.instance()
signals.console_message.emit("Iniciando processamento...")
signals.progress_update.emit(12.5)
```

Receber sinais (ex.):

```python
SignalManager.instance().console_message.connect(self._on_console_message)
```

Regras rápidas:
- Use `SignalManager` para comunicação *inter-plugin* e para atualizar componentes centrais (Console, ProgressBar, HUD).
- Para lógica/fluxo interno ao plugin, prefira sinais locais ou chamadas diretas entre objetos.

## ConsolePlugin — Mensagens e alertas ao usuário

O `ConsolePlugin` é a face voltada ao usuário para mensagens de status, alertas e passos de processo. Mensagens aqui devem ser legíveis e focadas na experiência do usuário; evite dumps técnicos extensos — esses vão para o `LogUtils`.

Fluxo recomendado:
- Plugin emite `SignalManager.instance().console_message.emit("texto")` quando quiser notificar o usuário.
- Mensagens de progresso devem ser acompanhadas por `progress_update` quando aplicável.

## ProgressBar (ui_main) — barra de progresso central

A `MainWindow` expõe uma única ProgressBar para sinalizar progresso global. **Regra obrigatória:**

Nenhuma ferramenta deve criar sua própria `QProgressBar` ou similar internamente — use `SignalManager.instance().progress_update.emit(valor)` para atualizar a barra central.

Use 0.0–100.0 como intervalo. A responsabilidade de transformar um avanço em percentuais (quando aplicável) fica a cargo da ferramenta que emite os sinais.

## HUDLoader — Indicador para operações longas

O `HUDLoader` é um indicador visual para operações demoradas e pode exibir status mais detalhado que a ProgressBar. Diferente da ProgressBar, seu uso é opcional e contextual — porém recomenda-se:

- Usar `SignalManager` (sinais `hud_show`, `hud_update`, `hud_hide`) para controlar o HUD a partir de workers.
- Preferir HUD para operações que bloqueiam/ocupam muito tempo ou exigem indicação destacada ao usuário.

Não existe uma proibição estrita similar à ProgressBar, mas prefira reutilizar `HUDLoader` central quando disponível em vez de criar implementações locais.

## LogUtils — Logs estruturados para desenvolvedores

`LogUtils` é a fonte primária de diagnóstico e deve ser usado para:

- Registrar exceções e contexto (`logger.error("msg", code="COD", error=str(e))`).
- Registrar variáveis, estados e entradas/saídas críticas.

Princípios:
- **Console ≠ Log**: Console mostra mensagens para o usuário; `LogUtils` registra dados estruturados para investigação.
- Evite `except:` sem `as e` e log — sempre capture a exceção e use `logger.error` com o `error=str(e)`.
- Não logar tudo: prefira logs significativos que ajudem em reproduzir/fixar bugs.

Exemplo mínimo:

```python
try:
    resultado = self._processar(dados)
except Exception as e:
    self.logger.error("Falha no processamento", code="PROC_ERR", error=str(e))
    SignalManager.instance().console_message.emit("Erro ao processar arquivo")
    MessageBox.show_error("Erro durante o processamento", detail=traceback.format_exc())
```

## Uso de `print()`

`print()` não é proibido, mas deve ser evitado. Permissões:

- Permitido apenas para testes locais rápidos (por exemplo, testar saídas do `LogUtils`) e scripts temporários.
- Nunca deixe `print()` em código final ou em commits destinados à base principal.

## Regras Resumidas (Golden Rules)

- **MessageBox**: sempre `utils.MessageBox` para diálogo com usuário.
- **SignalManager**: exclusivo para comunicação entre ferramentas e atualização de componentes centrais.
- **ConsolePlugin**: mensagens legíveis para o usuário; use `console_message`.
- **ProgressBar (ui_main)**: única barra oficial; atualize com `progress_update` — nunca crie barras locais.
- **HUDLoader**: use para operações longas; controle via sinais HUD quando disponível.
- **LogUtils**: registro estruturado e diagnóstico; erros sempre com `as e` e `logger.error(..., error=str(e))`.
- **print()**: só para testes locais; remova antes de commitar.

---

Se precisar, posso também criar exemplos práticos em um plugin de exemplo mostrando o fluxo completo (worker → signals → progress → console → log). 