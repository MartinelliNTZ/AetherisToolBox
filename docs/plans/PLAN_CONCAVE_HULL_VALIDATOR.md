# Plano de Ação: ConcaveHullValidatorPlugin

> **Ferramenta:** Validação de Envoltória Côncava com detecção de "escada"
> **Baseada em:** `docs/implementacoes/EST3.PY` (bloco `# ── VALIDACAO CONCAVE HULL`, linhas ~260–350)
> **Expansão:** Aceita LAS/LAZ + vetores de pontos (SHP, GPKG, KML, CSV, GeoJSON)
> **Prioridade:** Alta

---

## 📋 Visão Geral

Criar um plugin que gera `concave_hull` a partir de nuvens de pontos (LAS/LAZ) ou vetores de pontos (SHP, GPKG, KML, CSV, GeoJSON), com validação iterativa e detecção automática de "escada" (queda abrupta de área).

### Função Alvo (do EST3)

```
Amostra 100k pontos → Gera concave hull com ratio decrescente (0.10 passo 0.01)
→ Detecta "escada" quando queda de área > 12%
→ Suaviza polígono com buffer(20).buffer(-20)
→ Salva GPKGs de cada iteração
→ Exporta JSON com resultados
```

### Expansão Requerida

| Fonte | Original (EST3) | Novo Plugin |
|-------|-----------------|-------------|
| LAS/LAZ | ✅ Sim | ✅ Sim |
| SHP | ❌ Não | ✅ Sim |
| GPKG | ❌ Não | ✅ Sim |
| KML | ❌ Não | ✅ Sim |
| CSV (x,y) | ❌ Não | ✅ Sim |
| GeoJSON | ❌ Não | ✅ Sim |

---

## 🧱 Estrutura de Arquivos

```
plugins/concave_hull_validator/
├── __init__.py
├── ConcaveHullValidatorPlugin.py      # Widget principal (herda BasePlugin)
├── ConcaveHullValidatorStep.py        # Step do pipeline (herda BaseStep)
├── ConcaveHullValidatorTask.py        # Task opcional (herda BaseTask)
└── ConcaveHullValidatorUtil.py        # Lógica de leitura de fontes + concave hull
```

---

## 📦 Dependências

| Pacote | Uso | Já instalado? |
|--------|-----|---------------|
| `laspy` | Leitura de LAS/LAZ | ✅ Sim (usado em LasCheckPlugin) |
| `shapely` | `concave_hull`, `MultiPoint`, `buffer` | ✅ Sim |
| `fiona` | Escrita GPKG | ✅ Sim |
| `geopandas` | Leitura SHP/GPKG/KML/GeoJSON | ✅ Sim (usado em VectorLayerSource) |
| `numpy` | Amostragem, arrays | ✅ Sim |
| `rasterio` | (não necessário para este plugin) | — |

---

## 🏗 Passo 1: ToolKey + ToolRegistry

### `core/enum/ToolKey.py` — Adicionar:

```python
CONCAVE_HULL = "ConcaveHull"
```

### `core/config/ToolRegistry.py` — Adicionar entrada:

```python
ToolKey.CONCAVE_HULL.value: Tool(
    name=ToolKey.CONCAVE_HULL.value,
    title="Envoltória Côncava",
    widget_factory=_make_factory(
        "plugins.concave_hull_validator.ConcaveHullValidatorPlugin",
        "ConcaveHullValidatorPlugin",
    ),
    tooltip="Gera envoltória côncava de nuvens LAS/LAZ ou vetores de pontos com validação iterativa",
    tool_type=ToolType.VECTOR,
    category=CategoryTool.CENTRAL,
    show_in_toolbar=True,
),
```

---

## 🏗 Passo 2: ConcaveHullValidatorUtil — Lógica Central

**Arquivo:** `plugins/concave_hull_validator/ConcaveHullValidatorUtil.py`

### Responsabilidades

1. **Leitura de fontes** — método unificado que detecta extensão e extrai coordenadas (x, y):
   - `.las` / `.laz` → `laspy.read()` → `(las.x, las.y)`
   - `.shp` / `.gpkg` / `.kml` / `.geojson` → `geopandas.read_file()` → geometria de ponto
   - `.csv` → `pandas.read_csv()` → colunas x, y configuráveis

2. **Amostragem** — `max(1, n_pontos // N_AMOSTRAS)` para reduzir para ~100k pontos

3. **Geração iterativa do concave hull** — loop com ratio decrescente

4. **Detecção de escada** — queda de área > LIMIAR_ESCADA (12%)

