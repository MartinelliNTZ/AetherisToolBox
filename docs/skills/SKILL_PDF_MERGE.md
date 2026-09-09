# Skill: Criando a Ferramenta de Merge de PDFs (PdfMerge)

Guia para criar e registrar a ferramenta de **merge de arquivos gerando um PDF agrupado**.
A versão inicial (v1) mescla **somente PDFs**, mas a arquitetura é **genérica e extensível**:
qualquer formato suportado (imagens, próximos formatos) vira uma página do PDF de saída
sem mudar a UI do plugin.

> ⚠️ **Antes de começar**, consulte:
> - `docs/skills/SKILL_AGENT.md` — ponto de controle e regras de pensamento
> - `docs/skills/SKILL_CREATE_TOOL.md` — processo padrão de criação de plugins
> - `docs/skills/SKILL_WIDGETS.md` (Contrato 11) — verifique se já existe widget pronto
> - `docs/skills/SKILL_PREFERENCES.md` — obrigatório implementar load/save_prefs
> - `docs/skills/SKILL_HUD_PROGRESS.md` e `docs/skills/SKILL_ASYNC_PIPELINE.md` — progresso/background
> - `docs/skills/SKILL_PLUGIN_CONTRACT.md` — regras imutáveis (Contratos 8, 11, 17, 18, 20...)

---

## 🎯 Objetivo

| Aspecto | Decisão |
|---|---|
| Nome exibido | `Merge PDF` |
| ToolKey | `PDF_MERGE = "PdfMerge"` |
| Pasta do plugin | `plugins/pdf_merge/` |
| Classe | `PdfMergePlugin(BasePlugin)` |
| Grupo na toolbar | `ToolType.FOLDER` (documentos — igual ao Docling) |
| Categoria | `CategoryTool.CENTRAL` (aba no workspace central) |
| Entrada v1 | Somente `.pdf` (`PdfWriter.append`) |
| Futuro | Imagens (`.png`, `.jpg`, ...) e outros formatos → página no PDF |

## 🧱 Arquitetura "Genérica" (por handlers de extensão)

Em vez de codificar "merge de PDF" diretamente no botão, a ferramenta mantém um
**registro de input handlers**: cada extensão suportada tem uma função que anexa o
conteúdo do arquivo ao `PdfWriter` de saída. O dispatcher escolhe o handler pela
extensão do arquivo:

```python
# plugins/pdf_merge/PdfMergePlugin.py (módulo, fora da classe)
from typing import Callable, Dict

# Filtro v1 — só PDFs. Ao adicionar imagens, mescle com IMAGE_EXTENSIONS.
PDF_FILTER: Dict[str, Dict[str, Any]] = {
    ".pdf": {"label": ".pdf", "description": "Adobe Portable Document", "default": True},
}

# Registro de handlers — ext → função que anexa páginas ao writer.
HANDLERS: Dict[str, Callable[["PdfWriter", str], None]] = {
    ".pdf": _append_pdf,
    # Futuro: ".png": _append_image, ".jpg": _append_image, ...
}
```

> 💡 **Por que isso é genérico?** A UI (lista de arquivos, pasta de saída, opções)
> não muda quando novos formatos entram. Basta:
> 1. adicionar a extensão ao filtro passado ao `FileListView`;
> 2. registrar a função handler no dict `HANDLERS`;
> 3. usar Pillow (`requirements.txt` já tem) para converter imagem → página PDF.
> Nenhuma lógica de negócio é alterada.

### Dispatcher (núcleo do merge)

```python
def _append_file(self, writer, file_path: str) -> None:
    """Anexa qualquer arquivo suportado ao PDF de saída (genérico)."""
    ext = os.path.splitext(file_path)[1].lower()
    handler = HANDLERS.get(ext)
    if handler is None:
        raise ValueError(f"Formato não suportado: {ext}")
    handler(writer, file_path)
```

## 🛠 Passo 1: Definir a Identidade (ToolKey)

