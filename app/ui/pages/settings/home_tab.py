"""設定 > ホームタブ — カレンダーURL設定。"""
from __future__ import annotations

from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from app.core import home_settings_store

_TEXT2 = "#64748b"
_ACCENT = "#3b82f6"
_BORDER = "#e2e8f0"


class HomeTab(QWidget):
    """ホーム設定タブ — カレンダーURLの設定。"""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._build_ui()
        self._load()

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(20, 16, 20, 16)
        root.setSpacing(16)

        section = QWidget()
        section.setObjectName("section_calendar")
        section.setStyleSheet(
            "#section_calendar { background: #ffffff; "
            f"border: 1px solid {_BORDER}; border-radius: 8px; }}"
        )
        sl = QVBoxLayout(section)
        sl.setContentsMargins(16, 12, 16, 12)
        sl.setSpacing(8)

        title = QLabel("カレンダー設定")
        title.setStyleSheet("font-size: 14px; font-weight: 600; border: none;")
        sl.addWidget(title)

        desc = QLabel("ホーム画面のカレンダーに表示するURLを設定します。")
        desc.setStyleSheet(f"font-size: 12px; color: {_TEXT2}; border: none;")
        sl.addWidget(desc)

        row = QHBoxLayout()
        lbl = QLabel("URL")
        lbl.setFixedWidth(40)
        lbl.setStyleSheet(
            f"font-size: 12px; font-weight: 600; color: {_TEXT2}; border: none;"
        )
        row.addWidget(lbl)

        self.edit_url = QLineEdit()
        self.edit_url.setPlaceholderText("例: https://calendar.google.com/...")
        self.edit_url.setFixedHeight(30)
        self.edit_url.setStyleSheet(
            f"QLineEdit {{ border: 1px solid {_BORDER}; border-radius: 4px;"
            f" padding: 4px 8px; font-size: 12px; }}"
            f"QLineEdit:focus {{ border-color: {_ACCENT}; }}"
        )
        row.addWidget(self.edit_url, 1)

        btn_save = QPushButton("保存")
        btn_save.setFixedHeight(30)
        btn_save.setStyleSheet(
            f"QPushButton {{ background: {_ACCENT}; color: white; border: none;"
            f" padding: 4px 16px; border-radius: 5px; font-size: 12px; font-weight: 600; }}"
            f"QPushButton:hover {{ background: #2563eb; }}"
        )
        btn_save.clicked.connect(self._on_save)
        row.addWidget(btn_save)

        sl.addLayout(row)
        root.addWidget(section)
        root.addStretch()

    def _load(self) -> None:
        self.edit_url.setText(home_settings_store.get_calendar_url())

    def _on_save(self) -> None:
        url = self.edit_url.text().strip()
        home_settings_store.set_calendar_url(url)
        QMessageBox.information(
            self, "保存完了",
            "カレンダーURLを保存しました。\nホーム画面に戻ると反映されます。",
        )
