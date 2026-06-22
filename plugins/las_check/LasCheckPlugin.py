# -*- coding: utf-8 -*-
"""
LasCheckPlugin — Ferramenta de verificação de qualidade em nuvens LAS/LAZ
==========================================================================
Executa 8 checks de qualidade em arquivos LAS/LAZ e exibe relatório
consolidado com status (✅ pass / ⚠️ warning / ❌ fail / ⏭️ skipped).

Fluxo:
  - SelectorGrid de entrada detecta mudança no path automaticamente
  - GridCheckBox para selecionar quais checks executar
  - ExecutionButtons: EXECUTAR + EXPORTAR RELATÓRIO
  - PipelineRunner + LasCheckStep para execução em background
  - GridLabel para resultados compactos + ReadOnlyTextBrowser para relatório
"""

from __future__ import annotations

import os
import traceback
from datetime import datetime

from core.enum.ToolKey import ToolKey
from core.manager.SignalManager import SignalManager
from core.papeline.PipelineRunner import PipelineRunner
from core.papeline.step import LasCheckStep
from plugins.BasePlugin import BasePlugin
from resources.widgets.ExecutionButtons import ExecutionButtons
from resources.widgets.GridCheckBox import GridCheckBox
from resources.widgets.GridLabel import GridLabel
from resources.widgets.GroupPainel import GroupPainel
from resources.widgets.ReadOnlyTextBrowser import ReadOnlyTextBrowser
from resources.widgets.SelectorGrid import SelectorGrid
from utils.ExplorerUtils import ExplorerUtils
from utils.JsonUtil import JsonUtil
from utils.LasUtil import LasUtil
from utils.MessageBox import MessageBox


# ── Configuração dos checks ─────────────────────────────────────────────
CHECK_CONFIG: dict[str, dict] = {
    "point_count": {
        "label": "Contagem de Pontos",
        "description": "Verifica se ha pontos suficientes (> 0)",
        "default": True,
    },
    "bbox": {
        "label": "Bounding Box",
        "description": "Verifica se a bbox tem dimensoes validas",
        "default": True,
    },
    "rgb": {
        "label": "Bandas RGB",
        "description": "Verifica presenca de bandas RGB",
        "default": True,
    },
    "classification": {
        "label": "Classificacao",
        "description": "Verifica codigos de classificacao LAS (0-255)",
        "default": True,
    },
    "zero_coords": {
        "label": "Coordenadas Zero",
        "description": "Verifica pontos com X=Y=Z=0",
        "default": True,
    },
    "duplicates": {
        "label": "Duplicatas XY",
        "description": "Verifica duplicatas de coordenadas XY",
        "default": True,
    },
    "density": {
        "label": "Densidade / Gaps",
        "description": "Calcula densidade de pontos por area",
        "default": True,
    },
    "intensity": {
        "label": "Intensidade",
        "description": "Verifica range de intensidade (0-65535)",
        "default": True,
    },
}

CHECK_NAMES: dict[str, str] = {
    "point_count": "Contagem de Pontos",
    "bbox": "Bounding Box",
    "rgb": "Bandas RGB",
    "classification": "Classificacao",
    "zero_coords": "Coordenadas Zero",
    "duplicates": "Duplicatas XY",
    "density": "Densidade / Gaps",
    "intensity": "Intensidade",
}

STATUS_ICONS: dict[str, str] = {
    "pass": "✅",
    "warning": "⚠️",
    "fail": "❌",
    "skipped": "⏭️",
}

STATUS_LABELS: dict[str, str] = {
    "pass": "APROVADO",
    "warning": "ATENCAO",
    "fail": "FALHA",
    "skipped": "PULADO",
}


