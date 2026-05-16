# -*- coding: utf-8 -*-
"""
UI Principal — Aetheris ToolBox
================================
MainWindow modular com AppBar, MenuManager e WorkspaceManager.

A MainWindow POSICIONA os widgets prontos — a lógica de negócio
fica encapsulada nos managers (MenuManager, WorkspaceManager).
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import List, Optional

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QProgressBar,
)
from PySide6.QtCore import Qt, QRect, QPoint
from PySide6.QtGui import QIcon
if sys.platform == "win32":
    import ctypes
    import ctypes.wintypes

from core.model.Tool import Tool
from core.enum.ResizeMode import ResizeMode
from resources.widgets.app_bar import AppBar
from core.config.MenuManager import MenuManager
from core.config.WorkspaceManager import WorkspaceManager
from core.dialogs.AboutDialog import AboutDialog


class MainWindow(QMainWindow):
    """
    Janela principal do Aetheris ToolBox.

    Layout:
      [AppBar]
      [MenuManager.menu_bar]
      [MenuManager.toolbar_widget]
      [WorkspaceManager]  ← splitter: CentralWorkspace | SideWorkspace
      [ProgressBar]

    Nenhuma lógica de workspace ou menu vive aqui.
    """

    # ── Borda de detecção para resize (pixels) ──
    RESIZE_MARGIN = 8

    def __init__(self, tools: List[Tool]):
        super().__init__()
        self.setWindowTitle("Aetheris ToolBox")
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Window)
        self.setMinimumSize(1000, 650)
        self.resize(1100, 700)

        icon_path = Path(__file__).parent.parent.parent / "Aetheris.png"
        if icon_path.exists():
            self.setWindowIcon(QIcon(str(icon_path)))

        # ── Modo de resize (troque aqui para experimentar) ──
        self._resize_mode: ResizeMode = ResizeMode.NATIVE

        # ── Estado interno para resize via cursor ──
        self._resize_dragging = False
        self._resize_direction = 0  # bitmask: 1=N, 2=S, 4=W, 8=E
        self._resize_rect = QRect()
        self._resize_global_start = QPoint()

        self._build_ui(tools)
        self._setup_resize_mode()

    # ────────────────────────────────────────────────────────────────
    # Troca de modo de resize
    # ────────────────────────────────────────────────────────────────

    @property
    def resize_mode(self) -> ResizeMode:
        """Modo atual de redimensionamento."""
        return self._resize_mode

    @resize_mode.setter
    def resize_mode(self, mode: ResizeMode) -> None:
        """Altera o modo de resize em tempo real."""
        if mode == self._resize_mode:
            return
        self._resize_mode = mode
        self._setup_resize_mode()

    def _setup_resize_mode(self) -> None:
        """(Re)configura o modo de resize atual."""
        from core.config.LogUtils import LogUtils
        logger = LogUtils(tool="System", class_name="MainWindow")
        logger.info(
            "Modo de resize alterado",
            code="RESIZE_MODE",
            mode=self._resize_mode.value,
        )

        # Sempre desabilita mouse tracking primeiro
        self.setMouseTracking(False)

        if self._resize_mode == ResizeMode.NATIVE:
            # nativeEvent é sempre chamado, não precisa configurar nada extra
            pass

        elif self._resize_mode == ResizeMode.CURSOR:
            # Habilita mouse tracking para detectar bordas
            self.setMouseTracking(True)

    # ────────────────────────────────────────────────────────────────
    # nativeEvent — Modo NATIVO (Windows WM_NCHITTEST)
    # ────────────────────────────────────────────────────────────────

    def nativeEvent(self, event_type: bytes, message) -> tuple:
        """
        Intercepta WM_NCHITTEST do Windows para resize nativo.
        message é sip.voidptr no PySide6.
        """
        if self._resize_mode != ResizeMode.NATIVE or sys.platform != "win32":
            return super().nativeEvent(event_type, message)

        if event_type != b"windows_generic_MSG":
            return super().nativeEvent(event_type, message)

        try:
            # Converte sip.voidptr para ponteiro MSG
            msg = ctypes.wintypes.MSG.from_address(int(message))
            if msg.message != 0x0084:  # WM_NCHITTEST
                return super().nativeEvent(event_type, message)

            # Extrai coordenadas X, Y de lParam (signed 16-bit cada)
            raw = msg.lParam
            screen_x = ctypes.c_short(raw & 0xFFFF).value
            screen_y = ctypes.c_short((raw >> 16) & 0xFFFF).value

            return self._hit_test(screen_x, screen_y)
        except Exception:
            return super().nativeEvent(event_type, message)

    def _hit_test(self, screen_x: int, screen_y: int) -> tuple:
        """
        Calcula a região de resize pela posição do cursor.
        Retorna (True, HT_XXXX) se em borda, (False, 0) caso contrário.
        """
        if self.isMaximized() or self.isFullScreen():
            return False, 0

        r = self.frameGeometry()
        x = screen_x - r.x()
        y = screen_y - r.y()
        w, h = r.width(), r.height()
        m = self.RESIZE_MARGIN

        on_left = x < m
        on_right = x > w - m
        on_top = y < m
        on_bottom = y > h - m

        # Constantes Windows
        HT_NOWHERE = 0
        HT_LEFT, HT_RIGHT, HT_TOP, HT_BOTTOM = 10, 11, 12, 15
        HT_TOPLEFT, HT_TOPRIGHT = 13, 14
        HT_BOTTOMLEFT, HT_BOTTOMRIGHT = 16, 17

        if on_top and on_left:
            return True, HT_TOPLEFT
        if on_top and on_right:
            return True, HT_TOPRIGHT
        if on_bottom and on_left:
            return True, HT_BOTTOMLEFT
        if on_bottom and on_right:
            return True, HT_BOTTOMRIGHT
        if on_left:
            return True, HT_LEFT
        if on_right:
            return True, HT_RIGHT
        if on_top:
            return True, HT_TOP
        if on_bottom:
            return True, HT_BOTTOM

        return False, 0

    # ────────────────────────────────────────────────────────────────
    # mouse tracking — Modo CURSOR (cross-platform)
    # ────────────────────────────────────────────────────────────────

    def _get_resize_direction(self, pos: QPoint) -> int:
        """
        Retorna bitmask da direção de resize baseado na posição
        relativa ao widget. Retorna 0 se não estiver em borda.
        """
        if self.isMaximized() or self.isFullScreen():
            return 0

        r = self.rect()
        x, y = pos.x(), pos.y()
        w, h = r.width(), r.height()
        m = self.RESIZE_MARGIN

        direction = 0
        if x < m:
            direction |= 4  # W
        if x > w - m:
            direction |= 8  # E
        if y < m:
            direction |= 1  # N
        if y > h - m:
            direction |= 2  # S
        return direction

    def _cursor_for_direction(self, direction: int) -> Qt.CursorShape:
        """Retorna o cursor adequado para a direção de resize."""
        if direction in (1 | 4, 2 | 8):  # NW, SE
            return Qt.CursorShape.SizeFDiagCursor
        if direction in (1 | 8, 2 | 4):  # NE, SW
            return Qt.CursorShape.SizeBDiagCursor
        if direction in (4, 8):  # W, E
            return Qt.CursorShape.SizeHorCursor
        if direction in (1, 2):  # N, S
            return Qt.CursorShape.SizeVerCursor
        return Qt.CursorShape.ArrowCursor

    def mouseMoveEvent(self, event):
        if self._resize_mode != ResizeMode.CURSOR:
            super().mouseMoveEvent(event)
            return

        if self._resize_dragging:
            # Redimensionando — calcula nova geometria
            self._do_resize(event.globalPosition().toPoint())
            event.accept()
            return

        # Só muda o cursor se não estiver sobre a AppBar
        direction = self._get_resize_direction(event.position().toPoint())
        if direction:
            self.setCursor(self._cursor_for_direction(direction))
        else:
            self.setCursor(Qt.CursorShape.ArrowCursor)

        super().mouseMoveEvent(event)

    def mousePressEvent(self, event):
        if self._resize_mode != ResizeMode.CURSOR:
            super().mousePressEvent(event)
            return

        if event.button() == Qt.MouseButton.LeftButton:
            direction = self._get_resize_direction(event.position().toPoint())
            if direction:
                self._resize_dragging = True
                self._resize_direction = direction
                self._resize_rect = QRect(self.geometry())
                self._resize_global_start = event.globalPosition().toPoint()
                event.accept()
                return

        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        if self._resize_mode != ResizeMode.CURSOR:
            super().mouseReleaseEvent(event)
            return

        if event.button() == Qt.MouseButton.LeftButton and self._resize_dragging:
            self._resize_dragging = False
            self._resize_direction = 0
            event.accept()
            return

        super().mouseReleaseEvent(event)

    def _do_resize(self, global_pos: QPoint) -> None:
        """Aplica o redimensionamento baseado na posição global atual."""
        start = self._resize_global_start
        dx = global_pos.x() - start.x()
        dy = global_pos.y() - start.y()

        r = QRect(self._resize_rect)
        dir_ = self._resize_direction
        m = self.minimumSize()
        min_w = m.width()
        min_h = m.height()
        max_w = self.maximumWidth()
        max_h = self.maximumHeight()

        # Norte
        if dir_ & 1:
            new_y = r.y() + dy
            new_h = r.height() - dy
            if new_h < min_h:
                new_h = min_h
                new_y = r.bottom() - min_h
            elif 0 < max_h < new_h:
                new_h = max_h
                new_y = r.bottom() - max_h
            r.setY(new_y)
            r.setHeight(new_h)

        # Sul
        if dir_ & 2:
            new_h = r.height() + dy
            if new_h < min_h:
                new_h = min_h
            elif 0 < max_h < new_h:
                new_h = max_h
            r.setHeight(new_h)

        # Oeste
        if dir_ & 4:
            new_x = r.x() + dx
            new_w = r.width() - dx
            if new_w < min_w:
                new_w = min_w
                new_x = r.right() - min_w
            elif 0 < max_w < new_w:
                new_w = max_w
                new_x = r.right() - max_w
            r.setX(new_x)
            r.setWidth(new_w)

        # Leste
        if dir_ & 8:
            new_w = r.width() + dx
            if new_w < min_w:
                new_w = min_w
            elif 0 < max_w < new_w:
                new_w = max_w
            r.setWidth(new_w)

        # Se mudou, atualiza geometria e guarda novo start
        if r != self.geometry():
            self.setGeometry(r)
            self._resize_global_start = global_pos
            self._resize_rect = QRect(self.geometry())

    # ────────────────────────────────────────────────────────────────
    # Fim dos modos de resize
    # ────────────────────────────────────────────────────────────────

    def _build_ui(self, tools: List[Tool]) -> None:
        from core.config.LogUtils import LogUtils

        logger = LogUtils(tool="System", class_name="MainWindow")
        logger.info("Construindo interface", code="UI_BUILD", num_tools=len(tools))

        root = QWidget()
        root_layout = QVBoxLayout(root)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)
        self.setCentralWidget(root)

        # ── 1. APPBAR ──
        self.appbar = AppBar()
        self.appbar.minimize_clicked.connect(self.showMinimized)
        self.appbar.maximize_restore_clicked.connect(self._toggle_maximize_restore)
        self.appbar.close_clicked.connect(self.close)
        root_layout.addWidget(self.appbar)

        # ── 2. MENU + TOOLBAR (encapsulado no MenuManager) ──
        self._menu_manager = MenuManager()
        self._menu_manager.build()
        self._menu_manager.tool_activated.connect(self._on_tool_activated)
        self._menu_manager.sair_clicked.connect(self.close)
        self._menu_manager.sobre_clicked.connect(self._show_about)
        root_layout.addWidget(self._menu_manager.menu_bar)
        root_layout.addWidget(self._menu_manager.toolbar_widget)

        # ── 3. WORKSPACE (encapsulado no WorkspaceManager) ──
        self._workspace_manager = WorkspaceManager(tools)
        root_layout.addWidget(self._workspace_manager, 1)

        # ── 4. PROGRESS BAR ──
        self.progress = QProgressBar()
        self.progress.setMinimum(0)
        self.progress.setMaximum(10000)
        self.progress.setValue(0)
        self.progress.setTextVisible(True)
        self.progress.setFormat(" %p% - aguardando... ")
        self.progress.setFixedHeight(20)
        root_layout.addWidget(self.progress)

        # Conecta sinal de progresso
        from core.manager.SignalManager import SignalManager
        SignalManager.instance().progress_update.connect(self._on_progress_update)

    # ────────────────────────────────────────────────────────────────
    # About Dialog
    # ────────────────────────────────────────────────────────────────

    def _show_about(self):
        dialog = AboutDialog(self)
        dialog.exec()

    # ────────────────────────────────────────────────────────────────
    # Ativação de ferramenta (via toolbar ou menu)
    # ────────────────────────────────────────────────────────────────

    def _on_tool_activated(self, tool_name: str):
        """Delega abertura de ferramenta ao WorkspaceManager."""
        self._workspace_manager.open_tool(tool_name)

    # ────────────────────────────────────────────────────────────────
    # Acesso público (compatibilidade com código existente)
    # ────────────────────────────────────────────────────────────────

    @property
    def central_workspace(self):
        return self._workspace_manager.central_workspace

    @property
    def side_workspace(self):
        return self._workspace_manager.side_workspace

    def get_tool(self, name: str) -> Optional[Tool]:
        return self._workspace_manager.get_tool(name)

    def switch_to_tool(self, name: str) -> bool:
        return self._workspace_manager.switch_to_tool(name)

    def switch_to_console(self) -> None:
        self._workspace_manager.switch_to_console()

    # ────────────────────────────────────────────────────────────────
    # Controle de janela
    # ────────────────────────────────────────────────────────────────

    def _on_progress_update(self, value: float):
        """Atualiza a barra de progresso com 2 casas decimais."""
        scaled = int(round(value * 100.0))
        self.progress.setValue(scaled)
        if value <= 0:
            self.progress.setFormat(" %p% - aguardando... ")
        elif value >= 100:
            self.progress.setFormat(" 100% - concluído! ")
        else:
            self.progress.setFormat(f" {value:.2f}% - executando... ")

    def _toggle_maximize_restore(self) -> None:
        if self.isMaximized():
            self.showNormal()
        else:
            self.showMaximized()