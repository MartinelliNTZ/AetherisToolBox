# -*- coding: utf-8 -*-
"""
FileListView — Widget de lista com thumbnails, reordenação e drag & drop
==========================================================================
Encapsula uma QListWidget com:
- Miniaturas dos arquivos (120x80)
- Drag & drop interno (InternalMove) para reordenação
- Drag & drop externo de arquivos/pastas do sistema
- Botões internos: Add Files, Add Folder, Remove Selected, Clear, Move Up, Move Down
- Filtro por extensões via dict (DictManager-style)
- Conexão automática com PreviewPanel via parâmetro preview_widget
- Sinais: files_changed(count), selection_changed(path | None)

Uso:
    view = FileListView(
        file_filter=DictManager.IMAGE_EXTENSIONS,
        accept_dirs=True,
        preview_widget=preview_panel,  # conexão automática
    )
    view.add_files(["c:/foto.png", "c:/pasta/"])
    paths = view.get_ordered_paths()
"""

from __future__ import annotations

import os
from io import BytesIO
from typing import Any, Dict, List, Optional

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QPixmap, QImage
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QListWidget, QListWidgetItem,
    QPushButton, QLabel,
)

from utils.ExplorerUtils import ExplorerUtils


class FileListView(QWidget):
    """
    Lista de arquivos com thumbnails, drag & drop, botões internos.

    Parâmetros:
        file_filter: Dict[str, Dict] — extensões aceitas no formato DictManager.
                     Ex: IMAGE_EXTENSIONS, GEOPROCESSOR_EXTENSIONS.
        accept_dirs: bool — se True, pastas soltas são vasculhadas.
        preview_widget: PreviewPanel | None — se informado, conecta-se
                        automaticamente (atualiza preview ao selecionar item).
        icon_size: tuple — tamanho das miniaturas (largura, altura).
    """

    files_changed = Signal(int)       # emitido quando lista muda (count)
    selection_changed = Signal(str)   # emitido quando seleção muda (path ou "")

    def __init__(
        self,
        file_filter: Optional[Dict[str, Dict[str, Any]]] = None,
        accept_dirs: bool = True,
        preview_widget=None,
        icon_size: tuple[int, int] = (120, 80),
        parent=None,
    ):
        super().__init__(parent)
        self._file_filter = file_filter or {}
        self._accept_dirs = accept_dirs
        self._preview_widget = preview_widget
        self._icon_size = icon_size
        self._ext_set: set[str] = set()

        # Constrói set de extensões a partir do filter dict
        if self._file_filter:
            self._ext_set = {ext.lower() for ext in self._file_filter}

        self._build_ui()
        self._connect_signals()

    # ── UI ──────────────────────────────────────────────────────────

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        # Lista
        from PySide6.QtCore import QSize
        self._list = _FileListWidget(self._ext_set, self._accept_dirs, self._icon_size)
        self._list.setIconSize(QSize(self._icon_size[0], self._icon_size[1]))
        layout.addWidget(self._list, 1)

        # Botões
        self._build_buttons(layout)

    def _build_buttons(self, layout):
        # Linha 1: Add Files, Add Folder, Remove Selected, Clear
        row1 = QHBoxLayout()
        row1.setSpacing(4)

        self._btn_add_files = QPushButton("+ Adicionar Arquivos")
        self._btn_add_files.setObjectName("btn_ghost")
        self._btn_add_files.setCursor(Qt.CursorShape.PointingHandCursor)
        row1.addWidget(self._btn_add_files)

        self._btn_add_folder = QPushButton("+ Adicionar Pastas")
        self._btn_add_folder.setObjectName("btn_ghost")
        self._btn_add_folder.setCursor(Qt.CursorShape.PointingHandCursor)
        row1.addWidget(self._btn_add_folder)

        self._btn_remove = QPushButton("- Remover Sel.")
        self._btn_remove.setObjectName("btn_ghost")
        self._btn_remove.setCursor(Qt.CursorShape.PointingHandCursor)
        row1.addWidget(self._btn_remove)

        self._btn_clear = QPushButton("✖ Limpar Lista")
        self._btn_clear.setObjectName("btn_ghost")
        self._btn_clear.setCursor(Qt.CursorShape.PointingHandCursor)
        row1.addWidget(self._btn_clear)

        layout.addLayout(row1)

        # Linha 2: Mover Cima / Baixo
        row2 = QHBoxLayout()
        row2.setSpacing(4)

        self._btn_up = QPushButton("⬆ Mover acima")
        self._btn_up.setObjectName("btn_ghost")
        self._btn_up.setCursor(Qt.CursorShape.PointingHandCursor)
        row2.addWidget(self._btn_up)

        self._btn_down = QPushButton("⬇ Mover abaixo")
        self._btn_down.setObjectName("btn_ghost")
        self._btn_down.setCursor(Qt.CursorShape.PointingHandCursor)
        row2.addWidget(self._btn_down)

        row2.addStretch()
        layout.addLayout(row2)

    # ── Conexões ────────────────────────────────────────────────────

    def _connect_signals(self):
        self._btn_add_files.clicked.connect(self._on_add_files)
        self._btn_add_folder.clicked.connect(self._on_add_folder)
        self._btn_remove.clicked.connect(self.remove_selected)
        self._btn_clear.clicked.connect(self.clear)
        self._btn_up.clicked.connect(self.move_up)
        self._btn_down.clicked.connect(self.move_down)

        self._list.itemSelectionChanged.connect(self._on_selection_changed)

    def _on_selection_changed(self):
        """Atualiza preview quando seleção muda."""
        sel_item = self._list.currentItem()
        if sel_item:
            path = sel_item.data(Qt.UserRole)
            self.selection_changed.emit(path or "")
            if self._preview_widget is not None and path:
                self._preview_widget.show_preview(path)
        else:
            self.selection_changed.emit("")
            if self._preview_widget is not None:
                self._preview_widget.clear_preview()

    # ── Ações dos Botões ────────────────────────────────────────────

    def _on_add_files(self):
        """Abre diálogo para selecionar múltiplos arquivos."""
        # Constrói filtro a partir do dict
        exts = list(self._ext_set)
        if exts:
            filter_str = "Imagens (" + " ".join(f"*{e}" for e in exts) + ")"
        else:
            filter_str = "Todos (*.*)"
        paths = ExplorerUtils.open_files(
            "Selecionar imagens", "", filter_str, self,
        )
        if paths:
            self.add_files(paths)

    def _on_add_folder(self):
        """Abre diálogo para selecionar pasta."""
        folder = ExplorerUtils.select_directory(
            "Selecionar pasta com imagens", "", self,
        )
        if folder:
            self.add_files([folder])

    # ── API Pública ─────────────────────────────────────────────────

    def add_files(self, paths: List[str]) -> None:
        """
        Adiciona arquivos/pastas à lista (com validação de extensão).
        Se for pasta e accept_dirs=True, vasculha recursivamente.

        Args:
            paths: Lista de caminhos de arquivos ou pastas.
        """
        count_before = self._list.count()
        self._list.add_files(paths)
        count_after = self._list.count()
        if count_after != count_before:
            self.files_changed.emit(count_after)

    def remove_selected(self) -> None:
        """Remove os itens selecionados da lista."""
        items = list(self._list.selectedItems())
        if not items:
            return
        for it in items:
            self._list.takeItem(self._list.row(it))
        count = self._list.count()
        self.files_changed.emit(count)
        self._on_selection_changed()

    def clear(self) -> None:
        """Limpa toda a lista."""
        self._list.clear()
        self.files_changed.emit(0)
        if self._preview_widget is not None:
            self._preview_widget.clear_preview()

    def move_up(self) -> None:
        """Move o item selecionado uma posição para cima."""
        row = self._list.currentRow()
        if row > 0:
            item = self._list.takeItem(row)
            self._list.insertItem(row - 1, item)
            self._list.setCurrentItem(item)

    def move_down(self) -> None:
        """Move o item selecionado uma posição para baixo."""
        row = self._list.currentRow()
        if 0 <= row < self._list.count() - 1:
            item = self._list.takeItem(row)
            self._list.insertItem(row + 1, item)
            self._list.setCurrentItem(item)

    def get_ordered_paths(self) -> List[str]:
        """Retorna lista de caminhos na ordem atual da lista."""
        return [
            self._list.item(i).data(Qt.UserRole)
            for i in range(self._list.count())
        ]

    def selected_path(self) -> str:
        """Retorna o caminho do item atualmente selecionado, ou vazio."""
        item = self._list.currentItem()
        if item:
            return item.data(Qt.UserRole) or ""
        return ""

    def count(self) -> int:
        """Número de itens na lista."""
        return self._list.count()


