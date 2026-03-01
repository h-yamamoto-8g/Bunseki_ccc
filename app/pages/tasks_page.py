from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QFrame,
    QAbstractItemView, QStackedWidget, QMessageBox,
    QDialog, QComboBox, QLineEdit,
)
from PySide6.QtCore import Signal, Qt
from PySide6.QtGui import QColor, QFont

from app.data import task_store
from app.config import CURRENT_USER, STATE_LABELS, STATUS_LABELS, STATE_ORDER

DEMO_USERS = ["デモユーザー", "山田 太郎", "鈴木 花子", "田中 一郎"]
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

# Design tokens
_BG   = "#0f1117"
_BG2  = "#161b27"
_BG3  = "#1e2535"
_BG4  = "#252d3e"
_BORDER  = "#2a3349"
_BORDER2 = "#334166"
_TEXT    = "#e8eaf0"
_TEXT2   = "#8b93a8"
_TEXT3   = "#5a6278"
_ACCENT  = "#4a8cff"
_SUCCESS = "#2ecc8a"
_WARN    = "#f5a623"
_DANGER  = "#e85454"


# ── Helper widgets ─────────────────────────────────────────────────────────────

class _FilterTabs(QFrame):
    """Segmented tab control matching the HTML .filter-tabs style."""
    tab_changed = Signal(str)

    def __init__(self, tabs: list[str], parent=None):
        super().__init__(parent)
        self.setObjectName("FilterTabs")
        self.setStyleSheet(f"""
            QFrame#FilterTabs {{
                background: {_BG3};
                border-radius: 8px;
                border: none;
            }}
        """)
        self._btns: dict[str, QPushButton] = {}
        layout = QHBoxLayout(self)
        layout.setContentsMargins(3, 3, 3, 3)
        layout.setSpacing(2)
        for tab in tabs:
            btn = QPushButton(tab)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setStyleSheet(self._inactive_style())
            btn.clicked.connect(lambda _, t=tab: self._select(t))
            layout.addWidget(btn)
            self._btns[tab] = btn
        if tabs:
            self._select(tabs[0])

    def _inactive_style(self) -> str:
        return f"""
            QPushButton {{
                background: transparent; color: {_TEXT2};
                border: none; padding: 4px 12px; border-radius: 5px;
                font-size: 12px; font-weight: 500;
            }}
            QPushButton:hover {{ background: {_BG4}; color: {_TEXT}; }}
        """

    def _active_style(self) -> str:
        return f"""
            QPushButton {{
                background: {_BG2}; color: {_ACCENT};
                border: none; padding: 4px 12px; border-radius: 5px;
                font-size: 12px; font-weight: 600;
            }}
        """

    def _select(self, tab: str):
        self._active = tab
        for t, btn in self._btns.items():
            btn.setStyleSheet(self._active_style() if t == tab else self._inactive_style())
        self.tab_changed.emit(tab)