5. **Suavização** — `buffer(SUAVISACAO).buffer(-SUAVISACAO)`

6. **Exportação** — GPKG por iteração + JSON final

### API Pública

```python
class ConcaveHullValidatorUtil(BaseUtil):
    @staticmethod
    def extract_points(path: str, tool_key: str) -> tuple[np.ndarray, np.ndarray, dict]
        """Extrai coordenadas (x, y) de qualquer fonte suportada.
        Retorna (x, y, metadata) onde metadata contém info da fonte."""

    @staticmethod
    def validate_hull(
        x: np.ndarray,
        y: np.ndarray,
        output_dir: str,
        *,
        ratio_inicial: float = 0.10,
        ratio_step: float = 0.01,
        limiar_escada: float = 12.0,
        suavisacao: float = 20.0,
        n_amostras: int = 100_000,
        crs: str = "EPSG:31982",
        tool_key: str = "Untraceable",
        progress_callback: callable = None,
    ) -> dict
        """Executa validação completa e retorna dict com resultados."""
```

### Parâmetros do `validate_hull`

| Parâmetro | Default | Descrição |
|-----------|---------|-----------|
| `ratio_inicial` | 0.10 | Ratio inicial do concave hull |
| `ratio_step` | 0.01 | Decremento do ratio por iteração |
| `limiar_escada` | 12.0% | Queda de área que dispara detecção de escada |
| `suavisacao` | 20 m | Buffer de suavização pós-hull |
| `n_amostras` | 100.000 | Pontos usados para o hull |
| `crs` | EPSG:31982 | CRS para exportação GPKG |
| `progress_callback` | None | Callable(stage_idx, total_stages, message) |

### Retorno do `validate_hull`

```python
{
    "ratio_ideal": 0.08,
    "area_hull_m2": 12345.67,
    "area_suavizada_m2": 12000.00,
    "encontrou_escada": True,
    "ratio_escada": 0.06,
    "queda_escada_pct": 15.3,
    "n_pontos_usados": 100000,
    "n_pontos_total": 5000000,
    "fonte": "las",
    "arquivo_origem": "c:/dados.las",
    "gpkg_final": "c:/output/limite_concave_r0.08_suavizado.gpkg",
    "gpkg_iteracoes": ["c:/output/concave_r0.100.gpkg", ...],
    "resultados_iteracoes": [
        {"ratio": 0.10, "area_m2": 15000.0, "porcentagem": 100.0, "queda_porcentagem": 0.0},
        {"ratio": 0.09, "area_m2": 14000.0, "porcentagem": 93.3, "queda_porcentagem": 6.7},
        ...
    ],
    "json_path": "c:/output/resultado_concave_hull.json",
}
```

---

## 🏗 Passo 3: ConcaveHullValidatorStep — Step do Pipeline

**Arquivo:** `plugins/concave_hull_validator/ConcaveHullValidatorStep.py`

### Comportamento

```python
class ConcaveHullValidatorStep(BaseStep):
    def name(self) -> str: return "ConcaveHullValidatorStep"

    def should_run(self, context) -> bool:
        return bool(context.get("file_path"))

    def run_inline(self, context) -> dict:
        # 1. Extrai pontos da fonte (LAS ou vetor)
        # 2. Executa validate_hull()
        # 3. Retorna resultados no context
```

### Context (entrada)

| Chave | Tipo | Descrição |
|-------|------|-----------|
| `file_path` | str | Caminho do arquivo de entrada |
| `ratio_inicial` | float | Ratio inicial |
| `ratio_step` | float | Decremento |
| `limiar_escada` | float | % queda para detectar escada |
| `suavisacao` | float | Buffer de suavização |
| `n_amostras` | int | Pontos para amostragem |
| `crs` | str | CRS de saída |
| `output_dir` | str | Diretório de saída |
| `tool_key` | str | Chave da ferramenta |

### Context (saída)

| Chave | Tipo | Descrição |
|-------|------|-----------|
| `hull_result` | dict | Resultado completo do validate_hull() |
| `hull_summary` | dict | Resumo para exibição no GridLabel |

---

## 🏗 Passo 4: ConcaveHullValidatorPlugin — Widget Principal

**Arquivo:** `plugins/concave_hull_validator/ConcaveHullValidatorPlugin.py`

### UI Layout

