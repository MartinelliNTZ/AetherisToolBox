# 📐 Análise Arquitetural: GridComplexSelector + ComplexSelector

> **Data:** 07/06/2026  
> **Contexto:** Revisão de widgets reutilizáveis do Aetheris ToolBox  
> **Arquivos analisados:**  
> - `resources/widgets/complex/GridComplexSelector.py` (527 linhas)  
> - `resources/widgets/complex/ComplexSelector.py` (631 linhas)  
> - `plugins/las_vector_converter/LasVectorConverterPlugin.py` (543 linhas)  
> - `docs/skills/SKILL_PLUGIN_CONTRACT.md` (contratos do sistema)

---

## 📋 Sumário Executivo

| Gravidade | Tipo | Descrição |
|-----------|------|-----------|
| 🔴 **CRÍTICA** | Bug | Dynamic parent + callback chaining completamente quebrado |
| 🔴 **GRAVE** | Contrato | `ct` importado diretamente (viola Contrato 19) |
| 🟡 **MÉDIA** | Design | Dupla-registro de callbacks no mesmo `parent_key` |
| 🟡 **MÉDIA** | Código Morto | `Qt` importado e não utilizado (viola Contrato 9) |
| 🟢 **LEVE** | Code Style | `QTimer` importado duas vezes (módulo + local) |
| 🟢 **LEVE** | Design | Chaining frágil baseado em atributo de função |

---

## 🔴 1. BUG CRÍTICO: Dynamic Parent + Callback Chaining Quebrado

### 1.1 O Problema

GridComplexSelector usa um mecanismo de **chaining de callbacks** para que mudanças no seletor pai ("Entrada") propaguem para o filho ("Saída"). O mecanismo funciona assim:

1. **GridComplexSelector.**`_build_selector_row` configura listeners no **parent** (`parent_selector.on_path_change`)
2. **GridComplexSelector** salva o callback original em `self._user_callbacks[parent_key]`
3. **GridComplexSelector** substitui `on_path_change` por um wrapper que:  
   (a) chama o callback original salvo → (b) aplica lógica de linking

4. ❌ **O plugin sobrescreve `on_path_change` por completo**, quebrando a corrente:

```python
# LasVectorConverterPlugin.py:109 — APÓS o GridComplexSelector ser construído
self._grid_io["Entrada"].on_path_change = self._on_input_path_changed
# ↑ Isso mata os wrappers que o GridComplexSelector instalou!
```

### 1.2 Fluxo do Bug (Passo a Passo)

```
GridComplexSelector.__init__()
  └─ _build(specs)
      └─ _build_selector_row("Saída", {...dynamic_parent, parent:"Entrada"...})
          ├─ 1. Cria ComplexSelector("Saída")
          ├─ 2. _connect_dynamic_listener("Saída", "Entrada")
          │     ├─ Salva on_path_change da Entrada → None (ainda não configurado)
          │     └─ Entrada.on_path_change = dynamic_handler ✅
          ├─ 3. _connect_parent_listener("Saída", "Entrada")   ← MESMO parent!
          │     ├─ Salva on_path_change da Entrada → dynamic_handler (do passo 2)
          │     └─ Entrada.on_path_change = on_parent_changed
          │        └─ on_parent_changed → chama _user_cb (dynamic_handler) → aplica linking
          └─ 4. Retorna selector + btn_container

LasVectorConverterPlugin._build_ui()
  └─ 5. self._grid_io["Entrada"].on_path_change = self._on_input_path_changed
       └─ ❌ SUBSTITUI on_parent_changed (que continha a chain completa!)
       └─ Agora, quando a Entrada muda:
          - Apenas _on_input_path_changed é chamado
          - dynamic_handler NUNCA executa
          - O modo do filho NUNCA é adaptado
          - O output NUNCA é gerado automaticamente
```

### 1.3 Consequências

- ❌ `dynamic_parent` não funciona para plugins que configuram `on_path_change` na entrada
- ❌ Output nunca é gerado automaticamente quando o usuário muda a entrada
- ❌ Modo do output nunca é adaptado (file ↔ folder) conforme o tipo da entrada
- ❌ O botão "USAR ORIGEM" pode falhar se o output estiver vazio

### 1.4 Por que é Grotesca

O código do GridComplexSelector tem documentação e comentários explicitamente dizendo _"NÃO sobrescreve callback do usuário"_ (linha `_connect_parent_listener`), mas o design inteiro é vulnerável a isso — e o plugin mais importante (LasVectorConverter) faz exatamente isso.

