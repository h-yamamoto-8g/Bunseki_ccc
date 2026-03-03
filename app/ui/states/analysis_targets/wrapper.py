"""AnalysisTargetsState — 分析対象ステートのUIラッパー。"""
from __future__ import annotations

from PySide6.QtWidgets import QWidget, QVBoxLayout, QMessageBox, QDialog, QApplication
from PySide6.QtCore import Signal

from app.services.task_service import TaskService
from app.services.data_service import DataService
from .state import AnalysisTargetsUI, AddSampleDialog
from .print_preview import PrintPreviewDialog


class AnalysisTargetsState(QWidget):
    go_next = Signal()
    go_back = Signal()
    step_edited = Signal(str)       # 編集済みになった state_id を送出
    loading_changed = Signal(bool, str)  # (is_loading, message)

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
        self._readonly = False
        self._edit_mode = False

        self._ui = AnalysisTargetsUI()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self._ui)

        self._ui.next_requested.connect(self._on_next)
        self._ui.back_requested.connect(self.go_back)
        self._ui.add_sample_requested.connect(self._on_add_sample)
        self._ui.delete_row_requested.connect(self._ui.apply_delete)
        self._ui.edit_requested.connect(self._on_edit_requested)
        self._ui.content_edited.connect(
            lambda: self.step_edited.emit("analysis_targets")
        )
        self._ui.print_btn.clicked.connect(self._on_print)

    # ── Public API ────────────────────────────────────────────────────────────

    def load_task(self, task: dict, readonly: bool = False) -> None:
        self._task = task
        self._readonly = readonly
        self._edit_mode = False
        self._ui.edited_badge.setVisible(False)

        hg_code = task.get("holder_group_code", "")
        jobs = task.get("job_numbers", [])

        self.loading_changed.emit(True, "分析対象データを取得しています...")
        QApplication.processEvents()
        samples = self._data_service.get_analysis_targets(hg_code, jobs)
        self.loading_changed.emit(False, "")

        sd = task.get("state_data", {}).get("analysis_targets", {})
        deleted_codes = set(sd.get("deleted_codes", []))
        added_samples = list(sd.get("added_samples", []))

        self._ui.set_samples(samples, deleted_codes, added_samples)
        self._ui.set_editable(False)

        if readonly:
            self._ui.show_edit_btn(False)
            self._ui.set_nav_visible(False)
        else:
            self._ui.set_nav_visible(True)
            if task.get("current_state") != "analysis_targets":
                self._ui.show_edit_btn(True)
            else:
                self._ui.set_editable(True)
                self._ui.show_edit_btn(False)

    # ── Handlers ─────────────────────────────────────────────────────────────

    def _on_print(self) -> None:
        table = self._ui.table
        col_count = table.columnCount() - 1  # 最終列（削除ボタン）を除外

        headers = [
            table.horizontalHeaderItem(c).text() for c in range(col_count)
        ]
        rows = []
        for r in range(table.rowCount()):
            rows.append([
                (table.item(r, c).text() if table.item(r, c) else "")
                for c in range(col_count)
            ])

        hg_name = self._task.get("holder_group_name", "")
        title = f"分析対象一覧 — {hg_name}" if hg_name else "分析対象一覧"

        dlg = PrintPreviewDialog(title, headers, rows, self)
        dlg.exec()

    def _on_edit_requested(self) -> None:
        self._edit_mode = True
        self._ui.set_editable(True)
        self._ui.show_edit_btn(False)

    def _on_add_sample(self) -> None:
        valid_samples = self._data_service.get_valid_samples()
        dlg = AddSampleDialog(valid_samples, self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            name = dlg.selected_name()
            if name:
                self._ui.add_free_sample(name)

    def _on_next(
        self,
        vsset_codes: list,
        deleted_codes: list,
        added_samples: list,
    ) -> None:
        task_id = self._task["task_id"]
        current = self._task.get("current_state", "analysis_targets")
        in_edit = self._edit_mode and current not in ("analysis_targets", "task_setup")

        if in_edit:
            reply = QMessageBox.question(
                self,
                "確認",
                "分析対象を変更すると、以降のステートのデータが初期化されます。\n続行しますか？",
                QMessageBox.StandardButton.Ok | QMessageBox.StandardButton.Cancel,
            )
            if reply != QMessageBox.StandardButton.Ok:
                return

        self._task = self._task_service.save_analysis_targets(
            task_id, vsset_codes, deleted_codes, added_samples, in_edit
        )
        self.go_next.emit()
