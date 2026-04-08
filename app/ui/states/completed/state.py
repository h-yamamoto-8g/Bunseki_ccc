"""CompletedUI — タスク完了画面の純粋レイアウト（generated UI 使用）。"""
from __future__ import annotations

from PySide6.QtWidgets import QWidget, QPushButton
from PySide6.QtCore import Signal, Qt

from app.ui.generated.ui_statecompleted import Ui_PageStateEnd


class CompletedUI(QWidget):
    """タスク完了画面 (純粋レイアウト)。

    Signals:
        list_requested(): タスク一覧に戻るボタン押下
    """

    list_requested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._form = Ui_PageStateEnd()
        self._form.setupUi(self)

        # ── グローバル QSS でリセットされるデフォルト spacing を明示設定 ──
        self._form.horizontalLayout.setSpacing(8)
        self._form.horizontalLayout.setContentsMargins(8, 8, 8, 8)

        # 一覧へ戻るボタンを label の下に追加
        back_btn = QPushButton("タスク一覧に戻る")
        back_btn.setFixedWidth(200)
        back_btn.clicked.connect(self.list_requested)
        self._form.widget.layout().addWidget(
            back_btn, alignment=Qt.AlignmentFlag.AlignCenter
        )

        # summary_lbl エイリアス (wrapper から参照)
        self.summary_lbl = self._form.label

    def set_summary(self, task: dict, done: bool = False) -> None:
        created = task.get("created_at", "")[:16].replace("T", " ")
        holder = task.get("holder_group_name", "")
        jobs = ", ".join(task.get("job_numbers", []))
        creator = task.get("created_by", "")
        n_samples = len(
            task.get("state_data", {})
            .get("analysis_targets", {})
            .get("valid_sample_set_codes", [])
        )

        if done:
            updated = task.get("updated_at", "")[:16].replace("T", " ")
            self._form.label.setText(
                f"タスクが完了しました\n"
                f"タスク名: {task.get('task_name', '')}\n"
                f"ホルダグループ: {holder}  JOB番号: {jobs}\n"
                f"担当者: {creator}  分析サンプル数: {n_samples} 件\n"
                f"起票日時: {created}  完了日時: {updated}"
            )
        else:
            self._form.label.setText(
                f"タスクは進捗中です\n"
                f"タスク名: {task.get('task_name', '')}\n"
                f"ホルダグループ: {holder}  JOB番号: {jobs}\n"
                f"担当者: {creator}  分析サンプル数: {n_samples} 件\n"
                f"起票日時: {created}"
            )
