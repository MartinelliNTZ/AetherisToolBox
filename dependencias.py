"""
QGIS Package Manager — Gerenciador de pacotes Python para o QGIS
Requer: PySide6  →  pip install PySide6
Uso: rode com o Python interno do QGIS ou qualquer Python com PySide6 instalado.
"""

import sys
import subprocess
import importlib.metadata
from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout,
    QRadioButton, QButtonGroup, QPushButton, QTextEdit,
    QLabel, QScrollArea, QCheckBox, QFrame, QLineEdit,
    QSplitter, QProgressBar, QMessageBox, QStackedWidget,
    QSizePolicy
)
from PySide6.QtCore import Qt, QThread, Signal, QTimer
from PySide6.QtGui import QFont, QColor, QPalette, QIcon, QTextCursor

# ── Detecta o executável Python do QGIS ──────────────────────────────────────
PYTHON_EXE = sys.executable  # usa o mesmo Python que está rodando o script

# ─────────────────────────────────────────────────────────────────────────────
# Worker thread – roda pip sem travar a UI
# ─────────────────────────────────────────────────────────────────────────────
class PipWorker(QThread):
    log_line  = Signal(str)   # linha de output
    finished  = Signal(bool)  # True = sucesso

    def __init__(self, cmd: list[str]):
        super().__init__()
        self.cmd = cmd

    def run(self):
        try:
            proc = subprocess.Popen(
                self.cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                encoding="utf-8",
                errors="replace",
            )
            for line in proc.stdout:
                self.log_line.emit(line.rstrip())
            proc.wait()
            self.finished.emit(proc.returncode == 0)
        except Exception as e:
            self.log_line.emit(f"[ERRO] {e}")
            self.finished.emit(False)


