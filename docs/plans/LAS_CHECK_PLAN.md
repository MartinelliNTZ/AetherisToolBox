# 🧾 Plano de Implementação — Ferramenta de Check em Nuvem de Pontos LAS/LAZ

## 📋 Análise do Plugin Existente (LasBlackFilter)

O plugin `LasBlackFilterPlugin` serviu como referência arquitetural. Ele demonstra:

- **Seleção de entrada**: `SelectorGrid` com `SimpleSelector` para arquivo LAS/LAZ
- **Detecção automática**: `textChanged` dispara `_carregar_las()` que preenche metadados
- **Pipeline em background**: `PipelineRunner` + `LasBlackFilterStep` em `QThread`
- **Progresso**: `SignalManager.progress_update` + HUD Modo 3 (stages)
- **Estatísticas**: `ProcessStatisticsUtil` para ETA e tempo decorrido
- **UI**: `PluginPage` + `ExecutionButtons` + `GroupPainel` + `GridLabel` + `GridDoubleSpinBox` + `GridCheckBox`
- **Preferências**: `load_prefs()` / `save_prefs()` via `self.preferences`

**Componentes que podem ser reusados diretamente:**
- ✅ `LasUtil.get_info()` — metadados básicos (point_count, has_rgb, dimension_names)
- ✅ `LasUtil.get_bounding_box()` — bounding box aproximada
- ✅ `LasUtil.get_rgb_arrays()` — arrays RGB para validação
- ✅ `PipelineRunner` + step — execução em background
- ✅ `BasePlugin` — logger, preferences, badge, ciclo de vida

**O que NÃO vamos replicar** (já existente no sistema):
- ❌ ProgressBar local → usar `SignalManager.progress_update` (ui_main já tem)
- ❌ Log em arquivo → usar `self.logger` + `SignalManager.console_message`
- ❌ HUD customizado → usar `SignalManager.hud_show/hud_hide/hud_update`

---

## 🎯 Escopo da Ferramenta — "LAS Quality Check"

A ferramenta executará uma bateria de verificações em uma nuvem de pontos LAS/LAZ e exibirá um relatório consolidado com status (✅ APROVADO / ⚠️ AVISO / ❌ FALHA) para cada check.

### Checks a implementar (v1)

| # | Check | Descrição | Critério | Fonte |
|---|-------|-----------|----------|-------|
| 1 | 📊 **Contagem de Pontos** | Verifica se há pontos suficientes | `> 0` | `LasUtil.get_point_count()` |
| 2 | 📦 **Bounding Box** | Verifica se a bbox tem dimensões válidas | `x_min < x_max`, `y_min < y_max`, `z_min < z_max` | `LasUtil.get_bounding_box()` |
| 3 | 🎨 **Bandas RGB** | Verifica presença de RGB | `has_rgb == True` | `LasUtil.has_rgb()` |
| 4 | 🏷️ **Classificação** | Verifica se há códigos de classificação LAS válidos (0–255) | range válido | `laspy` direto no step |
| 5 | 📐 **Coordenadas Zero** | Verifica se há pontos com X=0, Y=0, Z=0 simultâneos | percentual < 1% | `laspy` direto |
| 6 | 🔁 **Duplicatas (XY)** | Verifica se há pontos com coordenadas XY duplicadas | percentual < 0.1% | amostragem |
| 7 | 📏 **Gaps/Overlaps** | Verifica se há grandes gaps entre pontos | métrica de densidade | bounding box + point count |
| 8 | 💡 **Intensidade** | Verifica se há valores de intensidade válidos (0–65535) | range válido | acesso a `las.intensity` |

### Resultados

Cada check produz:
- `status`: `"pass"`, `"warning"`, `"fail"`
- `message`: descrição legível
- `detail`: valor numérico ou detalhe técnico
- `suggestion`: sugestão de ação (se aplicável)

O relatório consolidado é:
- Exibido em tempo real na UI via `GridLabel`
- Exibido completo no `ReadOnlyTextBrowser` como relatório detalhado
- Opcionalmente exportável para `.txt` ou `.json`

---

## 🔧 Widgets e Recursos Necessários

### Widgets Já Existentes (reutilizar)