**Arquivo:** `core/enum/ToolKey.py`

```python
class ToolKey(str, Enum):
    ...
    PDF_MERGE = "PdfMerge"
```

> A chave **deve** ser idêntica ao `tool_key` passado no `super().__init__()` do plugin.

## 📦 Passo 2: Dependência — `pypdf`

O `pypdf` (sucessor mantido do PyPDF2) **não está** em `requirements.txt` atualmente.
Adicione-o (Contrato 8 — toda dependência nova DEVE ser registrada):

```txt
# requirements.txt
pypdf
```

- Importe **dentro dos métodos** (lazy), nunca no topo do módulo — mantém o carregamento
  do plugin rápido (coerente com o Lazy Loading do `ToolRegistry`).

Uso básico:

```python
from pypdf import PdfWriter

writer = PdfWriter()
writer.append("a.pdf")         # anexa todas as páginas de a.pdf
writer.append("b.pdf")
print(len(writer.pages))       # total de páginas
with open("merged.pdf", "wb") as f:
    writer.write(f)
```

## 🔢 Passo 3: Filtro de extensões da entrada

O `FileListView` filtra por um dict estilo `DictManager` (`PDF_FILTER` acima).
**Não** passe `preview_widget`: o `PreviewPanel` só tem handlers para
`IMAGE_EXTENSIONS` e `TEXT_EXTENSIONS` — `.pdf` não cobre, então só use o widget de
preview quando um handler de PDF for criado futuramente.

**Evolução futura (imagens):** o filtro vira a união dos formatos suportados:

```python
filtro_merge = {**PDF_FILTER, **{k: v for k, v in IMAGE_EXTENSIONS.items() if k in (".png", ".jpg", ".jpeg")}}
```

**Seleção da pasta de saída — `GridComplexSelector` (e NUNCA `SimpleSelector`):**
`SimpleSelector` está **DEPRECATED** no `SKILL_WIDGETS.md` — plugins devem usar
`GridComplexSelector` com um selector `mode_type="output"`:

```python
self._sel_saida = GridComplexSelector(
    {
        "Saída": {
            "mode_type": "output",
            "file_filter": "PDF (*.pdf)",
            "allow_folder": True,
            "allow_file": False,
            "multiple": False,
            "show_suggest_button": True,   # 📂 gera root/subfolder
            "subfolder": "pdfmerge",
            "placeholder": "Onde salvar o PDF mesclado...",
        },
    },
    title="Pasta de Saída",
)
main_layout.addWidget(self._sel_saida)
```

- Acesso: `self._sel_saida["Saída"].path()` (path atual) e `.get_selected_list()`.
- O 📂 (suggest button) usa `ProjectUtil.get_root_folder()` + `subfolder` — ideal para
  projetos `.mtl`.
- Restauração: `self._sel_saida["Saída"].set_path(path)` (nunca sobrescrever `on_path_change`).

## 🏗 Passo 4: Implementar o Widget

**Arquivo:** `plugins/pdf_merge/PdfMergePlugin.py`

Estrutura/layout seguindo o **Contrato 18** (botões no header do `PluginPage`, via
`buttons_config` — **não** crie `ExecutionButtons` manualmente):

```
Título → Badge → [stretch] → [MESCLAR]
┌─ Arquivos (stretch 1 — ancho completo) ───┐
│ FileListView (PDFs)                        │   ← reordenação por drag & drop
└────────────────────────────────────────────┘
┌─ Opções ───────────┐ ┌─ Pasta de Saída ────────────┐
│ ☑ Separador A4     │ │ GridComplexSelector "Saída" │
└────────────────────┘ └─────────────────────────────┘
```

