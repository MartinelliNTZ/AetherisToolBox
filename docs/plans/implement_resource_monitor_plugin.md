# 📊 Plano de Implementação — Resource Monitor Plugin

## 1. Visão Geral

**Objetivo:** Criar uma ferramenta no Aetheris ToolBox para monitoramento em tempo real de recursos do sistema:
- **RAM** — uso total, disponível, percentual, por processo
- **CPU** — uso percentual por core, total, por processo, temperatura
- **GPU** — uso percentual, memória, temperatura (NVIDIA e AMD via APIs)
- **Armazenamento** — uso por disco, leitura/escrita, espaço livre

**Chave da ferramenta:** `ResourceMonitor`

---

## 2. Sistema Existente — Contexto Completo

### 2.1 Arquitetura Geral

O Aetheris ToolBox é um sistema modular baseado em plugins. Cada ferramenta é um **plugin** independente que herda de `BasePlugin` e se registra no `ToolRegistry`. 

```
┌─────────────────────────────────────────────┐
│                 MainWindow                   │
│  ┌─────────────────────────────────────────┐ │
│  │              AppBar                     │ │
│  ├─────────────────────────────────────────┤ │
│  │          MenuManager (MenuBar)          │ │
│  ├─────────────────────────────────────────┤ │
│  │         MenuManager (Toolbar)           │ │
│  ├─────────────────────────────────────────┤ │
│  │      WorkspaceManager (QSplitter)       │ │
│  │  ┌──────────────┬──────────────────┐    │ │
│  │  │   Central    │    Side          │    │ │
│  │  │  Workspace   │   Workspace      │    │ │
│  │  └──────────────┴──────────────────┘    │ │
│  ├─────────────────────────────────────────┤ │
│  │            ProgressBar                  │ │
│  └─────────────────────────────────────────┘ │
└─────────────────────────────────────────────┘
```

### 2.2 Fluxo de Criação de um Plugin

```
1. Adicionar chave em core/enum/ToolKey.py
2. Criar diretório plugins/resource_monitor/
3. Criar classe herdando de BasePlugin
4. Implementar _build_ui(), load_prefs(), save_prefs()
5. Registrar em core/config/ToolRegistry.py com Tool()
6. (Opcional) Adicionar ícone em resources/icons/
```

### 2.3 Componentes Relevantes Existentes

| Componente | Path | Função |
|---|---|---|
| `BasePlugin` | `plugins/BasePlugin.py` | Classe base: fornece `self.logger`, `self.preferences`, `self.statistics`, `self.main_layout`, `self.page` |
| `PluginPage` | `resources/widgets/PluginPage.py` | Layout padrão: header com título, badge de status (PRONTA/RUNNING/ERROR), separator |
| `ExecutionButtons` | `resources/widgets/ExecutionButtons.py` | Botões padronizados: primary, secondary, danger, ghost |
| `GroupPainel` | `resources/widgets/GroupPainel.py` | Container agrupado com borda e título |
| `GridGroupPainel` | `resources/widgets/GridGroupPainel.py` | Grid horizontal de GroupPaineis lado a lado |
| `GridLabel` | `resources/widgets/GridLabel.py` | Label + valor em grid |
| `GridLineEdit` | `resources/widgets/GridLineEdit.py` | Label + campo de texto |
| `GridCheckBox` | `resources/widgets/GridCheckBox.py` | Grid de checkboxes com labels |
| `GridDoubleSpinBox` | `resources/widgets/GridDoubleSpinBox.py` | Label + spinbox numérico |
| `SimpleLabel` | `resources/widgets/SimpleLabel.py` | Label estilizado |
| `SectionPanel` | `resources/widgets/SectionPanel.py` | Painel expansível com título |
| `SelectorGrid` | `resources/widgets/SelectorGrid.py` | Grid de seletores |
| `ItemTable` | `resources/widgets/ItemTable.py` | Tabela de itens |
| `ReadOnlyTextBrowser` | `resources/widgets/ReadOnlyTextBrowser.py` | Texto readonly com suporte HTML |
| `AppStyles` | `resources/styles/AppStyles.py` | Estilos e cores centralizados |
| `ColorProvider` | `utils/ColorProvider.py` | Cores consistentes por nível/ferramenta/classe |

