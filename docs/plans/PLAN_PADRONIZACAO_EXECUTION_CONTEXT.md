# Plano de Ação: Padronização do ExecutionContext e Fluxo de Pipeline

## 1. Problemas Identificados

### 1.1 Acesso a Dados — Dict vs Atributos
Atualmente o `ExecutionContext` usa acesso estilo dicionário:
```python
context.get("file_path", "")
context.get("target_bands", {})
context.set("split_result", result)
```

**Problema:** Sem autocomplete, sem tipagem, sem documentação visível. O desenvolvedor precisa saber as strings mágicas de cor.

**Solução:** Atributos tipados com `@property`:
```python
context.input_path       # em vez de context.get("input_path")
context.target_bands     # em vez de context.get("target_bands", {})
context.files            # em vez de context.get("files", None)
```

### 1.2 Chaves Soltas sem Padronização
Cada step usa chaves diferentes:
- `LasTilerStep`: `file_path`, `output_dir`, `split_result`
- `IdwInterpolatorStep`: `input_dir`, `output_path`, `target_bands`
- `LasCheckStep`: `file_path`, `check_results`
- `LasBlackFilterStep`: `file_path`, `output_limpo`, `output_pretos`

**Problema:** Sem padrão, steps não podem ser encadeados genericamente.

**Solução:** Chaves canônicas:
| Chave | Tipo | Descrição |
|-------|------|-----------|
| `input_path` | `str` | Diretório de entrada (pasta com arquivos) |
| `output_path` | `str` | Diretório base de saída |
| `files` | `list[str] \| None` | Lista de arquivos a processar (None = todos no input_path) |
| `step_name` | `str` | Nome do step atual (para criar subpasta) |

### 1.3 Steps Não Atualizam input_path para o Próximo Step
Atualmente cada step recebe parâmetros fixos e não propaga seu output como input do próximo.

**Problema:** Pipeline não pode ser encadeada dinamicamente.

**Solução:** Convenção de fluxo:
```
input_path = /dados/raiz
output_path = /dados/raiz

Step 1 (LasCheck):
  → Lê: input_path
  → Salva relatório em: output_path/lascheck/
  → NÃO atualiza input_path (check não modifica dados)ao passar os steps para asyncpapeline podemos incluir alguns paramentros

  AsyncPipelineEngine[LasCheckStep(modified_path = false), LasBlackFilterStep, LasTilerStep, IdwInterpolatorStep, MergeRastersStep, RasterCheckStep]  algo assim entende 
eu passei essa ordem mas eu poderia inverter a ordem dos steps e o pipeline ainda funcionaria, pois cada step sabe de onde ler e para onde salvar, e o contexto é atualizado automaticamente.
Step 2 (LasBlackFilter):
  → Lê: input_path (= /dados/raiz)
  → Salva LAS filtrados em: output_path/lasblackfilter/
  → Atualiza: input_path = output_path/lasblackfilter/

Step 3 (LasTiler):
  → Lê: input_path (= /dados/raiz/lasblackfilter/)
  → Salva tiles em: output_path/lastiler/
  → Atualiza: input_path = output_path/lastiler/

Step 4 (IdwInterpolator):
  → Lê: input_path (= /dados/raiz/lastiler/)
  → Salva rasters em: output_path/idwtiles/
  → Atualiza: input_path = output_path/idwtiles/

Step 5 (Merge):
  → Lê: input_path (= /dados/raiz/idwtiles/)
  → Salva merged em: output_path/merge/
  → Atualiza: input_path = output_path/merge/

Step 6 (RasterCheck):
  → Lê: input_path (= /dados/raiz/merge/)
  → Salva relatório em: output_path/rastercheck/
  → NÃO atualiza input_path
```

