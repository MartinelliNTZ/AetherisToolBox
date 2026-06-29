# -*- coding: utf-8 -*-
"""
LasBlackFilterPlugin — Filtro de pontos pretos em nuvens LAS/LAZ
==================================================================
Remove pontos onde R, G e B estão todos abaixo de um limiar configurável.
Gera novo arquivo com sufixo _filtrado.las/.laz sem alterar o original.
Opção de salvar os pontos pretos removidos em arquivo separado.

Fluxo:
  - SelectorGrid de entrada detecta mudança no path automaticamente
  - SimpleSelectors de saída com botão 📂 para pasta do projeto
  - ExecutionButtons: USAR ORIGEM + EXECUTAR
  - PipelineRunner + LasBlackFilterStep para execução em background
"""

from __future__ import annotations

import os
import traceback

from core.enum.ToolKey import ToolKey
from core.manager.SignalManager import SignalManager
from core.papeline.PipelineRunner import PipelineRunner
from core.papeline.step import LasBlackFilterStep
from plugins.BasePlugin import BasePlugin
from resources.widgets.ExecutionButtons import ExecutionButtons
from resources.widgets.grid.GridCheckBox import GridCheckBox
from resources.widgets.grid.GridDoubleSpinBox import GridDoubleSpinBox
from resources.widgets.grid.GridLabel import GridLabel
from resources.widgets.GroupPainel import GroupPainel
from resources.widgets.grid.GridSelector import SelectorGrid
from resources.widgets.simple.SimpleSelector import SimpleSelector
from utils.ExplorerUtils import ExplorerUtils
from utils.LasUtil import LasUtil
from utils.MessageBox import MessageBox
from utils.Preferences import Preferences
from utils.ProcessStatisticsUtil import ProcessStatisticsUtil