```
┌─────────────────────────────────────────────┐
│  PluginPage (title="Envoltória Côncava")     │
│                                               │
│  ┌─ GroupPainel "Arquivo de Entrada" ──────┐ │
│  │  SelectorGrid:                           │ │
│  │    "Arquivo de Pontos"                   │ │
│  │    file_filter: "LAS/LAZ (*.las *.laz);;  │ │
│  │      Shapefile (*.shp);; GeoPackage       │ │
│  │      (*.gpkg);; KML (*.kml);; CSV (*.csv);;│ │
│  │      GeoJSON (*.geojson)"                 │ │
│  │  SimpleLabel: info da fonte detectada     │ │
│  └───────────────────────────────────────────┘ │
│                                               │
│  ┌─ GroupPainel "Parâmetros" ───────────────┐ │
│  │  GridDoubleSpinBox:                       │ │
│  │    "ratio_inicial": 0.10 (step 0.01)     │ │
│  │    "ratio_step":    0.01 (step 0.001)    │ │
│  │    "limiar_escada": 12.0 (step 0.5)      │ │
│  │    "suavisacao":    20.0 (step 1.0)      │ │
│  │    "n_amostras":    100000 (step 10000)  │ │
│  └───────────────────────────────────────────┘ │
│                                               │
│  ┌─ GroupPainel "Resultados" ───────────────┐ │
│  │  GridLabel (columns=2):                   │ │
│  │    "fonte":        "Fonte"               │ │
│  │    "n_pontos":     "Total Pontos"        │ │
│  │    "n_amostrados": "Pontos Amostrados"   │ │
│  │    "ratio_ideal":  "Ratio Ideal"         │ │
│  │    "area_hull":    "Área Hull"           │ │
│  │    "area_suav":    "Área Suavizada"      │ │
│  │    "escada":       "Escada Detectada"    │ │
│  │    "status":       "Status"              │ │
│  └───────────────────────────────────────────┘ │
│                                               │
│  ┌─ ExecutionButtons ───────────────────────┐ │
│  │  [SALVAR JSON] [EXECUTAR]                │ │
│  └───────────────────────────────────────────┘ │
└─────────────────────────────────────────────┘
```

### Widgets Reutilizáveis Utilizados

| Widget | Arquivo | Uso |
|--------|---------|-----|
| `SelectorGrid` | `resources/widgets/SelectorGrid.py` | Seleção do arquivo de entrada |
| `GridDoubleSpinBox` | `resources/widgets/GridDoubleSpinBox.py` | Parâmetros numéricos |
| `GridLabel` | `resources/widgets/GridLabel.py` | Exibição de resultados |
| `ExecutionButtons` | `resources/widgets/ExecutionButtons.py` | Botões EXECUTAR + SALVAR JSON |
| `GroupPainel` | `resources/widgets/GroupPainel.py` | Containers de seção |
| `SimpleLabel` | `resources/widgets/SimpleLabel.py` | Info da fonte detectada |

### Fluxo de Execução

```
1. Usuário seleciona arquivo → _on_input_path_changed()
   ├── Detecta extensão (.las, .shp, .gpkg, .kml, .csv, .geojson)
   ├── Extrai metadados (n_pontos, CRS, tipo)
   └── Atualiza GridLabel com info da fonte

2. Usuário clica EXECUTAR → _on_executar()
   ├── Valida parâmetros
   ├── Cria PipelineRunner + ConcaveHullValidatorStep
   ├── Emite HUD stages
   └── Executa em background (QThread)

3. Pipeline completa → _on_done()
   ├── Atualiza GridLabel com resultados
   ├── Habilita botão SALVAR JSON
   └── Emite console_message

4. Usuário clica SALVAR JSON → _on_salvar_json()
   └── Salva JSON com resultados completos
```

---

## 🏗 Passo 5: ConcaveHullValidatorTask (Opcional)

**Arquivo:** `plugins/concave_hull_validator/ConcaveHullValidatorTask.py`

Se o processamento for pesado (LAS com milhões de pontos), criar Task separada para rodar em thread dedicada. Caso contrário, o Step `run_inline` já executa na QThread do PipelineRunner.

---

## 📊 Detecção de "Escada" — Algoritmo

```
area_ref = concave_hull(mp, ratio=RATIO_INICIAL)
area_anterior = area_ref

para cada ratio em [RATIO_INICIAL - RATIO_STEP, ..., 0]:
    hull = concave_hull(mp, ratio=ratio_atual)
    area = hull.area
    queda_pct = ((area_anterior - area) / area_anterior) * 100
    
    se queda_pct > LIMIAR_ESCADA E ratio_atual < RATIO_INICIAL:
        ESCADA DETECTADA!
        ratio_ideal = ultimo_ratio_processado
        break
    
    area_anterior = area
    ultimo_ratio_processado = ratio_atual

se não encontrou escada:
    ratio_ideal = ultimo_ratio_processado

hull_suavizado = hull_final.buffer(SUAVISACAO).buffer(-SUAVISACAO)
```