### 1.4 Variáveis de Instrução por Step
Alguns steps precisam de parâmetros extras além do fluxo básico:
- `LasTilerStep`: `pontos_por_parte`
- `IdwInterpolatorStep`: `target_bands`, `resol_m`, `idw_k`, `idw_power`, etc.
- `LasBlackFilterStep`: `limiar`, `salvar_pretos`
- `LasCheckStep`: `checks_enabled`
Vamos chamar de parametros exclusivos e passar eles assim
AsyncPipelineEngine[LasCheckStep(modified_path = false), LasBlackFilterStep(limiar = 0.5, salvar_pretos = True), LasTilerStep, IdwInterpolatorStep, MergeRastersStep, RasterCheckStep]
**Solução:** Manter como atributos opcionais no contexto, mas documentados e com defaults.

---

## 2. Modificações no ExecutionContext

### 2.1 Atributos Canônicos (Propriedades)

```python
class ExecutionContext:
    # ── Atributos canônicos do pipeline ──────────────────────────
    gambiarra aqui nao quero assim e complexo e dificil de manter vamos usar variaveis  
    
    input_path = str
        """Diretório de entrada com arquivos a processar."""

    output_path = str
        """Diretório base onde os resultados serão salvos."""

        ...
    
    @property
    def files(self) -> list[str] | None:
        """
        Lista específica de arquivos a processar.
        None = processar todos os arquivos compatíveis no input_path.
        """
        return self._data.get("files", None)
    
    @files.setter
    def files(self, value: list[str] | None) -> None:
        self._data["files"] = value
    
    @property
    def tool_key(self) -> str:
        """ToolKey para logging."""
        return self._data.get("tool_key", ToolKey.UNTRACEABLE.value)
    
    @tool_key.setter
    def tool_key(self, value: str) -> None:
        self._data["tool_key"] = value
    
    @property
    def step_name(self) -> str:
        """Nome do step atual (usado para criar subpasta de saída)."""
        return self._data.get("step_name", "")
    
    @step_name.setter
    def step_name(self, value: str) -> None:
        self._data["step_name"] = value
```

### 2.2 Método Utilitário: output_subdir
errado tambem cada steps deve ter defiunido como uma contante o nome da sua subpasta de saída, e o output_subdir deve ser derivado de output_path + step_name
eu tambem poderia passar um input_path direto para um step para quando eu quiser processar um arquivo específico, mas o padrão é que cada step use input_path e output_subdir
AsyncPipelineEngine[, LasBlackFilterStep, LasTilerStep, IdwInterpolatorStep, MergeRastersStep, RasterCheckStep, LasCheckStep(modified_path = false, input_path = "D:/raiz/dados/lasblackfilter/")]
no ultimo step eu pasesei um input _path específico para processar apenas os arquivos filtrados, mas o padrão é que cada step use input_path e output_subdir mas quando algo fugir do padrao eu posso ter a liberdade de modificar 



### 2.3 Método Utilitário: advance_input

```python
def advance_input(self) -> None:
    """
    Atualiza input_path para apontar para a subpasta de saída do step atual.
    Usado por steps que transformam dados (ex: LasBlackFilter, LasTiler, IDW).
    Steps que só analisam (ex: LasCheck, RasterCheck) NÃO chamam este método.
    """
    self.input_path = self.output_subdir #defina esse metodo em @baseStep
```

### 2.4 Método Utilitário: resolve_files
#organizacao aqui, o plugin tem que passar a lista correta, de arquivos a processar ou a pasta inteira (recomendado )
```python
def resolve_files(self, *extensions: str) -> list[str]:
    """
    Retorna a lista de arquivos a processar.
    - Se self.files estiver definido, retorna self.files
    - Senão, lista todos os arquivos com as extensões fornecidas em input_path
    """
    if self.files is not None:
        return self.files
    import glob
    files = []
    for ext in extensions:
        pattern = os.path.join(self.input_path, f"*{ext}")
        files.extend(glob.glob(pattern))
    return sorted(files)
```

### 2.5 Acesso Genérico (para parâmetros extras)

Manter `get()` e `set()` para parâmetros específicos de cada step:

```python
# Parâmetros extras (específicos de cada step)
ja definimos que isso nao vai ficar no contexto e sim ser passado diretamente para o step 
context.get("pontos_por_parte", 5_000_000)
context.get("target_bands", {"r": True, "g": True, "b": True, "z": False})
context.get("limiar", 0)
```

