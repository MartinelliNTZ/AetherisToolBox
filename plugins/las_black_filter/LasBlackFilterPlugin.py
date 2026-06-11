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
"""

from __future__ import annotations

import os
import traceback

import laspy
import numpy as np

from PySide6.QtCore import QTimer

from core.enum.ToolKey import ToolKey
from core.manager.SignalManager import SignalManager
from plugins.BasePlugin import BasePlugin
from resources.widgets.ExecutionButtons import ExecutionButtons
from resources.widgets.GridCheckBox import GridCheckBox
from resources.widgets.GridDoubleSpinBox import GridDoubleSpinBox
from resources.widgets.GridLabel import GridLabel
from resources.widgets.GroupPainel import GroupPainel
from resources.widgets.SelectorGrid import SelectorGrid
from resources.widgets.SimpleSelector import SimpleSelector
from utils.ExplorerUtils import ExplorerUtils
from utils.MessageBox import MessageBox
from utils.Preferences import Preferences


class LasBlackFilterPlugin(BasePlugin):
    """
    Plugin para filtrar pontos pretos de arquivos LAS/LAZ.
    """

    _LAS_FILTER = "LAS/LAZ (*.las *.laz)"

    def __init__(self, parent=None):
        super().__init__(
            tool_key=ToolKey.LAS_BLACK_FILTER.value,
            parent=parent,
            title="Filtro Pontos Pretos",
        )
        self._current_path: str = ""
        self._las_info: dict = {}
        self._segundo_plano: bool = False
        self._suggested_dir: str = ""  # diretorio sugerido para saida
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

        # Selectors de saída criados manualmente para suportar suggested_path dinâmico
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
        """
        path = text.strip()
        if not path:
            return
        # Verifica se é arquivo existente com extensão valida
        ext = os.path.splitext(path)[1].lower()
        if ext not in (".las", ".laz") or not os.path.isfile(path):
            return
        # Evita recarregar o mesmo arquivo
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
        Preenche caminhos de saída na pasta do projeto ativo e
        atualiza o suggested_path (botao 📂) dos selectors de saida.
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
            # Fallback para origem
            self._on_usar_origem()

    def _on_executar(self):
        """Executa o filtro de pontos pretos em segundo plano."""
        if not self._current_path:
            MessageBox.show_warning(
                "Nenhum arquivo LAS carregado.", title="Filtro Pontos Pretos",
            )
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

        # Executa em segundo plano via QTimer para não travar UI
        self._btns.set_all_enabled(False)
        self.page.set_badge(self.page.RUNNING)
        self._segundo_plano = True

        SignalManager.instance().execution_started.emit(self.tool_key)
        SignalManager.instance().hud_show.emit({"message": "Filtrando pontos pretos..."})
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
        )

        QTimer.singleShot(0, lambda: self._executar_filtro(
            self._current_path, limiar, salvar_pretos,
            output_limpo, output_pretos,
        ))

    # ══════════════════════════════════════════════════════════════════
    # Lógica de filtragem
    # ══════════════════════════════════════════════════════════════════

    def _executar_filtro(
        self,
        input_path: str,
        limiar: int,
        salvar_pretos: bool,
        output_limpo: str,
        output_pretos: str,
    ):
        """
        Processa o LAS: filtra pontos pretos e salva arquivos.
        """
        signals = SignalManager.instance()
        try:
            # ── Leitura ─────────────────────────────────────────────
            signals.hud_update.emit({
                "message": "Lendo arquivo LAS...",
                "progress": 5.0,
            })
            signals.progress_update.emit(5.0)
            signals.console_message.emit("[LasBlackFilter] Lendo arquivo...")

            las = laspy.read(input_path)
            n_total = len(las.points)

            signals.progress_update.emit(15.0)
            signals.hud_update.emit({
                "message": f"Analisando {n_total:,} pontos...",
                "progress": 15.0,
            })

            red = np.asarray(las.red, dtype=np.int64)
            green = np.asarray(las.green, dtype=np.int64)
            blue = np.asarray(las.blue, dtype=np.int64)

            signals.progress_update.emit(25.0)

            mask_valido = (red > limiar) | (green > limiar) | (blue > limiar)
            n_removidos = n_total - int(np.sum(mask_valido))

            signals.progress_update.emit(40.0)
            signals.hud_update.emit({
                "message": f"Removendo {n_removidos:,} pontos pretos...",
                "progress": 40.0,
            })

            las_limpo = laspy.LasData(las.header)
            las_limpo.points = las.points[mask_valido]

            signals.progress_update.emit(55.0)

            signals.hud_update.emit({
                "message": f"Salvando LAS filtrado ({len(las_limpo.points):,} pontos)...",
                "progress": 60.0,
            })
            signals.console_message.emit(
                f"[LasBlackFilter] Salvando LAS filtrado: {output_limpo}"
            )
            ExplorerUtils.ensure_directory(
                os.path.dirname(output_limpo), tool_key=self.tool_key
            )
            las_limpo.write(output_limpo)

            signals.progress_update.emit(75.0)

            n_pretos = 0
            if salvar_pretos and n_removidos > 0 and output_pretos:
                mask_pretos = ~mask_valido
                las_pretos = laspy.LasData(las.header)
                las_pretos.points = las.points[mask_pretos]
                n_pretos = len(las_pretos.points)

                signals.hud_update.emit({
                    "message": f"Salvando {n_pretos:,} pontos pretos...",
                    "progress": 85.0,
                })
                signals.console_message.emit(
                    f"[LasBlackFilter] Salvando pontos pretos: {output_pretos}"
                )
                ExplorerUtils.ensure_directory(
                    os.path.dirname(output_pretos), tool_key=self.tool_key
                )
                las_pretos.write(output_pretos)

            signals.progress_update.emit(100.0)

            self.page.set_badge(self.page.PRONTA)

            signals.execution_finished.emit(self.tool_key)
            signals.console_message.emit(
                f"[LasBlackFilter] Filtro concluído! "
                f"{n_removidos:,} pontos removidos, "
                f"{len(las_limpo.points):,} mantidos."
            )

            self.logger.info(
                "Filtro concluído com sucesso",
                code="FILTER_DONE",
                removidos=n_removidos,
                restantes=len(las_limpo.points),
                total=n_total,
                output_limpo=output_limpo,
                output_pretos=output_pretos if (salvar_pretos and output_pretos) else None,
            )

            msg = (
                f"Filtro concluído!\n\n"
                f"Total de pontos: {n_total:,}\n"
                f"Pontos removidos: {n_removidos:,}\n"
                f"Pontos mantidos: {len(las_limpo.points):,}\n\n"
                f"LAS filtrado salvo em:\n{output_limpo}"
            )
            if salvar_pretos and n_pretos > 0 and output_pretos:
                msg += f"\n\nPontos pretos salvos em:\n{output_pretos}"

            MessageBox.show_info(msg, title="Filtro Pontos Pretos")

        except Exception as e:
            self.page.set_badge(self.page.ERROR)
            signals.execution_cancelled.emit(self.tool_key)
            signals.console_message.emit(f"[LasBlackFilter] ERRO: {str(e)}")
            self.logger.error(
                "Erro no filtro de pontos pretos",
                code="FILTER_ERR",
                error=str(e),
                path=input_path,
            )
            MessageBox.show_error(
                f"Erro durante o filtro:\n{str(e)}",
                title="Filtro Pontos Pretos",
                detail=traceback.format_exc(),
            )

        finally:
            self._btns.set_all_enabled(True)
            self._btns.set_enabled("executar", bool(self._current_path))
            self._segundo_plano = False

    # ══════════════════════════════════════════════════════════════════
    # Utilitários
    # ══════════════════════════════════════════════════════════════════

    def _carregar_las(self, path: str):
        """Carrega metadados do LAS e atualiza a UI."""
        self.logger.info("Carregando LAS", code="LAS_LOAD", path=path)

        try:
            with laspy.open(path) as las:
                n_pontos = las.header.point_count
                has_rgb = "red" in las.header.point_format.dimension_names

            self._current_path = path
            self._las_info = {
                "path": path,
                "n_pontos": n_pontos,
                "has_rgb": has_rgb,
            }

            # Atualiza UI
            self._selector_grid["LAS/LAZ de Entrada"].set_path(path)
            self._info_label.set("pontos", f"{n_pontos:,}")
            self._info_label.set("has_rgb", "Sim" if has_rgb else "Não")

            # Bounding box aproximada
            try:
                las_read = laspy.read(path, count=min(10000, n_pontos))
                if len(las_read.points) > 0:
                    x_min, x_max = float(las_read.x.min()), float(las_read.x.max())
                    y_min, y_max = float(las_read.y.min()), float(las_read.y.max())
                    self._info_label.set(
                        "bbox",
                        f"X[{x_min:.1f}, {x_max:.1f}] Y[{y_min:.1f}, {y_max:.1f}]",
                    )
            except Exception:
                self._info_label.set("bbox", "—")

            if not has_rgb:
                self._btns.set_enabled("executar", False)
                self.page.set_badge(self.page.ERROR)
                SignalManager.instance().console_message.emit(
                    "[LasBlackFilter] AVISO: LAS sem bandas RGB"
                )
                MessageBox.show_warning(
                    "O arquivo LAS não possui bandas RGB.\n"
                    "O filtro de pontos pretos não será executado.",
                    title="Filtro Pontos Pretos",
                )
            else:
                # Tenta preencher automaticamente: projeto > origem
                sys_prefs = Preferences.load_tool_prefs(ToolKey.SYSTEM)
                root_folder = sys_prefs.get("root_folder", "")
                if root_folder and os.path.isdir(root_folder):
                    self._on_usar_projeto()
                else:
                    self._on_usar_origem()
                self.page.set_badge(self.page.PRONTA)

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
            # Passa APENAS o path relativo — o widget resolve o root_folder
            rel_path = "las/black_points_filter"
            self._sel_limpo.set_suggested_path(rel_path)
            self._sel_pretos.set_suggested_path(rel_path)
            SignalManager.instance().console_message.emit(
                f"[LasBlackFilter] Botão 📂 configurado para: {rel_path}"
            )
        else:
            # Modo origem: esconde o botão 📂
            self._sel_limpo.set_suggested_path("")
            self._sel_pretos.set_suggested_path("")

    # ══════════════════════════════════════════════════════════════════
    # Preferências
    # ══════════════════════════════════════════════════════════════════

    def load_prefs(self) -> None:
        """Carrega preferências salvas."""
        last_path = self.preferences.get("last_path", "")
        limiar = self.preferences.get("limiar", 0)
        salvar_pretos = self.preferences.get("salvar_pretos", False)
        last_output_limpo = self.preferences.get("output_limpo", "")
        last_output_pretos = self.preferences.get("output_pretos", "")

        if last_path:
            self._carregar_las(last_path)

        if last_output_limpo:
            self._sel_limpo.set_path(last_output_limpo)
        if last_output_pretos:
            self._sel_pretos.set_path(last_output_pretos)

        self._spin_limiar.set_values({"limiar": limiar})
        self._ckb_salvar_pretos.set_all({"salvar_pretos": salvar_pretos})

    def save_prefs(self) -> None:
        """Salva preferências atuais."""
        self.preferences["last_path"] = self._current_path
        self.preferences["limiar"] = self._spin_limiar.get("limiar")
        self.preferences["salvar_pretos"] = self._ckb_salvar_pretos.checked.get(
            "salvar_pretos", False
        )
        self.preferences["output_limpo"] = self._sel_limpo.path()
        self.preferences["output_pretos"] = self._sel_pretos.path()