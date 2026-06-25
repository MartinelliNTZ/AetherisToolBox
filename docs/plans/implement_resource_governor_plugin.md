# 🛡️ Plano de Implementação — Resource Governor Plugin

## 1. Visão Geral

**Objetivo:** Criar um **sistema de governança de recursos** para o Aetheris ToolBox que **limite e gerencie** o uso de RAM, CPU, GPU e armazenamento pelos plugins, evitando que o software consuma recursos excessivos do sistema e travamentos por falta de memória.

**Chave da ferramenta:** `ResourceGovernor`

### O que é (e o que NÃO é)

| É | Não é |
|---|---|
| Sistema que **limita** RAM total que plugins podem usar | ❌ Apenas mostrar uso de RAM |
| Controla **quantos CPUs** cada plugin pode usar | ❌ Gráfico de uso |
| Determina **se/quando** GPU é utilizada | ❌ Monitoramento passivo |
| Previne **out of memory** travando o sistema | ❌ Relatório estatístico |
| Gerencia **cota de armazenamento** para operações temporárias | ❌ Visualização de disco |

---

## 2. Arquitetura do Sistema de Governança

```
┌──────────────────────────────────────────────────────────────┐
│                   ResourceGovernor                           │
│  (Singleton — central de controle de recursos)               │
│                                                              │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐  │
│  │ RamLimiter  │  │ CpuGovernor │  │ GpuController       │  │
│  │             │  │             │  │                     │  │
│  │ • max_usage │  │ • max_cores │  │ • enable/disable    │  │
│  │ • per_plugin│  │ • affinity  │  │ • per_plugin        │  │
│  │ • warning   │  │ • priority  │  │ • fallback          │  │
│  └─────────────┘  └─────────────┘  └─────────────────────┘  │
│                                                              │
│  ┌──────────────────────────────────────────────────────────┐│
│  │               DiskQuotaManager                           ││
│  │  • temp_max_bytes  • cleanup_threshold  • per_plugin     ││
│  └──────────────────────────────────────────────────────────┘│
└──────────────────────────────────────────────────────────────┘
         │                 │                   │
         ▼                 ▼                   ▼
┌──────────────────────────────────────────────────────────────┐
│                    PipelineRunner (modificado)                │
│  Antes de executar um step: ResourceGovernor.check()        │
│  Se recurso exceder limite → pausa/recusa/cancela           │
└──────────────────────────────────────────────────────────────┘
```

---

## 3. Sistema Existente — Contexto Relevante

### 3.1 Como Plugins Executam HOJE

O fluxo de execução atual para operações pesadas usa `PipelineRunner` em QThread:

```
Plugin._on_executar()
  → SignalManager.execution_started.emit()
  → PipelineRunner(steps=[...], context={...}).start()
    → AsyncPipelineEngine.start_non_blocking()
      → step.create_task(context) → BaseTask.run()
      → step.run_inline(context)
```

**Problema atual:** NÃO há verificação de recursos antes de executar. Um plugin como `LasCheck` ou `IdwInterpolator` pode consumir toda a RAM disponível e travar o sistema.

### 3.2 Recursos que Plugins Consomem

| Plugin | Tipo | RAM | CPU | GPU | Disco |
|---|---|---|---|---|---|
| LasBlackFilter | Nuvem pontos | ALTA (arquivos LAS/LAZ) | MÉDIA | NÃO | MÉDIO |
| LasCheck | Validação | ALTA | MÉDIA | NÃO | BAIXO |
| IdwInterpolator | Interpolação | ALTA (grid) | ALTA | OPCIONAL | MÉDIO |
| MrkSubstitutor | Texto | BAIXA | BAIXA | NÃO | BAIXO |
| PointBoundary | Geometria | MÉDIA | BAIXA | NÃO | BAIXO |
| Classifier (TF) | ML | ALTA | MÉDIA | SIM (CUDA) | BAIXO |
| Docling | Documentos | MÉDIA | BAIXA | NÃO | MÉDIO |

### 3.3 Componentes Existentes que Serão Reutilizados

| Componente | Path | Função no Governor |
|---|---|---|
| `BasePlugin` | `plugins/BasePlugin.py` | Plugins herdam e consultam governor via `self.governor.check()` |
| `PipelineRunner` | `core/papeline/PipelineRunner.py` | **PONTO DE INJEÇÃO** — governor acopla aqui |
| `BaseStep` | `core/papeline/BaseStep.py` | Steps podem ter `resource_estimate` |
| `AsyncPipelineEngine` | `core/papeline/AsyncPipelineEngine.py` | Engine executa steps — governor pausa/resume |
| `Preferences` | `utils/Preferences.py` | Persistir limites configurados pelo usuário |
| `LogUtils` | `core/config/LogUtils.py` | Logar violações de limite, recusas, etc |
| `SignalManager` | `core/manager/SignalManager.py` | Emitir `console_message` com alertas de recurso |
| `MessageBox` | `utils/MessageBox.py` | Avisar usuário quando recurso estourar |
| `ExecutionButtons` | `resources/widgets/ExecutionButtons.py` | Botões do plugin governor |
| `GroupPainel` | `resources/widgets/GroupPainel.py` | Agrupar configurações na UI |
| `GridDoubleSpinBox` | `resources/widgets/GridDoubleSpinBox.py` | Input numérico de limites |
| `GridCheckBox` | `resources/widgets/GridCheckBox.py` | Toggles de enable/disable |
| `PluginPage` | `resources/widgets/PluginPage.py` | Página padrão com badge |
| `FormatUtils` | `utils/FormatUtils.py` | Exibir tamanhos formatados (GB, MB) |

