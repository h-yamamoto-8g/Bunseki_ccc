"""ResultVerificationState — データ確認ステートのUIラッパー。"""
from __future__ import annotations

from PySide6.QtWidgets import QWidget, QVBoxLayout, QApplication
from PySide6.QtCore import Signal

from app.services.task_service import TaskService
from app.services.data_service import DataService
from app.ui.dialogs.loading_dialog import LoadingOverlay
from .state import ResultVerificationUI, TrendDialog


class ResultVerificationState(QWidget):
    go_next = Signal()
    go_back = Signal()
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

        self._ui = ResultVerificationUI()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self._ui)

        self._ui.next_requested.connect(self._on_next)
        self._ui.back_requested.connect(self.go_back)
        self._ui.graph_requested.connect(self._on_graph)

    def load_task(self, task: dict, readonly: bool = False) -> None:
        self._task = task
        hg_code = task.get("holder_group_code", "")
        jobs = task.get("job_numbers", [])
        vsset_codes = (
            task.get("state_data", {})
            .get("analysis_targets", {})
            .get("valid_sample_set_codes", [])
        )

        # HG設定からチェックリストを取得して UI に反映
        cfg = self._data_service.get_analysis_config(hg_code)
        verify_items = cfg.get("verify_checklist", [])
        if verify_items:
            self._ui.set_check_items(verify_items)

        result: dict = {}
        LoadingOverlay.run_with_overlay(
            lambda: result.update(df=self._data_service.get_result_data(hg_code, jobs, vsset_codes)),
            msg="データ確認テーブルを構築しています...",
        )
        df = result.get("df")
        if df is None:
            import pandas as pd
            df = pd.DataFrame()
        self._ui.build_tabs(
            df,
            hg_code,
            self._data_service.calculate_anomaly,
            self._data_service.extract_numeric,
        )

        sd = task.get("state_data", {}).get("result_verification", {})
        saved = sd.get("checks", [False] * len(verify_items))
        self._ui.restore_checks(saved, readonly)

    def set_state_done(self, done: bool) -> None:
        """完了済みステートなら完了ボタンを無効化して「完了済み」にする。"""
        if done:
            self._ui.next_btn.setEnabled(False)
            self._ui.next_btn.setText("完了済み")
        else:
            self._ui.next_btn.setText("完了")

    def _on_next(self, checks: list) -> None:
        self._task = self._task_service.save_result_verification(
            self._task["task_id"], checks
        )
        self.go_next.emit()

    def _on_graph(
        self,
        hg_code: str,
        vsset: str,
        vtest: str,
        unit: str,
        test_name: str,
    ) -> None:
        result: dict = {}
        LoadingOverlay.run_with_overlay(
            lambda: result.update(
                data=self._data_service.get_trend_data(hg_code, vsset, vtest),
                bounds=self._data_service.get_anomaly_bounds(hg_code, vsset, vtest),
                spec=self._data_service.get_spec_limits(hg_code, vsset, vtest),
            ),
            msg="グラフを作成しています...",
        )
        data = result.get("data", [])
        bounds = result.get("bounds", {})
        spec = result.get("spec", {})
        dlg = TrendDialog(data, bounds, spec, unit, test_name, self)
        dlg.exec()
