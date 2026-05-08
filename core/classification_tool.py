# -*- coding: utf-8 -*-
"""
ClassificationTool — Ferramenta de Classificação Raster
=========================================================
Widget extraído da UI principal para ser uma ferramenta
hospedada no Workspace do Aetheris ToolBox.
Console removido — agora é compartilhado via ConsoleTool.
"""

from __future__ import annotations

from pathlib import Path
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QSpinBox, QDoubleSpinBox, QComboBox, QCheckBox,
    QTableWidget, QTableWidgetItem, QHeaderView, QFileDialog,
    QGroupBox, QTextEdit, QProgressBar, QFrame,
    QSizePolicy, QGridLayout, QScrollArea
)
from PySide6.QtCore import Qt
from core.styles import AppStyles, Palette
from core.ui_field_specs import UI_FIELD_SPECS


# =============================================================================
# WIDGETS AUXILIARES
# =============================================================================

class Badge(QLabel):
    def __init__(self, text: str, parent=None):
        super().__init__(text, parent)
        self.setObjectName("section_badge")
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)


class Separator(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("separator")
        self.setFrameShape(QFrame.Shape.HLine)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.setFixedHeight(1)


class PathBrowseRow(QWidget):
    def __init__(self, label_text: str, default_path: str = "", file_mode=True,
                 file_filter="Todos (*.*)", browse_mode: str = "open_file", parent=None):
        super().__init__(parent)
        self.file_mode = file_mode
        self.file_filter = file_filter
        self.browse_mode = browse_mode

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)

        self.label = QLabel(label_text)
        self.label.setFixedWidth(130)

        self.edit = QLineEdit(default_path)
        self.edit.setPlaceholderText("Caminho do arquivo...")

        self.btn = QPushButton("...")
        self.btn.setObjectName("btn_secondary")
        self.btn.setFixedWidth(30)
        self.btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn.clicked.connect(self._browse)

        layout.addWidget(self.label)
        layout.addWidget(self.edit, 1)
        layout.addWidget(self.btn)

    def _browse(self):
        if self.browse_mode == "save_file":
            path, _ = QFileDialog.getSaveFileName(
                self, "Salvar arquivo", self.edit.text().strip() or "", self.file_filter
            )
        elif self.browse_mode == "directory":
            path = QFileDialog.getExistingDirectory(self, "Selecionar pasta")
        elif self.file_mode:
            path, _ = QFileDialog.getOpenFileName(
                self, "Selecionar arquivo", "", self.file_filter
            )
        else:
            path = QFileDialog.getExistingDirectory(self, "Selecionar pasta")
        if path:
            self.edit.setText(path)

    def path(self) -> str:
        return self.edit.text().strip()


# =============================================================================
# FERRAMENTA DE CLASSIFICAÇÃO
# =============================================================================

