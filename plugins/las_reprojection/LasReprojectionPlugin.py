# -*- coding: utf-8 -*-
"""
LasReprojectionPlugin — Ferramenta de Reprojeção de Nuvens LAS/LAZ
====================================================================
Permite reprojetar (transformar CRS) nuvens de pontos LAS/LAZ
com detecção automática do CRS de origem e seleção do CRS de destino.

Fluxo:
  - GridSelector para entrada (LAS/LAZ) e saída
  - CrsSelectorWidget para CRS de origem (auto-detectado)
  - CrsSelectorWidget para CRS de destino
  - ExecutionButtons: EXECUTAR
  - PipelineRunner + LasReprojectionStep para execução em background
  - GridLabel com metadados da reprojeção
"""

from __future__ import annotations

import os
import traceback

from core.enum.ToolKey import ToolKey
from core.manager.SignalManager import SignalManager
from core.papeline.PipelineRunner import PipelineRunner
from core.papeline.ExecutionContext import ExecutionContext
from plugins.BasePlugin import BasePlugin
from plugins.las_reprojection.LasReprojectionStep import LasReprojectionStep
from resources.widgets.ExecutionButtons import ExecutionButtons
from resources.widgets.grid.GridLabel import GridLabel
from resources.widgets.grid.GridSelector import GridSelector
from resources.widgets.GroupPainel import GroupPainel
from resources.widgets.crs.CrsSelectorWidget import CrsSelectorWidget
from utils.ExplorerUtils import ExplorerUtils
from utils.las.LasLayerProjection import LasLayerProjection
from utils.MessageBox import MessageBox


