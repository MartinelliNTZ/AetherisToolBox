# Skill: Sistema de Pipeline Assíncrono (AsyncPipeline)

Esta skill documenta o sistema de pipeline assíncrono implementado em `core/papeline/`, descrevendo sua arquitetura, componentes e como criar novas pipelines.

---

## 📋 Visão Geral

O sistema implementa um **pipeline sequencial assíncrono** composto por etapas (`Steps`) executadas uma após a outra. Cada etapa pode executar uma tarefa pesada em background e, ao finalizar, chama callbacks de sucesso/erro que avançam para a próxima etapa.

```
iniciar → step 1 → task assíncrona → callback sucesso → step 2 → ... → finalizar
```

## 🧱 Arquitetura

```
core/papeline/
├── __init__.py               — Exporta classes públicas (6 componentes)
├── ExecutionContext.py        — Estado compartilhado entre steps
├── BaseTask.py                — Wrapper abstrato para trabalho em background
├── BaseStep.py                — Contrato abstrato para etapas da pipeline
├── AsyncPipelineEngine.py     — Orquestrador (blocking thread.join)
├── QtPipelineEngine.py        — Executa pipeline em QThread (não bloqueante)
├── task/
│   ├── __init__.py            — Exporta tasks concretas (2 classes)
│   ├── MrkSinglePipelineTask.py — MrkSinglePipelineTask (BaseTask)
│   └── DoclingPipelineTask.py    — DoclingPipelineTask (BaseTask)
└── step/
    ├── __init__.py            — Exporta steps concretos
    ├── MrkSteps.py            — Steps MRK (MrkLoadDataStep, MrkProcessStep, MrkFindDataStep)
    └── DoclingSteps.py        — Steps Docling (DoclingConvertStep, DoclingSaveStep)
```

## 📦 Componentes

### `ExecutionContext` — `core/papeline/ExecutionContext.py`

Container de estado compartilhado entre todos os steps da pipeline.

```python
from core.papeline import ExecutionContext

ctx = ExecutionContext({"arquivo": "teste.mrk"})
ctx.set("resultado", 42)
ctx.set("caminho", "/tmp/saida").set("status", "ok")  # fluent

valor = ctx.get("resultado", default=0)
existe = ctx.has("caminho")
ctx.require(["caminho", "resultado"])  # KeyError se faltar

ctx.add_error(ValueError("algo errado"))
erros = ctx.get_errors()
if ctx.has_errors(): ...

ctx.cancel()
if ctx.is_cancelled(): ...

ctx.clear()  # reseta tudo
```

**Métodos:**

| Método | Retorno | Descrição |
|--------|---------|-----------|
| `set(key, value)` | `ExecutionContext` | Armazena valor (fluent) |
| `get(key, default)` | `Any` | Recupera valor |
| `has(key)` | `bool` | Verifica existência |
| `require(keys)` | `None` | Lança `KeyError` se faltar |
| `add_error(exc)` | `None` | Adiciona erro |
| `get_errors()` | `list[Exception]` | Retorna cópia dos erros |
| `has_errors()` | `bool` | True se houve erro |
| `cancel()` | `None` | Marca cancelamento |
| `is_cancelled()` | `bool` | True se cancelado |
| `clear()` | `None` | Reseta tudo |

---

### `BaseTask` — `core/papeline/BaseTask.py`

Classe abstrata para execução de trabalho pesado em background.

```python
from core.papeline import BaseTask

class MinhaTask(BaseTask):
    def __init__(self, dado: str):
        super().__init__(description=f"Processar: {dado}")
        self._dado = dado

    def _run(self) -> bool:
        # Lógica pesada aqui
        resultado = self._dado.upper()
        self.result = {"original": self._dado, "upper": resultado}
        return True  # False se falhar
```

**Atributos:**

| Atributo | Tipo | Descrição |
|----------|------|-----------|
| `description` | `str` | Descrição para logs |
| `exception` | `Exception \| None` | Exceção capturada |
| `result` | `Any` | Resultado produzido |
| `on_success` | `callable \| None` | Callback de sucesso |
| `on_error` | `callable \| None` | Callback de erro |
| `is_cancelled` | `bool` | True se cancelada |

