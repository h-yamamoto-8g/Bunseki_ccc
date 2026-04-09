"""設定 > ホームタブ — カレンダーURL・表示件数・タスク保持設定。"""
from __future__ import annotations

from PySide6.QtWidgets import (
    QComboBox,
    QFormLayout,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from app.core import home_settings_store

_TEXT2 = "#64748b"
_ACCENT = "#3b82f6"
_BORDER = "#e2e8f0"

_SECTION_STYLE = (
    "background: #ffffff; border: 1px solid #e5e7eb; border-radius: 8px;"
)
_TITLE_STYLE = "font-size: 14px; font-weight: 600; border: none;"
_DESC_STYLE = f"font-size: 12px; color: {_TEXT2}; border: none;"
_BTN_SAVE_STYLE = (
    f"QPushButton {{ background: {_ACCENT}; color: white; border: none;"
    f" padding: 4px 16px; border-radius: 5px; font-size: 12px; font-weight: 600; }}"
    f"QPushButton:hover {{ background: #2563eb; }}"
)


def _make_section(title: str, desc: str) -> tuple[QWidget, QVBoxLayout]:
    """共通のセクションウィジェットを生成する。"""
    section = QFrame()
    section.setStyleSheet(_SECTION_STYLE)
    sl = QVBoxLayout(section)
    sl.setContentsMargins(16, 12, 16, 12)
    sl.setSpacing(8)
    lbl_title = QLabel(title)
    lbl_title.setStyleSheet(_TITLE_STYLE)
    sl.addWidget(lbl_title)
    lbl_desc = QLabel(desc)
    lbl_desc.setStyleSheet(_DESC_STYLE)
    lbl_desc.setWordWrap(True)
    sl.addWidget(lbl_desc)
    return section, sl


class HomeTab(QWidget):
    """ホーム設定タブ — カレンダーURL・表示件数・タスク保持の設定。"""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._build_ui()
        self._load()

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(20, 16, 20, 16)
        root.setSpacing(16)

        # ── カレンダーURL ─────────────────────────────────────────
        sec_cal, sl_cal = _make_section(
            "カレンダー設定",
            "ホーム画面のカレンダーに表示するURLを設定します。",
        )
        row = QHBoxLayout()
        lbl = QLabel("URL")
        lbl.setFixedWidth(40)
        lbl.setStyleSheet(f"font-size: 12px; font-weight: 600; color: {_TEXT2}; border: none;")
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
        btn_save_cal = QPushButton("保存")
        btn_save_cal.setFixedHeight(30)
        btn_save_cal.setStyleSheet(_BTN_SAVE_STYLE)
        btn_save_cal.clicked.connect(self._on_save_calendar)
        row.addWidget(btn_save_cal)
        sl_cal.addLayout(row)
        root.addWidget(sec_cal)

        # ── 表示件数設定 ──────────────────────────────────────────
        sec_page, sl_page = _make_section(
            "表示件数設定",
            "各ページの初期表示件数と「さらに読み込む」の件数を設定します。",
        )
        form = QFormLayout()
        form.setSpacing(8)

        self._spin_tasks = QSpinBox()
        self._spin_tasks.setRange(10, 1000)
        self._spin_tasks.setSingleStep(50)
        self._spin_tasks.setSuffix(" 件")
        form.addRow("タスク一覧:", self._spin_tasks)

        self._spin_data = QSpinBox()
        self._spin_data.setRange(50, 5000)
        self._spin_data.setSingleStep(100)
        self._spin_data.setSuffix(" 件")
        form.addRow("データページ:", self._spin_data)

        self._spin_library = QSpinBox()
        self._spin_library.setRange(10, 500)
        self._spin_library.setSingleStep(10)
        self._spin_library.setSuffix(" 件")
        form.addRow("ライブラリ:", self._spin_library)

        sl_page.addLayout(form)

        btn_row_page = QHBoxLayout()
        btn_row_page.addStretch()
        btn_save_page = QPushButton("保存")
        btn_save_page.setFixedHeight(30)
        btn_save_page.setStyleSheet(_BTN_SAVE_STYLE)
        btn_save_page.clicked.connect(self._on_save_page_sizes)
        btn_row_page.addWidget(btn_save_page)
        sl_page.addLayout(btn_row_page)
        root.addWidget(sec_page)

        # ── タスク保持設定 ────────────────────────────────────────
        sec_ret, sl_ret = _make_section(
            "タスク保持設定",
            "終了したタスクをタスク一覧に表示する期間を設定します。期間を過ぎた終了タスクは一覧に表示されません。（データは削除されません）",
        )
        ret_row = QHBoxLayout()
        ret_row.setSpacing(8)
        self._spin_retention = QSpinBox()
        self._spin_retention.setRange(0, 3650)
        self._spin_retention.setSuffix(" 日")
        self._spin_retention.setSpecialValueText("無制限")
        ret_row.addWidget(self._spin_retention)
        ret_row.addStretch()
        btn_save_ret = QPushButton("保存")
        btn_save_ret.setFixedHeight(30)
        btn_save_ret.setStyleSheet(_BTN_SAVE_STYLE)
        btn_save_ret.clicked.connect(self._on_save_retention)
        ret_row.addWidget(btn_save_ret)
        sl_ret.addLayout(ret_row)
        root.addWidget(sec_ret)

        root.addStretch()

    def _load(self) -> None:
        """保存済みの設定をUIに反映する。"""
        self.edit_url.setText(home_settings_store.get_calendar_url())

        sizes = home_settings_store.get_page_sizes()
        self._spin_tasks.setValue(sizes.get("tasks", 100))
        self._spin_data.setValue(sizes.get("data", 500))
        self._spin_library.setValue(sizes.get("library", 50))

        self._spin_retention.setValue(home_settings_store.get_task_retention_days())

    def _on_save_calendar(self) -> None:
        url = self.edit_url.text().strip()
        home_settings_store.set_calendar_url(url)
        QMessageBox.information(
            self, "保存完了",
            "カレンダーURLを保存しました。\nホーム画面に戻ると反映されます。",
        )

    def _on_save_page_sizes(self) -> None:
        home_settings_store.set_page_sizes({
            "tasks": self._spin_tasks.value(),
            "data": self._spin_data.value(),
            "library": self._spin_library.value(),
        })
        QMessageBox.information(
            self, "保存完了",
            "表示件数を保存しました。\n各ページに戻ると反映されます。",
        )

    def _on_save_retention(self) -> None:
        home_settings_store.set_task_retention_days(self._spin_retention.value())
        days = self._spin_retention.value()
        msg = "無制限" if days == 0 else f"{days} 日"
        QMessageBox.information(
            self, "保存完了",
            f"タスク保持期間を「{msg}」に保存しました。",
        )
