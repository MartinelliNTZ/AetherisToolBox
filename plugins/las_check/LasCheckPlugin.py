# -*- coding: utf-8 -*-
"""
LasCheckPlugin — Ferramenta de verificação de qualidade em nuvens LAS/LAZ
==========================================================================
Executa 8 checks de qualidade em arquivos LAS/LAZ e exibe dados
no GridLabel com valores compactos.

Fluxo:
  - SelectorGrid de entrada detecta mudança no path automaticamente
  - GridCheckBox para selecionar quais checks executar
  - ExecutionButtons: EXECUTAR
  - PipelineRunner + LasCheckStep para execução em background
  - GridLabel com todos os resultados
"""

from __future__ import annotations

import os
import traceback

from core.enum.ToolKey import ToolKey
from core.manager.SignalManager import SignalManager
from core.papeline.PipelineRunner import PipelineRunner
from core.papeline.step import LasCheckStep
from plugins.BasePlugin import BasePlugin
from resources.widgets.ExecutionButtons import ExecutionButtons
from resources.widgets.GridCheckBox import GridCheckBox
from resources.widgets.GridLabel import GridLabel
from resources.widgets.GroupPainel import GroupPainel
from resources.widgets.SelectorGrid import SelectorGrid
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


class LasCheckPlugin(BasePlugin):
    """
    Plugin para verificar qualidade de nuvens LAS/LAZ.
    """

    _LAS_FILTER = "LAS/LAZ (*.las *.laz)"

    def __init__(self, parent=None):
        self._current_path: str = ""
        self._las_info: dict = {}
        self._runner: PipelineRunner | None = None
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
        })
        self._btns.set_enabled("executar", False)
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
                "pontos": {"label": "Total Pontos", "value": "—"},
                "has_rgb": {"label": "RGB", "value": "—"},
                "bbox": {"label": "BBox", "value": "—"},
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
                "point_count": {"label": "Pontos", "value": "—"},
                "bbox": {"label": "BBox", "value": "—"},
                "rgb": {"label": "RGB", "value": "—"},
                "classification": {"label": "Classificacao", "value": "—"},
                "zero_coords": {"label": "Coord Zero", "value": "—"},
                "duplicates": {"label": "Duplicatas", "value": "—"},
                "density": {"label": "Densidade", "value": "—"},
                "intensity": {"label": "Intensidade", "value": "—"},
                "resumo": {"label": "Resumo", "value": "—"},
            },
            columns=2,
        )
        grupo_result.group_layout.addWidget(self._result_label)

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
        self.page.set_badge(self.page.RUNNING)

        # Reseta resultados
        for key in ("point_count", "bbox", "rgb", "classification",
                     "zero_coords", "duplicates", "density", "intensity", "resumo"):
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

        # Cria step que executa checks inline na QThread
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

    # ══════════════════════════════════════════════════════════════════
    # Callbacks da Pipeline
    # ══════════════════════════════════════════════════════════════════

    def _on_done(self, context):
        """Callback de sucesso da pipeline."""
        results = context.get("check_results", {})
        summary = context.get("summary", {})

        pass_count = summary.get("pass", 0)
        warn_count = summary.get("warning", 0)
        fail_count = summary.get("fail", 0)
        total = summary.get("total", 0)

        # Resumo
        self._result_label.set("resumo",
            f"{pass_count} ✅ {warn_count} ⚠️ {fail_count} ❌ ({total})")

        # Atualiza cada check apenas com o valor/mensagem (sem icone/rotulo)
        for check_name in ("point_count", "bbox", "rgb", "classification",
                           "zero_coords", "duplicates", "density", "intensity"):
            result = results.get(check_name)
            if not result:
                continue
            message = result.get("message", "")
            status = result.get("status", "")
            # Mostra apenas o dado, sem APROVADO/ATENCAO/FALHA
            if status == "skipped":
                self._result_label.set(check_name, "-")
            else:
                self._result_label.set(check_name, message)

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

        if fail_count > 0:
            MessageBox.show_warning(
                f"Checks concluidos com {fail_count} falha(s)!",
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
        # Exibe erro no GridLabel se for erro de LAZ
        if "LAZ" in message or "laz" in message:
            self._result_label.set("resumo", "❌ Erro LAZ - use .LAS")
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

    # ══════════════════════════════════════════════════════════════════
    # Preferências
    # ══════════════════════════════════════════════════════════════════

    def load_prefs(self) -> None:
        """Carrega preferências salvas."""
        self.logger.info("Carregando preferencias", code="LASCHECK_PREFS_LOAD")
        last_path = self.preferences.get("last_path", "")
        checks_enabled = self.preferences.get("checks_enabled", {})

        if last_path:
            self._carregar_las(last_path)

        if checks_enabled:
            self._grid_checks.set_all(checks_enabled)

        self.logger.info("Preferencias carregadas", code="LASCHECK_PREFS_LOADED")

    def save_prefs(self) -> None:
        """Salva preferências atuais no cache de memória."""
        self.preferences["last_path"] = self._current_path
        self.preferences["checks_enabled"] = self._grid_checks.all
        self.logger.info("Preferencias salvas no cache", code="LASCHECK_PREFS_SAVED")