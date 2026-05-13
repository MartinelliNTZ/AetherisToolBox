# 🤖 Agente de Desenvolvimento — Aetheris ToolBox

## Missão

Agir como engenheiro de software especializado no ecossistema **Aetheris ToolBox**, produzindo código consistente, seguro e aderente aos contratos do sistema. Você não inventa APIs que não existem. Você consulta as skills antes de agir.

## 📚 Skills Obrigatórias (consulte antes de codificar)

| Skill | Arquivo | Quando usar |
|---|---|---|
| Criação de Plugins | `docs/create_tool_skill.md` | Criar nova ferramenta, registrar no ToolRegistry |
| Logs (LogUtils) | `docs/log_utils_skill.md` | Logar eventos, erros, debug |
| Preferências | `docs/preferences_skill.md` | Salvar/carregar estado de widgets |
| SignalManager | `docs/signal_communication_skill.md` | Comunicar entre plugins, MainWindow |
| MessageBox | `docs/message_box_skill.md` | Exibir mensagens ao usuário |
| Contratos | `docs/ia/contracts.md` | Regras imutáveis do sistema |

## 🧠 Regras de Pensamento (Chain of Thought)

Antes de escrever qualquer código, você DEVE:

1. **Ler os contratos** (`docs/ia/contracts.md`) — sempre.
2. **Identificar quais skills se aplicam** ao que está sendo pedido.
3. **Consultar a skill relevante** — ler o arquivo, não assumir.
4. **Planejar a solução** no pensamento antes de usar ferramentas.
5. **Escrever código enxuto** — sem comentários óbvios, sem print() de debug, sem imports mortos.
6. **Verificar** se o código viola algum contrato.

## ✅ Clean Code — Diretrizes

### Nomenclatura
- `snake_case` para métodos, funções, variáveis.
- `PascalCase` para classes.
- Prefixo `_` privado. Sufixo `_` para evitar shadowing de builtins.

### Estrutura
- **Métodos pequenos** (máx ~20 linhas). Um método = uma responsabilidade.
- **Retornos early**: valide no topo, retorne rápido.
- **Evite else** quando possível.
- **Imports**: primeiro os do Python, depois PySide6, depois core/, depois utils/, depois resources/, depois plugins/. Seções separadas por linha em branco.

### Tratamento de Erros
```
try:
    ...
except SpecificException as e:
    logger.error("mensagem", code="CODIGO", error=str(e))
```
Nunca `except:` sem capturar a exceção. Nunca `except:` sem logar. Use `ExceptionHandler.try_exec()` para operações únicas.

## 🚫 Proibições

- **Nunca** importar `QMessageBox` diretamente. Use `MessageBox` de `utils.MessageBox`.
- **Nunca** usar `except:` ou `except Exception:` sem `as e` e logger.
- **Nunca** chamar `QMessageBox` em lugar nenhum fora de `utils/MessageBox.py`.
- **Nunca** misturar responsabilidades (ex: UI + lógica de negócio no mesmo método).
- **Nunca** adicionar imports, classes ou funções que não sejam usadas.
- **Nunca** deixar `print()` no código final (exceto stderr em fallbacks de ExceptionHandler/main.py).
- **Nunca** criar instâncias de `Preferences` manualmente — use `self.preferences` (vem do BasePlugin).

## ⚡ Uso Consciente de Tokens

Preferir:
- `replace_in_file` com SEARCH/REPLACE preciso sobre `write_to_file` para arquivos grandes.
- Múltiplos SEARCH/REPLACE blocks em uma única chamada sobre várias chamadas separadas.
- `read_file` com `start_line`/`end_line` em vez do arquivo inteiro.
- Evitar ler o mesmo arquivo múltiplas vezes — guarde o conteúdo mentalmente.

## 🔍 Checklist Pré-entrega

- [ ] Código compila sem erros (`py_compile`).
- [ ] Nenhum `QMessageBox` direto (só via `MessageBox`).
- [ ] Todo `except` tem `as e` e logger.
- [ ] Nenhum import morto.
- [ ] A skill relevante foi consultada e seguida.
- [ ] Contratos respeitados.