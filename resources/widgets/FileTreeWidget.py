# -*- coding: utf-8 -*-
"""
FileTreeWidget — Widget QTreeView + QFileSystemModel para exploração de arquivos
=================================================================================
Componente reutilizável que exibe uma árvore de diretórios usando o modelo
nativo QFileSystemModel do Qt (ícones, datas, sem dependências externas).

Suporta:
- Navegação por árvore com root folder fixa
- Context menu com Renomear, Excluir, Criar Arquivo, Atualizar, Abrir Local
- Multi-seleção (Ctrl+clique, Shift+clique, Ctrl+A)
- Drag & Drop interno (mover arquivos entre pastas)
- Drag externo (arrastar arquivos para QGIS, Explorer, etc.)
- Conflito de nomes com diálogo Substituir/Manter ambos/Ignorar
- Sinais para todo o ciclo de vida dos arquivos
"""

from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path
from typing import List, Optional

from PySide6.QtCore import QDir, QMimeData, Qt, Signal
from PySide6.QtGui import QDrag
from PySide6.QtWidgets import (
    QAbstractItemView,
    QFileSystemModel,
    QInputDialog,
    QMenu,
    QMessageBox,
    QTreeView,
    QVBoxLayout,
    QWidget,
)

from utils.MessageBox import MessageBox