| Widget | Uso |
|--------|-----|
| `SelectorGrid` | Seleção do arquivo LAS/LAZ de entrada |
| `GridLabel` | Exibir status de cada check (label + valor) |
| `GroupPainel` | Agrupar seções: Checks, Relatório, Config |
| `ExecutionButtons` | Botões EXECUTAR, EXPORTAR RELATÓRIO |
| `GridCheckBox` | Selecionar quais checks executar |
| `ReadOnlyTextBrowser` | Exibir relatório detalhado formatado |
| `PluginPage` | Container base do plugin |
| `SimpleSelector` | Caminho do arquivo de relatório de saída |
| `SimpleLabel` | Mensagens auxiliares, hints |

### Novos Widgets (criar em `resources/widgets/`)

**Nenhum novo widget necessário para v1.** Todo o relatório pode ser composto com widgets existentes:
- `GridLabel` para status compacto (label + valor pass/warning/fail)
- `ReadOnlyTextBrowser` para relatório detalhado
- `GridCheckBox` para seleção de checks

---

## 🏗 Estrutura do Plugin

### Diretório: `plugins/las_check/`

```
plugins/las_check/
├── __init__.py
└── LasCheckPlugin.py
```

### Arquivo Step (opcional, se usar PipelineRunner)

```
core/papeline/step/
└── LasCheckStep.py
```

---

## 🏗 Layout do Plugin (Contrato 18 — Título → Separator → ExecutionButtons → conteúdo)

```
┌─ PluginPage (title="LAS Quality Check") ───────────────────────┐
│ Header: [LAS Quality Check]                          [badge]   │
│ Separator                                                      │
│ ┌─ ExecutionButtons ──────────────────────────────────────────┐│
│ │ [EXECUTAR]         [EXPORTAR RELATÓRIO]                     ││
│ └─────────────────────────────────────────────────────────────┘│
│ ┌─ GroupPainel "Arquivo de Entrada" ──────────────────────────┐│
│ │ SelectorGrid: [Arquivo LAS/LAZ] [📂] [___________]          ││
│ │ GridLabel: [Pontos: 1.234.567] [RGB: Sim] [BBox: ok]       ││
│ └─────────────────────────────────────────────────────────────┘│
│ ┌─ GroupPainel "Checks" ──────────────────────────────────────┐│
│ │ GridCheckBox (8 itens, 2 colunas):                          ││
│ │ [x] Contagem de Pontos   [x] Bounding Box                  ││
│ │ [x] Bandas RGB           [x] Classificação                 ││
│ │ [x] Coordenadas Zero     [x] Duplicatas XY                 ││
│ │ [x] Gaps/Overlaps        [x] Intensidade                   ││
│ │ ─────────────────────────────────────────────────────────── ││
│ │ [SELECIONAR TODOS] [LIMPAR]                                 ││
│ └─────────────────────────────────────────────────────────────┘│
│ ┌─ GroupPainel "Resultados" ──────────────────────────────────┐│
│ │ GridLabel (8 linhas, 1 coluna):                             ││
│ │ ✅ Contagem de Pontos: 1.234.567 pontos                     ││
│ │ ✅ Bounding Box: X[200.0, 800.0] Y[300.0, 900.0]           ││
│ │ ⚠️ Bandas RGB: Ausentes                                    ││
│ │ ✅ Classificação: OK (códigos 2, 6, 9)                     ││
│ │ ❌ Coordenadas Zero: 23 pontos (0.002%)                     ││
│ │ ✅ Duplicatas XY: Nenhuma                                   ││
│ │ ✅ Gaps/Overlaps: Densidade OK                              ││
│ │ ✅ Intensidade: Range 0–1023 válido                         ││
│ └─────────────────────────────────────────────────────────────┘│
│ ┌─ ReadOnlyTextBrowser (relatório detalhado, colapsável) ─────┐│
│ │ [Relatório Detalhado ▼]                                     ││
│ │ === LAS Quality Check Report ===                            ││
│ │ File: /ponto/nuvem.las                                      ││
│ │ Date: 22/06/2026 17:00:00                                   ││
│ │ Status: 6 ✅ | 1 ⚠️ | 1 ❌                                  ││
│ │ ...                                                         ││
│ └─────────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────┘
```

---

## 📦 Fluxo de Dados

