"""CompletedState — タスク完了ステートのUIラッパー。"""
from __future__ import annotations

from PySide6.QtWidgets import QWidget, QVBoxLayout
from PySide6.QtCore import Signal

from .state import CompletedUI


class CompletedState(QWidget):
    go_list = Signal()

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._ui = CompletedUI()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self._ui)
        self._ui.list_requested.connect(self.go_list)

    def load_task(self, task: dict, preview: bool = False) -> None:
        self._ui.set_summary(task, preview=preview)
