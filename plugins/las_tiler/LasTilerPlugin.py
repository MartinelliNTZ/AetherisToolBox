# -*- coding: utf-8 -*-
"""
LasTilerPlugin — Divisão de nuvens LAS/LAZ em partes
======================================================
Plugin que divide um arquivo LAS/LAZ em varios arquivos menores
com base no numero de pontos por parte.

Fluxo:
  - GridSelector de entrada detecta mudança no path automaticamente
  - ExecutionButtons: USAR ORIGEM + DIVIDIR
  - PipelineRunner + LasTilerStep para execução em background

Contratos seguidos:
  - Contrato 11: widgets reutilizáveis
  - Contrato 18: ExecutionButtons padronizado
  - Contrato 20: SignalManager para progresso/console
"""

from __future__ import annotations

import os
import traceback

from core.enum.ToolKey import ToolKey
from core.manager.SignalManager import SignalManager
from core.papeline.PipelineRunner import PipelineRunner
from core.papeline.step.LasTilerStep import LasTilerStep
from plugins.BasePlugin import BasePlugin
from resources.widgets.ExecutionButtons import ExecutionButtons
from resources.widgets.grid.GridDoubleSpinBox import GridDoubleSpinBox
from resources.widgets.grid.GridLabel import GridLabel
from resources.widgets.grid.GridSelector import GridSelector
from resources.widgets.grid.GridCheckBox import GridCheckBox
from resources.widgets.GroupPainel import GroupPainel
from utils.LasUtil import LasUtil
from utils.MessageBox import MessageBox
from utils.ProcessStatisticsUtil import ProcessStatisticsUtil


