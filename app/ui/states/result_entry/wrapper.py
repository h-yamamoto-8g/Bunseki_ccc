"""ResultEntryState — データ入力ステートのUIラッパー。"""
from __future__ import annotations

import subprocess
import webbrowser

from PySide6.QtWidgets import QWidget, QVBoxLayout, QMessageBox
from PySide6.QtCore import Signal

from app.services.task_service import TaskService
from app.services.data_service import DataService
from app.services.data_update_service import run_all as _run_data_update
from .state import ResultEntryUI

# ─────────────────────────────────────────────────────────────────────────────
# TODO: Lab-Aid の起動方法を変更するにはここを編集する。
#
#   パターン A — ローカル実行ファイル（Windows）:
#     _LABAID_PATH = r"C:\LabAid\LabAid.exe"
#
#   パターン B — ネットワーク共有パス:
#     _LABAID_PATH = r"\\server\share\LabAid.exe"
#
#   パターン C — Web ブラウザで開く URL:
#     _LABAID_PATH = "http://192.168.x.x/labaid/"
#
#   空文字のままにしておくとデモメッセージが表示される。
# ─────────────────────────────────────────────────────────────────────────────
_LABAID_PATH = ""


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
        self._ui.data_update_requested.connect(self._on_data_update)
        self._ui.labaid_requested.connect(self._open_labaid)

    def load_task(self, task: dict, readonly: bool = False) -> None:
        self._task = task
        self._ui.set_readonly(readonly)

    def _on_done(self) -> None:
        self._task = self._task_service.save_result_entry(self._task["task_id"])
        self.go_next.emit()

    def _open_labaid(self) -> None:
        """Lab-Aid を起動する。_LABAID_PATH を変更するだけで動作を切り替えられる。"""
        path = _LABAID_PATH.strip()
        if not path:
            QMessageBox.information(self, "Lab-Aid", "Lab-Aidを起動します（デモ）")
            return
        try:
            if path.startswith("http://") or path.startswith("https://"):
                webbrowser.open(path)
            else:
                subprocess.Popen([path])
        except Exception as e:
            QMessageBox.warning(self, "Lab-Aid 起動エラー", str(e))

    def _on_data_update(self) -> None:
        """「データ更新」ボタン押下時: データ更新・正規化を実行する。"""
        _run_data_update()