É uma **race condition estrutural**: o GridComplexSelector não tem como garantir que plugin não vai sobrescrever o chaining depois.

### 1.5 Correção Proposta

```python
# Na GridComplexSelector._build_selector_row:
# Em vez de substituir on_path_change ao final, registre um callback
# público que o plugin DEVE usar:

class GridComplexSelector(QWidget):
    def set_on_parent_changed(self, child_label: str, callback: Callable):
        """
        Registra callback para quando o path do parent mudar.
        Não quebra o chaining interno — o callback é adicionado
        à corrente após a lógica de linking.
        """
        meta = self._link_meta.get(child_label)
        if not meta:
            return
        parent_key = meta["parent"]
        parent_selector = self._selectors.get(parent_key)
        if not parent_selector:
            return
        self._user_callbacks[parent_key] = callback

    # OU melhor: usar Signals do PySide6 em vez de atributos de função
```

**Alternativa radical:** Converter `on_path_change` de atributo para `Signal()`:

```python
class ComplexSelector(QWidget):
    path_changed = Signal(list)  # Signal PySide6 verdadeiro

    def _emit_path_change(self):
        self.path_changed.emit(self._selected_list)  # Dispara Signal
```

Isso eliminaria o problema de overwrite porque Signals podem ter múltiplos slots conectados.

---

## 🔴 2. VIOLAÇÃO DE CONTRATO: `ct` importado diretamente

### 2.1 O Problema

Em `GridComplexSelector.show_error()` (linha ~330):

```python
from resources.styles.ThemeManager import ct  # ← VIOLA CONTRATO 19
```

### 2.2 Contrato Violado

**Contrato 19 — Importação de Estilos:**

```
Fora de resources/styles/, importe APENAS AppStyles.
Nunca importe BaseTheme, ThemeManager, temas concretos ou ct diretamente.
```

### 2.3 Consequência

Isso quebra o encapsulamento de temas. Se o ThemeManager mudar, todos os lugares que importam `ct` diretamente precisam ser atualizados.

### 2.4 Correção

Usar `AppStyles.theme_colors()` ou `AppStyles.vertical_tab_colors()`:

```python
# ❌ Atual (viola contrato)
from resources.styles.ThemeManager import ct
error_color = ct.theme.COLOR_DANGER

# ✅ Correto
from resources.styles.AppStyles import AppStyles
colors = AppStyles.theme_colors()
error_color = colors.get("COLOR_DANGER", "#FF4444")
```

Ou adicionar um método explícito em `AppStyles`:

```python
@staticmethod
def error_style() -> str:
    """Retorna stylesheet de borda vermelha para erro."""
    ct = ...  # import interno, só aqui
    return f"border: 2px solid {ct.theme.COLOR_DANGER}; ..."
```

---

## 🟡 3. DUPLO-REGISTRO DE CALLBACKS NO MESMO PARENT

### 3.1 O Problema

Em `_build_selector_row`, para um child que tem **ambos** `dynamic_parent=True` e `mode_type="output"`, **dois** métodos diferentes registram callbacks no mesmo parent:

```python
# GridComplexSelector._build_selector_row() — ordem de execução:

# 1. Se dynamic_parent e parent_key:
if dynamic_parent and parent_key:
    self._connect_dynamic_listener(label, parent_key)
    # ↑ Sobrescreve on_path_change do parent com dynamic_handler

# 2. Se mode_type == "output" e parent_key:
if mode_type == "output" and parent_key:
    self._connect_parent_listener(label, parent_key)
    # ↑ Sobrescreve on_path_change do parent com on_parent_changed
```

Ambos métodos:
- Usam a **mesma chave** `_user_callbacks[parent_key]` (sobrescrevendo um ao outro)
- Substituem `parent_selector.on_path_change`

O segundo (`_connect_parent_listener`) acaba salvando o `dynamic_handler` do primeiro como o callback original, o que é frágil e depende de ordem de execução.

### 3.2 Risco

Se a ordem de execução mudar (refatoração), a corrente inteira quebra. Além disso, `_connect_parent_listener` e `_connect_dynamic_listener` têm lógicas parcialmente duplicadas (`_generate_output`).

### 3.3 Correção

Unificar em um único método:

