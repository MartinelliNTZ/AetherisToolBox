# Plano de Ação: Padronização do ExecutionContext e Fluxo de Pipeline

## 1. Problemas Identificados

### 1.1 Acesso a Dados — Dict vs Atributos
Atualmente o `ExecutionContext` usa acesso estilo dicionário:
```python
context.get("file_path", "")
context.get("target_bands", {})
context.set("split_result", result)
```

**Problema:** Sem autocomplete, sem tipagem, sem documentação visível.

**Solução:** Variáveis de classe simples no `ExecutionContext`:
```python
context.input_path       # str — acesso direto a atributo
context.output_path      # str
context.files            # list[str] | None
```

### 1.2 Parâmetros Exclusivos Misturados no Contexto
Atualmente parâmetros específicos de cada step ficam soltos no context:
```python
context.get("pontos_por_parte", 5_000_000)
context.get("limiar", 0)
context.get("target_bands", {})
```

**Problema:** Contexto vira uma "sopa de letrinhas" sem separação do que é fluxo vs. específico.

**Solução:** Parâmetros exclusivos são passados DIRETAMENTE no construtor do step:
```python
AsyncPipelineEngine(
    steps=[
        LasCheckStep(modified_path=False),
        LasBlackFilterStep(limiar=30, salvar_pretos=True),
        LasTilerStep(pontos_por_parte=5_000_000),
        IdwInterpolatorStep(target_bands={...}, resol_m=0.01),
        MergeRastersStep(),
        RasterCheckStep(modified_path=False),
    ],
    context={...},
)
```

### 1.3 Steps Não Atualizam input_path para o Próximo Step
Atualmente cada step recebe parâmetros fixos e não propaga seu output como input do próximo.

**Solução:** Convenção de fluxo com flag `modified_path`:
`modified_path=True`  nao preciso passar toda vez somente quandoquero false
- `modified_path=True` (padrão) → step TRANSFORMA dados → chama `advance_input()` em `on_success()`
- `modified_path=False` → step só ANALISA → NÃO chama `advance_input()`

```
input_path = /dados/raiz
output_path = /dados/raiz

Step 1 (LasCheck, modified_path=False):
  → Lê: input_path
  → Salva relatório em: output_path/lascheck/
  → input_path continua = /dados/raiz

Step 2 (LasBlackFilter, modified_path=True):
  → Lê: input_path (= /dados/raiz)
  → Salva LAS filtrados em: output_path/lasblackfilter/
  → advance_input: input_path = /dados/raiz/lasblackfilter/

Step 3 (LasTiler, modified_path=True):
  → Lê: input_path (= /dados/raiz/lasblackfilter/)
  → Salva tiles em: output_path/lastiler/
  → advance_input: input_path = /dados/raiz/lastiler/

Step 4 (IdwInterpolator, modified_path=True):
  → Lê: input_path (= /dados/raiz/lastiler/)
  → Salva rasters em: output_path/idwtiles/
  → advance_input: input_path = /dados/raiz/idwtiles/

Step 5 (Merge, modified_path=True):
  → Lê: input_path (= /dados/raiz/idwtiles/)
  → Salva merged em: output_path/merge/
  → advance_input: input_path = /dados/raiz/merge/

Step 6 (RasterCheck, modified_path=False):
  → Lê: input_path (= /dados/raiz/merge/)
  → Salva relatório em: output_path/rastercheck/
  → input_path continua = /dados/raiz/merge/
```

**Ordem pode ser invertida** — cada step sabe de onde ler e para onde salvar. O pipeline funciona independentemente da ordem dos steps.

### 1.4 input_path Específico por Step (Exceção)
Em casos específicos, um step pode receber um `input_path` diferente do contexto:

```python
AsyncPipelineEngine(
    steps=[
        LasBlackFilterStep(),
        LasTilerStep(),
        IdwInterpolatorStep(),
        MergeRastersStep(),
        RasterCheckStep(),
        LasCheckStep(modified_path=False, input_path="D:/raiz/dados/lasblackfilter/"),
    ],
    ...
)
```