### 3.4 Contratos Relevantes

Os mesmos descritos no plano anterior (contratos 1-26), com ênfase adicional em:
- **Contrato 5**: ToolRegistry é a única fonte de configuração
- **Contrato 7**: Plugins se comunicam via SignalManager, não diretamente
- **Contrato 9**: Zero código morto
- **Contrato 11**: Widgets em `resources/widgets/` são obrigatórios
- **Contrato 12**: Documentação atualizada
- **Contrato 20**: Progresso via SignalManager

---

## 4. Plano de Implementação Detalhado

### 4.1 Fase 1 — Infraestrutura Core (`core/resource_governor/`)

Criar diretório `core/resource_governor/` com os módulos centrais:

#### 4.1.1 `ResourceGovernor` (Singleton)

**Arquivo:** `core/resource_governor/ResourceGovernor.py`

**Responsabilidade:** Único ponto de entrada para verificação de recursos. Todo plugin que quer executar operação pesada DEVE consultar o governor.

```python
class ResourceGovernor:
    """
    Singleton central de governança de recursos.
    
    Todo plugin DEVE consultar ResourceGovernor.check() antes de
    iniciar operações pesadas (PipelineRunner, I/O grande, etc).
    
    Uso:
        governor = ResourceGovernor.instance()
        result = governor.check("LasBlackFilter", 
            resource_type=ResourceType.RAM, 
            estimated_bytes=2_000_000_000)  # 2GB estimados
        if not result.allowed:
            MessageBox.show_warning(result.message)
            return
    """
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._ram_limiter = RamLimiter()
            cls._instance._cpu_governor = CpuGovernor()
            cls._instance._gpu_controller = GpuController()
            cls._instance._disk_quota = DiskQuotaManager()
        return cls._instance
    
    @classmethod
    def instance(cls) -> "ResourceGovernor":
        if cls._instance is None:
            cls._instance = ResourceGovernor()
        return cls._instance
    
    def check(self, plugin_key: str, resource_type: ResourceType,
              estimated_bytes: int = 0, estimated_cores: int = 1) -> ResourceCheckResult:
        """
        Verifica se o recurso solicitado está dentro dos limites.
        
        Args:
            plugin_key: ToolKey do plugin solicitante
            resource_type: RAM, CPU, GPU ou DISK
            estimated_bytes: bytes estimados (RAM/DISK)
            estimated_cores: cores estimados (CPU)
        Returns:
            ResourceCheckResult(allowed=True/False, message=str)
        """
        if resource_type == ResourceType.RAM:
            return self._ram_limiter.check(plugin_key, estimated_bytes)
        elif resource_type == ResourceType.CPU:
            return self._cpu_governor.check(plugin_key, estimated_cores)
        elif resource_type == ResourceType.GPU:
            return self._gpu_controller.check(plugin_key)
        elif resource_type == ResourceType.DISK:
            return self._disk_quota.check(plugin_key, estimated_bytes)
        return ResourceCheckResult(True, "OK")
    
    def release(self, plugin_key: str, resource_type: ResourceType,
                bytes_: int = 0, cores: int = 0) -> None:
        """Libera recursos após uso. Chamado no finish/cancel do plugin."""
        if resource_type == ResourceType.RAM:
            self._ram_limiter.release(plugin_key, bytes_)
        elif resource_type == ResourceType.CPU:
            self._cpu_governor.release(plugin_key, cores)
    
    # ── Getters para a UI de configuração ──────────────────────
    
    @property
    def ram_limiter(self) -> "RamLimiter":
        return self._ram_limiter
    
    @property
    def cpu_governor(self) -> "CpuGovernor":
        return self._cpu_governor
    
    @property
    def gpu_controller(self) -> "GpuController":
        return self._gpu_controller
    
    @property
    def disk_quota(self) -> "DiskQuotaManager":
        return self._disk_quota
```

#### 4.1.2 `ResourceType` Enum

**Arquivo:** `core/resource_governor/ResourceType.py`

```python
class ResourceType(str, Enum):
    RAM = "ram"
    CPU = "cpu"
    GPU = "gpu"
    DISK = "disk"
```

#### 4.1.3 `ResourceCheckResult` DataClass

**Arquivo:** `core/resource_governor/ResourceCheckResult.py`

```python
from dataclasses import dataclass

@dataclass
class ResourceCheckResult:
    allowed: bool
    message: str
    current_usage: float = 0.0     # % atual
    limit: float = 0.0             # % limite
    suggested_action: str = ""     # "wait", "reduce", "deny"
```

### 4.2 Fase 2 — Limitadores Individuais

#### 4.2.1 `RamLimiter`

**Arquivo:** `core/resource_governor/limiter/RamLimiter.py`

**Funcionamento:**
1. Calcula RAM total do sistema (via psutil)
2. Aplica limite percentual configurado (ex: 80% = não deixa o toolbox usar mais que 80% da RAM total)
3. Rastreia RAM consumida por plugin
4. Bloqueia nova operação se limite for excedido