```
1. Usuário seleciona arquivo LAS/LAZ
       │
       ▼
2. _on_input_path_changed() → _carregar_las(path)
       │
       ▼
3. LasUtil.get_info() → preenche GridLabel (preview)
       │
       ▼
4. Usuário seleciona quais checks executar (GridCheckBox)
       │
       ▼
5. Usuário clica EXECUTAR
       │
       ▼
6. _on_executar() → cria PipelineRunner com LasCheckStep
       │
       ▼
7. LasCheckStep._run() → QThread:
   ├── 7.1 Contagem de Pontos (LasUtil.get_point_count)
   ├── 7.2 Bounding Box (LasUtil.get_bounding_box)
   ├── 7.3 Bandas RGB (LasUtil.has_rgb)
   ├── 7.4 Classificação (laspy direto)
   ├── 7.5 Coordenadas Zero (laspy: X==0 & Y==0 & Z==0)
   ├── 7.6 Duplicatas XY (amostragem numpy)
   ├── 7.7 Gaps/Overlaps (densidade por bbox)
   └── 7.8 Intensidade (laspy: min/max/valid)
       │
       ▼
8. finished_ok → _on_done(context)
   ├── Atualiza GridLabel com resultados
   ├── Popula ReadOnlyTextBrowser com relatório
   └── Habilita EXPORTAR RELATÓRIO
```

---

## 📝 Passos da Implementação

### Passo 1: Criar estrutura do plugin
- [ ] Criar `plugins/las_check/__init__.py`
- [ ] Criar `plugins/las_check/LasCheckPlugin.py`
  - [ ] Classe `LasCheckPlugin(BasePlugin)` com `tool_key=ToolKey.LAS_CHECK`
  - [ ] `_build_ui()` com layout completo (SelectorGrid, GridCheckBox, GridLabel, ExecutionButtons, ReadOnlyTextBrowser)
  - [ ] `load_prefs()` / `save_prefs()` — salvar checks selecionados, último path
  - [ ] `_carregar_las(path)` — carregar metadados e atualizar preview
  - [ ] `_on_executar()` — iniciar pipeline
  - [ ] `_on_done(context)` — exibir resultados
  - [ ] `_on_exportar_relatorio()` — salvar .txt ou .json
  - [ ] Logs obrigatórios em pontos críticos (init, load, exec start/done/error)

### Passo 2: Criar Step da Pipeline
- [ ] Criar `core/papeline/step/LasCheckStep.py`
  - [ ] Classe `LasCheckStep(BaseStep)` com método `_run(context)`
  - [ ] Implementar cada check como método privado
  - [ ] Emitir progresso via `SignalManager.progress_update` entre checks
  - [ ] Retornar dict com resultados no context

### Passo 3: Registrar no sistema
- [ ] Adicionar `LAS_CHECK = "LasCheck"` em `ToolKey`
- [ ] Registrar em `ToolRegistry._TOOLS`:
  ```python
  ToolKey.LAS_CHECK.value: Tool(
      name=ToolKey.LAS_CHECK.value,
      title="LAS Quality Check",
      widget_factory=_make_factory(
          "plugins.las_check.LasCheckPlugin", "LasCheckPlugin"
      ),
      tooltip="Valida e inspeciona nuvens de pontos LAS/LAZ",
      tool_type=ToolType.LAS,
      category=CategoryTool.CENTRAL,
      show_in_toolbar=True,
  ),
  ```

### Passo 4: Verificações finais
- [ ] Compilar com `py_compile`
- [ ] Verificar contratos (Contrato 1–25)
- [ ] Verificar imports mortos
- [ ] Nenhum `QProgressBar` ou `QTextBrowser` bruto criado no plugin
- [ ] Todos os `except` têm `as e` e logger
- [ ] Nenhum `QMessageBox` direto (só via `MessageBox`)
- [ ] Nenhum `QFileDialog` direto (só via `ExplorerUtils`)

---

## 📋 Checklist dos Checks Individuais

### Check 1 — Contagem de Pontos
```python
def _check_point_count(self, las) -> dict:
    n = las.header.point_count
    if n == 0:
        return {"status": "fail", "message": "Nenhum ponto encontrado"}
    elif n < 1000:
        return {"status": "warning", "message": f"Apenas {n:,} pontos (nuvem pequena)"}
    return {"status": "pass", "message": f"{n:,} pontos"}
```