**Fluxo interno:**
1. `run()` é chamado
2. `run()` chama `_run()` (lógica real)
3. Se `_run()` lançar exceção → captura em `self.exception`, retorna `False`
4. Se `_run()` retornar `True` → `self.result` contém o resultado
5. `finished(success)` é chamado após o término
6. `success=True` → dispara `on_success(self.result)`
7. `success=False` → dispara `on_error(self.exception)`

> ⚠️ **Importante:** BaseTask NÃO é QThread. Para executar em thread sem travar UI, use `QtPipelineEngine`.

---

### `BaseStep` — `core/papeline/BaseStep.py`

Contrato abstrato que define uma etapa da pipeline.

```python
from core.papeline import BaseStep, ExecutionContext, BaseTask

class MeuStep(BaseStep):
    def name(self) -> str:
        return "meu_step"

    def create_task(self, context: ExecutionContext) -> BaseTask | None:
        arquivo = context.get("arquivo")
        return MinhaTask(arquivo)

    def on_success(self, context: ExecutionContext, result: Any) -> None:
        context.set("resultado_step", result)

    # Opcionais:
    def should_run(self, context: ExecutionContext) -> bool:
        return context.has("arquivo")

    def on_error(self, context: ExecutionContext, exception: Exception) -> None:
        context.add_error(exception)
```

**Métodos:**

| Método | Obrigatório | Descrição |
|--------|-------------|-----------|
| `name()` | ✅ | Identificador único |
| `create_task(context)` | ✅ | Cria `BaseTask \| None` |
| `on_success(context, result)` | ✅ | Callback de sucesso |
| `should_run(context)` | ❌ | Se `False`, step é pulado |
| `on_error(context, exception)` | ❌ | Tratamento de erro |
| `rollback(context)` | ❌ | Desfazer alterações |
| `run_inline(context)` | ❌ | Execução síncrona |

---

### `SingleTaskStep` — Step genérico (para plugins)

Step que executa UMA BaseTask a partir de uma factory function. Ideal para plugins que precisam rodar 1 task em background sem criar Steps customizados.

```python
from core.papeline import SingleTaskStep, ExecutionContext, QtPipelineEngine
from core.papeline.task import DoclingPipelineTask

step = SingleTaskStep(
    task_factory=lambda: DoclingPipelineTask(file_path, columnar=True),
    name="converter",
)
ctx = ExecutionContext({"file_path": file_path})

engine = QtPipelineEngine(steps=[step], context=ctx, parent=self)
engine.finished_ok.connect(self._on_done)
engine.failed.connect(self._on_error)
engine.start()
```

O resultado da task fica em `context.get("result")`.

---

### `QtPipelineEngine` — `core/papeline/QtPipelineEngine.py`

Executa N steps sequencialmente em uma QThread, sem travar a UI. Ideal para plugins.

```python
from core.papeline import QtPipelineEngine, ExecutionContext, SingleTaskStep

step = SingleTaskStep(task_factory=lambda: MinhaTask(dado), name="meu_step")
ctx = ExecutionContext({"dado": 42})

engine = QtPipelineEngine(steps=[step], context=ctx, parent=self)
engine.finished_ok.connect(minha_callback)
engine.failed.connect(minha_callback_erro)
engine.start()
```

**Sinais (Qt):**
| Sinal | Tipo | Descrição |
|-------|------|-----------|
| `finished_ok` | `Signal(object)` | ExecutionContext ao finalizar com sucesso |
| `failed` | `Signal(str)` | Mensagem de erro |

---

### `AsyncPipelineEngine` — `core/papeline/AsyncPipelineEngine.py`

Orquestrador principal para execução sequencial **fora do Qt**. Usa `thread.join()` — **não use em plugins** (bloqueia UI).

```python
from core.papeline import AsyncPipelineEngine, ExecutionContext

steps = [StepCarregar(), StepProcessar(), StepSalvar()]
context = ExecutionContext({"param": 10})

engine = AsyncPipelineEngine(
    steps=steps,
    context=context,
    on_finished=lambda ctx: print(f"Sucesso! {ctx.get('resultado')}"),
    on_error=lambda errors: print(f"Erros: {errors}"),
    on_cancelled=lambda ctx: print("Cancelado"),
)

engine.start()
```

**Parâmetros do construtor:**

| Parâmetro | Tipo | Descrição |
|-----------|------|-----------|
| `steps` | `list[BaseStep]` | Steps a executar |
| `context` | `ExecutionContext` | Estado compartilhado |
| `on_finished` | `callable \| None` | Callback de sucesso |
| `on_error` | `callable \| None` | Callback de erro |
| `on_cancelled` | `callable \| None` | Callback de cancelamento |

