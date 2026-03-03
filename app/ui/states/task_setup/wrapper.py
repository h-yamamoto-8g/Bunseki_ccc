"""TaskSetupState — 起票ステートのUIラッパー。

TaskSetupUI のシグナルを受け取り、TaskService / DataService を呼び出す。
"""
from __future__ import annotations

from PySide6.QtWidgets import QWidget, QVBoxLayout, QMessageBox
from PySide6.QtCore import Signal

from app.services.task_service import TaskService
from app.services.data_service import DataService
from .state import TaskSetupUI


class TaskSetupState(QWidget):
    """起票ステートのラッパー。

    Signals:
        submitted(task): 起票・保存完了後に task dict を emit
        cancelled(): キャンセル
    """

    submitted = Signal(dict)
    cancelled = Signal()
    go_next = Signal()

    def __init__(
        self,
        task_service: TaskService,
        data_service: DataService,
        parent=None,
    ) -> None:
        super().__init__(parent)
        self._task_service = task_service
        self._data_service = data_service
        self._task_id: str | None = None
        self._edit_mode = False

        self._ui = TaskSetupUI()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self._ui)

        self._ui.form_submitted.connect(self._on_form_submitted)
        self._ui.edit_requested.connect(self._on_edit_requested)
        self._ui.cancelled.connect(self.cancelled)
        self._ui.next_requested.connect(self.go_next)

    # ── Public API ────────────────────────────────────────────────────────────

    def open_new(self) -> None:
        self._task_id = None
        self._edit_mode = False
        hg_list = self._data_service.get_holder_groups()
        self._ui.set_holder_groups(hg_list)
        self._ui.show_new_mode()

    def open_existing(self, task: dict, readonly: bool = False) -> None:
        self._task_id = task["task_id"]
        self._edit_mode = False
        sd = task.get("state_data", {}).get("task_setup", {})
        hg_code = sd.get("holder_group_code", task.get("holder_group_code", ""))
        job_numbers = list(sd.get("job_numbers", task.get("job_numbers", [])))

        hg_list = self._data_service.get_holder_groups()
        self._ui.set_holder_groups(hg_list)
        self._ui.set_task_data(hg_code, job_numbers)
        self._ui.show_existing_mode(readonly)

    # ── Handlers ─────────────────────────────────────────────────────────────

    def _on_edit_requested(self) -> None:
        self._edit_mode = True
        self._ui.show_edit_mode()

    def _on_form_submitted(
        self, hg_code: str, hg_name: str, job_numbers: list
    ) -> None:
        if not hg_code:
            QMessageBox.warning(self, "入力エラー", "ホルダグループを選択してください。")
            return

        if self._task_id is None:
            task = self._task_service.create_task_setup(hg_code, hg_name, job_numbers)
        else:
            if self._edit_mode:
                reply = QMessageBox.question(
                    self,
                    "確認",
                    "起票情報を変更すると、以降のステートのデータが初期化されます。\n続行しますか？",
                    QMessageBox.StandardButton.Ok | QMessageBox.StandardButton.Cancel,
                )
                if reply != QMessageBox.StandardButton.Ok:
                    return
            task = self._task_service.update_task_setup(
                self._task_id, hg_code, hg_name, job_numbers, self._edit_mode
            )

        self.submitted.emit(task)