```python
class RamLimiter:
    """
    Limita o uso de RAM que o Aetheris ToolBox pode consumir.
    Impede que plugins iniciem operações se a RAM usada + estimada
    ultrapassar o limite configurado.
    """
    
    def __init__(self):
        self._enabled: bool = True
        self._max_percent: float = 80.0   # 80% da RAM total
        self._per_plugin_limits: Dict[str, float] = {}  # bytes por plugin
        self._current_usage: Dict[str, float] = {}  # bytes atuais por plugin
    
    def check(self, plugin_key: str, estimated_bytes: int) -> ResourceCheckResult:
        if not self._enabled:
            return ResourceCheckResult(True, "RAM limiter disabled")
        
        import psutil
        total_ram = psutil.virtual_memory().total
        max_bytes = total_ram * (self._max_percent / 100.0)
        
        # RAM já usada por todos os plugins + RAM do sistema
        used_by_toolbox = sum(self._current_usage.values())
        system_used = psutil.virtual_memory().used
        
        if used_by_toolbox + estimated_bytes > max_bytes:
            return ResourceCheckResult(
                allowed=False,
                message=(
                    f"Limite de RAM excedido! "
                    f"Uso atual: {FormatUtils.format_size(used_by_toolbox)} / "
                    f"Limite: {FormatUtils.format_size(max_bytes)} "
                    f"({self._max_percent:.0f}%)"
                ),
                current_usage=used_by_toolbox,
                limit=max_bytes,
                suggested_action="reduce",
            )
        
        # Verifica limite por plugin (se configurado)
        plugin_limit = self._per_plugin_limits.get(plugin_key)
        if plugin_limit and estimated_bytes > plugin_limit:
            return ResourceCheckResult(
                allowed=False,
                message=(
                    f"Plugin '{plugin_key}' excedeu limite de RAM: "
                    f"{FormatUtils.format_size(estimated_bytes)} > "
                    f"{FormatUtils.format_size(plugin_limit)}"
                ),
                suggested_action="reduce",
            )
        
        return ResourceCheckResult(True, "OK")
    
    def reserve(self, plugin_key: str, bytes_: int) -> None:
        """Reserva RAM para um plugin. Chamado ANTES da execução."""
        self._current_usage[plugin_key] = \
            self._current_usage.get(plugin_key, 0) + bytes_
    
    def release(self, plugin_key: str, bytes_: int) -> None:
        """Libera RAM reservada. Chamado no fim da execução."""
        current = self._current_usage.get(plugin_key, 0)
        self._current_usage[plugin_key] = max(0, current - bytes_)
        if self._current_usage[plugin_key] == 0:
            self._current_usage.pop(plugin_key, None)
    
    # ── Configuração (exposta na UI) ───────────────────────────
    
    def set_max_percent(self, percent: float) -> None:
        self._max_percent = max(10.0, min(99.0, percent))
    
    def set_plugin_limit(self, plugin_key: str, max_bytes: float) -> None:
        self._per_plugin_limits[plugin_key] = max_bytes
    
    def remove_plugin_limit(self, plugin_key: str) -> None:
        self._per_plugin_limits.pop(plugin_key, None)
```

#### 4.2.2 `CpuGovernor`

**Arquivo:** `core/resource_governor/limiter/CpuGovernor.py`

**Funcionamento:**
1. Define quantos **cores lógicos** os plugins podem usar simultaneamente
2. Opcionalmente define **CPU affinity** (processos pinados a cores específicos)
3. Evita que N plugins rodem em paralelo usando todos os cores

```python
class CpuGovernor:
    """
    Controla quantos cores cada plugin pode usar.
    Opcionalmente gerencia CPU affinity (Windows: SetProcessAffinityMask).
    """
    
    def __init__(self):
        self._enabled: bool = True
        self._max_cores_global: int = self._detect_cpu_count()
        self._per_plugin_cores: Dict[str, int] = {}  # cores por plugin
        self._current_allocation: Dict[str, int] = {}  # cores alocados
    
    def _detect_cpu_count(self) -> int:
        """Detecta cores lógicos do sistema, com fallback."""
        try:
            import psutil
            return psutil.cpu_count(logical=True)
        except (ImportError, AttributeError):
            import os
            return os.cpu_count() or 4
    
    def check(self, plugin_key: str, estimated_cores: int = 1) -> ResourceCheckResult:
        if not self._enabled:
            return ResourceCheckResult(True, "CPU governor disabled")
        
        # Limite por plugin
        plugin_max = self._per_plugin_cores.get(plugin_key, 
                       self._max_cores_global)
        
        if estimated_cores > plugin_max:
            return ResourceCheckResult(
                allowed=False,
                message=(
                    f"Plugin '{plugin_key}' solicitou {estimated_cores} "
                    f"cores, mas limite é {plugin_max}"
                ),
                suggested_action="reduce",
            )
        
        # Limite global: verifica se ainda há cores disponíveis
        allocated = sum(self._current_allocation.values())
        if allocated + estimated_cores > self._max_cores_global:
            return ResourceCheckResult(
                allowed=False,
                message=(
                    f"CPU sem capacidade! "
                    f"Alocado: {allocated}/{self._max_cores_global} cores"
                ),
                current_usage=allocated,
                limit=self._max_cores_global,
                suggested_action="wait",
            )
        
        return ResourceCheckResult(True, "OK")
    
    def reserve(self, plugin_key: str, cores: int) -> None:
        self._current_allocation[plugin_key] = \
            self._current_allocation.get(plugin_key, 0) + cores
    
    def release(self, plugin_key: str, cores: int) -> None:
        current = self._current_allocation.get(plugin_key, 0)
        self._current_allocation[plugin_key] = max(0, current - cores)
        if self._current_allocation[plugin_key] == 0:
            self._current_allocation.pop(plugin_key, None)
    
    def apply_affinity(self, plugin_key: str, cores: int) -> None:
        """
        Aplica CPU affinity ao processo atual para limitar 
        quantos cores físicos são usados.
        
        Nota: Em Python, CPU affinity é por processo, não por thread.
        Para controle mais fino, precisaria de multiprocessing.
        """
        try:
            import os
            if hasattr(os, 'sched_setaffinity'):  # Linux
                available = list(range(cores))
                os.sched_setaffinity(0, available)
            elif hasattr(os, 'system'):  # Windows
                mask = (1 << cores) - 1
                import ctypes
                kernel32 = ctypes.windll.kernel32
                kernel32.SetProcessAffinityMask(-1, mask)
        except Exception as e:
            LogUtils("System", "CpuGovernor").warning(
                "Falha ao aplicar CPU affinity", 
                code="AFFINITY_FAIL",
                error=str(e)
            )
```