```python
# -*- coding: utf-8 -*-
"""
PdfMergePlugin — Mescla PDFs em um único PDF agrupado (v1)
===========================================================
Arquitetura genérica de merge: um registry de handlers por extensão
(HANDLERS) anexa cada arquivo ao PdfWriter de saída. A UI é igual para
qualquer formato suportado.

Contratos seguidos:
  - Contrato 11: widgets reutilizáveis (FileListView, GridCheckBox, GridComplexSelector...)
  - Contrato 18: ExecutionButtons via buttons_config no header do PluginPage
  - Contrato 20: SignalManager para progresso e console
"""
from __future__ import annotations

import os

from PySide6.QtCore import QTimer

from core.enum.ToolKey import ToolKey
from core.manager.SignalManager import SignalManager
from core.ui.HudCircularRingsLoader import HudCircularRingsLoader
from plugins.BasePlugin import BasePlugin
from resources.widgets.FileListView import FileListView
from resources.widgets.GroupPainel import GroupPainel
from resources.widgets.complex.GridComplexSelector import GridComplexSelector
from resources.widgets.grid.GridCheckBox import GridCheckBox
from resources.widgets.grid.GridGroupPainel import GridGroupPainel
from utils.ExplorerUtils import ExplorerUtils
from utils.MessageBox import MessageBox


class PdfMergePlugin(BasePlugin):

    def __init__(self, parent=None):
        super().__init__(
            tool_key=ToolKey.PDF_MERGE.value,
            parent=parent,
            sys_prefs=True,
            title="Merge PDF",
            buttons_config={
                "merge": {
                    "text": "MESCLAR",
                    "callback": self._on_merge,
                    "type": "primary",
                    "description": "Gera um único PDF com todos os arquivos da lista",
                },
            },
        )
        self.logger.info("Merge PDF inicializado", code="PDF_MERGE_READY")
        self.page.set_badge(self.page.PRONTA)

    def _build_ui(self):
        super()._build_ui()

        self._loader = HudCircularRingsLoader(self)
        self._loader.setGeometry(0, 0, self.width(), self.height())

        # ── Lista de arquivos (somente PDFs na v1) ───────────────────
        self._file_list = FileListView(file_filter=PDF_FILTER)  # sem preview (v1)
        self._file_list.files_changed.connect(self._on_files_changed)

        grp_arquivos = GroupPainel("Arquivos")
        grp_arquivos.group_layout.addWidget(self._file_list)
        # Panel ÚNICO → va directo al layout para ocupar TODO el width
        # (GridGroupPainel con 1 solo panel deja una columna 2 vacía a la derecha)
        self.main_layout.addWidget(grp_arquivos, 1)

        # ── Opções ──────────────────────────────────────────────────
        self._grid_opts = GridCheckBox(
            config={
                "separator": {
                    "label": "Página em branco entre arquivos",
                    "description": "Insere uma página A4 vazia entre cada PDF",
                    "default": False,
                },
            },
            num_columns=1,
        )
        grp_opts = GroupPainel("Opções")
        grp_opts.group_layout.addWidget(self._grid_opts)

        # ── Pasta de Saída — GridComplexSelector (output) ───────────
        self._sel_saida = GridComplexSelector(
            {
                "Saída": {
                    "mode_type": "output",
                    "file_filter": "PDF (*.pdf)",
                    "allow_folder": True,
                    "allow_file": False,
                    "multiple": False,
                    "show_suggest_button": True,
                    "subfolder": "pdfmerge",
                    "placeholder": "Onde salvar o PDF mesclado...",
                },
            },
        )
        grp_saida = GroupPainel("Pasta de Saída")
        grp_saida.group_layout.addWidget(self._sel_saida)

        # Opções + Saída lado a lado (2 paneles → sí usamos GridGroupPainel)
        self.main_layout.addWidget(GridGroupPainel(grp_opts, grp_saida))

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._loader.setGeometry(0, 0, self.width(), self.height())

    # ── Signals ─────────────────────────────────────────────────────

    def _on_files_changed(self, count: int):
        if count > 0:
            self.page.set_badge(self.page.PRONTA)

    # ── Merge ───────────────────────────────────────────────────────

    def _on_merge(self):
        paths = self._file_list.get_ordered_paths()
        if not paths:
            MessageBox.show_warning("Nenhum PDF na lista.", title="Aviso")
            return

        output_dir = self._sel_saida["Saída"].path()
        if not output_dir:
            MessageBox.show_warning("Selecione a pasta de saída.", title="Aviso")
            return

        result = MessageBox.show_question(
            f"Mesclar {len(paths)} PDF(s) em um único arquivo?\nPasta: {output_dir}",
            title="Confirmar",
        )
        if result != MessageBox.YES:
            self.logger.info("Merge cancelado", code="PDF_MERGE_CANCELLED")
            return

        self.logger.info("Iniciando merge", code="PDF_MERGE_START", count=len(paths))
        SignalManager.instance().console_message.emit(f"Mesclando {len(paths)} PDF(s)...")
        self.page.set_badge(self.page.RUNNING)
        self.page.buttons.set_enabled("merge", False)
        self._loader.set_progress(0, "Mesclando PDFs...")
        self._loader.show_loader()
        QTimer.singleShot(0, lambda: self._run_merge(paths, output_dir))

    def _run_merge(self, paths, output_dir):
        from pypdf import PdfWriter   # lazy (mantém startup rápido)

        total = len(paths)
        total_pages = 0
        err_count = 0
        base_inicial = os.path.splitext(os.path.basename(paths[0]))[0]
        base_final = os.path.splitext(os.path.basename(paths[-1]))[0]
        out_path = os.path.join(output_dir, f"{base_inicial}_a_{base_final}.pdf")

        try:
            writer = PdfWriter()
            for idx, pdf_path in enumerate(paths, start=1):
                try:
                    count_before = len(writer.pages)
                    self._append_file(writer, pdf_path)   # dispatcher genérico
                    total_pages += len(writer.pages) - count_before
                    if self._grid_opts.is_item_checked("separator"):
                        writer.add_blank_page(width=595.28, height=841.89)  # A4 pts
                    self.logger.info(f"Anexado: {pdf_path}", code="PDF_MERGE_APPENDED")
                except Exception as e:
                    err_count += 1
                    self.logger.error(
                        f"Falha ao anexar {pdf_path}",
                        code="PDF_MERGE_APPEND_ERR",
                        error=str(e),
                    )
                    SignalManager.instance().console_message.emit(
                        f"Erro: {os.path.basename(pdf_path)} — {e}"
                    )

                pct = (idx / total) * 100.0
                SignalManager.instance().progress_update.emit(pct)
                self._loader.set_progress(pct, f"Mesclando {idx}/{total}...")

            ExplorerUtils.ensure_directory(output_dir)
            with open(out_path, "wb") as f:
                writer.write(f)

            self.logger.info(
                "Merge finalizado",
                code="PDF_MERGE_DONE",
                ok=total - err_count,
                pages=total_pages,
            )
            SignalManager.instance().console_message.emit(
                f"Merge concluído: {total - err_count} PDF(s), {total_pages} página(s)."
            )

            if err_count == 0:
                self.success_message(
                    output_path=out_path,
                    label="Arquivo PDF",
                    summary="PDF mesclado gerado!",
                    n_input=total,
                    n_output=total_pages,
                    n_arquivos=total - err_count,
                )
            else:
                self.page.set_badge(self.page.ERROR)
                MessageBox.show_warning(f"Concluído com {err_count} erro(s).", title="Aviso")
        except Exception as e:
            self.logger.error("Erro fatal no merge", code="PDF_MERGE_FATAL", error=str(e))
            SignalManager.instance().console_message.emit(f"Erro fatal: {e}")
            self.page.set_badge(self.page.ERROR)
        finally:
            self._loader.hide_loader()
            self.page.buttons.set_enabled("merge", True)
            SignalManager.instance().progress_update.emit(0.0)
            self.save_prefs()

    # ── Handlers de formato (genérico) ──────────────────────────────

    @staticmethod
    def _append_pdf(writer, pdf_path: str) -> None:
        """Handler v1 — anexa todas as páginas de um PDF."""
        writer.append(pdf_path)

    def _append_file(self, writer, file_path: str) -> None:
        """Dispatcher genérico: resolve o handler pela extensão."""
        ext = os.path.splitext(file_path)[1].lower()
        handler = HANDLERS.get(ext)
        if handler is None:
            raise ValueError(f"Formato não suportado: {ext}")
        handler(writer, file_path)

    # ── Preferências (Contrato 6 — obrigatório) ─────────────────────

    def load_prefs(self):
        paths = self.preferences.get("paths", [])
        if paths:
            self._file_list.add_files(paths)   # dispara files_changed sozinho
        out = self.preferences.get("output_dir", "")
        if out:
            self._sel_saida["Saída"].set_path(out)
        opts = self.preferences.get("options", {})
        if opts:
            self._grid_opts.set_all(opts)

    def save_prefs(self):
        self.preferences["paths"] = self._file_list.get_ordered_paths()  # ordem atual
        self.preferences["output_dir"] = self._sel_saida["Saída"].path()
        self.preferences["options"] = self._grid_opts.all
```

