from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QFrame,
    QAbstractItemView, QComboBox, QLineEdit, QDialog,
    QDialogButtonBox, QMessageBox,
)
from PySide6.QtCore import Signal, Qt
from PySide6.QtGui import QColor, QFont

from app.data import task_store
from app.config import STATE_LABELS


class AnalysisTargetsState(QWidget):
    go_next = Signal()
    go_back = Signal()

    def __init__(self, data_loader, parent=None):
        super().__init__(parent)
        self.data_loader = data_loader
        self._task: dict = {}
        self._samples: list[dict] = []
        self._readonly = False
        self._edit_mode = False
        self._added_samples: list[str] = []  # free-entry samples
        self._deleted_codes: set[str] = set()
        self._setup_ui()

    def _setup_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(32, 24, 32, 24)
        root.setSpacing(16)

        # Title row
        title_row = QHBoxLayout()
        self.title_lbl = QLabel("分析対象サンプル")
        self.title_lbl.setStyleSheet("font-size:20px; font-weight:bold; color:#e8eaf0;")
        title_row.addWidget(self.title_lbl)
        title_row.addStretch()

        self.edited_badge = QLabel("編集済み")
        self.edited_badge.setStyleSheet("""
            background:rgba(245,166,35,0.1); color:#d97706; border:1px solid #fde68a;
            border-radius:10px; padding:2px 10px; font-size:11px;
        """)
        self.edited_badge.setVisible(False)
        title_row.addWidget(self.edited_badge)

        self.print_btn = QPushButton("印刷")
        self.print_btn.setStyleSheet("""
            QPushButton { background:#1e2535; color:#c8cad4; border:1px solid #334166;
                          padding:6px 14px; border-radius:5px; }
            QPushButton:hover { background:#252d3e; }
        """)
        self.print_btn.clicked.connect(self._print)
        title_row.addWidget(self.print_btn)

        self.edit_btn = QPushButton("編集")
        self.edit_btn.setVisible(False)
        self.edit_btn.setStyleSheet("""
            QPushButton { background:#f59e0b; color:white; border:none;
                          padding:6px 16px; border-radius:5px; }
            QPushButton:hover { background:#d97706; }
        """)
        self.edit_btn.clicked.connect(self._enter_edit_mode)
        title_row.addWidget(self.edit_btn)
        root.addLayout(title_row)

        # Edit toolbar (hidden by default)
        self.edit_toolbar = QFrame()
        self.edit_toolbar.setVisible(False)
        et = QHBoxLayout(self.edit_toolbar)
        et.setContentsMargins(0, 0, 0, 0)
        self.add_sample_btn = QPushButton("＋ サンプル追加")
        self.add_sample_btn.setStyleSheet("""
            QPushButton { background:#10b981; color:white; border:none;
                          padding:6px 14px; border-radius:5px; }
            QPushButton:hover { background:#059669; }
        """)
        self.add_sample_btn.clicked.connect(self._add_sample_dialog)
        et.addWidget(self.add_sample_btn)
        et.addStretch()
        root.addWidget(self.edit_toolbar)

        # Table
        headers = ["JOB番号", "採取日", "サンプル名", "中央値", "最大値", "最小値", ""]
        self.table = QTableWidget(0, len(headers))
        self.table.setHorizontalHeaderLabels(headers)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setAlternatingRowColors(True)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(6, QHeaderView.ResizeMode.Fixed)
        self.table.setColumnWidth(6, 60)
        self.table.setStyleSheet("""
            QTableWidget { border:1px solid #2a3349; border-radius:6px; }
            QHeaderView::section { background:#1e2535; font-weight:bold; color:#c8cad4;
                                    padding:6px; border:none; border-bottom:1px solid #2a3349; }
        """)
        self.table.verticalHeader().setVisible(False)
        root.addWidget(self.table)

        # Navigation buttons
        nav = QHBoxLayout()
        self.back_btn = QPushButton("← 戻る")
        self.back_btn.setStyleSheet("""
            QPushButton { background:#1e2535; color:#c8cad4; border:1px solid #334166;
                          padding:8px 20px; border-radius:6px; font-size:13px; }
            QPushButton:hover { background:#252d3e; }
        """)
        self.back_btn.clicked.connect(self.go_back)
        nav.addWidget(self.back_btn)
        nav.addStretch()
        self.next_btn = QPushButton("次へ →")
        self.next_btn.setStyleSheet("""
            QPushButton { background:#4a8cff; color:white; border:none;
                          padding:8px 24px; border-radius:6px; font-size:13px; font-weight:bold; }
            QPushButton:hover { background:#3a7eff; }
        """)
        self.next_btn.clicked.connect(self._go_next)
        nav.addWidget(self.next_btn)
        root.addLayout(nav)

    # ── Public API ────────────────────────────────────────────────────────────

    def load_task(self, task: dict, readonly: bool = False):
        self._task = task
        self._readonly = readonly
        self._edit_mode = False
        self._deleted_codes = set()
        self._added_samples = []
        self.edited_badge.setVisible(False)

        hg_code = task.get("holder_group_code", "")
        jobs = task.get("job_numbers", [])
        task_name = task.get("task_name", "")
        self.title_lbl.setText(f"分析対象  —  {task_name}")

        # Load samples from CSV
        self._samples = self.data_loader.get_analysis_targets(hg_code, jobs)

        # Apply saved state
        sd = task.get("state_data", {}).get("analysis_targets", {})
        if sd.get("deleted_codes"):
            self._deleted_codes = set(sd["deleted_codes"])
        if sd.get("added_samples"):
            self._added_samples = sd["added_samples"]

        self._set_editable(False)
        if readonly:
            self.edit_btn.setVisible(False)
        elif task.get("current_state") != "analysis_targets":
            self.edit_btn.setVisible(True)
        else:
            self._set_editable(True)

        self._refresh_table()

    # ── Internal ──────────────────────────────────────────────────────────────

    def _enter_edit_mode(self):
        self._edit_mode = True
        self._set_editable(True)
        self.edit_btn.setVisible(False)

    def _set_editable(self, editable: bool):
        self._edit_mode = editable
        self.edit_toolbar.setVisible(editable)
        self._refresh_table()

    def _refresh_table(self):
        self.table.setRowCount(0)
        visible = [s for s in self._samples
                   if s["valid_sample_set_code"] not in self._deleted_codes]
        for s in visible:
            self._add_row(s, free=False)
        for name in self._added_samples:
            self._add_row({"valid_sample_set_code": f"FREE_{name}",
                           "valid_sample_display_name": name,
                           "sample_job_number": "",
                           "sample_sampling_date": "",
                           "median": None, "max": None, "min": None}, free=True)

    def _add_row(self, s: dict, free: bool):
        row = self.table.rowCount()
        self.table.insertRow(row)
        median = f"{s['median']:.3g}" if s.get("median") is not None else "—"
        max_v  = f"{s['max']:.3g}"    if s.get("max")    is not None else "—"
        min_v  = f"{s['min']:.3g}"    if s.get("min")    is not None else "—"

        vals = [
            s.get("sample_job_number", ""),
            s.get("sample_sampling_date", ""),
            s.get("valid_sample_display_name", ""),
            median, max_v, min_v,
        ]
        for col, v in enumerate(vals):
            item = QTableWidgetItem(str(v))
            item.setData(Qt.ItemDataRole.UserRole, s["valid_sample_set_code"])
            if free:
                item.setForeground(QColor("#7c3aed"))
            self.table.setItem(row, col, item)

        # Delete button
        if self._edit_mode:
            del_btn = QPushButton("削除")
            del_btn.setStyleSheet("""
                QPushButton { background:#fee2e2; color:#dc2626; border:none;
                              padding:2px 8px; border-radius:4px; font-size:11px; }
                QPushButton:hover { background:#fecaca; }
            """)
            code = s["valid_sample_set_code"]
            del_btn.clicked.connect(lambda _=False, c=code, f=free: self._delete_row(c, f))
            self.table.setCellWidget(row, 6, del_btn)

    def _delete_row(self, code: str, free: bool):
        if free:
            name = code.removeprefix("FREE_")
            if name in self._added_samples:
                self._added_samples.remove(name)
        else:
            self._deleted_codes.add(code)
        self.edited_badge.setVisible(True)
        self._refresh_table()

    def _add_sample_dialog(self):
        dlg = AddSampleDialog(self.data_loader, self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            name = dlg.selected_name()
            if name and name not in self._added_samples:
                self._added_samples.append(name)
                self.edited_badge.setVisible(True)
                self._refresh_table()

    def _go_next(self):
        # Save state
        visible_codes = [
            s["valid_sample_set_code"]
            for s in self._samples
            if s["valid_sample_set_code"] not in self._deleted_codes
        ]
        # Free samples don't have a real code for downstream use
        state_data = {
            "valid_sample_set_codes": visible_codes,
            "deleted_codes": list(self._deleted_codes),
            "added_samples": self._added_samples,
            "completed": True,
        }

        task_id = self._task["task_id"]
        current = self._task.get("current_state", "analysis_targets")

        if self._edit_mode and current not in ("analysis_targets", "task_setup"):
            reply = QMessageBox.question(
                self,
                "確認",
                "分析対象を変更すると、以降のステートのデータが初期化されます。\n続行しますか？",
                QMessageBox.StandardButton.Ok | QMessageBox.StandardButton.Cancel,
            )
            if reply != QMessageBox.StandardButton.Ok:
                return
            task_store.invalidate_after(task_id, "analysis_targets")

        task_store.update_task_state(task_id, "analysis_targets", state_data)
        if current == "analysis_targets":
            task_store.update_task_state(task_id, "analysis")
        self._task = task_store.get_task(task_id)
        self.go_next.emit()

    def _print(self):
        QMessageBox.information(self, "印刷", "印刷機能はデモ版では省略しています。")


class AddSampleDialog(QDialog):
    def __init__(self, data_loader, parent=None):
        super().__init__(parent)
        self.setWindowTitle("サンプル追加")
        self.setFixedSize(400, 220)
        self._name = ""

        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        layout.addWidget(QLabel("サンプル名をリストから選択、または自由記入してください。"))

        self.combo = QComboBox()
        samples = data_loader.get_valid_samples()
        self.combo.addItem("")
        for s in samples:
            self.combo.addItem(s["display_name"], s["set_code"])
        layout.addWidget(self.combo)

        layout.addWidget(QLabel("または自由記入:"))
        self.line = QLineEdit()
        self.line.setPlaceholderText("サンプル名を入力")
        layout.addWidget(self.line)

        btns = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        btns.accepted.connect(self._accept)
        btns.rejected.connect(self.reject)
        layout.addWidget(btns)

    def _accept(self):
        free = self.line.text().strip()
        if free:
            self._name = free
        else:
            self._name = self.combo.currentText()
        self.accept()

    def selected_name(self) -> str:
        return self._name