class FileTreeWidget(QWidget):
    """
    Árvore de diretórios baseada em QFileSystemModel.

    Sinais:
        file_renamed(old_path: str, new_path: str)
        file_deleted(path: str)
        file_created(path: str)
        file_moved(src: str, dst: str)
        selection_changed(path: str | None)
    """

    file_renamed = Signal(str, str)
    file_deleted = Signal(str)
    file_created = Signal(str)
    file_moved = Signal(str, str)
    selection_changed = Signal(object)  # str | None

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._root_path: str | None = None

        # ── Modelo nativo do Qt ────────────────────────────────────
        self._model = QFileSystemModel(self)
        self._model.setFilter(
            QDir.Filter.AllDirs
            | QDir.Filter.Files
            | QDir.Filter.NoDotAndDotDot
        )
        self._model.setRootPath(QDir.rootPath())

        # ── TreeView ───────────────────────────────────────────────
        self._tree = _FileTreeView(self)
        self._tree.setModel(self._model)
        self._tree.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self._tree.setDragEnabled(True)
        self._tree.setAcceptDrops(True)
        self._tree.setDropIndicatorShown(True)
        self._tree.setDragDropMode(QAbstractItemView.DragDrop)
        self._tree.setDefaultDropAction(Qt.MoveAction)
        self._tree.setAnimated(True)
        self._tree.setIndentation(20)
        self._tree.setSortingEnabled(True)
        self._tree.sortByColumn(0, Qt.AscendingOrder)
        self._tree.setHeaderHidden(False)
        self._tree.setAlternatingRowColors(True)
        self._tree.setContextMenuPolicy(Qt.CustomContextMenu)
        self._tree.setSelectionBehavior(QAbstractItemView.SelectRows)
        self._tree.customContextMenuRequested.connect(self._on_context_menu)
        self._tree.selectionModel().selectionChanged.connect(
            self._on_selection_changed
        )

        # ── Layout ─────────────────────────────────────────────────
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self._tree, 1)

    # ── API pública ────────────────────────────────────────────────

    def set_root_path(self, path: str) -> None:
        """
        Define o diretório raiz exibido na árvore.

        O usuário não consegue navegar acima deste diretório.
        """
        self._root_path = str(Path(path).resolve())
        root_index = self._model.setRootPath(self._root_path)
        self._tree.setRootIndex(root_index)

    def refresh(self) -> None:
        """Força recarga do modelo (F5 / botão Atualizar)."""
        if self._root_path:
            self._model.setRootPath(self._root_path)

    def selected_path(self) -> str | None:
        """
        Retorna o caminho completo do primeiro item selecionado,
        ou None se nada estiver selecionado.
        """
        indexes = self._tree.selectedIndexes()
        if not indexes:
            return None
        # Filtra apenas a primeira coluna para evitar duplicatas
        col_0 = [idx for idx in indexes if idx.column() == 0]
        if not col_0:
            return None
        path = self._model.filePath(col_0[0])
        return path if path else None

    def selected_paths(self) -> List[str]:
        """
        Retorna lista de caminhos completos de todos os itens selecionados.
        Único por item (filtra coluna 0).
        """
        indexes = self._tree.selectedIndexes()
        seen: set[str] = set()
        paths: list[str] = []
        for idx in indexes:
            if idx.column() != 0:
                continue
            path = self._model.filePath(idx)
            if path and path not in seen:
                seen.add(path)
                paths.append(path)
        return paths

    def selected_is_directory(self) -> bool:
        """Retorna True se o item selecionado for uma pasta."""
        path = self.selected_path()
        if not path:
            return False
        return Path(path).is_dir()

    def delete_selected(self) -> bool:
        """
        Exclui todos os itens selecionados.
        Mostra confirmação e loga cada operação.
        Retorna True se todos foram deletados com sucesso.
        """
        paths = self.selected_paths()
        if not paths:
            return False

        count = len(paths)
        label = (
            f"Excluir {count} itens?" if count > 1
            else f'Excluir "{Path(paths[0]).name}"?'
        )

        confirmed = MessageBox.show_question(
            label,
            title="Confirmar Exclusão",
            detail="Esta ação não pode ser desfeita.",
            buttons=MessageBox.YES_NO,
            default_button=MessageBox.NO,
        )
        if confirmed != MessageBox.YES:
            return False

        errors: list[str] = []
        for path in paths:
            try:
                p = Path(path)
                if p.is_dir():
                    shutil.rmtree(path)
                else:
                    os.remove(path)
                self.file_deleted.emit(path)
            except Exception as e:
                errors.append(path)

        if errors:
            MessageBox.show_warning(
                f"Não foi possível excluir {len(errors)} item(ns).",
                title="Erro ao Excluir",
            )

        return len(errors) == 0

    def rename_selected(self) -> bool:
        """
        Renomeia o item selecionado (apenas 1 item).
        Abre QInputDialog para o novo nome.
        Retorna True se bem-sucedido.
        """
        path = self.selected_path()
        if not path:
            return False

        old = Path(path)
        new_name, ok = QInputDialog.getText(
            self,
            "Renomear",
            "Novo nome:",
            text=old.name,
        )
        if not ok or not new_name or new_name == old.name:
            return False

        # Valida caracteres inválidos no Windows
        invalid = r'\/:*?"<>|'
        if any(c in new_name for c in invalid):
            MessageBox.show_warning(
                f"O nome '{new_name}' contém caracteres inválidos.",
                title="Nome Inválido",
            )
            return False

        new_path = old.parent / new_name
        try:
            os.rename(str(old), str(new_path))
            self.file_renamed.emit(str(old), str(new_path))
            return True
        except Exception as e:
            MessageBox.show_error(
                f"Erro ao renomear '{old.name}' para '{new_name}'.",
                title="Erro ao Renomear",
                detail=str(e),
            )
            return False

    def create_text_file(self, directory: str | None = None) -> bool:
        """
        Cria um arquivo de texto vazio no diretório especificado.
        Se directory for None, usa a pasta selecionada ou a raiz.
        Retorna True se criado com sucesso.
        """
        if directory is None:
            sel = self.selected_path()
            if sel and Path(sel).is_dir():
                directory = sel
            elif sel:
                directory = str(Path(sel).parent)
            else:
                directory = self._root_path

        if not directory:
            return False

        name, ok = QInputDialog.getText(
            self,
            "Criar Arquivo de Texto",
            "Nome do arquivo:",
            text="novo_arquivo.txt",
        )
        if not ok or not name:
            return False

        # Se não tem extensão, adiciona .txt
        p = Path(name)
        if not p.suffix:
            name = name + ".txt"

        invalid = r'\/:*?"<>|'
        if any(c in name for c in invalid):
            MessageBox.show_warning(
                f"O nome '{name}' contém caracteres inválidos.",
                title="Nome Inválido",
            )
            return False

        file_path = Path(directory) / name
        if file_path.exists():
            confirm = MessageBox.show_question(
                f"Já existe um arquivo '{name}' neste local.\nDeseja substituir?",
                title="Arquivo Existente",
                buttons=MessageBox.YES_NO,
                default_button=MessageBox.NO,
            )
            if confirm != MessageBox.YES:
                return False

        try:
            file_path.touch(exist_ok=True)
            self.file_created.emit(str(file_path))
            return True
        except Exception as e:
            MessageBox.show_error(
                f"Erro ao criar arquivo '{name}'.",
                title="Erro ao Criar",
                detail=str(e),
            )
            return False

    # ── Handlers internos ──────────────────────────────────────────

    def _on_context_menu(self, pos) -> None:
        """Exibe menu de contexto no QTreeView."""
        menu = QMenu(self)
        selected = self.selected_paths()
        count = len(selected)

        if count == 1:
            action_rename = menu.addAction("Renomear")
            action_rename.setShortcut("F2")

        menu.addAction(
            f"Excluir {count} itens" if count > 1 else "Excluir",
            self.delete_selected,
        ).setShortcut("Del")

        menu.addSeparator()
        menu.addAction("Criar Arquivo de Texto", self._on_create_file).setShortcut(
            "Ctrl+N"
        )
        menu.addAction("Atualizar", self.refresh).setShortcut("F5")
        menu.addSeparator()
        menu.addAction("Abrir Local no Explorer", self._open_in_explorer)

        if count == 1:
            action_rename.triggered.connect(self.rename_selected)

        menu.exec(self._tree.viewport().mapToGlobal(pos))

    def _on_create_file(self) -> None:
        """Callback para criar arquivo via menu."""
        self.create_text_file()

    def _on_selection_changed(self) -> None:
        """Repassa o path selecionado (ou None) via sinal."""
        self.selection_changed.emit(self.selected_path())

    def _open_in_explorer(self) -> None:
        """Abre o Windows Explorer no local do item selecionado."""
        path = self.selected_path()
        if not path:
            return
        try:
            p = Path(path)
            if p.is_file():
                subprocess.Popen(f'explorer /select,"{path}"')
            else:
                subprocess.Popen(f'explorer "{path}"')
        except Exception as e:
            self._logger_error(f"Erro ao abrir explorer: {e}")

    def _logger_error(self, msg: str) -> None:
        """Log de erro interno (fallback sem logger do plugin)."""
        import logging
        logging.getLogger(__name__).error(msg)

    # ── Diálogo de conflito (público para _FileTreeView usar) ─────

    def show_conflict_dialog(self, file_name: str) -> tuple[str, bool]:
        """
        Exibe diálogo de conflito de nomes.
        Retorna (escolha, apply_to_all).
        """
        reply = QMessageBox()
        reply.setWindowTitle("Substituir ou Ignorar Arquivos")
        reply.setText(f'O destino já contém um arquivo chamado "{file_name}".')
        reply.setInformativeText("O que deseja fazer?")
        reply.setIcon(QMessageBox.Question)

        btn_replace = reply.addButton("Substituir arquivo no destino", QMessageBox.ActionRole)
        btn_ignore = reply.addButton("Ignorar este arquivo", QMessageBox.RejectRole)
        btn_keep = reply.addButton("Manter ambos os arquivos", QMessageBox.ActionRole)
        reply.addButton(QMessageBox.Cancel)

        reply.exec()
        clicked = reply.clickedButton()

        if clicked == btn_replace:
            return ("substituir", False)
        elif clicked == btn_keep:
            return ("manter_ambos", False)
        else:
            return ("ignorar", False)

    @staticmethod
    def resolve_name_conflict(dst_path: Path) -> Path:
        """
        Resolve conflito adicionando sufixo numérico.
        Exemplo: "arquivo (2).txt"
        """
        parent = dst_path.parent
        stem = dst_path.stem
        suffix = dst_path.suffix
        counter = 2
        while (parent / f"{stem} ({counter}){suffix}").exists():
            counter += 1
        return parent / f"{stem} ({counter}){suffix}"


