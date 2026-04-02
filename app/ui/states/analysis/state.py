"""AnalysisUI — 分析ステートの純粋レイアウト。

分析前/後のドキュメント＋チェックリストを縦並びで表示する。
ビジネスロジック・task_store・DataLoader の import 禁止。
"""
from __future__ import annotations

import os
import subprocess
import sys

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QCheckBox, QScrollArea, QFrame, QSpacerItem, QSizePolicy,
)
from PySide6.QtCore import Signal, Qt, QUrl
from PySide6.QtGui import QDesktopServices


# ── スタイル定数 ──────────────────────────────────────────────────────────────

_FRAME_STYLE = (
    "QFrame#section_frame { background: #ffffff; border: 1px solid #e5e7eb; "
    "border-radius: 8px; }"
)
_TITLE_STYLE = "font-size: 14px; font-weight: 700; color: #1f2937; border: none;"


def _make_separator() -> QWidget:
    """細い水平区切り線を生成する。"""
    sep = QWidget()
    sep.setFixedHeight(1)
    sep.setStyleSheet("background: #e5e7eb;")
    return sep


def _open_location(location: str, loc_type: str) -> None:
    """リンクまたはパスを開く。"""
    if loc_type == "link":
        QDesktopServices.openUrl(QUrl(location))
    else:
        path = os.path.normpath(location)
        if sys.platform == "win32":
            os.startfile(path)  # noqa: S606
        elif sys.platform == "darwin":
            subprocess.Popen(["open", path])  # noqa: S603,S607
        else:
            subprocess.Popen(["xdg-open", path])  # noqa: S603,S607


