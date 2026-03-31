"""カレンダーポップアップ付き日付入力ウィジェット。

使い方:
    from app.ui.widgets.date_edit import DateEdit
    w = DateEdit()
    w.text()         # "2026-03-31" or ""
    w.setText("2026-03-31")
"""
from __future__ import annotations

import re
from datetime import date

from PySide6.QtCore import Qt, QDate, Signal
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QCalendarWidget,
    QHBoxLayout,
    QLineEdit,
    QMenu,
    QToolButton,
    QVBoxLayout,
    QWidget,
    QWidgetAction,
)

from app.ui.widgets.icon_utils import get_icon

_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
_BORDER = "#e2e8f0"
_ACCENT = "#3b82f6"
_TEXT = "#1e293b"
_TEXT2 = "#64748b"
_ERROR = "#ef4444"


class DateEdit(QWidget):
    """QLineEdit + カレンダーボタン + バリデーション。"""

    textChanged = Signal(str)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._valid = True
        self._build_ui()

    def _build_ui(self) -> None:
        hl = QHBoxLayout(self)
        hl.setContentsMargins(0, 0, 0, 0)
        hl.setSpacing(0)

        # テキスト入力
        self._edit = QLineEdit()
        self._edit.setPlaceholderText("YYYY-MM-DD")
        self._edit.setStyleSheet(
            f"QLineEdit {{ border:1px solid {_BORDER}; border-right:none;"
            f" border-radius:6px 0px 0px 6px;"
            f" padding:5px 10px; font-size:12px; color:{_TEXT}; }}"
            f"QLineEdit:focus {{ border-color:{_ACCENT}; }}"
        )
        self._edit.textChanged.connect(self._on_text_changed)
        hl.addWidget(self._edit, 1)

        # カレンダーボタン
        self._btn = QToolButton()
        self._btn.setIcon(get_icon(":/icons/calendar.svg", _TEXT2, size=18))
        self._btn.setFixedSize(36, 36)
        self._btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._btn.setStyleSheet(
            f"QToolButton {{ background:#ffffff; border:1px solid {_BORDER};"
            f" border-left:none; border-radius:0px 6px 6px 0px; }}"
            f"QToolButton:hover {{ background:#f1f5f9; }}"
        )
        self._btn.clicked.connect(self._show_calendar)
        hl.addWidget(self._btn)

    # ── 公開 API ──────────────────────────────────────────────────────────────

    def text(self) -> str:
        return self._edit.text().strip()

    def setText(self, text: str) -> None:
        self._edit.setText(text)

    def setPlaceholderText(self, text: str) -> None:
        self._edit.setPlaceholderText(text)

    def clear(self) -> None:
        self._edit.clear()

    def setFixedWidth(self, w: int) -> None:
        super().setFixedWidth(w)

    def isValid(self) -> bool:
        """入力が空 or 正しい日付形式なら True。"""
        return self._valid

    # ── 内部 ──────────────────────────────────────────────────────────────────

    def _on_text_changed(self, text: str) -> None:
        text = text.strip()
        if text == "":
            self._set_valid(True)
        elif _DATE_RE.match(text):
            try:
                y, m, d = text.split("-")
                date(int(y), int(m), int(d))
                self._set_valid(True)
            except ValueError:
                self._set_valid(False)
        else:
            self._set_valid(False)
        self.textChanged.emit(text)

    def _set_valid(self, valid: bool) -> None:
        self._valid = valid
        border_color = _BORDER if valid else _ERROR
        self._edit.setStyleSheet(
            f"QLineEdit {{ border:1px solid {border_color}; border-right:none;"
            f" border-radius:6px 0px 0px 6px;"
            f" padding:5px 10px; font-size:12px; color:{_TEXT}; }}"
            f"QLineEdit:focus {{ border-color:{_ACCENT if valid else _ERROR}; }}"
        )

    def _show_calendar(self) -> None:
        menu = QMenu(self)
        menu.setStyleSheet(
            "QMenu { background:#ffffff; border:1px solid #e5e7eb;"
            " border-radius:8px; padding:4px; }"
        )

        cal = QCalendarWidget()
        cal.setGridVisible(False)
        cal.setVerticalHeaderFormat(
            QCalendarWidget.VerticalHeaderFormat.NoVerticalHeader
        )

        # 現在の入力値があればカレンダーに反映
        text = self.text()
        if text and _DATE_RE.match(text):
            try:
                y, m, d = text.split("-")
                cal.setSelectedDate(QDate(int(y), int(m), int(d)))
            except ValueError:
                pass

        def _on_date_selected(qdate: QDate) -> None:
            self._edit.setText(qdate.toString("yyyy-MM-dd"))
            menu.close()

        cal.clicked.connect(_on_date_selected)

        action = QWidgetAction(menu)
        action.setDefaultWidget(cal)
        menu.addAction(action)
        menu.exec(self._btn.mapToGlobal(self._btn.rect().bottomLeft()))
