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

## ✅ Checklist ao criar nova Pipeline

- [ ] Criei as tasks em `core/papeline/task/` herdando de `BaseTask`?
- [ ] Criei os steps em `core/papeline/step/` herdando de `BaseStep`?
- [ ] Atualizei os `__init__.py` correspondentes?
- [ ] Usei `super().__init__(description=...)` nas tasks?
- [ ] O `on_success` atualiza o `ExecutionContext` com os resultados?
- [ ] Tratei exceções dentro de `_run()` retornando `False`?

## 🔗 Referências

- Documentação de análise: `docs/implementacoes/analise_sistema_pipeline_assincrono.md`
- Contratos do sistema: `docs/skills/SKILL_PLUGIN_CONTRACT.md`