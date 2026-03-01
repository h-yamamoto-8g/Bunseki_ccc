from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame,
)
from PySide6.QtCore import Signal, Qt

from app.config import STATE_LABELS


class CompletedState(QWidget):
    go_list = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(32, 32, 32, 32)
        root.setSpacing(24)
        root.setAlignment(Qt.AlignmentFlag.AlignTop)

        card = QFrame()
        card.setStyleSheet("""
            QFrame { background:#161b27; border:1px solid #2a3349; border-radius:12px; }
        """)
        cl = QVBoxLayout(card)
        cl.setContentsMargins(48, 48, 48, 48)
        cl.setSpacing(16)
        cl.setAlignment(Qt.AlignmentFlag.AlignCenter)

        icon = QLabel("✓")
        icon.setStyleSheet("""
            color:#10b981; font-size:56px; font-weight:bold;
        """)
        icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        cl.addWidget(icon)

        done_lbl = QLabel("タスクが完了しました")
        done_lbl.setStyleSheet("font-size:22px; font-weight:bold; color:#e8eaf0;")
        done_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        cl.addWidget(done_lbl)

        self.summary_lbl = QLabel()
        self.summary_lbl.setStyleSheet("color:#8b93a8; font-size:13px; line-height:1.6;")
        self.summary_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.summary_lbl.setWordWrap(True)
        cl.addWidget(self.summary_lbl)

        back_btn = QPushButton("タスク一覧に戻る")
        back_btn.setStyleSheet("""
            QPushButton { background:#4a8cff; color:white; border:none;
                          padding:10px 28px; border-radius:6px; font-size:14px; font-weight:bold; }
            QPushButton:hover { background:#3a7eff; }
        """)
        back_btn.clicked.connect(self.go_list)
        cl.addWidget(back_btn, alignment=Qt.AlignmentFlag.AlignCenter)

        root.addWidget(card)

    def load_task(self, task: dict):
        created = task.get("created_at", "")[:16].replace("T", " ")
        updated = task.get("updated_at", "")[:16].replace("T", " ")
        holder = task.get("holder_group_name", "")
        jobs = ", ".join(task.get("job_numbers", []))
        creator = task.get("created_by", "")

        # Count analysis items
        vsset_codes = (
            task.get("state_data", {})
            .get("analysis_targets", {})
            .get("valid_sample_set_codes", [])
        )
        n_samples = len(vsset_codes)

        self.summary_lbl.setText(
            f"タスク名: {task.get('task_name','')}\n"
            f"ホルダグループ: {holder}　JOB番号: {jobs}\n"
            f"担当者: {creator}　分析サンプル数: {n_samples} 件\n"
            f"起票日時: {created}　完了日時: {updated}"
        )