class LasTilerPlugin(BasePlugin):
    """
    Plugin para divisão de nuvens LAS/LAZ em partes.
    """

    _LAS_FILTER = "LAS/LAZ (*.las *.laz)"

    def __init__(self, parent=None):
        self._current_path: str = ""
        self._current_metadata: dict = {}
        self._runner: PipelineRunner | None = None
        super().__init__(
            tool_key=ToolKey.LAS_TILER.value,
            parent=parent,
            title="Divisor de LAS",
        )
        self.logger.info("Ferramenta inicializada", code="TILER_READY")

    # ══════════════════════════════════════════════════════════════════
    # UI
    # ══════════════════════════════════════════════════════════════════

    def _build_ui(self):
        """Constrói a interface completa do plugin."""
        super()._build_ui()

        # ── ExecutionButtons ────────────────────────────────────────
        self._btns = ExecutionButtons(self, {
            "usar_origem": {
                "text": "USAR ORIGEM",
                "callback": self._on_usar_origem,
                "type": "secondary",
                "description": "Salvar na pasta do arquivo LAS original",
            },
            "executar": {
                "text": "DIVIDIR",
                "callback": self._on_executar,
                "type": "primary",
                "description": "Divide LAS em partes",
            },
            "cancelar": {
                "text": "CANCELAR",
                "callback": self._on_cancelar,
                "type": "danger",
                "description": "Cancela execucao em andamento",
            },
        })
        self._btns.set_enabled("executar", False)
        self._btns.set_enabled("cancelar", False)
        self.main_layout.addWidget(self._btns)

        # ── GroupPainel "Arquivo de Entrada" ────────────────────────
        grupo_entrada = GroupPainel("Arquivo de Entrada")
        self.main_layout.addWidget(grupo_entrada)

        self._selector_grid = GridSelector({
            "LAS/LAZ de Entrada": {
                "file_filter": self._LAS_FILTER,
                "browse_mode": "open_file",
                "placeholder": "Selecione o arquivo LAS/LAZ...",
            },
            "Pasta de Saida": {
                "file_filter": "",
                "browse_mode": "directory",
                "placeholder": "Selecione a pasta de saida...",
            },
        })
        grupo_entrada.group_layout.addWidget(self._selector_grid)

        # Conecta mudança no texto do selector de entrada
        sel_entrada = self._selector_grid["LAS/LAZ de Entrada"]
        sel_entrada.edit.textChanged.connect(self._on_input_path_changed)

        self._info_label = GridLabel(
            {
                "pontos": {"label": "Total de Pontos", "value": "—"},
                "partes": {"label": "Partes Estimadas", "value": "—"},
            },
            columns=1,
        )
        grupo_entrada.group_layout.addWidget(self._info_label)

        # ── GroupPainel "Configurações" ─────────────────────────────
        grupo_config = GroupPainel("Configurações")
        self.main_layout.addWidget(grupo_config)

        self._params_grid = GridDoubleSpinBox({
            "pontos_por_parte": {
                "label": "Pontos por parte",
                "description": "Numero maximo de pontos por arquivo",
                "decimal": 0,
                "default": 5_000_000,
                "min": 1_000,
                "max": 100_000_000,
                "step": 500_000,
            },
        })
        grupo_config.group_layout.addWidget(self._params_grid)

        self._ckb_config = GridCheckBox(
            {
                "eliminar_original": {
                    "label": "Mover original para lixeira apos dividir",
                    "description": "Remove o arquivo LAS original apos a divisao",
                    "default": False,
                },
            },
            num_columns=1,
        )
        grupo_config.group_layout.addWidget(self._ckb_config)

        # ── GroupPainel "Resultados" ─────────────────────────────────
        grupo_result = GroupPainel("Resultados")
        self.main_layout.addWidget(grupo_result)

        self._result_label = GridLabel(
            {
                "n_partes": {"label": "N Partes", "value": "—"},
                "n_pontos": {"label": "Pontos Totais", "value": "—"},
                "pts_por_parte": {"label": "Pontos/Parte", "value": "—"},
                "output_path": {"label": "Saida", "value": "—"},
                "status": {"label": "Status", "value": "Aguardando..."},
            },
            columns=2,
        )
        grupo_result.group_layout.addWidget(self._result_label)

        self.page.set_badge(self.page.PRONTA)

    # ══════════════════════════════════════════════════════════════════
    # Handlers
    # ══════════════════════════════════════════════════════════════════

    def _on_usar_origem(self):
        """
        Preenche caminho de saída na pasta do arquivo LAS original.
        Ex: /pasta/arquivo.las → /pasta/arquivo/ (pasta com nome do arquivo)
        """
        if not self._current_path:
            MessageBox.show_warning(
                "Nenhum arquivo LAS carregado.\nSelecione um arquivo primeiro.",
                title="Divisor de LAS",
            )
            self.logger.warning(
                "Tentativa de usar origem sem LAS carregado",
                code="TILER_ORIGEM_NO_LAS",
            )
            return

        dir_arquivo = os.path.dirname(self._current_path)
        basename = os.path.splitext(os.path.basename(self._current_path))[0]
        pasta = os.path.join(dir_arquivo, basename)

        sel_saida = self._selector_grid["Pasta de Saida"]
        sel_saida.set_path(pasta)
        self._btns.set_enabled("executar", True)

        self.logger.info(
            "Pasta de origem definida",
            code="TILER_ORIGEM_SET",
            pasta=pasta,
        )
        SignalManager.instance().console_message.emit(
            f"[TILER] Destino: {pasta}"
        )

    def _on_input_path_changed(self, text: str):
        """
        Disparado quando o texto do selector de entrada muda.
        Se o path for um arquivo valido, carrega o LAS automaticamente.
        """
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
        """Executa o split via PipelineRunner em background."""
        self.logger.info("Botao DIVIDIR pressionado", code="TILER_EXEC_BTN")

        if self._runner is not None and self._runner.isRunning():
            MessageBox.show_warning(
                "Ja existe uma divisao em andamento.", title="Aguarde"
            )
            return

        # Validações
        if not self._current_path:
            MessageBox.show_warning(
                "Nenhum arquivo LAS carregado.", title="Divisor de LAS",
            )
            self.logger.warning("Tentativa de executar sem LAS", code="TILER_EXEC_NO_LAS")
            return

        output_dir = self._selector_grid["Pasta de Saida"].path()
        if not output_dir:
            MessageBox.show_warning(
                "Selecione a pasta de saida.\nUse USAR ORIGEM ou preencha manualmente.",
                title="Divisor de LAS",
            )
            self.logger.warning("Nenhuma pasta de saida selecionada", code="TILER_NO_OUTPUT")
            return

        try:
            pontos_por_parte = int(self._params_grid.get("pontos_por_parte"))
        except Exception:
            pontos_por_parte = 5_000_000
        n_pontos = self._current_metadata.get("n_pontos", 0)

        # Estatísticas
        self.statistics.start(
            n=0,
            ntype=ProcessStatisticsUtil.POINTS,
            ntotal=n_pontos,
        )

        # Prepara UI
        self._btns.set_all_enabled(False)
        self._btns.set_enabled("cancelar", True)
        self.page.set_badge(self.page.RUNNING)
        self._result_label.set_values({
            "n_partes": "—",
            "n_pontos": "—",
            "pts_por_parte": "—",
            "output_path": "—",
            "status": "Processando...",
        })

        SignalManager.instance().execution_started.emit(self.tool_key)
        SignalManager.instance().hud_show.emit({
            "message": f"Dividindo LAS ({n_pontos:,} pontos)...",
            "timer": max(10.0, n_pontos / 1_000_000 * 30.0),
            "eta": max(10.0, n_pontos / 1_000_000 * 30.0),
        })
        SignalManager.instance().console_message.emit(
            f"[TILER] Dividindo {os.path.basename(self._current_path)} "
            f"({n_pontos:,} pontos, {pontos_por_parte:,} pts/parte)"
        )

        self.logger.info(
            "Iniciando split",
            code="TILER_EXEC_START",
            path=self._current_path,
            output=output_dir,
            pontos_por_parte=pontos_por_parte,
            n_total=n_pontos,
        )

        # Cria PipelineRunner com LasTilerStep
        # pontos_por_parte é parâmetro exclusivo do step (Contrato 28)
        step = LasTilerStep(points_per_part=pontos_por_parte)
        runner = PipelineRunner(
            steps=[step],
            input_path=os.path.dirname(self._current_path),
            output_path=output_dir,
            tool_key=self.tool_key,
            parent=self,
        )
        runner.finished_ok.connect(self._on_done)
        runner.failed.connect(self._on_error)
        runner.finished.connect(self._on_runner_finished)
        self._runner = runner
        runner.start()

        self.save_prefs()

    def _on_cancelar(self):
        """Cancela a execução em andamento."""
        self.logger.info("Botao CANCELAR pressionado", code="TILER_CANCEL_BTN")
        if self._runner and self._runner.isRunning():
            self._runner.cancel()
            self._result_label.set("status", "Cancelado pelo usuario")

    # ══════════════════════════════════════════════════════════════════
    # Callbacks da Pipeline
    # ══════════════════════════════════════════════════════════════════

    def _on_done(self, context):
        """Callback de sucesso da pipeline."""
        split_result = context.get_result("split_result", {})
        n_partes = split_result.get("n_partes", 0)
        n_total = split_result.get("n_total", 0)
        pts_por_parte = split_result.get("pontos_por_parte", 0)
        arquivos = split_result.get("arquivos", [])

        # Finaliza monitoramento de estatisticas
        elapsed = self.statistics.end()
        self.logger.info(
            "Tempo de processamento registrado",
            code="STATS_RECORDED",
            elapsed_s=round(elapsed, 3),
            usages=self.statistics.usages,
        )

        self._result_label.set("n_partes", str(n_partes))
        self._result_label.set("n_pontos", f"{n_total:,}")
        self._result_label.set("pts_por_parte", f"{pts_por_parte:,}")
        self._result_label.set("output_path", str(arquivos[0]) if arquivos else "—")
        self._result_label.set("status", "Concluido")

        SignalManager.instance().execution_finished.emit(self.tool_key)
        SignalManager.instance().progress_update.emit(100.0)

        msg = (
            f"Split concluido!\n\n"
            f"Total de pontos: {n_total:,}\n"
            f"Partes geradas: {n_partes}\n"
            f"Pontos por parte: {pts_por_parte:,}\n\n"
            f"Saida:\n{os.path.dirname(arquivos[0]) if arquivos else '—'}"
        )
        MessageBox.show_info(msg, title="Divisor de LAS")

        SignalManager.instance().console_message.emit(
            f"[TILER] Split concluido! {n_partes} partes, {n_total:,} pontos"
        )

        if arquivos:
            output_dir = os.path.dirname(arquivos[0])
            url_path = output_dir.replace("\\", "/")
            SignalManager.instance().console_html.emit(
                f'[TILER] Saida: <a href="file:///{url_path}"'
                f' style="color:#4FC3F7;">{output_dir}</a>'
            )
            for arq in arquivos:
                SignalManager.instance().console_message.emit(
                    f"  - {os.path.basename(arq)}"
                )

        self.logger.info(
            "Split concluido com sucesso",
            code="TILER_DONE",
            n_partes=n_partes,
            n_total=n_total,
            arquivos=len(arquivos),
            elapsed_s=round(elapsed, 3),
        )

    def _on_error(self, message: str):
        """Callback de erro da pipeline."""
        SignalManager.instance().execution_cancelled.emit(self.tool_key)
        SignalManager.instance().console_message.emit(f"[TILER] ERRO: {message}")

        self._result_label.set("status", "Erro")

        self.logger.error(
            "Split falhou",
            code="TILER_ERR",
            error=message,
            path=self._current_path,
        )

        MessageBox.show_error(
            f"Erro ao dividir LAS:\n{message}",
            title="Divisor de LAS",
        )

    def _on_runner_finished(self):
        """Callback executado ao final da pipeline (sucesso ou erro)."""
        self._runner = None
        self._btns.set_all_enabled(True)
        self._btns.set_enabled("executar", bool(self._current_path))
        self._btns.set_enabled("cancelar", False)
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

        self.logger.info("Carregando LAS", code="TILER_LAS_LOAD", path=path)

        try:
            info = LasUtil.get_info(path, tool_key=self.tool_key)
            if info.get("error"):
                raise RuntimeError(info["error"])

            n_pontos = info["point_count"]
            try:
                pts_por_parte = int(self._params_grid.get("pontos_por_parte"))
            except Exception:
                pts_por_parte = 5_000_000
            n_partes_est = max(1, int((n_pontos + pts_por_parte - 1) // pts_por_parte))

            self._current_path = path
            self._current_metadata = {
                "path": path,
                "n_pontos": n_pontos,
            }

            # Atualiza UI com bloqueio de sinais para evitar recursao
            sel_entrada = self._selector_grid["LAS/LAZ de Entrada"]
            sel_entrada.edit.blockSignals(True)
            sel_entrada.set_path(path)
            sel_entrada.edit.blockSignals(False)

            self._info_label.set("pontos", f"{n_pontos:,}")
            self._info_label.set("partes", f"~{n_partes_est}")

            self._btns.set_enabled("executar", True)
            self.page.set_badge(self.page.PRONTA)

            SignalManager.instance().console_message.emit(
                f"[TILER] Carregado: {os.path.basename(path)} "
                f"({n_pontos:,} pontos, ~{n_partes_est} partes)"
            )

            self.logger.info(
                "LAS carregado",
                code="TILER_LAS_LOADED",
                path=path,
                points=n_pontos,
                partes_estimadas=n_partes_est,
            )

        except Exception as e:
            self.logger.error(
                "Erro ao carregar LAS",
                code="TILER_LAS_LOAD_ERR",
                error=str(e),
                path=path,
            )
            self.page.set_badge(self.page.ERROR)
            MessageBox.show_error(
                f"Erro ao carregar arquivo LAS:\n{str(e)}",
                title="Divisor de LAS",
                detail=traceback.format_exc(),
            )
        finally:
            self._loading_las = False

    # ══════════════════════════════════════════════════════════════════
    # Preferências
    # ══════════════════════════════════════════════════════════════════

    def load_prefs(self) -> None:
        """Carrega preferências salvas do disco."""
        self.logger.info("Carregando preferencias", code="TILER_PREFS_LOAD")

        last_path = self.preferences.get("last_path", "")
        last_output = self.preferences.get("last_output", "")
        params = self.preferences.get("params", {})

        if last_path:
            self._carregar_las(last_path)

        if last_output:
            self._selector_grid["Pasta de Saida"].set_path(last_output)

        if params:
            self._params_grid.set_values(params)

        self.logger.info("Preferencias carregadas", code="TILER_PREFS_LOADED")

    def save_prefs(self) -> None:
        """Salva preferências atuais no cache de memória."""
        self.preferences["last_path"] = self._current_path
        self.preferences["last_output"] = self._selector_grid["Pasta de Saida"].path()
        self.preferences["params"] = self._params_grid.values
        self.logger.info("Preferencias salvas no cache", code="TILER_PREFS_SAVED")