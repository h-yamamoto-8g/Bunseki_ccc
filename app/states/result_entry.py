from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame,
)
from PySide6.QtCore import Signal, Qt

from app.data import task_store


class ResultEntryState(QWidget):
    go_next = Signal()
    go_back = Signal()

    def __init__(self, data_loader, parent=None):
        super().__init__(parent)
        self.data_loader = data_loader
        self._task: dict = {}
        self._setup_ui()

    def _setup_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(32, 24, 32, 24)
        root.setSpacing(24)

        self.title_lbl = QLabel("データ入力")
        self.title_lbl.setStyleSheet("font-size:20px; font-weight:bold; color:#1e293b;")
        root.addWidget(self.title_lbl)

        # Info card
        card = QFrame()
        card.setStyleSheet("""
            QFrame { background:white; border:1px solid #e2e8f0; border-radius:8px; }
        """)
        cl = QVBoxLayout(card)
        cl.setContentsMargins(32, 32, 32, 32)
        cl.setSpacing(16)

        msg = QLabel("通常のデータ入力を行なってください。")
        msg.setStyleSheet("font-size:15px; color:#374151;")
        msg.setAlignment(Qt.AlignmentFlag.AlignCenter)
        cl.addWidget(msg)

        sub = QLabel("Lab-Aid でデータ入力が完了したら「入力完了」ボタンを押してください。")
        sub.setStyleSheet("font-size:13px; color:#6b7280;")
        sub.setAlignment(Qt.AlignmentFlag.AlignCenter)
        sub.setWordWrap(True)
        cl.addWidget(sub)

        labaid_btn = QPushButton("Lab-Aid の起動")
        labaid_btn.setFixedWidth(180)
        labaid_btn.setStyleSheet("""
            QPushButton { background:#7c3aed; color:white; border:none;
                          padding:10px 20px; border-radius:6px; font-size:13px; }
            QPushButton:hover { background:#6d28d9; }
        """)
        labaid_btn.clicked.connect(self._launch_labaid)
        cl.addWidget(labaid_btn, alignment=Qt.AlignmentFlag.AlignHCenter)

        root.addWidget(card)

        # Navigation
        nav = QHBoxLayout()
        self.back_btn = QPushButton("← 戻る")
        self.back_btn.setStyleSheet("""
            QPushButton { background:#f1f5f9; color:#374151; border:1px solid #d1d5db;
                          padding:8px 20px; border-radius:6px; font-size:13px; }
            QPushButton:hover { background:#e2e8f0; }
        """)
        self.back_btn.clicked.connect(self.go_back)
        nav.addWidget(self.back_btn)
        nav.addStretch()
        self.done_btn = QPushButton("入力完了 →")
        self.done_btn.setStyleSheet("""
            QPushButton { background:#2563eb; color:white; border:none;
                          padding:8px 24px; border-radius:6px; font-size:13px; font-weight:bold; }
            QPushButton:hover { background:#1d4ed8; }
        """)
        self.done_btn.clicked.connect(self._complete)
        nav.addWidget(self.done_btn)
        root.addLayout(nav)
        root.addStretch()

    def load_task(self, task: dict, readonly: bool = False):
        self._task = task
        task_name = task.get("task_name", "")
        self.title_lbl.setText(f"データ入力  —  {task_name}")
        self.done_btn.setVisible(not readonly)
        self.back_btn.setVisible(True)

    def _launch_labaid(self):
        from PySide6.QtWidgets import QMessageBox
        QMessageBox.information(self, "Lab-Aid", "Lab-Aidを起動します（デモ）")

    def _complete(self):
        task_id = self._task["task_id"]
        task_store.update_task_state(task_id, "result_entry", {"completed": True})
        task_store.update_task_state(task_id, "result_verification")
        self._task = task_store.get_task(task_id)
        self.go_next.emit()
