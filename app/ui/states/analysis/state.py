"""AnalysisUI — 分析準備チェックリストの純粋レイアウト（generated UI 使用）。

ビジネスロジック・task_store・DataLoader の import 禁止。
"""
from __future__ import annotations

from PySide6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QLabel, QPushButton, QCheckBox,
)
from PySide6.QtCore import Signal, QUrl
from PySide6.QtGui import QDesktopServices

from app.ui.generated.ui_stateanalysis import Ui_PageStateAnalysis


class AnalysisUI(QWidget):
    """分析準備チェックリスト (純粋レイアウト)。

    Signals:
        finish_requested(pre_checks, post_checks): 分析終了ボタン押下
        back_requested(): 戻る
    """

    finish_requested = Signal(list, list)
    back_requested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._pre_checks: list[QCheckBox] = []
        self._post_checks: list[QCheckBox] = []

        self._form = Ui_PageStateAnalysis()
        self._form.setupUi(self)

        # ── グローバル QSS でリセットされるデフォルト spacing を明示設定 ──
        self._form.verticalLayout_6.setSpacing(8)
        self._form.verticalLayout_6.setContentsMargins(8, 8, 8, 8)

        # 生成UIのバグ修正: after チェックリストのタイトルが "分析前確認リスト" になっている
        self._form.groupBox_after_check_list.setTitle("分析後確認リスト")

        # btn_next は全チェック完了まで無効
        self._form.btn_next.setEnabled(False)

        # 一括チェックボタン接続
        self._form.btn_before_all_checked.clicked.connect(
            lambda: self._check_all(self._pre_checks)
        )
        self._form.btn_after_all_checked.clicked.connect(
            lambda: self._check_all(self._post_checks)
        )

        # ナビゲーション接続
        self._form.btn_back.setVisible(False)
        self._form.btn_next.setText("完了")
        self._form.btn_next.clicked.connect(self._on_finish)

        # エイリアス (restore_checks でVisible制御に使用)
        self.finish_btn = self._form.btn_next
        self.back_btn   = self._form.btn_back

        # リンクセクション用コンテナ (VBox) を groupBox_links の horizontalLayout に追加
        self._links_container = QWidget()
        self._links_vbox = QVBoxLayout(self._links_container)
        self._links_vbox.setContentsMargins(0, 0, 0, 0)
        self._links_vbox.setSpacing(8)
        self._form.horizontalLayout.addWidget(self._links_container)
        self._form.horizontalLayout.addStretch()

    # ── Public API ────────────────────────────────────────────────────────────

    def set_config(self, cfg: dict) -> None:
        """設定を元にリンク・チェックリストを構築する。"""
        self._clear_content()
        self._build_links_section(cfg)
        self._build_pre_checklist(cfg)
        self._build_post_checklist(cfg)
        self._update_finish_btn()

    def restore_checks(
        self, pre_saved: list[bool], post_saved: list[bool], readonly: bool
    ) -> None:
        for cb, val in zip(self._pre_checks, pre_saved):
            cb.setChecked(bool(val))
            cb.setEnabled(not readonly)
        for cb, val in zip(self._post_checks, post_saved):
            cb.setChecked(bool(val))
            cb.setEnabled(not readonly)
        self._form.btn_next.setVisible(not readonly)
        self._form.btn_before_all_checked.setVisible(not readonly)
        self._form.btn_after_all_checked.setVisible(not readonly)
        self._update_finish_btn()

    # ── Internal ──────────────────────────────────────────────────────────────

    def _clear_content(self) -> None:
        # リンクコンテナをクリア
        while self._links_vbox.count():
            item = self._links_vbox.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        # 分析前チェックリストをクリア
        layout = self._form.verticalLayout_7
        while layout.count():
            item = layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        # 分析後チェックリストをクリア
        layout = self._form.verticalLayout_8
        while layout.count():
            item = layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        self._pre_checks = []
        self._post_checks = []

    def _build_links_section(self, cfg: dict) -> None:
        analysis_links = cfg.get("analysis_links", [])
        manual_links   = cfg.get("manual_links", [])
        tool_links     = cfg.get("tool_links", [])
        labaid         = cfg.get("labaid_link", "")
        all_links = analysis_links + manual_links + tool_links
        if labaid:
            all_links.append({"label": "Lab-Aid 起動", "url": labaid})

        self._form.groupBox_links.setVisible(bool(all_links))
        if not all_links:
            return

        for link in all_links:
            row = QWidget()
            rl = QHBoxLayout(row)
            rl.setContentsMargins(0, 0, 0, 0)
            lbl = QLabel(f"• {link.get('label', '')}")
            lbl.setStyleSheet("color:#475569; font-size:13px;")
            rl.addWidget(lbl)
            btn = QPushButton("開く")
            btn.setFixedWidth(60)
            url = link.get("url", "")
            btn.clicked.connect(lambda _=False, u=url: QDesktopServices.openUrl(QUrl(u)))
            rl.addWidget(btn)
            rl.addStretch()
            self._links_vbox.addWidget(row)

    def _build_pre_checklist(self, cfg: dict) -> None:
        items = cfg.get("pre_checklist", [])
        self._form.groupBox_before_check_list.setVisible(bool(items))
        layout = self._form.verticalLayout_7
        for item in items:
            cb = QCheckBox(item if isinstance(item, str) else item.get("label", str(item)))
            cb.setStyleSheet("font-size:13px; color:#334155; padding:2px 0;")
            cb.stateChanged.connect(self._update_finish_btn)
            layout.addWidget(cb)
            self._pre_checks.append(cb)

    def _build_post_checklist(self, cfg: dict) -> None:
        items = cfg.get("post_checklist", [])
        self._form.groupBox_after_check_list.setVisible(bool(items))
        layout = self._form.verticalLayout_8
        for item in items:
            cb = QCheckBox(item if isinstance(item, str) else item.get("label", str(item)))
            cb.setStyleSheet("font-size:13px; color:#334155; padding:2px 0;")
            cb.stateChanged.connect(self._update_finish_btn)
            layout.addWidget(cb)
            self._post_checks.append(cb)

    def _check_all(self, checkboxes: list[QCheckBox]) -> None:
        for cb in checkboxes:
            if cb.isEnabled():
                cb.setChecked(True)

    def _update_finish_btn(self) -> None:
        all_checked = all(cb.isChecked() for cb in self._pre_checks + self._post_checks)
        self._form.btn_next.setEnabled(all_checked)

    def _on_finish(self) -> None:
        pre  = [cb.isChecked() for cb in self._pre_checks]
        post = [cb.isChecked() for cb in self._post_checks]
        self.finish_requested.emit(pre, post)