**Métodos:**

| Método | Descrição |
|--------|-----------|
| `start()` | Inicia execução |
| `cancel()` | Cancela (cooperativo) |

---

## 🧠 ResourceGovernor — Governança de Recursos

O `ResourceGovernor` é um sistema de governança de memória RAM integrado ao pipeline para evitar OOM (Out Of Memory).

### Arquitetura

```
core/governor/
├── __init__.py                 — (vazio, sem exports para evitar circular imports)
├── RamGovernor.py              — Monitora RAM (sistema, processo) via psutil
├── RamLimitPolicy.py           — Estratégias de limite (GLOBAL 90%, DEDICATED 50%)
└── ResourceGovernor.py         — Orquestrador: can_execute(), recommended_tile_size()
```

### Componentes

| Classe | Responsabilidade |
|--------|-----------------|
| `RamGovernor` | Coleta RAM total/usada/disponível do sistema + RAM do processo. |
| `RamLimitPolicy` | Estratégia: `GLOBAL` (90% do total) ou `DEDICATED` (50% fixo). |
| `ResourceGovernor` | Consultas: `can_execute()`, `recommended_tile_size()`, `snapshot()`. |

### Como usar no plugin (transparente)

O `PipelineRunner` **cria automaticamente** um `ResourceGovernor` interno.
**O plugin, step e task não precisam saber da existência do governor.**

```python
from core.papeline import PipelineRunner

# O runner já cria o governor internamente — plugin não precisa fazer nada
runner = PipelineRunner(steps=[MeuStep()], context=ctx, parent=self)
runner.finished_ok.connect(self._on_done)
runner.failed.connect(self._on_error)
runner.start()
```

### Onde o governor atua (totalmente transparente para o plugin)

1. **`PipelineRunner.run()`** — cria `ResourceGovernor` com política `GLOBAL 90%`
2. **`AsyncPipelineEngine._run_loop()`** — antes de cada task, checa `governor.can_execute()`
3. **`BaseTask.run()`** — verifica governor antes de executar `_run()`

Se a memória estourar o limite configurado, o pipeline falha com erro e o plugin recebe
o sinal `failed` normalmente — sem nenhuma alteração no código do plugin.

### Logging

O governor usa `BaseUtil._get_logger()` com `ToolKey` (Contrato 26) e logs:
- `GOV_SNAPSHOT` — debug: snapshot completo a cada inicialização
- `GOV_LOW_MEMORY` — warning: quando memória insuficiente
- `GOV_THROTTLED` — error: múltiplos warnings consecutivos

## 🔧 Tasks Concretas

### `MrkSinglePipelineTask` — `core/papeline/task/MrkSinglePipelineTask.py`

Task para processamento de arquivos MRK.

```python
from core.papeline.task import MrkSinglePipelineTask

task = MrkSinglePipelineTask(
    mrk_path="dados/arquivo.mrk",
    data=[{"Lat": "-22.123", "Lon": "-42.456"}],
    mapping={"Lat": "Lat", "Lon": "Lon", "Ellh": "Ellh"},
    output_dir="saida/",
)
```

### `DoclingPipelineTask` — `core/papeline/task/DoclingPipelineTask.py`

Task para conversão de documentos via Docling.

```python
from core.papeline.task import DoclingPipelineTask

task = DoclingPipelineTask(
    file_path="documento.pdf",
    columnar=True,
    manual_columns=0,
)
```

---

## 🎯 Exemplo Completo

### Pipeline para pipeline engine (assíncrono, não bloqueante)

```python
from core.papeline import (
    ExecutionContext,
    QtPipelineEngine,
    SingleTaskStep,
)
from core.papeline.task import DoclingPipelineTask

# Step que converte documento
step = SingleTaskStep(
    task_factory=lambda: DoclingPipelineTask("documento.pdf"),
    name="converter",
)

# Engine não bloqueante
ctx = ExecutionContext({"file": "documento.pdf"})
engine = QtPipelineEngine(steps=[step], context=ctx, parent=plugin)
engine.finished_ok.connect(lambda ctx: print(f"OK: {ctx.get('result')}"))
engine.failed.connect(lambda msg: print(f"ERRO: {msg}"))
engine.start()
```

### Pipeline com steps customizados (blocking)

