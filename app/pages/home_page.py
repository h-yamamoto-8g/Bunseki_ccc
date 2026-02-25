from datetime import datetime
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QFrame,
    QCalendarWidget, QAbstractItemView, QSplitter,
)
from PySide6.QtCore import Signal, Qt, QDate
from PySide6.QtGui import QColor, QFont

from app.data import task_store
from app.config import CURRENT_USER, STATE_LABELS, STATUS_LABELS


class HomePage(QWidget):
    navigate_to_new_task = Signal()
    navigate_to_task = Signal(str)

    def __init__(self, data_loader, parent=None):
        super().__init__(parent)
        self.data_loader = data_loader
        self._setup_ui()

    def _setup_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # Header bar
        header = QFrame()
        header.setFixedHeight(56)
        header.setStyleSheet("background:#f8fafc; border-bottom:1px solid #e2e8f0;")
        hl = QHBoxLayout(header)
        hl.setContentsMargins(24, 0, 24, 0)
        title_lbl = QLabel("ホーム")
        title_lbl.setStyleSheet("font-size:18px; font-weight:bold; color:#1e293b;")
        hl.addWidget(title_lbl)
        hl.addStretch()
        new_btn = QPushButton("+ 新規タスク起票")
        new_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        new_btn.setStyleSheet("""
            QPushButton {
                background:#2563eb; color:white; border:none;
                padding:8px 20px; border-radius:6px; font-size:13px; font-weight:bold;
            }
            QPushButton:hover { background:#1d4ed8; }
        """)
        new_btn.clicked.connect(self.navigate_to_new_task)
        hl.addWidget(new_btn)
        root.addWidget(header)

        # Body splitter
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setStyleSheet("QSplitter::handle { background:#e2e8f0; }")

        # Left: Calendar
        left = QWidget()
        left.setMinimumWidth(320)
        ll = QVBoxLayout(left)
        ll.setContentsMargins(20, 20, 12, 20)
        cal_lbl = QLabel("当月予定表")
        cal_lbl.setStyleSheet("font-size:14px; font-weight:bold; color:#374151; margin-bottom:8px;")
        ll.addWidget(cal_lbl)
        self.calendar = QCalendarWidget()
        self.calendar.setGridVisible(True)
        self.calendar.setStyleSheet("""
            QCalendarWidget QWidget          { background: white; color: #1e293b; }
            QCalendarWidget QToolButton      { color: #1e293b; background: white;
                                               font-size: 13px; font-weight: bold;
                                               border: none; padding: 4px 8px; }
            QCalendarWidget QToolButton:hover { background: #e2e8f0; }
            QCalendarWidget QMenu            { color: #1e293b; background: white; }
            QCalendarWidget QSpinBox         { color: #1e293b; background: white; }
            QCalendarWidget QAbstractItemView:enabled  { color: #1e293b; background: white; }
            QCalendarWidget QAbstractItemView:disabled { color: #94a3b8; }
            QCalendarWidget QAbstractItemView:selected { background: #2563eb; color: white; }
        """)
        today = QDate.currentDate()
        self.calendar.setSelectedDate(today)
        ll.addWidget(self.calendar)
        schedule_note = QLabel("※ 予定表Excelはapp_data/bunseki/以下のファイルを使用します")
        schedule_note.setStyleSheet("color:#94a3b8; font-size:11px; margin-top:4px;")
        schedule_note.setWordWrap(True)
        ll.addWidget(schedule_note)
        ll.addStretch()
        splitter.addWidget(left)

        # Right: Task lists
        right = QWidget()
        rl = QVBoxLayout(right)
        rl.setContentsMargins(12, 20, 20, 20)
        rl.setSpacing(12)

        # Warning banner (hidden by default)
        self.warn_banner = QFrame()
        self.warn_banner.setStyleSheet("""
            QFrame { background:#fef2f2; border:1px solid #fca5a5;
                     border-radius:6px; padding:4px; }
        """)
        wb_layout = QHBoxLayout(self.warn_banner)
        wb_layout.setContentsMargins(12, 8, 12, 8)
        self.warn_lbl = QLabel()
        self.warn_lbl.setStyleSheet("color:#dc2626; font-size:12px;")
        self.warn_lbl.setWordWrap(True)
        wb_layout.addWidget(self.warn_lbl)
        reissue_btn = QPushButton("再起票")
        reissue_btn.setStyleSheet("""
            QPushButton { background:#dc2626; color:white; border:none;
                          padding:4px 12px; border-radius:4px; font-size:12px; }
            QPushButton:hover { background:#b91c1c; }
        """)
        reissue_btn.clicked.connect(self.navigate_to_new_task)
        wb_layout.addWidget(reissue_btn)
        self.warn_banner.setVisible(False)
        rl.addWidget(self.warn_banner)

        # My tasks
        my_lbl = QLabel(f"自分のタスク  ({CURRENT_USER})")
        my_lbl.setStyleSheet("font-size:14px; font-weight:bold; color:#374151;")
        rl.addWidget(my_lbl)
        self.my_table = self._make_table()
        self.my_table.doubleClicked.connect(self._on_my_double_click)
        rl.addWidget(self.my_table)

        # Others' tasks
        other_lbl = QLabel("他のユーザーのタスク")
        other_lbl.setStyleSheet("font-size:14px; font-weight:bold; color:#374151;")
        rl.addWidget(other_lbl)
        self.other_table = self._make_table()
        self.other_table.doubleClicked.connect(self._on_other_double_click)
        rl.addWidget(self.other_table)

        splitter.addWidget(right)
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 2)
        root.addWidget(splitter)

    def _make_table(self) -> QTableWidget:
        headers = ["タスク名", "ホルダグループ", "JOB番号", "ステータス", "担当者", "最終更新"]
        t = QTableWidget(0, len(headers))
        t.setHorizontalHeaderLabels(headers)
        t.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        t.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        t.setAlternatingRowColors(True)
        t.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        t.setStyleSheet("""
            QTableWidget { border:1px solid #e2e8f0; border-radius:6px; }
            QHeaderView::section { background:#f8fafc; font-weight:bold; color:#374151;
                                    padding:6px; border:none; border-bottom:1px solid #e2e8f0; }
        """)
        t.verticalHeader().setVisible(False)
        t.setMaximumHeight(240)
        return t

    def refresh(self):
        tasks = task_store.load_tasks()
        active = [t for t in tasks if t.get("status") != "終了"]

        my_tasks = [t for t in active if t.get("assigned_to") == CURRENT_USER]
        other_tasks = [t for t in active if t.get("assigned_to") != CURRENT_USER]

        self._fill_table(self.my_table, my_tasks)
        self._fill_table(self.other_table, other_tasks)

        # Check if any task has a missing state
        self.warn_banner.setVisible(False)

    def _fill_table(self, table: QTableWidget, tasks: list[dict]):
        table.setRowCount(0)
        for t in tasks:
            row = table.rowCount()
            table.insertRow(row)
            state = t.get("current_state", "")
            state_label = STATE_LABELS.get(state, state)
            job_str = ", ".join(t.get("job_numbers", []))
            updated = t.get("updated_at", "")[:16].replace("T", " ")

            vals = [
                t.get("task_name", ""),
                t.get("holder_group_name", ""),
                job_str,
                f"{t.get('status','')} / {state_label}",
                t.get("assigned_to", ""),
                updated,
            ]
            for col, v in enumerate(vals):
                item = QTableWidgetItem(str(v))
                item.setData(Qt.ItemDataRole.UserRole, t.get("task_id"))
                if col == 3:
                    color = STATUS_LABELS.get(t.get("status", ""), "#6b7280")
                    item.setForeground(QColor(color))
                    item.setFont(QFont("", -1, QFont.Weight.Bold))
                table.setItem(row, col, item)

    def _on_my_double_click(self, index):
        item = self.my_table.item(index.row(), 0)
        if item:
            task_id = item.data(Qt.ItemDataRole.UserRole)
            if task_id:
                self.navigate_to_task.emit(task_id)

    def _on_other_double_click(self, index):
        item = self.other_table.item(index.row(), 0)
        if item:
            task_id = item.data(Qt.ItemDataRole.UserRole)
            if task_id:
                self.navigate_to_task.emit(task_id)
