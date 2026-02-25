from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QFrame,
    QAbstractItemView, QStackedWidget, QComboBox, QMessageBox,
)
from PySide6.QtCore import Signal, Qt
from PySide6.QtGui import QColor, QFont

from app.data import task_store
from app.config import CURRENT_USER, STATE_LABELS, STATUS_LABELS, STATE_ORDER
from app.states.task_setup import TaskSetupState
from app.states.analysis_targets import AnalysisTargetsState
from app.states.analysis import AnalysisState
from app.states.result_entry import ResultEntryState
from app.states.result_verification import ResultVerificationState
from app.states.submission import SubmissionState
from app.states.completed import CompletedState


# State index in the stacked widget (0 = list, 1..7 = states)
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
    navigate_home = Signal()

    def __init__(self, data_loader, parent=None):
        super().__init__(parent)
        self.data_loader = data_loader
        self._current_task: dict | None = None
        self._setup_ui()

    def _setup_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # Breadcrumb bar for state pages
        self.breadcrumb_bar = QFrame()
        self.breadcrumb_bar.setFixedHeight(36)
        self.breadcrumb_bar.setStyleSheet("""
            QFrame { background:#f1f5f9; border-bottom:1px solid #e2e8f0; }
        """)
        bc_layout = QHBoxLayout(self.breadcrumb_bar)
        bc_layout.setContentsMargins(24, 0, 24, 0)
        bc_layout.setSpacing(4)
        self._bc_labels: list[QLabel] = []
        for i, s in enumerate(STATE_ORDER):
            if i > 0:
                sep = QLabel("›")
                sep.setStyleSheet("color:#94a3b8; font-size:12px;")
                bc_layout.addWidget(sep)
            lbl = QLabel(STATE_LABELS.get(s, s))
            lbl.setStyleSheet("color:#94a3b8; font-size:12px;")
            bc_layout.addWidget(lbl)
            self._bc_labels.append(lbl)
        bc_layout.addStretch()
        self.breadcrumb_bar.setVisible(False)
        root.addWidget(self.breadcrumb_bar)

        self.stack = QStackedWidget()
        root.addWidget(self.stack)

        # 0: Task list
        self.stack.addWidget(self._build_list_widget())

        # 1: task_setup
        self.setup_state = TaskSetupState(self.data_loader)
        self.setup_state.submitted.connect(self._on_setup_submitted)
        self.setup_state.cancelled.connect(self.show_list)
        self.stack.addWidget(self.setup_state)

        # 2: analysis_targets
        self.targets_state = AnalysisTargetsState(self.data_loader)
        self.targets_state.go_next.connect(lambda: self._go_to_state("analysis"))
        self.targets_state.go_back.connect(lambda: self._go_to_state("task_setup"))
        self.stack.addWidget(self.targets_state)

        # 3: analysis
        self.analysis_state = AnalysisState(self.data_loader)
        self.analysis_state.go_next.connect(lambda: self._go_to_state("result_entry"))
        self.analysis_state.go_back.connect(lambda: self._go_to_state("analysis_targets"))
        self.stack.addWidget(self.analysis_state)

        # 4: result_entry
        self.entry_state = ResultEntryState(self.data_loader)
        self.entry_state.go_next.connect(lambda: self._go_to_state("result_verification"))
        self.entry_state.go_back.connect(lambda: self._go_to_state("analysis"))
        self.stack.addWidget(self.entry_state)

        # 5: result_verification
        self.verify_state = ResultVerificationState(self.data_loader)
        self.verify_state.go_next.connect(lambda: self._go_to_state("submission"))
        self.verify_state.go_back.connect(lambda: self._go_to_state("result_entry"))
        self.stack.addWidget(self.verify_state)

        # 6: submission
        self.submission_state = SubmissionState(self.data_loader)
        self.submission_state.go_next.connect(lambda: self._go_to_state("completed"))
        self.submission_state.go_back.connect(lambda: self._go_to_state("result_verification"))
        self.stack.addWidget(self.submission_state)

        # 7: completed
        self.completed_state = CompletedState()
        self.completed_state.go_list.connect(self.show_list)
        self.stack.addWidget(self.completed_state)

    # ── List widget ───────────────────────────────────────────────────────────

    def _build_list_widget(self) -> QWidget:
        w = QWidget()
        root = QVBoxLayout(w)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # Header
        header = QFrame()
        header.setFixedHeight(56)
        header.setStyleSheet("background:#f8fafc; border-bottom:1px solid #e2e8f0;")
        hl = QHBoxLayout(header)
        hl.setContentsMargins(24, 0, 24, 0)
        title = QLabel("タスク一覧")
        title.setStyleSheet("font-size:18px; font-weight:bold; color:#1e293b;")
        hl.addWidget(title)
        hl.addStretch()
        new_btn = QPushButton("+ 新規起票")
        new_btn.setStyleSheet("""
            QPushButton { background:#2563eb; color:white; border:none;
                          padding:8px 20px; border-radius:6px; font-size:13px; font-weight:bold; }
            QPushButton:hover { background:#1d4ed8; }
        """)
        new_btn.clicked.connect(self.start_new_task)
        hl.addWidget(new_btn)
        root.addWidget(header)

        # Filter bar
        filter_bar = QFrame()
        filter_bar.setStyleSheet("background:#f8fafc; border-bottom:1px solid #e2e8f0;")
        fl = QHBoxLayout(filter_bar)
        fl.setContentsMargins(24, 8, 24, 8)
        fl.addWidget(QLabel("フィルタ:"))
        self.filter_combo = QComboBox()
        self.filter_combo.addItems(["全件", "進行中", "回覧中", "終了", CURRENT_USER])
        self.filter_combo.setStyleSheet("""
            QComboBox { border:1px solid #d1d5db; border-radius:5px;
                        padding:4px 10px; min-width:140px; background:white; color:#1e293b; }
            QComboBox QAbstractItemView { color:#1e293b; background:white;
                selection-background-color:#2563eb; selection-color:white; }
        """)
        self.filter_combo.currentTextChanged.connect(self._apply_filter)
        fl.addWidget(self.filter_combo)
        fl.addStretch()
        self.count_lbl = QLabel()
        self.count_lbl.setStyleSheet("color:#6b7280; font-size:12px;")
        fl.addWidget(self.count_lbl)
        root.addWidget(filter_bar)

        # Table
        headers = ["タスク名", "ホルダグループ", "JOB番号", "ステータス", "担当者", "最終更新", "Action"]
        self.task_table = QTableWidget(0, len(headers))
        self.task_table.setHorizontalHeaderLabels(headers)
        self.task_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.task_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.task_table.setAlternatingRowColors(True)
        self.task_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.task_table.horizontalHeader().setSectionResizeMode(6, QHeaderView.ResizeMode.Fixed)
        self.task_table.setColumnWidth(6, 80)
        self.task_table.setStyleSheet("""
            QTableWidget { border:none; }
            QHeaderView::section { background:#f8fafc; font-weight:bold; color:#374151;
                                    padding:8px; border:none; border-bottom:1px solid #e2e8f0; }
        """)
        self.task_table.verticalHeader().setVisible(False)
        self.task_table.doubleClicked.connect(self._on_row_double_click)
        root.addWidget(self.task_table)

        return w

    # ── Public API ────────────────────────────────────────────────────────────

    def show_list(self):
        self._current_task = None
        self.breadcrumb_bar.setVisible(False)
        self.stack.setCurrentIndex(_IDX_LIST)
        self._refresh_list()

    def start_new_task(self):
        self._current_task = None
        self.setup_state.open_new()
        self.stack.setCurrentIndex(_STATE_IDX["task_setup"])

    def resume_task(self, task_id: str):
        task = task_store.get_task(task_id)
        if not task:
            QMessageBox.critical(self, "エラー", f"タスク {task_id} が見つかりません。")
            self.show_list()
            return
        self._current_task = task
        state = task.get("current_state", "analysis_targets")
        self._navigate_to_state(state, task)

    # ── Internal ──────────────────────────────────────────────────────────────

    def _refresh_list(self):
        all_tasks = task_store.load_tasks()
        self._all_tasks = all_tasks[:100]  # max 100
        self._apply_filter(self.filter_combo.currentText())

    def _apply_filter(self, filter_text: str):
        tasks = getattr(self, "_all_tasks", [])
        if filter_text == "進行中":
            tasks = [t for t in tasks if t.get("status") == "進行中"]
        elif filter_text == "回覧中":
            tasks = [t for t in tasks if t.get("status") == "回覧中"]
        elif filter_text == "終了":
            tasks = [t for t in tasks if t.get("status") == "終了"]
        elif filter_text == CURRENT_USER:
            tasks = [t for t in tasks if t.get("assigned_to") == CURRENT_USER]

        self._fill_table(tasks)
        self.count_lbl.setText(f"{len(tasks)} 件")

    def _fill_table(self, tasks: list[dict]):
        self.task_table.setRowCount(0)
        for t in tasks:
            row = self.task_table.rowCount()
            self.task_table.insertRow(row)
            state = t.get("current_state", "")
            state_label = STATE_LABELS.get(state, state)
            status = t.get("status", "")
            job_str = ", ".join(t.get("job_numbers", []))
            updated = t.get("updated_at", "")[:16].replace("T", " ")

            vals = [
                t.get("task_name", ""),
                t.get("holder_group_name", ""),
                job_str,
                f"{status}  [{state_label}]",
                t.get("assigned_to", ""),
                updated,
            ]
            for col, v in enumerate(vals):
                item = QTableWidgetItem(str(v))
                item.setData(Qt.ItemDataRole.UserRole, t["task_id"])
                if col == 3:
                    color = STATUS_LABELS.get(status, "#6b7280")
                    item.setForeground(QColor(color))
                    item.setFont(QFont("", -1, QFont.Weight.Bold))
                self.task_table.setItem(row, col, item)

            # Action button
            act_btn = QPushButton("開く")
            act_btn.setStyleSheet("""
                QPushButton { background:#eff6ff; color:#2563eb; border:1px solid #bfdbfe;
                              padding:4px 10px; border-radius:4px; font-size:12px; }
                QPushButton:hover { background:#dbeafe; }
            """)
            task_id = t["task_id"]
            act_btn.clicked.connect(lambda _=False, tid=task_id: self.resume_task(tid))
            self.task_table.setCellWidget(row, 6, act_btn)

    def _on_row_double_click(self, index):
        item = self.task_table.item(index.row(), 0)
        if item:
            task_id = item.data(Qt.ItemDataRole.UserRole)
            if task_id:
                self.resume_task(task_id)

    def _on_setup_submitted(self, task: dict):
        self._current_task = task
        self._navigate_to_state("analysis_targets", task)

    def _go_to_state(self, state: str):
        task = task_store.get_task(self._current_task["task_id"]) if self._current_task else None
        if not task:
            self.show_list()
            return
        self._current_task = task
        self._navigate_to_state(state, task)

    def _navigate_to_state(self, state: str, task: dict):
        """Navigate to a specific state widget and load the task."""
        readonly = task.get("status") == "終了"
        if state == "task_setup":
            sd_done = task.get("state_data", {}).get("task_setup", {}).get("completed", False)
            if sd_done:
                self.setup_state.open_existing(task, readonly=readonly)
            else:
                self.setup_state.open_new()
        elif state == "analysis_targets":
            self.targets_state.load_task(task, readonly=readonly)
        elif state == "analysis":
            self.analysis_state.load_task(task, readonly=readonly)
        elif state == "result_entry":
            self.entry_state.load_task(task, readonly=readonly)
        elif state == "result_verification":
            self.verify_state.load_task(task, readonly=readonly)
        elif state == "submission":
            self.submission_state.load_task(task, readonly=readonly)
        elif state == "completed":
            self.completed_state.load_task(task)
        else:
            self.show_list()
            return

        idx = _STATE_IDX.get(state)
        if idx is not None:
            self.stack.setCurrentIndex(idx)
            # Update breadcrumb
            self.breadcrumb_bar.setVisible(True)
            for i, s in enumerate(STATE_ORDER):
                lbl = self._bc_labels[i]
                if s == state:
                    lbl.setStyleSheet("color:#2563eb; font-size:12px; font-weight:bold;")
                elif STATE_ORDER.index(s) < STATE_ORDER.index(state):
                    lbl.setStyleSheet("color:#64748b; font-size:12px;")
                else:
                    lbl.setStyleSheet("color:#cbd5e1; font-size:12px;")