class _StateBar(QFrame):
    """Horizontal step-progress bar with numbered circles and connectors."""
    state_clicked = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._circles: list[QLabel] = []
        self._labels: list[QLabel] = []
        self._connectors: list[QFrame] = []
        self.setObjectName("StateBar")
        self.setStyleSheet(f"""
            QFrame#StateBar {{
                background: {_BG2};
                border: 1px solid {_BORDER};
                border-radius: 12px;
            }}
        """)
        self._build_ui()

    def _build_ui(self):
        hl = QHBoxLayout(self)
        hl.setContentsMargins(16, 14, 16, 14)
        hl.setSpacing(0)
        hl.setAlignment(Qt.AlignmentFlag.AlignHCenter)

        for i, state in enumerate(STATE_ORDER):
            if i > 0:
                # Connector with bottom margin so it vertically aligns with circle center
                cw = QWidget()
                cw.setStyleSheet("background: transparent;")
                cw_l = QVBoxLayout(cw)
                cw_l.setContentsMargins(0, 0, 0, 18)
                cw_l.setSpacing(0)
                conn = QFrame()
                conn.setFixedWidth(28)
                conn.setFixedHeight(2)
                conn.setStyleSheet(f"QFrame {{ background: {_BORDER2}; border: none; }}")
                cw_l.addWidget(conn)
                hl.addWidget(cw)
                self._connectors.append(conn)

            # Step container
            step = QWidget()
            step.setCursor(Qt.CursorShape.PointingHandCursor)
            step.setStyleSheet("background: transparent;")
            step.mousePressEvent = lambda e, s=state: self.state_clicked.emit(s)

            vl = QVBoxLayout(step)
            vl.setContentsMargins(2, 0, 2, 0)
            vl.setSpacing(4)
            vl.setAlignment(Qt.AlignmentFlag.AlignHCenter)

            circle = QLabel(str(i + 1))
            circle.setFixedSize(30, 30)
            circle.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self._apply_circle(circle, "future", i + 1)
            vl.addWidget(circle, alignment=Qt.AlignmentFlag.AlignHCenter)

            label = QLabel(STATE_LABELS.get(state, state))
            label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            label.setStyleSheet(f"font-size: 10px; color: {_TEXT3}; background: transparent;")
            vl.addWidget(label)

            hl.addWidget(step)
            self._circles.append(circle)
            self._labels.append(label)

    def _apply_circle(self, circle: QLabel, mode: str, num: int):
        if mode == "done":
            circle.setText("✓")
            circle.setStyleSheet(f"""
                QLabel {{
                    border: 2px solid {_SUCCESS}; border-radius: 15px;
                    font-size: 11px; color: {_SUCCESS};
                    background: rgba(46,204,138,0.1);
                }}
            """)
        elif mode == "active":
            circle.setText(str(num))
            circle.setStyleSheet(f"""
                QLabel {{
                    border: 2px solid {_ACCENT}; border-radius: 15px;
                    font-size: 11px; color: white;
                    background: {_ACCENT};
                }}
            """)
        else:
            circle.setText(str(num))
            circle.setStyleSheet(f"""
                QLabel {{
                    border: 2px solid {_BORDER2}; border-radius: 15px;
                    font-size: 11px; color: {_TEXT3};
                    background: {_BG3};
                }}
            """)

    def set_active_state(self, active_state: str):
        try:
            active_idx = STATE_ORDER.index(active_state)
        except ValueError:
            return
        for i, (circle, label) in enumerate(zip(self._circles, self._labels)):
            if i < active_idx:
                self._apply_circle(circle, "done", i + 1)
                label.setStyleSheet(f"font-size: 10px; color: {_SUCCESS}; background: transparent;")
            elif i == active_idx:
                self._apply_circle(circle, "active", i + 1)
                label.setStyleSheet(
                    f"font-size: 10px; color: {_ACCENT}; font-weight: 600; background: transparent;"
                )
            else:
                self._apply_circle(circle, "future", i + 1)
                label.setStyleSheet(f"font-size: 10px; color: {_TEXT3}; background: transparent;")
        for i, conn in enumerate(self._connectors):
            if i < active_idx:
                conn.setStyleSheet(f"QFrame {{ background: {_SUCCESS}; border: none; }}")
            else:
                conn.setStyleSheet(f"QFrame {{ background: {_BORDER2}; border: none; }}")


