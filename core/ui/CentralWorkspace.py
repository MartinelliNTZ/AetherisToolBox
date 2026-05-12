# -*- coding: utf-8 -*-
"""
Workspace — Área de trabalho do Aetheris ToolBox
==================================================
Gerencia múltiplas ferramentas via QTabBar + QStackedWidget.
Cada ferramenta é um widget registrado com um nome único.

Abas podem ser fechadas (×) e movidas (drag).
Ao clicar em uma ferramenta na toolbar, se já estiver aberta,
apenas foca a aba. Caso contrário, abre uma nova aba.
"""

from __future__ import annotations

from PySide6.QtCore import Qt, Signal, Slot, QPoint, QRect
from PySide6.QtGui import QPainter, QPen, QColor, QFont, QFontMetrics, QPainterPath
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QStackedWidget,
    QTabBar, QScrollArea, QFrame, QMenu
)

from core.config.LogUtils import LogUtils
from core.enum.CategoryTool import CategoryTool
from core.model.Tool import Tool
from resources.styles.styles import Palette


class _WorkspaceTabBar(QTabBar):
    """
    QTabBar customizado que desenha as abas com paintEvent próprio.
    Corner-radius: 2 8 2 2 (similar ao VerticalTab mas invertido).
    Hover: fundo GOLD + texto BG_DEEPEST.
    Selected: fundo GOLD + texto BG_DEEPEST com barra indicadora no topo.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("workspace_tabs")
        self._hovered_tab = -1

        self.setMouseTracking(True)
        self.setDrawBase(True)
        self.setExpanding(False)
        self.setMovable(True)
        self.setTabsClosable(True)

    def _tab_rect(self, index: int) -> QRect:
        """Retorna o retângulo da aba com padding interno."""
        r = self.tabRect(index)
        return QRect(r.x() + 1, r.y() + 1, r.width() - 2, r.height() - 3)

    def _draw_rounded_rect(self, painter, rect, tl=2, tr=8, br=2, bl=2):
        path = QPainterPath()
        path.moveTo(rect.left() + tl, rect.top())
        path.lineTo(rect.right() - tr, rect.top())
        path.arcTo(rect.right() - 2*tr, rect.top(), 2*tr, 2*tr, 90, -90)
        path.lineTo(rect.right(), rect.bottom() - br)
        path.arcTo(rect.right() - 2*br, rect.bottom() - 2*br, 2*br, 2*br, 0, -90)
        path.lineTo(rect.left() + bl, rect.bottom())
        path.arcTo(rect.left(), rect.bottom() - 2*bl, 2*bl, 2*bl, 270, -90)
        path.lineTo(rect.left(), rect.top() + tl)
        path.arcTo(rect.left(), rect.top(), 2*tl, 2*tl, 180, -90)
        path.closeSubpath()
        return path

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setRenderHint(QPainter.RenderHint.TextAntialiasing)

        P = Palette

        # Fundo do tab bar (a area vazia a direita)
        painter.fillRect(event.rect(), QColor(P.TITLE_BAR_BG))

        for i in range(self.count()):
            rect = self._tab_rect(i)
            if not rect.isValid() or rect.width() < 4:
                continue

            selected = (i == self.currentIndex())
            hovered = (i == self._hovered_tab)

            if selected:
                bg     = QColor(P.GOLD)
                fg     = QColor(P.BG_DEEPEST)
                border = QColor(P.GOLD_DIM)
            elif hovered:
                bg     = QColor(P.GOLD)
                fg     = QColor(P.BG_DEEPEST)
                border = QColor(P.BORDER_HOVER)
            else:
                bg     = QColor(P.BG_DEEPEST)
                fg     = QColor(P.TEXT_SECONDARY)
                border = QColor(P.BORDER)

            path = self._draw_rounded_rect(painter, rect, tl=2, tr=8, br=2, bl=2)
            painter.setClipPath(path)
            painter.fillPath(path, bg)

            # Indicador de selecao (barra no topo)
            if selected:
                painter.fillRect(rect.x(), rect.y(), rect.width(), 3, QColor(P.GOLD_HOVER))

            painter.setPen(QPen(border, 1))
            painter.drawPath(path)
            painter.setClipping(False)

            # Texto da aba
            name = self.tabData(i)
            display = str(name) if name else f"Tab {i}"
            font = QFont("Segoe UI", 10)
            font.setWeight(QFont.Weight.Medium if selected else QFont.Weight.Normal)
            painter.setFont(font)
            painter.setPen(QPen(fg))

            fm = QFontMetrics(font)
            text = fm.elidedText(display, Qt.TextElideMode.ElideRight, rect.width() - 16)
            painter.drawText(
                rect.adjusted(8, 0, -8, 0),
                Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft,
                text,
            )

        painter.end()

    def mouseMoveEvent(self, event):
        tab = self.tabAt(event.pos())
        old = self._hovered_tab
        self._hovered_tab = tab if tab >= 0 else -1
        if old != self._hovered_tab:
            self.update()
        super().mouseMoveEvent(event)

    def leaveEvent(self, event):
        self._hovered_tab = -1
        self.update()
        super().leaveEvent(event)


class CentralWorkspace(QWidget):

    current_tool_changed = Signal(int, object)
    tool_closed          = Signal(str)
    tool_request_move_to_side = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._tools: dict[str, Tool] = {}   # nome -> Tool
        self._log = LogUtils(tool="System", class_name="Workspace")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.tab_bar = _WorkspaceTabBar()
        self.tab_bar.tabCloseRequested.connect(self._on_tab_close_requested)
        self.tab_bar.currentChanged.connect(self._on_tab_changed)
        self.tab_bar.tabMoved.connect(self._on_tab_moved)
        self.tab_bar.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.tab_bar.customContextMenuRequested.connect(self._on_tab_context_menu)
        layout.addWidget(self.tab_bar)

        sep = QFrame()
        sep.setObjectName("workspace_separator")
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setFixedHeight(1)
        layout.addWidget(sep)

        self.stack = QStackedWidget()
        layout.addWidget(self.stack, 1)

    # ------------------------------------------------------------------
    # API pública
    # ------------------------------------------------------------------

    def register_tool(self, tool: Tool, focus: bool = True) -> str:
        """Registra uma ferramenta. Retorna o nome."""
        name = tool.name
        self._tools[name] = tool

        # Placeholder no stack (na mesma posição da aba)
        placeholder = QWidget()
        self.stack.addWidget(placeholder)

        # Aba no tab bar — tabData guarda o NOME (viaja junto no drag)
        tab_index = self.tab_bar.addTab("")
        if tool.tooltip:
            self.tab_bar.setTabToolTip(tab_index, tool.tooltip)
        self.tab_bar.setTabData(tab_index, name)

        self._log.info(f"Tool registrada: {name}", code="TOOL_REG")

        if focus:
            self.tab_bar.setCurrentIndex(tab_index)

        return name

    def open_tool(self, tool: Tool) -> str:
        """Abre ou foca uma ferramenta. Retorna o nome."""
        name = tool.name
        if name in self._tools:
            self.set_current_tool(name)
            return name
        return self.register_tool(tool, focus=True)

    def set_current_tool(self, name: str) -> None:
        """Muda para a aba com o nome da ferramenta."""
        for tab_id in range(self.tab_bar.count()):
            if self.tab_bar.tabData(tab_id) == name:
                if self.tab_bar.currentIndex() == tab_id:
                    self._on_tab_changed(tab_id)
                else:
                    self.tab_bar.setCurrentIndex(tab_id)
                return

    def current_tool_name(self) -> str | None:
        tid = self.tab_bar.currentIndex()
        return self.tab_bar.tabData(tid) if tid >= 0 else None

    def current_tool_widget(self) -> QWidget | None:
        name = self.current_tool_name()
        if name and name in self._tools:
            return self._tools[name].widget
        return None

    def is_tool_open(self, name: str) -> bool:
        return name in self._tools

    def remove_tool_by_name(self, name: str, keep_widget: bool = True) -> bool:
        tool = self._tools.get(name)
        if tool is None:
            return False

        tab_index = -1
        for tid in range(self.tab_bar.count()):
            if self.tab_bar.tabData(tid) == name:
                tab_index = tid
                break
        if tab_index < 0:
            return False

        w = self.stack.widget(tab_index)
        if w:
            self.stack.removeWidget(w)
            if keep_widget:
                if isinstance(w, QScrollArea):
                    inner = w.widget()
                    if inner:
                        w.takeWidget()
                        inner.setParent(None)
                w.deleteLater()
            else:
                w.deleteLater()

        self.tab_bar.removeTab(tab_index)
        del self._tools[name]

        if not keep_widget:
            tool.unload()
            self.tool_closed.emit(name)

        self._log.info(f"Aba removida (move): {name}", code="TAB_MOVED_OUT")
        return True

    # ------------------------------------------------------------------
    # Slots privados
    # ------------------------------------------------------------------

    @Slot(int, int)
    def _on_tab_moved(self, from_idx: int, to_idx: int) -> None:
        w = self.stack.widget(from_idx)
        if w:
            self.stack.removeWidget(w)
            self.stack.insertWidget(to_idx, w)
        self._log.debug(f"Aba movida: {from_idx} -> {to_idx}", code="TAB_MOVED")

    @Slot(int)
    def _on_tab_changed(self, tab_index: int) -> None:
        name = self.tab_bar.tabData(tab_index)
        if not name or name not in self._tools:
            return

        tool = self._tools[name]

        if not tool.is_loaded:
            self._log.info(f"Carregando tool (lazy): {name}", code="LAZY_LOAD")
            widget = tool.widget
            scroll = QScrollArea()
            scroll.setWidgetResizable(True)
            scroll.setHorizontalScrollBarPolicy(
                Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
            scroll.setWidget(widget)
            scroll.setObjectName(f"workspace_scroll_{name}")

            old = self.stack.widget(tab_index)
            if old:
                self.stack.removeWidget(old)
                old.deleteLater()
            self.stack.insertWidget(tab_index, scroll)

        self.stack.setCurrentIndex(tab_index)
        self.current_tool_changed.emit(-1, tool.widget if tool.is_loaded else None)

    @Slot(QPoint)
    def _on_tab_context_menu(self, pos):
        tab_index = self.tab_bar.tabAt(pos)
        if tab_index < 0:
            return
        name = self.tab_bar.tabData(tab_index)
        if not name or name not in self._tools:
            return

        tool = self._tools[name]
        if tool.category != CategoryTool.BOTH:
            return

        menu = QMenu(self)
        move_action = menu.addAction("Mover para Side")
        action = menu.exec(self.tab_bar.mapToGlobal(pos))
        if action == move_action:
            self.tool_request_move_to_side.emit(name)

    @Slot(int)
    def _on_tab_close_requested(self, tab_index: int) -> None:
        name = self.tab_bar.tabData(tab_index)
        if not name or name not in self._tools:
            self._log.error(
                f"Tentativa de fechar aba inexistente: tab={tab_index}",
                code="TAB_CLOSE_ERR")
            return

        tool = self._tools[name]

        w = self.stack.widget(tab_index)
        if w:
            self.stack.removeWidget(w)
            w.deleteLater()

        self.tab_bar.removeTab(tab_index)
        del self._tools[name]
        tool.unload()
        self.tool_closed.emit(name)
        self._log.info(f"Aba fechada: {name}", code="TAB_CLOSED")