#### 4.2.3 `GpuController`

**Arquivo:** `core/resource_governor/limiter/GpuController.py`

**Funcionamento:**
1. Controla **se** GPU pode ser usada (enable/disable global)
2. Controla **quais plugins** podem usar GPU
3. Controla se GPU é usada com fallback automático para CPU
4. Detecta GPU disponível (NVIDIA via nvidia-smi, AMD via rocm-smi, Intel)

```python
class GpuController:
    """
    Controla o uso de GPU pelos plugins.
    
    Modos:
        - OFF: GPU desabilitada globalmente
        - AUTO: GPU usada apenas se disponível e o plugin tem permissão
        - FORCE: GPU obrigatória (falha se não disponível)
    
    Plugins que usam GPU: Classifier (TensorFlow/CUDA), 
    futuros plugins de ML/visão computacional.
    """
    
    # Modos de operação
    MODE_OFF = "off"
    MODE_AUTO = "auto"
    MODE_FORCE = "force"
    
    def __init__(self):
        self._mode: str = self.MODE_AUTO
        self._gpu_available: bool = self._detect_gpu()
        self._allowed_plugins: set[str] = set()  # plugins que podem usar GPU
        self._gpu_info: dict = {}  # info da GPU detectada
    
    def _detect_gpu(self) -> bool:
        """Detecta GPU NVIDIA ou AMD disponível."""
        # Tenta nvidia-smi
        try:
            import subprocess
            result = subprocess.run(
                ["nvidia-smi", "--query-gpu=name,memory.total,driver_version",
                 "--format=csv,noheader,nounits"],
                capture_output=True, text=True, timeout=3
            )
            if result.returncode == 0:
                parts = result.stdout.strip().split(",")
                self._gpu_info = {
                    "vendor": "nvidia",
                    "name": parts[0].strip() if len(parts) > 0 else "Unknown",
                    "memory_mb": float(parts[1].strip()) if len(parts) > 1 else 0,
                    "driver": parts[2].strip() if len(parts) > 2 else "",
                }
                return True
        except (FileNotFoundError, subprocess.TimeoutExpired, Exception):
            pass
        
        # Tenta verificar se TensorFlow/CUDA está disponível
        try:
            import torch
            if torch.cuda.is_available():
                self._gpu_info = {
                    "vendor": "nvidia",
                    "name": torch.cuda.get_device_name(0),
                    "memory_mb": torch.cuda.get_device_properties(0).total_memory / 1e6,
                    "driver": torch.version.cuda or "",
                }
                return True
        except ImportError:
            pass
        
        return False
    
    def check(self, plugin_key: str) -> ResourceCheckResult:
        if self._mode == self.MODE_OFF:
            return ResourceCheckResult(False, "GPU desabilitada globalmente",
                                       suggested_action="deny")
        
        if plugin_key not in self._allowed_plugins:
            return ResourceCheckResult(False, 
                f"Plugin '{plugin_key}' não tem permissão para usar GPU",
                suggested_action="deny")
        
        if self._mode == self.MODE_FORCE and not self._gpu_available:
            return ResourceCheckResult(False, 
                "GPU habilitada como FORÇADA, mas nenhuma GPU disponível",
                suggested_action="deny")
        
        if not self._gpu_available:
            return ResourceCheckResult(False, 
                "GPU não disponível. Use fallback CPU.",
                suggested_action="reduce")
        
        return ResourceCheckResult(True, "GPU disponível")
    
    def allow_plugin(self, plugin_key: str) -> None:
        """Permite que um plugin use GPU."""
        self._allowed_plugins.add(plugin_key)
    
    def disallow_plugin(self, plugin_key: str) -> None:
        """Remove permissão de GPU de um plugin."""
        self._allowed_plugins.discard(plugin_key)
```

#### 4.2.4 `DiskQuotaManager`

**Arquivo:** `core/resource_governor/limiter/DiskQuotaManager.py`

**Funcionamento:**
1. Define cota máxima de **armazenamento temporário** que plugins podem usar
2. Monitora diretórios temporários (`config/data/file_preview/temp/`)
3. Limpeza automática quando cota é excedida

