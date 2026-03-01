from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QCheckBox, QScrollArea, QGroupBox,
)
from PySide6.QtCore import Signal, Qt

from app.data import task_store


# Demo links/checklists — in production these would come from config JSON
DEMO_LINKS = [
    {"label": "分析基準書", "url": "https://example.com/manual", "type": "web"},
    {"label": "関連マニュアル A", "url": "https://example.com/manual-a", "type": "web"},
    {"label": "業務ツール Lab-Aid", "url": "", "type": "file"},
]

PRE_CHECKS = [
    "試薬の有効期限を確認した",
    "装置の校正が完了している",
    "サンプル容器にラベルが正しく記載されている",
    "ブランクサンプルを準備した",
]

POST_CHECKS = [
    "全サンプルの測定が完了した",
    "装置のログを保存した",
    "試薬の使用量を記録した",
    "廃液を適切に処理した",
]


class AnalysisState(QWidget):
    go_next = Signal()
    go_back = Signal()

    def __init__(self, data_loader, parent=None):
        super().__init__(parent)
        self.data_loader = data_loader
        self._task: dict = {}
        self._readonly = False
        self._pre_checks: list[QCheckBox] = []
        self._post_checks: list[QCheckBox] = []
        self._setup_ui()

    def _setup_ui(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        outer.addWidget(scroll)

        container = QWidget()
        container.setStyleSheet("background: #161b27;")
        scroll.setWidget(container)
        root = QVBoxLayout(container)
        root.setContentsMargins(32, 24, 32, 24)
        root.setSpacing(20)

        self.title_lbl = QLabel("分析準備")
        self.title_lbl.setStyleSheet("font-size:20px; font-weight:bold; color:#e8eaf0;")
        root.addWidget(self.title_lbl)

        # Links section
        links_group = self._section("参考リンク・ツール")
        links_layout = QVBoxLayout()
        links_layout.setSpacing(8)
        for link in DEMO_LINKS:
            row = QHBoxLayout()
            lbl = QLabel(f"• {link['label']}")
            lbl.setStyleSheet("color:#c8cad4; font-size:13px;")
            row.addWidget(lbl)
            btn = QPushButton("開く")
            btn.setFixedWidth(60)
            btn.setStyleSheet("""
                QPushButton { background:#eff6ff; color:#4a8cff; border:1px solid #bfdbfe;
                              padding:3px 10px; border-radius:4px; font-size:12px; }
                QPushButton:hover { background:#dbeafe; }
            """)
            url = link["url"]
            btn.clicked.connect(lambda _=False, u=url: self._open_link(u))
            row.addWidget(btn)
            row.addStretch()
            links_layout.addLayout(row)
        links_group.setLayout(links_layout)
        root.addWidget(links_group)

        # Pre-analysis checklist
        pre_group = self._section("分析前確認リスト")
        pre_layout = QVBoxLayout()
        pre_layout.setSpacing(8)
        all_pre_btn = QPushButton("一括チェック")
        all_pre_btn.setStyleSheet("""
            QPushButton { background:#f0fdf4; color:#166534; border:1px solid #bbf7d0;
                          padding:4px 12px; border-radius:4px; font-size:12px; }
            QPushButton:hover { background:#dcfce7; }
        """)
        all_pre_btn.clicked.connect(lambda: self._check_all(self._pre_checks))
        pre_layout.addWidget(all_pre_btn)
        self._pre_checks = []
        for item in PRE_CHECKS:
            cb = QCheckBox(item)
            cb.setStyleSheet("font-size:13px; color:#c8cad4; padding:2px 0;")
            cb.stateChanged.connect(self._update_finish_btn)
            pre_layout.addWidget(cb)
            self._pre_checks.append(cb)
        pre_group.setLayout(pre_layout)
        root.addWidget(pre_group)

        # Post-analysis checklist
        post_group = self._section("分析後確認リスト")
        post_layout = QVBoxLayout()
        post_layout.setSpacing(8)
        all_post_btn = QPushButton("一括チェック")
        all_post_btn.setStyleSheet("""
            QPushButton { background:#f0fdf4; color:#166534; border:1px solid #bbf7d0;
                          padding:4px 12px; border-radius:4px; font-size:12px; }
            QPushButton:hover { background:#dcfce7; }
        """)
        all_post_btn.clicked.connect(lambda: self._check_all(self._post_checks))
        post_layout.addWidget(all_post_btn)
        self._post_checks = []
        for item in POST_CHECKS:
            cb = QCheckBox(item)
            cb.setStyleSheet("font-size:13px; color:#c8cad4; padding:2px 0;")
            cb.stateChanged.connect(self._update_finish_btn)
            post_layout.addWidget(cb)
            self._post_checks.append(cb)
        post_group.setLayout(post_layout)
        root.addWidget(post_group)

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
        self.finish_btn = QPushButton("分析終了 →")
        self.finish_btn.setEnabled(False)
        self.finish_btn.setStyleSheet("""
            QPushButton { background:#4a8cff; color:white; border:none;
                          padding:8px 24px; border-radius:6px; font-size:13px; font-weight:bold; }
            QPushButton:hover { background:#3a7eff; }
            QPushButton:disabled { background:#93c5fd; }
        """)
        self.finish_btn.clicked.connect(self._finish)
        nav.addWidget(self.finish_btn)
        root.addLayout(nav)
        root.addStretch()

    def _section(self, title: str) -> QGroupBox:
        group = QGroupBox(title)
        group.setStyleSheet("""
            QGroupBox { font-weight:bold; font-size:13px; color:#c8cad4;
                         border:1px solid #2a3349; border-radius:8px; margin-top:8px; }
            QGroupBox::title { subcontrol-origin:margin; left:12px; padding:0 4px; }
        """)
        return group

    def load_task(self, task: dict, readonly: bool = False):
        self._task = task
        self._readonly = readonly
        task_name = task.get("task_name", "")
        self.title_lbl.setText(f"分析準備  —  {task_name}")

        # Restore saved checks
        sd = task.get("state_data", {}).get("analysis", {})
        pre_saved = sd.get("pre_checks", [False] * len(PRE_CHECKS))
        post_saved = sd.get("post_checks", [False] * len(POST_CHECKS))

        for cb, val in zip(self._pre_checks, pre_saved):
            cb.setChecked(val)
            cb.setEnabled(not readonly)
        for cb, val in zip(self._post_checks, post_saved):
            cb.setChecked(val)
            cb.setEnabled(not readonly)

        self.finish_btn.setVisible(not readonly)
        self._update_finish_btn()

    def _check_all(self, checkboxes: list[QCheckBox]):
        for cb in checkboxes:
            cb.setChecked(True)

    def _update_finish_btn(self):
        all_checked = all(cb.isChecked() for cb in self._pre_checks + self._post_checks)
        self.finish_btn.setEnabled(all_checked)

    def _open_link(self, url: str):
        if url:
            from PySide6.QtGui import QDesktopServices
            from PySide6.QtCore import QUrl
            QDesktopServices.openUrl(QUrl(url))

    def _finish(self):
        state_data = {
            "pre_checks": [cb.isChecked() for cb in self._pre_checks],
            "post_checks": [cb.isChecked() for cb in self._post_checks],
            "completed": True,
        }
        task_id = self._task["task_id"]
        task_store.update_task_state(task_id, "analysis", state_data)
        task_store.update_task_state(task_id, "result_entry")
        self._task = task_store.get_task(task_id)
        self.go_next.emit()