Aqui o último `LasCheckStep` recebe um `input_path` específico para analisar APENAS a pasta filtrada, ignorando o fluxo padrão.

---

## 2. Modificações no ExecutionContext

### 2.1 Atributos Canônicos (Variáveis de Classe Simples)

Nada de `@property` — variáveis de classe diretas, sem gambiarra:

```python
class ExecutionContext:
    """
    Container de estado compartilhado entre todos os steps da pipeline.
    
    Atributos canônicos (acesso direto):
        input_path: str    — Diretório de entrada com arquivos a processar
        output_path: str   — Diretório base onde os resultados serão salvos
        files: list[str] | None — Lista específica de arquivos (None = todos no input_path)
        tool_key: str      — ToolKey para logging
    """

    input_path: str = ""
    """Diretório de entrada com arquivos a processar."""

    output_path: str = ""
    """Diretório base onde os resultados serão salvos."""

    files: list[str] | None = None
    """Lista específica de arquivos a processar. None = todos no input_path."""

    tool_key: str = ""
    """ToolKey para logging."""

    def __init__(self, initial_data: dict = None):
        self._data: dict = initial_data.copy() if initial_data else {}
        self._errors: list[Exception] = []
        self._is_cancelled: bool = False

        # Sincroniza _data com atributos de classe
        if initial_data:
            if "input_path" in initial_data:
                self.input_path = initial_data["input_path"]
            if "output_path" in initial_data:
                self.output_path = initial_data["output_path"]
            if "files" in initial_data:
                self.files = initial_data["files"]
            if "tool_key" in initial_data:
                self.tool_key = initial_data["tool_key"]
```

### 2.2 Manter `get()`/`set()` para Compatibilidade

```python
    def set(self, key: str, value: Any) -> ExecutionContext:
        """Armazena valor no contexto. Retorna self para fluent interface."""
        self._data[key] = value
        return self

    def get(self, key: str, default: Any = None) -> Any:
        """Recupera valor do contexto."""
        return self._data.get(key, default)
```

### 2.3 Remover Class Variables Obsoletas

Remover:
```python
INPUT_PATH = None   # ❌ REMOVER
OUTPUT_PATH = None  # ❌ REMOVER
TOOL_KEY = None     # ❌ REMOVER
```

---

## 3. Modificações no BaseStep

### 3.1 Novo Atributo: `modified_path`

```python
class BaseStep(ABC):
    """Contrato que define uma etapa da pipeline."""

    # ── Atributos de configuração do step ───────────────────────
    subpasta: str = ""  #SUBFOLDER  nomes de metodos paramtros clases tudo e em ingles  ta nop contrato 
    """Nome da subpasta de saída (ex: 'lascheck', 'lasblackfilter'). 
    Usado para criar output_path/subpasta/ automaticamente."""

    modified_path: bool = True
    """
    Se True (padrão): step TRANSFORMA dados → chama advance_input() em on_success()
    Se False: step só ANALISA → NÃO chama advance_input()
    """
```

### 3.2 Novo Método: `advance_input()`

```python
    def advance_input(self, context: ExecutionContext) -> None:
        """
        Atualiza input_path para apontar para a subpasta de saída do step atual.
        Chamado automaticamente em on_success() se modified_path == True.
        """
        if self.subpasta:
            context.input_path = os.path.join(context.output_path, self.subpasta)
```

### 3.3 Novo Método: `resolve_files()`

```python
    def resolve_files(self, context: ExecutionContext, *extensions: str) -> list[str]:
        """
        Retorna a lista de arquivos a processar.
        - Se context.files estiver definido, retorna context.files
        - Senão, lista todos os arquivos com as extensões fornecidas em context.input_path
        """
        if context.files is not None:
            return context.files
        files = []
        for ext in extensions:
            pattern = os.path.join(context.input_path, f"*{ext}")
            files.extend(glob.glob(pattern))
        return sorted(files)
```

### 3.4 Novo Método: `output_subdir()`

