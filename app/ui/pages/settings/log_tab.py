"""設定 > ログ設定タブ — ログ保持期間の設定。"""
from __future__ import annotations

from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from app.core import home_settings_store

_ACCENT = "#3b82f6"
_BTN_SAVE = (
    f"QPushButton {{ background: {_ACCENT}; color: white; border: none;"
    f" padding: 4px 16px; border-radius: 5px; font-size: 12px; font-weight: 600; }}"
    f"QPushButton:hover {{ background: #2563eb; }}"
)


class LogTab(QWidget):
    """ログ設定タブ — ログ保持期間を設定する。"""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._build_ui()
        self._load()

    def _build_ui(self) -> None:
        outer = QVBoxLayout(self)
        outer.setContentsMargins(20, 16, 20, 16)
        outer.setSpacing(16)

        # ── ログ保持期間 ──────────────────────────────────────────
        section = QFrame()
        section.setStyleSheet(
            "background: #ffffff; border: 1px solid #e5e7eb; border-radius: 8px;"
        )
        sl = QVBoxLayout(section)
        sl.setContentsMargins(16, 12, 16, 12)
        sl.setSpacing(8)

        title = QLabel("ログ保持期間")
        title.setStyleSheet("font-size: 14px; font-weight: 600; border: none;")
        sl.addWidget(title)

        desc = QLabel(
            "アプリケーションログの保持期間を設定します。"
            " 期間を過ぎたログファイルは起動時に自動削除されます。"
        )
        desc.setStyleSheet("font-size: 12px; color: #6b7280; border: none;")
        desc.setWordWrap(True)
        sl.addWidget(desc)

        row = QHBoxLayout()
        row.setSpacing(8)
        self._spin = QSpinBox()
        self._spin.setRange(0, 3650)
        self._spin.setSuffix(" 日")
        self._spin.setSpecialValueText("無制限")
        row.addWidget(self._spin)
        row.addStretch()
        btn = QPushButton("保存")
        btn.setFixedHeight(30)
        btn.setStyleSheet(_BTN_SAVE)
        btn.clicked.connect(self._on_save)
        row.addWidget(btn)
        sl.addLayout(row)

        outer.addWidget(section)
        outer.addStretch()

    def _load(self) -> None:
        self._spin.setValue(home_settings_store.get_log_retention_days())

    def _on_save(self) -> None:
        home_settings_store.set_log_retention_days(self._spin.value())
        days = self._spin.value()
        msg = "無制限" if days == 0 else f"{days} 日"
        QMessageBox.information(
            self, "保存完了",
            f"ログ保持期間を「{msg}」に保存しました。",
        )
