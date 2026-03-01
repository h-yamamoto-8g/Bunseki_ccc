from datetime import datetime
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QFrame,
    QCalendarWidget, QAbstractItemView, QScrollArea, QSizePolicy,
)
from PySide6.QtCore import Signal, Qt, QDate
from PySide6.QtGui import QColor, QFont

from app.data import task_store
from app.config import CURRENT_USER, STATE_LABELS, STATUS_LABELS

# ── Design tokens (bunseki_ui.html) ──────────────────────────────────────────
_BG2    = "#161b27"
_BG3    = "#1e2535"
_BG4    = "#252d3e"
_BORDER = "#2a3349"
_TEXT   = "#e8eaf0"
_TEXT2  = "#8b93a8"
_TEXT3  = "#5a6278"
_ACCENT = "#4a8cff"
_SUCCESS= "#2ecc8a"
_WARN   = "#f5a623"
_DANGER = "#e85454"

_STAT_CHIPS = [
    ("in_progress", "進行中",   _ACCENT,   f"rgba(74,140,255,0.1)"),
    ("circulation", "回覧中",   _WARN,     f"rgba(245,166,35,0.1)"),
    ("done_month",  "今月完了", _SUCCESS,  f"rgba(46,204,138,0.1)"),
    ("total",       "全件",     _TEXT2,    _BG2),
]

_TAG_COLORS = {
    "進行中": (_ACCENT, "rgba(74,140,255,0.15)"),
    "回覧中": (_WARN,   "rgba(245,166,35,0.1)"),
    "終了":   (_SUCCESS,"rgba(46,204,138,0.1)"),
}


def _tag_style(status: str) -> str:
    color, bg = _TAG_COLORS.get(status, (_TEXT2, _BG4))
    return f"color:{color}; background:{bg}; border-radius:4px; padding:2px 8px; font-size:11px; font-weight:500;"


def _section_label(text: str) -> QLabel:
    lbl = QLabel(text)
    lbl.setStyleSheet(f"""
        font-size:11px; font-weight:700; color:{_TEXT3};
        letter-spacing:1px; text-transform:uppercase;
        margin-top:4px; margin-bottom:2px;
    """)
    return lbl


