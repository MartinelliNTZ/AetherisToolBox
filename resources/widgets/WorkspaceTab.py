from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QWidget, QHBoxLayout, QLabel, QSizePolicy


class WorkspaceTab(QWidget):

    def __init__(self, title: str, tooltip: str = "", parent=None):
        super().__init__(parent)
        self._title = title
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
        layout.addWidget(self._label)

        # Widget se ajusta ao conteúdo automaticamente
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