```python
class DiskQuotaManager:
    """
    Gerencia cota de armazenamento para arquivos temporários.
    Previne que operações de plugins encham o disco.
    """
    
    def __init__(self):
        self._enabled: bool = True
        self._max_temp_bytes: int = 10_000_000_000  # 10GB padrão
        self._cleanup_threshold: float = 0.85  # limpa quando atinge 85%
        self._per_plugin_quota: Dict[str, int] = {}
    
    def _get_temp_dir(self) -> Path:
        """Retorna diretório temp padronizado."""
        from utils.ExplorerUtils import ExplorerUtils
        return Path(ExplorerUtils.get_plugin_config_dir()) / "file_preview" / "temp"
    
    def check(self, plugin_key: str, estimated_bytes: int) -> ResourceCheckResult:
        if not self._enabled:
            return ResourceCheckResult(True, "Disk quota disabled")
        
        temp_dir = self._get_temp_dir()
        if not temp_dir.exists():
            return ResourceCheckResult(True, "OK")
        
        # Calcula tamanho atual do diretório temp
        current_size = sum(
            f.stat().st_size for f in temp_dir.rglob("*") if f.is_file()
        )
        
        # Se estourar threshold, tenta limpeza automática
        if current_size > self._max_temp_bytes * self._cleanup_threshold:
            self._auto_cleanup(temp_dir)
            current_size = sum(
                f.stat().st_size for f in temp_dir.rglob("*") if f.is_file()
            )
        
        # Verifica se ainda há espaço
        if current_size + estimated_bytes > self._max_temp_bytes:
            return ResourceCheckResult(
                allowed=False,
                message=(
                    f"Cota de disco temporário excedida! "
                    f"Uso: {FormatUtils.format_size(current_size)} / "
                    f"Limite: {FormatUtils.format_size(self._max_temp_bytes)}"
                ),
                suggested_action="wait",
            )
        
        return ResourceCheckResult(True, "OK")
    
    def _auto_cleanup(self, temp_dir: Path) -> None:
        """Remove arquivos temporários mais antigos."""
        import time
        now = time.time()
        max_age = 3600  # 1 hora
        removed = 0
        for f in temp_dir.rglob("*"):
            if f.is_file() and (now - f.stat().st_mtime) > max_age:
                try:
                    f.unlink()
                    removed += 1
                except OSError:
                    pass
        
        if removed:
            LogUtils("System", "DiskQuotaManager").info(
                f"Limpeza automática: {removed} arquivos removidos",
                code="DISK_CLEANUP"
            )
```

### 4.3 Fase 3 — Injeção no PipelineRunner

**Arquivo modificado:** `core/papeline/PipelineRunner.py`

Adicionar verificação de recursos ANTES de executar qualquer pipeline. Esta é a principal forma de **forçar** os plugins a respeitarem os limites.

```python
class ResourceAwarePipelineRunner(PipelineRunner):
    """
    PipelineRunner com verificação de recursos.
    
    Antes de executar, consulta ResourceGovernor.
    Se recurso insuficiente, emite warning e NÃO executa.
    """
    
    resource_blocked = Signal(str)  # emitido quando recurso bloqueia execução
    
    def run(self) -> None:
        # Verifica recursos ANTES de rodar
        governor = ResourceGovernor.instance()
        
        # Estima recursos do contexto
        estimated_ram = self._context_data.get("estimated_ram_bytes", 0)
        estimated_cores = self._context_data.get("estimated_cores", 1)
        
        # Verifica RAM
        if estimated_ram > 0:
            result = governor.check(
                self._context_data.get("tool_key", "unknown"),
                ResourceType.RAM, estimated_bytes=estimated_ram
            )
            if not result.allowed:
                self.resource_blocked.emit(result.message)
                self.failed.emit(result.message)
                return
            
            # Reserva RAM
            governor.ram_limiter.reserve(
                self._context_data.get("tool_key", "unknown"), 
                estimated_ram
            )
        
        # Verifica CPU
        if estimated_cores > 1:
            result = governor.check(
                self._context_data.get("tool_key", "unknown"),
                ResourceType.CPU, estimated_cores=estimated_cores
            )
            if not result.allowed:
                self.resource_blocked.emit(result.message)
                self.failed.emit(result.message)
                return
        
        # Executa pipeline original
        super().run()
```

### 4.4 Fase 4 — Plugin UI de Configuração

#### 4.4.1 Estrutura da UI

