"""タスク設定タブ — 分析項目×ステータス別レイアウト。

分析項目（ホルダグループ）ごとに、タスクのステータス別に
設定項目を縦長ブロックで表示する。
"""
from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QFileDialog,
    QFrame,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QTextBrowser,
    QVBoxLayout,
    QWidget,
)

from app.services.hg_config_service import HgConfigService


# ── ステータス定義 ────────────────────────────────────────────────────────────

STATUS_DEFS: list[tuple[str, str]] = [
    ("task_setup",          "起票"),
    ("analysis_targets",    "サンプル"),
    ("analysis",            "分析"),
    ("result_entry",        "入力"),
    ("result_verification", "チェック"),
    ("submission",          "フロー"),
    ("completed",           "終了"),
]


# ── 再利用可能なチェックリストエディタ ─────────────────────────────────────

class _ChecklistEditor(QWidget):
    """チェックリスト項目の追加・削除ができるウィジェット。"""

    def __init__(self, title: str, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._items: list[str] = []
        self._rows: list[QWidget] = []

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)

        lbl = QLabel(title)
        lbl.setStyleSheet("font-weight: 600; font-size: 13px; color: #374151;")
        layout.addWidget(lbl)

        # 項目リスト領域
        self._list_layout = QVBoxLayout()
        self._list_layout.setSpacing(4)
        layout.addLayout(self._list_layout)

        # 追加行
        add_row = QHBoxLayout()
        add_row.setSpacing(6)
        self._input = QLineEdit()
        self._input.setPlaceholderText("項目を入力")
        self._input.setStyleSheet(
            "border: 1px solid #d1d5db; border-radius: 4px; padding: 4px 8px;"
        )
        self._input.returnPressed.connect(self._on_add)
        add_row.addWidget(self._input, 1)

        btn_add = QPushButton("追加")
        btn_add.setFixedHeight(28)
        btn_add.setStyleSheet(
            "background: #3b82f6; color: white; border: none; "
            "border-radius: 4px; padding: 4px 12px; font-weight: 600;"
        )
        btn_add.clicked.connect(self._on_add)
        add_row.addWidget(btn_add)
        layout.addLayout(add_row)

    def set_items(self, items: list[str]) -> None:
        self._items = list(items)
        self._rebuild()

    def get_items(self) -> list[str]:
        return list(self._items)

    def _rebuild(self) -> None:
        for row in self._rows:
            row.deleteLater()
        self._rows.clear()

        for i, text in enumerate(self._items):
            row = QWidget()
            hl = QHBoxLayout(row)
            hl.setContentsMargins(0, 0, 0, 0)
            hl.setSpacing(6)

            lbl = QLabel(f"  {i + 1}. {text}")
            lbl.setStyleSheet("font-size: 13px; color: #334155;")
            hl.addWidget(lbl, 1)

            btn_del = QPushButton("×")
            btn_del.setFixedSize(24, 24)
            btn_del.setCursor(Qt.CursorShape.PointingHandCursor)
            btn_del.setStyleSheet(
                "QPushButton { background: transparent; color: #9ca3af; "
                "border: 1px solid #e5e7eb; border-radius: 4px; font-weight: bold; }"
                "QPushButton:hover { background: #fee2e2; color: #ef4444; "
                "border-color: #fca5a5; }"
            )
            idx = i
            btn_del.clicked.connect(lambda _=False, j=idx: self._on_remove(j))
            hl.addWidget(btn_del)

            self._list_layout.addWidget(row)
            self._rows.append(row)

    def _on_add(self) -> None:
        text = self._input.text().strip()
        if not text:
            return
        self._items.append(text)
        self._input.clear()
        self._rebuild()

    def _on_remove(self, idx: int) -> None:
        if 0 <= idx < len(self._items):
            self._items.pop(idx)
            self._rebuild()


# ── マニュアルセクション ──────────────────────────────────────────────────────

