"""ジョブページ — JOB番号の設定・管理（CRUD）"""
import json
from datetime import date
from pathlib import Path

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QTableWidget, QTableWidgetItem, QHeaderView,
    QAbstractItemView, QDialog, QDialogButtonBox, QFormLayout,
    QLineEdit, QDateEdit, QMessageBox,
)
from PySide6.QtCore import Qt, QDate
from PySide6.QtGui import QColor, QFont

from app.config import DATA_PATH

_BG2    = "#161b27"
_BG3    = "#1e2535"
_BORDER = "#2a3349"
_TEXT   = "#e8eaf0"
_TEXT2  = "#8b93a8"
_TEXT3  = "#5a6278"
_ACCENT = "#4a8cff"
_SUCCESS= "#2ecc8a"
_WARN   = "#f5a623"
_DANGER = "#e85454"

_JOBS_PATH = DATA_PATH / "bunseki" / "jobs" / "jobs.json"


def _load_jobs() -> list[dict]:
    if _JOBS_PATH.exists():
        try:
            return json.loads(_JOBS_PATH.read_text(encoding="utf-8")).get("items", [])
        except Exception:
            pass
    return []


def _save_jobs(items: list[dict]):
    _JOBS_PATH.parent.mkdir(parents=True, exist_ok=True)
    _JOBS_PATH.write_text(
        json.dumps({"items": items}, ensure_ascii=False, indent=2), encoding="utf-8"
    )


def _next_id(items: list[dict]) -> str:
    nums = []
    for it in items:
        try:
            nums.append(int(it["id"].replace("J-", "")))
        except (KeyError, ValueError):
            pass
    return f"J-{(max(nums) + 1) if nums else 1:03d}"


class JobPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()
        self._load_jobs()

    def _setup_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # Topbar
        topbar = QFrame()
        topbar.setFixedHeight(48)
        topbar.setStyleSheet(f"QFrame {{ background:{_BG2}; border-bottom:1px solid {_BORDER}; }}")
        tl = QHBoxLayout(topbar)
        tl.setContentsMargins(20, 0, 20, 0)
        title_lbl = QLabel("ジョブ")
        title_lbl.setStyleSheet(f"font-size:13px; font-weight:600; color:{_TEXT2};")
        tl.addWidget(title_lbl)
        tl.addStretch()
        root.addWidget(topbar)

        # Body
        body = QWidget()
        bl = QVBoxLayout(body)
        bl.setContentsMargins(20, 20, 20, 20)
        bl.setSpacing(12)
        root.addWidget(body)

        h1 = QLabel("ジョブ")
        h1.setStyleSheet(f"font-size:20px; font-weight:700; color:{_TEXT};")
        bl.addWidget(h1)
        sub = QLabel("分析に必要なJOB番号を設定・管理します")
        sub.setStyleSheet(f"font-size:12px; color:{_TEXT3};")
        bl.addWidget(sub)

        # Toolbar
        tb = QHBoxLayout()
        tb.setSpacing(8)

        add_btn = QPushButton("+ 追加")
        add_btn.setStyleSheet(f"""
            QPushButton {{ background:{_ACCENT}; color:white; border:none;
                          padding:6px 14px; border-radius:6px; font-size:12px; }}
            QPushButton:hover {{ background:#5a9dff; }}
        """)
        add_btn.clicked.connect(self._add_job)
        tb.addWidget(add_btn)

        edit_btn = QPushButton("編集")
        edit_btn.setStyleSheet(f"""
            QPushButton {{ background:{_BG3}; color:{_TEXT}; border:1px solid {_BORDER};
                          padding:6px 14px; border-radius:6px; font-size:12px; }}
            QPushButton:hover {{ border-color:{_ACCENT}; color:{_ACCENT}; }}
        """)
        edit_btn.clicked.connect(self._edit_job)
        tb.addWidget(edit_btn)

        del_btn = QPushButton("削除")
        del_btn.setStyleSheet(f"""
            QPushButton {{ background:{_BG3}; color:{_DANGER}; border:1px solid {_BORDER};
                          padding:6px 14px; border-radius:6px; font-size:12px; }}
            QPushButton:hover {{ border-color:{_DANGER}; }}
        """)
        del_btn.clicked.connect(self._delete_job)
        tb.addWidget(del_btn)

        tb.addStretch()
        self.count_lbl = QLabel("")
        self.count_lbl.setStyleSheet(f"font-size:11px; color:{_TEXT3};")
        tb.addWidget(self.count_lbl)
        bl.addLayout(tb)

        # Table
        headers = ["ID", "JOB番号", "開始日", "終了日"]
        self.table = QTableWidget(0, len(headers))
        self.table.setHorizontalHeaderLabels(headers)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setAlternatingRowColors(True)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.table.setStyleSheet(f"""
            QTableWidget {{ background:{_BG2}; color:{_TEXT}; border:1px solid {_BORDER};
                           border-radius:8px; gridline-color:{_BORDER}; }}
            QTableWidget::item {{ color:{_TEXT}; border:none; padding:2px 8px; }}
            QTableWidget::item:alternate {{ background:{_BG3}; }}
            QTableWidget::item:selected {{ background:{_ACCENT}; color:white; }}
            QHeaderView::section {{ background:{_BG2}; color:{_TEXT3}; border:none;
                border-bottom:1px solid {_BORDER}; padding:8px 12px;
                font-size:11px; font-weight:bold; }}
        """)
        self.table.verticalHeader().setVisible(False)
        self.table.doubleClicked.connect(self._edit_job)
        bl.addWidget(self.table)
        bl.addStretch()

    def _load_jobs(self):
        items = _load_jobs()
        self._items = items
        self.table.setRowCount(0)
        today = date.today().isoformat()
        for it in items:
            r = self.table.rowCount()
            self.table.insertRow(r)
            end = it.get("end_date", "")
            vals = [it.get("id", ""), it.get("job_number", ""), it.get("start_date", ""), end]
            for col, v in enumerate(vals):
                item = QTableWidgetItem(str(v))
                # 終了日が過去なら薄く表示
                if col == 3 and end and end < today:
                    item.setForeground(QColor(_TEXT3))
                self.table.setItem(r, col, item)
        self.count_lbl.setText(f"{len(items)} 件")

    def _add_job(self):
        dlg = _JobDialog(parent=self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            items = _load_jobs()
            new_id = _next_id(items)
            items.append({"id": new_id, **dlg.values()})
            _save_jobs(items)
            self._load_jobs()

    def _edit_job(self):
        row = self.table.currentRow()
        if row < 0:
            return
        job_id = self.table.item(row, 0).text()
        items = _load_jobs()
        target = next((it for it in items if it.get("id") == job_id), None)
        if target is None:
            return
        dlg = _JobDialog(initial=target, parent=self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            target.update(dlg.values())
            _save_jobs(items)
            self._load_jobs()

    def _delete_job(self):
        row = self.table.currentRow()
        if row < 0:
            return
        job_id = self.table.item(row, 0).text()
        job_no = self.table.item(row, 1).text()
        reply = QMessageBox.question(
            self, "削除確認", f"JOB番号「{job_no}」(ID: {job_id}) を削除しますか？"
        )
        if reply == QMessageBox.StandardButton.Yes:
            items = _load_jobs()
            items = [it for it in items if it.get("id") != job_id]
            _save_jobs(items)
            self._load_jobs()


class _JobDialog(QDialog):
    def __init__(self, initial: dict | None = None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("JOB番号の追加" if initial is None else "JOB番号の編集")
        self.resize(360, 220)
        vl = QVBoxLayout(self)
        vl.setSpacing(12)

        form = QFormLayout()
        self.job_input = QLineEdit(initial.get("job_number", "") if initial else "")
        self.job_input.setPlaceholderText("例: 250107W")

        start = initial.get("start_date", date.today().isoformat()) if initial else date.today().isoformat()
        end   = initial.get("end_date", "") if initial else ""

        self.start_date = QDateEdit(QDate.fromString(start, "yyyy-MM-dd") if start else QDate.currentDate())
        self.start_date.setCalendarPopup(True)
        self.start_date.setDisplayFormat("yyyy-MM-dd")

        self.end_date = QDateEdit(QDate.fromString(end, "yyyy-MM-dd") if end else QDate.currentDate())
        self.end_date.setCalendarPopup(True)
        self.end_date.setDisplayFormat("yyyy-MM-dd")

        form.addRow("JOB番号:", self.job_input)
        form.addRow("開始日:", self.start_date)
        form.addRow("終了日:", self.end_date)
        vl.addLayout(form)

        btns = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        btns.accepted.connect(self._accept)
        btns.rejected.connect(self.reject)
        vl.addWidget(btns)

    def _accept(self):
        if not self.job_input.text().strip():
            QMessageBox.warning(self, "入力エラー", "JOB番号を入力してください。")
            return
        self.accept()

    def values(self) -> dict:
        return {
            "job_number": self.job_input.text().strip(),
            "start_date": self.start_date.date().toString("yyyy-MM-dd"),
            "end_date": self.end_date.date().toString("yyyy-MM-dd"),
        }