```
┌──────────────────────────────────────────────────────┐
│  Gerenciador de Recursos          [badge PRONTA]      │
├──────────────────────────────────────────────────────┤
│                                                       │
│  ┌─ RAM ─────────────────────────────────────────┐   │
│  │  ☑ Habilitar limite de RAM                    │   │
│  │  Limite máximo: [ 80 ] % da RAM total         │   │
│  │                                               │   │
│  │  ┌─ Limites por Plugin ──────────────────┐    │   │
│  │  │ LasBlackFilter: [ 4 ] GB  [REMOVER]   │    │   │
│  │  │ IdwInterpolator: [ 8 ] GB [REMOVER]   │    │   │
│  │  │ [+ ADICIONAR PLUGIN]                  │    │   │
│  │  └───────────────────────────────────────┘    │   │
│  └───────────────────────────────────────────────┘   │
│                                                       │
│  ┌─ CPU ─────────────────────────────────────────┐   │
│  │  ☑ Habilitar controle de CPU                  │   │
│  │  Cores máximos globais: [ 4 ] de [8]          │   │
│  │                                               │   │
│  │  ┌─ Limites por Plugin ──────────────────┐    │   │
│  │  │ LasBlackFilter: [ 2 ] cores [REMOVER] │    │   │
│  │  │ Classifier:      [ 4 ] cores [REMOVER]│    │   │
│  │  └───────────────────────────────────────┘    │   │
│  └───────────────────────────────────────────────┘   │
│                                                       │
│  ┌─ GPU ─────────────────────────────────────────┐   │
│  │  Modo GPU: [● Desligado] [○ Auto] [○ Forçado] │   │
│  │  GPU detectada: NVIDIA RTX 3060 (12GB)        │   │
│  │                                               │   │
│  │  ☑ Classifier pode usar GPU                   │   │
│  │  ☐ (futuros plugins...)                       │   │
│  └───────────────────────────────────────────────┘   │
│                                                       │
│  ┌─ Armazenamento ───────────────────────────────┐   │
│  │  ☑ Habilitar cota de disco temp               │   │
│  │  Limite máximo: [ 10 ] GB                      │   │
│  │  Limpeza automática em: [ 85 ] %              │   │
│  │  [LIMPAR CACHE AGORA]                         │   │
│  └───────────────────────────────────────────────┘   │
│                                                       │
│  [SALVAR CONFIG] [RESTAURAR PADRÕES]                 │
└──────────────────────────────────────────────────────┘
```

#### 4.4.2 `ResourceGovernorPlugin`

**Arquivo:** `plugins/resource_governor/ResourceGovernorPlugin.py`

```python
class ResourceGovernorPlugin(BasePlugin):
    """
    Plugin de configuração do Resource Governor.
    Permite ao usuário definir limites de RAM, CPU, GPU e 
    armazenamento para o sistema e por plugin.
    """
    
    def __init__(self, parent=None):
        super().__init__(
            tool_key=ToolKey.RESOURCE_GOVERNOR.value,
            parent=parent,
            title="Gerenciador de Recursos",
        )
        self._governor = ResourceGovernor.instance()
        self.logger.info("ResourceGovernorPlugin inicializado", code="RGOV_READY")
    
    def _build_ui(self):
        super()._build_ui()
        self._btns = ExecutionButtons(self, {
            "salvar": {"text": "SALVAR CONFIG", "callback": self._on_salvar, "type": "primary"},
            "restaurar": {"text": "RESTAURAR PADRÕES", "callback": self._on_restaurar, "type": "secondary"},
        })
        
        # ── RAM ───────────────────────────────────────────────────
        grp_ram = GroupPainel("RAM")
        
        self._ram_enabled = GridCheckBox({
            "ram_enabled": {"label": "Habilitar limite de RAM", "default": True}
        }, num_columns=1)
        grp_ram.group_layout.addWidget(self._ram_enabled)
        
        self._ram_percent = GridDoubleSpinBox({
            "ram_percent": {
                "label": "Limite máximo:", 
                "default": 80.0, "min": 10, "max": 99, 
                "suffix": " % da RAM total"
            }
        })
        grp_ram.group_layout.addWidget(self._ram_percent)
        
        # Tabela de limites por plugin
        self._ram_plugins = self._build_plugin_limits_grid("ram")
        grp_ram.group_layout.addWidget(self._ram_plugins)
        
        self.main_layout.addWidget(grp_ram)
        
        # ── CPU ───────────────────────────────────────────────────
        grp_cpu = GroupPainel("CPU")
        
        self._cpu_enabled = GridCheckBox({
            "cpu_enabled": {"label": "Habilitar controle de CPU", "default": True}
        }, num_columns=1)
        grp_cpu.group_layout.addWidget(self._cpu_enabled)
        
        cpu_count = self._governor.cpu_governor._detect_cpu_count()
        self._cpu_max = GridDoubleSpinBox({
            "cpu_max": {
                "label": "Cores máximos globais:",
                "default": min(4, cpu_count), "min": 1, "max": cpu_count,
                "suffix": f" de {cpu_count}"
            }
        })
        grp_cpu.group_layout.addWidget(self._cpu_max)
        
        self._cpu_plugins = self._build_plugin_limits_grid("cpu")
        grp_cpu.group_layout.addWidget(self._cpu_plugins)
        
        self.main_layout.addWidget(grp_cpu)
        
        # ── GPU ───────────────────────────────────────────────────
        grp_gpu = GroupPainel("GPU")
        
        gpu_info = self._governor.gpu_controller._gpu_info
        gpu_status = f"{gpu_info.get('name', 'Nenhuma')}" if gpu_info else "Nenhuma GPU detectada"
        gpu_label = GridLabel({"gpu_status": {"label": "GPU detectada:", "value": gpu_status}})
        grp_gpu.group_layout.addWidget(gpu_label)
        
        self._gpu_mode = GridRadio({
            "off": {"label": "Desligado", "description": "GPU não será usada"},
            "auto": {"label": "Automático", "description": "Usa GPU se disponível"},
            "force": {"label": "Forçado", "description": "GPU obrigatória"},
        }, num_columns=3)
        self._gpu_mode.set_selected("auto")
        grp_gpu.group_layout.addWidget(self._gpu_mode)
        
        # Plugins com permissão GPU
        self._gpu_plugins = self._build_gpu_plugins_grid()
        grp_gpu.group_layout.addWidget(self._gpu_plugins)
        
        self.main_layout.addWidget(grp_gpu)
        
        # ── Armazenamento ──────────────────────────────────────────
        grp_disk = GroupPainel("Armazenamento Temporário")
        
        self._disk_enabled = GridCheckBox({
            "disk_enabled": {"label": "Habilitar cota de disco temporário", "default": True}
        }, num_columns=1)
        grp_disk.group_layout.addWidget(self._disk_enabled)
        
        self._disk_limit = GridDoubleSpinBox({
            "disk_limit": {
                "label": "Limite máximo:", 
                "default": 10, "min": 1, "max": 1000,
                "suffix": " GB"
            }
        })
        grp_disk.group_layout.addWidget(self._disk_limit)
        
        self._disk_cleanup = GridDoubleSpinBox({
            "disk_cleanup": {
                "label": "Limpeza automática em:", 
                "default": 85, "min": 50, "max": 100,
                "suffix": " %"
            }
        })
        grp_disk.group_layout.addWidget(self._disk_cleanup)
        
        btn_cleanup = SimpleSecondaryButton("LIMPAR CACHE AGORA")
        btn_cleanup.clicked.connect(self._on_cleanup_now)
        grp_disk.group_layout.addWidget(btn_cleanup)
        
        self.main_layout.addWidget(grp_disk)
        
        # ── Botões de ação ─────────────────────────────────────────
        self.main_layout.addWidget(self._btns)
        self.main_layout.addStretch()
```