> ⚠️ **Cuidado com signal chain na restauração** (vale para `GridComplexSelector` e `FileListView`):
> - `self._sel_saida["Saída"].set_path(saved_path)` já dispara os handlers internos de
>   linking — **nunca** sobrescreva `on_path_change` nem chame callbacks manualmente.
> - Para `set_path` sem re-avaliação: `saved = grid.suspend_callbacks()` → `set_path()`
>   → `grid.resume_callbacks(saved)` (API pública do `GridComplexSelector`).
> - `_file_list.add_files(paths)` já emite `files_changed` — não precisa de chamada extra.
> - Se a ferramenta tiver modos (arquivo/pasta), salve **ambos** os paths no `save_prefs()`,
>   preservando o do outro modo (não sobrescreva com vazio).

## 🔗 Passo 5: Registrar no ToolRegistry

**Arquivo:** `core/config/ToolRegistry.py` (dict `_TOOLS`)

```python
# Dentro do dict `_TOOLS` do ToolRegistry
ToolKey.PDF_MERGE.value: Tool(
    name=ToolKey.PDF_MERGE.value,
    title="Merge PDF",
    widget_factory=_make_factory(
        "plugins.pdf_merge.PdfMergePlugin", "PdfMergePlugin"
    ),
    tooltip="Mescla PDFs em um único arquivo PDF agrupado",
    tool_type=ToolType.FOLDER,      # grupo de documentos na toolbar (como Docling)
    category=CategoryTool.CENTRAL,  # aba no workspace central
    show_in_toolbar=True,
)
```