class AnalysisUI(QWidget):
    """分析ステート (純粋レイアウト)。

    Signals:
        finish_requested(pre_checks, post_checks): 完了ボタン押下
        back_requested(): 戻る
    """

    finish_requested = Signal(list, list)
    back_requested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._pre_checks: list[QCheckBox] = []
        self._post_checks: list[QCheckBox] = []
        self._build_ui()

    def _build_ui(self) -> None:
        outer = QVBoxLayout(self)
        outer.setContentsMargins(8, 8, 8, 8)
        outer.setSpacing(8)

        # ── スクロール領域 ────────────────────────────────────────────────
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)

        content = QWidget()
        self._content_layout = QVBoxLayout(content)
        self._content_layout.setContentsMargins(0, 0, 0, 0)
        self._content_layout.setSpacing(12)

        # 動的コンテンツ用プレースホルダー（set_config で置換）
        self._content_layout.addStretch()
        scroll.setWidget(content)
        outer.addWidget(scroll, 1)

        # ── ナビゲーションボタン ──────────────────────────────────────────
        action_bar = QWidget()
        hl = QHBoxLayout(action_bar)
        hl.addStretch()

        self.back_btn = QPushButton("戻る")
        self.back_btn.setMinimumSize(100, 50)
        self.back_btn.setMaximumSize(100, 50)
        self.back_btn.setVisible(False)
        self.back_btn.clicked.connect(self.back_requested)
        hl.addWidget(self.back_btn)

        self.finish_btn = QPushButton("完了")
        self.finish_btn.setMinimumSize(100, 50)
        self.finish_btn.setMaximumSize(100, 50)
        self.finish_btn.setEnabled(False)
        self.finish_btn.clicked.connect(self._on_finish)
        hl.addWidget(self.finish_btn)

        hl.addStretch()
        outer.addWidget(action_bar)

    # ── Public API ────────────────────────────────────────────────────────────

    def set_config(self, cfg: dict) -> None:
        """設定を元にドキュメント・チェックリストを構築する。"""
        self._clear_content()

        # 分析前ドキュメント
        pre_docs = cfg.get("pre_documents", [])
        self._content_layout.addWidget(
            self._make_docs_group("分析前ドキュメント", pre_docs)
        )

        # 分析前チェックリスト
        pre_items = cfg.get("pre_checklist", [])
        pre_group, self._pre_checks = self._make_checklist_group(
            "分析前チェックリスト", pre_items
        )
        self._content_layout.addWidget(pre_group)

        # 分析後ドキュメント
        post_docs = cfg.get("post_documents", [])
        self._content_layout.addWidget(
            self._make_docs_group("分析後ドキュメント", post_docs)
        )

        # 分析後チェックリスト
        post_items = cfg.get("post_checklist", [])
        post_group, self._post_checks = self._make_checklist_group(
            "分析後チェックリスト", post_items
        )
        self._content_layout.addWidget(post_group)

        self._content_layout.addStretch()
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
        self.finish_btn.setVisible(not readonly)
        # 一括チェックボタンも非表示に
        for btn in self._check_all_btns:
            btn.setVisible(not readonly)
        self._update_finish_btn()

    # ── Internal ──────────────────────────────────────────────────────────────

    def _clear_content(self) -> None:
        self._pre_checks = []
        self._post_checks = []
        self._check_all_btns: list[QPushButton] = []
        while self._content_layout.count():
            item = self._content_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

    def _make_docs_group(
        self, title: str, docs: list[dict]
    ) -> QFrame:
        """ドキュメント一覧のセクションを生成する。"""
        group = QFrame()
        group.setObjectName("section_frame")
        group.setStyleSheet(_FRAME_STYLE)
        vl = QVBoxLayout(group)
        vl.setContentsMargins(16, 12, 16, 12)
        vl.setSpacing(8)

        lbl_title = QLabel(title)
        lbl_title.setStyleSheet(_TITLE_STYLE)
        vl.addWidget(lbl_title)

        vl.addWidget(_make_separator())

        if not docs:
            lbl = QLabel("ドキュメントなし")
            lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            lbl.setStyleSheet("color: #9ca3af; font-size: 13px; padding: 8px;")
            vl.addWidget(lbl)
            return group

        for doc in docs:
            row = QWidget()
            rl = QHBoxLayout(row)
            rl.setContentsMargins(0, 0, 0, 0)
            rl.setSpacing(8)

            name = doc.get("name", "")
            location = doc.get("location", "")
            loc_type = doc.get("type", "path")

            icon = "🔗" if loc_type == "link" else "📁"
            lbl = QLabel(f"{icon}  {name}")
            lbl.setStyleSheet("font-size: 13px; color: #334155;")
            rl.addWidget(lbl, 1)

            if location:
                btn = QPushButton("開く")
                btn.setFixedWidth(60)
                btn.setStyleSheet(
                    "QPushButton { background: #3b82f6; color: white; border: none; "
                    "border-radius: 4px; padding: 4px 8px; font-weight: 600; }"
                    "QPushButton:hover { background: #2563eb; }"
                )
                btn.clicked.connect(
                    lambda _=False, loc=location, t=loc_type: _open_location(loc, t)
                )
                rl.addWidget(btn)

            vl.addWidget(row)

        return group

    def _make_checklist_group(
        self, title: str, items: list[str]
    ) -> tuple[QFrame, list[QCheckBox]]:
        """チェックリストのセクションを生成する。"""
        group = QFrame()
        group.setObjectName("section_frame")
        group.setStyleSheet(_FRAME_STYLE)
        vl = QVBoxLayout(group)
        vl.setContentsMargins(16, 12, 16, 12)
        vl.setSpacing(6)

        lbl_title = QLabel(title)
        lbl_title.setStyleSheet(_TITLE_STYLE)
        vl.addWidget(lbl_title)

        vl.addWidget(_make_separator())

        checks: list[QCheckBox] = []

        if not items:
            lbl = QLabel("チェック項目なし")
            lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            lbl.setStyleSheet("color: #9ca3af; font-size: 13px; padding: 8px;")
            vl.addWidget(lbl)
            return group, checks

        # 一括チェックボタン
        btn_all = QPushButton("一括チェック")
        btn_all.setMinimumSize(100, 35)
        btn_all.setMaximumSize(100, 50)
        btn_all.clicked.connect(lambda: self._check_all(checks))
        vl.addWidget(btn_all)
        self._check_all_btns.append(btn_all)

        for text in items:
            label = text if isinstance(text, str) else text.get("label", str(text))
            cb = QCheckBox(label)
            cb.setStyleSheet("font-size: 13px; color: #334155; padding: 2px 0;")
            cb.stateChanged.connect(self._update_finish_btn)
            vl.addWidget(cb)
            checks.append(cb)

        return group, checks

    def _check_all(self, checkboxes: list[QCheckBox]) -> None:
        for cb in checkboxes:
            if cb.isEnabled():
                cb.setChecked(True)

    def _update_finish_btn(self) -> None:
        all_checked = all(
            cb.isChecked() for cb in self._pre_checks + self._post_checks
        )
        self.finish_btn.setEnabled(all_checked)

    def _on_finish(self) -> None:
        pre = [cb.isChecked() for cb in self._pre_checks]
        post = [cb.isChecked() for cb in self._post_checks]
        self.finish_requested.emit(pre, post)
