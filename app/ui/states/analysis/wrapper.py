"""AnalysisState — 分析準備ステートのUIラッパー。"""
from __future__ import annotations

from PySide6.QtWidgets import QWidget, QVBoxLayout
from PySide6.QtCore import Signal

from app.services.task_service import TaskService
from app.services.data_service import DataService
from .state import AnalysisUI


class AnalysisState(QWidget):
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
        self._data_service = data_service
        self._task: dict = {}

        self._ui = AnalysisUI()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self._ui)

        self._ui.finish_requested.connect(self._on_finish)
        self._ui.back_requested.connect(self.go_back)

    def load_task(self, task: dict, readonly: bool = False) -> None:
        self._task = task
        hg_code = task.get("holder_group_code", "")
        cfg = self._data_service.get_analysis_config(hg_code)
        self._ui.set_config(cfg)

        sd = task.get("state_data", {}).get("analysis", {})
        pre_saved  = sd.get("pre_checks",  [False] * len(self._ui._pre_checks))
        post_saved = sd.get("post_checks", [False] * len(self._ui._post_checks))
        self._ui.restore_checks(pre_saved, post_saved, readonly)

    def set_state_done(self, done: bool) -> None:
        """完了済みステートなら完了ボタンを無効化して「完了済み」にする。"""
        if done:
            self._ui.finish_btn.setEnabled(False)
            self._ui.finish_btn.setText("完了済み")
        else:
            self._ui.finish_btn.setText("完了")

    def _on_finish(self, pre_checks: list, post_checks: list) -> None:
        self._task = self._task_service.save_analysis(
            self._task["task_id"], pre_checks, post_checks
        )
        self.go_next.emit()
