"""設定 > アプリタブ — 表示件数・タスク保持・日付フォーマット・ログ保持。"""
from __future__ import annotations

from PySide6.QtWidgets import (
    QComboBox,
    QFormLayout,
    QFrame,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)
from PySide6.QtCore import Qt

from app.core import home_settings_store

_TEXT2 = "#64748b"
_ACCENT = "#3b82f6"

_SECTION_STYLE = (
    "background: #ffffff; border: 1px solid #e5e7eb; border-radius: 8px;"
)
_TITLE_STYLE = "font-size: 14px; font-weight: 600; border: none;"
_DESC_STYLE = f"font-size: 12px; color: {_TEXT2}; border: none;"
_BTN_SAVE = (
    f"QPushButton {{ background: {_ACCENT}; color: white; border: none;"
    f" padding: 4px 16px; border-radius: 5px; font-size: 12px; font-weight: 600; }}"
    f"QPushButton:hover {{ background: #2563eb; }}"
)


def _make_section(title: str, desc: str) -> tuple[QFrame, QVBoxLayout]:
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


class AppTab(QWidget):
    """アプリタブ — 表示件数・タスク保持・日付フォーマット・ログ保持の設定。"""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._build_ui()
        self._load()

    def _build_ui(self) -> None:
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        content = QWidget()
        root = QVBoxLayout(content)
        root.setContentsMargins(20, 16, 20, 16)
        root.setSpacing(16)

        # ── 表示件数設定 ──────────────────────────────────────────
        sec_page, sl_page = _make_section(
            "表示件数設定",
            "各ページの初期表示件数と「さらに読み込む」の件数を設定します。",
        )
        form_page = QFormLayout()
        form_page.setSpacing(8)
        form_page.setLabelAlignment(Qt.AlignmentFlag.AlignRight)

        self._spin_tasks = QSpinBox()
        self._spin_tasks.setRange(10, 1000)
        self._spin_tasks.setSingleStep(50)
        self._spin_tasks.setSuffix(" 件")
        self._spin_tasks.setFixedWidth(120)
        form_page.addRow("タスク一覧:", self._spin_tasks)

        self._spin_data = QSpinBox()
        self._spin_data.setRange(50, 5000)
        self._spin_data.setSingleStep(100)
        self._spin_data.setSuffix(" 件")
        self._spin_data.setFixedWidth(120)
        form_page.addRow("データページ:", self._spin_data)

        self._spin_library = QSpinBox()
        self._spin_library.setRange(10, 500)
        self._spin_library.setSingleStep(10)
        self._spin_library.setSuffix(" 件")
        self._spin_library.setFixedWidth(120)
        form_page.addRow("ライブラリ:", self._spin_library)

        sl_page.addLayout(form_page)
        btn_row = QHBoxLayout()
        btn_row.addStretch()
        btn_save_page = QPushButton("保存")
        btn_save_page.setFixedHeight(30)
        btn_save_page.setStyleSheet(_BTN_SAVE)
        btn_save_page.clicked.connect(self._on_save_page_sizes)
        btn_row.addWidget(btn_save_page)
        sl_page.addLayout(btn_row)
        root.addWidget(sec_page)

        # ── タスク保持設定 ────────────────────────────────────────
        sec_ret, sl_ret = _make_section(
            "タスク保持設定",
            "終了したタスクをタスク一覧に表示する期間を設定します。"
            "期間を過ぎた終了タスクは一覧に表示されません。（データは削除されません）",
        )
        ret_row = QHBoxLayout()
        ret_row.setSpacing(8)
        self._spin_retention = QSpinBox()
        self._spin_retention.setRange(0, 3650)
        self._spin_retention.setSuffix(" 日")
        self._spin_retention.setSpecialValueText("無制限")
        self._spin_retention.setFixedWidth(120)
        ret_row.addWidget(self._spin_retention)
        ret_row.addStretch()
        btn_save_ret = QPushButton("保存")
        btn_save_ret.setFixedHeight(30)
        btn_save_ret.setStyleSheet(_BTN_SAVE)
        btn_save_ret.clicked.connect(self._on_save_retention)
        ret_row.addWidget(btn_save_ret)
        sl_ret.addLayout(ret_row)
        root.addWidget(sec_ret)

        # ── 日付フォーマット設定 ──────────────────────────────────
        sec_date, sl_date = _make_section(
            "日付表示フォーマット",
            "アプリ全体の日付表示形式を設定します。",
        )
        date_row = QHBoxLayout()
        date_row.setSpacing(8)
        date_row.addWidget(QLabel("フォーマット:"))
        self._combo_date_fmt = QComboBox()
        for opt in home_settings_store.DATE_FORMAT_OPTIONS:
            self._combo_date_fmt.addItem(opt["label"])
        date_row.addWidget(self._combo_date_fmt)
        date_row.addStretch()
        btn_save_date = QPushButton("保存")
        btn_save_date.setFixedHeight(30)
        btn_save_date.setStyleSheet(_BTN_SAVE)
        btn_save_date.clicked.connect(self._on_save_date_format)
        date_row.addWidget(btn_save_date)
        sl_date.addLayout(date_row)
        root.addWidget(sec_date)

        # ── ログ保持期間 ──────────────────────────────────────────
        sec_log, sl_log = _make_section(
            "ログ保持期間",
            "アプリケーションログの保持期間を設定します。"
            "期間を過ぎたログファイルは起動時に自動削除されます。",
        )
        log_row = QHBoxLayout()
        log_row.setSpacing(8)
        self._spin_log = QSpinBox()
        self._spin_log.setRange(0, 3650)
        self._spin_log.setSuffix(" 日")
        self._spin_log.setSpecialValueText("無制限")
        self._spin_log.setFixedWidth(120)
        log_row.addWidget(self._spin_log)
        log_row.addStretch()
        btn_save_log = QPushButton("保存")
        btn_save_log.setFixedHeight(30)
        btn_save_log.setStyleSheet(_BTN_SAVE)
        btn_save_log.clicked.connect(self._on_save_log)
        log_row.addWidget(btn_save_log)
        sl_log.addLayout(log_row)
        root.addWidget(sec_log)

        root.addStretch()
        scroll.setWidget(content)
        outer.addWidget(scroll)

    def _load(self) -> None:
        sizes = home_settings_store.get_page_sizes()
        self._spin_tasks.setValue(sizes.get("tasks", 100))
        self._spin_data.setValue(sizes.get("data", 500))
        self._spin_library.setValue(sizes.get("library", 50))
        self._spin_retention.setValue(home_settings_store.get_task_retention_days())
        fmt_label = home_settings_store.get_date_format()
        idx = self._combo_date_fmt.findText(fmt_label)
        if idx >= 0:
            self._combo_date_fmt.setCurrentIndex(idx)
        self._spin_log.setValue(home_settings_store.get_log_retention_days())

    def _on_save_page_sizes(self) -> None:
        home_settings_store.set_page_sizes({
            "tasks": self._spin_tasks.value(),
            "data": self._spin_data.value(),
            "library": self._spin_library.value(),
        })
        QMessageBox.information(self, "保存完了", "表示件数を保存しました。")

    def _on_save_retention(self) -> None:
        home_settings_store.set_task_retention_days(self._spin_retention.value())
        days = self._spin_retention.value()
        msg = "無制限" if days == 0 else f"{days} 日"
        QMessageBox.information(self, "保存完了", f"タスク保持期間を「{msg}」に保存しました。")

    def _on_save_date_format(self) -> None:
        home_settings_store.set_date_format(self._combo_date_fmt.currentText())
        QMessageBox.information(self, "保存完了", "日付フォーマットを保存しました。")

    def _on_save_log(self) -> None:
        home_settings_store.set_log_retention_days(self._spin_log.value())
        days = self._spin_log.value()
        msg = "無制限" if days == 0 else f"{days} 日"
        QMessageBox.information(self, "保存完了", f"ログ保持期間を「{msg}」に保存しました。")
