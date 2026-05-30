#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
==============================================
🧾 App: Conversor ICO (PySide6)
Autor: M. Martinelli (adaptado)
Versão: 1.0
Identificador: pyd6_ico_conv_v1
==============================================

Funcionalidades:
- Selecionar arquivos e pastas (diálogo);
- Drag & drop de arquivos/pastas na lista (reordenáveis, seleção múltipla);
- Miniaturas na lista e pré-visualização;
- Checkboxes para múltiplos tamanhos (16,32,48,64,128,256) como na imagem;
- Apenas 32 bits (alpha/transparência) — fixo;
- Gerar um arquivo .ICO por imagem, contendo as resoluções selecionadas;
- Escolher pasta de saída antes da geração;
- Barra de progresso, log em pasta oculta "log" na raiz do script;
- Remover itens, limpar lista, mover cima/baixo.
"""

import os
import sys
import ctypes
from datetime import datetime
from io import BytesIO
from PIL import Image

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QPushButton, QLabel,
    QFileDialog, QListWidget, QVBoxLayout, QHBoxLayout,
    QSpinBox, QComboBox, QTabWidget, QListWidgetItem,
    QGraphicsView, QGraphicsScene, QToolBar, QCheckBox,
    QProgressBar, QSplitter, QMessageBox
)

from PySide6.QtGui import QAction, QPixmap, QIcon, QImage
from PySide6.QtCore import Qt, QSize
# -----------------------------
# Config
# -----------------------------
APP_ID = "pyd6_ico_conv_v1"
LOGCODE = APP_ID
# developer-provided uploaded image path (used as window icon if available)
DEV_IMAGE_PATH = "/mnt/data/7c7513ec-8014-4310-b836-b5126e53c66d.png"

# -----------------------------
# Logging utilities
# -----------------------------
def criar_pasta_log(raiz):
    log_dir = os.path.join(raiz, "log")
    os.makedirs(log_dir, exist_ok=True)
    # tornar oculta no Windows
    try:
        if os.name == "nt":
            FILE_ATTRIBUTE_HIDDEN = 0x02
            ctypes.windll.kernel32.SetFileAttributesW(log_dir, FILE_ATTRIBUTE_HIDDEN)
    except Exception:
        pass
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    return os.path.join(log_dir, f"{LOGCODE}_LOG_{ts}.txt")

def escrever_log(caminho_log, msg):
    try:
        with open(caminho_log, "a", encoding="utf-8") as f:
            f.write(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - {msg}\n")
    except Exception:
        # falha de log não deve quebrar app
        pass

# -----------------------------
# Reorderable QListWidget com drag & drop de arquivos/pastas
# -----------------------------
class ReorderableListWidget(QListWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAcceptDrops(True)
        self.setDragEnabled(True)
        self.setDragDropMode(QListWidget.InternalMove)
        self.setDefaultDropAction(Qt.MoveAction)
        self.setSelectionMode(QListWidget.ExtendedSelection)
        self.setIconSize(QSize(120, 80))

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            super().dragEnterEvent(event)

    def dragMoveEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            super().dragMoveEvent(event)

    def dropEvent(self, event):
        if event.mimeData().hasUrls():
            paths = []
            for url in event.mimeData().urls():
                if url.isLocalFile():
                    paths.append(url.toLocalFile())
            self.add_files(paths)
            event.acceptProposedAction()
        else:
            super().dropEvent(event)

    def add_files(self, paths):
        exts = {'.png', '.jpg', '.jpeg', '.tif', '.tiff', '.bmp', '.gif', '.webp'}
        for p in paths:
            if os.path.isdir(p):
                for fname in sorted(os.listdir(p)):
                    fp = os.path.join(p, fname)
                    if os.path.splitext(fname)[1].lower() in exts:
                        self._add_item(fp)
            else:
                if os.path.splitext(p)[1].lower() in exts:
                    self._add_item(p)

    def _add_item(self, path):
        # evita duplicatas (comparando caminho absoluto)
        for i in range(self.count()):
            if self.item(i).data(Qt.UserRole) == path:
                return
        item = QListWidgetItem(os.path.basename(path))
        item.setToolTip(path)
        item.setData(Qt.UserRole, path)
        # tentativa de miniatura
        try:
            img = Image.open(path)
            img.thumbnail((240, 160), Image.LANCZOS)
            bio = BytesIO()
            img.convert("RGBA").save(bio, format="PNG")
            qimg = QImage.fromData(bio.getvalue())
            pix = QPixmap.fromImage(qimg)
            item.setIcon(pix)
        except Exception:
            pass
        self.addItem(item)

    def get_ordered_paths(self):
        return [self.item(i).data(Qt.UserRole) for i in range(self.count())]

# -----------------------------
# Main Window
# -----------------------------
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Conversor ICO (PySide6)")
        self.resize(1100, 700)

        # window icon (try developer image)
        if os.path.exists(DEV_IMAGE_PATH):
            try:
                self.setWindowIcon(QIcon(DEV_IMAGE_PATH))
            except Exception:
                pass

        # root folder & log
        self.root_folder = os.path.dirname(os.path.realpath(__file__))
        self.log_path = criar_pasta_log(self.root_folder)
        escrever_log(self.log_path, "Aplicação iniciada")

        # Widgets
        central = QWidget()
        main_layout = QVBoxLayout()
        central.setLayout(main_layout)
        self.setCentralWidget(central)

        # Toolbar
        toolbar = QToolBar("Principal")
        self.addToolBar(toolbar)

        act_add_files = QAction("Adicionar arquivos", self)
        act_add_files.triggered.connect(self.add_files_dialog)
        toolbar.addAction(act_add_files)

        act_add_folder = QAction("Adicionar pasta", self)
        act_add_folder.triggered.connect(self.add_folder_dialog)
        toolbar.addAction(act_add_folder)

        act_clear = QAction("Limpar lista", self)
        act_clear.triggered.connect(self.clear_list)
        toolbar.addAction(act_clear)

        # Splitter: left list / right preview & controls
        splitter = QSplitter()
        main_layout.addWidget(splitter)

        # Left: list + buttons
        left_widget = QWidget()
        left_layout = QVBoxLayout()
        left_widget.setLayout(left_layout)

        left_layout.addWidget(QLabel("Imagens (arraste arquivos/pastas aqui):"))
        self.list_widget = ReorderableListWidget()
        left_layout.addWidget(self.list_widget)

        btns_h = QHBoxLayout()
        btn_add = QPushButton("➕ Adicionar Arquivos")
        btn_add.clicked.connect(self.add_files_dialog)
        btn_folder = QPushButton("📁 Adicionar Pasta")
        btn_folder.clicked.connect(self.add_folder_dialog)
        btn_remove = QPushButton("🗑 Remover Selecionados")
        btn_remove.clicked.connect(self.remove_selected)
        btn_clear2 = QPushButton("✖ Limpar Tudo")
        btn_clear2.clicked.connect(self.clear_list)
        btns_h.addWidget(btn_add)
        btns_h.addWidget(btn_folder)
        btns_h.addWidget(btn_remove)
        btns_h.addWidget(btn_clear2)
        left_layout.addLayout(btns_h)

        # Move up/down
        move_h = QHBoxLayout()
        btn_up = QPushButton("⬆ Mover acima")
        btn_up.clicked.connect(self.move_up)
        btn_down = QPushButton("⬇ Mover abaixo")
        btn_down.clicked.connect(self.move_down)
        move_h.addWidget(btn_up)
        move_h.addWidget(btn_down)
        left_layout.addLayout(move_h)

        splitter.addWidget(left_widget)

        # Right: preview, options and generate
        right_widget = QWidget()
        right_layout = QVBoxLayout()
        right_widget.setLayout(right_layout)

        right_layout.addWidget(QLabel("Pré-visualização:"))
        self.preview_label = QLabel("Nenhuma imagem selecionada")
        self.preview_label.setAlignment(Qt.AlignCenter)
        self.preview_label.setFixedSize(480, 360)
        self.preview_label.setStyleSheet("background: #f8f8f8; border: 1px solid #ccc;")
        right_layout.addWidget(self.preview_label)

        # Checkboxes de tamanhos (igual à foto)
        right_layout.addSpacing(8)
        right_layout.addWidget(QLabel("Tamanhos (selecione um ou mais):"))
        self.chk16 = QCheckBox("16 pixels")
        self.chk32 = QCheckBox("32 pixels")
        self.chk48 = QCheckBox("48 pixels")
        self.chk64 = QCheckBox("64 pixels")
        self.chk128 = QCheckBox("128 pixels")
        self.chk256 = QCheckBox("256 pixels (funciona apenas com 32 bits)")
        # marcar os mais comuns por padrão como na imagem
        self.chk16.setChecked(True)
        self.chk32.setChecked(True)
        self.chk48.setChecked(True)
        self.chk64.setChecked(True)
        self.chk128.setChecked(True)
        self.chk256.setChecked(False)
        right_layout.addWidget(self.chk16)
        right_layout.addWidget(self.chk32)
        right_layout.addWidget(self.chk48)
        right_layout.addWidget(self.chk64)
        right_layout.addWidget(self.chk128)
        right_layout.addWidget(self.chk256)

        # Bit depth (fixo 32 bits)
        right_layout.addSpacing(6)
        right_layout.addWidget(QLabel("Profundidade de bits:"))
        label_bits = QLabel("32 bits (16,7 milhões de cores e transparência alfa) — FIXO")
        right_layout.addWidget(label_bits)

        # Generate button + progress
        right_layout.addSpacing(10)
        self.btn_generate = QPushButton("▶ Converter para ICO (um ICO por imagem)")
        self.btn_generate.clicked.connect(self.generate_icos)
        right_layout.addWidget(self.btn_generate)

        self.progress = QProgressBar()
        self.progress.setValue(0)
        right_layout.addWidget(self.progress)

        # Spacer
        right_layout.addStretch()

        splitter.addWidget(right_widget)
        splitter.setStretchFactor(0, 3)
        splitter.setStretchFactor(1, 2)

        # Signals
        self.list_widget.itemSelectionChanged.connect(self.update_preview)

    # -------------------------
    # UI actions
    # -------------------------
    def add_files_dialog(self):
        files, _ = QFileDialog.getOpenFileNames(
            self,
            "Selecione imagens",
            os.path.expanduser("~"),
            "Imagens (*.png *.jpg *.jpeg *.tif *.tiff *.bmp *.gif *.webp)"
        )
        if files:
            self.list_widget.add_files(files)
            escrever_log(self.log_path, f"Adicionados {len(files)} arquivos via diálogo")

    def add_folder_dialog(self):
        folder = QFileDialog.getExistingDirectory(self, "Selecione a pasta com imagens", os.path.expanduser("~"))
        if folder:
            self.list_widget.add_files([folder])
            escrever_log(self.log_path, f"Adicionada pasta: {folder}")

    def remove_selected(self):
        items = list(self.list_widget.selectedItems())
        for it in items:
            self.list_widget.takeItem(self.list_widget.row(it))
        escrever_log(self.log_path, "Itens removidos da lista")

    def clear_list(self):
        self.list_widget.clear()
        escrever_log(self.log_path, "Lista limpa")

    def move_up(self):
        row = self.list_widget.currentRow()
        if row > 0:
            item = self.list_widget.takeItem(row)
            self.list_widget.insertItem(row - 1, item)
            self.list_widget.setCurrentItem(item)

    def move_down(self):
        row = self.list_widget.currentRow()
        if row < self.list_widget.count() - 1 and row != -1:
            item = self.list_widget.takeItem(row)
            self.list_widget.insertItem(row + 1, item)
            self.list_widget.setCurrentItem(item)

    def update_preview(self):
        sel = self.list_widget.currentItem()
        if not sel:
            self.preview_label.setText("Nenhuma imagem selecionada")
            self.preview_label.setPixmap(QPixmap())
            return
        path = sel.data(Qt.UserRole)
        try:
            img = Image.open(path)
            img.thumbnail((self.preview_label.width(), self.preview_label.height()), Image.LANCZOS)
            bio = BytesIO()
            img.convert("RGBA").save(bio, format="PNG")
            qimg = QImage.fromData(bio.getvalue())
            pix = QPixmap.fromImage(qimg)
            self.preview_label.setPixmap(pix.scaled(self.preview_label.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation))
        except Exception as e:
            self.preview_label.setText("Erro ao carregar imagem")
            escrever_log(self.log_path, f"Erro preview {path}: {e}")

    # -------------------------
    # Conversão para ICO
    # -------------------------
    def generate_icos(self):
        paths = self.list_widget.get_ordered_paths()
        if not paths:
            QMessageBox.warning(self, "Aviso", "Nenhuma imagem na lista.")
            return

        # coletar tamanhos selecionados
        sizes = []
        if self.chk16.isChecked(): sizes.append(16)
        if self.chk32.isChecked(): sizes.append(32)
        if self.chk48.isChecked(): sizes.append(48)
        if self.chk64.isChecked(): sizes.append(64)
        if self.chk128.isChecked(): sizes.append(128)
        if self.chk256.isChecked(): sizes.append(256)
        if not sizes:
            QMessageBox.warning(self, "Aviso", "Selecione ao menos um tamanho.")
            return

        # escolher pasta de saída (sempre pedir conforme solicitado)
        out_dir = QFileDialog.getExistingDirectory(self, "Escolha pasta para salvar os .ICO (ou crie nova):", self.root_folder)
        if not out_dir:
            return

        escrever_log(self.log_path, f"Iniciando geração ICOs. count={len(paths)} sizes={sizes} out_dir={out_dir}")

        total = len(paths)
        self.progress.setMaximum(total)
        self.progress.setValue(0)
        QApplication.processEvents()

        try:
            for idx, p in enumerate(paths, start=1):
                try:
                    img = Image.open(p).convert("RGBA")  # manter alpha
                    # preparar lista de tuplas de tamanho para PIL
                    sizes_tuples = [(s, s) for s in sorted(sizes)]
                    # Pillow aceita salvar .ico com parâmetro sizes, mas cada size será gerada a partir da imagem original
                    base_name = os.path.splitext(os.path.basename(p))[0]
                    out_name = f"{base_name}.ico"
                    out_path = os.path.join(out_dir, out_name)

                    # Se houver tamanho 256, PIL gera adequadamente com RGBA (32 bits)
                    # Alguns formatos podem precisar ser convertidos para RGBA
                    # Para garantir qualidade, geramos versões redimensionadas temporárias
                    # Pillow permite: img.save(out_path, format='ICO', sizes=[(16,16),(32,32)])
                    img_for_save = img
                    try:
                        img_for_save.save(out_path, format='ICO', sizes=sizes_tuples)
                    except Exception:
                        # fallback: gerar imagens redimensionadas manualmente e salvar usando primeira como base
                        resized_imgs = []
                        for s in sorted(sizes):
                            im2 = img.copy()
                            im2 = im2.resize((s, s), Image.LANCZOS)
                            resized_imgs.append(im2.convert("RGBA"))
                        # PIL does not accept append_images for ICO; instead re-generate via sizes param on first;
                        # As a last resort, save the largest as ICO (not ideal), but attempt again with the largest image and sizes
                        largest = resized_imgs[-1]
                        try:
                            largest.save(out_path, format='ICO', sizes=sizes_tuples)
                        except Exception as e:
                            # última tentativa: save single NXN as ico
                            resized_imgs[0].save(out_path, format='ICO')
                            escrever_log(self.log_path, f"Fallback simples para {out_path}: {e}")

                    escrever_log(self.log_path, f"ICO salvo: {out_path}")
                except Exception as e:
                    escrever_log(self.log_path, f"Erro ao processar {p}: {e}")

                self.progress.setValue(idx)
                QApplication.processEvents()

            QMessageBox.information(self, "Concluído", "Conversão finalizada.")
            escrever_log(self.log_path, "Processo finalizado com sucesso.")
            self.progress.setValue(0)

        except Exception as e:
            escrever_log(self.log_path, f"ERRO durante geração: {e}")
            QMessageBox.critical(self, "Erro", f"Ocorreu um erro:\n{e}")
            self.progress.setValue(0)

# -----------------------------
# Execução
# -----------------------------
def main():
    # No Windows, set AppID to allow taskbar icon grouping (não crítico)
    try:
        if os.name == "nt":
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(APP_ID)
    except Exception:
        pass

    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
