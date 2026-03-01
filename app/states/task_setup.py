from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QComboBox, QLineEdit, QFrame, QScrollArea, QSizePolicy,
    QMessageBox,
)
from PySide6.QtCore import Signal, Qt
from PySide6.QtGui import QColor

from app.data import task_store
from app.config import CURRENT_USER


class TaskSetupState(QWidget):
    submitted = Signal(dict)   # emits new task dict
    cancelled = Signal()

    def __init__(self, data_loader, parent=None):
        super().__init__(parent)
        self.data_loader = data_loader
        self._task_id: str | None = None
        self._readonly = False
        self._edit_mode = False
        self._job_numbers: list[str] = []
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 24, 32, 24)
        layout.setSpacing(16)

        # Title row
        title_row = QHBoxLayout()
        self.title_lbl = QLabel("新規起票")
        self.title_lbl.setStyleSheet("font-size:20px; font-weight:bold; color:#e8eaf0;")
        title_row.addWidget(self.title_lbl)
        title_row.addStretch()
        self.edit_btn = QPushButton("編集")
        self.edit_btn.setVisible(False)
        self.edit_btn.setStyleSheet("""
            QPushButton { background:#f59e0b; color:white; border:none;
                          padding:6px 16px; border-radius:5px; }
            QPushButton:hover { background:#d97706; }
        """)
        self.edit_btn.clicked.connect(self._enter_edit_mode)
        title_row.addWidget(self.edit_btn)
        layout.addLayout(title_row)

        # Form card
        card = QFrame()
        card.setStyleSheet("""
            QFrame { background:#161b27; border:1px solid #2a3349;
                     border-radius:8px; }
        """)
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(24, 20, 24, 20)
        card_layout.setSpacing(18)

        # Holder group
        card_layout.addWidget(self._field_label("ホルダグループ *"))
        self.hg_combo = QComboBox()
        self.hg_combo.setMinimumHeight(36)
        self.hg_combo.setStyleSheet("""
            QComboBox { border:1px solid #334166; border-radius:5px;
                        padding:4px 8px; font-size:13px; background:#161b27; color:#e8eaf0; }
            QComboBox:disabled { background:#1e2535; color:#5a6278; }
            QComboBox QAbstractItemView { color:#e8eaf0; background:#161b27;
                selection-background-color:#4a8cff; selection-color:white; }
        """)
        card_layout.addWidget(self.hg_combo)

        # JOB numbers
        card_layout.addWidget(self._field_label("JOB番号"))
        job_row = QHBoxLayout()
        self.job_input = QLineEdit()
        self.job_input.setPlaceholderText("JOB番号を入力")
        self.job_input.setMinimumHeight(36)
        self.job_input.setStyleSheet("""
            QLineEdit { border:1px solid #334166; border-radius:5px;
                        padding:4px 8px; font-size:13px; }
            QLineEdit:disabled { background:#1e2535; color:#5a6278; }
        """)
        job_row.addWidget(self.job_input)
        self.add_job_btn = QPushButton("＋ 追加")
        self.add_job_btn.setMinimumHeight(36)
        self.add_job_btn.setStyleSheet("""
            QPushButton { background:#252d3e; color:#c8cad4; border:none;
                          padding:4px 14px; border-radius:5px; font-size:13px; }
            QPushButton:hover { background:#cbd5e1; }
            QPushButton:disabled { background:#1e2535; color:#5a6278; }
        """)
        self.add_job_btn.clicked.connect(self._add_job)
        job_row.addWidget(self.add_job_btn)
        card_layout.addLayout(job_row)

        # JOB tags area
        self.tags_frame = QFrame()
        self.tags_frame.setStyleSheet("QFrame { border:none; }")
        self.tags_layout = QHBoxLayout(self.tags_frame)
        self.tags_layout.setContentsMargins(0, 0, 0, 0)
        self.tags_layout.setSpacing(6)
        self.tags_layout.addStretch()
        card_layout.addWidget(self.tags_frame)

        layout.addWidget(card)

        # Buttons
        btn_row = QHBoxLayout()
        btn_row.addStretch()
        self.cancel_btn = QPushButton("キャンセル")
        self.cancel_btn.setStyleSheet("""
            QPushButton { background:#1e2535; color:#c8cad4; border:1px solid #334166;
                          padding:8px 20px; border-radius:6px; font-size:13px; }
            QPushButton:hover { background:#252d3e; }
        """)
        self.cancel_btn.clicked.connect(self.cancelled)
        btn_row.addWidget(self.cancel_btn)
        self.submit_btn = QPushButton("起票　→")
        self.submit_btn.setStyleSheet("""
            QPushButton { background:#4a8cff; color:white; border:none;
                          padding:8px 24px; border-radius:6px; font-size:13px; font-weight:bold; }
            QPushButton:hover { background:#3a7eff; }
        """)
        self.submit_btn.clicked.connect(self._submit)
        btn_row.addWidget(self.submit_btn)
        layout.addLayout(btn_row)
        layout.addStretch()

        self._load_holder_groups()

    def _field_label(self, text: str) -> QLabel:
        lbl = QLabel(text)
        lbl.setStyleSheet("font-size:13px; font-weight:bold; color:#c8cad4;")
        return lbl

    def _load_holder_groups(self):
        self.hg_combo.clear()
        self._hg_list = self.data_loader.get_holder_groups()
        for g in self._hg_list:
            self.hg_combo.addItem(g["holder_group_name"], g["holder_group_code"])

    # ── Public API ────────────────────────────────────────────────────────────

    def open_new(self):
        """Open for new task creation."""
        self._task_id = None
        self._readonly = False
        self._edit_mode = False
        self._job_numbers = []
        self.title_lbl.setText("新規起票")
        self.edit_btn.setVisible(False)
        self.submit_btn.setVisible(True)
        self.cancel_btn.setVisible(True)
        self._load_holder_groups()
        self.job_input.clear()
        self._refresh_tags()
        self._set_editable(True)

    def open_existing(self, task: dict, readonly: bool = False):
        """Open for viewing/editing an existing task."""
        self._task_id = task["task_id"]
        self._readonly = readonly
        self._edit_mode = False
        sd = task.get("state_data", {}).get("task_setup", {})
        self.title_lbl.setText("起票")

        # Load holder groups and select current
        self._load_holder_groups()
        hg_code = sd.get("holder_group_code", task.get("holder_group_code", ""))
        for i in range(self.hg_combo.count()):
            if self.hg_combo.itemData(i) == hg_code:
                self.hg_combo.setCurrentIndex(i)
                break

        self._job_numbers = list(sd.get("job_numbers", task.get("job_numbers", [])))
        self.job_input.clear()
        self._refresh_tags()

        if readonly:
            self._set_editable(False)
            self.edit_btn.setVisible(False)
            self.submit_btn.setVisible(False)
            self.cancel_btn.setText("閉じる")
        else:
            # Already progressed — show read-only with edit button
            self._set_editable(False)
            self.edit_btn.setVisible(True)
            self.submit_btn.setVisible(False)
            self.cancel_btn.setText("戻る")

    # ── Internal ──────────────────────────────────────────────────────────────

    def _set_editable(self, editable: bool):
        self.hg_combo.setEnabled(editable)
        self.job_input.setEnabled(editable)
        self.add_job_btn.setEnabled(editable)
        self._refresh_tags()

    def _enter_edit_mode(self):
        self._edit_mode = True
        self._set_editable(True)
        self.edit_btn.setVisible(False)
        self.submit_btn.setText("保存")
        self.submit_btn.setVisible(True)
        self.cancel_btn.setText("キャンセル")

    def _add_job(self):
        txt = self.job_input.text().strip()
        if txt and txt not in self._job_numbers:
            self._job_numbers.append(txt)
            self.job_input.clear()
            self._refresh_tags()

    def _refresh_tags(self):
        # Clear existing tags
        while self.tags_layout.count() > 1:
            item = self.tags_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        editable = self.hg_combo.isEnabled()
        for job in self._job_numbers:
            tag = self._make_tag(job, editable)
            self.tags_layout.insertWidget(self.tags_layout.count() - 1, tag)

    def _make_tag(self, text: str, removable: bool) -> QFrame:
        frame = QFrame()
        frame.setStyleSheet("""
            QFrame { background:rgba(74,140,255,0.15); border-radius:4px; border:none; }
        """)
        hl = QHBoxLayout(frame)
        hl.setContentsMargins(10, 4, 6, 4)
        hl.setSpacing(4)
        lbl = QLabel(text)
        lbl.setStyleSheet("color:#4a8cff; font-size:12px; font-weight:500;")
        hl.addWidget(lbl)
        if removable:
            rm = QPushButton("✕")
            rm.setFixedSize(18, 18)
            rm.setStyleSheet("""
                QPushButton { background:transparent; color:#4a8cff; border:none; font-size:11px; }
                QPushButton:hover { color:#e85454; }
            """)
            rm.clicked.connect(lambda _=False, t=text: self._remove_job(t))
            hl.addWidget(rm)
        return frame

    def _remove_job(self, text: str):
        if text in self._job_numbers:
            self._job_numbers.remove(text)
            self._refresh_tags()

    def _submit(self):
        hg_code = self.hg_combo.currentData()
        hg_name = self.hg_combo.currentText()
        if not hg_code:
            QMessageBox.warning(self, "入力エラー", "ホルダグループを選択してください。")
            return

        if self._task_id is None:
            # New task
            task = task_store.create_task(hg_code, hg_name, self._job_numbers)
            self.submitted.emit(task)
        else:
            # Update existing (with confirmation if edit mode)
            if self._edit_mode:
                reply = QMessageBox.question(
                    self,
                    "確認",
                    "起票情報を変更すると、以降のステートのデータが初期化されます。\n続行しますか？",
                    QMessageBox.StandardButton.Ok | QMessageBox.StandardButton.Cancel,
                )
                if reply != QMessageBox.StandardButton.Ok:
                    return
                task_store.invalidate_after(self._task_id, "task_setup")
                task_store.update_task_field(
                    self._task_id,
                    holder_group_code=hg_code,
                    holder_group_name=hg_name,
                    job_numbers=self._job_numbers,
                )
                task_store.update_task_state(
                    self._task_id,
                    "task_setup",
                    {
                        "holder_group_code": hg_code,
                        "holder_group_name": hg_name,
                        "job_numbers": self._job_numbers,
                        "completed": True,
                    },
                )
            task = task_store.get_task(self._task_id)
            self.submitted.emit(task)
