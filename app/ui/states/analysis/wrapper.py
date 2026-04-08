"""AnalysisState — 分析準備ステートのUIラッパー。"""
from __future__ import annotations

from PySide6.QtWidgets import QWidget, QVBoxLayout
from PySide6.QtCore import Signal

import app.config as _cfg
from app.services.task_service import TaskService
from app.services.data_service import DataService
from app.services.log_service import LogService
from .state import AnalysisUI


class AnalysisState(QWidget):
    go_next = Signal()
    go_back = Signal()

    def __init__(
        self,
        task_service: TaskService,
        data_service: DataService,
        log_service: LogService | None = None,
        parent=None,
    ) -> None:
        super().__init__(parent)
        self._task_service = task_service
        self._data_service = data_service
        self._log_service = log_service or LogService()
        self._task: dict = {}

        self._ui = AnalysisUI()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self._ui)

        self._ui.finish_requested.connect(self._on_finish)
        self._ui.back_requested.connect(self.go_back)
        self._ui.reagent_changed.connect(self._on_reagent_changed)
        self._ui.equipment_changed.connect(self._on_equipment_changed)

    def load_task(self, task: dict, readonly: bool = False) -> None:
        self._task = task
        hg_code = task.get("holder_group_code", "")
        hg_name = task.get("holder_group_name", "")
        cfg = self._data_service.get_analysis_config(hg_code)
        self._ui.set_config(cfg)
        self._ui.set_log_context(hg_code, hg_name)
        self._load_logs(hg_code)

        sd = task.get("state_data", {}).get("analysis", {})
        pre_saved = sd.get("pre_checks", [False] * len(self._ui._pre_checks))
        post_saved = sd.get("post_checks", [False] * len(self._ui._post_checks))
        self._ui.restore_checks(pre_saved, post_saved, readonly)

    def set_state_done(self, done: bool) -> None:
        if done:
            self._ui.finish_btn.setEnabled(False)
            self._ui.finish_btn.setText("完了済み")
        else:
            self._ui.finish_btn.setText("完了")

    # ── Internal ──────────────────────────────────────────────────────────────

    def _load_logs(self, hg_code: str) -> None:
        all_reagents = self._log_service.get_all_reagents()
        reagents = [r for r in all_reagents if r.get("holder_group_code") == hg_code]
        self._ui.set_reagents(reagents)

        all_equipment = self._log_service.get_all_equipment()
        equipment = [e for e in all_equipment if e.get("holder_group_code") == hg_code]
        self._ui.set_equipment(equipment)

    def _on_reagent_changed(self, action: str, data: dict) -> None:
        if action == "create":
            self._log_service.create_reagent(
                name=data["name"],
                shelf_life_days=data["shelf_life_days"],
                holder_group_code=data["holder_group_code"],
                holder_group_name=data["holder_group_name"],
                created_by=_cfg.CURRENT_USER,
                preparation_date=data.get("preparation_date", ""),
            )
        elif action == "update":
            self._log_service.update_reagent(
                data["id"],
                updated_by=_cfg.CURRENT_USER,
                name=data["name"],
                shelf_life_days=data["shelf_life_days"],
                preparation_date=data.get("preparation_date", ""),
            )
        hg_code = self._task.get("holder_group_code", "")
        self._load_logs(hg_code)

    def _on_equipment_changed(self, action: str, data: dict) -> None:
        if action == "create":
            self._log_service.create_equipment(
                name=data["name"],
                link=data.get("link", ""),
                holder_group_code=data["holder_group_code"],
                holder_group_name=data["holder_group_name"],
                created_by=_cfg.CURRENT_USER,
            )
        elif action == "update":
            self._log_service.update_equipment(
                data["id"],
                name=data["name"],
                link=data.get("link", ""),
            )
        hg_code = self._task.get("holder_group_code", "")
        self._load_logs(hg_code)

    def _on_finish(self, pre_checks: list, post_checks: list) -> None:
        self._task = self._task_service.save_analysis(
            self._task["task_id"], pre_checks, post_checks
        )
        self.go_next.emit()