## 🎨 Passo 6: Ícone (Opcional)

Adicione `resources/icons/PdfMerge.ico` — o `IconManager` encontra automaticamente pelo
nome da ToolKey. O `MenuManager` lê o `ToolType` do registro para posicionar o botão.

## 💬 Passo 7: Mensagens Padronizadas

Use os helpers do `BasePlugin` no fim do merge (ver `_run_merge` acima):

- `self.stats_message(n_arquivos=..., n_processed=..., ntype="páginas")` — resumo com tempo
  (usa o `ProcessStatisticsUtil` interno do `BasePlugin`).
- `self.output_message(out_path, label="Arquivo PDF")` — link clicável no Explorer
  (sempre passe o **diretório** via `os.path.dirname(out_path)`).
- `self.success_message(...)` — combina ambos + `execution_finished` + `MessageBox.show_info`.

**Regras de log/console:**
- NÃO emita o nome da ferramenta no início da mensagem de console (o ConsolePlugin já mostra).
- Erros sempre com `code=` e `error=str(e)` no logger.

## 🔄 Passo 8: Execução Longa / Progresso

O padrão acima (`QTimer.singleShot` + `HudCircularRingsLoader` + `progress_update`)
é suficiente para merges de dezenas de PDFs. Se a ferramenta for processar volumes
grandes, use a **Async Pipeline** (`BaseStep`/`BaseTask`) em `core/papeline/` — consulte
`docs/skills/SKILL_ASYNC_PIPELINE.md` e `docs/skills/SKILL_HUD_PROGRESS.md`.