---

## 3. Modificações nos Steps
   
refaça

## 4. Modificações no PipelineRunner

### 4.1 Injeção Automática de step_name

O `PipelineRunner` deve injetar automaticamente o `step_name` no contexto antes de cada step:

```python
class PipelineRunner(QThread):
    def run(self) -> None:
        ctx = ExecutionContext(self._context_data)
        # ... governor setup ...
        
        self._engine = AsyncPipelineEngine(
            steps=self._steps,
            context=ctx,
            ...
        )
        self._engine.start_non_blocking()
```

E no `AsyncPipelineEngine`, antes de executar cada step:

```python
def _run_loop(self, blocking: bool) -> None:
    while self._is_running and not self._is_cancelled:
        # ...
        step = self._steps[self._current_index]
        
        # Injeta step_name automaticamente
        self._context.step_name = step.name()
        
        # ... executa step ...
```

---

## 5. Variáveis Canônicas do ExecutionContext

### 5.1 Definição Final

| Variável | Tipo | Origem | Descrição |
|----------|------|--------|-----------|
| `input_path` | `str` | Plugin/Step anterior | Diretório com arquivos de entrada |
| `output_path` | `str` | Plugin (config) | Diretório base para salvar resultados |
| `files` | `list[str] \| None` | Plugin/Step anterior | Lista específica de arquivos (None = todos) |
| `tool_key` | `str` | Plugin | ToolKey para logging |
| `step_name` | `str` | Engine (auto) | Nome do step atual (para subpasta) |  melhor colocar subpasta como variavel em cada step 
| `output_subdir` | `str` | Engine (auto) | `output_path/step_name/` (criado automaticamente) |

### 5.2 Variáveis Específicas por Step

| Step | Variáveis |
|------|-----------|
| `LasCheckStep` | `checks_enabled: dict[str, bool]` |
| `LasBlackFilterStep` | `limiar: int`, `salvar_pretos: bool` |
| `LasTilerStep` | `pontos_por_parte: int` |
| `IdwInterpolatorStep` | `target_bands: dict`, `merge_bands: bool`, `resol_m: float`, `idw_k: int`, `idw_power: float`, `idw_raio_max: float`, `idw_overlap: float`, `crs_str: str`, `eliminar_tiles: bool`, `salvar_las: bool` |
| `MergeRastersStep` | (nenhuma além das canônicas) |
| `RasterCheckStep` | (nenhuma além das canônicas) |

---

## 6. Exemplo de Pipeline Completa

```python
# Plugin prepara o contexto
runner = PipelineRunner(
    steps=[
        LasCheckStep(incluir parametros aqui ),           # Analisa → salva em /output/lascheck/
        LasBlackFilterStep(),     # Filtra → salva em /output/lasblackfilter/ → advance_input
        LasCheckStep(),           # Re-analisa os filtrados em /output/lasblackfilter/
        LasTilerStep(),           # Tilea → salva em /output/lastiler/ → advance_input
        IdwInterpolatorStep(),    # Interpola → salva em /output/idwtiles/ → advance_input
        MergeRastersStep(),       # Merge → salva em /output/merge/ → advance_input
        RasterCheckStep(),        # Valida → salva em /output/rastercheck/
    ],
    context={
        "input_path": "D:/raiz/dados",
        "output_path": "D:/raiz",
        "tool_key": ToolKey.IDW_INTERPOLATOR.value,
        # Parâmetros específicos
        "pontos_por_parte": 5_000_000,
        "target_bands": {"r": True, "g": True, "b": True, "z": True},
        "resol_m": 0.01,
        "limiar": 30,
    },
    parent=self,
)
```

---

## 7. Ordem de Implementação