class _ManualSection(QWidget):
    """マニュアルのアップロード・プレビュー・削除ウィジェット。"""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        lbl = QLabel("マニュアル")
        lbl.setStyleSheet("font-weight: 600; font-size: 13px; color: #374151;")
        layout.addWidget(lbl)

        row = QHBoxLayout()
        row.setSpacing(8)

        self.lbl_status = QLabel("未登録")
        self.lbl_status.setStyleSheet("color: #9ca3af; font-size: 13px;")
        row.addWidget(self.lbl_status)
        row.addStretch()

        self.btn_upload = QPushButton("アップロード")
        self.btn_upload.setStyleSheet(
            "background: #3b82f6; color: white; border: none; "
            "border-radius: 4px; padding: 6px 16px; font-weight: 600;"
        )
        row.addWidget(self.btn_upload)

        self.btn_preview = QPushButton("プレビュー")
        self.btn_preview.setStyleSheet(
            "background: #10b981; color: white; border: none; "
            "border-radius: 4px; padding: 6px 16px; font-weight: 600;"
        )
        row.addWidget(self.btn_preview)

        self.btn_delete = QPushButton("削除")
        self.btn_delete.setStyleSheet(
            "background: #ef4444; color: white; border: none; "
            "border-radius: 4px; padding: 6px 16px; font-weight: 600;"
        )
        row.addWidget(self.btn_delete)
        layout.addLayout(row)

    def update_status(self, registered: bool) -> None:
        if registered:
            self.lbl_status.setText("登録済み")
            self.lbl_status.setStyleSheet(
                "color: #059669; font-size: 13px; font-weight: 600;"
            )
        else:
            self.lbl_status.setText("未登録")
            self.lbl_status.setStyleSheet("color: #9ca3af; font-size: 13px;")


# ── ステータスブロック ────────────────────────────────────────────────────────

_BLOCK_STYLE = (
    "QGroupBox { background: #ffffff; border: 1px solid #e5e7eb; "
    "border-radius: 8px; margin-top: 8px; padding: 16px 16px 12px 16px; }"
    "QGroupBox::title { subcontrol-origin: margin; subcontrol-position: top left; "
    "padding: 0 8px; font-weight: 700; font-size: 14px; color: #1f2937; }"
)


def _make_status_block(title: str, widgets: list[QWidget]) -> QGroupBox:
    """ステータス名付きブロックを生成する。"""
    group = QGroupBox(title)
    group.setStyleSheet(_BLOCK_STYLE)
    vl = QVBoxLayout(group)
    vl.setContentsMargins(12, 20, 12, 12)
    vl.setSpacing(16)

    if not widgets:
        lbl = QLabel("設定項目なし")
        lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl.setStyleSheet("color: #9ca3af; font-size: 13px; padding: 12px;")
        vl.addWidget(lbl)
    else:
        for w in widgets:
            vl.addWidget(w)

    return group


# ── メインタブ ─────────────────────────────────────────────────────────────

