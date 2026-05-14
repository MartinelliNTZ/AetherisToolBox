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
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QSpinBox, QCheckBox, QComboBox, QFrame, QGroupBox,
)
from PySide6.QtCore import Qt

from core.enum.ToolKey import ToolKey
from resources.widgets.SimplePrimaryButton import SimplePrimaryButton
from resources.widgets.SimpleSecondaryButton import SimpleSecondaryButton
from resources.widgets.SimpleDangerButton import SimpleDangerButton
from resources.widgets.SimpleSelector import SimpleSelector
from resources.widgets.GroupDiv import GroupDiv
from resources.widgets.GridCheckBox import GridCheckBox
from utils.DictManager import DictManager
from utils.Preferences import Preferences
from utils.MessageBox import MessageBox


class RenamerPlugin(QWidget):
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
        super().__init__(parent)
        self._prefs = Preferences(section=ToolKey.RENAMER.value)
        self._ext_config = DictManager.file_extensions()
        self._build_ui()
        self._load_prefs()

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
        actions = QHBoxLayout()
        actions.setSpacing(6)
        self.btn_executar = SimplePrimaryButton("EXECUTAR RENOMEIO")
        self.btn_executar.clicked.connect(self._on_executar)
        actions.addWidget(self.btn_executar)
        self.btn_preview = SimpleSecondaryButton("PRÉ-VISUALIZAR")
        self.btn_preview.clicked.connect(self._on_preview)
        actions.addWidget(self.btn_preview)
        self.btn_reset = SimpleSecondaryButton("RESTAURAR PADRÃO")
        self.btn_reset.clicked.connect(self._reset_prefs)
        actions.addWidget(self.btn_reset)
        actions.addStretch()
        main_layout.addLayout(actions)

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

        main_layout.addWidget(grp_pastas)

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

        main_layout.addWidget(grp_modo)

        # ── Filtro de Extensões ──
        grp_ext = GroupDiv("Filtro de Extensões (deschecadas = ignoradas)")
        ext_layout = grp_ext.group_layout
        ext_layout.setSpacing(4)

        self._grid_ext = GridCheckBox(self._ext_config, num_columns=5)
        ext_layout.addWidget(self._grid_ext)

        main_layout.addWidget(grp_ext, 1)

        # Atualiza visibilidade inicial
        self._on_mode_changed(self._combo_modo.currentText())

    def _on_mode_changed(self, mode: str):
        """Mostra/esconde parâmetros conforme o modo selecionado."""
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

    def _load_prefs(self):
        """Carrega estado salvo."""
        self._sel_origem.set_path(self._prefs.get("origem", ""))
        self._sel_destino.set_path(self._prefs.get("destino", ""))

        mode = self._prefs.get("modo", self.MODES[0])
        idx = self._combo_modo.findText(mode)
        if idx >= 0:
            self._combo_modo.setCurrentIndex(idx)

        self._edit_texto.setText(self._prefs.get("texto", ""))
        self._edit_subst.setText(self._prefs.get("subst", ""))
        self._spin_qtd.setValue(self._prefs.get("qtd", 1))
        self._chk_case_sensitive.setChecked(self._prefs.get("case_sensitive", False))
        self._chk_trecho_exato.setChecked(self._prefs.get("trecho_exato", True))

        ext_states = self._prefs.get("extensoes", {})
        if ext_states:
            self._grid_ext.set_all(ext_states)

    def _save_prefs(self):
        """Salva estado atual."""
        self._prefs.set("origem", self._sel_origem.path())
        self._prefs.set("destino", self._sel_destino.path())
        self._prefs.set("modo", self._combo_modo.currentText())
        self._prefs.set("texto", self._edit_texto.text())
        self._prefs.set("subst", self._edit_subst.text())
        self._prefs.set("qtd", self._spin_qtd.value())
        self._prefs.set("case_sensitive", self._chk_case_sensitive.isChecked())
        self._prefs.set("trecho_exato", self._chk_trecho_exato.isChecked())
        self._prefs.set("extensoes", self._grid_ext.all)
        self._prefs.save()

    def _reset_prefs(self):
        """Restaura valores padrão."""
        self._prefs = Preferences(section=ToolKey.RENAMER.value)
        # Limpa todas as keys da seção
        data = self._prefs.to_dict()
        for k in list(data.keys()):
            self._prefs.set(k, None)
        self._prefs.save()
        self._load_prefs()
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
                MessageBox.show_warning("Selecione uma pasta de origem primeiro.", title="Aviso")
            else:
                MessageBox.show_info("Nenhum arquivo será modificado com as configurações atuais.", title="Preview")
            return

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
            MessageBox.show_warning("Nada a renomear. Verifique a pasta e o filtro.", title="Aviso")
            return

        ok = MessageBox.show_question(
            text=f"Confirmar renomeio de {len(preview)} arquivo(s)?",
            title="Confirmar",
        )
        if not ok:
            return

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

        self._save_prefs()

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