### 4.5 Fase 5 — Integração nos Plugins Existentes

Cada plugin que consome recursos significativos DEVE ser modificado para consultar o `ResourceGovernor` antes de executar.

#### 4.5.1 Modificação no `PipelineRunner` (recomendado)

A abordagem mais limpa é modificar o `PipelineRunner.run()` para verificar automaticamente os recursos. Assim **nenhum plugin precisa ser modificado manualmente** — basta que o contexto contenha estimativas de recurso.

**Context padrão para plugins pesados:**
```python
context = {
    "tool_key": self.tool_key,
    "estimated_ram_bytes": 500_000_000,  # 500MB
    "estimated_cores": 2,
}
```

#### 4.5.2 Plugins que Precisam de Atenção

| Plugin | RAM Estimada | Cores | GPU | Prioridade |
|---|---|---|---|---|
| LasBlackFilter | 2GB+ | 2 | Não | Alta |
| LasCheck | 1GB+ | 2 | Não | Alta |
| IdwInterpolator | 4GB+ | 4 | Opcional | Alta |
| PointBoundary | 500MB | 1 | Não | Média |
| Classifier (TF) | 2GB+ | 4 | Sim (CUDA) | Alta |
| Docling | 500MB | 1 | Não | Baixa |

### 4.6 Fase 6 — Persistência e Preferências

**Arquivo:** `plugins/resource_governor/ResourceGovernorPlugin.py`

```python
PREF_RAM_ENABLED = "ram_enabled"
PREF_RAM_PERCENT = "ram_percent"
PREF_RAM_PLUGINS = "ram_plugin_limits"  # dict: {"LasBlackFilter": 4_000_000_000}
PREF_CPU_ENABLED = "cpu_enabled"
PREF_CPU_MAX = "cpu_max_cores"
PREF_CPU_PLUGINS = "cpu_plugin_limits"  # dict: {"LasBlackFilter": 2}
PREF_GPU_MODE = "gpu_mode"
PREF_GPU_PLUGINS = "gpu_allowed_plugins"  # list: ["Classifier"]
PREF_DISK_ENABLED = "disk_enabled"
PREF_DISK_LIMIT = "disk_limit_gb"
PREF_DISK_CLEANUP = "disk_cleanup_percent"

def load_prefs(self):
    # RAM
    ram_enabled = self.preferences.get(PREF_RAM_ENABLED, True)
    ram_percent = self.preferences.get(PREF_RAM_PERCENT, 80.0)
    self._ram_enabled.set_checked("ram_enabled", ram_enabled)
    self._ram_percent.set_value("ram_percent", ram_percent)
    
    # Aplica no governor
    self._governor.ram_limiter._enabled = ram_enabled
    self._governor.ram_limiter.set_max_percent(ram_percent)
    
    # Limites por plugin (RAM)
    ram_limits = self.preferences.get(PREF_RAM_PLUGINS, {})
    for plugin, max_bytes in ram_limits.items():
        self._governor.ram_limiter.set_plugin_limit(plugin, max_bytes)
    
    # ... similar para CPU, GPU, DISK

def save_prefs(self):
    self.preferences[PREF_RAM_ENABLED] = self._ram_enabled.get_checked("ram_enabled")
    self.preferences[PREF_RAM_PERCENT] = self._ram_percent.get_value("ram_percent")
    # ... etc
```

---

## 5. Cronograma de Implementação

| Fase | O que | Arquivos | Esforço |
|---|---|---|---|
| **1** | ResourceGovernor singleton + ResourceType + ResourceCheckResult | 3 arquivos | 1h |
| **2a** | RamLimiter | 1 arquivo | 1h |
| **2b** | CpuGovernor | 1 arquivo | 1h |
| **2c** | GpuController | 1 arquivo | 1.5h |
| **2d** | DiskQuotaManager | 1 arquivo | 1h |
| **3** | Modificação PipelineRunner (ResourceAwarePipelineRunner) | 1 arquivo modificado | 1h |
| **4** | ResourceGovernorPlugin (UI completa) | 1 arquivo | 2h |
| **5** | Integração em plugins existentes (context com estimativas) | 7 arquivos modificados | 2h |
| **6** | Persistência + Preferências + Icone | 2 arquivos | 30min |
| **7** | Documentação (skill + contratos + este plano) | 3 arquivos | 30min |