class HgConfigTab(QWidget):
    """タスク設定タブ — 分析項目×ステータス別レイアウト。"""

    def __init__(
        self,
        hg_config_service: HgConfigService,
        holder_groups: list[dict],
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._service = hg_config_service
        self._holder_groups = holder_groups
        self._current_hg_code: str = ""
        self._build_ui()
        self._connect_signals()
        if holder_groups:
            self._combo.setCurrentIndex(0)
            self._on_hg_changed(0)

    def _build_ui(self) -> None:
        outer = QVBoxLayout(self)
        outer.setContentsMargins(16, 16, 16, 16)
        outer.setSpacing(12)

        # ── ヘッダー行: 分析項目選択 + 保存ボタン ─────────────────────────
        header = QHBoxLayout()
        header.setSpacing(12)

        header.addWidget(QLabel("分析項目:"))
        self._combo = QComboBox()
        self._combo.setMinimumWidth(250)
        for hg in self._holder_groups:
            self._combo.addItem(
                hg.get("holder_group_name", ""),
                hg.get("holder_group_code", ""),
            )
        header.addWidget(self._combo)
        header.addStretch()

        self._btn_save = QPushButton("保存")
        self._btn_save.setStyleSheet(
            "background: #3b82f6; color: white; border: none; "
            "border-radius: 6px; padding: 8px 24px; font-weight: 600;"
        )
        header.addWidget(self._btn_save)
        outer.addLayout(header)

        # ── スクロール領域 ────────────────────────────────────────────────
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)

        content = QWidget()
        self._content_layout = QVBoxLayout(content)
        self._content_layout.setContentsMargins(0, 0, 0, 0)
        self._content_layout.setSpacing(12)

        # ── ステータスごとのブロックを構築 ────────────────────────────────
        # 分析ステータスに設定項目を配置
        self._manual_section = _ManualSection()
        self._pre_editor = _ChecklistEditor("分析前チェックリスト")
        self._post_editor = _ChecklistEditor("分析後チェックリスト")

        # チェックステータスに設定項目を配置
        self._verify_editor = _ChecklistEditor("データ確認チェックリスト")

        # 各ステータスに対応するウィジェットのマッピング
        status_widgets: dict[str, list[QWidget]] = {
            "analysis": [self._manual_section, self._pre_editor, self._post_editor],
            "result_verification": [self._verify_editor],
        }

        for status_id, status_name in STATUS_DEFS:
            widgets = status_widgets.get(status_id, [])
            block = _make_status_block(status_name, widgets)
            self._content_layout.addWidget(block)

        self._content_layout.addStretch()
        scroll.setWidget(content)
        outer.addWidget(scroll, 1)

    def _connect_signals(self) -> None:
        self._combo.currentIndexChanged.connect(self._on_hg_changed)
        self._btn_save.clicked.connect(self._on_save)
        self._manual_section.btn_upload.clicked.connect(self._on_upload)
        self._manual_section.btn_preview.clicked.connect(self._on_preview)
        self._manual_section.btn_delete.clicked.connect(self._on_delete_manual)

    # ── HG 切替 ───────────────────────────────────────────────────────────

    def _on_hg_changed(self, index: int) -> None:
        hg_code = self._combo.itemData(index) or ""
        self._current_hg_code = hg_code
        if not hg_code:
            return
        cfg = self._service.get_config(hg_code)
        self._pre_editor.set_items(cfg.get("pre_checklist", []))
        self._post_editor.set_items(cfg.get("post_checklist", []))
        self._verify_editor.set_items(cfg.get("verify_checklist", []))
        self._manual_section.update_status(cfg.get("has_manual", False))

    # ── 保存 ──────────────────────────────────────────────────────────────

    def _on_save(self) -> None:
        hg_code = self._current_hg_code
        if not hg_code:
            return
        self._service.save_checklists(
            hg_code,
            pre_checklist=self._pre_editor.get_items(),
            post_checklist=self._post_editor.get_items(),
            verify_checklist=self._verify_editor.get_items(),
        )
        hg_name = self._combo.currentText()
        QMessageBox.information(
            self, "保存完了", f"「{hg_name}」の設定を保存しました。"
        )

    # ── マニュアル操作 ────────────────────────────────────────────────────

    def _on_upload(self) -> None:
        hg_code = self._current_hg_code
        if not hg_code:
            return
        path, _ = QFileDialog.getOpenFileName(
            self,
            f"HTMLマニュアルを選択 — {self._combo.currentText()}",
            "",
            "HTML Files (*.html *.htm);;All Files (*)",
        )
        if not path:
            return
        err = self._service.upload_manual(hg_code, Path(path))
        if err:
            QMessageBox.warning(self, "エラー", err)
            return
        self._manual_section.update_status(True)
        QMessageBox.information(self, "完了", "マニュアルを登録しました。")

    def _on_preview(self) -> None:
        hg_code = self._current_hg_code
        if not hg_code:
            return
        html = self._service.get_manual_html(hg_code)
        if not html:
            QMessageBox.information(self, "プレビュー", "マニュアルは未登録です。")
            return
        dlg = QDialog(self)
        dlg.setWindowTitle(f"マニュアル — {self._combo.currentText()}")
        dlg.resize(700, 500)
        layout = QVBoxLayout(dlg)
        browser = QTextBrowser()
        browser.setHtml(html)
        layout.addWidget(browser)
        btn_close = QPushButton("閉じる")
        btn_close.clicked.connect(dlg.accept)
        layout.addWidget(btn_close, alignment=Qt.AlignmentFlag.AlignRight)
        dlg.exec()

    def _on_delete_manual(self) -> None:
        hg_code = self._current_hg_code
        if not hg_code:
            return
        if not self._service.get_manual_html(hg_code):
            QMessageBox.information(self, "削除", "マニュアルは未登録です。")
            return
        ret = QMessageBox.question(
            self,
            "確認",
            f"「{self._combo.currentText()}」のマニュアルを削除しますか？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if ret != QMessageBox.StandardButton.Yes:
            return
        self._service.delete_manual(hg_code)
        self._manual_section.update_status(False)
