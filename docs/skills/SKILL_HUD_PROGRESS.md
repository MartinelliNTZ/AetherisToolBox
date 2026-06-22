# Skill: HUD Loader e ProgressBar — Sistema de Progresso

Esta skill documenta como o **HUD Loader** (overlay visual) e a **ProgressBar** (barra inferior) funcionam em conjunto no Aetheris ToolBox, e como plugins/tasks devem emitir progresso corretamente.

---

## 📋 Visão Geral

O sistema de progresso é **centralizado na MainWindow** (`core/ui/ui_main.py`). Ela possui:

1. **`QProgressBar`** — barra fixa na parte inferior da janela (0–10000, formatada como %)
2. **`HudCircularRingsLoader`** — overlay animado no centro da tela (3 modos: feedback real, timer, etapas)

Ambos são controlados **exclusivamente via `SignalManager`**. Nenhum plugin deve criar sua própria barra ou loader.

```
Plugin / Task                          MainWindow
      │                                     │
      ├─ execution_started ───────────────► │  ← mostra HUD + reseta ProgressBar
      │                                     │
      ├─ hud_update + progress_update ────► │  ← durante processamento
      │                                     │
      ├─ execution_finished ──────────────► │  ← sucesso: esconde HUD + reseta
      └─ execution_cancelled ────────────► │  ← falha: esconde HUD + reseta
```

---

## 🔌 Conexões na MainWindow (`core/ui/ui_main.py`)

```python
# ── ProgressBar ──────────────────────────────────────────────
self.progress = QProgressBar()
self.progress.setMinimum(0)
self.progress.setMaximum(10000)
self.progress.setValue(0)
self.progress.setFormat(" %p% - aguardando... ")
self.progress.setFixedHeight(20)

SignalManager.instance().progress_update.connect(self._on_progress_update)
SignalManager.instance().progress_reset.connect(self._on_progress_reset)

# ── HUD Loader (overlay) ────────────────────────────────────
self._hud = HudCircularRingsLoader(self)
self._hud.setGeometry(self.rect())

SignalManager.instance().hud_show.connect(self._on_hud_show)
SignalManager.instance().hud_update.connect(self._on_hud_update)
SignalManager.instance().hud_hide.connect(self._on_hud_hide)

# ── Ciclo de vida de execução ───────────────────────────────
SignalManager.instance().execution_started.connect(self._on_execution_started)
SignalManager.instance().execution_finished.connect(self._on_execution_finished)
SignalManager.instance().execution_cancelled.connect(self._on_execution_cancelled)
```

### Handlers da MainWindow

```python
def _on_execution_started(self, tool_name: str):
    """Início de execução: mostra HUD e reseta progresso."""
    self._hud.set_progress(0.0, f"Iniciando {tool_name}...")
    self._hud.show_loader()
    self._on_progress_reset()

def _on_execution_finished(self, tool_name: str):
    """Fim de execução: esconde HUD e reseta progress para 0%."""
    self._hud.hide_loader()
    self._on_progress_reset()

def _on_execution_cancelled(self, tool_name: str):
    """Cancelamento: esconde HUD e reseta progresso."""
    self._hud.hide_loader()
    self._on_progress_reset()

def _on_progress_update(self, value: float):
    scaled = int(round(value * 100.0))
    self.progress.setValue(scaled)
    if value <= 0:
        self.progress.setFormat(" %p% - aguardando... ")
    elif value >= 100:
        self.progress.setFormat(" 100% - concluído! ")
    else:
        self.progress.setFormat(f" {value:.2f}% - executando... ")

def _on_hud_show(self, data: dict):
    msg = data.get("message", "Processando...")
    timer = data.get("timer", None)       # Modo 2
    stages = data.get("stages", None)     # Modo 3
    if timer is not None:
        self._hud.start_timer(float(timer), msg)
    elif stages is not None and isinstance(stages, (list, tuple)) and len(stages) == 2:
        self._hud.start_staged(float(stages[0]), int(stages[1]), msg)
    else:
        self._hud.set_progress(0.0, msg)  # Modo 1
    self._hud.show_loader()

def _on_hud_update(self, data: dict):
    msg = data.get("message", "")
    progress = data.get("progress", None)
    if progress is not None:
        self._hud.progress = max(0.0, min(100.0, float(progress)))
    if msg:
        self._hud.message = msg
    if progress is not None or msg:
        self._hud.update()
```

---

## 📡 Fluxo de Progresso em Background (QThread)

Quando uma **Task** (herdando de `BaseTask`) executa em **QThread** (via `PipelineRunner`), ela DEVE emitir progresso usando `SignalManager.instance()` — os **sinais Qt são thread-safe**:

```python
# core/papeline/task/MinhaTask.py
from core.manager.SignalManager import SignalManager

class MinhaTask(BaseTask):
    def _run(self) -> bool:
        signals = SignalManager.instance()

        # Etapa 1 (0% → 30%)
        signals.hud_update.emit({"message": "Etapa 1...", "progress": 10.0})
        signals.progress_update.emit(10.0)
        # ... lógica pesada ...

        # Etapa 2 (30% → 70%)
        signals.hud_update.emit({"message": "Etapa 2...", "progress": 50.0})
        signals.progress_update.emit(50.0)
        # ... lógica pesada ...

        # Final (100%)
        self.result = {...}
        return True
```

