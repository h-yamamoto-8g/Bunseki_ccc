"""SetupUserProfileDialog: USERPROFILEフォルダ設定ダイアログ。

SetupRootDialog と同じレイアウト:
  - 説明ラベル
  - パス入力欄 + 参照ボタン
  - OK / キャンセルボタン
"""
from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QSize
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QDialog,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QSizePolicy,
    QSpacerItem,
    QVBoxLayout,
    QWidget,
)

from app.config import save_user_profile, reload_user_profile
from app.ui.widgets.icon_utils import get_icon


class SetupUserProfileDialog(QDialog):
    """ユーザープロファイルフォルダを選択・設定するダイアログ。

    Args:
        current_path: 現在の設定パス（あれば入力欄に表示）。
        parent: 親ウィジェット。
    """

    def __init__(
        self, current_path: str = "", parent: QWidget | None = None
    ) -> None:
        super().__init__(parent)
        self._setup_ui()
        if current_path:
            self._input_path.setText(current_path)

    def _setup_ui(self) -> None:
        self.setWindowTitle("USERPROFILE の設定")
        self.resize(572, 130)

        root = QVBoxLayout(self)

        # ── 説明メッセージ ────────────────────────────────────────────────
        widget_message = QWidget()
        vl_msg = QVBoxLayout(widget_message)
        vl_msg.setContentsMargins(0, 0, 0, 0)

        self._label_message = QLabel(
            "ユーザープロファイルフォルダを選択してください。\n"
            "例: C:\\Users\\12414"
        )
        font_msg = QFont()
        font_msg.setPointSize(10)
        self._label_message.setFont(font_msg)
        vl_msg.addWidget(self._label_message)

        root.addWidget(widget_message)

        # ── パス入力 + 参照ボタン ─────────────────────────────────────────
        widget_input = QWidget()
        hl_input = QHBoxLayout(widget_input)
        hl_input.setContentsMargins(0, 0, 0, 0)

        self._input_path = QLineEdit()
        self._input_path.setMinimumSize(QSize(500, 0))
        font_input = QFont()
        font_input.setPointSize(12)
        self._input_path.setFont(font_input)
        hl_input.addWidget(self._input_path)

        btn_browse = QPushButton()
        btn_browse.setMinimumSize(QSize(30, 30))
        btn_browse.setMaximumSize(QSize(30, 30))
        btn_browse.setIcon(get_icon(":/icons/path.svg", "#333333", size=16))
        btn_browse.setIconSize(QSize(16, 16))
        btn_browse.clicked.connect(self._browse)
        hl_input.addWidget(btn_browse)

        root.addWidget(widget_input)

        # ── OK / キャンセル ───────────────────────────────────────────────
        widget_buttons = QWidget()
        hl_btn = QHBoxLayout(widget_buttons)
        hl_btn.setContentsMargins(0, 0, 0, 0)

        hl_btn.addItem(
            QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        )

        btn_ok = QPushButton("OK")
        btn_ok.setMinimumSize(QSize(100, 0))
        btn_ok.setMaximumSize(QSize(100, 16777215))
        btn_ok.setFont(font_input)
        btn_ok.clicked.connect(self._on_ok)
        hl_btn.addWidget(btn_ok)

        btn_cancel = QPushButton("キャンセル")
        btn_cancel.setMinimumSize(QSize(100, 0))
        btn_cancel.setMaximumSize(QSize(100, 16777215))
        btn_cancel.setFont(font_input)
        btn_cancel.clicked.connect(self.reject)
        hl_btn.addWidget(btn_cancel)

        root.addWidget(widget_buttons)

    def _browse(self) -> None:
        """フォルダ選択ダイアログを開く。"""
        start_dir = self._input_path.text() or str(Path.home())
        folder = QFileDialog.getExistingDirectory(
            self, "ユーザープロファイルフォルダを選択", start_dir
        )
        if folder:
            self._input_path.setText(folder)

    def _on_ok(self) -> None:
        """入力パスを検証し、有効なら保存してダイアログを閉じる。"""
        path_text = self._input_path.text().strip()
        if not path_text:
            self._label_message.setText("パスを入力してください。")
            self._label_message.setStyleSheet("color: #ef4444;")
            return

        p = Path(path_text)
        if not p.exists() or not p.is_dir():
            self._label_message.setText(
                "指定されたフォルダが存在しません。正しいパスを選択してください。"
            )
            self._label_message.setStyleSheet("color: #ef4444;")
            return

        save_user_profile(p)
        reload_user_profile(p)
        self.accept()

    def selected_path(self) -> Path:
        """ユーザーが選択したパスを返す。"""
        return Path(self._input_path.text().strip())