### 2.4 Utilitários Disponíveis

| Utilitário | Path | Função |
|---|---|---|
| `MessageBox` | `utils/MessageBox.py` | **Única** forma de exibir mensagens ao usuário (Contrato 1) |
| `ExplorerUtils` | `utils/ExplorerUtils.py` | **Única** forma de usar QFileDialog (Contrato 17) |
| `Preferences` | `utils/Preferences.py` | Persistência de preferências por tool_key |
| `LogUtils` | `core/config/LogUtils.py` | Logging estruturado: `self.logger.info/warning/error(...)` |
| `FormatUtils` | `utils/FormatUtils.py` | Formatação de datas e tamanhos (Contrato 22) |
| `JsonUtil` | `utils/JsonUtil.py` | Criação/leitura de JSONs temporários (Contrato 21) |
| `ColorProvider` | `utils/ColorProvider.py` | Cores por nível, ferramenta e classe |
| `ProcessStatisticsUtil` | `utils/ProcessStatisticsUtil.py` | Monitor de tempo/ETA para operações longas |

### 2.5 Sistema de Sinais (SignalManager)

```python
# Sinais disponíveis para uso (SignalCatalog.py):
SignalManager.instance().tool_opened.emit("ResourceMonitor")
SignalManager.instance().tool_closed.emit("ResourceMonitor")
SignalManager.instance().console_message.emit("texto")          # Mensagem no ConsolePlugin
SignalManager.instance().progress_update.emit(50.0)             # ProgressBar 0-100%
SignalManager.instance().progress_reset.emit()                  # Reset barra
SignalManager.instance().hud_show.emit({"message": "..."})     # HUD Loader
SignalManager.instance().hud_update.emit({"message": "..."})   # Atualizar HUD
SignalManager.instance().hud_hide.emit()                        # Esconder HUD
SignalManager.instance().execution_started.emit("tool_key")     # Início execução
SignalManager.instance().execution_finished.emit("tool_key")    # Fim execução
SignalManager.instance().execution_cancelled.emit("tool_key")   # Cancelamento
```

### 2.6 Contratos Relevantes (devem ser seguidos)

- **Contrato 1**: `QMessageBox` proibido → usar `MessageBox`
- **Contrato 2**: `except` SEMPRE com `as e` + logger
- **Contrato 3**: Usar `LogUtils`, nunca `print()`
- **Contrato 4**: `self.preferences` vem do BasePlugin
- **Contrato 6**: Plugin herda de `BasePlugin`, implementa `load_prefs()` e `save_prefs()`
- **Contrato 7**: Comunicação via `SignalManager` — plugins não se importam
- **Contrato 9**: Código morto proibido
- **Contrato 11**: Widgets de `resources/widgets/` são obrigatórios; NUNCA importar `PySide6.QtWidgets` diretamente sem verificar
- **Contrato 12**: Documentação deve ser atualizada
- **Contrato 17**: `QFileDialog` só via `ExplorerUtils`
- **Contrato 18**: Usar `ExecutionButtons` para botões de ação, nunca `QHBoxLayout` manual
- **Contrato 19**: Estilos só via `AppStyles`
- **Contrato 20**: Progresso via `SignalManager`, nunca `QProgressBar` interno
- **Contrato 23**: Utilitários compartilhados são obrigatórios
- **Contrato 24**: `SignalManager` é para comunicação entre componentes, não para mudanças internas
- **Contrato 25**: I/O vetorial/raster via utils especializados
- **Contrato 26**: ToolKey SEMPRE via `ToolKey.XXX.value`

### 2.7 Estrutura de Diretórios do Plugin

