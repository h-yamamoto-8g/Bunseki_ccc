"""設定 > タスク > 印刷設定タブ。"""
from __future__ import annotations

from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from app.ui.pages.settings.mail_print_widget import PrintSettingsWidget

_BTN_STYLE = "font-size: 16px; font-weight: 700; color: #1f2937;"


class PrintTab(QWidget):
    """印刷設定タブ。PrintSettingsWidget をラップする。"""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        outer = QVBoxLayout(self)
        outer.setContentsMargins(16, 16, 16, 16)
        outer.setSpacing(16)

        self._print_settings = PrintSettingsWidget()
        outer.addWidget(self._print_settings)
        outer.addStretch()