class _HandoverDialog(QDialog):
    """担当者引き継ぎダイアログ。"""

    def __init__(self, task: dict, parent=None):
        super().__init__(parent)
        self._task = task
        self.new_assignee: str = ""
        self.setWindowTitle("担当者の引き継ぎ")
        self.setFixedWidth(420)
        self.setModal(True)
        self.setStyleSheet(f"""
            QDialog {{
                background: {_BG2};
            }}
            QLabel {{
                color: {_TEXT};
                background: transparent;
            }}
        """)
        self._build_ui()

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(24, 24, 24, 24)
        root.setSpacing(16)

        # ── ヘッダー
        title = QLabel("担当者の引き継ぎ")
        title.setStyleSheet(f"font-size: 15px; font-weight: 700; color: {_TEXT};")
        root.addWidget(title)

        div = QFrame()
        div.setFixedHeight(1)
        div.setStyleSheet(f"background: {_BORDER};")
        root.addWidget(div)

        # ── タスク情報
        info_frame = QFrame()
        info_frame.setStyleSheet(f"""
            QFrame {{
                background: {_BG3};
                border: 1px solid {_BORDER};
                border-radius: 8px;
            }}
        """)
        info_l = QVBoxLayout(info_frame)
        info_l.setContentsMargins(14, 12, 14, 12)
        info_l.setSpacing(6)

        task_name_lbl = QLabel(f"タスク: {self._task.get('task_name', '')}")
        task_name_lbl.setStyleSheet(f"font-size: 13px; font-weight: 600; color: {_TEXT};")
        info_l.addWidget(task_name_lbl)

        current_owner = self._task.get("assigned_to", "未割り当て")
        cur_lbl = QLabel(f"現在の担当者:  {current_owner}")
        cur_lbl.setStyleSheet(f"font-size: 12px; color: {_TEXT2};")
        info_l.addWidget(cur_lbl)
        root.addWidget(info_frame)

        # ── 引き継ぎ先選択
        sel_lbl = QLabel("引き継ぎ先")
        sel_lbl.setStyleSheet(
            f"font-size: 11px; font-weight: 600; color: {_TEXT2}; letter-spacing: 0.5px;"
        )
        root.addWidget(sel_lbl)

        self._combo = QComboBox()
        self._combo.setEditable(True)
        self._combo.setInsertPolicy(QComboBox.InsertPolicy.InsertAtTop)

        # 既存の担当者一覧を優先し、デモユーザーも追加
        known = list({CURRENT_USER} | set(DEMO_USERS))
        known.sort()
        for u in known:
            self._combo.addItem(u)
        # 既存の担当者を初期選択から外す（空欄スタート）
        self._combo.setCurrentText("")
        self._combo.setStyleSheet(f"""
            QComboBox {{
                background: {_BG3}; color: {_TEXT};
                border: 1px solid {_BORDER2}; border-radius: 6px;
                padding: 6px 10px; font-size: 13px; min-height: 32px;
            }}
            QComboBox:focus {{ border-color: {_ACCENT}; }}
            QComboBox QAbstractItemView {{
                background: {_BG3}; color: {_TEXT};
                selection-background-color: {_ACCENT};
            }}
        """)
        root.addWidget(self._combo)

        # 自分が引き継ぐ クイックボタン
        if self._task.get("assigned_to") != CURRENT_USER:
            takeover_btn = QPushButton(f"自分が引き継ぐ  ({CURRENT_USER})")
            takeover_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            takeover_btn.setStyleSheet(f"""
                QPushButton {{
                    background: rgba(74,140,255,0.12); color: {_ACCENT};
                    border: 1px solid rgba(74,140,255,0.4);
                    padding: 6px 14px; border-radius: 6px; font-size: 12px;
                }}
                QPushButton:hover {{ background: rgba(74,140,255,0.2); }}
            """)
            takeover_btn.clicked.connect(lambda: self._combo.setCurrentText(CURRENT_USER))
            root.addWidget(takeover_btn)

        # ── ボタン行
        div2 = QFrame()
        div2.setFixedHeight(1)
        div2.setStyleSheet(f"background: {_BORDER};")
        root.addWidget(div2)

        btn_row = QHBoxLayout()
        btn_row.setSpacing(8)
        btn_row.addStretch()

        cancel_btn = QPushButton("キャンセル")
        cancel_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        cancel_btn.setStyleSheet(f"""
            QPushButton {{
                background: {_BG4}; color: {_TEXT};
                border: 1px solid {_BORDER2};
                padding: 6px 16px; border-radius: 6px; font-size: 12px;
            }}
            QPushButton:hover {{ border-color: {_ACCENT}; color: {_ACCENT}; }}
        """)
        cancel_btn.clicked.connect(self.reject)
        btn_row.addWidget(cancel_btn)

        confirm_btn = QPushButton("引き継ぎを確定")
        confirm_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        confirm_btn.setStyleSheet(f"""
            QPushButton {{
                background: {_ACCENT}; color: white;
                border: none;
                padding: 6px 16px; border-radius: 6px; font-size: 12px; font-weight: 500;
            }}
            QPushButton:hover {{ background: #5a9dff; }}
        """)
        confirm_btn.clicked.connect(self._on_confirm)
        btn_row.addWidget(confirm_btn)

        root.addLayout(btn_row)

    def _on_confirm(self):
        name = self._combo.currentText().strip()
        if not name:
            QMessageBox.warning(self, "入力エラー", "引き継ぎ先を入力してください。")
            return
        if name == self._task.get("assigned_to"):
            QMessageBox.warning(self, "入力エラー", "現在の担当者と同じです。")
            return
        self.new_assignee = name
        self.accept()