```
plugins/resource_monitor/
├── __init__.py
├── ResourceMonitorPlugin.py          # Plugin principal (UI + lógica)
├── collector/
│   ├── __init__.py
│   ├── BaseCollector.py              # Classe abstrata para coletores
│   ├── RamCollector.py               # Coleta dados de RAM
│   ├── CpuCollector.py               # Coleta dados de CPU
│   ├── GpuCollector.py               # Coleta dados de GPU
│   └── DiskCollector.py              # Coleta dados de disco
└── widgets/
    ├── __init__.py
    ├── ResourceGaugeWidget.py        # Widget gauge circular/barra
    ├── ResourceTimelineWidget.py     # Widget gráfico de linha temporal
    └── ProcessTableWidget.py         # Tabela de processos
```

---

## 3. Plano de Implementação Detalhado

### 3.1 Fase 1 — Infraestrutura Básica

#### 3.1.1 Registrar ToolKey

**Arquivo:** `core/enum/ToolKey.py`

Adicionar ao enum:
```python
RESOURCE_MONITOR = "ResourceMonitor"
```

#### 3.1.2 Registrar no ToolRegistry

**Arquivo:** `core/config/ToolRegistry.py`

Adicionar entrada em `_TOOLS`:
```python
ToolKey.RESOURCE_MONITOR.value: Tool(
    name=ToolKey.RESOURCE_MONITOR.value,
    title="Monitor de Recursos",
    widget_factory=_make_factory(
        "plugins.resource_monitor.ResourceMonitorPlugin",
        "ResourceMonitorPlugin",
    ),
    tooltip="Monitora uso de RAM, CPU, GPU e armazenamento do sistema",
    tool_type=ToolType.SYSTEM,
    category=CategoryTool.CENTRAL,
    show_in_toolbar=True,
),
```

#### 3.1.3 Adicionar ToolType (se necessário)

Caso não exista ToolType apropriado, pode-se adicionar `MONITOR = "Monitor"` em `core/enum/ToolType.py`, ou usar `ToolType.SYSTEM` que já cobre ferramentas de sistema.

### 3.2 Fase 2 — Coletores de Dados

#### 3.2.1 `BaseCollector` (classe abstrata)

```python
# plugins/resource_monitor/collector/BaseCollector.py

class BaseCollector:
    """Classe base para coletores de dados do sistema."""
    
    def collect(self) -> dict:
        """Coleta dados atuais. Retorna dict com chaves padronizadas."""
        raise NotImplementedError
    
    @property
    def name(self) -> str:
        """Nome amigável do coletor."""
        raise NotImplementedError
```

#### 3.2.2 `RamCollector`

**Dependências:** `psutil` (precisa ser adicionado ao `requirements.txt` conforme Contrato 8)

**Dados coletados:**
- `total_bytes` — RAM total
- `available_bytes` — RAM disponível
- `used_bytes` — RAM usada
- `percent` — percentual de uso
- `processes` — lista de top processos por RAM

```python
import psutil

class RamCollector(BaseCollector):
    def collect(self) -> dict:
        mem = psutil.virtual_memory()
        return {
            "total": mem.total,
            "available": mem.available,
            "used": mem.used,
            "percent": mem.percent,
            "processes": [
                {"pid": p.info["pid"], "name": p.info["name"], 
                 "memory": p.info["memory_info"].rss}
                for p in psutil.process_iter(["pid", "name", "memory_info"])
                if p.info["memory_info"] and p.info["memory_info"].rss > 0
            ][:20]  # top 20
        }
```

#### 3.2.3 `CpuCollector`

**Dados coletados:**
- `percent` — uso total da CPU
- `per_cpu` — uso por core (lista de percentuais)
- `count` — número de cores lógicos e físicos
- `frequency_current`, `frequency_min`, `frequency_max` — frequências em MHz
- `temperature` — temperatura (se disponível, via `psutil.sensors_temperatures`)

