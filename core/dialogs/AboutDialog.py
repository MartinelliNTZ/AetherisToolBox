# -*- coding: utf-8 -*-
"""AboutDialog — Dialog simples com informações do sistema, estilizado com Palette."""

from __future__ import annotations

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton
)
from PySide6.QtCore import Qt

from resources.styles.styles import Palette, AppStyles


class AboutDialog(QDialog):
    """Dialog simples exibindo informações do Aetheris ToolBox."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Sobre o Aetheris ToolBox")
        self.setFixedSize(380, 240)
        self.setModal(True)
        self.setObjectName("about_dialog")
        self._apply_style()
        self._build_ui()

    def _apply_style(self):
        p = Palette
        self.setStyleSheet(f"""
            QDialog#about_dialog {{
                background-color: {p.BG_DARK};
                border: 1px solid {p.BORDER};
                border-radius: 10px;
            }}
            QLabel#about_title {{
                color: {p.TEXT_GOLD};
                font-size: 16px;
                font-weight: 700;
                letter-spacing: 0.5px;
            }}
            QLabel#about_version {{
                color: {p.TEXT_SECONDARY};
                font-size: 12px;
            }}
            QLabel#about_desc {{
                color: {p.TEXT_PRIMARY};
                font-size: 12px;
                line-height: 1.4;
            }}
            QLabel#about_copyright {{
                color: {p.TEXT_MUTED};
                font-size: 11px;
            }}
        """)

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 20)
        layout.setSpacing(8)

        # Título
        title = QLabel("Aetheris ToolBox")
        title.setObjectName("about_title")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        # Versão
        version = QLabel("Versão 1.0.0")
        version.setObjectName("about_version")
        version.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(version)

        layout.addSpacing(8)

        # Descrição
        desc = QLabel(
            "Ferramentas para automação de processos\n"
            "de classificação raster e análise de dados."
        )
        desc.setObjectName("about_desc")
        desc.setAlignment(Qt.AlignmentFlag.AlignCenter)
        desc.setWordWrap(True)
        layout.addWidget(desc)

        layout.addSpacing(4)

        # Copyright
        copyright_label = QLabel("© 2026 Aetheris ToolBox")
        copyright_label.setObjectName("about_copyright")
        copyright_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(copyright_label)

        layout.addStretch()

        # Botão OK (estilo ghost)
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        btn_ok = QPushButton("OK")
        btn_ok.setFixedWidth(80)
        btn_ok.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_ok.setStyleSheet(AppStyles.btn_secondary_style())
        btn_ok.clicked.connect(self.accept)
        btn_layout.addWidget(btn_ok)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)