---

## 🔧 Correções do EST3 Aplicáveis

| ID | Correção | Aplicação |
|----|----------|-----------|
| V2 | nodata=255 | Não se aplica (sem raster) |
| V5 | BIGTIFF=YES | Não se aplica (sem raster) |
| — | GPKG com CRS | Usar `fiona.open(..., crs=CRS)` para todos GPKGs de saída |

---

## ✅ Checklist de Implementação

### Fase 1 — Estrutura Base
- [ ] Criar diretório `plugins/concave_hull_validator/`
- [ ] Criar `plugins/concave_hull_validator/__init__.py`
- [ ] Adicionar `CONCAVE_HULL = "ConcaveHull"` em `core/enum/ToolKey.py`
- [ ] Registrar em `core/config/ToolRegistry.py` com `ToolType.VECTOR`

### Fase 2 — Lógica Central (Util)
- [ ] Criar `ConcaveHullValidatorUtil.py` com:
  - [ ] `extract_points()` — leitura de LAS/LAZ
  - [ ] `extract_points()` — leitura de SHP/GPKG/KML/GeoJSON (geopandas)
  - [ ] `extract_points()` — leitura de CSV (pandas)
  - [ ] `validate_hull()` — loop iterativo com detecção de escada
  - [ ] Suavização com `buffer(SUAVISACAO).buffer(-SUAVISACAO)`
  - [ ] Exportação GPKG por iteração
  - [ ] Geração do JSON de resultados

### Fase 3 — Step do Pipeline
- [ ] Criar `ConcaveHullValidatorStep.py`
  - [ ] `should_run()` — valida file_path
  - [ ] `run_inline()` — orquestra extração + validação
  - [ ] `on_success()` — mescla resultados no context

### Fase 4 — Plugin Widget
- [ ] Criar `ConcaveHullValidatorPlugin.py`
  - [ ] `_build_ui()` — SelectorGrid + GridDoubleSpinBox + GridLabel + ExecutionButtons
  - [ ] `_on_input_path_changed()` — detecta tipo de arquivo, extrai metadados
  - [ ] `_on_executar()` — cria PipelineRunner, executa em background
  - [ ] `_on_done()` / `_on_error()` — atualiza UI
  - [ ] `_on_salvar_json()` — exporta JSON
  - [ ] `load_prefs()` / `save_prefs()` — persistência

### Fase 5 — Validação e Testes
- [ ] Testar com arquivo LAS/LAZ
- [ ] Testar com Shapefile de pontos
- [ ] Testar com GeoPackage de pontos
- [ ] Testar com KML de pontos
- [ ] Testar com CSV (x, y)
- [ ] Testar detecção de escada (ratio baixo)
- [ ] Testar sem escada (ratio ideal = último)
- [ ] Verificar GPKGs de saída
- [ ] Verificar JSON de resultados
- [ ] Verificar logs em todos os pontos críticos

### Fase 6 — Documentação
- [ ] Atualizar `docs/implementacoes/FERRAMENTAS_EXTRAIDAS_EST3.md` (marcar como implementado)
- [ ] Documentar parâmetros e uso no plugin

---

## 🔗 Relação com Outras Ferramentas

```
LAS/LAZ / SHP / GPKG / KML / CSV / GeoJSON
    │
    └──► [3] ConcaveHullValidatorPlugin
            │
            ├──► GPKG do polígono suavizado (usado por RasterPolygonClipperPlugin)
            ├──► JSON com resultados das iterações
            └──► Área suavizada (usada por LasStatisticsPlugin para densidade real)
```

---

## ⚠️ Riscos e Mitigações

| Risco | Mitigação |
|-------|-----------|
| LAS muito grande (>100M pts) | Amostragem automática para 100k pontos |
| CSV sem colunas x/y identificáveis | SelectorGrid com campos extras para nome das colunas |
| KML sem pontos (linhas/polígonos) | Validar geometria: extrair apenas Point/ MultiPoint |
| CRS ausente no vetor | Usar CRS padrão (EPSG:31982) com aviso no log |
| `concave_hull` lento em muitos pontos | Amostragem + validação em 100k pontos (comprovado no EST3) |

---

> **Plano gerado em:** 23/06/2026
> **Baseado em:** EST3.PY v5, FERRAMENTAS_EXTRAIDAS_EST3.md, SKILL_CREATE_TOOL.md, SKILL_WIDGETS.md, agent.md