# -*- coding: utf-8 -*-
"""
ClassificationTool — Ferramenta de Classificação Raster
=========================================================
Widget extraído da UI principal para ser uma ferramenta
hospedada no Workspace do Aetheris ToolBox.
Console removido — agora é compartilhado via ConsoleTool.
"""

from __future__ import annotations

from PySide6.QtWidgets import (
    QVBoxLayout,
    QTextEdit,
    QFrame,
    QSizePolicy,
)
from PySide6.QtCore import Qt
from plugins.BasePlugin import BasePlugin
from core.enum.ToolKey import ToolKey
from resources.widgets.ExecutionButtons import ExecutionButtons
from resources.widgets.SimpleGhostButton import SimpleGhostButton
from resources.widgets.GroupPainel import GroupPainel
from resources.widgets.SimpleSelector import SimpleSelector
from resources.widgets.SelectorGrid import SelectorGrid
from resources.widgets.SimpleComboBox import SimpleComboBox
from resources.widgets.GridGroupPainel import GridGroupPainel
from resources.widgets.ItemTable import ItemTable
from resources.widgets.GridLineEdit import GridLineEdit
from resources.widgets.GridDoubleSpinBox import GridDoubleSpinBox
from resources.widgets.GridCheckBox import GridCheckBox
from plugins.tensorflow_classifier.tensor_utils.ui_field_specs import UI_FIELD_SPECS