### Check 2 — Bounding Box
```python
def _check_bbox(self, las) -> dict:
    # Lê amostra para obter bbox
    x, y, z = las.x, las.y, las.z
    x_min, x_max = float(np.min(x)), float(np.max(x))
    y_min, y_max = float(np.min(y)), float(np.max(y))
    z_min, z_max = float(np.min(z)), float(np.max(z))
    issues = []
    if x_min >= x_max: issues.append("X")
    if y_min >= y_max: issues.append("Y")
    if z_min >= z_max: issues.append("Z")
    if issues:
        return {"status": "fail", "message": f"BBox inválida nos eixos: {', '.join(issues)}"}
    return {"status": "pass", "message": f"X[{x_min:.1f}, {x_max:.1f}] Y[{y_min:.1f}, {y_max:.1f}] Z[{z_min:.1f}, {z_max:.1f}]"}
```

### Check 3 — Bandas RGB
```python
def _check_rgb(self, las) -> dict:
    has_rgb = hasattr(las, "red") and hasattr(las, "green") and hasattr(las, "blue")
    if not has_rgb:
        return {"status": "warning", "message": "LAS não possui bandas RGB"}
    return {"status": "pass", "message": "RGB presente"}
```

### Check 4 — Classificação
```python
def _check_classification(self, las) -> dict:
    if not hasattr(las, "classification"):
        return {"status": "warning", "message": "Sem campo de classificação"}
    classes = np.unique(las.classification)
    invalid = classes[(classes < 0) | (classes > 255)]
    if len(invalid) > 0:
        return {"status": "fail", "message": f"Códigos inválidos: {invalid.tolist()}"}
    return {"status": "pass", "message": f"Códigos válidos: {sorted(classes[classes > 0]).tolist()}"}
```

### Check 5 — Coordenadas Zero
```python
def _check_zero_coords(self, las) -> dict:
    n_total = len(las.points)
    mask_zero = (las.x == 0) & (las.y == 0) & (las.z == 0)
    n_zero = int(np.sum(mask_zero))
    pct = (n_zero / n_total * 100) if n_total > 0 else 0
    if pct >= 1.0:
        return {"status": "fail", "message": f"{n_zero:,} pontos ({(pct):.3f}%) com X=Y=Z=0"}
    elif pct > 0:
        return {"status": "warning", "message": f"{n_zero:,} pontos ({(pct):.3f}%) com X=Y=Z=0"}
    return {"status": "pass", "message": "Nenhum ponto com coordenadas zero"}
```

### Check 6 — Duplicatas XY (amostragem)
```python
def _check_duplicates(self, las) -> dict:
    # Se muito grande, amostra
    n_total = len(las.points)
    sample = min(n_total, 50000)
    idx = np.random.choice(n_total, sample, replace=False) if n_total > sample else slice(None)
    coords = np.column_stack((las.x[idx], las.y[idx]))
    _, counts = np.unique(coords, axis=0, return_counts=True)
    dup = int(np.sum(counts > 1))
    pct = (dup / sample * 100) if sample > 0 else 0
    if pct > 0.1:
        return {"status": "fail", "message": f"{dup:,} duplicatas em amostra ({pct:.3f}%)"}
    elif dup > 0:
        return {"status": "warning", "message": f"{dup:,} duplicatas em amostra ({pct:.3f}%)"}
    return {"status": "pass", "message": "Nenhuma duplicata detectada"}
```

### Check 7 — Densidade / Gaps
```python
def _check_density(self, las) -> dict:
    n_total = len(las.points)
    x_min, x_max = float(np.min(las.x)), float(np.max(las.x))
    y_min, y_max = float(np.min(las.y)), float(np.max(las.y))
    area = (x_max - x_min) * (y_max - y_min)
    if area <= 0:
        return {"status": "warning", "message": "Área planar zero (pontos coplanares?)"}
    density = n_total / area
    return {"status": "pass", "message": f"Densidade: {density:.2f} pts/m²"}
```

### Check 8 — Intensidade
```python
def _check_intensity(self, las) -> dict:
    if not hasattr(las, "intensity"):
        return {"status": "warning", "message": "Sem campo de intensidade"}
    i_min, i_max = int(np.min(las.intensity)), int(np.max(las.intensity))
    if i_min < 0 or i_max > 65535:
        return {"status": "fail", "message": f"Intensidade fora do range: [{i_min}, {i_max}]"}
    return {"status": "pass", "message": f"Range [{i_min}, {i_max}] (válido)"}
```