### Progresso combinado (HUD + ProgressBar)

Para manter HUD e ProgressBar sincronizados, **sempre emita ambos**:

```python
progresso = 50.0
mensagem = "Processando..."

signals.hud_update.emit({"message": mensagem, "progress": progresso})
signals.progress_update.emit(progresso)
```

---

## 🎯 Fluxo Completo (Plugin + PipelineRunner + Task)

```
┌─────────────────────────────────────────────────────────────────────┐
│ PLUGIN (Main Thread)                                                │
│                                                                     │
│  1. _on_executar()                                                  │
│     ├─ signals.execution_started.emit(tool_name)  ← MainWindow      │
│     │                                          mostra HUD + reseta  │
│     ├─ signals.hud_show.emit({"message": "..."}) ← Modo 1           │
│     └─ runner.start() ─────────────────────────────────────────┐    │
│                                                                 │    │
│  2. _on_done(context)  ← finished_ok da pipeline               │    │
│     ├─ signals.execution_finished.emit(tool_name)               │    │
│     └─ MessageBox.show_info("Concluído!")                      │    │
│                                                                 │    │
│  3. _on_runner_finished()  ← finished da pipeline              │    │
│     ├─ hud_hide.emit()                                         │    │
│     ├─ progress_update.emit(0)                                 │    │
│     └─ restaura botões                                        │    │
└─────────────────────────────────────────────────────────────────┘    │
                                                                       │
┌─────────────────────────────────────────────────────────────────────┐ │
│ PIPELINERUNNER (QThread)                                           │ │
│                                                                     │ │
│  runner.run()                                                       │ │
│    ├─ Cria ExecutionContext                                         │ │
│    ├─ Cria AsyncPipelineEngine(steps, context)                      │ │
│    ├─ engine.start_non_blocking() ──────────────────────────────┐   │ │
│    │                                                            │   │ │
│    └─ while engine.is_running: msleep(50) ← mantém thread viva  │   │ │
└─────────────────────────────────────────────────────────────────┤   │ │
                                                                   │   │ │
┌─────────────────────────────────────────────────────────────────┐│   │ │
│ TASK (dentro da QThread)                                        ││   │ │
│                                                                  ││   │ │
│  _run()                                                          ││   │ │
│    ├─ signals.hud_update(5%) + progress_update(5%)              ││   │ │
│    │   ← "Lendo arquivo..."                                     ││   │ │
│    ├─ laspy.read()                                              ││   │ │
│    ├─ signals.hud_update(50%) + progress_update(50%)            ││   │ │
│    │   ← "Filtrando pontos..."                                  ││   │ │
│    ├─ processamento                                             ││   │ │
│    ├─ signals.hud_update(75%) + progress_update(75%)            ││   │ │
│    │   ← "Salvando resultado..."                                ││   │ │
│    ├─ write()                                                   ││   │ │
│    └─ return True                                               ││   │ │
└─────────────────────────────────────────────────────────────────┘│   │ │
                                                                   │   │ │
  SignalManager.instance() (thread-safe) ◄─────────────────────────┘   │ │
    ├─ hud_update ──► MainWindow._on_hud_update (Main Thread)          │ │
    ├─ progress_update ──► MainWindow._on_progress_update              │ │
    └─ sinais são postos na fila de eventos da Main Thread ────────────┘ │
                                                                         │
  PipelineRunner terminou ◄──────────────────────────────────────────────┘
    ├─ finished_ok.emit(context) ──► Plugin._on_done (Main Thread)
    └─ finished.emit() ──► Plugin._on_runner_finished (Main Thread)
```

---

## 📌 Regras Obrigatórias

| Regra | Descrição |
|-------|-----------|
| **Sinais Qt são thread-safe** | `SignalManager.instance().hud_update.emit(...)` funciona de dentro de qualquer QThread |
| **Sempre emita progress_update com hud_update** | Para manter a ProgressBar sincronizada com o HUD |
| **execution_started/finished** | Controlam mostrar/esconder o HUD automaticamente |
| **Nunca crie QProgressBar no plugin** | Use sempre `progress_update` (Contrato 20) |
| **Task não sabe da UI** | Task só emite sinais — não importa widgets, não chama MessageBox |
| **Plugin gerencia o ciclo** | Plugin chama `hud_show` antes do runner, `hud_hide` no `_on_runner_finished` |

---

## 🔍 Checklist ao implementar progresso

- [ ] Task importa `SignalManager` e emite `hud_update` + `progress_update` durante `_run()`
- [ ] Plugin emite `execution_started` antes de iniciar o runner
- [ ] Plugin emite `execution_finished` no callback de sucesso
- [ ] Plugin emite `hud_hide` + `progress_update(0)` no `_on_runner_finished`
- [ ] Nenhum `QProgressBar` ou `QLabel` de progresso foi criado no plugin
- [ ] A Task não importa `QWidget`, `MessageBox` ou qualquer classe de UI