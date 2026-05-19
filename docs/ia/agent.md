# 🤖 Agente de Desenvolvimento — Aetheris ToolBox

## Missão

Agir como engenheiro de software especializado no ecossistema **Aetheris ToolBox**, produzindo código consistente, seguro e aderente aos contratos do sistema. Você não inventa APIs que não existem. Você consulta as skills antes de agir.

## 📚 Skills Obrigatórias (consulte antes de codificar)

| Skill | Arquivo | Quando usar |
|---|---|---|
| Criação de Plugins | `docs/skills/create_tool_skill.md` | Criar nova ferramenta, registrar no ToolRegistry |
| Logs (LogUtils) | `docs/skills/log_utils_skill.md` | Logar eventos, erros, debug |
| Preferências | `docs/skills/preferences_skill.md` | Salvar/carregar estado de widgets |
| SignalManager | `docs/skills/signal_communication_skill.md` | Comunicar entre plugins, MainWindow |
| MessageBox | `docs/skills/message_box_skill.md` | Exibir mensagens ao usuário |
| MenuBar | `docs/skills/menubar_skill.md` | Criar/modificar sistema de menus (MenuItem, MenuBar, MenuManager) |
| Widgets | `docs/skills/widgets_skill.md` | Verificar/ criar widgets reutilizáveis |
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
- `PascalCase` para nomes de arquivos de configuração/manager (ex: `MenuManager.py`, `WorkspaceManager.py`, `ToolRegistry.py`).
- `PascalCase` para arquivos de widget em `resources/widgets/` (ex: `SimpleSelector.py`, `PreferenceItemGrid.py`).

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
- **Nunca** importar widgets brutos do `PySide6.QtWidgets` sem antes verificar em `resources/widgets/` se já existe um widget pronto (Contrato 11).
- **Nunca** montar componentes compostos manualmente (label + campo + botão) se já existe um widget em `resources/widgets/` que faz isso.
- **Nunca** misturar responsabilidades (ex: UI + lógica de negócio no mesmo método).
- **Nunca** adicionar imports, classes ou funções que não sejam usadas.
- **Nunca** deixar `print()` no código final (exceto stderr em fallbacks de ExceptionHandler/main.py).
- **Nunca** criar instâncias de `Preferences` manualmente — use `self.preferences` (vem do BasePlugin).
- **Nunca** modificar funcionalidade sem atualizar a documentação correspondente (Contrato 12).
- **Nunca** a MainWindow deve importar ou manipular `MenuBar`, `CentralWorkspace` ou `SideWorkspace` diretamente (Contratos 14 e 16).
- **Nunca** configurar propriedades de `Tool` fora do `ToolRegistry` (Contrato 13).
- **Nunca** importar ou chamar `QFileDialog` fora de `utils/ExplorerUtils.py` (Contrato 17).

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
- [ ] Widgets de `resources/widgets/` foram consultados antes de criar UI nova (Contrato 11).
- [ ] A skill relevante foi consultada e seguida.
- [ ] Contratos respeitados.
- [ ] Documentação atualizada se houver mudança funcional (Contrato 12).