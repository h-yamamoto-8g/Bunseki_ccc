"""SubmissionUI — 回覧ステートの純粋レイアウト（プログラム構築）。

ビジネスロジック・task_store・DataLoader の import 禁止。
"""
from __future__ import annotations

import os
import platform
import subprocess
from pathlib import Path

from PySide6.QtCore import Qt, Signal, QSize
from PySide6.QtWidgets import (
    QComboBox,
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QPlainTextEdit,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from app.ui.widgets.icon_utils import get_icon

# ── デザイントークン ──────────────────────────────────────────────────────────
_BG2 = "#ffffff"
_BG3 = "#f1f5f9"
_TEXT = "#1e293b"
_TEXT2 = "#475569"
_TEXT3 = "#94a3b8"
_ACCENT = "#3b82f6"
_ACCENT_LIGHT = "#eff6ff"
_DANGER = "#ef4444"
_SUCCESS = "#10b981"
_BORDER = "#e2e8f0"


class _RemoveButton(QPushButton):
    """cancel.svg アイコン付き削除ボタン。ホバー時にアイコン色を赤に変える。"""

    def __init__(self, icon_normal, icon_hover, parent=None):
        super().__init__(parent)
        self._icon_normal = icon_normal
        self._icon_hover = icon_hover
        self.setIcon(icon_normal)
        self.setIconSize(QSize(12, 12))
        self.setFixedSize(18, 18)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setToolTip("削除")
        self.setStyleSheet(
            "QPushButton { background:transparent; border:none;"
            " min-height:0; min-width:0; padding:0; }"
            "QPushButton:hover { background:rgba(239,68,68,0.10); border-radius:9px; }"
        )

    def enterEvent(self, event):
        self.setIcon(self._icon_hover)
        super().enterEvent(event)

    def leaveEvent(self, event):
        self.setIcon(self._icon_normal)
        super().leaveEvent(event)


class SubmissionUI(QWidget):
    """回覧ステート (純粋レイアウト)。

    Signals:
        send_requested(comment, attachments): 分析者→最初の確認者へ送信
        back_requested(): 前のステートへ戻る
        forward_requested(): 確認者→次の確認者へ送信
        return_requested(): 確認者→分析者へ差し戻し
        complete_requested(): 最後の確認者→終了
        reclaim_requested(): 分析者が取り戻し
    """

    send_requested = Signal(str, list)       # comment, attachments
    back_requested = Signal()
    forward_requested = Signal()
    return_requested = Signal()
    complete_requested = Signal()
    reclaim_requested = Signal()
    comment_add_requested = Signal(str)
    comment_delete_requested = Signal(str)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._creator: str = ""
        self._reviewers: list[str] = []
        self._attachments: list[str] = []
        self._comments: list[dict] = []
        self._editable = True
        self._can_comment = True
        self._current_user: str = ""
        self._mode: str = "edit"
        self._current_reviewer_index: int = 0
        self._build_ui()

    # ══════════════════════════════════════════════════════════════════════════
    # UI 構築
    # ══════════════════════════════════════════════════════════════════════════

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(20, 16, 20, 16)
        root.setSpacing(0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)

        content = QWidget()
        main_hl = QHBoxLayout(content)
        main_hl.setContentsMargins(0, 0, 0, 0)
        main_hl.setSpacing(16)

        # ── 左カラム: コメント＋添付 ──
        left_col = QWidget()
        left_vl = QVBoxLayout(left_col)
        left_vl.setContentsMargins(0, 0, 0, 0)
        left_vl.setSpacing(14)
        left_vl.addWidget(self._build_comment_section())
        left_vl.addWidget(self._build_attachment_section())
        left_vl.addStretch()
        main_hl.addWidget(left_col, 1)

        # ── 右カラム: 回覧フロー ──
        right_col = QWidget()
        right_vl = QVBoxLayout(right_col)
        right_vl.setContentsMargins(0, 0, 0, 0)
        right_vl.setSpacing(0)
        right_vl.addWidget(self._build_flow_section())
        right_vl.addStretch()
        right_col.setFixedWidth(280)
        main_hl.addWidget(right_col)

        scroll.setWidget(content)
        root.addWidget(scroll, 1)
        root.addSpacing(12)
        root.addWidget(self._build_button_bar())

    # ── フローセクション (右カラム — 縦型ステッパー) ─────────────────────

    def _build_flow_section(self) -> QFrame:
        frame = QFrame()
        frame.setStyleSheet(
            f"QFrame {{ background:{_BG2}; border:1px solid {_BORDER}; border-radius:10px; }}"
        )
        vl = QVBoxLayout(frame)
        vl.setContentsMargins(16, 14, 16, 14)
        vl.setSpacing(10)

        lbl = QLabel("回覧フロー")
        lbl.setFixedHeight(16)
        lbl.setStyleSheet(
            f"font-size:11px; font-weight:700; color:{_TEXT3}; border:none;"
            " letter-spacing:1px; text-transform:uppercase;"
        )
        vl.addWidget(lbl)

        # フロー図 — 縦型ステッパー
        self._flow_container = QWidget()
        self._flow_container.setStyleSheet("border:none;")
        self._flow_layout = QVBoxLayout(self._flow_container)
        self._flow_layout.setContentsMargins(4, 4, 4, 4)
        self._flow_layout.setSpacing(0)
        self._flow_layout.addStretch()
        vl.addWidget(self._flow_container)

        # ── 確認者追加行 ──
        self._add_row = QWidget()
        self._add_row.setStyleSheet("border:none;")
        add_vl = QVBoxLayout(self._add_row)
        add_vl.setContentsMargins(0, 6, 0, 0)
        add_vl.setSpacing(6)

        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet(f"background:{_BORDER}; border:none; max-height:1px;")
        add_vl.addWidget(sep)

        add_lbl = QLabel("確認者を追加")
        add_lbl.setStyleSheet(
            f"font-size:11px; font-weight:600; color:{_TEXT3}; border:none;"
        )
        add_vl.addWidget(add_lbl)

        add_hl = QHBoxLayout()
        add_hl.setSpacing(6)

        self._reviewer_combo = QComboBox()
        self._reviewer_combo.setMinimumWidth(140)
        self._reviewer_combo.setStyleSheet(
            f"QComboBox {{ border:1px solid {_BORDER}; border-radius:6px;"
            f" padding:4px 8px; font-size:12px; color:{_TEXT}; background:{_BG2}; }}"
            f"QComboBox:focus {{ border-color:{_ACCENT}; }}"
            f"QComboBox::drop-down {{ border:none; }}"
        )
        add_hl.addWidget(self._reviewer_combo, 1)

        self._btn_add = QPushButton()
        self._btn_add.setFixedSize(30, 30)
        self._btn_add.setIcon(get_icon(":/icons/add.svg", "#ffffff", 14))
        self._btn_add.setIconSize(QSize(14, 14))
        self._btn_add.setText("")
        self._btn_add.setCursor(Qt.CursorShape.PointingHandCursor)
        self._btn_add.setStyleSheet(
            f"QPushButton {{ background:{_ACCENT}; color:white; border:none;"
            f" border-radius:15px; min-height:0; }}"
            f"QPushButton:hover {{ background:#2563eb; }}"
        )
        self._btn_add.clicked.connect(self._on_add_reviewer)
        add_hl.addWidget(self._btn_add)

        add_vl.addLayout(add_hl)
        vl.addWidget(self._add_row)

        return frame

    # ── コメントセクション ────────────────────────────────────────────────

    def _build_comment_section(self) -> QFrame:
        frame = QFrame()
        frame.setStyleSheet(
            f"QFrame {{ background:{_BG2}; border:1px solid {_BORDER}; border-radius:10px; }}"
        )
        vl = QVBoxLayout(frame)
        vl.setContentsMargins(16, 10, 16, 12)
        vl.setSpacing(6)

        lbl = QLabel("コメント")
        lbl.setFixedHeight(16)
        lbl.setStyleSheet(
            f"font-size:11px; font-weight:700; color:{_TEXT3}; border:none;"
            " letter-spacing:1px;"
        )
        vl.addWidget(lbl)

        self._comment_container = QWidget()
        self._comment_container.setStyleSheet("border:none;")
        self._comment_layout = QVBoxLayout(self._comment_container)
        self._comment_layout.setContentsMargins(0, 0, 0, 0)
        self._comment_layout.setSpacing(6)
        vl.addWidget(self._comment_container)

        input_row = QHBoxLayout()
        input_row.setSpacing(8)
        self._comment_edit = QPlainTextEdit()
        self._comment_edit.setPlaceholderText("コメントを入力…")
        self._comment_edit.setFixedHeight(64)
        self._comment_edit.setStyleSheet(
            f"QPlainTextEdit {{ border:1px solid {_BORDER}; border-radius:8px;"
            f" padding:8px 10px; font-size:13px; color:{_TEXT}; background:{_BG2}; }}"
            f"QPlainTextEdit:focus {{ border-color:{_ACCENT}; }}"
        )
        input_row.addWidget(self._comment_edit, 1)

        self._btn_comment_add = QPushButton()
        self._btn_comment_add.setFixedSize(32, 32)
        self._btn_comment_add.setIcon(get_icon(":/icons/add.svg", "#ffffff", 14))
        self._btn_comment_add.setIconSize(QSize(14, 14))
        self._btn_comment_add.setText("")
        self._btn_comment_add.setCursor(Qt.CursorShape.PointingHandCursor)
        self._btn_comment_add.setStyleSheet(
            f"QPushButton {{ background:{_ACCENT}; color:white; border:none;"
            f" border-radius:16px; min-height:0; }}"
            f"QPushButton:hover {{ background:#2563eb; }}"
        )
        self._btn_comment_add.clicked.connect(self._on_add_comment)
        input_row.addWidget(self._btn_comment_add, alignment=Qt.AlignmentFlag.AlignTop)
        vl.addLayout(input_row)

        return frame

    # ── 添付資料セクション ────────────────────────────────────────────────

    def _build_attachment_section(self) -> QFrame:
        frame = QFrame()
        frame.setStyleSheet(
            f"QFrame {{ background:{_BG2}; border:1px solid {_BORDER}; border-radius:10px; }}"
        )
        vl = QVBoxLayout(frame)
        vl.setContentsMargins(16, 10, 16, 12)
        vl.setSpacing(6)

        header = QHBoxLayout()
        header.setSpacing(8)
        lbl = QLabel("添付資料")
        lbl.setFixedHeight(16)
        lbl.setStyleSheet(
            f"font-size:11px; font-weight:700; color:{_TEXT3}; border:none;"
            " letter-spacing:1px;"
        )
        header.addWidget(lbl)
        header.addStretch()
        self._btn_attach = QPushButton("ファイルを追加")
        self._btn_attach.setFixedHeight(26)
        self._btn_attach.setCursor(Qt.CursorShape.PointingHandCursor)
        self._btn_attach.setStyleSheet(
            f"QPushButton {{ background:{_ACCENT_LIGHT}; color:{_ACCENT}; border:1px solid {_BORDER};"
            f" padding:3px 12px; border-radius:6px; font-size:11px; font-weight:600; }}"
            f"QPushButton:hover {{ background:#dbeafe; border-color:{_ACCENT}; }}"
        )
        self._btn_attach.clicked.connect(self._on_add_attachment)
        header.addWidget(self._btn_attach)
        vl.addLayout(header)

        # 添付ファイルリスト
        self._att_container = QWidget()
        self._att_container.setStyleSheet("border:none;")
        self._att_layout = QVBoxLayout(self._att_container)
        self._att_layout.setContentsMargins(0, 0, 0, 0)
        self._att_layout.setSpacing(4)
        vl.addWidget(self._att_container)

        empty = QLabel("添付ファイルはありません")
        empty.setStyleSheet(f"font-size:12px; color:{_TEXT3}; border:none;")
        self._att_layout.addWidget(empty)

        return frame

    # ── ボタンバー ────────────────────────────────────────────────────────

    def _build_button_bar(self) -> QWidget:
        bar = QWidget()
        hl = QHBoxLayout(bar)
        hl.setContentsMargins(0, 0, 0, 0)
        hl.setSpacing(8)

        _secondary = (
            f"QPushButton {{ background:{_BG3}; color:{_TEXT}; border:1px solid {_BORDER};"
            f" padding:8px 20px; border-radius:8px; font-size:13px; font-weight:600; }}"
            f"QPushButton:hover {{ background:#e2e8f0; }}"
        )
        _primary = (
            f"QPushButton {{ background:{_ACCENT}; color:white; border:none;"
            f" padding:8px 20px; border-radius:8px; font-size:13px; font-weight:600; }}"
            f"QPushButton:hover {{ background:#2563eb; }}"
        )
        _danger = (
            f"QPushButton {{ background:{_BG2}; color:{_DANGER}; border:1px solid {_DANGER};"
            f" padding:8px 20px; border-radius:8px; font-size:13px; font-weight:600; }}"
            f"QPushButton:hover {{ background:#fef2f2; }}"
        )
        _success = (
            f"QPushButton {{ background:{_SUCCESS}; color:white; border:none;"
            f" padding:8px 20px; border-radius:8px; font-size:13px; font-weight:600; }}"
            f"QPushButton:hover {{ background:#059669; }}"
        )

        self._btn_back = QPushButton("← 戻る")
        self._btn_back.setStyleSheet(_secondary)
        self._btn_back.clicked.connect(self.back_requested)
        hl.addWidget(self._btn_back)

        hl.addStretch()

        self._btn_reclaim = QPushButton("取り戻し")
        self._btn_reclaim.setStyleSheet(_danger)
        self._btn_reclaim.clicked.connect(self.reclaim_requested)
        hl.addWidget(self._btn_reclaim)

        self._btn_return = QPushButton("差し戻し")
        self._btn_return.setStyleSheet(_danger)
        self._btn_return.clicked.connect(self.return_requested)
        hl.addWidget(self._btn_return)

        self._btn_send = QPushButton("送信 →")
        self._btn_send.setStyleSheet(_primary)
        self._btn_send.clicked.connect(self._on_send)
        hl.addWidget(self._btn_send)

        self._btn_forward = QPushButton("送信 →")
        self._btn_forward.setStyleSheet(_primary)
        self._btn_forward.clicked.connect(self.forward_requested)
        hl.addWidget(self._btn_forward)

        self._btn_complete = QPushButton("終了")
        self._btn_complete.setStyleSheet(_success)
        self._btn_complete.clicked.connect(self.complete_requested)
        hl.addWidget(self._btn_complete)

        return bar

    # ══════════════════════════════════════════════════════════════════════════
    # Public API
    # ══════════════════════════════════════════════════════════════════════════

    def set_available_users(self, names: list[str]) -> None:
        """確認者コンボボックスの候補を設定する。"""
        self._reviewer_combo.clear()
        self._reviewer_combo.addItems(names)

    def set_creator(self, name: str) -> None:
        self._creator = name

    def set_reviewers(self, names: list[str]) -> None:
        self._reviewers = list(names)

    def set_comment(self, text: str) -> None:
        self._comment_edit.setPlainText(text)

    def set_comments(self, comments: list[dict]) -> None:
        self._comments = list(comments)
        self._rebuild_comments()

    def set_attachments(self, attachments: list) -> None:
        """attachments は list[dict(path,added_by)] または後方互換の list[str]。"""
        normalized = []
        for item in attachments:
            if isinstance(item, dict):
                normalized.append(item)
            else:
                normalized.append({"path": str(item), "added_by": ""})
        self._attachments = normalized

    def get_comment(self) -> str:
        return self._comment_edit.toPlainText()

    def get_draft_comment(self) -> str:
        return self._comment_edit.toPlainText().strip()

    def clear_draft_comment(self) -> None:
        self._comment_edit.clear()

    def get_attachments(self) -> list[dict]:
        return list(self._attachments)

    def get_reviewers(self) -> list[str]:
        return list(self._reviewers)

    def apply_mode(
        self,
        mode: str,
        current_reviewer_index: int = 0,
    ) -> None:
        """UIモードを適用する。

        mode:
            "edit"          — 分析者・送信前（編集可）
            "sent_analyst"  — 分析者・送信後（取り戻しのみ）
            "reviewer_mid"  — 確認者・次の人がいる（差し戻し+送信）
            "reviewer_last" — 確認者・最後（差し戻し+終了）
            "readonly"      — 終了済み（閲覧のみ）
        """
        self._mode = mode
        self._current_reviewer_index = max(current_reviewer_index, 0)
        self._editable = mode in ("edit", "reviewer_mid", "reviewer_last")
        self._can_comment = mode in ("edit", "reviewer_mid", "reviewer_last")

        # フロー図を再描画
        self._rebuild_flow(current_reviewer_index, highlight=(mode != "edit"))

        # 確認者追加行
        self._add_row.setVisible(mode in ("edit", "reviewer_mid", "reviewer_last"))

        # コメント・添付
        self._comment_edit.setReadOnly(not self._can_comment)
        self._btn_comment_add.setVisible(self._can_comment)
        self._rebuild_comments()
        self._btn_attach.setVisible(mode == "edit")
        self._rebuild_attachments()

        # ボタン
        self._btn_back.setVisible(mode == "edit")
        self._btn_send.setVisible(mode == "edit")
        self._btn_reclaim.setVisible(mode == "sent_analyst")
        self._btn_return.setVisible(mode in ("reviewer_mid", "reviewer_last"))
        if mode in ("reviewer_mid", "reviewer_last"):
            has_next = self._current_reviewer_index < len(self._reviewers) - 1
            self._btn_forward.setVisible(has_next)
            self._btn_complete.setVisible(not has_next)
        else:
            self._btn_forward.setVisible(False)
            self._btn_complete.setVisible(False)

    def set_current_user(self, user_name: str) -> None:
        self._current_user = user_name
        self._rebuild_comments()

    # ══════════════════════════════════════════════════════════════════════════
    # Internal
    # ══════════════════════════════════════════════════════════════════════════

    def _on_add_reviewer(self) -> None:
        name = self._reviewer_combo.currentText()
        if not name or name in self._reviewers:
            return
        self._reviewers.append(name)
        self._rebuild_flow(current_idx=-1, highlight=False)
        if self._mode in ("reviewer_mid", "reviewer_last"):
            self.apply_mode(self._mode, self._current_reviewer_index)

    def _remove_reviewer(self, idx: int) -> None:
        if 0 <= idx < len(self._reviewers):
            if self._mode in ("reviewer_mid", "reviewer_last") and idx <= self._current_reviewer_index:
                return
            self._reviewers.pop(idx)
            self._rebuild_flow(current_idx=-1, highlight=False)
            if self._mode in ("reviewer_mid", "reviewer_last"):
                self.apply_mode(self._mode, self._current_reviewer_index)

    def _rebuild_flow(self, current_idx: int, highlight: bool) -> None:
        """フロー図（縦型ステッパー: 起票者 → 確認者1 → ...）を再構築する。"""
        while self._flow_layout.count():
            item = self._flow_layout.takeAt(0)
            w = item.widget()
            if w:
                w.deleteLater()

        # 起票者（常に完了スタイル）
        self._flow_layout.addWidget(self._make_node(self._creator, "起票者", state="done"))

        for i, name in enumerate(self._reviewers):
            # コネクタ線（縦）
            passed = highlight and i <= current_idx
            self._flow_layout.addWidget(self._make_connector(passed))

            is_active = highlight and i == current_idx
            is_done = highlight and i < current_idx
            if is_active:
                node_state = "active"
            elif is_done:
                node_state = "done"
            else:
                node_state = "pending"

            if not self._editable:
                removable_idx = None
            elif self._mode in ("reviewer_mid", "reviewer_last"):
                removable_idx = i if i > self._current_reviewer_index else None
            else:
                removable_idx = i
            self._flow_layout.addWidget(
                self._make_node(
                    name,
                    f"確認者{i + 1}",
                    state=node_state,
                    removable_idx=removable_idx,
                )
            )

        self._flow_layout.addStretch()

    def _make_node(
        self,
        name: str,
        role: str,
        state: str,
        removable_idx: int | None = None,
    ) -> QWidget:
        """縦型ステッパー用のフローノードを生成する。

        state: "active" | "done" | "pending"
        横配置: [avatar] [name + role] [remove_btn?]
        """
        w = QWidget()
        w.setStyleSheet("border:none;")
        hl = QHBoxLayout(w)
        hl.setContentsMargins(0, 3, 0, 3)
        hl.setSpacing(10)

        # ── アバター ──
        initial = name[0] if name else "?"
        avatar = QLabel(initial)
        avatar.setFixedSize(38, 38)
        avatar.setAlignment(Qt.AlignmentFlag.AlignCenter)

        if state == "active":
            avatar.setStyleSheet(
                f"background:{_ACCENT}; color:white;"
                f" border:2px solid {_ACCENT}; border-radius:19px;"
                " font-size:15px; font-weight:bold;"
            )
        elif state == "done":
            avatar.setStyleSheet(
                "background:#dbeafe; color:#1d4ed8;"
                " border:2px solid #93c5fd; border-radius:19px;"
                " font-size:15px; font-weight:bold;"
            )
        else:
            avatar.setStyleSheet(
                f"background:{_BG3}; color:{_TEXT3};"
                f" border:2px solid {_BORDER}; border-radius:19px;"
                " font-size:15px; font-weight:bold;"
            )
        hl.addWidget(avatar)

        # ── 名前・役割 ──
        text_vl = QVBoxLayout()
        text_vl.setContentsMargins(0, 0, 0, 0)
        text_vl.setSpacing(1)

        nm = QLabel(name)
        if state == "active":
            nm.setStyleSheet(f"font-size:13px; color:{_TEXT}; font-weight:600; border:none;")
        else:
            nm.setStyleSheet(f"font-size:13px; color:{_TEXT2}; border:none;")
        text_vl.addWidget(nm)

        rl = QLabel(role)
        rl.setStyleSheet(f"font-size:10px; color:{_TEXT3}; border:none;")
        text_vl.addWidget(rl)

        hl.addLayout(text_vl, 1)

        # ── 削除ボタン ──
        if removable_idx is not None:
            rm = _RemoveButton(
                get_icon(":/icons/cancel.svg", "#cbd5e1", 12),
                get_icon(":/icons/cancel.svg", "#ef4444", 12),
            )
            rm.clicked.connect(lambda _=False, j=removable_idx: self._remove_reviewer(j))
            hl.addWidget(rm, alignment=Qt.AlignmentFlag.AlignVCenter)

        return w

    def _on_add_comment(self) -> None:
        text = self.get_draft_comment()
        if not text:
            return
        self.comment_add_requested.emit(text)

    def _rebuild_comments(self) -> None:
        while self._comment_layout.count():
            item = self._comment_layout.takeAt(0)
            w = item.widget()
            if w:
                w.deleteLater()

        if not self._comments:
            empty = QLabel("コメントはまだありません")
            empty.setStyleSheet(f"font-size:12px; color:{_TEXT3}; border:none;")
            self._comment_layout.addWidget(empty)
            return

        for c in self._comments:
            self._comment_layout.addWidget(self._make_comment_card(c))

    def _make_comment_card(self, comment: dict) -> QFrame:
        card = QFrame()
        card.setStyleSheet(
            f"QFrame {{ background:{_BG3}; border:none;"
            f" border-left:3px solid {_ACCENT}; border-radius:4px; }}"
        )
        vl = QVBoxLayout(card)
        vl.setContentsMargins(10, 6, 8, 6)
        vl.setSpacing(3)

        top = QHBoxLayout()
        top.setContentsMargins(0, 0, 0, 0)
        top.setSpacing(6)
        author = str(comment.get("author", ""))
        top_lbl = QLabel(author or "不明ユーザー")
        top_lbl.setStyleSheet(f"font-size:12px; color:{_ACCENT}; border:none; font-weight:600;")
        top.addWidget(top_lbl)
        top.addStretch()

        can_delete = (
            self._can_comment
            and author == self._current_user
            and bool(comment.get("pending", False))
        )
        if can_delete:
            del_btn = QPushButton()
            del_btn.setIcon(get_icon(":/icons/cancel.svg", _TEXT3, 14))
            del_btn.setIconSize(QSize(14, 14))
            del_btn.setFixedSize(20, 20)
            del_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            del_btn.setStyleSheet(
                "QPushButton { background:transparent; border:none; }"
                "QPushButton:hover { background:#fee2e2; border-radius:4px; }"
            )
            comment_id = str(comment.get("id", ""))
            del_btn.clicked.connect(
                lambda _=False, cid=comment_id: self.comment_delete_requested.emit(cid)
            )
            top.addWidget(del_btn)
        vl.addLayout(top)

        body = QLabel(str(comment.get("text", "")))
        body.setWordWrap(True)
        body.setStyleSheet(f"font-size:13px; color:{_TEXT}; border:none;")
        vl.addWidget(body)

        return card

    @staticmethod
    def _make_connector(passed: bool) -> QWidget:
        """ノード間の縦コネクタ線を生成する。"""
        w = QWidget()
        w.setFixedHeight(20)
        w.setStyleSheet("border:none;")
        hl = QHBoxLayout(w)
        hl.setContentsMargins(0, 0, 0, 0)
        hl.setSpacing(0)

        color = "#93c5fd" if passed else _BORDER
        line = QWidget()
        line.setFixedWidth(2)
        line.setStyleSheet(f"background:{color}; border:none; border-radius:1px;")

        # アバター中央 (38/2 = 19px) に合わせてオフセット
        hl.addSpacing(18)
        hl.addWidget(line)
        hl.addStretch()

        return w

    # ── 添付ファイル ──────────────────────────────────────────────────────

    def _on_add_attachment(self) -> None:
        files, _ = QFileDialog.getOpenFileNames(self, "ファイルを選択")
        existing_paths = {a["path"] for a in self._attachments}
        for f in files:
            if f not in existing_paths:
                self._attachments.append({"path": f, "added_by": self._current_user})
        self._rebuild_attachments()

    def _remove_attachment(self, idx: int) -> None:
        if 0 <= idx < len(self._attachments):
            self._attachments.pop(idx)
            self._rebuild_attachments()

    def _rebuild_attachments(self) -> None:
        while self._att_layout.count():
            item = self._att_layout.takeAt(0)
            w = item.widget()
            if w:
                w.deleteLater()

        if not self._attachments:
            empty = QLabel("添付ファイルはありません")
            empty.setStyleSheet(f"font-size:12px; color:{_TEXT3}; border:none;")
            self._att_layout.addWidget(empty)
            return

        for i, att in enumerate(self._attachments):
            self._att_layout.addWidget(self._make_att_card(att, i))

    def _make_att_card(self, att: dict, idx: int) -> QFrame:
        path = att["path"]
        added_by = att.get("added_by", "")
        is_owner = self._editable and (
            added_by == self._current_user or added_by == ""
        )

        card = QFrame()
        card.setStyleSheet(
            f"QFrame {{ background:{_BG3}; border:1px solid {_BORDER}; border-radius:6px; }}"
        )
        hl = QHBoxLayout(card)
        hl.setContentsMargins(10, 5, 6, 5)
        hl.setSpacing(8)

        icon = QLabel()
        icon.setPixmap(get_icon(":/icons/link.svg", _ACCENT, 14).pixmap(14, 14))
        icon.setFixedSize(14, 14)
        icon.setStyleSheet("border:none;")
        hl.addWidget(icon)

        name_btn = QPushButton(Path(path).name)
        name_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        name_btn.setFlat(True)
        name_btn.setStyleSheet(
            f"QPushButton {{ font-size:12px; color:{_TEXT}; border:none;"
            " background:transparent; text-align:left; padding:0; }"
            f"QPushButton:hover {{ color:{_ACCENT}; text-decoration:underline; }}"
        )
        name_btn.clicked.connect(lambda _=False, p=path: self._open_attachment(p))
        hl.addWidget(name_btn, 1)

        if is_owner:
            del_btn = QPushButton()
            del_btn.setIcon(get_icon(":/icons/cancel.svg", _TEXT3, 14))
            del_btn.setIconSize(QSize(14, 14))
            del_btn.setFixedSize(20, 20)
            del_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            del_btn.setToolTip("削除")
            del_btn.setStyleSheet(
                "QPushButton { background:transparent; border:none; }"
                "QPushButton:hover { background:#fee2e2; border-radius:4px; }"
            )
            del_btn.clicked.connect(lambda _=False, j=idx: self._remove_attachment(j))
            hl.addWidget(del_btn)

        return card

    def _open_attachment(self, path: str) -> None:
        """添付ファイルをOSのデフォルトアプリで開く。"""
        p = Path(path)
        # 相対パスなら DATA_PATH を基準に解決（SharePoint 共有対応）
        if not p.is_absolute():
            import app.config as _cfg
            p = _cfg.DATA_PATH / p
        if not p.exists():
            from PySide6.QtWidgets import QMessageBox
            QMessageBox.warning(self, "ファイルが見つかりません", str(p))
            return
        try:
            if platform.system() == "Darwin":
                subprocess.run(["open", str(p)], check=False)
            elif platform.system() == "Windows":
                os.startfile(str(p))
            else:
                subprocess.run(["xdg-open", str(p)], check=False)
        except Exception as e:
            from PySide6.QtWidgets import QMessageBox
            QMessageBox.warning(self, "ファイルを開けません", str(e))

    # ── 送信 ──────────────────────────────────────────────────────────────

    def _on_send(self) -> None:
        self.send_requested.emit(
            self._comment_edit.toPlainText(),
            list(self._attachments),
        )