class _TaskHeaderBar(QFrame):
    """Task detail header: [← 一覧へ] | [task name / status tag] | [owner + 引き継ぎ]."""
    back_clicked = Signal()
    handover_clicked = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("TaskHeaderBar")
        self.setStyleSheet(f"""
            QFrame#TaskHeaderBar {{
                background: {_BG2};
                border: 1px solid {_BORDER};
                border-radius: 8px;
            }}
        """)
        hl = QHBoxLayout(self)
        hl.setContentsMargins(10, 8, 10, 8)
        hl.setSpacing(12)

        # Back button
        back_btn = QPushButton("← 一覧へ")
        back_btn.setFixedHeight(28)
        back_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        back_btn.setStyleSheet(f"""
            QPushButton {{
                background: {_BG4}; color: {_TEXT}; border: 1px solid {_BORDER2};
                padding: 4px 10px; border-radius: 4px; font-size: 11px;
            }}
            QPushButton:hover {{ border-color: {_ACCENT}; color: {_ACCENT}; }}
        """)
        back_btn.clicked.connect(self.back_clicked)
        hl.addWidget(back_btn, stretch=0)

        # Center: task name + status tag
        center = QVBoxLayout()
        center.setSpacing(4)
        center.setAlignment(Qt.AlignmentFlag.AlignHCenter)

        self._name_lbl = QLabel()
        self._name_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._name_lbl.setStyleSheet(f"font-size: 15px; font-weight: 700; color: {_TEXT};")
        center.addWidget(self._name_lbl)

        self._status_lbl = QLabel()
        self._status_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._status_lbl.setStyleSheet(f"""
            background: rgba(74,140,255,0.15); color: {_ACCENT};
            border-radius: 4px; padding: 2px 8px;
            font-size: 11px; font-weight: 500;
        """)
        center.addWidget(self._status_lbl, alignment=Qt.AlignmentFlag.AlignHCenter)

        hl.addLayout(center, stretch=1)

        # Right: owner label + handover button
        right = QHBoxLayout()
        right.setSpacing(8)

        self._owner_lbl = QLabel()
        self._owner_lbl.setStyleSheet(f"font-size: 12px; color: {_TEXT3};")
        right.addWidget(self._owner_lbl)

        self._handover_btn = QPushButton("引き継ぎ")
        self._handover_btn.setFixedHeight(28)
        self._handover_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._handover_btn.setStyleSheet(f"""
            QPushButton {{
                background: {_BG4}; color: {_TEXT2};
                border: 1px solid {_BORDER2};
                padding: 4px 10px; border-radius: 4px; font-size: 11px;
            }}
            QPushButton:hover {{ border-color: {_ACCENT}; color: {_ACCENT}; }}
        """)
        self._handover_btn.clicked.connect(self.handover_clicked)
        right.addWidget(self._handover_btn)

        hl.addLayout(right, stretch=0)

    def update_task(self, task: dict, current_state: str):
        self._name_lbl.setText(task.get("task_name", ""))
        state_label = STATE_LABELS.get(current_state, current_state)
        self._status_lbl.setText(state_label)
        owner = task.get("assigned_to", "")
        self._owner_lbl.setText(f"担当: {owner}" if owner else "")
        # 終了済みタスクは引き継ぎ不可
        readonly = task.get("status") == "終了"
        self._handover_btn.setVisible(not readonly)