```python
from core.papeline import (
    ExecutionContext,
    BaseStep,
    BaseTask,
    AsyncPipelineEngine,
)

class CalcularTask(BaseTask):
    def __init__(self, valor):
        super().__init__("calcular")
        self._valor = valor

    def _run(self) -> bool:
        self.result = self._valor * 2
        return True

class StepCalcular(BaseStep):
    def name(self): return "calcular"
    def create_task(self, ctx):
        v = ctx.get("valor", 10)
        return CalcularTask(v)
    def on_success(self, ctx, result):
        ctx.set("resultado", result)

ctx = ExecutionContext({"valor": 21})
engine = AsyncPipelineEngine(
    steps=[StepCalcular()],
    context=ctx,
    on_finished=lambda c: print(f"Pipeline OK: {c.get('resultado')}"),
)
engine.start()
```

---

## ⚠️ Regras e Comportamentos

| Comportamento | Descrição |
|---------------|-----------|
| **Pipeline só executa uma vez** | `start()` lança `RuntimeError` se já executando |
| **Steps sequenciais** | Step só começa quando anterior termina |
| **Step pode ser pulado** | `should_run()` retornando `False` |
| **Step síncrono** | `create_task()` retorna `None` + implementar `run_inline()` |
| **Erro para a pipeline** | Exceção em qualquer step interrompe a execução |
| **Cancelamento cooperativo** | Step DEVE verificar `context.is_cancelled()` |
| **Contexto é o estado** | Steps comunicam-se exclusivamente via `ExecutionContext` |
| **Em plugins, use QtPipelineEngine** | Nunca use AsyncPipelineEngine em plugins (bloqueia UI) |

## 🔄 Reuso de Steps e Tasks entre Plugins

Steps e tasks DEVEM ser **genéricos, independentes e reutilizáveis**. Um step NUNCA sabe qual step vem antes ou depois. Cada step:
1. Le do `ExecutionContext` os dados que precisa
2. Executa sua task
3. Escreve no `ExecutionContext` o resultado que produziu

O `PipelineRunner` (ou `QtPipelineEngine`) orquestra a sequencia.

### Fluxo Correto: Steps Independentes

```
Plugin prepara context inicial
       ↓
PipelineRunner executa steps em sequencia
       ↓
Step 1 (ex: LasTilerStep)
  → Le: file_path, output_dir, pontos_por_parte
  → Produz: split_result = {"arquivos": [...], "n_partes": N, ...}
       ↓
Step 2 (ex: IdwInterpolatorStep)
  → Le: split_result["arquivos"] (NAO sabe quem produziu)
  → Le: output_path, target_bands, resol_m, ...
  → Produz: idw_result = {"grid": {...}, "arquivos_gerados": [...], ...}
       ↓
Plugin recebe context final via callback finished_ok
```

### Regra: Steps em `core/papeline/step/` são PÚBLICOS

Steps registrados em `core/papeline/step/__init__.py` podem ser importados por QUALQUER plugin:

```python
from core.papeline.step.LasTilerStep import LasTilerStep

# Reutilizado no pipeline do IDW — o LasTilerStep NAO sabe que o IDW existe
runner = PipelineRunner(
    steps=[LasTilerStep(), IdwInterpolatorStep()],
    context={...},
)
```

### Regra: Tasks em `core/papeline/task/` são PÚBLICAS

Tasks registradas em `core/papeline/task/__init__.py` podem ser usadas por qualquer step:

```python
from core.papeline.task.LasTilerTask import LasTilerTask

# Usado tanto pelo LasTilerStep quanto por outros steps que precisam dividir LAS
task = LasTilerTask(file_path=path, output_dir=out, pontos_por_parte=pts)
```

### Padrão: Step extrai params do contexto, Task recebe params individuais

```python
# ❌ ERRADO — Task recebe dict bruto
class MinhaTask(BaseTask):
    def __init__(self, context: dict):
        self._file_path = context["file_path"]  # fragil, sem defaults

# ✅ CORRETO — Task recebe parametros nomeados
class MinhaTask(BaseTask):
    def __init__(self, file_path: str, output_dir: str = ""):
        self._file_path = file_path
        self._output_dir = output_dir
```

```python
# ❌ ERRADO — Step usa logger proprio no __init__
class MeuStep(BaseStep):
    def __init__(self):
        self._logger = BaseUtil._get_logger(...)  # sem tool_key do contexto

# ✅ CORRETO — Step usa get_logger(context)
class MeuStep(BaseStep):
    def should_run(self, context):
        logger = self.get_logger(context)  # tool_key extraida do contexto
```

