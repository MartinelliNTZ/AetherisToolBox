# -*- coding: utf-8 -*-
"""
RenamerPlugin — Renomeador em lote de arquivos
===============================================
Ferramenta do tipo FOLDER que permite renomear arquivos em lote
com 4 modos e filtro de extensões.

Modos:
  1. Adicionar Sufixo    → anexa texto ao final (antes da extensão)
  2. Adicionar Prefixo   → anexa texto ao início
  3. Remover X do Final  → remove N caracteres do final (ignorando extensão)
  4. Remover X do Começo → remove N caracteres do início
  5. Substituir Texto    → busca e substitui com opções de case/trecho
  6. Limpar Extensão     → remove todas as extensões

Filtro de extensões: GridCheckBox com as extensões do DictManager.
"""

from __future__ import annotations

import os
import shutil
from pathlib import Path
from typing import Any, Dict, List, Optional

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QGridLayout, QLabel, QLineEdit,
    QSpinBox, QCheckBox, QComboBox, QFrame, QGroupBox,
)
from PySide6.QtCore import Qt

from core.enum.ToolKey import ToolKey
from core.model.BasePlugin import BasePlugin
from resources.widgets.ExecutionButtons import ExecutionButtons
from resources.widgets.SimpleSelector import SimpleSelector
from resources.widgets.GroupDiv import GroupDiv
from resources.widgets.GridCheckBox import GridCheckBox
from utils.DictManager import DictManager
from utils.MessageBox import MessageBox