```python
    @property
    def output_subdir(self, context: ExecutionContext) -> str:
        """
        Retorna o caminho completo da subpasta de saída.
        Ex: output_path + "/" + subpasta
        Cria a pasta se não existir.
        """
        if not self.subpasta:
            return context.output_path
        subdir = os.path.join(context.output_path, self.subpasta)
        os.makedirs(subdir, exist_ok=True)
        return subdir
```

### 3.5 on_success() com advance_input Automático

```python
    def on_success(self, context: ExecutionContext, result: Any) -> None:
        """
        Callback padrão: se modified_path == True, avança o input_path.
        Steps que transformam dados SOBRESCREVEM este método para mapear resultados.
        Steps que só analisam (modified_path=False) não precisam fazer nada.
        """
        if self.modified_path:
            self.advance_input(context)
```

---

## 4. Modificações nos Steps Concretos

### 4.1 LasCheckStep

```python
class LasCheckStep(BaseStep):
    subpasta = "lascheck"
    modified_path = False  # Só analisa, não transforma

    def __init__(self, modified_path: bool = False, input_path: str = ""):
        self.modified_path = modified_path
        self._custom_input_path = input_path  # input_path específico (opcional)

    def name(self) -> str:
        return "lascheck"

    def should_run(self, context: ExecutionContext) -> bool:
        # Se tem input_path custom, usa ele
        path = self._custom_input_path or context.input_path
        return bool(path)

    def run_inline(self, context: ExecutionContext) -> dict:
        path = self._custom_input_path or context.input_path
        files = self.resolve_files(context, ".las", ".laz")
        # ... processa cada arquivo ...
        # Salva relatório em output_subdir
        report_path = os.path.join(self.output_subdir(context), "check_report.json")
        return {"check_results": results, "report_path": report_path}
```

### 4.2 LasBlackFilterStep

```python
class LasBlackFilterStep(BaseStep):
    subpasta = "lasblackfilter"
    modified_path = True  # Transforma dados

    def __init__(self, limiar: int = 0, salvar_pretos: bool = False, 
                 modified_path: bool = True, input_path: str = ""):
        self._limiar = limiar
        self._salvar_pretos = salvar_pretos
        self.modified_path = modified_path
        self._custom_input_path = input_path

    def name(self) -> str:
        return "lasblackfilter"

    def create_task(self, context: ExecutionContext) -> LasBlackFilterTask:
        path = self._custom_input_path or context.input_path
        files = self.resolve_files(context, ".las", ".laz")
        return LasBlackFilterTask(
            files=files,
            output_dir=self.output_subdir(context),
            limiar=self._limiar,
            salvar_pretos=self._salvar_pretos,
        )

    def on_success(self, context: ExecutionContext, result: Any) -> None:
        if isinstance(result, dict):
            context.set("filter_result", result)
        self.advance_input(context)  # modified_path = True
```

### 4.3 LasTilerStep

```python
class LasTilerStep(BaseStep):
    subpasta = "lastiler"
    modified_path = True

    def __init__(self, pontos_por_parte: int = 5_000_000,
                 modified_path: bool = True, input_path: str = ""):
        self._pontos_por_parte = pontos_por_parte
        self.modified_path = modified_path
        self._custom_input_path = input_path

    def name(self) -> str:
        return "lastiler"

    def create_task(self, context: ExecutionContext) -> LasTilerTask:
        path = self._custom_input_path or context.input_path
        files = self.resolve_files(context, ".las", ".laz")
        return LasTilerTask(
            files=files,
            output_dir=self.output_subdir(context),
            pontos_por_parte=self._pontos_por_parte,
        )

    def on_success(self, context: ExecutionContext, result: Any) -> None:
        if isinstance(result, dict):
            context.set("split_result", result)
        self.advance_input(context)
```

### 4.4 IdwInterpolatorStep