class LasBlackFilterPlugin(BasePlugin):
    """
    Plugin para filtrar pontos pretos de arquivos LAS/LAZ.
    """

    _LAS_FILTER = "LAS/LAZ (*.las *.laz)"

    def __init__(self, parent=None):
        # -- Inicializa atributos ANTES de super().__init__() --
        # pois BasePlugin.__init__() chama load_prefs() que acessa estes atributos
        self._current_path: str = ""
        self._las_info: dict = {}
        self._runner: PipelineRunner | None = None
        super().__init__(
            tool_key=ToolKey.LAS_BLACK_FILTER.value,
            parent=parent,
            title="Filtro Pontos Pretos",
        )
        self.logger.info("Ferramenta inicializada", code="TOOL_READY")

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
                "text": "EXECUTAR",
                "callback": self._on_executar,
                "type": "primary",
                "description": "Executar filtro de pontos pretos",
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

        # Conecta mudança no texto do selector de entrada
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

        # ── GroupPainel "Configurações" ─────────────────────────────
        grupo_config = GroupPainel("Configurações")
        self.main_layout.addWidget(grupo_config)

        self._spin_limiar = GridDoubleSpinBox(
            {
                "limiar": {
                    "label": "Limiar de Preto",
                    "description": "Valor maximo de R/G/B para considerar preto (0–255)",
                    "decimal": 0,
                    "default": 0,
                    "min": 0,
                    "max": 255,
                    "step": 1,
                },
            },
        )
        grupo_config.group_layout.addWidget(self._spin_limiar)

        self._ckb_salvar_pretos = GridCheckBox(
            {
                "salvar_pretos": {
                    "label": "Salvar pontos pretos removidos",
                    "description": "Gera arquivo separado com os pontos filtrados",
                    "default": False,
                },
            },
            num_columns=1,
        )
        grupo_config.group_layout.addWidget(self._ckb_salvar_pretos)

        # ── GroupPainel "Arquivos de Saída" ─────────────────────────
        grupo_saida = GroupPainel("Arquivos de Saída")
        self.main_layout.addWidget(grupo_saida)

        self._sel_limpo = SimpleSelector(
            label_text="LAS Filtrado",
            file_filter=self._LAS_FILTER,
            browse_mode="save_file",
            placeholder="Caminho do LAS filtrado...",
        )
        grupo_saida.group_layout.addWidget(self._sel_limpo)

        self._sel_pretos = SimpleSelector(
            label_text="LAS Pretos",
            file_filter=self._LAS_FILTER,
            browse_mode="save_file",
            placeholder="Caminho do LAS de pontos pretos...",
        )
        grupo_saida.group_layout.addWidget(self._sel_pretos)

        self.page.set_badge(self.page.PRONTA)

    # ══════════════════════════════════════════════════════════════════
    # Handlers
    # ══════════════════════════════════════════════════════════════════

    def _on_input_path_changed(self, text: str):
        """
        Disparado quando o texto do selector de entrada muda.
        Se o path for um arquivo valido, carrega o LAS automaticamente.
        Evita chamada recursiva se o path ja estiver carregado.
        """
        path = text.strip()
        if not path:
            return
        ext = os.path.splitext(path)[1].lower()
        if ext not in (".las", ".laz") or not os.path.isfile(path):
            return
        # -- Protecao contra recursao: se ja estamos carregando, ignora --
        if getattr(self, "_loading_las", False):
            return
        if path == self._current_path:
            return
        self._carregar_las(path)

    def _on_usar_origem(self):
        """
        Preenche caminhos de saída na pasta do arquivo LAS original.
        Ex: /pasta/arquivo.las → /pasta/arquivo_filtrado.las
        """
        if not self._current_path:
            MessageBox.show_warning(
                "Nenhum arquivo LAS carregado.\nSelecione um arquivo primeiro.",
                title="Filtro Pontos Pretos",
            )
            self.logger.warning(f"Tentativa de executar sem LAS carregado em :{self._current_path}", code="EXEC_NO_LAS")
            
            return

        caminhos = self._resolver_caminhos_saida(modo="origem")
        self._sel_limpo.set_path(caminhos["limpo"])
        self._sel_pretos.set_path(caminhos["pretos"])
        self._atualizar_suggested_path(modo="origem")
        self._btns.set_enabled("executar", True)
        SignalManager.instance().console_message.emit(
            "[LasBlackFilter] Destino: pasta do LAS original"
        )

    def _on_usar_projeto(self):
        """
        Preenche caminhos de saída na pasta do projeto ativo.
        Se não houver projeto ativo, faz fallback para origem.
        """
        if not self._current_path:
            return

        sys_prefs = Preferences.load_tool_prefs(ToolKey.SYSTEM)
        root_folder = sys_prefs.get("root_folder", "")

        if root_folder and os.path.isdir(root_folder):
            caminhos = self._resolver_caminhos_saida(modo="projeto")
            self._sel_limpo.set_path(caminhos["limpo"])
            self._sel_pretos.set_path(caminhos["pretos"])
            self._atualizar_suggested_path(modo="projeto")
            self._btns.set_enabled("executar", True)
        else:
            self._on_usar_origem()

    def _on_executar(self):
        """Executa o filtro de pontos pretos via PipelineRunner em background."""
        if self._runner is not None and self._runner.isRunning():
            MessageBox.show_warning(
                "Já existe um filtro em andamento.", title="Aguarde"
            )
            return

        if not self._current_path:
            MessageBox.show_warning(
                "Nenhum arquivo LAS carregado.", title="Filtro Pontos Pretos",
            )
            self.logger.warning(f"Tentativa de executar sem LAS carregado em :{self._current_path}", code="EXEC_NO_LAS")
            return

        if not self._las_info.get("has_rgb", False):
            MessageBox.show_warning(
                "O arquivo LAS não possui bandas RGB.\n"
                "Não é possível filtrar pontos pretos.",
                title="Filtro Pontos Pretos",
            )
            return

        limiar = self._spin_limiar.get("limiar")
        salvar_pretos = self._ckb_salvar_pretos.checked.get("salvar_pretos", False)

        output_limpo = self._sel_limpo.path()
        if not output_limpo:
            MessageBox.show_warning(
                "Defina o caminho do arquivo de saída (LAS Filtrado).\n"
                "Use USAR ORIGEM ou preencha manualmente.",
                title="Filtro Pontos Pretos",
            )
            return

        output_pretos = self._sel_pretos.path() if salvar_pretos else ""

        # Obtem total de pontos via LasUtil para o statistics
        n_total = LasUtil.get_point_count(
            self._current_path, tool_key=self.tool_key
        )

        # Inicia monitoramento de estatisticas (ETA, tempo, etc.)
        self.statistics.start(
            n=0,
            ntype=ProcessStatisticsUtil.POINTS,
            ntotal=n_total,
        )

        SignalManager.instance().console_message.emit(
            f"[LasBlackFilter] {self.statistics.summary}"
        )

        # Prepara UI para execução
        self._btns.set_all_enabled(False)
        self.page.set_badge(self.page.RUNNING)

        # Obtem tempo total estimado do ProcessStatisticsUtil para o HUD
        total_estimate_seconds = max(
            self.statistics.remaining_time,
            self.statistics.total_time,
            30.0,  # fallback padrao
        )

        SignalManager.instance().execution_started.emit(self.tool_key)
        # HUD Modo 3 (Stages): 4 etapas com duração total estimada
        SignalManager.instance().hud_show.emit({
            "message": "Filtrando pontos pretos...",
            "stages": [total_estimate_seconds, 4],
        })
        SignalManager.instance().console_message.emit(
            f"[LasBlackFilter] Iniciando filtro (limiar={limiar})..."
        )

        self.logger.info(
            "Iniciando filtro",
            code="FILTER_START",
            path=self._current_path,
            limiar=limiar,
            salvar_pretos=salvar_pretos,
            output_limpo=output_limpo,
            n_total=n_total,
            eta=self.statistics.eta_str,
            total_estimate_seconds=round(total_estimate_seconds, 1),
        )

        # Cria e inicia a pipeline em background via QThread
        step = LasBlackFilterStep()
        runner = PipelineRunner(
            steps=[step],
            context={
                "file_path": self._current_path,
                "limiar": limiar,
                "salvar_pretos": salvar_pretos,
                "output_limpo": output_limpo,
                "output_pretos": output_pretos,
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
        n_removidos = context.get("n_removidos", 0)
        n_mantidos = context.get("n_mantidos", 0)
        n_total = context.get("n_total", 0)
        n_pretos = context.get("n_pretos", 0)
        output_limpo = context.get("output_limpo", "")
        output_pretos = context.get("output_pretos", "")

        # Finaliza monitoramento de estatisticas
        elapsed = self.statistics.end()
        self.logger.info(
            "Tempo de processamento registrado",
            code="STATS_RECORDED",
            elapsed_s=round(elapsed, 3),
            usages=self.statistics.usages,
        )

        SignalManager.instance().execution_finished.emit(self.tool_key)
        SignalManager.instance().console_message.emit(
            f"[LasBlackFilter] Filtro concluído! "
            f"{n_removidos:,} pontos removidos, "
            f"{n_mantidos:,} mantidos."
        )

        self.logger.info(
            "Filtro concluído com sucesso",
            code="FILTER_DONE",
            removidos=n_removidos,
            restantes=n_mantidos,
            total=n_total,
            output_limpo=output_limpo,
            output_pretos=output_pretos or None,
        )

        msg = (
            f"Filtro concluído!\n\n"
            f"Total de pontos: {n_total:,}\n"
            f"Pontos removidos: {n_removidos:,}\n"
            f"Pontos mantidos: {n_mantidos:,}\n\n"
            f"LAS filtrado salvo em:\n{output_limpo}"
        )
        if n_pretos > 0 and output_pretos:
            msg += f"\n\nPontos pretos salvos em:\n{output_pretos}"

        MessageBox.show_info(msg, title="Filtro Pontos Pretos")

    def _on_error(self, message: str):
        """Callback de erro da pipeline."""
        SignalManager.instance().execution_cancelled.emit(self.tool_key)
        SignalManager.instance().console_message.emit(
            f"[LasBlackFilter] ERRO: {message}"
        )
        self.logger.error(
            "Erro no filtro de pontos pretos",
            code="FILTER_ERR",
            error=message,
            path=self._current_path,
        )
        MessageBox.show_error(
            f"Erro durante o filtro:\n{message}",
            title="Filtro Pontos Pretos",
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
        # -- Protecao contra reentrada, evita recursao via textChanged --
        if getattr(self, "_loading_las", False):
            return
        self._loading_las = True

        self.logger.info("Carregando LAS", code="LAS_LOAD", path=path)

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

            # Atualiza UI
            # Usa bloqueio de sinais para evitar recursao via textChanged
            sel_entrada = self._selector_grid["LAS/LAZ de Entrada"]
            sel_entrada.edit.blockSignals(True)
            sel_entrada.set_path(path)
            sel_entrada.edit.blockSignals(False)

            self._info_label.set("pontos", f"{n_pontos:,}")
            self._info_label.set("has_rgb", "Sim" if has_rgb else "Não")

            # Bounding box aproximada via LasUtil
            bbox = LasUtil.get_bounding_box(path, tool_key=self.tool_key)
            if bbox:
                self._info_label.set(
                    "bbox",
                    f"X[{bbox['x_min']:.1f}, {bbox['x_max']:.1f}] "
                    f"Y[{bbox['y_min']:.1f}, {bbox['y_max']:.1f}]",
                )
            else:
                self._info_label.set("bbox", "—")

            # Habilita/desabilita botao executar conforme has_rgb
            self._btns.set_enabled("executar", has_rgb)
            self.page.set_badge(self.page.PRONTA if has_rgb else self.page.ERROR)

            if not has_rgb:
                SignalManager.instance().console_message.emit(
                    "[LasBlackFilter] AVISO: LAS sem bandas RGB"
                )
                MessageBox.show_warning(
                    "O arquivo LAS não possui bandas RGB.\n"
                    "O filtro de pontos pretos não será executado.",
                    title="Filtro Pontos Pretos",
                )

            self.logger.info(
                "LAS carregado",
                code="LAS_LOADED",
                path=path,
                points=n_pontos,
                has_rgb=has_rgb,
            )

        except Exception as e:
            self.logger.error(
                "Erro ao carregar LAS",
                code="LAS_LOAD_ERR",
                error=str(e),
                path=path,
            )
            self.page.set_badge(self.page.ERROR)
            MessageBox.show_error(
                f"Erro ao carregar arquivo LAS:\n{str(e)}",
                title="Filtro Pontos Pretos",
                detail=traceback.format_exc(),
            )
        finally:
            self._loading_las = False

    def _resolver_caminhos_saida(self, modo: str) -> dict[str, str]:
        """
        Resolve os caminhos de saída para os arquivos filtrados.

        Args:
            modo: "origem" → pasta do LAS original
                  "projeto" → root_folder/las/black_points_filter/

        Returns:
            Dict com "limpo" e "pretos" (caminhos completos).
        """
        if not self._current_path:
            return {"limpo": "", "pretos": ""}

        dir_origem = os.path.dirname(self._current_path)
        basename = os.path.splitext(os.path.basename(self._current_path))[0]
        ext = os.path.splitext(self._current_path)[1].lower()

        if modo == "projeto":
            sys_prefs = Preferences.load_tool_prefs(ToolKey.SYSTEM)
            root_folder = sys_prefs.get("root_folder", "")
            if root_folder and os.path.isdir(root_folder):
                base_dir = os.path.join(root_folder, "las", "black_points_filter")
            else:
                base_dir = dir_origem
        else:
            base_dir = dir_origem

        limpo = os.path.join(base_dir, f"{basename}_filtrado{ext}")
        pretos = os.path.join(base_dir, f"{basename}_pretos{ext}")

        return {"limpo": limpo, "pretos": pretos}

    def _atualizar_suggested_path(self, modo: str):
        """
        Atualiza o botao 📂 dos selectors de saida com o PATH RELATIVO.

        O SimpleSelector usará este path relativo e, quando o botão for
        clicado, buscará o root_folder do projeto ativo via ProjectUtil
        e concatenará com este path para formar o caminho completo.

        modo "projeto" → "las/black_points_filter"
        modo "origem"  → caminho vazio (esconde o botão)
        """
        if modo == "projeto":
            rel_path = "las/black_points_filter"
            self._sel_limpo.set_suggested_path(rel_path)
            self._sel_pretos.set_suggested_path(rel_path)
            SignalManager.instance().console_message.emit(
                f"[LasBlackFilter] Botão 📂 configurado para: {rel_path}"
            )
        else:
            self._sel_limpo.set_suggested_path("")
            self._sel_pretos.set_suggested_path("")

    # ══════════════════════════════════════════════════════════════════
    # Preferências
    # ══════════════════════════════════════════════════════════════════

    def load_prefs(self) -> None:
        """Carrega preferências salvas."""
        self.logger.info("Carregando preferências", code="PREFS_LOAD")
        last_path = self.preferences.get("last_path", "")
        limiar = self.preferences.get("limiar", 0)
        salvar_pretos = self.preferences.get("salvar_pretos", False)
        last_output_limpo = self.preferences.get("output_limpo", "")
        last_output_pretos = self.preferences.get("output_pretos", "")

        # Carrega o LAS primeiro (se houver) para setar _current_path
        if last_path:
            self._carregar_las(last_path)

        # Restaura outputs salvos (se existirem) SEM depender de _on_usar_*()
        if last_output_limpo:
            self._sel_limpo.set_path(last_output_limpo)
        if last_output_pretos:
            self._sel_pretos.set_path(last_output_pretos)

        # Atualiza suggested_path se output_limpo aponta para pasta do projeto
        if last_output_limpo and "black_points_filter" in last_output_limpo:
            self._atualizar_suggested_path(modo="projeto")
        elif self._current_path:
            self._atualizar_suggested_path(modo="origem")

        # Habilita executar se tem LAS carregado com RGB
        if self._current_path and self._las_info.get("has_rgb", False):
            self._btns.set_enabled("executar", True)

        self._spin_limiar.set_values({"limiar": limiar})
        self._ckb_salvar_pretos.set_all({"salvar_pretos": salvar_pretos})
        self.logger.info("Preferências carregadas", code="PREFS_LOADED")

    def save_prefs(self) -> None:
        """Salva preferências atuais no cache de memória."""
        self.preferences["last_path"] = self._current_path
        self.preferences["limiar"] = self._spin_limiar.get("limiar")
        self.preferences["salvar_pretos"] = self._ckb_salvar_pretos.checked.get(
            "salvar_pretos", False
        )
        self.preferences["output_limpo"] = self._sel_limpo.path()
        self.preferences["output_pretos"] = self._sel_pretos.path()
        self.logger.info("Preferências salvas no cache", code="PREFS_SAVED")