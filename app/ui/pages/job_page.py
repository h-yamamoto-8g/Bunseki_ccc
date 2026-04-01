"""JOBマスタ管理ページ — JOB番号の設定・管理（CRUD）。"""
from __future__ import annotations

from datetime import date

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from app.config import CURRENT_USER
from app.services.job_service import JobService
from app.ui.widgets.date_edit import DateEdit
from app.ui.widgets.table_utils import enable_row_numbers_and_sort

# ── デザイントークン ──────────────────────────────────────────────────────────
_BG = "#f8fafc"
_BG2 = "#ffffff"
_TEXT = "#1e293b"
_TEXT2 = "#64748b"
_ACCENT = "#3b82f6"
_BORDER = "#e2e8f0"
_DANGER = "#ef4444"


class JobPage(QWidget):
    """JOBマスタ一覧 + 新規作成/編集/削除。"""

    def __init__(self, job_service: JobService, parent: QWidget | None = None):
        super().__init__(parent)
        self._svc = job_service
        self._build_ui()

    # ── UI 構築 ───────────────────────────────────────────────────────────────

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(24, 16, 24, 16)
        root.setSpacing(12)

        # ヘッダー行
        header = QHBoxLayout()
        title = QLabel("JOBマスタ")
        title.setStyleSheet(f"font-size:18px; font-weight:700; color:{_TEXT};")
        header.addWidget(title)
        header.addStretch()

        self.btn_new = QPushButton("+ 新規")
        self.btn_new.setFixedHeight(28)
        self.btn_new.setStyleSheet(
            f"QPushButton {{ background:{_ACCENT}; color:white; border:none;"
            f" padding:4px 12px; border-radius:5px; font-size:12px; font-weight:600; }}"
            f"QPushButton:hover {{ background:#2563eb; }}"
        )
        self.btn_new.clicked.connect(self._on_new)
        header.addWidget(self.btn_new)
        root.addLayout(header)

        # テーブル
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(
            ["JOB番号", "開始日", "終了日", "メモ", "状態", "操作"]
        )
        self.table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Stretch
        )
        self.table.horizontalHeader().setSectionResizeMode(
            5, QHeaderView.ResizeMode.Fixed
        )
        self.table.setColumnWidth(5, 140)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.verticalHeader().setDefaultSectionSize(40)
        enable_row_numbers_and_sort(self.table, self._on_sort_column)
        self.table.setStyleSheet(
            f"QTableWidget {{ border:1px solid {_BORDER}; border-radius:6px;"
            f" background:{_BG2}; gridline-color:{_BORDER}; }}"
            f"QHeaderView::section {{ background:#f1f5f9; color:{_TEXT};"
            f" font-size:12px; font-weight:600; padding:6px;"
            f" border:none; border-bottom:1px solid {_BORDER}; }}"
            f"QTableWidget::item {{ padding:4px 8px; font-size:12px; color:{_TEXT}; }}"
        )
        root.addWidget(self.table, 1)

    # ── 公開 API ──────────────────────────────────────────────────────────────

    _JOB_SORT_KEYS = ["job_number", "start_date", "end_date", "notes"]

    def _on_sort_column(self, col: int, ascending: bool) -> None:
        if hasattr(self, "_jobs_data") and col < len(self._JOB_SORT_KEYS):
            key = self._JOB_SORT_KEYS[col]
            self._jobs_data.sort(
                key=lambda j: j.get(key, ""), reverse=not ascending,
            )
            self._populate_jobs(self._jobs_data)

    def _load_jobs(self) -> None:
        """main.py からページ切替時に呼ばれる。"""
        self._jobs_data = self._svc.get_all_jobs()
        self._populate_jobs(self._jobs_data)

    def _populate_jobs(self, jobs: list[dict]) -> None:
        self.table.setRowCount(len(jobs))
        today = date.today().isoformat()

        for row, job in enumerate(jobs):
            self.table.setItem(
                row, 0, QTableWidgetItem(job.get("job_number", ""))
            )
            self.table.setItem(
                row, 1, QTableWidgetItem(job.get("start_date", ""))
            )
            self.table.setItem(
                row, 2, QTableWidgetItem(job.get("end_date", ""))
            )
            self.table.setItem(
                row, 3, QTableWidgetItem(job.get("notes", ""))
            )

            # 状態チップ
            is_active = job.get("is_active", True)
            start = job.get("start_date", "")
            end = job.get("end_date", "")
            is_valid = is_active and start and end and start <= today <= end
            status_item = QTableWidgetItem("有効" if is_valid else "期間外")
            status_item.setForeground(
                QColor("#16a34a") if is_valid else QColor("#94a3b8")
            )
            self.table.setItem(row, 4, status_item)

            # 操作ボタン
            actions = QWidget()
            hl = QHBoxLayout(actions)
            hl.setContentsMargins(4, 2, 4, 2)
            hl.setSpacing(4)

            btn_edit = QPushButton("編集")
            btn_edit.setFixedHeight(22)
            btn_edit.setStyleSheet(
                f"QPushButton {{ background:{_BG2}; color:{_TEXT2};"
                f" border:1px solid {_BORDER}; padding:1px 8px;"
                f" border-radius:4px; font-size:11px; }}"
                f"QPushButton:hover {{ background:#f1f5f9; }}"
            )
            job_id = job["id"]
            btn_edit.clicked.connect(
                lambda _=False, jid=job_id: self._on_edit(jid)
            )
            hl.addWidget(btn_edit)

            btn_del = QPushButton("削除")
            btn_del.setFixedHeight(22)
            btn_del.setStyleSheet(
                f"QPushButton {{ background:#fef2f2; color:{_DANGER};"
                f" border:1px solid #fecaca; padding:1px 8px;"
                f" border-radius:4px; font-size:11px; }}"
                f"QPushButton:hover {{ background:#fee2e2; }}"
            )
            btn_del.clicked.connect(
                lambda _=False, jid=job_id: self._on_delete(jid)
            )
            hl.addWidget(btn_del)

            self.table.setCellWidget(row, 5, actions)

    # ── ハンドラ ──────────────────────────────────────────────────────────────

    def _on_new(self) -> None:
        dlg = JobEditDialog(parent=self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            data = dlg.result_data()
            self._svc.create_job(
                job_number=data["job_number"],
                start_date=data["start_date"],
                end_date=data["end_date"],
                created_by=CURRENT_USER,
                notes=data["notes"],
            )
            self._load_jobs()

    def _on_edit(self, job_id: str) -> None:
        job = self._svc.get_job(job_id)
        if not job:
            return
        dlg = JobEditDialog(job=job, parent=self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            data = dlg.result_data()
            self._svc.update_job(
                job_id,
                job_number=data["job_number"],
                start_date=data["start_date"],
                end_date=data["end_date"],
                notes=data["notes"],
            )
            self._load_jobs()

    def _on_delete(self, job_id: str) -> None:
        job = self._svc.get_job(job_id)
        if not job:
            return
        reply = QMessageBox.question(
            self,
            "削除確認",
            f"「{job.get('job_number', '')}」を削除しますか？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            self._svc.delete_job(job_id)
            self._load_jobs()


# ── 編集ダイアログ ─────────────────────────────────────────────────────────────


class JobEditDialog(QDialog):
    """JOB新規作成 / 編集ダイアログ。"""

    def __init__(
        self, job: dict | None = None, parent: QWidget | None = None
    ):
        super().__init__(parent)
        self._job = job
        self.setWindowTitle("JOB編集" if job else "JOB作成")
        self.resize(420, 280)
        self.setMinimumSize(360, 240)
        self._build_ui()
        if job:
            self._load(job)

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(20, 16, 20, 16)
        root.setSpacing(12)

        # JOB番号
        self.edit_job_number = QLineEdit()
        self.edit_job_number.setPlaceholderText("例: 260106W")
        self._style_input(self.edit_job_number)
        root.addLayout(self._row("JOB番号 *", self.edit_job_number))

        # 開始日
        self.edit_start_date = DateEdit()
        root.addLayout(self._row("開始日 *", self.edit_start_date))

        # 終了日
        self.edit_end_date = DateEdit()
        root.addLayout(self._row("終了日 *", self.edit_end_date))

        # メモ
        self.edit_notes = QLineEdit()
        self.edit_notes.setPlaceholderText("任意メモ")
        self._style_input(self.edit_notes)
        root.addLayout(self._row("メモ", self.edit_notes))

        root.addStretch()

        # OK / Cancel
        btns = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok
            | QDialogButtonBox.StandardButton.Cancel
        )
        btns.button(QDialogButtonBox.StandardButton.Ok).setText("保存")
        btns.button(QDialogButtonBox.StandardButton.Cancel).setText(
            "キャンセル"
        )
        btns.accepted.connect(self._on_ok)
        btns.rejected.connect(self.reject)
        root.addWidget(btns)

    def _load(self, job: dict) -> None:
        self.edit_job_number.setText(job.get("job_number", ""))
        self.edit_start_date.setText(job.get("start_date", ""))
        self.edit_end_date.setText(job.get("end_date", ""))
        self.edit_notes.setText(job.get("notes", ""))

    def _on_ok(self) -> None:
        if not self.edit_job_number.text().strip():
            QMessageBox.warning(self, "入力エラー", "JOB番号を入力してください。")
            return
        start = self.edit_start_date.text().strip()
        end = self.edit_end_date.text().strip()
        if not start or not end:
            QMessageBox.warning(self, "入力エラー", "開始日と終了日を入力してください。")
            return
        if not self.edit_start_date.isValid() or not self.edit_end_date.isValid():
            QMessageBox.warning(
                self, "入力エラー", "日付はYYYY-MM-DD形式で入力してください。"
            )
            return
        if start > end:
            QMessageBox.warning(self, "入力エラー", "終了日は開始日以降にしてください。")
            return
        self.accept()

    def result_data(self) -> dict:
        return {
            "job_number": self.edit_job_number.text().strip(),
            "start_date": self.edit_start_date.text().strip(),
            "end_date": self.edit_end_date.text().strip(),
            "notes": self.edit_notes.text().strip(),
        }

    def _row(self, label: str, widget: QWidget) -> QHBoxLayout:
        hl = QHBoxLayout()
        lbl = QLabel(label)
        lbl.setFixedWidth(80)
        lbl.setStyleSheet(f"font-size:12px; font-weight:600; color:{_TEXT2};")
        hl.addWidget(lbl)
        hl.addWidget(widget, 1)
        return hl

    @staticmethod
    def _style_input(w: QLineEdit) -> None:
        w.setFixedHeight(30)
        w.setStyleSheet(
            f"QLineEdit {{ border:1px solid {_BORDER}; border-radius:4px;"
            f" padding:4px 8px; font-size:12px; color:{_TEXT}; }}"
            f"QLineEdit:focus {{ border-color:{_ACCENT}; }}"
        )