```python
class IdwInterpolatorStep(BaseStep):
    subpasta = "idwtiles"
    modified_path = True

    def __init__(self, target_bands: dict = None, merge_bands: bool = True,
                 resol_m: float = 0.01, idw_k: int = 5, idw_power: float = 2.0,
                 idw_raio_max: float = 0.5, idw_overlap: float = 3.0,
                 crs_str: str = "EPSG:31982", eliminar_tiles: bool = True,
                 salvar_las: bool = False,
                 modified_path: bool = True, input_path: str = ""):
        self._target_bands = target_bands or {}
        self._merge_bands = merge_bands
        self._resol_m = resol_m
        self._idw_k = idw_k
        self._idw_power = idw_power
        self._idw_raio_max = idw_raio_max
        self._idw_overlap = idw_overlap
        self._crs_str = crs_str
        self._eliminar_tiles = eliminar_tiles
        self._salvar_las = salvar_las
        self.modified_path = modified_path
        self._custom_input_path = input_path

    def name(self) -> str:
        return "idwtiles"

    def create_task(self, context: ExecutionContext) -> IdwInterpolatorTask:
        path = self._custom_input_path or context.input_path
        return IdwInterpolatorTask(
            input_dir=path,
            output_path=os.path.join(self.output_subdir(context), "merged.tif"),
            target_bands=self._target_bands,
            merge_bands=self._merge_bands,
            resol_m=self._resol_m,
            idw_k=self._idw_k,
            idw_power=self._idw_power,
            idw_raio_max=self._idw_raio_max,
            idw_overlap=self._idw_overlap,
            crs_str=self._crs_str,
            eliminar_tiles=self._eliminar_tiles,
            salvar_las=self._salvar_las,
        )

    def on_success(self, context: ExecutionContext, result: Any) -> None:
        if isinstance(result, dict):
            context.set("idw_result", result)
        self.advance_input(context)
```

### 4.5 MergeRastersStep (NOVO)

```python
class MergeRastersStep(BaseStep):
    subpasta = "merge"
    modified_path = True

    def __init__(self, modified_path: bool = True, input_path: str = ""):
        self.modified_path = modified_path
        self._custom_input_path = input_path

    def name(self) -> str:
        return "merge"

    def create_task(self, context: ExecutionContext) -> MergeRastersTask:
        path = self._custom_input_path or context.input_path
        return MergeRastersTask(
            input_dir=path,
            output_path=os.path.join(self.output_subdir(context), "merged.tif"),
        )

    def on_success(self, context: ExecutionContext, result: Any) -> None:
        if isinstance(result, dict):
            context.set("merge_result", result)
        self.advance_input(context)
```

### 4.6 RasterCheckStep (NOVO)

```python
class RasterCheckStep(BaseStep):
    subpasta = "rastercheck"
    modified_path = False  # Só analisa

    def __init__(self, modified_path: bool = False, input_path: str = ""):
        self.modified_path = modified_path
        self._custom_input_path = input_path

    def name(self) -> str:
        return "rastercheck"

    def run_inline(self, context: ExecutionContext) -> dict:
        path = self._custom_input_path or context.input_path
        # Valida rasters no input_path
        # Salva relatório em output_subdir
        return {"check_results": results}
```

---

## 5. Modificações no AsyncPipelineEngine

### 5.1 Injeção Automática de input_path Custom

Se o step tiver `_custom_input_path`, o engine usa esse valor em vez do `context.input_path`:

```python
def _run_loop(self, blocking: bool) -> None:
    while self._is_running and not self._is_cancelled:
        step = self._steps[self._current_index]

        # Se o step tem input_path custom, sobrescreve no contexto
        custom_path = getattr(step, "_custom_input_path", None)
        if custom_path:
            self._context.input_path = custom_path

        # ... executa step ...
```

---

## 6. Variáveis Canônicas do ExecutionContext

### 6.1 Definição Final

| Variável | Tipo | Origem | Descrição |
|----------|------|--------|-----------|
| `input_path` | `str` | Plugin / Step anterior | Diretório com arquivos de entrada |
| `output_path` | `str` | Plugin (config) | Diretório base para salvar resultados |
| `files` | `list[str] \| None` | Plugin | Lista específica de arquivos (None = todos) |
| `tool_key` | `str` | Plugin | ToolKey para logging |

### 6.2 Atributos do Step (definidos em cada step concreto)

| Atributo | Tipo | Onde define | Descrição |
|----------|------|-------------|-----------|
| `subpasta` | `str` | Constante no step | Nome da subpasta de saída |
| `modified_path` | `bool` | Construtor do step | Se True, chama advance_input() |
| `_custom_input_path` | `str` | Construtor (opcional) | input_path específico para este step |