### Fase 1 — ExecutionContext (core)
- [ ] 1.1 Adicionar `@property input_path`, `output_path`, `files`, `tool_key`, `step_name`
- [ ] 1.2 Adicionar `@property output_subdir` (cria pasta automaticamente)
- [ ] 1.3 Adicionar `advance_input()` (input_path = output_subdir)
- [ ] 1.4 Adicionar `resolve_files(*extensions)` (usa files ou lista diretório)
- [ ] 1.5 Manter `get()`/`set()` para compatibilidade e parâmetros extras
- [ ] 1.6 Remover class variables `INPUT_PATH`, `OUTPUT_PATH`, `TOOL_KEY` (obsoletas)

### Fase 2 — AsyncPipelineEngine
- [ ] 2.1 Injetar `step_name` automaticamente antes de cada step
- [ ] 2.2 Garantir que `output_subdir` seja criado antes da execução

### Fase 3 — Steps (refatorar um por um)
- [ ] 3.1 `LasCheckStep` → usar `input_path`, `resolve_files()`, `output_subdir`
- [ ] 3.2 `LasBlackFilterStep` → usar `input_path`, `resolve_files()`, `advance_input()`
- [ ] 3.3 `LasTilerStep` → usar `input_path`, `resolve_files()`, `advance_input()`
- [ ] 3.4 `IdwInterpolatorStep` → usar `input_path`, `advance_input()`
- [ ] 3.5 `MrkSteps` → manter compatibilidade (não usam pipeline de LAS)
- [ ] 3.6 `DoclingSteps` → manter compatibilidade (não usam pipeline de LAS)

### Fase 4 — Novos Steps
- [ ] 4.1 Criar `MergeRastersStep` + `MergeRastersTask`
- [ ] 4.2 Criar `RasterCheckStep` (run_inline)

### Fase 5 — Plugins (atualizar chamadas)
- [ ] 5.1 `LasCheckPlugin` → usar `input_path` em vez de `file_path`
- [ ] 5.2 `LasBlackFilterPlugin` → usar `input_path` em vez de `file_path`
- [ ] 5.3 `LasTilerPlugin` → usar `input_path` em vez de `file_path`
- [ ] 5.4 `IdwInterpolatorPlugin` → usar `input_path` em vez de `input_dir`
- [ ] 5.5 `PointBoundaryStep` → adaptar para novo padrão (se aplicável)

### Fase 6 — Documentação
- [ ] 6.1 Atualizar `SKILL_ASYNC_PIPELINE.md` com novo padrão
- [ ] 6.2 Atualizar `SKILL_AGENT.md` se necessário
- [ ] 6.3 Atualizar `contracts.md` se houver novos contratos

---

## 8. Contratos Novos/Atualizados

### Contrato 27 — Atributos Canônicos do ExecutionContext
```
Todo step DEVE usar os atributos canônicos do ExecutionContext:
- input_path, output_path, files, tool_key, step_name
- output_subdir para pasta de saída do step
- advance_input() para propagar output como input do próximo step
- resolve_files() para obter lista de arquivos
```

### Contrato 28 — Steps que Transformam vs Steps que Analisam
```
Steps que TRANSFORMAM dados (filtram, tileam, interpolam, merge):
  → Chamam advance_input() em on_success()
  → Próximo step recebe a pasta transformada como input

Steps que ANALISAM dados (check, validação):
  → NÃO chamam advance_input()
  → Próximo step recebe a mesma pasta que o step atual
```

### Contrato 29 — step_name Automático
```
O step_name é injetado automaticamente pelo AsyncPipelineEngine.
Steps NUNCA devem setar step_name manualmente.
O output_subdir é derivado automaticamente de output_path + step_name.
```

---

## 9. Riscos e Mitigações

| Risco | Mitigação |
|-------|-----------|
| Quebrar plugins existentes | Manter `get()`/`set()` como fallback; migrar gradualmente |
| Steps que esperam arquivo único vs diretório | `resolve_files()` retorna lista; step decide se processa 1 ou N |
| Subpastas aninhadas demais | `output_subdir` cria apenas 1 nível (`output_path/step_name/`) |
| Compatibilidade com MrkSteps/DoclingSteps | Não usar `advance_input()` neles; manter `get()`/`set()` |