class LasReprojectionPlugin(BasePlugin):
    """
    Plugin para reprojetar nuvens LAS/LAZ entre sistemas de coordenadas.
    """

    _LAS_FILTER = "LAS/LAZ (*.las *.laz)"

    def __init__(self, parent=None):
        self._current_path: str = ""
        self._source_crs: str = ""
        self._runner: PipelineRunner | None = None
        super().__init__(
            tool_key=ToolKey.LAS_REPROJECTION.value,
            parent=parent,
            title="Reprojeção LAS",
        )
        self.logger.info("Ferramenta inicializada", code="LASREPROJ_READY")

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
                "description": "Reprojeta a nuvem LAS/LAZ",
            },
        })
        self._btns.set_enabled("executar", False)
        self.main_layout.addWidget(self._btns)

        # ── GroupPainel "Arquivos" ──────────────────────────────────
        grupo_arquivos = GroupPainel("Arquivos")
        self.main_layout.addWidget(grupo_arquivos)

        self._selector_grid = GridSelector(
            {
                "LAS/LAZ de Entrada": {
                    "file_filter": self._LAS_FILTER,
                    "browse_mode": "open_file",
                    "placeholder": "Selecione o arquivo LAS/LAZ...",
                },
                "Pasta de Saída": {
                    "browse_mode": "directory",
                    "placeholder": "Pasta para salvar o resultado...",
                },
            },
        )
        grupo_arquivos.group_layout.addWidget(self._selector_grid)

        sel_entrada = self._selector_grid["LAS/LAZ de Entrada"]
        sel_entrada.edit.textChanged.connect(self._on_input_path_changed)

        # ── GroupPainel "Sistema de Coordenadas" ────────────────────
        grupo_crs = GroupPainel("Sistema de Coordenadas")
        self.main_layout.addWidget(grupo_crs)

        self._crs_origem = CrsSelectorWidget(label="CRS de Origem:")
        self._crs_destino = CrsSelectorWidget(label="CRS de Destino:")
        grupo_crs.group_layout.addWidget(self._crs_origem)
        grupo_crs.group_layout.addWidget(self._crs_destino)

        # Conecta mudanças de CRS para validar botão executar
        self._crs_origem.crs_changed.connect(self._on_crs_changed)
        self._crs_destino.crs_changed.connect(self._on_crs_changed)

        # ── GroupPainel "Metadados" ─────────────────────────────────
        grupo_meta = GroupPainel("Metadados")
        self.main_layout.addWidget(grupo_meta)

        self._result_label = GridLabel(
            {
                "arquivo": {"label": "Arquivo", "value": "—"},
                "crs_origem": {"label": "CRS Origem", "value": "—"},
                "crs_destino": {"label": "CRS Destino", "value": "—"},
                "n_pontos": {"label": "Total Pontos", "value": "—"},
                "status": {"label": "Status", "value": "—"},
            },
            columns=2,
        )
        grupo_meta.group_layout.addWidget(self._result_label)

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

    def _on_crs_changed(self, value: str):
        """Disparado quando algum CRS muda."""
        self._atualizar_botao_executar()

    def _on_executar(self):
        """Executa a reprojeção via PipelineRunner em background."""
        self.logger.info(
            "Botao EXECUTAR pressionado",
            code="LASREPROJ_EXEC_BTN",
            path=self._current_path,
        )

        if self._runner is not None and self._runner.isRunning():
            self.logger.warning(
                "Tentativa de executar enquanto ja em execucao",
                code="LASREPROJ_EXEC_ALREADY_RUNNING",
            )
            MessageBox.show_warning(
                "Ja existe uma reprojeção em andamento.", title="Aguarde"
            )
            return

        if not self._current_path:
            self.logger.warning(
                "Tentativa de executar sem LAS carregado",
                code="LASREPROJ_EXEC_NO_FILE",
            )
            MessageBox.show_warning(
                "Nenhum arquivo LAS carregado.", title="Reprojeção LAS",
            )
            return

        source_crs = self._crs_origem.get_crs()
        target_crs = self._crs_destino.get_crs()

        if not source_crs:
            self.logger.warning(
                "CRS de origem nao definido",
                code="LASREPROJ_NO_SRC_CRS",
            )
            MessageBox.show_warning(
                "Defina o CRS de origem.", title="Reprojeção LAS",
            )
            return

        if not target_crs:
            self.logger.warning(
                "CRS de destino nao definido",
                code="LASREPROJ_NO_TGT_CRS",
            )
            MessageBox.show_warning(
                "Defina o CRS de destino.", title="Reprojeção LAS",
            )
            return

        # Resolve pasta de saída
        output_dir = self._selector_grid["Pasta de Saída"].path()
        if not output_dir:
            output_dir = os.path.dirname(self._current_path)

        basename = os.path.splitext(os.path.basename(self._current_path))[0]
        output_path = os.path.join(output_dir, f"{basename}_reprojected.las")

        # Prepara UI para execução
        self._btns.set_all_enabled(False)
        self.page.set_badge(self.page.RUNNING)
        self._result_label.set("status", "Reprojetando...")

        self.logger.info(
            "Iniciando reprojeção em background",
            code="LASREPROJ_EXEC_START",
            input_path=self._current_path,
            output_path=output_path,
            source_crs=source_crs,
            target_crs=target_crs,
        )

        SignalManager.instance().execution_started.emit(self.tool_key)
        SignalManager.instance().console_message.emit(
            f"Reprojeta: {os.path.basename(self._current_path)} "
            f"{source_crs} → {target_crs}"
        )
        SignalManager.instance().hud_show.emit({
            "message": "Reprojetando nuvem de pontos...",
            "timer": 30.0,
        })

        # Cria step com os CRS e output_path direto
        step = LasReprojectionStep(
            source_crs=source_crs,
            target_crs=target_crs,
            output_path=output_path,
        )

        runner = PipelineRunner(
            steps=[step],
            input_path=self._current_path,
            output_path=output_dir,
            tool_key=self.tool_key,
            parent=self,
        )
        runner.finished_ok.connect(self._on_done)
        runner.failed.connect(self._on_error)
        runner.finished.connect(self._on_runner_finished)
        self._runner = runner
        runner.start()

        self.logger.debug(
            "PipelineRunner iniciado em QThread",
            code="LASREPROJ_RUNNER_STARTED",
            thread_id=id(runner),
        )

    # ══════════════════════════════════════════════════════════════════
    # Callbacks da Pipeline
    # ══════════════════════════════════════════════════════════════════

    def _on_done(self, context):
        """Callback de sucesso da pipeline."""
        self.logger.info(
            "Reprojeção concluida com sucesso",
            code="LASREPROJ_PIPELINE_DONE",
        )
        result = context.get_result("reprojection_result", {})

        n_points = result.get("n_points", 0)
        output_path = result.get("output_path", "")
        source_crs = result.get("source_crs", "")
        target_crs = result.get("target_crs", "")

        self._result_label.set("status", "✅ Concluído")
        self._result_label.set("n_pontos", f"{n_points:,}")
        self._result_label.set("crs_origem", source_crs)
        self._result_label.set("crs_destino", target_crs)

        SignalManager.instance().execution_finished.emit(self.tool_key)
        SignalManager.instance().console_message.emit(
            f"Reprojeta concluida! "
            f"{n_points:,} pontos | {source_crs} → {target_crs}"
        )

        self.stats_message(
            n_arquivos=1,
            n_processed=n_points,
            ntype="pontos",
        )
        self.output_message(output_path, label="LAS Reprojetado")

        self.logger.info(
            "Reprojeção finalizada com sucesso",
            code="LASREPROJ_EXEC_DONE",
            n_points=n_points,
            output_path=output_path,
        )

    def _on_error(self, message: str):
        """Callback de erro da pipeline."""
        self.logger.critical(
            "Reprojeção falhou",
            code="LASREPROJ_PIPELINE_FAILED",
            error=message,
        )
        SignalManager.instance().execution_cancelled.emit(self.tool_key)
        SignalManager.instance().console_message.emit(
            f"ERRO: {message}"
        )
        self._result_label.set("status", "❌ Erro")
        self.logger.error(
            "Erro na reprojeção",
            code="LASREPROJ_EXEC_ERR",
            error=message,
        )
        MessageBox.show_error(
            f"Erro durante a reprojeção:\n{message}",
            title="Reprojeção LAS",
        )

    def _on_runner_finished(self):
        """Callback executado ao final da pipeline (sucesso ou erro)."""
        self.logger.info(
            "PipelineRunner finalizado",
            code="LASREPROJ_RUNNER_FINISHED",
        )
        self._runner = None
        self._btns.set_all_enabled(True)
        self._atualizar_botao_executar()
        self.page.set_badge(self.page.PRONTA)
        SignalManager.instance().hud_hide.emit()
        SignalManager.instance().progress_update.emit(0.0)

    # ══════════════════════════════════════════════════════════════════
    # Utilitários
    # ══════════════════════════════════════════════════════════════════

    def _carregar_las(self, path: str):
        """Carrega metadados do LAS e detecta CRS automaticamente."""
        if getattr(self, "_loading_las", False):
            return
        self._loading_las = True

        self.logger.info(
            "Carregando LAS para reprojeção",
            code="LASREPROJ_LAS_LOAD",
            path=path,
        )

        try:
            from utils.las.LasLayerSource import LasLayerSource

            info = LasLayerSource.get_info(path, tool_key=self.tool_key)
            if info.get("error"):
                raise RuntimeError(info["error"])

            n_pontos = info["point_count"]
            self._current_path = path

            # Detecta CRS automaticamente
            crs_detectado = LasLayerProjection.get_crs(path, tool_key=self.tool_key)
            self._source_crs = crs_detectado

            # Atualiza UI
            self._result_label.set("arquivo", os.path.basename(path))
            self._result_label.set("n_pontos", f"{n_pontos:,}")

            if crs_detectado:
                self._crs_origem.set_crs(crs_detectado)
                self._result_label.set("crs_origem", crs_detectado)
                self.logger.info(
                    "CRS detectado automaticamente",
                    code="LASREPROJ_CRS_AUTO",
                    crs=crs_detectado,
                )
            else:
                self._crs_origem.set_crs("")
                self._result_label.set("crs_origem", "Não detectado")
                self.logger.warning(
                    "CRS nao detectado no LAS",
                    code="LASREPROJ_CRS_NOT_FOUND",
                )

            self._result_label.set("status", "Carregado")
            self._atualizar_botao_executar()

            SignalManager.instance().console_message.emit(
                f"Carregado: {os.path.basename(path)} "
                f"({n_pontos:,} pontos, CRS: {crs_detectado or 'não detectado'})"
            )

            self.logger.info(
                "LAS carregado com sucesso",
                code="LASREPROJ_LAS_LOADED",
                path=path,
                points=n_pontos,
                crs=crs_detectado,
            )

        except Exception as e:
            self.logger.error(
                "Erro ao carregar LAS",
                code="LASREPROJ_LAS_LOAD_ERR",
                error=str(e),
            )
            self.page.set_badge(self.page.ERROR)
            MessageBox.show_error(
                f"Erro ao carregar LAS:\n{str(e)}",
                title="Reprojeção LAS",
                detail=traceback.format_exc(),
            )
        finally:
            self._loading_las = False

    def _atualizar_botao_executar(self):
        """Habilita/desabilita o botão executar conforme estado."""
        tem_path = bool(self._current_path)
        tem_crs_origem = bool(self._crs_origem.get_crs())
        tem_crs_destino = bool(self._crs_destino.get_crs())
        pode_executar = tem_path and tem_crs_origem and tem_crs_destino
        self._btns.set_enabled("executar", pode_executar)

    # ══════════════════════════════════════════════════════════════════
    # Preferências
    # ══════════════════════════════════════════════════════════════════

    def load_prefs(self) -> None:
        """Carrega preferências salvas."""
        self.logger.info("Carregando preferencias", code="LASREPROJ_PREFS_LOAD")
        last_path = self.preferences.get("last_path", "")
        last_output = self.preferences.get("last_output", "")
        last_target_crs = self.preferences.get("last_target_crs", "")

        if last_path:
            self._carregar_las(last_path)

        if last_output:
            self._selector_grid["Pasta de Saída"].set_path(last_output)

        if last_target_crs:
            self._crs_destino.set_crs(last_target_crs)

        self.logger.info("Preferencias carregadas", code="LASREPROJ_PREFS_LOADED")

    def save_prefs(self) -> None:
        """Salva preferências atuais no cache de memória."""
        self.preferences["last_path"] = self._current_path
        self.preferences["last_output"] = self._selector_grid["Pasta de Saída"].path()
        self.preferences["last_target_crs"] = self._crs_destino.get_crs()
        self.logger.info("Preferencias salvas no cache", code="LASREPROJ_PREFS_SAVED")