### 6.3 Parâmetros Exclusivos por Step

| Step | Parâmetros (passados no construtor) |
|------|--------------------------------------|
| `LasCheckStep` | `modified_path=False`, `input_path=""` |
| `LasBlackFilterStep` | `limiar: int=0`, `salvar_pretos: bool=False`, `modified_path=True`, `input_path=""` |
| `LasTilerStep` | `pontos_por_parte: int=5_000_000`, `modified_path=True`, `input_path=""` |
| `IdwInterpolatorStep` | `target_bands: dict`, `merge_bands: bool=True`, `resol_m: float=0.01`, `idw_k: int=5`, `idw_power: float=2.0`, `idw_raio_max: float=0.5`, `idw_overlap: float=3.0`, `crs_str: str="EPSG:31982"`, `eliminar_tiles: bool=True`, `salvar_las: bool=False`, `modified_path=True`, `input_path=""` |
| `MergeRastersStep` | `modified_path=True`, `input_path=""` |
| `RasterCheckStep` | `modified_path=False`, `input_path=""` |

---

## 7. Exemplo de Pipeline Completa

```python
runner = PipelineRunner(
    steps=[
        LasCheckStep(modified_path=False),                    # Analisa → /output/lascheck/
        LasBlackFilterStep(limiar=30, salvar_pretos=True),    # Filtra → /output/lasblackfilter/ → advance
        LasCheckStep(modified_path=False),                    # Re-analisa filtrados
        LasTilerStep(pontos_por_parte=5_000_000),             # Tilea → /output/lastiler/ → advance
        IdwInterpolatorStep(                                  # Interpola → /output/idwtiles/ → advance
            target_bands={"r": True, "g": True, "b": True, "z": True},
            resol_m=0.01,
        ),
        MergeRastersStep(),                                   # Merge → /output/merge/ → advance
        RasterCheckStep(modified_path=False),                 # Valida → /output/rastercheck/
    ],
    context={
        "input_path": "D:/raiz/dados",
        "output_path": "D:/raiz",
        "tool_key": ToolKey.IDW_INTERPOLATOR.value,
    },
    parent=self,
)
```

### Exemplo com input_path Específico

```python
runner = PipelineRunner(
    steps=[
        LasBlackFilterStep(limiar=30),
        LasTilerStep(pontos_por_parte=5_000_000),
        IdwInterpolatorStep(target_bands={"r": True, "g": True, "b": True}),
        MergeRastersStep(),
        RasterCheckStep(modified_path=False),
        LasCheckStep(modified_path=False, input_path="D:/raiz/dados/lasblackfilter/"),
    ],
    context={
        "input_path": "D:/raiz/dados",
        "output_path": "D:/raiz",
        "tool_key": ToolKey.IDW_INTERPOLATOR.value,
    },
    parent=self,
)
```

---

## 8. Ordem de Implementação

### Fase 1 — ExecutionContext (core)
- [ ] 1.1 Adicionar variáveis de classe: `input_path`, `output_path`, `files`, `tool_key`
- [ ] 1.2 Sincronizar `__init__` para popular as variáveis a partir do dict inicial
- [ ] 1.3 Manter `get()`/`set()` para compatibilidade com código legado
- [ ] 1.4 Remover class variables `INPUT_PATH`, `OUTPUT_PATH`, `TOOL_KEY`

### Fase 2 — BaseStep (core)
- [ ] 2.1 Adicionar atributo `subpasta: str = ""`
- [ ] 2.2 Adicionar atributo `modified_path: bool = True`
- [ ] 2.3 Adicionar método `advance_input(context)`
- [ ] 2.4 Adicionar método `resolve_files(context, *extensions)`
- [ ] 2.5 Adicionar property `output_subdir(context)`
- [ ] 2.6 Modificar `on_success()` padrão para chamar `advance_input()` se `modified_path == True`

### Fase 3 — AsyncPipelineEngine
- [ ] 3.1 Verificar `_custom_input_path` no step e sobrescrever `context.input_path` se presente