**Total estimado:** ~10-12 horas de desenvolvimento.

---

## 6. Estrutura Final Esperada

```
core/resource_governor/
├── __init__.py                           # exporta ResourceGovernor
├── ResourceGovernor.py                   # Singleton central (~100 linhas)
├── ResourceType.py                       # Enum (~10 linhas)
├── ResourceCheckResult.py                # DataClass (~10 linhas)
└── limiter/
    ├── __init__.py
    ├── RamLimiter.py                     # ~100 linhas
    ├── CpuGovernor.py                    # ~100 linhas
    ├── GpuController.py                  # ~100 linhas
    └── DiskQuotaManager.py               # ~80 linhas

plugins/resource_governor/
├── __init__.py
└── ResourceGovernorPlugin.py             # ~400 linhas

core/papeline/
├── PipelineRunner.py                     # MODIFICADO (+30 linhas)

plugins/*/ (vários)
├── ...Plugin.py                          # MODIFICADO: contexto com estimated_ram/cores

core/enum/
├── ToolKey.py                            # +1 linha (RESOURCE_GOVERNOR)

core/config/
├── ToolRegistry.py                       # +10 linhas

resources/icons/
├── ResourceGovernor.ico                  # (opcional)
```

**Novos arquivos:** 10
**Arquivos modificados:** ~9 (PipelineRunner + 7 plugins + ToolKey + ToolRegistry)

---

## 7. Dependências

### Obrigatórias (já existem ou nativas)
- `psutil` — já necessário para RamLimiter/CpuGovernor (adicionar ao requirements.txt)
- `subprocess`, `json`, `ctypes` — nativos do Python
- `dataclasses` — Python 3.7+
- `threading` — para operações de limpeza

### Adicionar ao requirements.txt
```
psutil>=5.9.0
```

---

## 8. Riscos e Mitigações

| Risco | Impacto | Mitigação |
|---|---|---|
| Plugin não consulta governor | Recurso pode estourar | Injeção automática no PipelineRunner |
| CPU affinity por processo afeta todos plugins | Controle falho | Documentar limitação; usar multiprocessing futuramente |
| GPU detectada mas não disponível em runtime | Plugin falha | GpuController retorna `suggested_action="reduce"` para fallback CPU |
| Cálculo de RAM estimada muito alta | Plugins bloqueados desnecessariamente | Estimar por baixo; permitir override na config |
| Disco temp cresce rápido | Cota estoura | Cleanup automático + alerta |
| Usuário desabilita governor global | Sem proteção | Log warning; permissão do usuário |

---

## 9. Checklist de Verificação Final

- [ ] **ResourceGovernor** implementado como Singleton em `core/resource_governor/`
- [ ] **RamLimiter** bloqueia RAM acima do limite configurado
- [ ] **CpuGovernor** limita cores por plugin e global
- [ ] **GpuController** detecta GPU e controla permissões
- [ ] **DiskQuotaManager** monitora e limpa temp
- [ ] **ResourceAwarePipelineRunner** verifica recursos automaticamente
- [ ] **ResourceGovernorPlugin** com UI de configuração
- [ ] **Plugins modificados** com estimativas de recurso no contexto
- [ ] **ToolKey.RESOURCE_GOVERNOR** adicionado
- [ ] **ToolRegistry** atualizado
- [ ] **requirements.txt** com `psutil>=5.9.0`
- [ ] **Nenhum `QMessageBox`** — só `MessageBox`
- [ ] **Nenhum `QFileDialog`** — só `ExplorerUtils`
- [ ] **Nenhum `print()`** — só `self.logger`
- [ ] **`except`** sempre com `as e` + `self.logger.error(...)`
- [ ] **Widgets novos** em `resources/widgets/` (se criados)
- [ ] **Documentação** atualizada (Contrato 12)

---

## 10. Como Usar o Governor nos Plugins

### Modo 1: Automático (recomendado)
Basta adicionar estimativas no contexto do PipelineRunner. O `ResourceAwarePipelineRunner` faz a verificação automaticamente.

```python
runner = PipelineRunner(
    steps=[MeuStep()],
    context={
        "tool_key": self.tool_key,
        "estimated_ram_bytes": 1_000_000_000,  # 1GB
        "estimated_cores": 2,
    },
    parent=self,
)
```

### Modo 2: Manual (para plugins sem PipelineRunner)
```python
governor = ResourceGovernor.instance()

result = governor.check(
    plugin_key=self.tool_key,
    resource_type=ResourceType.RAM,
    estimated_bytes=500_000_000,  # 500MB
)

if not result.allowed:
    MessageBox.show_warning(
        result.message,
        title="Recurso Indisponível"
    )
    return

# ... executar operação ...
governor.release(self.tool_key, ResourceType.RAM, 500_000_000)
```

### Modo 3: PipelineRunner com callback personalizado
```python
runner = ResourceAwarePipelineRunner(
    steps=[...],
    context={...},
    parent=self,
)
runner.resource_blocked.connect(
    lambda msg: MessageBox.show_warning(msg, title="Recurso Bloqueado")
)
runner.start()
```

---