```python
def _connect_output_listener(self, child_label: str, parent_key: str):
    """Único listener para output com parent e opcional dynamic_parent."""
    meta = self._link_meta.get(child_label, {})
    parent_selector = self._selectors.get(parent_key)
    if not parent_selector:
        return

    # Salva callback original do usuário
    if parent_key not in self._user_callbacks:
        self._user_callbacks[parent_key] = parent_selector.on_path_change

    def unified_handler(paths: list[str]):
        # 1. Callback original do usuário
        user_cb = self._user_callbacks.get(parent_key)
        if user_cb:
            user_cb(paths)

        # 2. Se dynamic_parent, aplica modo
        if meta.get("dynamic_parent"):
            self._apply_dynamic_mode(child_label)

        # 3. Gera output se necessário
        selector = self._selectors.get(child_label)
        if selector and (self._self_generated.get(child_label, False) or not selector.get_paths()):
            self._generate_output(child_label, paths)

    parent_selector.on_path_change = unified_handler
```

---

## 🟡 4. CÓDIGO MORTO: `Qt` importado e não utilizado

### 4.1 O Problema

Em `ComplexSelector.py`, linha 32:

```python
from PySide6.QtCore import Qt  # ← NUNCA usado no arquivo inteiro
```

### 4.2 Contrato Violado

**Contrato 9 — Código Morto:**

```
Nenhum import, classe, função ou variável não utilizado.
```

### 4.3 Correção

Remover a linha.

---

## 🟢 5. `QTimer` importado duas vezes

### 5.1 O Problema

Em `GridComplexSelector.py`:

```python
# Linha 17: import no topo do módulo
from PySide6.QtCore import QTimer

# Linha 361: import LOCAL dentro de show_error()
from PySide6.QtCore import QTimer
```

O import local sobrescreve o import global, mas o que está no topo do módulo nunca é usado.

### 5.2 Correção

Remover o import local e usar o global:

```python
def show_error(self, label: str, message: str, duration_ms: int = 3000):
    ...
    if duration_ms > 0:
        QTimer.singleShot(duration_ms, lambda: self._clear_error(edit))
    # ↑ QTimer já importado no topo
```

---

---
---

## 📊 COMPARATIVO: Atributo vs Signal

| Aspecto | Atributo (`on_path_change = func`) | Signal (`path_changed = Signal(list)`) |
|---------|-----------------------------------|----------------------------------------|
| Múltiplos listeners | ❌ Apenas 1 | ✅ Ilimitados |
| Sobrescrita segura | ❌ Fácil de quebrar | ✅ Conecta sem conflito |
| Desconexão | `= None` | `.disconnect()` |
| Chain automático | Manual (wrapper) | Automático |
| Type safety | ❌ None | ✅ Signal tipado |
| Debugging | Difícil (qual função está setada?) | Fácil (slots listados) |
| Manutenção | Frágil | Robusto |

---

## 🛠️ CHECKLIST DE CORREÇÕES

- [ ] **CRÍTICO**: Substituir `on_path_change` por `Signal` no ComplexSelector
- [ ] **CRÍTICO**: Atualizar GridComplexSelector para usar `path_changed.connect()` em vez de chaining manual
- [ ] **GRAVE**: Substituir `from resources.styles.ThemeManager import ct` por `AppStyles`
- [ ] **MÉDIO**: Unificar `_connect_dynamic_listener` + `_connect_parent_listener` em método único
- [ ] **MÉDIO**: Remover `from PySide6.QtCore import Qt` não utilizado
- [ ] **LEVE**: Remover import local duplicado de `QTimer`
- [ ] **LEVE**: Setar `_self_generated[label] = True` também no `_generate_output`
- [ ] **LEVE**: Adicionar confirmação em `_on_use_origin` se output já preenchido
- [ ] **DOC**: Atualizar `docs/skills/SKILL_WIDGETS.md` com padrão Signal

---

## 🔗 IMPACTO NOS PLUGINS EXISTENTES

Os seguintes plugins usam `on_path_change` e seriam afetados pela migração para Signal:

| Plugin | Arquivo | Uso |
|--------|---------|-----|
| LasVectorConverter | `LasVectorConverterPlugin.py:109` | `on_path_change = self._on_input_path_changed` |

A migração seria simples: `selector.path_changed.connect(self._on_input_path_changed)`.

---

## 📌 CONCLUSÃO

O design atual de callback chaining via **atributos de função substituíveis** (`on_path_change`) é estruturalmente frágil e já causou um bug crítico que **quebra completamente** o `dynamic_parent` no LasVectorConverter.

A raiz do problema não é um erro de implementação, mas sim uma **escolha arquitetural** que conflita com o padrão de uso real (plugins configurando callbacks). A correção definitiva é migrar para **PySide6 Signals**, que é o mecanismo nativo do Qt para este exato propósito.

Além disso, a violação do **Contrato 19** (import direto de `ct`) mostra que mesmo widgets reutilizáveis precisam seguir as regras de estilo estabelecidas.