class Separator(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("separator")
        self.setFrameShape(QFrame.Shape.HLine)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.setFixedHeight(1)


class TensorflowClassificationPlugin(BasePlugin):
    """
    Widget completo da ferramenta de classificação raster.
    Pode ser hospedada no Workspace.
    """

    def __init__(self, parent=None):
        super().__init__(tool_key=ToolKey.CLASSIFIER.value, parent=parent, title="TensorFlow")
        self.logger.info("TensorFlow plugin carregado", code="TOOL_READY")

    def _build_ui(self):
        super()._build_ui()
        main_layout = self.main_layout

        self.badge_status = self.page.set_badge(self.page.PRONTA)

        # --- ACTION BUTTONS ---
        self._btns = ExecutionButtons(self)
        self._btns.setup(
            {
                "load_cfg": {
                    "text": "Carregar Config",
                    "type": "secondary",
                    "description": "Carrega uma configuração salva anteriormente",
                },
                "save_cfg": {
                    "text": "Salvar Config",
                    "type": "secondary",
                    "description": "Salva a configuração atual em disco",
                },
                "reset_cfg": {
                    "text": "Restaurar Padrao",
                    "type": "secondary",
                    "description": "Restaura configurações para o valor padrão",
                },
                "cancelar": {
                    "text": "CANCELAR",
                    "type": "danger",
                    "description": "Cancela a execução em andamento",
                },
                "executar": {
                    "text": "EXECUTAR PIPELINE",
                    "type": "primary",
                    "description": "Inicia o pipeline de classificação",
                },
            }
        )
        self._btns.set_enabled("cancelar", False)
        main_layout.addWidget(self._btns)

        # =====================================================================
        # TOP ROW — Imagens & Saida | Persistencia do Modelo
        # =====================================================================

        grp_img = GroupPainel("Imagens & Saida")
        sel_grid = SelectorGrid(
            {
                "Imagem Treino": {
                    "file_filter": "GeoTIFF (*.tif *.tiff)",
                    "default_path": "dados/imagemTreino.tif",
                },
                "Imagem Classif.": {
                    "file_filter": "GeoTIFF (*.tif *.tiff)",
                    "default_path": "dados/imagemCompleta.tif",
                },
                "Saida GeoTIFF": {
                    "file_filter": "GeoTIFF (*.tif *.tiff)",
                    "default_path": "resultado/mapa_classificado_ui.tif",
                    "browse_mode": "save_file",
                },
            },
            title=None,
        )
        self._sel_img_treino = sel_grid["Imagem Treino"]
        self._sel_img_classif = sel_grid["Imagem Classif."]
        self._sel_img_saida = sel_grid["Saida GeoTIFF"]
        grp_img.group_layout.addWidget(sel_grid)
        grp_img.group_layout.addStretch()

        grp_mod = GroupPainel("Persistencia do Modelo")
        self.combo_model_action = SimpleComboBox(
            items=["Treinar modelo novo", "Treinar modelo existente", "Usar modelo existente"],
            label="Acao:",
        )
        grp_mod.group_layout.addWidget(self.combo_model_action)
        self.row_modelo_existente = SimpleSelector(
            "Modelo Existente", "", file_filter="Keras Model (*.keras)"
        )
        self.row_modelo_existente.setVisible(False)
        grp_mod.group_layout.addWidget(self.row_modelo_existente)
        self.btn_listar_modelos = SimpleGhostButton("Listar Modelos")
        self.btn_listar_modelos.setVisible(False)
        grp_mod.group_layout.addWidget(self.btn_listar_modelos, alignment=Qt.AlignmentFlag.AlignLeft)
        self.grid_salvar_modelo = GridCheckBox({
            "save_model": {
                "label": "Salvar modelo (.keras)",
                "description": "Salvar o modelo treinado em disco (.keras)",
                "default": True,
            },
        }, num_columns=1)
        grp_mod.group_layout.addWidget(self.grid_salvar_modelo)
        self.row_modelo_path = SimpleSelector(
            "Caminho",
            "resultado/modelo_ui.keras",
            file_filter="Keras Model (*.keras)",
            browse_mode="save_file",
        )
        grp_mod.group_layout.addWidget(self.row_modelo_path)
        grp_mod.group_layout.addStretch()

        top_row = GridGroupPainel(grp_img, grp_mod)
        main_layout.addWidget(top_row)

        # =====================================================================
        # BOTTOM ROW — Shapefiles | Rede Neural & Treinamento
        # =====================================================================

        grp_shp = GroupPainel("Shapefiles por Classe")
        self.table_shp = ItemTable(
            columns=[
                {"header": "Caminho", "type": "text", "stretch": True, "editable": False},
                {"header": "ID",      "type": "spin", "width": 55, "min": 0, "max": 999},
                {"header": "Legenda", "type": "line", "width": 90, "placeholder": "Legenda..."},
                {"header": "",        "type": "remove", "width": 65},
            ]
        )
        grp_shp.group_layout.addWidget(self.table_shp)
        self.btn_add_shp = SimpleGhostButton("+ Adicionar Shapefile")
        grp_shp.group_layout.addWidget(self.btn_add_shp, alignment=Qt.AlignmentFlag.AlignLeft)
        grp_shp.group_layout.addStretch()

        # =====================================================================
        # REDE NEURAL & TREINAMENTO — composto por widgets genéricos
        # =====================================================================

        grp_rede = GroupPainel("Rede Neural & Treinamento")

        # Camadas (GridLineEdit — 1 campo genérico)
        self.grid_camadas = GridLineEdit({
            "camadas": {
                "label": "Camadas:",
                "default": "128, 64, 32",
                "placeholder": "ex: 256, 128, 64",
                "description": "Neurônios por camada oculta, separados por vírgula",
            },
        })
        grp_rede.group_layout.addWidget(self.grid_camadas)

        # Ativação (SimpleComboBox)
        self.combo_ativacao = SimpleComboBox(
            items=["relu", "elu", "tanh", "sigmoid", "linear"],
            label="Ativacao:",
        )
        self.combo_ativacao.current_value = "relu"
        grp_rede.group_layout.addWidget(self.combo_ativacao)

        # Campos numéricos (GridDoubleSpinBox) em 2 colunas
        self.grid_numericos = GridDoubleSpinBox({
            "dropout": {
                "label": "Dropout:",
                "decimal": 2,
                "default": 0.10,
                "min": 0.0,
                "max": 0.9,
                "step": 0.05,
                "description": "Taxa de dropout para regularização",
            },
            "epochs": {
                "label": "Epocas:",
                "decimal": 0,
                "default": 150,
                "min": 1,
                "max": 10000,
                "step": 1,
                "description": "Número de épocas de treinamento",
            },
            "batch_train": {
                "label": "Batch Treino:",
                "decimal": 0,
                "default": 64,
                "min": 1,
                "max": 8192,
                "step": 1,
                "description": "Tamanho do lote para treinamento",
            },
            "batch_pred": {
                "label": "Batch Pred.:",
                "decimal": 0,
                "default": 4096,
                "min": 1,
                "max": 65536,
                "step": 1,
                "description": "Tamanho do lote para predição",
            },
            "test_size": {
                "label": "Test Size:",
                "decimal": 2,
                "default": 0.30,
                "min": 0.01,
                "max": 0.99,
                "step": 0.01,
                "description": "Proporção dos dados para validação",
            },
            "random_state": {
                "label": "Random State:",
                "decimal": 0,
                "default": 42,
                "min": 0,
                "max": 999999,
                "step": 1,
                "description": "Semente aleatória para reprodutibilidade",
            },
            "ram_pct": {
                "label": "RAM:",
                "decimal": 0,
                "default": 70,
                "min": 10,
                "max": 95,
                "step": 1,
                "suffix": "%",
                "description": "Limite percentual de RAM utilizável",
            },
            "nodata_limiar": {
                "label": "Limiar Nodata:",
                "decimal": 0,
                "default": 250,
                "min": 0,
                "max": 255,
                "step": 1,
                "description": "Valor de limiar para considerar nodata",
            },
        }, columns=2)
        grp_rede.group_layout.addWidget(self.grid_numericos)

        # Checkboxes (GridCheckBox)
        self.grid_checkboxes = GridCheckBox({
            "use_mask": {
                "label": "Mascara alpha",
                "description": "Aplicar máscara alpha na saída",
                "default": True,
            },
            "zero_nodata": {
                "label": "0 = nodata",
                "description": "Considerar valor 0 como nodata",
                "default": False,
            },
        }, num_columns=2)
        grp_rede.group_layout.addWidget(self.grid_checkboxes)

        grp_rede.group_layout.addStretch()

        bottom_row = GridGroupPainel(grp_shp, grp_rede)
        main_layout.addWidget(bottom_row)

        # --- Resumo hidden (compatibilidade controller) ---
        self.lbl_resumo = QTextEdit()
        self.lbl_resumo.setReadOnly(True)
        self.lbl_resumo.setMaximumHeight(1)
        self.lbl_resumo.setVisible(False)
        main_layout.addWidget(self.lbl_resumo)

        # --- Apply field tooltips ---
        self._apply_field_tooltips()

    def _apply_field_tooltips(self):
        mapping = [
            (
                "training_image",
                [
                    self._sel_img_treino.label,
                    self._sel_img_treino.edit,
                    self._sel_img_treino.btn,
                ],
            ),
            (
                "classification_image",
                [
                    self._sel_img_classif.label,
                    self._sel_img_classif.edit,
                    self._sel_img_classif.btn,
                ],
            ),
            (
                "output_tiff",
                [
                    self._sel_img_saida.label,
                    self._sel_img_saida.edit,
                    self._sel_img_saida.btn,
                ],
            ),
            ("hidden_layers", [self.grid_camadas]),
            ("activation", [self.combo_ativacao]),
            ("dropout_rate", [self.grid_numericos]),
            ("epochs", [self.grid_numericos]),
            ("batch_size_train", [self.grid_numericos]),
            ("batch_size_pred", [self.grid_numericos]),
            ("test_size", [self.grid_numericos]),
            ("random_state", [self.grid_numericos]),
            ("ram_limit_pct", [self.grid_numericos]),
            ("use_mask", [self.grid_checkboxes]),
            ("zero_as_nodata", [self.grid_checkboxes]),
            ("nodata_threshold", [self.grid_numericos]),
            ("model_action", [self.combo_model_action]),
            (
                "existing_model_path",
                [
                    self.row_modelo_existente.label,
                    self.row_modelo_existente.edit,
                    self.row_modelo_existente.btn,
                ],
            ),
            ("save_model", [self.grid_salvar_modelo]),
            (
                "model_path",
                [
                    self.row_modelo_path.label,
                    self.row_modelo_path.edit,
                    self.row_modelo_path.btn,
                ],
            ),
        ]
        for key, widgets in mapping:
            spec = UI_FIELD_SPECS.get(key)
            desc = spec.description if spec else ""
            if not desc:
                continue
            for widget in widgets:
                widget.setToolTip(desc)

    # ────────────────────────────────────────────────────────────────────────
    # Métodos públicos (compatibilidade com controller)
    # ────────────────────────────────────────────────────────────────────────

    def add_shp_row_ui(self, path: str, classe: int, legenda: str = ""):
        """Adiciona uma linha na tabela de shapefiles (chamado pelo controller)."""
        self.table_shp.add_row(path, classe, legenda)

    # ─── Exposição de campos para compatibilidade com o controller ─────

    @property
    def edit_camadas(self):
        """Compatibilidade: QLineEdit de camadas."""
        return self.grid_camadas.widget("camadas")

    @property
    def spin_dropout(self):
        """Compatibilidade: spin de dropout."""
        return self.grid_numericos.widget("dropout")

    @property
    def spin_epochs(self):
        return self.grid_numericos.widget("epochs")

    @property
    def spin_batch_train(self):
        return self.grid_numericos.widget("batch_train")

    @property
    def spin_batch_pred(self):
        return self.grid_numericos.widget("batch_pred")

    @property
    def spin_test_size(self):
        return self.grid_numericos.widget("test_size")

    @property
    def spin_random(self):
        return self.grid_numericos.widget("random_state")

    @property
    def spin_ram(self):
        return self.grid_numericos.widget("ram_pct")

    @property
    def spin_alpha(self):
        return self.grid_numericos.widget("nodata_limiar")

    @property
    def chk_mascara(self):
        """Compatibilidade: QCheckBox de máscara."""
        return self.grid_checkboxes.widget("use_mask")

    @property
    def chk_zero_nodata(self):
        return self.grid_checkboxes.widget("zero_nodata")

    @property
    def chk_salvar_modelo(self):
        """Compatibilidade: QCheckBox de salvar modelo."""
        return self.grid_salvar_modelo.widget("save_model")