```python
import psutil

class CpuCollector(BaseCollector):
    def collect(self) -> dict:
        temps = psutil.sensors_temperatures()
        cpu_temp = None
        if "coretemp" in temps:
            cpu_temp = temps["coretemp"][0].current
        elif "cpu_thermal" in temps:
            cpu_temp = temps["cpu_thermal"][0].current
        
        freq = psutil.cpu_freq()
        return {
            "percent": psutil.cpu_percent(interval=0.1),
            "per_cpu": psutil.cpu_percent(interval=0.1, percpu=True),
            "logical_count": psutil.cpu_count(),
            "physical_count": psutil.cpu_count(logical=False),
            "frequency_current": freq.current if freq else 0,
            "frequency_min": freq.min if freq else 0,
            "frequency_max": freq.max if freq else 0,
            "temperature": cpu_temp,
            "processes": [
                {"pid": p.info["pid"], "name": p.info["name"],
                 "cpu_percent": p.info["cpu_percent"]}
                for p in psutil.process_iter(["pid", "name", "cpu_percent"])
            ][:20]
        }
```

#### 3.2.4 `GpuCollector`

**Nota:** Coleta de GPU é mais complexa. Opções:

| Opção | Prós | Contras |
|---|---|---|
| `nvidia-smi` CLI via subprocess | Funciona sem lib extra | Apenas NVIDIA, parsing frágil |
| `pynvml` (NVML Python bindings) | API oficial NVIDIA | Apenas NVIDIA, dependência extra |
| `GPUtil` | Simples, open source | Apenas NVIDIA |
| `pyadl` / `amdsmi` | AMD support | Menos mantido |

**Recomendação:** Implementar como tentativa de `nvidia-smi` com fallback. Adicionar `pynvml` como dependência opcional.

**Dados coletados:**
- `name` — nome da GPU
- `utilization_gpu` — percentual de uso
- `memory_total`, `memory_used`, `memory_free` — memória da GPU
- `temperature` — temperatura da GPU
- `processes` — processos usando GPU (PID, nome, memória usada)

```python
# Estratégia: tentar nvidia-smi primeiro, depois pynvml, depois vazio
import subprocess
import json

class GpuCollector(BaseCollector):
    def collect(self) -> dict:
        try:
            result = subprocess.run(
                ["nvidia-smi", "--query-gpu=name,utilization.gpu,memory.total,"
                 "memory.used,memory.free,temperature.gpu",
                 "--format=csv,noheader,nounits"],
                capture_output=True, text=True, timeout=5
            )
            if result.returncode == 0:
                return self._parse_nvidia_smi(result.stdout)
        except (FileNotFoundError, subprocess.TimeoutExpired):
            pass
        return {"available": False, "gpus": []}
```

#### 3.2.5 `DiskCollector`

**Dados coletados:**
- `partitions` — lista de partições com:
  - `device`, `mountpoint`, `fstype`
  - `total`, `used`, `free` (bytes)
  - `percent` — percentual de uso
- `io_counters` — I/O de leitura/escrita desde boot

```python
import psutil

class DiskCollector(BaseCollector):
    def collect(self) -> dict:
        io = psutil.disk_io_counters()
        partitions = []
        for part in psutil.disk_partitions():
            try:
                usage = psutil.disk_usage(part.mountpoint)
                partitions.append({
                    "device": part.device,
                    "mountpoint": part.mountpoint,
                    "fstype": part.fstype,
                    "total": usage.total,
                    "used": usage.used,
                    "free": usage.free,
                    "percent": usage.percent,
                })
            except PermissionError:
                continue
        
        return {
            "partitions": partitions,
            "io_read_bytes": io.read_bytes if io else 0,
            "io_write_bytes": io.write_bytes if io else 0,
            "io_read_count": io.read_count if io else 0,
            "io_write_count": io.write_count if io else 0,
        }
```

### 3.3 Fase 3 — Widgets Customizados

#### 3.3.1 `ResourceGaugeWidget` (em `resources/widgets/` conforme Contrato 11)

**Descrição:** Widget circular/barra para exibir percentual de uso com cor gradiente (verde → amarelo → vermelho).

**Atributos:**
- `value` — float 0.0–100.0
- `label` — string descritiva (ex: "RAM", "CPU")
- `sublabel` — string secundária (ex: "8.2/16.0 GB")
- `threshold_warning` — valor acima do qual fica amarelo (padrão 70.0)
- `threshold_danger` — valor acima do qual fica vermelho (padrão 90.0)
- `size` — tupla (width, height)