class ClassificationTool(QWidget):
    """
    Widget completo da ferramenta de classificação raster.
    Pode ser hospedado no Workspace.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self._build_ui()

    def _make_group_box(self, title: str) -> QGroupBox:
        """Cria um GroupBox com titulo DENTRO do box (nao sobre a borda)."""
        gb = QGroupBox(title)
        return gb

    def _build_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(18, 10, 18, 10)
        main_layout.setSpacing(8)

        # --- HEADER ---
        header = QWidget()
        hl = QHBoxLayout(header)
        hl.setContentsMargins(0, 0, 0, 0)
        hl.setSpacing(10)
        tc = QVBoxLayout()
        tc.setSpacing(2)
        self.lbl_title = QLabel("Aetheris Classifier")
        self.lbl_title.setObjectName("header_title")
        self.lbl_subtitle = QLabel("Pipeline de classificacao supervisionada com redes neurais profundas")
        self.lbl_subtitle.setObjectName("header_subtitle")
        self.lbl_subtitle.setWordWrap(True)
        tc.addWidget(self.lbl_title)
        tc.addWidget(self.lbl_subtitle)
        hl.addLayout(tc, 1)
        self.badge_status = Badge("PRONTA")
        self.badge_status.setStyleSheet(AppStyles.badge_success())
        hl.addWidget(self.badge_status, alignment=Qt.AlignmentFlag.AlignVCenter)
        main_layout.addWidget(header)
        main_layout.addWidget(Separator())

        # --- ACTION BUTTONS ---
        ab = QWidget()
        al = QHBoxLayout(ab)
        al.setContentsMargins(0, 0, 0, 0)
        al.setSpacing(6)
        self.btn_load_cfg = QPushButton("Carregar Config")
        self.btn_load_cfg.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_load_cfg.setStyleSheet(AppStyles.btn_secondary_style())
        self.btn_load_cfg.setMinimumHeight(32)
        self.btn_save_cfg = QPushButton("Salvar Config")
        self.btn_save_cfg.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_save_cfg.setStyleSheet(AppStyles.btn_secondary_style())
        self.btn_save_cfg.setMinimumHeight(32)
        self.btn_reset_cfg = QPushButton("Restaurar Padrao")
        self.btn_reset_cfg.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_reset_cfg.setStyleSheet(AppStyles.btn_secondary_style())
        self.btn_reset_cfg.setMinimumHeight(32)
        self.btn_clear_console = QPushButton("Limpar Console")
        self.btn_clear_console.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_clear_console.setStyleSheet(AppStyles.btn_secondary_style())
        self.btn_clear_console.setMinimumHeight(32)
        self.btn_cancelar = QPushButton("CANCELAR")
        self.btn_cancelar.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_cancelar.setEnabled(False)
        self.btn_cancelar.setStyleSheet(AppStyles.btn_danger_style())
        self.btn_cancelar.setMinimumHeight(32)
        self.btn_cancelar.setMinimumWidth(100)
        al.addWidget(self.btn_load_cfg)
        al.addWidget(self.btn_save_cfg)
        al.addWidget(self.btn_reset_cfg)
        al.addWidget(self.btn_clear_console)
        al.addWidget(self.btn_cancelar)
        al.addStretch()
        self.btn_executar = QPushButton("EXECUTAR PIPELINE")
        self.btn_executar.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_executar.setStyleSheet(AppStyles.btn_primary_style())
        self.btn_executar.setMinimumWidth(180)
        self.btn_executar.setMinimumHeight(34)
        al.addWidget(self.btn_executar)
        main_layout.addWidget(ab)

        # =====================================================================
        # GRID 2x2
        # =====================================================================
        grid = QGridLayout()
        grid.setSpacing(10)

        # ---- (0,0) - IMAGENS & SAIDA ----
        grp_img = self._make_group_box("Imagens & Saida")
        li = QVBoxLayout(grp_img)
        li.setSpacing(6)
        li.setContentsMargins(6, 6, 6, 6)
        self.row_img_treino = PathBrowseRow("Imagem Treino", "dados/imagemTreino.tif",
            file_filter="GeoTIFF (*.tif *.tiff)")
        self.row_img_classif = PathBrowseRow("Imagem Classif.", "dados/imagemCompleta.tif",
            file_filter="GeoTIFF (*.tif *.tiff)")
        self.row_img_saida = PathBrowseRow("Saida GeoTIFF", "resultado/mapa_classificado_ui.tif",
            file_filter="GeoTIFF (*.tif *.tiff)", browse_mode="save_file")
        li.addWidget(self.row_img_treino)
        li.addWidget(self.row_img_classif)
        li.addWidget(self.row_img_saida)
        li.addStretch()
        grid.addWidget(grp_img, 0, 0)

        # ---- (0,1) - PERSISTENCIA DO MODELO ----
        grp_mod = self._make_group_box("Persistencia do Modelo")
        lm = QVBoxLayout(grp_mod)
        lm.setSpacing(6)
        lm.setContentsMargins(6, 6, 6, 6)
        rm = QHBoxLayout()
        rm.setSpacing(6)
        rm.addWidget(QLabel("Acao:"))
        self.combo_model_action = QComboBox()
        self.combo_model_action.addItems([
            "Treinar modelo novo", "Treinar modelo existente", "Usar modelo existente"
        ])
        self.combo_model_action.setCurrentText("Treinar modelo novo")
        rm.addWidget(self.combo_model_action, 1)
        lm.addLayout(rm)
        self.row_modelo_existente = PathBrowseRow("Modelo Existente", "",
            file_filter="Keras Model (*.keras)")
        self.row_modelo_existente.setVisible(False)
        lm.addWidget(self.row_modelo_existente)
        self.btn_listar_modelos = QPushButton("Listar Modelos")
        self.btn_listar_modelos.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_listar_modelos.setStyleSheet(AppStyles.btn_ghost_style())
        self.btn_listar_modelos.setVisible(False)
        lm.addWidget(self.btn_listar_modelos, alignment=Qt.AlignmentFlag.AlignLeft)
        self.chk_salvar_modelo = QCheckBox("Salvar modelo (.keras)")
        self.chk_salvar_modelo.setChecked(True)
        lm.addWidget(self.chk_salvar_modelo)
        self.row_modelo_path = PathBrowseRow("Caminho", "resultado/modelo_ui.keras",
            file_filter="Keras Model (*.keras)")
        lm.addWidget(self.row_modelo_path)
        lm.addStretch()
        grid.addWidget(grp_mod, 0, 1)

        # ---- (1,0) - SHAPEFILES ----
        grp_shp = self._make_group_box("Shapefiles por Classe")
        ls = QVBoxLayout(grp_shp)
        ls.setSpacing(6)
        ls.setContentsMargins(6, 6, 6, 6)
        self.table_shp = QTableWidget(0, 4)
        self.table_shp.setHorizontalHeaderLabels(["Caminho", "ID", "Legenda", ""])
        hh = self.table_shp.horizontalHeader()
        hh.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        hh.setSectionResizeMode(1, QHeaderView.ResizeMode.Fixed)
        hh.setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)
        hh.setSectionResizeMode(3, QHeaderView.ResizeMode.Fixed)
        self.table_shp.setColumnWidth(1, 55)
        self.table_shp.setColumnWidth(2, 90)
        self.table_shp.setColumnWidth(3, 65)
        self.table_shp.setMinimumHeight(100)
        self.table_shp.verticalHeader().setDefaultSectionSize(24)
        ls.addWidget(self.table_shp)
        btn_add_shp = QPushButton("+ Adicionar Shapefile")
        btn_add_shp.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_add_shp.setStyleSheet(AppStyles.btn_ghost_style())
        self.btn_add_shp = btn_add_shp
        ls.addWidget(btn_add_shp, alignment=Qt.AlignmentFlag.AlignLeft)
        ls.addStretch()
        grid.addWidget(grp_shp, 1, 0)

        # ---- (1,1) - REDE NEURAL & TREINAMENTO ----
        grp_rede = self._make_group_box("Rede Neural & Treinamento")
        lr = QGridLayout(grp_rede)
        lr.setSpacing(6)
        lr.setContentsMargins(6, 6, 6, 6)

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

        # Row 1: Dropout + Epocas + Batch Treino
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

        # Row 4: RAM % + Mascara + Nodata + Limiar
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

        grid.addWidget(grp_rede, 1, 1)

        grid.setColumnStretch(0, 1)
        grid.setColumnStretch(1, 1)
        grid.setRowStretch(0, 1)
        grid.setRowStretch(1, 1)

        main_layout.addLayout(grid)

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
            ("training_image", [self.row_img_treino.label, self.row_img_treino.edit, self.row_img_treino.btn]),
            ("classification_image", [self.row_img_classif.label, self.row_img_classif.edit, self.row_img_classif.btn]),
            ("output_tiff", [self.row_img_saida.label, self.row_img_saida.edit, self.row_img_saida.btn]),
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
            ("existing_model_path", [self.row_modelo_existente.label, self.row_modelo_existente.edit, self.row_modelo_existente.btn]),
            ("save_model", [self.chk_salvar_modelo]),
            ("model_path", [self.row_modelo_path.label, self.row_modelo_path.edit, self.row_modelo_path.btn]),
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
        row = self.table_shp.rowCount()
        self.table_shp.insertRow(row)
        ip = QTableWidgetItem(path)
        ip.setFlags(ip.flags() & ~Qt.ItemFlag.ItemIsEditable)
        self.table_shp.setItem(row, 0, ip)
        sc = QSpinBox()
        sc.setRange(0, 999)
        sc.setValue(classe)
        sc.setStyleSheet("background-color: transparent; border: none;")
        self.table_shp.setCellWidget(row, 1, sc)
        el = QLineEdit(legenda)
        el.setPlaceholderText("Legenda...")
        el.setStyleSheet("background-color: transparent; border: none;")
        self.table_shp.setCellWidget(row, 2, el)
        br = QPushButton("Remover")
        br.setCursor(Qt.CursorShape.PointingHandCursor)
        br.setStyleSheet(AppStyles.btn_remove_style())
        br.clicked.connect(lambda checked, r=row: self._remove_shp_row_ui(r))
        self.table_shp.setCellWidget(row, 3, br)

    def _remove_shp_row_ui(self, row: int):
        """Remove uma linha da tabela de shapefiles."""
        self.table_shp.removeRow(row)
        for r in range(self.table_shp.rowCount()):
            btn = self.table_shp.cellWidget(r, 3)
            if btn:
                try:
                    btn.clicked.disconnect()
                except Exception:
                    pass
                btn.clicked.connect(lambda checked, fixed_row=r: self._remove_shp_row_ui(fixed_row))