# ─────────────────────────────────────────────────────────────────────────────
# Janela principal
# ─────────────────────────────────────────────────────────────────────────────
class QGISPkgManager(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("QGIS · Gerenciador de Pacotes Python")
        self.setMinimumSize(820, 620)
        self._worker = None
        self._build_ui()
        self._apply_style()

    # ── UI ───────────────────────────────────────────────────────────────────
    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setSpacing(0)
        root.setContentsMargins(0, 0, 0, 0)

        # ── Cabeçalho ─────────────────────────────────────────────────────
        header = QFrame()
        header.setObjectName("header")
        header.setFixedHeight(64)
        h_lay = QHBoxLayout(header)
        h_lay.setContentsMargins(24, 0, 24, 0)

        title = QLabel("⚙  QGIS Package Manager")
        title.setObjectName("title")
        h_lay.addWidget(title)
        h_lay.addStretch()

        py_label = QLabel(f"Python  {sys.version.split()[0]}   ·   {PYTHON_EXE}")
        py_label.setObjectName("pyinfo")
        h_lay.addWidget(py_label)
        root.addWidget(header)

        # ── Seletor de modo ───────────────────────────────────────────────
        mode_frame = QFrame()
        mode_frame.setObjectName("modeBar")
        mode_lay = QHBoxLayout(mode_frame)
        mode_lay.setContentsMargins(24, 12, 24, 12)
        mode_lay.setSpacing(32)

        self.rb_install   = QRadioButton("  Instalar")
        self.rb_uninstall = QRadioButton("  Desinstalar")
        self.rb_install.setChecked(True)
        self.rb_install.setObjectName("rb")
        self.rb_uninstall.setObjectName("rb")

        group = QButtonGroup(self)
        group.addButton(self.rb_install)
        group.addButton(self.rb_uninstall)

        self.rb_install.toggled.connect(self._on_mode_change)

        mode_lay.addWidget(QLabel("Modo:"))
        mode_lay.addWidget(self.rb_install)
        mode_lay.addWidget(self.rb_uninstall)
        mode_lay.addStretch()

        # botão atualizar lista (só visível no modo desinstalar)
        self.btn_refresh = QPushButton("↻  Atualizar lista")
        self.btn_refresh.setObjectName("btnSecondary")
        self.btn_refresh.clicked.connect(self._load_installed)
        self.btn_refresh.setVisible(False)
        mode_lay.addWidget(self.btn_refresh)

        root.addWidget(mode_frame)

        # ── Área central (stack) ──────────────────────────────────────────
        self.stack = QStackedWidget()
        self.stack.addWidget(self._build_install_panel())   # índice 0
        self.stack.addWidget(self._build_uninstall_panel()) # índice 1
        root.addWidget(self.stack, stretch=1)

        # ── Log ───────────────────────────────────────────────────────────
        log_frame = QFrame()
        log_frame.setObjectName("logFrame")
        log_lay = QVBoxLayout(log_frame)
        log_lay.setContentsMargins(12, 8, 12, 8)
        log_lay.setSpacing(4)

        log_header = QHBoxLayout()
        log_header.addWidget(QLabel("📋  Saída do pip"))
        log_header.addStretch()
        self.btn_clear_log = QPushButton("Limpar")
        self.btn_clear_log.setObjectName("btnTiny")
        self.btn_clear_log.clicked.connect(lambda: self.log.clear())
        log_header.addWidget(self.btn_clear_log)
        log_lay.addLayout(log_header)

        self.log = QTextEdit()
        self.log.setReadOnly(True)
        self.log.setObjectName("logBox")
        self.log.setFixedHeight(160)
        log_lay.addWidget(self.log)

        self.progress = QProgressBar()
        self.progress.setRange(0, 0)  # indeterminate
        self.progress.setFixedHeight(4)
        self.progress.setObjectName("pbar")
        self.progress.setVisible(False)
        log_lay.addWidget(self.progress)

        root.addWidget(log_frame)

    # ── Painel INSTALAR ───────────────────────────────────────────────────────
    def _build_install_panel(self):
        w = QWidget()
        lay = QVBoxLayout(w)
        lay.setContentsMargins(24, 20, 24, 20)
        lay.setSpacing(14)

        lbl = QLabel(
            "Digite os pacotes que deseja instalar.\n"
            "Separe por vírgula, espaço ou nova linha. "
            "Versões aceitas:  numpy>=1.24  opencv-python==4.8.0"
        )
        lbl.setObjectName("hint")
        lbl.setWordWrap(True)
        lay.addWidget(lbl)

        self.txt_pkgs = QTextEdit()
        self.txt_pkgs.setObjectName("inputBox")
        self.txt_pkgs.setPlaceholderText(
            "Ex:\nopencv-python\nnumpy>=1.24\nscipy\ngeopandas"
        )
        lay.addWidget(self.txt_pkgs, stretch=1)

        # opções extras
        opt_lay = QHBoxLayout()
        self.chk_upgrade = QCheckBox("--upgrade  (atualizar se já instalado)")
        self.chk_upgrade.setObjectName("optCheck")
        self.chk_no_deps = QCheckBox("--no-deps  (ignorar dependências)")
        self.chk_no_deps.setObjectName("optCheck")
        opt_lay.addWidget(self.chk_upgrade)
        opt_lay.addWidget(self.chk_no_deps)
        opt_lay.addStretch()
        lay.addLayout(opt_lay)

        self.btn_install = QPushButton("▶  Instalar pacotes")
        self.btn_install.setObjectName("btnPrimary")
        self.btn_install.clicked.connect(self._run_install)
        lay.addWidget(self.btn_install)

        return w

    # ── Painel DESINSTALAR ────────────────────────────────────────────────────
    def _build_uninstall_panel(self):
        w = QWidget()
        lay = QVBoxLayout(w)
        lay.setContentsMargins(24, 16, 24, 16)
        lay.setSpacing(10)

        top_lay = QHBoxLayout()
        hint = QLabel("Marque os pacotes que deseja remover:")
        hint.setObjectName("hint")
        top_lay.addWidget(hint)
        top_lay.addStretch()

        self.lbl_selected = QLabel("0 selecionados")
        self.lbl_selected.setObjectName("badge")
        top_lay.addWidget(self.lbl_selected)

        self.btn_sel_all  = QPushButton("Selecionar todos")
        self.btn_sel_all.setObjectName("btnTiny")
        self.btn_sel_all.clicked.connect(lambda: self._select_all(True))
        self.btn_sel_none = QPushButton("Limpar seleção")
        self.btn_sel_none.setObjectName("btnTiny")
        self.btn_sel_none.clicked.connect(lambda: self._select_all(False))
        top_lay.addWidget(self.btn_sel_all)
        top_lay.addWidget(self.btn_sel_none)
        lay.addLayout(top_lay)

        # busca
        self.search = QLineEdit()
        self.search.setObjectName("searchBox")
        self.search.setPlaceholderText("🔍  Filtrar pacotes…")
        self.search.textChanged.connect(self._filter_packages)
        lay.addWidget(self.search)

        # lista com scroll
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setObjectName("pkgScroll")
        self.pkg_container = QWidget()
        self.pkg_layout    = QVBoxLayout(self.pkg_container)
        self.pkg_layout.setSpacing(2)
        self.pkg_layout.setContentsMargins(8, 8, 8, 8)
        self.pkg_layout.addStretch()
        scroll.setWidget(self.pkg_container)
        lay.addWidget(scroll, stretch=1)

        self.btn_uninstall = QPushButton("🗑  Desinstalar selecionados")
        self.btn_uninstall.setObjectName("btnDanger")
        self.btn_uninstall.clicked.connect(self._run_uninstall)
        lay.addWidget(self.btn_uninstall)

        self._checkboxes: list[QCheckBox] = []
        return w

    # ── Lógica de modo ────────────────────────────────────────────────────────
    def _on_mode_change(self, checked: bool):
        if self.rb_install.isChecked():
            self.stack.setCurrentIndex(0)
            self.btn_refresh.setVisible(False)
        else:
            self.stack.setCurrentIndex(1)
            self.btn_refresh.setVisible(True)
            if not self._checkboxes:
                self._load_installed()

    # ── Carrega pacotes instalados ─────────────────────────────────────────────
    def _load_installed(self):
        # limpa lista anterior
        for cb in self._checkboxes:
            cb.setParent(None)
        self._checkboxes.clear()

        pkgs = sorted(
            importlib.metadata.distributions(),
            key=lambda d: d.metadata["Name"].lower()
        )

        stretch = self.pkg_layout.takeAt(self.pkg_layout.count() - 1)
        for dist in pkgs:
            name    = dist.metadata["Name"]
            version = dist.metadata["Version"]
            cb = QCheckBox(f"{name}  ({version})")
            cb.setObjectName("pkgCheck")
            cb.stateChanged.connect(self._update_selected_count)
            self.pkg_layout.addWidget(cb)
            self._checkboxes.append(cb)
        self.pkg_layout.addStretch()
        self._update_selected_count()
        self._log(f"[INFO] {len(self._checkboxes)} pacotes encontrados.", "#6ee7b7")

    def _filter_packages(self, text: str):
        for cb in self._checkboxes:
            cb.setVisible(text.lower() in cb.text().lower())

    def _select_all(self, state: bool):
        for cb in self._checkboxes:
            if cb.isVisible():
                cb.setChecked(state)

    def _update_selected_count(self):
        n = sum(1 for cb in self._checkboxes if cb.isChecked())
        self.lbl_selected.setText(f"{n} selecionados")

    # ── Instalar ──────────────────────────────────────────────────────────────
    def _run_install(self):
        raw = self.txt_pkgs.toPlainText()
        # separa por vírgula, espaço ou nova linha
        import re
        pkgs = [p.strip() for p in re.split(r"[\s,]+", raw) if p.strip()]
        if not pkgs:
            self._log("[AVISO] Nenhum pacote informado.", "#fbbf24")
            return

        cmd = [PYTHON_EXE, "-m", "pip", "install"] + pkgs
        if self.chk_upgrade.isChecked():
            cmd.append("--upgrade")
        if self.chk_no_deps.isChecked():
            cmd.append("--no-deps")

        self._log(f"[CMD] {' '.join(cmd)}", "#93c5fd")
        self._run_cmd(cmd)

    # ── Desinstalar ───────────────────────────────────────────────────────────
    def _run_uninstall(self):
        selected = [
            cb.text().split("  (")[0].strip()
            for cb in self._checkboxes if cb.isChecked()
        ]
        if not selected:
            self._log("[AVISO] Nenhum pacote selecionado.", "#fbbf24")
            return

        confirm = QMessageBox.question(
            self, "Confirmar remoção",
            f"Desinstalar {len(selected)} pacote(s)?\n\n" + "\n".join(selected),
            QMessageBox.Yes | QMessageBox.No
        )
        if confirm != QMessageBox.Yes:
            return

        cmd = [PYTHON_EXE, "-m", "pip", "uninstall", "-y"] + selected
        self._log(f"[CMD] {' '.join(cmd)}", "#93c5fd")
        self._run_cmd(cmd, post_action=self._load_installed)

    # ── Executa pip em thread ─────────────────────────────────────────────────
    def _run_cmd(self, cmd: list[str], post_action=None):
        self._set_busy(True)
        self._worker = PipWorker(cmd)
        self._worker.log_line.connect(lambda l: self._log(l))
        self._worker.finished.connect(lambda ok: self._on_done(ok, post_action))
        self._worker.start()

    def _on_done(self, ok: bool, post_action=None):
        self._set_busy(False)
        color = "#6ee7b7" if ok else "#f87171"
        self._log("✔  Concluído com sucesso." if ok else "✖  Falhou.", color)
        if ok and post_action:
            post_action()

    def _set_busy(self, busy: bool):
        self.progress.setVisible(busy)
        self.btn_install.setEnabled(not busy)
        self.btn_uninstall.setEnabled(not busy)
        self.rb_install.setEnabled(not busy)
        self.rb_uninstall.setEnabled(not busy)

    def _log(self, text: str, color: str = "#e2e8f0"):
        self.log.setTextColor(QColor(color))
        self.log.append(text)
        self.log.moveCursor(QTextCursor.End)

    # ── Estilo ────────────────────────────────────────────────────────────────
    def _apply_style(self):
        self.setStyleSheet("""
            /* ── Geral ── */
            QWidget {
                background: #0f172a;
                color: #e2e8f0;
                font-family: 'Consolas', 'JetBrains Mono', monospace;
                font-size: 13px;
            }

            /* ── Cabeçalho ── */
            QFrame#header {
                background: #1e293b;
                border-bottom: 2px solid #334155;
            }
            QLabel#title {
                font-size: 17px;
                font-weight: bold;
                color: #38bdf8;
                letter-spacing: 1px;
            }
            QLabel#pyinfo {
                font-size: 11px;
                color: #64748b;
            }

            /* ── Barra de modo ── */
            QFrame#modeBar {
                background: #1e293b;
                border-bottom: 1px solid #334155;
            }
            QRadioButton#rb {
                font-size: 14px;
                spacing: 8px;
                color: #cbd5e1;
            }
            QRadioButton#rb::indicator {
                width: 18px; height: 18px;
                border-radius: 9px;
                border: 2px solid #475569;
                background: #0f172a;
            }
            QRadioButton#rb::indicator:checked {
                border-color: #38bdf8;
                background: #38bdf8;
            }
            QRadioButton#rb:checked {
                color: #38bdf8;
                font-weight: bold;
            }

            /* ── Inputs ── */
            QTextEdit#inputBox, QLineEdit#searchBox {
                background: #1e293b;
                border: 1px solid #334155;
                border-radius: 6px;
                padding: 10px;
                color: #e2e8f0;
                font-size: 13px;
            }
            QTextEdit#inputBox:focus, QLineEdit#searchBox:focus {
                border-color: #38bdf8;
            }

            /* ── Log ── */
            QFrame#logFrame {
                background: #0b1120;
                border-top: 2px solid #334155;
            }
            QTextEdit#logBox {
                background: #020817;
                border: 1px solid #1e293b;
                border-radius: 4px;
                color: #94a3b8;
                font-size: 12px;
                padding: 6px;
            }

            /* ── Progress bar ── */
            QProgressBar#pbar {
                border: none;
                background: #1e293b;
                border-radius: 2px;
            }
            QProgressBar#pbar::chunk {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #38bdf8, stop:1 #818cf8);
                border-radius: 2px;
            }

            /* ── Botões ── */
            QPushButton#btnPrimary {
                background: #0ea5e9;
                color: #fff;
                font-size: 14px;
                font-weight: bold;
                border: none;
                border-radius: 8px;
                padding: 12px 24px;
            }
            QPushButton#btnPrimary:hover  { background: #38bdf8; }
            QPushButton#btnPrimary:pressed{ background: #0284c7; }
            QPushButton#btnPrimary:disabled { background: #334155; color: #64748b; }

            QPushButton#btnDanger {
                background: #dc2626;
                color: #fff;
                font-size: 14px;
                font-weight: bold;
                border: none;
                border-radius: 8px;
                padding: 12px 24px;
            }
            QPushButton#btnDanger:hover  { background: #ef4444; }
            QPushButton#btnDanger:pressed{ background: #b91c1c; }
            QPushButton#btnDanger:disabled{ background: #334155; color: #64748b; }

            QPushButton#btnSecondary {
                background: #334155;
                color: #e2e8f0;
                border: none;
                border-radius: 6px;
                padding: 7px 16px;
            }
            QPushButton#btnSecondary:hover { background: #475569; }

            QPushButton#btnTiny {
                background: #1e293b;
                color: #94a3b8;
                border: 1px solid #334155;
                border-radius: 4px;
                padding: 4px 10px;
                font-size: 11px;
            }
            QPushButton#btnTiny:hover { background: #334155; color: #e2e8f0; }

            /* ── Checkboxes de pacotes ── */
            QCheckBox#pkgCheck {
                spacing: 10px;
                color: #cbd5e1;
                padding: 5px 8px;
                border-radius: 4px;
            }
            QCheckBox#pkgCheck:hover { background: #1e293b; }
            QCheckBox#pkgCheck::indicator {
                width: 16px; height: 16px;
                border-radius: 3px;
                border: 1px solid #475569;
                background: #0f172a;
            }
            QCheckBox#pkgCheck::indicator:checked {
                background: #0ea5e9;
                border-color: #0ea5e9;
                image: none;
            }

            QCheckBox#optCheck {
                spacing: 8px;
                color: #94a3b8;
            }
            QCheckBox#optCheck::indicator {
                width: 15px; height: 15px;
                border-radius: 3px;
                border: 1px solid #475569;
                background: #1e293b;
            }
            QCheckBox#optCheck::indicator:checked {
                background: #818cf8;
                border-color: #818cf8;
            }

            /* ── Badge contador ── */
            QLabel#badge {
                background: #1e40af;
                color: #bfdbfe;
                border-radius: 10px;
                padding: 2px 10px;
                font-size: 11px;
                font-weight: bold;
            }

            QLabel#hint {
                color: #64748b;
                font-size: 12px;
            }

            /* ── Scroll ── */
            QScrollArea#pkgScroll {
                border: 1px solid #1e293b;
                border-radius: 6px;
                background: #080f1e;
            }
            QScrollBar:vertical {
                background: #1e293b;
                width: 8px;
                border-radius: 4px;
            }
            QScrollBar::handle:vertical {
                background: #475569;
                border-radius: 4px;
                min-height: 20px;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0;
            }
        """)


# ─────────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    win = QGISPkgManager()
    win.show()
    sys.exit(app.exec())