**Métodos:**
- `set_value(value, sublabel="")` — atualiza valor e sublabel

**Uso previsto:**
```python
gauge = ResourceGaugeWidget("RAM", size=(180, 180))
gauge.set_value(45.2, "7.2/16.0 GB")
self.main_layout.addWidget(gauge)
```

#### 3.3.2 `ProcessTableWidget` (em `resources/widgets/`)

**Descrição:** Tabela para exibir processos ordenados por uso de recurso.

**Atributos:**
- `mode` — "memory" ou "cpu" (define colunas)
- `items` — lista de dicts com dados dos processos

**Métodos:**
- `update_data(items, mode)` — atualiza dados da tabela

#### 3.3.3 `ResourceTimelineWidget` (em `resources/widgets/`)

**Descrição:** Gráfico de linha simples mostrando evolução temporal do recurso (últimos 60 segundos).

**Atributos:**
- `history` — lista de valores com timestamp
- `max_history` — máximo de pontos no gráfico (padrão 60)
- `color` — cor da linha

**Métodos:**
- `add_point(value)` — adiciona ponto ao histórico
- `clear()` — limpa histórico

### 3.4 Fase 4 — Plugin Principal (`ResourceMonitorPlugin`)

#### 3.4.1 Estrutura da UI

```
┌──────────────────────────────────────────────────┐
│  Monitor de Recursos               [badge PRONTA]│
├──────────────────────────────────────────────────┤
│ ┌────────────┐ ┌────────────┐ ┌────────────┐    │
│ │    RAM     │ │    CPU     │ │    GPU     │    │
│ │   ╭──────╮ │ │   ╭──────╮ │ │   ╭──────╮ │    │
│ │   │ 45%  │ │ │   │ 23%  │ │ │   │ 67%  │ │    │
│ │   ╰──────╯ │ │   ╰──────╯ │ │   ╰──────╯ │    │
│ │ 7.2/16 GB  │ │ 2.4 GHz    │ │ 4.1/8.0 GB │    │
│ └────────────┘ └────────────┘ └────────────┘    │
│ ┌────────────┐                                   │
│ │  Disco C:  │  ───────── 62% ─────────          │
│ │  320/500GB │                                   │
│ │  Disco D:  │  ───────── 15% ─────────          │
│ │  80/500GB  │                                   │
│ └────────────┘                                   │
├──────────────────────────────────────────────────┤
│  [Top Processos ▼]                                │
│  ┌──────────────────────────────────────┐        │
│  │ PID │ Nome        │ RAM   │ CPU      │        │
│  │ 123 │ chrome.exe  │ 450MB │ 12.3%    │        │
│  │ 456 │ python.exe  │ 200MB │  5.1%    │        │
│  │ ... │ ...         │ ...   │ ...      │        │
│  └──────────────────────────────────────┘        │
├──────────────────────────────────────────────────┤
│  [INICIAR MONITORAMENTO] [PARAR] [SALVAR LOG]    │
└──────────────────────────────────────────────────┘
```

#### 3.4.2 Timer de Atualização

- Usar `QTimer` para atualização periódica (a cada 1 segundo por padrão)
- Configurável via preferências (0.5s, 1s, 2s, 5s)
- Desligar timer quando o plugin perde foco (opcional)

```python
self._timer = QTimer(self)
self._timer.timeout.connect(self._refresh_data)
self._timer.start(1000)  # 1 segundo
```

#### 3.4.3 `_build_ui()` — Construção da UI

