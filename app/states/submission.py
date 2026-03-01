from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QTextEdit, QFileDialog, QScrollArea, QComboBox,
)
from PySide6.QtCore import Signal, Qt

from app.data import task_store
from app.config import CURRENT_USER

DEMO_USERS = ["デモユーザー", "山田 太郎", "鈴木 花子", "田中 一郎"]


class SubmissionState(QWidget):
    go_next = Signal()
    go_back = Signal()

    def __init__(self, data_loader, parent=None):
        super().__init__(parent)
        self.data_loader = data_loader
        self._task: dict = {}
        self._readonly = False
        self._attachments: list[str] = []
        self._is_reviewer = False
        self._setup_ui()

    def _setup_ui(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        outer.addWidget(scroll)

        container = QWidget()
        scroll.setWidget(container)
        root = QVBoxLayout(container)
        root.setContentsMargins(32, 24, 32, 24)
        root.setSpacing(20)

        self.title_lbl = QLabel("回覧")
        self.title_lbl.setStyleSheet("font-size:20px; font-weight:bold; color:#e8eaf0;")
        root.addWidget(self.title_lbl)

        # Circulation flow
        flow_frame = self._card()
        fl = QVBoxLayout(flow_frame)
        fl.addWidget(self._section_lbl("回覧フロー"))
        self.flow_lbl = QLabel()
        self.flow_lbl.setStyleSheet("color:#c8cad4; font-size:13px;")
        fl.addWidget(self.flow_lbl)

        # Reviewer selector
        reviewer_row = QHBoxLayout()
        reviewer_row.addWidget(QLabel("確認者を選択:"))
        self.reviewer_combo = QComboBox()
        self.reviewer_combo.setMinimumWidth(180)
        for u in DEMO_USERS:
            if u != CURRENT_USER:
                self.reviewer_combo.addItem(u)
        reviewer_row.addWidget(self.reviewer_combo)
        reviewer_row.addStretch()
        fl.addLayout(reviewer_row)
        root.addWidget(flow_frame)

        # Attachments
        att_frame = self._card()
        al = QVBoxLayout(att_frame)
        al.addWidget(self._section_lbl("添付ファイル"))
        self.att_label = QLabel("（なし）")
        self.att_label.setStyleSheet("color:#8b93a8; font-size:13px;")
        al.addWidget(self.att_label)
        att_btn = QPushButton("ファイルを追加")
        att_btn.setStyleSheet("""
            QPushButton { background:#1e2535; color:#c8cad4; border:1px solid #334166;
                          padding:6px 14px; border-radius:5px; font-size:13px; }
            QPushButton:hover { background:#252d3e; }
        """)
        att_btn.clicked.connect(self._add_attachment)
        al.addWidget(att_btn)
        root.addWidget(att_frame)

        # Comment
        cmt_frame = self._card()
        cmtl = QVBoxLayout(cmt_frame)
        cmtl.addWidget(self._section_lbl("コメント"))
        self.comment_edit = QTextEdit()
        self.comment_edit.setFixedHeight(100)
        self.comment_edit.setPlaceholderText("コメントを入力してください...")
        self.comment_edit.setStyleSheet("border:1px solid #334166; border-radius:5px; font-size:13px;")
        cmtl.addWidget(self.comment_edit)
        root.addWidget(cmt_frame)

        # Reviewer actions (hidden initially)
        self.reviewer_frame = self._card()
        rl = QVBoxLayout(self.reviewer_frame)
        rl.addWidget(self._section_lbl("確認者操作"))
        rl_btns = QHBoxLayout()
        self.next_reviewer_btn = QPushButton("次へ回覧")
        self.next_reviewer_btn.setStyleSheet("""
            QPushButton { background:#f59e0b; color:white; border:none;
                          padding:8px 20px; border-radius:6px; font-size:13px; }
            QPushButton:hover { background:#d97706; }
        """)
        self.next_reviewer_btn.clicked.connect(self._next_reviewer)
        rl_btns.addWidget(self.next_reviewer_btn)
        self.end_btn = QPushButton("終了")
        self.end_btn.setStyleSheet("""
            QPushButton { background:#10b981; color:white; border:none;
                          padding:8px 20px; border-radius:6px; font-size:13px; font-weight:bold; }
            QPushButton:hover { background:#059669; }
        """)
        self.end_btn.clicked.connect(self._complete)
        rl_btns.addWidget(self.end_btn)
        rl_btns.addStretch()
        rl.addLayout(rl_btns)
        self.reviewer_frame.setVisible(False)
        root.addWidget(self.reviewer_frame)

        # Navigation
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
        self.send_btn = QPushButton("回覧送信")
        self.send_btn.setStyleSheet("""
            QPushButton { background:#4a8cff; color:white; border:none;
                          padding:8px 24px; border-radius:6px; font-size:13px; font-weight:bold; }
            QPushButton:hover { background:#3a7eff; }
        """)
        self.send_btn.clicked.connect(self._send)
        nav.addWidget(self.send_btn)
        root.addLayout(nav)
        root.addStretch()

    def _card(self) -> QFrame:
        f = QFrame()
        f.setStyleSheet("QFrame { background:#161b27; border:1px solid #2a3349; border-radius:8px; }")
        return f

    def _section_lbl(self, text: str) -> QLabel:
        l = QLabel(text)
        l.setStyleSheet("font-weight:bold; font-size:13px; color:#c8cad4; margin-bottom:6px;")
        return l

    def load_task(self, task: dict, readonly: bool = False):
        self._task = task
        self._readonly = readonly
        task_name = task.get("task_name", "")
        self.title_lbl.setText(f"回覧  —  {task_name}")

        sd = task.get("state_data", {}).get("submission", {})
        reviewer = sd.get("reviewer", "未定")
        self.flow_lbl.setText(
            f"起票者: {task.get('created_by', '—')}　→　確認者: {reviewer}"
        )

        # Restore attachments and comment
        self._attachments = list(sd.get("attachments", []))
        self._refresh_attachments()
        comment = sd.get("comment", "")
        self.comment_edit.setPlainText(comment)

        # Show/hide reviewer actions depending on status
        self._is_reviewer = task.get("status") == "回覧中" and task.get("assigned_to") == CURRENT_USER
        self.reviewer_frame.setVisible(self._is_reviewer or readonly)
        self.send_btn.setVisible(not self._is_reviewer and not readonly)
        self.comment_edit.setReadOnly(readonly)

    def _add_attachment(self):
        files, _ = QFileDialog.getOpenFileNames(self, "ファイルを選択")
        for f in files:
            if f not in self._attachments:
                self._attachments.append(f)
        self._refresh_attachments()

    def _refresh_attachments(self):
        if self._attachments:
            self.att_label.setText("\n".join(self._attachments))
        else:
            self.att_label.setText("（なし）")

    def _send(self):
        reviewer = self.reviewer_combo.currentText()
        state_data = {
            "reviewer": reviewer,
            "comment": self.comment_edit.toPlainText(),
            "attachments": self._attachments,
            "completed": True,
        }
        task_id = self._task["task_id"]
        task_store.update_task_state(task_id, "submission", state_data)
        # Mark as 回覧中
        from app.data import task_store as ts
        ts.update_task_field(task_id, status="回覧中")
        self._task = task_store.get_task(task_id)
        self.flow_lbl.setText(
            f"起票者: {self._task.get('created_by','—')}　→　確認者: {reviewer}"
        )
        self.send_btn.setEnabled(False)
        from PySide6.QtWidgets import QMessageBox
        QMessageBox.information(self, "送信完了",
                                f"確認者 {reviewer} に回覧しました。\n（デモ: Outlook起動は省略）")

    def _next_reviewer(self):
        reviewer = self.reviewer_combo.currentText()
        from PySide6.QtWidgets import QMessageBox
        QMessageBox.information(self, "回覧", f"次の確認者 {reviewer} に回覧しました（デモ）。")

    def _complete(self):
        task_id = self._task["task_id"]
        task_store.update_task_state(task_id, "completed", {"completed": True})
        self._task = task_store.get_task(task_id)
        self.go_next.emit()