---

## 📋 Logs Obrigatórios (dev) + Console (user)

| Momento | Log (LogUtils) | Console (SignalManager) |
|---------|----------------|------------------------|
| Init | `"LASCHECK_READY"` | — |
| Load LAS ok | `"LASCHECK_LAS_LOADED: {path}, {n} pts"` | `"[LasCheck] Carregado: {path}"` |
| Load LAS erro | `"LASCHECK_LAS_LOAD_ERR: {error}"` | `"[LasCheck] Erro ao carregar LAS"` |
| Exec start | `"LASCHECK_EXEC_START: {path}, {n} checks"` | `"[LasCheck] Iniciando {n} checks..."` |
| Each check | `"LASCHECK_CHECK_DONE: {check_name} → {status}"` | — |
| Exec done | `"LASCHECK_EXEC_DONE: {pass_count} pass, {warn_count} warn, {fail_count} fail"` | `"[LasCheck] Checks concluídos! {pass_count} ✅, {warn_count} ⚠️, {fail_count} ❌"` |
| Exec error | `"LASCHECK_EXEC_ERR: {error}"` | `"[LasCheck] Erro durante check: {error}"` |
| Export report | `"LASCHECK_EXPORT: {path}"` | `"[LasCheck] Relatório exportado: {path}"` |

---

## 🖥️ Progresso (via SignalManager)

```python
# Durante execução — 8 stages (1 por check)
SignalManager.instance().hud_show.emit({
    "message": "Verificando nuvem de pontos...",
    "stages": [estimated_seconds, 8],
})
# A cada check concluído
SignalManager.instance().hud_stage_done.emit(stage_index)
SignalManager.instance().progress_update.emit(progress_pct)
# Ao final
SignalManager.instance().hud_hide.emit()
```

---

## 💾 Preferências Salvas

```python
self.preferences = {
    "last_path": "c:/dados/nuvem.las",
    "checks_enabled": {
        "point_count": True,
        "bbox": True,
        "rgb": True,
        "classification": True,
        "zero_coords": True,
        "duplicates": True,
        "density": True,
        "intensity": True,
    },
}
```

---

## 🔮 Possíveis Extensões Futuras (v2+)

- [ ] **Relatório em PDF** — exportar resultados formatados
- [ ] **Check de projeção** — validar CRS/SRS do LAS
- [ ] **Check de metadados** — validar header fields (version, point format, etc.)
- [ ] **Check de bordas** — detectar pontos isolados nas bordas
- [ ] **Suporte a múltiplos arquivos** — batch check em lote
- [ ] **Gráfico de distribuição** — histograma de intensidade/classificação
- [ ] **Comparação entre nuvens** — diff entre duas nuvens

---

## ✅ Checklist Final de Verificação

- [ ] ToolKey adicionado em `core/enum/ToolKey.py`
- [ ] Tool registrada em `core/config/ToolRegistry.py`
- [ ] Plugin herda de `BasePlugin` com `tool_key`, `title`
- [ ] `_build_ui()` segue Contrato 18 (Título → Separator → ExecutionButtons → conteúdo)
- [ ] `load_prefs()` / `save_prefs()` implementados
- [ ] Uso de widgets de `resources/widgets/` (nenhum `QWidget` bruto)
- [ ] Uso de `ExecutionButtons` (nenhum `QPushButton` ou `QHBoxLayout` manual)
- [ ] Nenhum `QMessageBox` direto (só `MessageBox`)
- [ ] Nenhum `QFileDialog` direto (só `ExplorerUtils`)
- [ ] Nenhum `QProgressBar` ou `QTextBrowser` bruto no plugin
- [ ] Todos `except` têm `as e` + logger
- [ ] Logs nos pontos críticos (init, load, exec start/done/error)
- [ ] Console messages via `SignalManager.console_message`
- [ ] Progresso via `SignalManager.progress_update`
- [ ] Pipeline via `PipelineRunner` + step em `QThread`
- [ ] Documentação atualizada se houver mudança funcional (Contrato 12)