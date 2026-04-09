"""確認者設定タブ — 回覧ステートで使用するデフォルト確認者リストの管理。"""
from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QCheckBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from app.services.hg_config_service import HgConfigService
from app.services.data_service import DataService

# ── スタイル定数 ──────────────────────────────────────────────────────────────

_FRAME_STYLE = (
    "QFrame#reviewer_frame { background: #ffffff; border: 1px solid #e5e7eb;"
    " border-radius: 8px; }"
    "QFrame#reviewer_frame QWidget { background: #ffffff; }"
)
_SECTION_LABEL = "font-weight: 600; font-size: 14px; color: #1f2937;"
_HINT = "font-size: 12px; color: #6b7280;"
_BTN_PRIMARY = (
    "QPushButton { background: #3b82f6; color: white; border: none;"
    " border-radius: 6px; padding: 8px 24px; font-weight: 600; }"
    "QPushButton:hover { background: #2563eb; }"
)


class ReviewerTab(QWidget):
    """確認者設定タブ。

    確認者権限を持つユーザー一覧からデフォルト確認者を選択する。

    Args:
        hg_config_service: ホルダグループ設定サービス。
        data_service: データサービス（ユーザー一覧取得用）。
        parent: 親ウィジェット。
    """

    def __init__(
        self,
        hg_config_service: HgConfigService,
        data_service: DataService,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._hg_service = hg_config_service
        self._data_service = data_service
        self._checkboxes: list[tuple[QCheckBox, str]] = []
        self._build_ui()
        self._load()

    def _build_ui(self) -> None:
        outer = QVBoxLayout(self)
        outer.setContentsMargins(16, 16, 16, 16)
        outer.setSpacing(12)

        # ヘッダー
        header = QHBoxLayout()
        lbl = QLabel("確認者設定")
        lbl.setStyleSheet(_SECTION_LABEL)
        header.addWidget(lbl)
        header.addStretch()

        self._btn_save = QPushButton("保存")
        self._btn_save.setStyleSheet(_BTN_PRIMARY)
        self._btn_save.clicked.connect(self._on_save)
        header.addWidget(self._btn_save)
        outer.addLayout(header)

        hint = QLabel(
            "回覧ステートでデフォルトの確認者として選択されるユーザーを設定します。"
            "\n確認者権限を持つユーザーのみ表示されます。"
        )
        hint.setStyleSheet(_HINT)
        hint.setWordWrap(True)
        outer.addWidget(hint)

        # チェックボックスリスト
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        self._list_frame = QFrame()
        self._list_frame.setObjectName("reviewer_frame")
        self._list_frame.setStyleSheet(_FRAME_STYLE)
        self._list_layout = QVBoxLayout(self._list_frame)
        self._list_layout.setContentsMargins(16, 12, 16, 12)
        self._list_layout.setSpacing(8)

        scroll.setWidget(self._list_frame)
        outer.addWidget(scroll, 1)

    def _load(self) -> None:
        """確認者一覧と保存済みデフォルトを読み込んで表示する。"""
        # チェックボックスをクリア
        for cb, _ in self._checkboxes:
            cb.deleteLater()
        self._checkboxes.clear()

        # 確認者権限を持つユーザー一覧を取得
        reviewers = self._data_service.get_reviewers()
        if not reviewers:
            lbl = QLabel("確認者権限を持つユーザーがいません。")
            lbl.setStyleSheet("color: #9ca3af; font-size: 13px; padding: 12px;")
            lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self._list_layout.addWidget(lbl)
            return

        # 保存済みデフォルト
        defaults = set(self._hg_service.get_default_reviewers())

        for user in reviewers:
            name = user.get("name", "")
            if not name:
                continue
            cb = QCheckBox(name)
            cb.setStyleSheet("font-size: 13px; padding: 4px;")
            cb.setChecked(name in defaults)
            self._list_layout.addWidget(cb)
            self._checkboxes.append((cb, name))

        self._list_layout.addStretch()

    def _on_save(self) -> None:
        """選択された確認者を保存する。"""
        selected = [name for cb, name in self._checkboxes if cb.isChecked()]
        self._hg_service.save_default_reviewers(selected)
        QMessageBox.information(
            self, "保存完了",
            f"デフォルト確認者を保存しました。\n選択: {len(selected)} 名",
        )