## 🔮 Evolução futura: Merge genérico (imagens → PDF)

Com a arquitetura de handlers, adicionar imagens é trivial:

```python
def _append_image(writer, image_path: str) -> None:
    """Converte uma imagem em página PDF. Pillow já está em requirements.txt."""
    from io import BytesIO

    from PIL import Image
    from pypdf import PdfReader

    img = Image.open(image_path).convert("RGB")
    buffer = BytesIO()
    img.save(buffer, format="PDF")
    buffer.seek(0)
    writer.append(PdfReader(buffer))
```

Depois basta:
1. adicionar as extensões de imagem ao **filtro** do `FileListView`;
2. registrar `".png": _append_image, ".jpg": _append_image, ...` no dict `HANDLERS`.

A UI, as preferências e o registro no `ToolRegistry` permanecem inalterados — o
dispatcher `_append_file()` resolve o handler pela extensão. **Isso torna a ferramenta
um merge genérico de arquivos gerando um PDF agrupado.**

## ✅ Checklist de Verificação

- [ ] `ToolKey.PDF_MERGE` adicionado e idêntico ao `tool_key` no `super().__init__()`.
- [ ] `pypdf` adicionado ao `requirements.txt` (Contrato 8).
- [ ] `buttons_config` no `super().__init__()` — **sem** `ExecutionButtons` manual (Contrato 18).
- [ ] Widgets de `resources/widgets/` consultados em `SKILL_WIDGETS.md` (Contrato 11).
- [ ] Pasta de saída via `GridComplexSelector` (`mode_type="output"`) — **nunca** `SimpleSelector` (DEPRECATED).
- [ ] **Sem** `QMessageBox` / `QFileDialog` diretos (Contratos 1 e 17).
- [ ] Todo `except` tem `as e` + logger (Contrato 2).
- [ ] `load_prefs()` e `save_prefs()` implementados (Contrato 6).
- [ ] Logs nos pontos críticos (init, início/fim do merge, erros).
- [ ] Mensagens padrão: `success_message()` / `output_message()` / `stats_message()`.
- [ ] Módulo registrado em `_TOOLS` com `_make_factory("plugins.pdf_merge.PdfMergePlugin", "PdfMergePlugin")`.
- [ ] `CategoryTool.CENTRAL` + `ToolType.FOLDER`.
- [ ] Documentação atualizada (Contrato 12) — nova skill; se criar widget novo: `SKILL_WIDGETS.md`.
- [ ] Changelog atualizado em `docs/data/changelog.txt`.

## 🧪 Validação (NUNCA importe widgets fora de QApplication)

**NUNCA** rode no terminal:

```powershell
python -c "from PySide6.QtWidgets import ..."        # ❌ TRAVA o Qt
python -c "from resources.widgets.X import ..."      # ❌ TRAVA o Qt
python -c "from plugins.pdf_merge.PdfMergePlugin import PdfMergePlugin"  # ❌ TRAVA o Qt
```

Use verificação **sintática** (segura) ou o app real:

```powershell
python -c "import ast; ast.parse(open(r'plugins/pdf_merge/PdfMergePlugin.py', encoding='utf-8').read()); print('OK')"
python main.py   # teste funcional completo com QApplication
```

---

> 💡 **Consulte também:** `SKILL_CREATE_TOOL.md` (fluxo completo de plugins e ferramentas INSTANT),
> `SKILL_PREFERENCES.md` (persistência), `SKILL_COMUNICATION.md` (SignalManager).