# ═══════════════════════════════════════════════════════════════════
# Widget interno: QListWidget com drag & drop e thumbnails
# ═══════════════════════════════════════════════════════════════════

class _FileListWidget(QListWidget):
    """QListWidget interno com suporte a drag & drop e thumbnails."""

    def __init__(
        self,
        ext_set: set[str],
        accept_dirs: bool,
        icon_size: tuple[int, int],
        parent=None,
    ):
        super().__init__(parent)
        self._ext_set = ext_set
        self._accept_dirs = accept_dirs
        self._icon_size = icon_size

        self.setAcceptDrops(True)
        self.setDragEnabled(True)
        self.setDragDropMode(QListWidget.InternalMove)
        self.setDefaultDropAction(Qt.MoveAction)
        self.setSelectionMode(QListWidget.ExtendedSelection)

    def add_files(self, paths: List[str]) -> None:
        """Adiciona caminhos validando extensões."""
        for p in paths:
            if os.path.isdir(p) and self._accept_dirs:
                self._add_directory(p)
            elif self._is_valid_file(p):
                self._add_item(p)

    def _add_directory(self, dir_path: str) -> None:
        """Vasculha pasta recursivamente e adiciona arquivos válidos."""
        try:
            for root, _dirs, files in os.walk(dir_path):
                for fname in sorted(files):
                    fp = os.path.join(root, fname)
                    if self._is_valid_file(fp):
                        self._add_item(fp)
        except (OSError, PermissionError):
            pass

    def _is_valid_file(self, path: str) -> bool:
        """Verifica se o arquivo tem extensão aceita."""
        if not os.path.isfile(path):
            return False
        if not self._ext_set:
            return True  # sem filtro, aceita tudo
        ext = os.path.splitext(path)[1].lower()
        return ext in self._ext_set

    def _add_item(self, path: str) -> None:
        """Adiciona um único item à lista (evita duplicatas)."""
        # Evita duplicatas
        abs_path = os.path.abspath(path)
        for i in range(self.count()):
            existing = self.item(i).data(Qt.UserRole)
            if existing and os.path.abspath(existing) == abs_path:
                return

        item = QListWidgetItem(os.path.basename(path))
        item.setToolTip(path)
        item.setData(Qt.UserRole, path)

        # Gera thumbnail
        thumbnail = self._generate_thumbnail(path)
        if thumbnail:
            item.setIcon(thumbnail)

        self.addItem(item)

    def _generate_thumbnail(self, path: str):
        """Gera QIcon thumbnail para o arquivo."""
        try:
            from PIL import Image as PILImage

            img = PILImage.open(path)
            w, h = self._icon_size
            img.thumbnail((w * 2, h * 2), PILImage.LANCZOS)
            bio = BytesIO()
            img.convert("RGBA").save(bio, format="PNG")
            qimg = QImage.fromData(bio.getvalue())
            return QPixmap.fromImage(qimg)
        except Exception:
            return None

    # ── Drag & Drop ────────────────────────────────────────────────

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