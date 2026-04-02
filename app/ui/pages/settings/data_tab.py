"""データ設定タブ — 列の表示/非表示・表示名を設定する。"""
from __future__ import annotations

from PySide6.QtCore import Qt, QSize
from PySide6.QtWidgets import (
    QCheckBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from app.services.data_config_service import DataConfigService
from app.ui.widgets.icon_utils import get_icon

_FRAME_STYLE = (
    "QFrame#col_list_block { background: #ffffff; border: 1px solid #e5e7eb; "
    "border-radius: 8px; }"
    "QFrame#col_list_block QWidget { background: #ffffff; }"
)
_TITLE_STYLE = "font-size: 14px; font-weight: 700; color: #1f2937; border: none;"


def _make_separator() -> QWidget:
    sep = QWidget()
    sep.setFixedHeight(1)
    sep.setStyleSheet("background: #e5e7eb;")
    return sep


class DataTab(QWidget):
    """データ設定タブ。"""

    def __init__(
        self,
        data_config_service: DataConfigService,
        csv_columns: list[str] | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._service = data_config_service
        self._csv_columns = csv_columns
        self._rows: list[dict] = []
        self._build_ui()
        self._load()

    def _build_ui(self) -> None:
        outer = QVBoxLayout(self)
        outer.setContentsMargins(16, 16, 16, 16)
        outer.setSpacing(12)

        # ── ヘッダー: 保存ボタン ─────────────────────────────────
        header = QHBoxLayout()
        header.addStretch()
        self._btn_save = QPushButton("保存")
        self._btn_save.setStyleSheet(
            "background: #3b82f6; color: white; border: none; "
            "border-radius: 6px; padding: 8px 24px; font-weight: 600;"
        )
        self._btn_save.clicked.connect(self._on_save)
        header.addWidget(self._btn_save)
        outer.addLayout(header)

        # ── スクロール領域 ────────────────────────────────────────
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)

        content = QWidget()
        self._content_layout = QVBoxLayout(content)
        self._content_layout.setContentsMargins(0, 0, 0, 0)
        self._content_layout.setSpacing(12)

        # ── 列設定セクション ──────────────────────────────────────
        section = QFrame()
        section.setObjectName("col_list_block")
        section.setStyleSheet(_FRAME_STYLE)
        vl = QVBoxLayout(section)
        vl.setContentsMargins(16, 12, 16, 12)
        vl.setSpacing(0)

        title = QLabel("表示列の設定")
        title.setStyleSheet(_TITLE_STYLE)
        vl.addWidget(title)
        vl.addWidget(_make_separator())

        desc = QLabel("チェックで表示/非表示を切り替え、列名を変更できます。")
        desc.setStyleSheet(
            "color: #6b7280; font-size: 12px; padding: 8px 0 4px 0;"
        )
        vl.addWidget(desc)

        self._list_layout = QVBoxLayout()
        self._list_layout.setSpacing(0)
        vl.addLayout(self._list_layout)

        self._content_layout.addWidget(section)
        self._content_layout.addStretch()

        scroll.setWidget(content)
        outer.addWidget(scroll, 1)

    def _load(self) -> None:
        columns = self._service.get_columns(csv_columns=self._csv_columns)
        self._rebuild(columns)

    def _rebuild(self, columns: list[dict]) -> None:
        # 既存行をクリア
        for r in self._rows:
            r["widget"].deleteLater()
        self._rows.clear()

        for i, col in enumerate(columns):
            row_data = self._make_row(col, is_last=(i == len(columns) - 1))
            self._list_layout.addWidget(row_data["widget"])
            self._rows.append(row_data)

    def _make_row(self, col: dict, is_last: bool) -> dict:
        row = QWidget()
        row.setObjectName("col_row")
        hl = QHBoxLayout(row)
        hl.setContentsMargins(8, 4, 16, 4)
        hl.setSpacing(12)

        # 表示チェックボックス
        cb = QCheckBox()
        cb.setChecked(col.get("visible", True))
        cb.setFixedSize(28, 28)
        cb.setStyleSheet(
            "QCheckBox { border-bottom: none; padding: 0; }"
            "QCheckBox::indicator { width: 24px; height: 24px; }"
        )
        hl.addWidget(cb, alignment=Qt.AlignmentFlag.AlignVCenter)

        # 列キー表示
        key_lbl = QLabel(col["key"])
        key_lbl.setFixedWidth(240)
        key_lbl.setStyleSheet("font-size: 12px; color: #6b7280;")
        hl.addWidget(key_lbl, alignment=Qt.AlignmentFlag.AlignVCenter)

        # 表示名入力
        edit = QLineEdit(col.get("label", ""))
        edit.setPlaceholderText("表示名")
        hl.addWidget(edit, 1)

        if not is_last:
            row.setStyleSheet("QWidget#col_row { border-bottom: 1px solid #e5e7eb; }")

        return {"widget": row, "key": col["key"], "cb": cb, "edit": edit}

    def _on_save(self) -> None:
        columns = []
        for r in self._rows:
            columns.append({
                "key": r["key"],
                "label": r["edit"].text().strip() or r["key"],
                "visible": r["cb"].isChecked(),
            })
        self._service.save_columns(columns)
        QMessageBox.information(self, "保存完了", "データ表示設定を保存しました。")
