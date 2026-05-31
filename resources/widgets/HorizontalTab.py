from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QWidget, QHBoxLayout, QLabel, QSizePolicy


class HorizontalTab(QWidget):
    """
    Aba customizada do Workspace.
    A formatação visual (fundo, bordas, fonte) é feita via QSS em styles.py,
    aplicada diretamente no QTabBar::tab.

    Args:
        title: Texto exibido na aba.
        tooltip: Tooltip opcional.
        closable: Se True (padrão), exibe botão de fechar na aba.
        parent: Widget pai.
    """

    def __init__(self, title: str, tooltip: str = "", closable: bool = True, parent=None):
        super().__init__(parent)
        self._title = title
        self._closable = closable
        self.setObjectName("workspace_tab")
        if tooltip:
            self.setToolTip(tooltip)
        self._build_ui()

    def _build_ui(self) -> None:
        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 2, 8, 2)
        layout.setSpacing(0)

        self._label = QLabel(self._title)
        self._label.setObjectName("workspace_tab_label")
        self._label.setAttribute(Qt.WA_TransparentForMouseEvents)
        self._label.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Preferred)
        self._label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self._label)

        self.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Preferred)
        self.adjustSize()

    @property
    def title(self) -> str:
        return self._title

    @title.setter
    def title(self, value: str) -> None:
        self._title = value
        self._label.setText(value)
        self.adjustSize()