class LasCheckPlugin(BasePlugin):
    """
    Plugin para verificar qualidade de nuvens LAS/LAZ.
    """

    _LAS_FILTER = "LAS/LAZ (*.las *.laz)"

    def __init__(self, parent=None):
        self._current_path: str = ""
        self._las_info: dict = {}
        self._runner: PipelineRunner | None = None
        self._check_results: dict | None = None
        super().__init__(
            tool_key=ToolKey.LAS_CHECK.value,
            parent=parent,
            title="LAS Quality Check",
        )
        self.logger.info("Ferramenta inicializada", code="LASCHECK_READY")

    # ══════════════════════════════════════════════════════════════════
    # UI
    # ══════════════════════════════════════════════════════════════════

    def _build_ui(self):
        """Constrói a interface completa do plugin."""
        super()._build_ui()

        # ── ExecutionButtons ────────────────────────────────────────
        self._btns = ExecutionButtons(self, {
            "executar": {
                "text": "EXECUTAR",
                "callback": self._on_executar,
                "type": "primary",
                "description": "Executar checks de qualidade",
            },
            "exportar": {
                "text": "EXPORTAR RELATORIO",
                "callback": self._on_exportar,
                "type": "secondary",
                "description": "Exportar relatorio para arquivo",
            },
        })
        self._btns.set_enabled("executar", False)
        self._btns.set_enabled("exportar", False)
        self.main_layout.addWidget(self._btns)

        # ── GroupPainel "Arquivo de Entrada" ────────────────────────
        grupo_entrada = GroupPainel("Arquivo de Entrada")
        self.main_layout.addWidget(grupo_entrada)

        self._selector_grid = SelectorGrid(
            {
                "LAS/LAZ de Entrada": {
                    "file_filter": self._LAS_FILTER,
                    "browse_mode": "open_file",
                    "placeholder": "Selecione o arquivo LAS/LAZ...",
                },
            },
        )
        grupo_entrada.group_layout.addWidget(self._selector_grid)

        sel_entrada = self._selector_grid["LAS/LAZ de Entrada"]
        sel_entrada.edit.textChanged.connect(self._on_input_path_changed)

        self._info_label = GridLabel(
            {
                "pontos": {"label": "Total de Pontos", "value": "—"},
                "has_rgb": {"label": "Possui RGB", "value": "—"},
                "bbox": {"label": "Bounding Box", "value": "—"},
            },
            columns=1,
        )
        grupo_entrada.group_layout.addWidget(self._info_label)

        # ── GroupPainel "Checks" ────────────────────────────────────
        grupo_checks = GroupPainel("Checks")
        self.main_layout.addWidget(grupo_checks)

        self._grid_checks = GridCheckBox(CHECK_CONFIG, num_columns=2)
        grupo_checks.group_layout.addWidget(self._grid_checks)

        # ── GroupPainel "Resultados" ────────────────────────────────
        grupo_result = GroupPainel("Resultados")
        self.main_layout.addWidget(grupo_result)

        self._result_label = GridLabel(
            {
                "point_count": {"label": "Contagem de Pontos", "value": "—"},
                "bbox": {"label": "Bounding Box", "value": "—"},
                "rgb": {"label": "Bandas RGB", "value": "—"},
                "classification": {"label": "Classificacao", "value": "—"},
                "zero_coords": {"label": "Coordenadas Zero", "value": "—"},
                "duplicates": {"label": "Duplicatas XY", "value": "—"},
                "density": {"label": "Densidade / Gaps", "value": "—"},
                "intensity": {"label": "Intensidade", "value": "—"},
            },
            columns=1,
        )
        grupo_result.group_layout.addWidget(self._result_label)

        # ── ReadOnlyTextBrowser (relatório detalhado) ───────────────
        self._report_browser = ReadOnlyTextBrowser(
            placeholder="Relatorio detalhado aparecera aqui apos a execucao...",
        )
        self.main_layout.addWidget(self._report_browser)

        self.page.set_badge(self.page.PRONTA)

    # ══════════════════════════════════════════════════════════════════
    # Handlers
    # ══════════════════════════════════════════════════════════════════

    def _on_input_path_changed(self, text: str):
        """Disparado quando o texto do selector de entrada muda."""
        path = text.strip()
        if not path:
            return
        ext = os.path.splitext(path)[1].lower()
        if ext not in (".las", ".laz") or not os.path.isfile(path):
            return
        if getattr(self, "_loading_las", False):
            return
        if path == self._current_path:
            return
        self._carregar_las(path)

    def _on_executar(self):
        """Executa os checks de qualidade via PipelineRunner em background."""
        if self._runner is not None and self._runner.isRunning():
            MessageBox.show_warning(
                "Ja existe uma verificacao em andamento.", title="Aguarde"
            )
            return

        if not self._current_path:
            MessageBox.show_warning(
                "Nenhum arquivo LAS carregado.", title="LAS Quality Check",
            )
            return

        checks_enabled = self._grid_checks.checked
        if not checks_enabled:
            MessageBox.show_warning(
                "Selecione ao menos um check para executar.",
                title="LAS Quality Check",
            )
            return

        # Prepara UI para execução
        self._btns.set_all_enabled(False)
        self._btns.set_enabled("exportar", False)
        self.page.set_badge(self.page.RUNNING)
        self._report_browser.clear_content()

        # Reseta resultados
        for key in CHECK_NAMES:
            self._result_label.set(key, "—")

        n_checks = len(checks_enabled)

        SignalManager.instance().execution_started.emit(self.tool_key)
        SignalManager.instance().hud_show.emit({
            "message": "Verificando nuvem de pontos...",
            "stages": [30.0, 8],
        })
        SignalManager.instance().console_message.emit(
            f"[LasCheck] Iniciando {n_checks} checks em: "
            f"{os.path.basename(self._current_path)}"
        )

        self.logger.info(
            "Iniciando checks",
            code="LASCHECK_EXEC_START",
            path=self._current_path,
            checks=list(checks_enabled.keys()),
        )

        # Cria e inicia a pipeline em background
        step = LasCheckStep()
        runner = PipelineRunner(
            steps=[step],
            context={
                "file_path": self._current_path,
                "checks_enabled": checks_enabled,
                "tool_key": self.tool_key,
            },
            parent=self,
        )
        runner.finished_ok.connect(self._on_done)
        runner.failed.connect(self._on_error)
        runner.finished.connect(self._on_runner_finished)
        self._runner = runner
        runner.start()

    def _on_exportar(self):
        """Exporta o relatório para arquivo .txt ou .json."""
        if not self._check_results:
            MessageBox.show_warning(
                "Nenhum resultado para exportar.\nExecute os checks primeiro.",
                title="LAS Quality Check",
            )
            return

        path = ExplorerUtils.save_file(
            "Exportar Relatorio",
            filter="Texto (*.txt);;JSON (*.json)",
            parent=self,
        )
        if not path:
            return

        try:
            ext = os.path.splitext(path)[1].lower()
            if ext == ".json":
                JsonUtil.write_json(path, self._check_results)
            else:
                report = self._gerar_relatorio_texto()
                with open(path, "w", encoding="utf-8") as f:
                    f.write(report)

            self.logger.info(
                "Relatorio exportado",
                code="LASCHECK_EXPORT",
                path=path,
            )
            SignalManager.instance().console_message.emit(
                f"[LasCheck] Relatorio exportado: {path}"
            )
            MessageBox.show_info(
                f"Relatorio exportado com sucesso:\n{path}",
                title="LAS Quality Check",
            )

        except Exception as e:
            self.logger.error(
                "Erro ao exportar relatorio",
                code="LASCHECK_EXPORT_ERR",
                error=str(e),
            )
            MessageBox.show_error(
                f"Erro ao exportar relatorio:\n{str(e)}",
                title="LAS Quality Check",
            )

    # ══════════════════════════════════════════════════════════════════
    # Callbacks da Pipeline
    # ══════════════════════════════════════════════════════════════════

    def _on_done(self, context):
        """Callback de sucesso da pipeline."""
        results = context.get("check_results", {})
        summary = context.get("summary", {})

        self._check_results = {
            "file_path": self._current_path,
            "timestamp": datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
            "summary": summary,
            "results": results,
        }

        pass_count = summary.get("pass", 0)
        warn_count = summary.get("warning", 0)
        fail_count = summary.get("fail", 0)
        total = summary.get("total", 0)

        # Atualiza GridLabel com resultados
        for check_name, result in results.items():
            status = result.get("status", "skipped")
            icon = STATUS_ICONS.get(status, "—")
            message = result.get("message", "")
            self._result_label.set(check_name, f"{icon} {message}")

        # Gera relatório detalhado no ReadOnlyTextBrowser
        report = self._gerar_relatorio_texto()
        self._report_browser.append_html(f"<pre>{report}</pre>")

        # Habilita exportar
        self._btns.set_enabled("exportar", True)

        SignalManager.instance().execution_finished.emit(self.tool_key)
        SignalManager.instance().console_message.emit(
            f"[LasCheck] Checks concluidos! "
            f"{pass_count} ✅, {warn_count} ⚠️, {fail_count} ❌"
        )

        self.logger.info(
            "Checks concluidos com sucesso",
            code="LASCHECK_EXEC_DONE",
            pass_count=pass_count,
            warn_count=warn_count,
            fail_count=fail_count,
            total=total,
        )

        # Notifica o usuário se houver falhas
        if fail_count > 0:
            MessageBox.show_warning(
                f"Checks concluidos com {fail_count} falha(s)!\n\n"
                f"{pass_count} ✅ aprovados\n"
                f"{warn_count} ⚠️ atencao\n"
                f"{fail_count} ❌ falhas\n\n"
                f"Consulte o relatorio detalhado para mais informacoes.",
                title="LAS Quality Check",
            )
        else:
            MessageBox.show_info(
                f"Checks concluidos!\n\n"
                f"{pass_count} ✅ aprovados\n"
                f"{warn_count} ⚠️ atencao\n"
                f"{fail_count} ❌ falhas",
                title="LAS Quality Check",
            )

    def _on_error(self, message: str):
        """Callback de erro da pipeline."""
        SignalManager.instance().execution_cancelled.emit(self.tool_key)
        SignalManager.instance().console_message.emit(
            f"[LasCheck] ERRO: {message}"
        )
        self.logger.error(
            "Erro nos checks",
            code="LASCHECK_EXEC_ERR",
            error=message,
            path=self._current_path,
        )
        MessageBox.show_error(
            f"Erro durante os checks:\n{message}",
            title="LAS Quality Check",
        )

    def _on_runner_finished(self):
        """Callback executado ao final da pipeline (sucesso ou erro)."""
        self._runner = None
        self._btns.set_all_enabled(True)
        self._btns.set_enabled("executar", bool(self._current_path))
        self.page.set_badge(self.page.PRONTA)
        SignalManager.instance().hud_hide.emit()
        SignalManager.instance().progress_update.emit(0.0)

    # ══════════════════════════════════════════════════════════════════
    # Utilitários
    # ══════════════════════════════════════════════════════════════════

    def _carregar_las(self, path: str):
        """Carrega metadados do LAS e atualiza a UI."""
        if getattr(self, "_loading_las", False):
            return
        self._loading_las = True

        self.logger.info("Carregando LAS", code="LASCHECK_LAS_LOAD", path=path)

        try:
            info = LasUtil.get_info(path, tool_key=self.tool_key)
            if info.get("error"):
                raise RuntimeError(info["error"])

            n_pontos = info["point_count"]
            has_rgb = info["has_rgb"]

            self._current_path = path
            self._las_info = {
                "path": path,
                "n_pontos": n_pontos,
                "has_rgb": has_rgb,
            }

            # Atualiza UI com bloqueio de sinais
            sel_entrada = self._selector_grid["LAS/LAZ de Entrada"]
            sel_entrada.edit.blockSignals(True)
            sel_entrada.set_path(path)
            sel_entrada.edit.blockSignals(False)

            self._info_label.set("pontos", f"{n_pontos:,}")
            self._info_label.set("has_rgb", "Sim" if has_rgb else "Nao")

            bbox = LasUtil.get_bounding_box(path, tool_key=self.tool_key)
            if bbox:
                self._info_label.set(
                    "bbox",
                    f"X[{bbox['x_min']:.1f}, {bbox['x_max']:.1f}] "
                    f"Y[{bbox['y_min']:.1f}, {bbox['y_max']:.1f}]",
                )
            else:
                self._info_label.set("bbox", "—")

            self._btns.set_enabled("executar", True)
            self.page.set_badge(self.page.PRONTA)

            SignalManager.instance().console_message.emit(
                f"[LasCheck] Carregado: {os.path.basename(path)} "
                f"({n_pontos:,} pontos)"
            )

            self.logger.info(
                "LAS carregado",
                code="LASCHECK_LAS_LOADED",
                path=path,
                points=n_pontos,
                has_rgb=has_rgb,
            )

        except Exception as e:
            self.logger.error(
                "Erro ao carregar LAS",
                code="LASCHECK_LAS_LOAD_ERR",
                error=str(e),
                path=path,
            )
            self.page.set_badge(self.page.ERROR)
            MessageBox.show_error(
                f"Erro ao carregar arquivo LAS:\n{str(e)}",
                title="LAS Quality Check",
                detail=traceback.format_exc(),
            )
        finally:
            self._loading_las = False

    def _gerar_relatorio_texto(self) -> str:
        """Gera relatório em texto puro a partir dos resultados."""
        if not self._check_results:
            return "Nenhum resultado disponivel."

        data = self._check_results
        lines = []
        lines.append("=" * 60)
        lines.append("          LAS QUALITY CHECK REPORT")
        lines.append("=" * 60)
        lines.append(f"Arquivo:  {data.get('file_path', '—')}")
        lines.append(f"Data:     {data.get('timestamp', '—')}")
        lines.append("")

        summary = data.get("summary", {})
        pass_c = summary.get("pass", 0)
        warn_c = summary.get("warning", 0)
        fail_c = summary.get("fail", 0)
        total = summary.get("total", 0)
        lines.append(f"Resumo:   {pass_c} ✅  {warn_c} ⚠️  {fail_c} ❌  (total: {total})")
        lines.append("")

        results = data.get("results", {})
        for check_name, result in results.items():
            display = CHECK_NAMES.get(check_name, check_name)
            status = result.get("status", "skipped")
            icon = STATUS_ICONS.get(status, "—")
            label = STATUS_LABELS.get(status, status.upper())
            message = result.get("message", "")
            suggestion = result.get("suggestion", "")

            lines.append(f"  {icon} [{label}] {display}")
            lines.append(f"     {message}")
            if suggestion:
                lines.append(f"     Sugestao: {suggestion}")
            lines.append("")

        lines.append("=" * 60)
        lines.append("Fim do relatorio")
        lines.append("=" * 60)
        return "\n".join(lines)

    # ══════════════════════════════════════════════════════════════════
    # Preferências
    # ══════════════════════════════════════════════════════════════════

    def load_prefs(self) -> None:
        """Carrega preferências salvas."""
        self.logger.info("Carregando preferencias", code="LASCHECK_PREFS_LOAD")
        last_path = self.preferences.get("last_path", "")
        checks_enabled = self.preferences.get("checks_enabled", {})

        # Carrega o LAS primeiro
        if last_path:
            self._carregar_las(last_path)

        # Restaura checks habilitados
        if checks_enabled:
            self._grid_checks.set_all(checks_enabled)

        self.logger.info("Preferencias carregadas", code="LASCHECK_PREFS_LOADED")

    def save_prefs(self) -> None:
        """Salva preferências atuais no cache de memória."""
        self.preferences["last_path"] = self._current_path
        self.preferences["checks_enabled"] = self._grid_checks.all
        self.logger.info("Preferencias salvas no cache", code="LASCHECK_PREFS_SAVED")