```python
def _build_ui(self):
    super()._build_ui()
    
    # Topo: gauges lado a lado
    gauge_row = QHBoxLayout()
    self._ram_gauge = ResourceGaugeWidget("RAM", size=(180, 180))
    self._cpu_gauge = ResourceGaugeWidget("CPU", size=(180, 180))
    self._gpu_gauge = ResourceGaugeWidget("GPU", size=(180, 180))
    gauge_row.addWidget(self._ram_gauge)
    gauge_row.addWidget(self._cpu_gauge)
    gauge_row.addWidget(self._gpu_gauge)
    gauge_row.addStretch()
    self.main_layout.addLayout(gauge_row)
    
    # Meio: discos
    self._disk_group = GroupPainel("Armazenamento")
    self._disk_layout = QVBoxLayout()
    self._disk_group.group_layout.addLayout(self._disk_layout)
    self.main_layout.addWidget(self._disk_group)
    
    # Processos
    self._process_table = ProcessTableWidget()
    grp_procs = GroupPainel("Top Processos")
    grp_procs.group_layout.addWidget(self._process_table)
    self.main_layout.addWidget(grp_procs)
    
    # Botões de ação
    self._btns = ExecutionButtons(self, {
        "start": {"text": "INICIAR MONITORAMENTO", "callback": self._on_start, "type": "primary"},
        "stop": {"text": "PARAR", "callback": self._on_stop, "type": "danger"},
        "save_log": {"text": "SALVAR LOG", "callback": self._on_save_log, "type": "secondary"},
    })
    self._btns.set_enabled("stop", False)
    self.main_layout.addWidget(self._btns)
```

#### 3.4.4 Timer e Atualização

```python
def _build_ui(self):
    super()._build_ui()
    self._timer = QTimer(self)
    self._timer.timeout.connect(self._refresh_data)

def _on_start(self):
    interval = self.preferences.get("refresh_interval_ms", 1000)
    self._timer.start(interval)
    self._btns.set_enabled("start", False)
    self._btns.set_enabled("stop", True)
    self.page.set_badge(self.page.RUNNING)
    self.logger.info("Monitoramento iniciado", code="MONITOR_START")

def _on_stop(self):
    self._timer.stop()
    self._btns.set_enabled("start", True)
    self._btns.set_enabled("stop", False)
    self.page.set_badge(self.page.PRONTA)
    self.logger.info("Monitoramento parado", code="MONITOR_STOP")

def _refresh_data(self):
    ram = self._ram_collector.collect()
    cpu = self._cpu_collector.collect()
    gpu = self._gpu_collector.collect()
    disk = self._disk_collector.collect()
    
    self._update_gauges(ram, cpu, gpu)
    self._update_disks(disk)
    self._update_processes(ram, cpu)
    
    # Log periódico opcional
    self._log_snapshot(ram, cpu, gpu, disk)
```

#### 3.4.5 Preferências

```python
PREF_INTERVAL = "refresh_interval_ms"
PREF_SHOW_GPU = "show_gpu"
PREF_SHOW_PROCESSES = "show_processes"
PREF_LOG_ENABLED = "log_enabled"
PREF_LOG_INTERVAL = "log_interval_sec"

def load_prefs(self):
    interval = self.preferences.get(PREF_INTERVAL, 1000)
    # aplicar nas UI
    self._interval_combo.set_selected(str(interval))

def save_prefs(self):
    self.preferences[PREF_INTERVAL] = 1000
    self.preferences[PREF_SHOW_GPU] = True
    self.preferences[PREF_SHOW_PROCESSES] = True
    self.preferences[PREF_LOG_ENABLED] = False
    self.preferences[PREF_LOG_INTERVAL] = 60
```

### 3.5 Fase 5 — Dependências Externas

**Adicionar ao `requirements.txt`** (Contrato 8):
```
psutil>=5.9.0
pynvml>=11.5.0       # opcional — GPU NVIDIA
```

`psutil` é a única dependência obrigatória (RAM, CPU, Disk). `pynvml` é opcional para GPU NVIDIA — o código deve funcionar sem ela.

### 3.6 Fase 6 — Novo Enum ToolType (Opcional)

Se desejar agrupar visualmente na toolbar, adicionar em `core/enum/ToolType.py`:
```python
class ToolType(str, Enum):
    ...
    MONITOR = "Monitor"
```

---

## 4. Cronograma de Implementação