class HomePage(QWidget):
    navigate_to_new_task = Signal()
    navigate_to_task = Signal(str)

    def __init__(self, data_loader, parent=None):
        super().__init__(parent)
        self.data_loader = data_loader
        self._chip_num: dict[str, QLabel] = {}
        self._setup_ui()

    def _setup_ui(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        # ── Topbar ─────────────────────────────────────────────────────────────
        topbar = QFrame()
        topbar.setFixedHeight(48)
        topbar.setStyleSheet(f"QFrame {{ background:{_BG2}; border-bottom:1px solid {_BORDER}; }}")
        tl = QHBoxLayout(topbar)
        tl.setContentsMargins(20, 0, 20, 0)
        tl.setSpacing(12)

        title = QLabel("ホーム")
        title.setStyleSheet(f"font-size:13px; font-weight:600; color:{_TEXT2};")
        tl.addWidget(title)
        tl.addStretch()

        today_str = datetime.now().strftime("%-m月%-d日")
        date_lbl = QLabel(f"{today_str}  {CURRENT_USER}")
        date_lbl.setStyleSheet(f"font-size:11px; color:{_TEXT3};")
        tl.addWidget(date_lbl)
        outer.addWidget(topbar)

        # ── Scroll body ────────────────────────────────────────────────────────
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        outer.addWidget(scroll)

        body = QWidget()
        body.setStyleSheet(f"background:{_BG2};")  # darker bg for content area... actually transparent
        bl = QVBoxLayout(body)
        bl.setContentsMargins(20, 20, 20, 20)
        bl.setSpacing(12)
        scroll.setWidget(body)

        # ── Page header ────────────────────────────────────────────────────────
        hdr = QHBoxLayout()
        hdr_left = QVBoxLayout()
        hdr_left.setSpacing(4)
        h1 = QLabel("ホーム")
        h1.setStyleSheet(f"font-size:20px; font-weight:700; color:{_TEXT};")
        sub = QLabel(f"{datetime.now().strftime('%Y年%-m月%-d日')} — 本日のタスクと当月スケジュール")
        sub.setStyleSheet(f"font-size:12px; color:{_TEXT3};")
        hdr_left.addWidget(h1)
        hdr_left.addWidget(sub)
        hdr.addLayout(hdr_left)
        hdr.addStretch()

        new_btn = QPushButton("+ 新規タスク作成")
        new_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        new_btn.setStyleSheet(f"""
            QPushButton {{
                background:{_ACCENT}; color:white; border:none;
                padding:6px 14px; border-radius:6px; font-size:12px; font-weight:500;
            }}
            QPushButton:hover {{ background:#5a9dff; }}
        """)
        new_btn.clicked.connect(self.navigate_to_new_task)
        hdr.addWidget(new_btn)
        bl.addLayout(hdr)

        # ── Warning banner (hidden by default) ─────────────────────────────────
        self.warn_banner = QFrame()
        self.warn_banner.setStyleSheet(f"""
            QFrame {{
                background:rgba(245,166,35,0.1);
                border:1px solid rgba(245,166,35,0.3);
                border-radius:6px;
            }}
        """)
        wb = QHBoxLayout(self.warn_banner)
        wb.setContentsMargins(12, 8, 12, 8)
        self.warn_lbl = QLabel()
        self.warn_lbl.setStyleSheet(f"color:{_WARN}; font-size:12px;")
        self.warn_lbl.setWordWrap(True)
        wb.addWidget(self.warn_lbl)
        reissue_btn = QPushButton("再起票")
        reissue_btn.setStyleSheet(f"""
            QPushButton {{ background:{_DANGER}; color:white; border:none;
                          padding:4px 12px; border-radius:4px; font-size:12px; }}
            QPushButton:hover {{ background:#c94444; }}
        """)
        reissue_btn.clicked.connect(self.navigate_to_new_task)
        wb.addWidget(reissue_btn)
        self.warn_banner.setVisible(False)
        bl.addWidget(self.warn_banner)

        # ── Stat chips ─────────────────────────────────────────────────────────
        chips_row = QHBoxLayout()
        chips_row.setSpacing(8)
        for key, label, color, bg in _STAT_CHIPS:
            chip = QFrame()
            chip.setStyleSheet(f"""
                QFrame {{
                    background:{_BG2};
                    border:1px solid {_BORDER};
                    border-radius:8px;
                }}
            """)
            chip.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
            cl = QHBoxLayout(chip)
            cl.setContentsMargins(16, 10, 16, 10)
            cl.setSpacing(10)

            num = QLabel("0")
            num.setStyleSheet(f"font-size:22px; font-weight:700; color:{color}; font-family:'Courier New',monospace;")
            cl.addWidget(num)

            info = QVBoxLayout()
            info.setSpacing(2)
            lbl_w = QLabel(label)
            lbl_w.setStyleSheet(f"font-size:11px; font-weight:600; color:{_TEXT};")
            info.addWidget(lbl_w)
            cl.addLayout(info)
            cl.addStretch()

            self._chip_num[key] = num
            chips_row.addWidget(chip)
        bl.addLayout(chips_row)

        # ── 自分のタスク ────────────────────────────────────────────────────────
        bl.addWidget(_section_label("自分のタスク"))
        self.my_table = self._make_my_table()
        self.my_table.doubleClicked.connect(self._on_my_double_click)
        bl.addWidget(self.my_table)

        # ── チームのタスク ──────────────────────────────────────────────────────
        bl.addWidget(_section_label(f"チームのタスク（進行中）"))
        self.other_table = self._make_other_table()
        self.other_table.doubleClicked.connect(self._on_other_double_click)
        bl.addWidget(self.other_table)

        # ── 当月予定表 ──────────────────────────────────────────────────────────
        bl.addSpacing(4)
        divider = QFrame()
        divider.setFixedHeight(1)
        divider.setStyleSheet(f"background:{_BORDER};")
        bl.addWidget(divider)

        bl.addWidget(_section_label("当月予定表"))
        cal_card = QFrame()
        cal_card.setStyleSheet(f"""
            QFrame {{
                background:{_BG2};
                border:1px solid {_BORDER};
                border-radius:8px;
            }}
        """)
        cal_l = QVBoxLayout(cal_card)
        cal_l.setContentsMargins(12, 12, 12, 12)
        self.calendar = QCalendarWidget()
        self.calendar.setGridVisible(True)
        self.calendar.setSelectedDate(QDate.currentDate())
        self.calendar.setMaximumHeight(260)
        cal_l.addWidget(self.calendar)
        bl.addWidget(cal_card)

        bl.addStretch()

    def _make_table_base(self, headers: list[str]) -> QTableWidget:
        t = QTableWidget(0, len(headers))
        t.setHorizontalHeaderLabels(headers)
        t.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        t.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        t.setAlternatingRowColors(True)
        t.setStyleSheet(f"""
            QTableWidget {{
                background:{_BG2}; color:{_TEXT};
                border:1px solid {_BORDER}; border-radius:8px;
                gridline-color:{_BORDER};
            }}
            QTableWidget::item {{ color:{_TEXT}; border:none; padding:2px 8px; }}
            QTableWidget::item:alternate {{ background:{_BG3}; }}
            QTableWidget::item:selected {{ background:{_ACCENT}; color:white; }}
            QHeaderView::section {{
                background:{_BG2}; color:{_TEXT3};
                border:none; border-bottom:1px solid {_BORDER};
                padding:8px 12px; font-size:11px; font-weight:bold;
            }}
        """)
        t.verticalHeader().setVisible(False)
        t.setMaximumHeight(200)
        return t

    def _make_my_table(self) -> QTableWidget:
        headers = ["作成日時", "ホルダグループ", "JOB番号", "ステータス", "最終更新", ""]
        t = self._make_table_base(headers)
        hh = t.horizontalHeader()
        hh.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        hh.setSectionResizeMode(1, QHeaderView.ResizeMode.Fixed)
        hh.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        hh.setSectionResizeMode(3, QHeaderView.ResizeMode.Fixed)
        hh.setSectionResizeMode(4, QHeaderView.ResizeMode.Fixed)
        hh.setSectionResizeMode(5, QHeaderView.ResizeMode.Fixed)
        t.setColumnWidth(0, 140)
        t.setColumnWidth(1, 120)
        t.setColumnWidth(3, 110)
        t.setColumnWidth(4, 140)
        t.setColumnWidth(5, 70)
        return t

    def _make_other_table(self) -> QTableWidget:
        headers = ["作成日時", "ホルダグループ", "JOB番号", "ステータス", "担当者", "最終更新", ""]
        t = self._make_table_base(headers)
        hh = t.horizontalHeader()
        hh.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        hh.setSectionResizeMode(1, QHeaderView.ResizeMode.Fixed)
        hh.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        hh.setSectionResizeMode(3, QHeaderView.ResizeMode.Fixed)
        hh.setSectionResizeMode(4, QHeaderView.ResizeMode.Fixed)
        hh.setSectionResizeMode(5, QHeaderView.ResizeMode.Fixed)
        hh.setSectionResizeMode(6, QHeaderView.ResizeMode.Fixed)
        t.setColumnWidth(0, 140)
        t.setColumnWidth(1, 120)
        t.setColumnWidth(3, 110)
        t.setColumnWidth(4, 90)
        t.setColumnWidth(5, 140)
        t.setColumnWidth(6, 70)
        return t

    def refresh(self):
        tasks = task_store.load_tasks()
        active = [t for t in tasks if t.get("status") != "終了"]

        my_tasks    = [t for t in active if t.get("assigned_to") == CURRENT_USER]
        other_tasks = [t for t in active if t.get("assigned_to") != CURRENT_USER]

        self._fill_table(self.my_table, my_tasks, show_owner=False)
        self._fill_table(self.other_table, other_tasks, show_owner=True)

        # Stat chips
        now = datetime.now()
        month_pfx = now.strftime("%Y-%m")
        in_progress = sum(1 for t in tasks if t.get("status") == "進行中")
        circulation = sum(1 for t in tasks if t.get("status") == "回覧中")
        done_month  = sum(
            1 for t in tasks
            if t.get("status") == "終了"
            and t.get("updated_at", "").startswith(month_pfx)
        )
        self._chip_num["in_progress"].setText(str(in_progress))
        self._chip_num["circulation"].setText(str(circulation))
        self._chip_num["done_month"].setText(str(done_month))
        self._chip_num["total"].setText(str(len(tasks)))

        self.warn_banner.setVisible(False)

    def _fill_table(self, table: QTableWidget, tasks: list[dict], show_owner: bool = False):
        table.setRowCount(0)
        for t in tasks:
            row = table.rowCount()
            table.insertRow(row)
            state = t.get("current_state", "")
            state_label = STATE_LABELS.get(state, state)
            job_str = ", ".join(t.get("job_numbers", []))
            updated = t.get("updated_at", "")[:16].replace("T", " ")
            created = t.get("created_at", "")[:16].replace("T", " ")
            status  = t.get("status", "")

            if show_owner:
                vals = [
                    created,
                    t.get("holder_group_name", ""),
                    job_str,
                    f"{status} / {state_label}",
                    t.get("assigned_to", ""),
                    updated,
                ]
            else:
                vals = [
                    created,
                    t.get("holder_group_name", ""),
                    job_str,
                    f"{status} / {state_label}",
                    updated,
                ]

            for col, v in enumerate(vals):
                item = QTableWidgetItem(str(v))
                item.setData(Qt.ItemDataRole.UserRole, t.get("task_id"))
                if col == 3:
                    color, _ = _TAG_COLORS.get(status, (_TEXT2, ""))
                    item.setForeground(QColor(color))
                    item.setFont(QFont("", -1, QFont.Weight.Bold))
                table.setItem(row, col, item)

            # Action button
            last_col = len(vals)
            act_btn = QPushButton("開く")
            act_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            act_btn.setStyleSheet(f"""
                QPushButton {{
                    background:#252d3e; color:#4a8cff; border:1px solid #334166;
                    padding:4px 10px; border-radius:4px; font-size:11px;
                }}
                QPushButton:hover {{ border-color:#4a8cff; }}
            """)
            task_id = t.get("task_id")
            act_btn.clicked.connect(lambda _=False, tid=task_id: self.navigate_to_task.emit(tid))
            table.setCellWidget(row, last_col, act_btn)

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
