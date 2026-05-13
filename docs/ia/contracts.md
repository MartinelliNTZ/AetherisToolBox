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