| Fase | O que | Arquivos | Esforço |
|---|---|---|---|
| **1** | ToolKey + ToolRegistry + __init__ | 3 arquivos | 30 min |
| **2a** | RamCollector + CpuCollector + DiskCollector | 4 arquivos | 1h |
| **2b** | GpuCollector | 1 arquivo | 1h |
| **3a** | ResourceGaugeWidget | 1 arquivo + skill | 1h |
| **3b** | ProcessTableWidget | 1 arquivo | 30 min |
| **3c** | ResourceTimelineWidget | 1 arquivo | 30 min |
| **4** | ResourceMonitorPlugin (UI + timer + refresh) | 1 arquivo | 2h |
| **5** | requirements.txt + testes | 1 arquivo | 15 min |
| **6** | Documentação (skill + esta skill) | 2 arquivos | 30 min |

**Total estimado:** ~6–7 horas de desenvolvimento.

---

## 5. Considerações Técnicas

### 5.1 Performance do Timer

- O timer de 1s dispara coleta de todos os coletores. `psutil` é rápido (sub-ms), mas `nvidia-smi` pode levar 100-300ms.
- **Solução:** Coletar GPU em timer separado (a cada 2s) se GPU estiver disponível, ou usar cache curto.
- **Solução 2:** Executar coletores em `QThread` com `PipelineRunner` (padrão existente no sistema).

### 5.2 Pipeline para Coleta

Para manter a UI responsiva, a coleta pode ser feita em thread separada:

```python
from core.papeline.PipelineRunner import PipelineRunner
from core.papeline.step import BaseStep

class CollectStep(BaseStep):
    def execute(self, context):
        context["ram_data"] = RamCollector().collect()
        context["cpu_data"] = CpuCollector().collect()
        return context
```

Mas para um timer de 1s, o overhead de criar PipelineRunner a cada segundo é alto. **Recomendação:** coletar síncrono no timer para dados leves (RAM, CPU simples) e thread separada para GPU.

### 5.3 Log de Histórico

- Usar `Preferences` para persistir configurações, NÃO para histórico de dados.
- Para logging de snapshots, usar `JsonUtil.create_temp_json()` com timestamp.
- Exportar CSV via `FormatUtils` para análise externa.

### 5.4 Temperatura da CPU

- `psutil.sensors_temperatures()` funciona no Linux e Windows (via WMI).
- No Windows, pode retornar vazio. Alternativa: usar `wmic` via subprocess ou `pywin32`.
- **Decisão de design:** Mostrar temperatura apenas se disponível, sem travar se não existir.

### 5.5 Discos Montados

- `psutil.disk_partitions()` lista todos os discos. Alguns podem não ter permissão de leitura (ex: CD-ROM vazio).
- Filtrar com `try/except PermissionError`.

---

## 6. Riscos e Mitigações

| Risco | Impacto | Mitigação |
|---|---|---|
| `nvidia-smi` não instalado | GPU não monitorada | Fallback silencioso, mostrar "GPU indisponível" |
| `psutil.sensors_temperatures()` vazio | Temperatura não disponível | Mostrar "N/A" no gauge |
| Permissão negada ao ler disco | Disco não aparece | `try/except PermissionError` e pular |
| Timer de 1s sobrecarregar CPU | UI lenta | Timer configurável (1s, 2s, 5s); coleta GPU separada |
| `PyNVML` não instalado | GPU NVIDIA não monitorada via NVML | Tentar nvidia-smi como fallback primário |
| Muitos processos (centenas) | Tabela lenta | Filtrar top 20; paginação opcional |

---

## 7. Dependências

### Obrigatórias
```
psutil>=5.9.0
```

### Opcionais
```
pynvml>=11.5.0       # GPU NVIDIA via NVML
```

### Nativas do Python (já disponíveis)
- `subprocess` — para `nvidia-smi`
- `json` — parsing de saída
- `time` — timestamps
- `dataclasses` — estrutura de dados (Python 3.7+)
- `threading` — coleta em background

---

## 8. Documentação Necessária (Contrato 12)

### Skills a atualizar:
1. `docs/skills/widgets_skill.md` — adicionar `ResourceGaugeWidget`, `ProcessTableWidget`, `ResourceTimelineWidget`
2. `docs/skills/SKILL_CREATE_TOOL.md` — nada a mudar (padrão já cobre)
3. Criar `docs/skills/SKILL_RESOURCE_MONITOR.md` — skill específica do monitor

