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
    QLabel,
    QLineEdit,
    QSpinBox,
    QDoubleSpinBox,
    QCheckBox,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QTextEdit,
    QFrame,
    QSizePolicy,
    QGridLayout,QComboBox,
)
from PySide6.QtCore import Qt
from plugins.BasePlugin import BasePlugin
from core.enum.ToolKey import ToolKey
from resources.widgets.ExecutionButtons import ExecutionButtons
from resources.widgets.SimpleGhostButton import SimpleGhostButton
from resources.widgets.SimpleRemoveButton import SimpleRemoveButton
from resources.widgets.GroupPainel import GroupPainel
from resources.widgets.SimpleSelector import SimpleSelector
from resources.widgets.SelectorGrid import SelectorGrid
from resources.widgets.SimpleComboBox import SimpleComboBox
from resources.widgets.GridGroupPainel import GridGroupPainel
from resources.widgets.ItemTable import ItemTable
from plugins.tensorflow_classifier.tensor_utils.ui_field_specs import UI_FIELD_SPECS

# =============================================================================
# WIDGETS AUXILIARES
# =============================================================================


class Separator(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("separator")
        self.setFrameShape(QFrame.Shape.HLine)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.setFixedHeight(1)


# =============================================================================
# FERRAMENTA DE CLASSIFICAÇÃO
# =============================================================================


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

        # ---- (col 0) - IMAGENS & SAIDA ----
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

        # ---- (col 1) - PERSISTENCIA DO MODELO ----
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
        self.chk_salvar_modelo = QCheckBox("Salvar modelo (.keras)")
        self.chk_salvar_modelo.setChecked(True)
        grp_mod.group_layout.addWidget(self.chk_salvar_modelo)
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

        # ---- (col 0) - SHAPEFILES ----
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

        # ---- (col 1) - REDE NEURAL & TREINAMENTO ----
        grp_rede = GroupPainel("Rede Neural & Treinamento", layout_type=QGridLayout)
        lr = grp_rede.group_layout

        # Row 0: Camadas Ocultas + Ativacao
        lr.addWidget(QLabel("Camadas:"), 0, 0)
        self.edit_camadas = QLineEdit("128, 64, 32")
        self.edit_camadas.setPlaceholderText("ex: 256, 128, 64")
        lr.addWidget(self.edit_camadas, 0, 1)
        lr.addWidget(QLabel("Ativacao:"), 0, 2)
        self.combo_ativacao = QComboBox()
        self.combo_ativacao.addItems(["relu", "elu", "tanh", "sigmoid", "linear"])
        self.combo_ativacao.setCurrentText("relu")
        lr.addWidget(self.combo_ativacao, 0, 3)

        # Row 1: Dropout + Epocas
        lr.addWidget(QLabel("Dropout:"), 1, 0)
        self.spin_dropout = QDoubleSpinBox()
        self.spin_dropout.setRange(0.0, 0.9)
        self.spin_dropout.setSingleStep(0.05)
        self.spin_dropout.setDecimals(2)
        self.spin_dropout.setValue(0.1)
        lr.addWidget(self.spin_dropout, 1, 1)
        lr.addWidget(QLabel("Epocas:"), 1, 2)
        self.spin_epochs = QSpinBox()
        self.spin_epochs.setRange(1, 10000)
        self.spin_epochs.setValue(150)
        lr.addWidget(self.spin_epochs, 1, 3)

        # Row 2: Batch Treino + Batch Pred
        lr.addWidget(QLabel("Batch Treino:"), 2, 0)
        self.spin_batch_train = QSpinBox()
        self.spin_batch_train.setRange(1, 8192)
        self.spin_batch_train.setValue(64)
        lr.addWidget(self.spin_batch_train, 2, 1)
        lr.addWidget(QLabel("Batch Pred.:"), 2, 2)
        self.spin_batch_pred = QSpinBox()
        self.spin_batch_pred.setRange(1, 65536)
        self.spin_batch_pred.setValue(4096)
        lr.addWidget(self.spin_batch_pred, 2, 3)

        # Row 3: Test Size + Random State
        lr.addWidget(QLabel("Test Size:"), 3, 0)
        self.spin_test_size = QDoubleSpinBox()
        self.spin_test_size.setRange(0.01, 0.99)
        self.spin_test_size.setSingleStep(0.01)
        self.spin_test_size.setDecimals(2)
        self.spin_test_size.setValue(0.30)
        lr.addWidget(self.spin_test_size, 3, 1)
        lr.addWidget(QLabel("Random State:"), 3, 2)
        self.spin_random = QSpinBox()
        self.spin_random.setRange(0, 999999)
        self.spin_random.setValue(42)
        lr.addWidget(self.spin_random, 3, 3)

        # Row 4: RAM % + Mascara + Nodata
        lr.addWidget(QLabel("RAM:"), 4, 0)
        self.spin_ram = QSpinBox()
        self.spin_ram.setRange(10, 95)
        self.spin_ram.setValue(70)
        self.spin_ram.setSuffix(" %")
        lr.addWidget(self.spin_ram, 4, 1)
        self.chk_mascara = QCheckBox("Mascara alpha")
        self.chk_mascara.setChecked(True)
        lr.addWidget(self.chk_mascara, 4, 2)
        self.chk_zero_nodata = QCheckBox("0 = nodata")
        self.chk_zero_nodata.setChecked(False)
        lr.addWidget(self.chk_zero_nodata, 4, 3)

        # Row 5: Limiar nodata
        lr.addWidget(QLabel("Limiar Nodata:"), 5, 0)
        self.spin_alpha = QSpinBox()
        self.spin_alpha.setRange(0, 255)
        self.spin_alpha.setValue(250)
        lr.addWidget(self.spin_alpha, 5, 1)

        lr.setColumnStretch(0, 0)
        lr.setColumnStretch(1, 1)
        lr.setColumnStretch(2, 0)
        lr.setColumnStretch(3, 1)
        lr.setRowStretch(5, 1)

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
            ("hidden_layers", [self.edit_camadas]),
            ("activation", [self.combo_ativacao]),
            ("dropout_rate", [self.spin_dropout]),
            ("epochs", [self.spin_epochs]),
            ("batch_size_train", [self.spin_batch_train]),
            ("batch_size_pred", [self.spin_batch_pred]),
            ("test_size", [self.spin_test_size]),
            ("random_state", [self.spin_random]),
            ("ram_limit_pct", [self.spin_ram]),
            ("use_mask", [self.chk_mascara]),
            ("zero_as_nodata", [self.chk_zero_nodata]),
            ("nodata_threshold", [self.spin_alpha]),
            ("model_action", [self.combo_model_action]),
            (
                "existing_model_path",
                [
                    self.row_modelo_existente.label,
                    self.row_modelo_existente.edit,
                    self.row_modelo_existente.btn,
                ],
            ),
            ("save_model", [self.chk_salvar_modelo]),
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
