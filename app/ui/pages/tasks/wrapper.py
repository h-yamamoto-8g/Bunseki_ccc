"""TasksPage — タスクページのUIラッパー。"""
from __future__ import annotations

from PySide6.QtWidgets import QWidget, QVBoxLayout, QMessageBox, QDialog
from PySide6.QtCore import Signal

import app.config as _cfg
from app.config import STATE_ORDER
from app.services.task_service import TaskService
from app.services.data_service import DataService
from app.ui.states.task_setup import TaskSetupState
from app.ui.states.analysis_targets import AnalysisTargetsState
from app.ui.states.analysis import AnalysisState
from app.ui.states.result_entry import ResultEntryState
from app.ui.states.result_verification import ResultVerificationState
from app.ui.states.submission import SubmissionState
from app.ui.states.completed import CompletedState
from .page import TasksPageUI

_IDX_LIST = 0
_STATE_IDX = {
    "task_setup": 1,
    "analysis_targets": 2,
    "analysis": 3,
    "result_entry": 4,
    "result_verification": 5,
    "submission": 6,
    "completed": 7,
}


class TasksPage(QWidget):
    navigate_home         = Signal()
    task_context_changed  = Signal(str, str, str)  # (task_name, state_id, current_state)
    task_context_cleared  = Signal()
    step_edited           = Signal(str)         # (state_id) 編集済みになった step
    loading_changed       = Signal(bool, str)   # (is_loading, message)
    handover_available    = Signal(bool)        # 引き継ぎボタンの有効/無効

    def __init__(
        self,
        task_service: TaskService,
        data_service: DataService,
        job_service=None,
        parent=None,
    ) -> None:
        super().__init__(parent)
        self._task_service = task_service
        self._data_service = data_service
        self._job_service = job_service
        self._current_task: dict | None = None
        self._current_view_state: str = ""
        self._all_tasks_full: list[dict] = []
        self._display_limit: int = 100

        self._ui = TasksPageUI()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self._ui)

        self._setup_states()
        self._connect_signals()

    def _setup_states(self) -> None:
        ts = self._task_service
        ds = self._data_service

        self.setup_state = TaskSetupState(ts, ds, job_service=self._job_service)
        self.targets_state = AnalysisTargetsState(ts, ds)
        self.analysis_state = AnalysisState(ts, ds)
        self.entry_state = ResultEntryState(ts, ds)
        self.verify_state = ResultVerificationState(ts, ds)
        self.submission_state = SubmissionState(ts, ds)
        self.completed_state = CompletedState()

        for state in [
            self.setup_state,
            self.targets_state,
            self.analysis_state,
            self.entry_state,
            self.verify_state,
            self.submission_state,
            self.completed_state,
        ]:
            self._ui.stack.addWidget(state)

    def _connect_signals(self) -> None:
        ui = self._ui
        ui.task_open_requested.connect(self.resume_task)
        ui.new_task_requested.connect(self.start_new_task)
        ui.filter_changed.connect(self._apply_filter)
        ui.back_to_list_requested.connect(self.show_list)
        ui.handover_requested.connect(self._on_handover)
        ui.task_delete_requested.connect(self._on_task_deleted)
        ui.load_more_requested.connect(self._on_load_more)

        ui.view_prev_requested.connect(self._on_view_prev)
        ui.view_next_requested.connect(self._on_view_next)

        self.setup_state.submitted.connect(self._on_setup_submitted)
        self.setup_state.cancelled.connect(self.show_list)
        self.setup_state.go_next.connect(lambda: self._go_to_state("analysis_targets"))

        self.targets_state.go_next.connect(lambda: self._go_to_state("analysis"))
        self.targets_state.go_back.connect(lambda: self._go_to_state("task_setup"))
        self.targets_state.step_edited.connect(self.step_edited)
        self.targets_state.loading_changed.connect(self.loading_changed)

        self.analysis_state.go_next.connect(lambda: self._go_to_state("result_entry"))
        self.analysis_state.go_back.connect(lambda: self._go_to_state("analysis_targets"))

        self.entry_state.go_next.connect(lambda: self._go_to_state("result_verification"))
        self.entry_state.go_back.connect(lambda: self._go_to_state("analysis"))

        self.verify_state.go_next.connect(lambda: self._go_to_state("submission"))
        self.verify_state.go_back.connect(lambda: self._go_to_state("result_entry"))
        self.verify_state.loading_changed.connect(self.loading_changed)

        self.submission_state.go_next.connect(lambda: self._go_to_state("completed"))
        self.submission_state.go_back.connect(lambda: self._go_to_state("result_verification"))
        self.submission_state.loading_changed.connect(self.loading_changed)

        self.completed_state.go_list.connect(self.show_list)

    # ── Public API ────────────────────────────────────────────────────────────

    def request_handover(self) -> None:
        """共通ヘッダーの「引き継ぎ」ボタンから呼ばれる。"""
        self._on_handover()

    def show_list(self) -> None:
        self._current_task = None
        self._current_view_state = ""
        self._ui.show_list_view()
        self._refresh_list()
        self.task_context_cleared.emit()

    def start_new_task(self) -> None:
        self._current_task = None
        self.setup_state.open_new()
        self._ui.show_list_view()
        self._ui.stack.setCurrentIndex(_STATE_IDX["task_setup"])
        self.task_context_changed.emit("新規タスク", "task_setup", "task_setup")

    def resume_task(self, task_id: str) -> None:
        task = self._task_service.get_task(task_id)
        if not task:
            QMessageBox.critical(self, "エラー", f"タスク {task_id} が見つかりません。")
            self.show_list()
            return
        self._current_task = task
        state = task.get("current_state", "analysis_targets")
        self._navigate_to_state(state, task)

    def navigate_to_state(self, state_id: str) -> None:
        if self._current_task:
            self._navigate_to_state(state_id, self._current_task)
        else:
            # タスク未選択時はタスク一覧を表示してリストを読み込む
            self.show_list()

    # ── Internal ──────────────────────────────────────────────────────────────

    def _refresh_list(self) -> None:
        all_tasks = self._task_service.get_all_tasks()
        self._all_tasks_full = all_tasks
        self._display_limit = 100
        self._update_list_display()

    def _update_list_display(self) -> None:
        self._all_tasks = self._all_tasks_full[: self._display_limit]
        current_filter = self._ui.filter_tabs._active if hasattr(self._ui.filter_tabs, "_active") else "全件"
        self._apply_filter(current_filter)
        # さらに読み込むボタンの表示切替
        has_more = len(self._all_tasks_full) > self._display_limit
        self._ui.set_load_more_visible(has_more)

    def _apply_filter(self, filter_key: str) -> None:
        tasks = getattr(self, "_all_tasks", [])
        filtered = self._task_service.filter_tasks(tasks, filter_key)
        self._ui.fill_table(filtered)

    def _on_handover(self) -> None:
        if not self._current_task:
            return
        task = self._current_task

        # 終了済みタスクは変更不可
        if self._task_service.is_task_readonly(task):
            QMessageBox.information(self, "引き継ぎ不可", "終了済みのタスクは引き継げません。")
            return

        # 自分のタスクは引き継げない（ボタンが無効のため通常到達しない）
        if task.get("assigned_to", "") == _cfg.CURRENT_USER:
            return

        # 確認ダイアログ → 自分が引き継ぐ
        dlg = self._ui.get_takeover_dialog(task)
        if dlg.exec() != QDialog.DialogCode.Accepted:
            return
        updated = self._task_service.handover_task(
            task["task_id"],
            new_assignee=_cfg.CURRENT_USER,
            operated_by=_cfg.CURRENT_USER,
        )
        if updated:
            self._current_task = updated
            self.task_context_changed.emit(
                updated.get("task_name", ""),
                updated.get("current_state", ""),
                updated.get("current_state", ""),
            )
        # 引き継ぎ後は自分のタスクになるのでボタンを無効化
        self.handover_available.emit(False)
        QMessageBox.information(
            self,
            "引き継ぎ完了",
            f"タスクを引き継ぎました。\n担当者が「{_cfg.CURRENT_USER}」に変更されました。",
        )

    def _on_task_deleted(self, task_id: str) -> None:
        task = self._task_service.get_task(task_id)
        if task and task.get("assigned_to", "") != _cfg.CURRENT_USER:
            QMessageBox.warning(
                self, "操作不可",
                "自分が担当していないタスクは削除できません。",
            )
            return
        self._task_service.delete_task(task_id)
        self._refresh_list()

    def _on_load_more(self) -> None:
        self._display_limit += 100
        self._update_list_display()

    def _on_setup_submitted(self, task: dict) -> None:
        self._current_task = task
        self._navigate_to_state("analysis_targets", task)

    def _go_to_state(self, state: str) -> None:
        if not self._current_task:
            self.show_list()
            return
        task = self._task_service.get_task(self._current_task["task_id"])
        if not task:
            self.show_list()
            return
        self._current_task = task
        self._navigate_to_state(state, task)

    def _is_future_state(self, target: str, task: dict) -> bool:
        """target がタスクの current_state より先のステートか判定する。"""
        current = task.get("current_state", "")
        try:
            return STATE_ORDER.index(target) > STATE_ORDER.index(current)
        except ValueError:
            return False

    def _is_past_state(self, target: str, task: dict) -> bool:
        """target がタスクの current_state より前（完了済み）のステートか判定する。"""
        current = task.get("current_state", "")
        try:
            return STATE_ORDER.index(target) < STATE_ORDER.index(current)
        except ValueError:
            return False

    def _navigate_to_state(self, state: str, task: dict) -> None:
        readonly = self._task_service.is_task_readonly(task)
        # 自分のタスクでなければ閲覧専用
        if not readonly and task.get("assigned_to", "") != _cfg.CURRENT_USER:
            readonly = True
        # current_state より先へジャンプした場合はプレビュー（操作不可）
        preview = not readonly and self._is_future_state(state, task)
        if preview:
            readonly = True
        # このステートが既に完了済みか
        state_done = self._is_past_state(state, task)

        if state == "task_setup":
            if self._task_service.is_setup_done(task):
                self.setup_state.open_existing(task, readonly=readonly)
            else:
                self.setup_state.open_new()
            self.setup_state.set_state_done(state_done)
        elif state == "analysis_targets":
            self.targets_state.load_task(task, readonly=readonly)
            self.targets_state.set_state_done(state_done)
        elif state == "analysis":
            self.analysis_state.load_task(task, readonly=readonly)
            self.analysis_state.set_state_done(state_done)
        elif state == "result_entry":
            self.entry_state.load_task(task, readonly=readonly)
            self.entry_state.set_state_done(state_done)
        elif state == "result_verification":
            self.verify_state.load_task(task, readonly=readonly)
            self.verify_state.set_state_done(state_done)
        elif state == "submission":
            self.submission_state.load_task(task, readonly=readonly)
        elif state == "completed":
            self.completed_state.load_task(task, preview=preview)
        else:
            self.show_list()
            return

        idx = _STATE_IDX.get(state)
        if idx is not None:
            self._ui.stack.setCurrentIndex(idx)
            self._ui.show_detail_view(task, state)
            self._current_view_state = state
            self.task_context_changed.emit(
                task.get("task_name", ""),
                state,
                task.get("current_state", state),
            )
            # 引き継ぎボタンの有効/無効: 終了済み or 自分のタスクは無効
            can_takeover = (
                not readonly
                and task.get("assigned_to", "") != _cfg.CURRENT_USER
            )
            self.handover_available.emit(can_takeover)
            # 閲覧用の左右ナビゲーション更新
            self._update_view_nav(state, task, readonly)

    # ── 閲覧用ナビゲーション ──────────────────────────────────────────────────

    def _get_viewable_states(self, task: dict) -> list[str]:
        """閲覧可能なステートの一覧を返す（全ステート）。"""
        return list(STATE_ORDER)

    def _update_view_nav(self, state: str, task: dict, readonly: bool) -> None:
        """閲覧用の左右ナビゲーションボタンの表示状態を更新する。"""
        viewable = self._get_viewable_states(task)
        if len(viewable) <= 1:
            self._ui.set_view_nav_visible(False)
            return
        self._ui.set_view_nav_visible(True)
        try:
            idx = viewable.index(state)
        except ValueError:
            self._ui.set_view_nav_enabled(False, False)
            return
        self._ui.set_view_nav_enabled(idx > 0, idx < len(viewable) - 1)

    def _on_view_prev(self) -> None:
        """閲覧用: 前のステートを表示する（ステート進行なし）。"""
        if not self._current_task:
            return
        task = self._task_service.get_task(self._current_task["task_id"])
        if not task:
            return
        self._current_task = task
        viewable = self._get_viewable_states(task)
        try:
            idx = viewable.index(self._current_view_state)
        except ValueError:
            return
        if idx > 0:
            self._navigate_to_state(viewable[idx - 1], task)

    def _on_view_next(self) -> None:
        """閲覧用: 次のステートを表示する（ステート進行なし）。"""
        if not self._current_task:
            return
        task = self._task_service.get_task(self._current_task["task_id"])
        if not task:
            return
        self._current_task = task
        viewable = self._get_viewable_states(task)
        try:
            idx = viewable.index(self._current_view_state)
        except ValueError:
            return
        if idx < len(viewable) - 1:
            self._navigate_to_state(viewable[idx + 1], task)