### Documentos a criar:
1. `docs/plans/implement_resource_monitor_plugin.md` (este documento)

---

## 9. Checklist de Verificação Final

- [ ] **ToolKey.RESOURCE_MONITOR** adicionado em `core/enum/ToolKey.py`
- [ ] **Plugin registrado** em `core/config/ToolRegistry.py` com categoria `CENTRAL`
- [ ] **Classe** herda de `BasePlugin` com `tool_key=ToolKey.RESOURCE_MONITOR.value`
- [ ] **`_build_ui()`** com `super()._build_ui()` e widgets de `resources/widgets/`
- [ ] **`load_prefs()`** e **`save_prefs()`** implementados
- [ ] **Coletores** seguem padrão `BaseCollector` com tratamento de erros
- [ ] **GpuCollector** tem fallback se GPU não disponível
- [ ] **Timer** configurável via preferências
- [ ] **Nenhum `QMessageBox`** — só `MessageBox`
- [ ] **Nenhum `QFileDialog`** — só `ExplorerUtils`
- [ ] **Nenhum `QProgressBar`** — só `SignalManager.progress_update`
- [ ] **Nenhum `print()`** — só `self.logger`
- [ ] **`except`** sempre com `as e` + `self.logger.error(...)`
- [ ] **Dependências** adicionadas ao `requirements.txt` (Contrato 8)
- [ ] **Widgets novos** em `resources/widgets/` (Contrato 11)
- [ ] **Widgets novos** documentados em `widgets_skill.md` (Contrato 12)
- [ ] **`requirements.txt`** atualizado com `psutil>=5.9.0`
- [ ] **Skill de monitor** criada em `docs/skills/`
- [ ] **Código compila** sem erros (`py_compile`)

---

## 10. Referências

- **Contratos do sistema:** `docs/ia/contracts.md`
- **Skill de criação de plugins:** `docs/skills/SKILL_CREATE_TOOL.md`
- **Skill de HUD/Progresso:** `docs/skills/SKILL_HUD_PROGRESS.md`
- **Skill de widgets:** `docs/skills/SKILL_WIDGETS.md`
- **Skill de comunicação:** `docs/skills/SKILL_COMUNICATION.md`
- **Skill de preferências:** `docs/skills/SKILL_PREFERENCES.md`
- **Skill de logs:** `docs/skills/SKILL_UTILS.md` → sessão LogUtils
- **Catálogo de classes:** `docs/skills/CatalogoClasses.md`
- **Plugin de exemplo:** `plugins/mrk_substitutor/MrkSubstitutorPlugin.py`
- **ConsolePlugin (exemplo simples):** `plugins/console/ConsolePlugin.py`
- **Pipeline assíncrono:** `docs/skills/SKILL_ASYNC_PIPELINE.md`

---

## 11. Estrutura Final Esperada

```
plugins/resource_monitor/
├── __init__.py                                   # vazio
├── ResourceMonitorPlugin.py                      # ~300 linhas
├── collector/
│   ├── __init__.py                               # exporta todos os coletores
│   ├── BaseCollector.py                          # ~20 linhas
│   ├── RamCollector.py                           # ~40 linhas
│   ├── CpuCollector.py                           # ~50 linhas
│   ├── GpuCollector.py                           # ~80 linhas
│   └── DiskCollector.py                          # ~50 linhas

resources/widgets/
├── ResourceGaugeWidget.py                        # ~150 linhas (NOVO)
├── ProcessTableWidget.py                         # ~100 linhas (NOVO)
└── ResourceTimelineWidget.py                     # ~80 linhas (NOVO)

core/enum/
├── ToolKey.py                                    # +1 linha (RESOURCE_MONITOR)

core/config/
├── ToolRegistry.py                               # +10 linhas (registro no _TOOLS)

requirements.txt                                  # +1 linha (psutil)
```

Total de **novos arquivos:** 12
Total de **arquivos modificados:** 3 (ToolKey, ToolRegistry, requirements.txt)

---