class RenamerPlugin(BasePlugin):
    """
    Renomeador em lote de arquivos com múltiplos modos e filtro de extensões.
    """

    # Lista de modos
    MODES = [
        "Adicionar Prefixo",
        "Adicionar Sufixo",
        "Remover X do Começo",
        "Remover X do Final (ignora extensão)",
        "Substituir Texto",
        "Limpar Extensão",
    ]

    def __init__(self, parent=None):
        super().__init__(tool_key=ToolKey.RENAMER.value, parent=parent)
        self._ext_config = DictManager.file_extensions()
        self._build_ui()
        self.load_prefs()
        self.logger.info("RenamerPlugin inicializado", code="RENAMER_READY")

    def _build_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(18, 10, 18, 10)
        main_layout.setSpacing(8)

        # ── Header ──
        header = QLabel("Renomeador em Lote")
        header.setObjectName("header_title")
        main_layout.addWidget(header)

        sep = QFrame()
        sep.setObjectName("separator")
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setFixedHeight(1)
        main_layout.addWidget(sep)

        # ── Ações ──
        self._btns = ExecutionButtons(self)
        self._btns.setup({
            "preview": {
                "text": "PRÉ-VISUALIZAR",
                "callback": self._on_preview,
                "type": "secondary",
                "description": "Exibe prévia das alterações antes de renomear",
            },
            "reset": {
                "text": "RESTAURAR PADRÃO",
                "callback": self._reset_prefs,
                "type": "secondary",
                "description": "Restaura configurações para o valor padrão",
            },
            "executar": {
                "text": "EXECUTAR RENOMEIO",
                "callback": self._on_executar,
                "type": "primary",
                "description": "Executa o renomeio em lote dos arquivos",
            },
        })
        main_layout.addWidget(self._btns)

        # ── Seletores de Pasta ──
        grp_pastas = GroupDiv("Pastas")
        pl = grp_pastas.group_layout
        pl.setSpacing(6)

        # Pasta de origem (uma pasta)
        self._sel_origem = SimpleSelector(
            "Pasta Origem:", "",
            placeholder="Caminho da pasta com os arquivos...",
            browse_mode="directory", label_width=120,
        )
        pl.addWidget(self._sel_origem)

        # Pasta de destino (uma pasta, opcional — se vazia = sobrescreve)
        self._sel_destino = SimpleSelector(
            "Pasta Destino:", "",
            placeholder="Deixe vazio para renomear no local",
            browse_mode="directory", label_width=120,
        )
        pl.addWidget(self._sel_destino)

        # Checkbox vasculhar subpastas
        self._chk_subpastas = QCheckBox("Vasculhar subpastas")
        self._chk_subpastas.setObjectName("pref_check")
        pl.addWidget(self._chk_subpastas)

        # ── Grid: Pastas (0,0) | Modo (0,1) | Filtro (1,0-1) ──
        grid = QGridLayout()
        grid.setSpacing(10)

        grid.addWidget(grp_pastas, 0, 0)

        # ── Modo de Renomeio ──
        grp_modo = GroupDiv("Modo de Renomeio")
        ml = grp_modo.group_layout
        ml.setSpacing(6)

        # Combo de modo
        ml.addWidget(QLabel("Modo:"))
        self._combo_modo = QComboBox()
        self._combo_modo.addItems(self.MODES)
        self._combo_modo.currentTextChanged.connect(self._on_mode_changed)
        ml.addWidget(self._combo_modo)

        # ── Parâmetros comuns ──
        # Texto (prefixo/sufixo/busca)
        self._lbl_texto = QLabel("Texto:")
        self._edit_texto = QLineEdit()
        self._edit_texto.setPlaceholderText("Texto para adicionar ou buscar...")
        ml.addWidget(self._lbl_texto)
        ml.addWidget(self._edit_texto)

        # Substituir por
        self._lbl_subst = QLabel("Substituir por:")
        self._edit_subst = QLineEdit()
        self._edit_subst.setPlaceholderText("Texto de substituição...")
        ml.addWidget(self._lbl_subst)
        ml.addWidget(self._edit_subst)

        # Número de caracteres (remover)
        self._lbl_qtd = QLabel("Quantidade:")
        self._spin_qtd = QSpinBox()
        self._spin_qtd.setRange(1, 9999)
        self._spin_qtd.setValue(1)
        ml.addWidget(self._lbl_qtd)
        ml.addWidget(self._spin_qtd)

        # ── Checkboxes de opções ──
        self._chk_case_sensitive = QCheckBox("Case Sensitive")
        self._chk_case_sensitive.setObjectName("pref_check")
        ml.addWidget(self._chk_case_sensitive)

        self._chk_trecho_exato = QCheckBox("Substituir trecho exato (senão substitui nome todo)")
        self._chk_trecho_exato.setObjectName("pref_check")
        self._chk_trecho_exato.setChecked(True)
        ml.addWidget(self._chk_trecho_exato)

        grid.addWidget(grp_modo, 0, 1)

        # ── Filtro de Extensões (ocupa as 2 colunas) ──
        grp_ext = GroupDiv("Filtro de Extensões (deschecadas = ignoradas)")
        ext_layout = grp_ext.group_layout
        ext_layout.setSpacing(4)

        self._grid_ext = GridCheckBox(self._ext_config, num_columns=7)
        ext_layout.addWidget(self._grid_ext)

        grid.addWidget(grp_ext, 1, 0, 1, 2)

        # Stretch igual nas 2 colunas para expandirem juntas
        grid.setColumnStretch(0, 1)
        grid.setColumnStretch(1, 1)
        # Filtro ganha mais espaço vertical
        grid.setRowStretch(0, 1)
        grid.setRowStretch(1, 2)

        main_layout.addLayout(grid)

        # Atualiza visibilidade inicial
        self._on_mode_changed(self._combo_modo.currentText())

    def _on_mode_changed(self, mode: str):
        """Mostra/esconde parâmetros conforme o modo selecionado."""
        self.logger.info(f"Modo alterado: {mode}", code="RENAMER_MODE")
        is_prefix_suffix = mode in ("Adicionar Prefixo", "Adicionar Sufixo")
        is_remove = mode in ("Remover X do Começo", "Remover X do Final (ignora extensão)")
        is_replace = mode == "Substituir Texto"
        is_clear = mode == "Limpar Extensão"

        self._lbl_texto.setVisible(is_prefix_suffix or is_replace)
        self._edit_texto.setVisible(is_prefix_suffix or is_replace)
        self._lbl_subst.setVisible(is_replace)
        self._edit_subst.setVisible(is_replace)
        self._lbl_qtd.setVisible(is_remove)
        self._spin_qtd.setVisible(is_remove)
        self._chk_case_sensitive.setVisible(is_replace)
        self._chk_trecho_exato.setVisible(is_replace)

    # ── Preferências ──────────────────────────────────────────────────

    def load_prefs(self):
        """Carrega estado salvo."""
        self._sel_origem.set_path(self.preferences.get("origem", ""))
        self._sel_destino.set_path(self.preferences.get("destino", ""))

        mode = self.preferences.get("modo", self.MODES[0])
        idx = self._combo_modo.findText(mode)
        if idx >= 0:
            self._combo_modo.setCurrentIndex(idx)

        self._edit_texto.setText(self.preferences.get("texto", ""))
        self._edit_subst.setText(self.preferences.get("subst", ""))
        self._spin_qtd.setValue(self.preferences.get("qtd", 1))
        self._chk_case_sensitive.setChecked(self.preferences.get("case_sensitive", False))
        self._chk_trecho_exato.setChecked(self.preferences.get("trecho_exato", True))

        self._chk_subpastas.setChecked(self.preferences.get("subpastas", False))

        ext_states = self.preferences.get("extensoes", {})
        if ext_states:
            self._grid_ext.set_all(ext_states)

    def save_prefs(self):
        """Salva estado atual."""
        self.preferences["origem"] = self._sel_origem.path()
        self.preferences["destino"] = self._sel_destino.path()
        self.preferences["modo"] = self._combo_modo.currentText()
        self.preferences["texto"] = self._edit_texto.text()
        self.preferences["subst"] = self._edit_subst.text()
        self.preferences["qtd"] = self._spin_qtd.value()
        self.preferences["case_sensitive"] = self._chk_case_sensitive.isChecked()
        self.preferences["trecho_exato"] = self._chk_trecho_exato.isChecked()
        self.preferences["subpastas"] = self._chk_subpastas.isChecked()
        self.preferences["extensoes"] = self._grid_ext.all

    def _reset_prefs(self):
        """Restaura valores padrão."""
        self.preferences.clear()
        from core.enum.ToolKey import ToolKey
        from utils.Preferences import Preferences
        Preferences.save_tool_prefs(ToolKey.RENAMER, self.preferences)
        self.load_prefs()
        self.logger.info("Preferências restauradas para o padrão", code="RENAMER_RESET")
        MessageBox.show_info("Preferências restauradas para o padrão.", title="Restaurado")

    # ── Preview ──────────────────────────────────────────────────────

    def _get_files(self) -> List[Path]:
        """Retorna lista de arquivos na pasta de origem que passam no filtro."""
        origem = Path(self._sel_origem.path())
        if not origem.is_dir():
            return []

        ext_filter = self._grid_ext.checked  # só extensões checadas
        if not ext_filter:
            return []

        files = []
        for f in origem.iterdir():
            if f.is_file():
                ext = f.suffix.lower()
                if ext in ext_filter:
                    files.append(f)
        return sorted(files)

    def _generate_preview(self) -> List[tuple]:
        """
        Gera lista de (nome_original, nome_novo) para preview.
        Retorna lista vazia se algo inválido.
        """
        files = self._get_files()
        if not files:
            return []

        destino_base = Path(self._sel_destino.path()) if self._sel_destino.path() else None
        if destino_base and not destino_base.is_dir():
            return []

        mode = self._combo_modo.currentText()
        texto = self._edit_texto.text()
        subst = self._edit_subst.text()
        qtd = self._spin_qtd.value()
        case_sensitive = self._chk_case_sensitive.isChecked()
        trecho_exato = self._chk_trecho_exato.isChecked()

        results = []
        for f in files:
            stem = f.stem  # nome sem extensão
            ext = f.suffix

            if mode == "Adicionar Prefixo":
                new_stem = texto + stem
            elif mode == "Adicionar Sufixo":
                new_stem = stem + texto
            elif mode == "Remover X do Começo":
                new_stem = stem[qtd:]
            elif mode == "Remover X do Final (ignora extensão)":
                new_stem = stem[:-qtd] if qtd < len(stem) else ""
            elif mode == "Substituir Texto":
                if trecho_exato:
                    # Substitui apenas o trecho exato
                    if case_sensitive:
                        new_stem = stem.replace(texto, subst)
                    else:
                        new_stem = _case_insensitive_replace(stem, texto, subst)
                else:
                    # Substitui o nome todo (se encontrar o texto)
                    if case_sensitive:
                        if texto in stem:
                            new_stem = subst
                        else:
                            new_stem = stem
                    else:
                        if texto.lower() in stem.lower():
                            new_stem = subst
                        else:
                            new_stem = stem
            elif mode == "Limpar Extensão":
                new_stem = stem
                ext = ""
            else:
                new_stem = stem

            new_name = new_stem + ext if ext else new_stem
            if destino_base:
                new_path = destino_base / new_name
            else:
                new_path = f.parent / new_name

            if str(f.name) != new_name:
                results.append((str(f.name), new_name))

        return results

    def _on_preview(self):
        """Exibe pré-visualização em MessageBox."""
        preview = self._generate_preview()
        if not preview:
            origem = self._sel_origem.path()
            if not origem:
                self.logger.warning("Preview solicitado sem pasta de origem", code="RENAMER_NO_ORIGEM")
                MessageBox.show_warning("Selecione uma pasta de origem primeiro.", title="Aviso")
            else:
                self.logger.info("Preview vazio — nenhum arquivo será modificado", code="RENAMER_PREVIEW_EMPTY")
                MessageBox.show_info("Nenhum arquivo será modificado com as configurações atuais.", title="Preview")
            return

        self.logger.info(f"Preview gerado — {len(preview)} arquivo(s)", code="RENAMER_PREVIEW")

        lines = [f"{orig} → {novo}" for orig, novo in preview[:50]]
        if len(preview) > 50:
            lines.append(f"... e mais {len(preview) - 50} arquivo(s)")
        text = "\n".join(lines)

        from PySide6.QtWidgets import QTextEdit, QDialog, QVBoxLayout, QPushButton
        dlg = QDialog(self)
        dlg.setWindowTitle(f"Pré-Visualização — {len(preview)} arquivo(s)")
        dlg.resize(600, 400)
        layout = QVBoxLayout(dlg)
        te = QTextEdit(text)
        te.setReadOnly(True)
        layout.addWidget(te)
        btn = QPushButton("Fechar")
        btn.clicked.connect(dlg.accept)
        layout.addWidget(btn)
        dlg.exec()

    # ── Execução ─────────────────────────────────────────────────────

    def _on_executar(self):
        """Executa o renomeio."""
        preview = self._generate_preview()
        if not preview:
            self.logger.warning("Execução abortada — preview vazio", code="RENAMER_EXEC_EMPTY")
            MessageBox.show_warning("Nada a renomear. Verifique a pasta e o filtro.", title="Aviso")
            return

        ok = MessageBox.show_question(
            text=f"Confirmar renomeio de {len(preview)} arquivo(s)?",
            title="Confirmar",
        )
        if not ok:
            self.logger.info("Execução cancelada pelo usuário", code="RENAMER_CANCEL")
            return

        self.logger.info(f"Iniciando renomeio de {len(preview)} arquivo(s)", code="RENAMER_START")
        origem_base = Path(self._sel_origem.path())
        destino_base = Path(self._sel_destino.path()) if self._sel_destino.path() else None

        errors = 0
        renamed = 0
        for orig_name, new_name in preview:
            src = origem_base / orig_name
            if destino_base:
                dst = destino_base / new_name
            else:
                dst = src.parent / new_name

            try:
                if dst.exists():
                    # Se destino já existe, adiciona número
                    base = dst.stem
                    ext = dst.suffix
                    count = 1
                    while dst.exists():
                        dst = dst.parent / f"{base}_{count}{ext}"
                        count += 1
                src.rename(dst)
                renamed += 1
            except Exception as e:
                errors += 1
                self.logger.error(f"Erro ao renomear {orig_name}: {e}", code="RENAMER_RENAME_ERR", error=str(e))

        self.save_prefs()

        self.logger.info(f"Renomeio concluído — {renamed} renomeado(s), {errors} erro(s)", code="RENAMER_DONE")

        msg = f"{renamed} arquivo(s) renomeado(s) com sucesso."
        if errors:
            msg += f" {errors} erro(s)."
        MessageBox.show_info(msg, title="Concluído")


def _case_insensitive_replace(text: str, old: str, new: str) -> str:
    """Substitui old por new ignorando case, preservando o case do original."""
    if not old:
        return text
    result = []
    i = 0
    lower_text = text.lower()
    lower_old = old.lower()
    while i < len(text):
        pos = lower_text.find(lower_old, i)
        if pos == -1:
            result.append(text[i:])
            break
        result.append(text[i:pos])
        result.append(new)
        i = pos + len(old)
    return "".join(result)