class _FileTreeView(QTreeView):
    """
    QTreeView customizado com suporte a:
    - Drag externo (urls para QGIS, Explorer, etc.)
    - Drag interno com shutil.move e conflito
    """

    def startDrag(self, supported_actions) -> None:
        """
        Sobrescrito para emitir QMimeData com urls,
        permitindo arrastar arquivos para fora do aplicativo (QGIS, Explorer).
        """
        widget = self.parent()
        if not isinstance(widget, FileTreeWidget):
            super().startDrag(supported_actions)
            return

        paths = widget.selected_paths()
        if not paths:
            return

        mime = QMimeData()
        mime.setUrls([self._to_qurl(p) for p in paths])

        drag = QDrag(self)
        drag.setMimeData(mime)
        # CopyAction para drag externo (não deleta origem)
        drag.exec(Qt.CopyAction | Qt.MoveAction)

    def dropEvent(self, event):
        """
        Sobrescrito para implementar:
        - shutil.move() em vez do comportamento padrão do modelo
        - Diálogo de conflito com Substituir/Manter ambos/Ignorar
        - Guarda contra mover pasta para dentro de si mesma
        """
        widget = self.parent()
        if not isinstance(widget, FileTreeWidget):
            super().dropEvent(event)
            return

        # Obtém paths de origem dos índices em movimento
        src_paths = widget.selected_paths()
        if not src_paths:
            event.ignore()
            return

        # Obtém diretório destino do índice sob o mouse
        drop_idx = self.indexAt(event.position().toPoint())
        if drop_idx.isValid():
            dst_dir = Path(widget._model.filePath(drop_idx))
            if not dst_dir.is_dir():
                dst_dir = dst_dir.parent
        else:
            dst_dir = Path(widget._root_path or "")

        if not dst_dir.exists():
            event.ignore()
            return

        apply_to_all = False
        last_choice = "substituir"

        for src in src_paths:
            src_p = Path(src)
            dst = dst_dir / src_p.name

            # Guarda: não mover pasta para dentro de si mesma
            if src_p in dst.parents or src_p == dst:
                continue

            if dst.exists() and not apply_to_all:
                choice, apply_to_all = widget.show_conflict_dialog(dst.name)
                if choice == "ignorar":
                    if not apply_to_all:
                        continue
                    last_choice = "ignorar"
                elif choice == "substituir":
                    last_choice = "substituir"
                elif choice == "manter_ambos":
                    dst = FileTreeWidget.resolve_name_conflict(dst)
                    last_choice = "manter_ambos"
            elif dst.exists() and apply_to_all:
                if last_choice == "ignorar":
                    continue
                elif last_choice == "manter_ambos":
                    dst = FileTreeWidget.resolve_name_conflict(dst)

            try:
                shutil.move(str(src), str(dst))
                widget.file_moved.emit(str(src), str(dst))
            except Exception as e:
                import logging
                logging.getLogger(__name__).error(
                    f"Erro ao mover {src} -> {dst}: {e}"
                )

        event.accept()

    @staticmethod
    def _to_qurl(path: str) -> "PySide6.QtCore.QUrl":
        """Converte path para QUrl.fromLocalFile."""
        from PySide6.QtCore import QUrl
        return QUrl.fromLocalFile(path)
