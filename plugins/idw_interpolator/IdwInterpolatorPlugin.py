# -*- coding: utf-8 -*-
"""
IdwInterpolatorPlugin — Interpolação IDW de nuvens LAS/LAZ em grid regular
=============================================================================
Interface para interpolação IDW com:
  - GridCheckBox: alvo R, G, B, Altura (Z)
  - GridCheckBox: Separar Bandas?
  - Botão "Calcular Pixel Ideal" → carrega no GridDoubleSpinBox
  - GridDoubleSpinBox: resolução, fator conversão, k, power, raio, overlap, pontos/tile
  - ExecutionButtons: PIXEL IDEAL, EXECUTAR, CANCELAR
  - PipelineRunner + IdwInterpolatorStep em background

Contratos seguidos:
  - Contrato 11: widgets reutilizáveis (GridCheckBox, GridDoubleSpinBox, etc.)
  - Contrato 18: ExecutionButtons padronizado
  - Contrato 20: SignalManager para progresso/console
  - Contrato 24: SignalManager apenas para comunicação entre componentes
"""

from __future__ import annotations

import os

from core.enum.ToolKey import ToolKey
from core.manager.SignalManager import SignalManager
from core.papeline.PipelineRunner import PipelineRunner
from plugins.BasePlugin import BasePlugin
from plugins.idw_interpolator.IdwInterpolatorStep import IdwInterpolatorStep
from resources.widgets.ExecutionButtons import ExecutionButtons
from resources.widgets.grid.GridCheckBox import GridCheckBox
from resources.widgets.grid.GridDoubleSpinBox import GridDoubleSpinBox
from resources.widgets.grid.GridLabel import GridLabel
from resources.widgets.GroupPainel import GroupPainel
from resources.widgets.SelectorGrid import SelectorGrid
from resources.widgets.SimpleLabel import SimpleLabel
from utils.LasUtil import LasUtil
from utils.MessageBox import MessageBox


# ── Config dos checks de bandas ────────────────────────────────
TARGET_CONFIG: dict[str, dict] = {
    "r": {
        "label": "R (Vermelho)",
        "description": "Interpola banda vermelha da nuvem",
        "default": True,
    },
    "g": {
        "label": "G (Verde)",
        "description": "Interpola banda verde da nuvem",
        "default": True,
    },
    "b": {
        "label": "B (Azul)",
        "description": "Interpola banda azul da nuvem",
        "default": True,
    },
    "z": {
        "label": "Altura (Z)",
        "description": "Interpola altitude Z",
        "default": False,
    },
}

SEPARAR_CONFIG: dict[str, dict] = {
    "separate": {
        "label": "Separar Bandas?",
        "description": "Se true: banda_R/G/B/Z.tif individuais. Se false: mosaico_rgb.tif",
        "default": False,
    },
}