### Fase 4 — Steps (refatorar um por um)
- [ ] 4.1 `LasCheckStep` → adicionar `subpasta`, `modified_path=False`, `__init__` com parâmetros
- [ ] 4.2 `LasBlackFilterStep` → adicionar `subpasta`, `__init__` com parâmetros exclusivos
- [ ] 4.3 `LasTilerStep` → adicionar `subpasta`, `__init__` com parâmetros exclusivos
- [ ] 4.4 `IdwInterpolatorStep` → adicionar `subpasta`, `__init__` com parâmetros exclusivos
- [ ] 4.5 `MrkSteps` → manter compatibilidade (não usam pipeline de LAS)
- [ ] 4.6 `DoclingSteps` → manter compatibilidade (não usam pipeline de LAS)

### Fase 5 — Novos Steps
- [ ] 5.1 Criar `MergeRastersStep` + `MergeRastersTask`
- [ ] 5.2 Criar `RasterCheckStep` (run_inline)

### Fase 6 — Plugins (atualizar chamadas)
- [ ] 6.1 `LasCheckPlugin` → passar parâmetros no construtor do step
- [ ] 6.2 `LasBlackFilterPlugin` → passar parâmetros no construtor do step
- [ ] 6.3 `LasTilerPlugin` → passar parâmetros no construtor do step
- [ ] 6.4 `IdwInterpolatorPlugin` → passar parâmetros no construtor do step
- [ ] 6.5 `PointBoundaryStep` → adaptar para novo padrão (se aplicável)

### Fase 7 — Documentação
- [ ] 7.1 Atualizar `SKILL_ASYNC_PIPELINE.md` com novo padrão
- [ ] 7.2 Atualizar `SKILL_AGENT.md` se necessário
- [ ] 7.3 Atualizar `contracts.md` se houver novos contratos

---

## 9. Contratos Novos/Atualizados

### Contrato 27 — Atributos Canônicos do ExecutionContext
```
O ExecutionContext possui variáveis de classe para acesso direto:
- input_path, output_path, files, tool_key

NUNCA use @property ou getters/setters para esses atributos.
Acesso é direto: context.input_path = "/caminho"
```

### Contrato 28 — Parâmetros Exclusivos no Construtor do Step
```
Parâmetros específicos de cada step são passados DIRETAMENTE no construtor:
    LasBlackFilterStep(limiar=30, salvar_pretos=True)

NUNCA misture parâmetros exclusivos no ExecutionContext.
O context contém APENAS: input_path, output_path, files, tool_key.
```

### Contrato 29 — modified_path (Transforma vs Analisa)
```
Todo step define modified_path:
- True (padrão): step TRANSFORMA dados → advance_input() em on_success()
- False: step só ANALISA → NÃO avança input_path

Steps que transformam: LasBlackFilter, LasTiler, IdwInterpolator, Merge
Steps que analisam: LasCheck, RasterCheck
```

### Contrato 30 — subpasta Constante no Step
```
Cada step define subpasta como constante da classe:
    subpasta = "lascheck"  # Nome da subpasta de saída

O output_subdir é derivado automaticamente: output_path + "/" + subpasta
```

### Contrato 31 — input_path Específico (Exceção)
```
Um step pode receber input_path próprio no construtor para casos específicos:
    LasCheckStep(modified_path=False, input_path="D:/raiz/dados/lasblackfilter/")

Isso sobrescreve context.input_path APENAS para aquele step.
Use com moderação — o padrão é usar context.input_path.
```

---

## 10. Riscos e Mitigações

| Risco | Mitigação |
|-------|-----------|
| Quebrar plugins existentes | Manter `get()`/`set()` como fallback; migrar gradualmente |
| Steps que esperam arquivo único vs diretório | `resolve_files()` retorna lista; step decide se processa 1 ou N |
| Compatibilidade com MrkSteps/DoclingSteps | Não usam `subpasta`/`modified_path`; manter `get()`/`set()` |
| Usuário esquecer de passar parâmetro obrigatório | Construtor tem defaults sensatos; validação em `should_run()` |