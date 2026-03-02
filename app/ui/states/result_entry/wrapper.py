"""ResultEntryState — データ入力ステートのUIラッパー。"""
from __future__ import annotations

from PySide6.QtWidgets import QWidget, QVBoxLayout, QMessageBox
from PySide6.QtCore import Signal

from app.services.task_service import TaskService
from app.services.data_service import DataService
from .state import ResultEntryUI


class ResultEntryState(QWidget):
    go_next = Signal()
    go_back = Signal()

    def __init__(
        self,
        task_service: TaskService,
        data_service: DataService,
        parent=None,
    ) -> None:
        super().__init__(parent)
        self._task_service = task_service
        self._task: dict = {}

        self._ui = ResultEntryUI()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self._ui)

        self._ui.done_requested.connect(self._on_done)
        self._ui.back_requested.connect(self.go_back)
        self._ui.labaid_requested.connect(
            lambda: QMessageBox.information(self, "Lab-Aid", "Lab-Aidを起動します（デモ）")
        )

    def load_task(self, task: dict, readonly: bool = False) -> None:
        self._task = task
        self._ui.set_readonly(readonly)

    def _on_done(self) -> None:
        self._task = self._task_service.save_result_entry(self._task["task_id"])
        self.go_next.emit()