class IdwInterpolatorPlugin(BasePlugin):
    """
    Plugin para interpolação IDW de nuvens LAS/LAZ.
    """

    _LAS_FILTER = "LAS/LAZ (*.las *.laz)"

    def __init__(self, parent=None):
        self._current_path: str = ""
        self._current_metadata: dict = {}
        self._runner: PipelineRunner | None = None
        super().__init__(
            tool_key=ToolKey.IDW_INTERPOLATOR.value,
            parent=parent,
            title="Interpolação IDW",
        )
        self.logger.info("Ferramenta inicializada", code="IDW_READY")

    # ══════════════════════════════════════════════════════════════════
    # UI
    # ══════════════════════════════════════════════════════════════════

    def _build_ui(self):
        """Constrói a interface completa do plugin."""
        super()._build_ui()

        # ── ExecutionButtons ────────────────────────────────────────
        self._btns = ExecutionButtons(self, {
            "pixel_ideal": {
                "text": "CALCULAR PIXEL IDEAL",
                "callback": self._on_calc_ideal_pixel,
                "type": "secondary",
                "description": "Calcula pixel ideal pela densidade da nuvem",
            },
            "executar": {
                "text": "EXECUTAR",
                "callback": self._on_executar,
                "type": "primary",
                "description": "Executa interpolacao IDW",
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

        self._selector_grid = SelectorGrid({
            "LAS/LAZ de Entrada": {
                "file_filter": self._LAS_FILTER,
                "browse_mode": "open_file",
                "placeholder": "Selecione o arquivo LAS/LAZ...",
            },
            "Salvar Raster em": {
                "file_filter": "GeoTIFF (*.tif)",
                "browse_mode": "save_file",
                "placeholder": "Selecione onde salvar o raster...",
            },
        })
        grupo_entrada.group_layout.addWidget(self._selector_grid)

        sel_entrada = self._selector_grid["LAS/LAZ de Entrada"]
        sel_entrada.edit.textChanged.connect(self._on_input_path_changed)
        sel_entrada.edit.textChanged.connect(self._log_path_changed)

        # Labels informativos (ocultos até calcular pixel ideal)
        self._info_las = SimpleLabel("")
        self._info_las.setVisible(False)
        grupo_entrada.group_layout.addWidget(self._info_las)

        self._info_bbox = SimpleLabel("")
        self._info_bbox.setVisible(False)
        grupo_entrada.group_layout.addWidget(self._info_bbox)

        self._info_densidade = SimpleLabel("")
        self._info_densidade.setVisible(False)
        grupo_entrada.group_layout.addWidget(self._info_densidade)

        self._info_espacamento = SimpleLabel("")
        self._info_espacamento.setVisible(False)
        grupo_entrada.group_layout.addWidget(self._info_espacamento)

        # ── GroupPainel "Target da Interpolação" ─────────────────────
        grupo_target = GroupPainel("Target da Interpolacao")
        self.main_layout.addWidget(grupo_target)

        self._target_grid = GridCheckBox(TARGET_CONFIG, num_columns=4)
        self._target_grid.changed.connect(self._on_target_changed)
        grupo_target.group_layout.addWidget(self._target_grid)

        self._separar_grid = GridCheckBox(SEPARAR_CONFIG, num_columns=1)
        self._separar_grid.changed.connect(self._on_target_changed)
        grupo_target.group_layout.addWidget(self._separar_grid)

        # ── GroupPainel "Parâmetros IDW" ────────────────────────────
        grupo_params = GroupPainel("Parametros IDW")
        self.main_layout.addWidget(grupo_params)

        self._params_grid = GridDoubleSpinBox({
            "resolution": {
                "label": "Resolucao (cm)",
                "description": "Tamanho do pixel em centimetros",
                "decimal": 2,
                "default": 1.00,
                "min": 0.1,
                "max": 100.0,
                "step": 0.01,
                "suffix": "cm",
            },
            "fator_conversao": {
                "label": "Fator Conversao",
                "description": "Multiplicador do espacamento (0.75 = 75%)",
                "decimal": 2,
                "default": 0.75,
                "min": 0.1,
                "max": 5.0,
                "step": 0.01,
            },
            "k": {
                "label": "Vizinhos (k)",
                "description": "Numero de vizinhos mais proximos para IDW",
                "decimal": 0,
                "default": 5,
                "min": 1,
                "max": 50,
                "step": 1,
            },
            "power": {
                "label": "Potencia (p)",
                "description": "Expoente da distancia (2 = inverso quadratico)",
                "decimal": 1,
                "default": 2.0,
                "min": 0.5,
                "max": 5.0,
                "step": 0.1,
            },
            "raio_max": {
                "label": "Raio Max (m)",
                "description": "Raio maximo de busca em metros",
                "decimal": 2,
                "default": 0.50,
                "min": 0.01,
                "max": 10.0,
                "step": 0.05,
                "suffix": "m",
            },
            "overlap": {
                "label": "Overlap (m)",
                "description": "Sobreposicao entre tiles para evitar artefatos",
                "decimal": 1,
                "default": 3.0,
                "min": 0.0,
                "max": 10.0,
                "step": 0.5,
                "suffix": "m",
            },
            "pontos_por_tile": {
                "label": "Pontos/Tile",
                "description": "Numero alvo de pontos por tile",
                "decimal": 0,
                "default": 10_000_000,
                "min": 100_000,
                "max": 100_000_000,
                "step": 1_000_000,
            },
        })
        grupo_params.group_layout.addWidget(self._params_grid)

        # ── GroupPainel "Resultados" ─────────────────────────────────
        grupo_result = GroupPainel("Resultados")
        self.main_layout.addWidget(grupo_result)

        self._result_label = GridLabel(
            {
                "grid_dims":   {"label": "Grid (px)", "value": "—"},
                "resolucao":   {"label": "Resolucao", "value": "—"},
                "n_tiles":     {"label": "N Tiles", "value": "—"},
                "tempo_idw":   {"label": "Tempo IDW", "value": "—"},
                "output_path": {"label": "Saida", "value": "—"},
                "status":      {"label": "Status", "value": "Aguardando..."},
            },
            columns=2,
        )
        grupo_result.group_layout.addWidget(self._result_label)

        self.page.set_badge(self.page.PRONTA)

    # ══════════════════════════════════════════════════════════════════
    # Handlers
    # ══════════════════════════════════════════════════════════════════

    def _log_path_changed(self, text: str):
        """Loga qualquer mudança no campo de texto do selector (inclusive botao ...)."""
        path = text.strip()
        if path:
            self.logger.debug(
                "Selector alterado",
                code="IDW_SELECTOR_CHANGED",
                path=path,
            )

    def _on_input_path_changed(self, text: str):
        """Disparado quando o texto do selector de entrada muda."""
        path = text.strip()
        if not path:
            return
        ext = os.path.splitext(path)[1].lower()
        if ext not in (".las", ".laz") or not os.path.isfile(path):
            return
        if path == self._current_path:
            return
        self._carregar_las(path)

    def _on_target_changed(self):
        """Disparado quando qualquer checkbox de target ou separar muda."""
        target = self._target_grid.checked
        separate = self._separar_grid.is_item_checked("separate")

        has_rgb = "r" in target and "g" in target and "b" in target
        has_any_rgb = "r" in target or "g" in target or "b" in target

        if not separate and has_any_rgb and not has_rgb:
            self._result_label.set("status",
                "Mosaico requer R, G e B. Marque 'Separar Bandas?' "
                "para bandas individuais."
            )
        else:
            self._result_label.set("status", "Pronto")

    def _on_calc_ideal_pixel(self):
        """Calcula pixel ideal pela densidade da nuvem e carrega no GridDoubleSpinBox."""
        self.logger.info("Botao CALCULAR PIXEL IDEAL pressionado", code="IDW_CALC_PIXEL")

        if not self._current_path:
            MessageBox.show_warning(
                "Carregue um arquivo LAS primeiro.",
                title="Interpolacao IDW",
            )
            return

        try:
            fator = self._params_grid.get("fator_conversao")
            result = LasUtil.calcular_pixel_ideal(
                self._current_path,
                fator_conversao=fator,
                tool_key=self.tool_key,
            )

            if not result:
                MessageBox.show_error(
                    "Nao foi possivel calcular o pixel ideal.\n"
                    "Verifique se o LAS possui pontos validos.",
                    title="Interpolacao IDW",
                )
                return

            # Carrega no GridDoubleSpinBox
            self._params_grid.set("resolution", result["pixel_ideal_cm"])

            # Exibe labels informativos
            bbox = result["bbox"]
            self._info_bbox.setText(
                f"BBox: X[{bbox['x_min']:.2f}, {bbox['x_max']:.2f}] "
                f"Y[{bbox['y_min']:.2f}, {bbox['y_max']:.2f}]"
            )
            self._info_bbox.setVisible(True)

            self._info_densidade.setText(
                f"Densidade: {result['densidade_pts_m2']:.2f} pts/m²"
            )
            self._info_densidade.setVisible(True)

            self._info_espacamento.setText(
                f"Espacamento: {result['espacamento_cm']:.2f} cm/ponto | "
                f"Pixel ideal: {result['pixel_ideal_cm']:.2f} cm"
            )
            self._info_espacamento.setVisible(True)

            self.logger.info(
                "Pixel ideal calculado e carregado",
                code="IDW_PIXEL_CALC_DONE",
                pixel_cm=result["pixel_ideal_cm"],
            )

        except Exception as e:
            self.logger.error(
                "Erro ao calcular pixel ideal",
                code="IDW_PIXEL_CALC_ERR",
                error=str(e),
            )
            MessageBox.show_error(
                f"Erro ao calcular pixel ideal:\n{str(e)}",
                title="Interpolacao IDW",
            )

    def _resolver_output_path(self, base_path: str, has_z: bool) -> str:
        """
        Resolve o caminho de saída.
        Se Z estiver ativo e o nome base não contiver '_Z', adiciona o sufixo.
        """
        if not has_z:
            return base_path
        dir_name = os.path.dirname(base_path)
        basename = os.path.splitext(os.path.basename(base_path))[0]
        ext = os.path.splitext(base_path)[1] or ".tif"
        if not basename.endswith("_Z"):
            basename += "_Z"
        return os.path.join(dir_name, f"{basename}{ext}")

    def _on_executar(self):
        """Executa a interpolação IDW via PipelineRunner em background."""
        self.logger.info("Botao EXECUTAR pressionado", code="IDW_EXEC_BTN")

        if self._runner is not None and self._runner.isRunning():
            MessageBox.show_warning(
                "Ja existe uma interpolacao em andamento.", title="Aguarde"
            )
            return

        # Validações
        if not self._current_path:
            MessageBox.show_warning(
                "Nenhum arquivo LAS carregado.", title="Interpolacao IDW",
            )
            return

        output_path = self._selector_grid["Salvar Raster em"].path()
        if not output_path:
            MessageBox.show_warning(
                "Selecione onde salvar o raster de saida.",
                title="Interpolacao IDW",
            )
            self.logger.warning("Nenhum caminho de saída selecionado", code="IDW_NO_OUTPUT")
            return

        target = self._target_grid.checked
        if not target:
            MessageBox.show_warning(
                "Selecione ao menos uma banda para interpolar.",
                title="Interpolacao IDW",
            )
            self.logger.warning("Nenhuma banda selecionada", code="IDW_NO_TARGET")
            return

        separate = self._separar_grid.is_item_checked("separate")
        has_rgb = "r" in target and "g" in target and "b" in target
        has_any_rgb = "r" in target or "g" in target or "b" in target
        has_z = "z" in target

        if not separate and has_any_rgb and not has_rgb:
            MessageBox.show_warning(
                "Para gerar mosaico, e necessario selecionar R, G e B simultaneamente.\n"
                "Marque 'Separar Bandas?' para bandas individuais.",
                title="Interpolacao IDW",
            )
            self.logger.warning("Nenhuma banda selecionada", code="IDW_NO_TARGET")
            return

        # Resolve output path com sufixo _Z se Z ativo
        output_path = self._resolver_output_path(output_path, has_z)

        # Coleta parâmetros
        params = self._params_grid.values
        resol_cm = params.get("resolution", 1.0)
        resol_m = resol_cm / 100.0

        # Prepara UI
        self._btns.set_enabled("executar", False)
        self._btns.set_enabled("cancelar", True)
        self._btns.set_enabled("pixel_ideal", False)
        self.page.set_badge(self.page.RUNNING)
        self._result_label.set_values({
            "grid_dims": "—",
            "resolucao": "—",
            "n_tiles": "—",
            "tempo_idw": "—",
            "output_path": "—",
            "status": "Processando...",
        })

        self.logger.info(
            "Iniciando interpolacao IDW",
            code="IDW_EXEC_START",
            path=self._current_path,
            output=output_path,
            target=target,
            separate=separate,
            resol_cm=resol_cm,
        )

        SignalManager.instance().execution_started.emit(self.tool_key)
        SignalManager.instance().hud_show.emit({
            "message": "Interpolacao IDW em andamento...",
            "stages": [60.0, 7],
        })
        SignalManager.instance().console_message.emit(
            f"[IDW] Iniciando interpolacao de "
            f"{os.path.basename(self._current_path)}"
        )

        # Cria step e runner
        step = IdwInterpolatorStep()
        crs_str = "EPSG:31982"
        runner = PipelineRunner(
            steps=[step],
            context={
                "file_path": self._current_path,
                "output_path": output_path,
                "target_bands": target,
                "separate_bands": separate,
                "resol_m": resol_m,
                "idw_k": params.get("k", 5),
                "idw_power": params.get("power", 2.0),
                "idw_raio_max": params.get("raio_max", 0.5),
                "idw_overlap": params.get("overlap", 3.0),
                "pontos_por_tile": int(params.get("pontos_por_tile", 10_000_000)),
                "crs_str": crs_str,
                "tool_key": self.tool_key,
            },
            parent=self,
        )
        runner.finished_ok.connect(self._on_done)
        runner.failed.connect(self._on_error)
        runner.finished.connect(self._on_runner_finished)
        self._runner = runner
        runner.start()

        # Salva preferências ao executar
        self.save_prefs()

    def _on_cancelar(self):
        """Cancela a execução em andamento."""
        self.logger.info("Botao CANCELAR pressionado", code="IDW_CANCEL_BTN")
        if self._runner and self._runner.isRunning():
            self._runner.cancel()
            self._result_label.set("status", "Cancelado pelo usuario")

    # ══════════════════════════════════════════════════════════════════
    # Callbacks da Pipeline
    # ══════════════════════════════════════════════════════════════════

    def _on_done(self, context):
        """Callback de sucesso da pipeline."""
        self.logger.info("Pipeline IDW finalizada com sucesso", code="IDW_PIPELINE_DONE")

        idw_result = context.get("idw_result", {})
        if not idw_result:
            return

        grid = idw_result.get("grid", {})
        params = idw_result.get("parametros", {})
        tiles = idw_result.get("tiles", {})
        arquivos = idw_result.get("arquivos_gerados", [])

        self._result_label.set("grid_dims",
            f"{grid.get('width_px', 0):,} x {grid.get('height_px', 0):,} px"
        )
        resol_cm = params.get("resolucao_cm", 0)
        self._result_label.set("resolucao", f"{resol_cm:.2f} cm")
        self._result_label.set("n_tiles", str(tiles.get("total", 0)))
        self._result_label.set("output_path", str(arquivos[0]) if arquivos else "—")
        self._result_label.set("status", "Concluido")

        SignalManager.instance().execution_finished.emit(self.tool_key)
        SignalManager.instance().console_message.emit(
            f"[IDW] Interpolacao concluida! "
            f"Grid: {grid.get('width_px', 0)}x{grid.get('height_px', 0)} px, "
            f"Tiles: {tiles.get('total', 0)}"
        )

    def _on_error(self, message: str):
        """Callback de erro da pipeline."""
        self.logger.error("Pipeline IDW falhou", code="IDW_PIPELINE_FAILED", error=message)

        SignalManager.instance().execution_cancelled.emit(self.tool_key)
        SignalManager.instance().console_message.emit(f"[IDW] ERRO: {message}")

        self._result_label.set("status", "Erro")
        MessageBox.show_error(
            f"Erro durante a interpolacao IDW:\n{message}",
            title="Interpolacao IDW",
        )

    def _on_runner_finished(self):
        """Callback executado ao final da pipeline (sucesso ou erro)."""
        self._runner = None
        self._btns.set_enabled("executar", bool(self._current_path))
        self._btns.set_enabled("cancelar", False)
        self._btns.set_enabled("pixel_ideal", bool(self._current_path))
        self.page.set_badge(self.page.PRONTA)
        SignalManager.instance().hud_hide.emit()
        SignalManager.instance().progress_update.emit(0.0)

    # ══════════════════════════════════════════════════════════════════
    # Utilitários
    # ══════════════════════════════════════════════════════════════════

    def _carregar_las(self, path: str):
        """Carrega metadados do LAS e atualiza a UI."""
        self.logger.info("Carregando LAS", code="IDW_LAS_LOAD", path=path)

        try:
            info = LasUtil.get_info(path, tool_key=self.tool_key)
            if info.get("error"):
                raise RuntimeError(info["error"])

            n_pontos = info["point_count"]
            has_rgb = info["has_rgb"]

            self._current_path = path
            self._current_metadata = {
                "path": path,
                "n_pontos": n_pontos,
                "has_rgb": has_rgb,
            }

            # Atualiza label info
            self._info_las.setText(
                f"Pontos: {n_pontos:,} | RGB: {'sim' if has_rgb else 'nao'}"
            )
            self._info_las.setVisible(True)

            # Se não tem RGB, desmarca R, G, B
            if not has_rgb:
                current_z = self._target_grid.is_item_checked("z")
                self._target_grid.set_all({
                    "r": False,
                    "g": False,
                    "b": False,
                    "z": current_z,
                })

            self._btns.set_enabled("executar", True)
            self._btns.set_enabled("pixel_ideal", True)
            self.page.set_badge(self.page.PRONTA)

            SignalManager.instance().console_message.emit(
                f"[IDW] Carregado: {os.path.basename(path)} "
                f"({n_pontos:,} pontos, RGB: {'sim' if has_rgb else 'nao'})"
            )

            self.logger.info(
                "LAS carregado com sucesso",
                code="IDW_LAS_LOADED",
                path=path,
                n_pontos=n_pontos,
                has_rgb=has_rgb,
            )

        except Exception as e:
            self.logger.error("Erro ao carregar LAS", code="IDW_LAS_LOAD_ERR", error=str(e))
            self.page.set_badge(self.page.ERROR)
            MessageBox.show_error(
                f"Erro ao carregar LAS:\n{str(e)}",
                title="Interpolacao IDW",
            )

    # ══════════════════════════════════════════════════════════════════
    # Preferências (SKILL_PREFERENCES.md)
    # ══════════════════════════════════════════════════════════════════

    def load_prefs(self) -> None:
        """Carrega preferências salvas do disco."""
        self.logger.info("Carregando preferencias", code="IDW_PREFS_LOAD")

        last_path = self.preferences.get("last_path", "")
        last_output = self.preferences.get("last_output", "")
        target = self.preferences.get("target", {})
        separate = self.preferences.get("separate", {})
        params = self.preferences.get("params", {})

        if last_path:
            sel = self._selector_grid["LAS/LAZ de Entrada"]
            sel.edit.blockSignals(True)
            sel.set_path(last_path)
            sel.edit.blockSignals(False)
            self._carregar_las(last_path)

        if last_output:
            self._selector_grid["Salvar Raster em"].set_path(last_output)

        if target:
            self._target_grid.set_all(target)

        if separate:
            self._separar_grid.set_all(separate)

        if params:
            self._params_grid.set_values(params)

        self.logger.info("Preferencias carregadas", code="IDW_PREFS_LOADED")

    def save_prefs(self) -> None:
        """Salva preferências atuais no cache de memória."""
        self.preferences["last_path"] = self._current_path
        self.preferences["last_output"] = self._selector_grid["Salvar Raster em"].path()
        self.preferences["target"] = self._target_grid.all
        self.preferences["separate"] = self._separar_grid.all
        self.preferences["params"] = self._params_grid.values
        self.logger.info("Preferencias salvas no cache", code="IDW_PREFS_SAVED")