### Padrão: Step busca dados de MULTIPLAS fontes no contexto

Um step NAO deve assumir que um step anterior produziu uma chave especifica.
Deve buscar dados de forma flexivel:

```python
class MeuStep(BaseStep):
    def _obter_arquivos(self, context) -> list[str]:
        # 1. Tenta resultado de step anterior
        resultado = context.get("resultado_anterior", {})
        if resultado.get("arquivos"):
            return resultado["arquivos"]
        # 2. Tenta chave direta no contexto
        if context.get("arquivos"):
            return context["arquivos"]
        # 3. Tenta pasta como fallback
        pasta = context.get("pasta", "")
        if pasta:
            return glob.glob(os.path.join(pasta, "*.las"))
        return []
```

### Exemplo: Pipeline IDW (2 steps independentes)

```python
# Plugin prepara o context com TUDO que ambos steps precisam
tiles_dir = os.path.join(
    os.path.dirname(output_path),
    os.path.splitext(os.path.basename(las_path))[0]
)

runner = PipelineRunner(
    steps=[LasTilerStep(), IdwInterpolatorStep()],
    context={
        # LasTilerStep le (divide o LAS):
        "file_path": "/dados/nuvem.las",
        "output_dir": tiles_dir,
        "pontos_por_parte": 5_000_000,
        # IdwInterpolatorStep le (interpola a pasta):
        "input_dir": tiles_dir,
        "output_path": "/dados/raster.tif",
        "target_bands": {"r": True, "g": True, "b": True, "z": False},
        "merge_bands": True,
        "resol_m": 0.01,
        "idw_k": 5,
        "idw_power": 2.0,
        "idw_raio_max": 0.5,
        "idw_overlap": 3.0,
        "crs_str": "EPSG:31982",
        "eliminar_tiles": True,
        "salvar_las": False,
        # Ambos usam:
        "tool_key": ToolKey.IDW_INTERPOLATOR.value,
    },
    parent=self,
)
# LasTilerStep produz: context["split_result"] = {"arquivos": [...], ...}
# IdwInterpolatorStep le: context["input_dir"] (pasta com .las)
# IdwInterpolatorStep produz: context["idw_result"] = {...}
```

### Lista de Steps/Tasks Públicos

| Step | Task | Proposito | Produz no Context |
|------|------|-----------|-------------------|
| `LasTilerStep` | `LasTilerTask` | Divide LAS/LAZ em partes | `split_result` |
| `LasCheckStep` | `LasCheckTask` | Valida arquivos LAS | `check_result` |
| `LasBlackFilterStep` | `LasBlackFilterTask` | Filtra pontos pretos | `filter_result` |
| `DoclingConvertStep` | `DoclingPipelineTask` | Converte documentos | `docling_result` |
| `MrkLoadDataStep` | `MrkSinglePipelineTask` | Carrega dados MRK | `mrk_data` |
| `MrkProcessStep` | — | Processa MRK contra dados | `mrk_result` |

## ✅ Checklist ao criar nova Pipeline

- [ ] Criei as tasks em `core/papeline/task/` herdando de `BaseTask`?
- [ ] Criei os steps em `core/papeline/step/` herdando de `BaseStep`?
- [ ] Atualizei os `__init__.py` correspondentes?
- [ ] Usei `super().__init__(description=...)` nas tasks?
- [ ] Task recebe parametros nomeados (NAO dict bruto)?
- [ ] Step usa `get_logger(context)` (NAO logger proprio)?
- [ ] Step NAO sabe qual step vem antes ou depois?
- [ ] Step busca dados de multiplas fontes no contexto (fallback)?
- [ ] O `on_success` atualiza o `ExecutionContext` com os resultados?
- [ ] Tratei exceções dentro de `_run()` retornando `False`?
- [ ] Ja existe um step/task em `core/papeline/step/` ou `core/papeline/task/` que faz o que preciso? Reutilize!

## 🔗 Referências

- Documentação de análise: `docs/implementacoes/analise_sistema_pipeline_assincrono.md`
- Contratos do sistema: `docs/skills/SKILL_PLUGIN_CONTRACT.md`
- Catálogo de steps/tasks: `core/papeline/step/__init__.py` e `core/papeline/task/__init__.py`