# ── Main page ──────────────────────────────────────────────────────────────────

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

        # ── Detail header (task-header-bar + state-bar), hidden in list view ──
        self.detail_header = QWidget()
        self.detail_header.setStyleSheet(f"background: {_BG};")
        dh_layout = QVBoxLayout(self.detail_header)
        dh_layout.setContentsMargins(20, 12, 20, 0)
        dh_layout.setSpacing(8)

        self.task_header_bar = _TaskHeaderBar()
        self.task_header_bar.back_clicked.connect(self.show_list)
        self.task_header_bar.handover_clicked.connect(self._on_handover)
        dh_layout.addWidget(self.task_header_bar)

        self.state_bar = _StateBar()
        self.state_bar.state_clicked.connect(self._on_state_bar_click)
        dh_layout.addWidget(self.state_bar)

        self.detail_header.setVisible(False)
        root.addWidget(self.detail_header)

        # ── Stacked widget ────────────────────────────────────────────────────
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
        w.setStyleSheet(f"background: {_BG};")
        root = QVBoxLayout(w)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # Header
        header = QFrame()
        header.setFixedHeight(48)
        header.setStyleSheet(f"QFrame {{ background: {_BG2}; border-bottom: 1px solid {_BORDER}; }}")
        hl = QHBoxLayout(header)
        hl.setContentsMargins(20, 0, 20, 0)
        title_lbl = QLabel("タスク")
        title_lbl.setStyleSheet(f"font-size: 13px; font-weight: 600; color: {_TEXT2};")
        hl.addWidget(title_lbl)
        hl.addStretch()
        new_btn = QPushButton("+ 新規作成")
        new_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        new_btn.setStyleSheet(f"""
            QPushButton {{
                background: {_ACCENT}; color: white; border: none;
                padding: 6px 14px; border-radius: 6px; font-size: 12px; font-weight: 500;
            }}
            QPushButton:hover {{ background: #5a9dff; }}
        """)
        new_btn.clicked.connect(self.start_new_task)
        hl.addWidget(new_btn)
        root.addWidget(header)

        # Filter bar
        filter_bar = QWidget()
        filter_bar.setStyleSheet(f"background: {_BG}; border-bottom: 1px solid {_BORDER};")
        fl = QHBoxLayout(filter_bar)
        fl.setContentsMargins(20, 8, 20, 8)
        fl.setSpacing(8)

        self.filter_tabs = _FilterTabs(["全件", "進行中", "終了", CURRENT_USER])
        self.filter_tabs.tab_changed.connect(self._apply_filter)
        fl.addWidget(self.filter_tabs)
        fl.addStretch()

        self.count_lbl = QLabel()
        self.count_lbl.setStyleSheet(f"color: {_TEXT3}; font-size: 12px;")
        fl.addWidget(self.count_lbl)
        root.addWidget(filter_bar)

        # Table
        headers = ["作成日時", "ホルダグループ", "JOB番号", "ステータス", "担当者", "最終更新", ""]
        self.task_table = QTableWidget(0, len(headers))
        self.task_table.setHorizontalHeaderLabels(headers)
        self.task_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.task_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.task_table.setAlternatingRowColors(True)
        hh = self.task_table.horizontalHeader()
        hh.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        hh.setSectionResizeMode(1, QHeaderView.ResizeMode.Fixed)
        hh.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        hh.setSectionResizeMode(3, QHeaderView.ResizeMode.Fixed)
        hh.setSectionResizeMode(4, QHeaderView.ResizeMode.Fixed)
        hh.setSectionResizeMode(5, QHeaderView.ResizeMode.Fixed)
        hh.setSectionResizeMode(6, QHeaderView.ResizeMode.Fixed)
        self.task_table.setColumnWidth(0, 140)
        self.task_table.setColumnWidth(1, 120)
        self.task_table.setColumnWidth(3, 120)
        self.task_table.setColumnWidth(4, 100)
        self.task_table.setColumnWidth(5, 140)
        self.task_table.setColumnWidth(6, 70)
        self.task_table.setStyleSheet(f"""
            QTableWidget {{
                border: none; background: {_BG}; color: {_TEXT};
                gridline-color: {_BORDER};
            }}
            QTableWidget::item {{ color: {_TEXT}; border: none; padding: 2px 8px; }}
            QTableWidget::item:alternate {{ background: {_BG3}; }}
            QTableWidget::item:selected {{ background: {_ACCENT}; color: white; }}
            QHeaderView::section {{
                background: {_BG2}; color: {_TEXT3};
                border: none; border-bottom: 1px solid {_BORDER};
                padding: 8px 12px; font-size: 11px; font-weight: bold;
            }}
        """)
        self.task_table.verticalHeader().setVisible(False)
        self.task_table.doubleClicked.connect(self._on_row_double_click)
        root.addWidget(self.task_table)

        return w

    # ── Public API ────────────────────────────────────────────────────────────

    def show_list(self):
        self._current_task = None
        self.detail_header.setVisible(False)
        self.stack.setCurrentIndex(_IDX_LIST)
        self._refresh_list()

    def start_new_task(self):
        self._current_task = None
        self.setup_state.open_new()
        self.detail_header.setVisible(False)
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
        self._all_tasks = all_tasks[:100]
        self._apply_filter(self.filter_tabs._active if hasattr(self.filter_tabs, "_active") else "全件")

    def _apply_filter(self, filter_text: str):
        tasks = getattr(self, "_all_tasks", [])
        if filter_text == "進行中":
            tasks = [t for t in tasks if t.get("status") not in ("終了",)]
        elif filter_text == "終了":
            tasks = [t for t in tasks if t.get("status") == "終了"]
        elif filter_text == CURRENT_USER:
            tasks = [t for t in tasks if t.get("assigned_to") == CURRENT_USER]
        self._fill_table(tasks)
        self.count_lbl.setText(f"{len(tasks)} 件")

    def _fill_table(self, tasks: list[dict]):
        from app.config import STATE_LABELS
        self.task_table.setRowCount(0)
        for t in tasks:
            row = self.task_table.rowCount()
            self.task_table.insertRow(row)
            state = t.get("current_state", "")
            state_label = STATE_LABELS.get(state, state)
            status = t.get("status", "")
            job_str = ", ".join(t.get("job_numbers", []))
            updated = t.get("updated_at", "")[:16].replace("T", " ")
            created = t.get("created_at", "")[:16].replace("T", " ")

            vals = [
                created,
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
                    color = _ACCENT if status == "進行中" else (
                        _WARN if status == "回覧中" else (
                        _SUCCESS if status == "終了" else _TEXT2))
                    item.setForeground(QColor(color))
                    item.setFont(QFont("", -1, QFont.Weight.Bold))
                self.task_table.setItem(row, col, item)

            # Action button
            act_btn = QPushButton("開く")
            act_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            act_btn.setStyleSheet(f"""
                QPushButton {{
                    background: {_BG4}; color: {_ACCENT}; border: 1px solid {_BORDER2};
                    padding: 4px 10px; border-radius: 4px; font-size: 11px;
                }}
                QPushButton:hover {{ border-color: {_ACCENT}; }}
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

    def _on_state_bar_click(self, state: str):
        self._go_to_state(state)

    def _on_handover(self):
        """引き継ぎボタン押下時: ダイアログを開き、確定されたら担当者を変更する。"""
        if not self._current_task:
            return
        dlg = _HandoverDialog(self._current_task, parent=self)
        if dlg.exec() != QDialog.DialogCode.Accepted:
            return
        new_assignee = dlg.new_assignee
        task_store.handover_task(
            self._current_task["task_id"],
            new_assignee=new_assignee,
            operated_by=CURRENT_USER,
        )
        # タスクを再読み込みしてヘッダーを更新
        task = task_store.get_task(self._current_task["task_id"])
        if task:
            self._current_task = task
            current_state = task.get("current_state", "analysis_targets")
            self.task_header_bar.update_task(task, current_state)
        QMessageBox.information(
            self,
            "引き継ぎ完了",
            f"担当者を「{new_assignee}」に変更しました。",
        )

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
            # Show detail header and update
            self.detail_header.setVisible(True)
            self.task_header_bar.update_task(task, state)
            self.state_bar.set_active_state(state)
