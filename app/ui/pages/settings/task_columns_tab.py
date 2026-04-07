"""タスク列設定タブ — 分析対象・データ確認テーブルの表示列を設定する。"""
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

_FRAME_STYLE = (
    "QFrame#col_section { background: #ffffff; border: 1px solid #e5e7eb; "
    "border-radius: 8px; }"
    "QFrame#col_section QWidget { background: #ffffff; }"
)
_TITLE_STYLE = "font-size: 14px; font-weight: 700; color: #1f2937; border: none;"
_SUB_TITLE_STYLE = "font-size: 13px; font-weight: 600; color: #374151; border: none;"


def _make_separator() -> QWidget:
    sep = QWidget()
    sep.setFixedHeight(1)
    sep.setStyleSheet("background: #e5e7eb;")
    return sep


_MOVE_BTN_STYLE = (
    "QPushButton { background: transparent; border: 1px solid #d1d5db;"
    " border-radius: 4px; padding: 0; min-height: 0; min-width: 0;"
    " font-size: 12px; color: #6b7280; }"
    "QPushButton:hover { background: #eff6ff; border-color: #3b82f6; color: #3b82f6; }"
    "QPushButton:disabled { color: #d1d5db; border-color: #e5e7eb; }"
)


class _ColumnListEditor(QWidget):
    """1スコープ分の列チェックボックス + 表示名エディタ + 並び替え。"""

    def __init__(
        self,
        title: str,
        scope: str,
        service: DataConfigService,
        csv_columns: list[str] | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._scope = scope
        self._service = service
        self._csv_columns = csv_columns
        self._columns: list[dict] = []
        self._rows: list[dict] = []
        self._build_ui(title)
        self._load()

    def _build_ui(self, title: str) -> None:
        section = QFrame()
        section.setObjectName("col_section")
        section.setStyleSheet(_FRAME_STYLE)
        vl = QVBoxLayout(section)
        vl.setContentsMargins(16, 12, 16, 12)
        vl.setSpacing(0)

        lbl = QLabel(title)
        lbl.setStyleSheet(_SUB_TITLE_STYLE)
        vl.addWidget(lbl)
        vl.addWidget(_make_separator())

        desc = QLabel(
            "チェックで表示/非表示を切り替え、列名を変更できます。"
            "  ▲▼ で表示順を変更できます。"
        )
        desc.setStyleSheet(
            "color: #6b7280; font-size: 12px; padding: 8px 0 4px 0;"
        )
        vl.addWidget(desc)

        self._list_layout = QVBoxLayout()
        self._list_layout.setSpacing(0)
        vl.addLayout(self._list_layout)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(section)

    def _load(self) -> None:
        columns = self._service.get_task_columns(
            self._scope, csv_columns=self._csv_columns,
        )
        self._columns = columns
        self._rebuild()

    def _rebuild(self) -> None:
        for r in self._rows:
            r["widget"].deleteLater()
        self._rows.clear()

        n = len(self._columns)
        for i, col in enumerate(self._columns):
            row_data = self._make_row(col, index=i, total=n)
            self._list_layout.addWidget(row_data["widget"])
            self._rows.append(row_data)

    def _make_row(self, col: dict, index: int, total: int) -> dict:
        row = QWidget()
        row.setObjectName("col_row")
        hl = QHBoxLayout(row)
        hl.setContentsMargins(8, 4, 8, 4)
        hl.setSpacing(8)

        # 上下移動ボタン
        btn_up = QPushButton("▲")
        btn_up.setFixedSize(QSize(24, 24))
        btn_up.setStyleSheet(_MOVE_BTN_STYLE)
        btn_up.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_up.setEnabled(index > 0)
        btn_up.clicked.connect(lambda _=False, idx=index: self._move(idx, -1))
        hl.addWidget(btn_up, alignment=Qt.AlignmentFlag.AlignVCenter)

        btn_down = QPushButton("▼")
        btn_down.setFixedSize(QSize(24, 24))
        btn_down.setStyleSheet(_MOVE_BTN_STYLE)
        btn_down.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_down.setEnabled(index < total - 1)
        btn_down.clicked.connect(lambda _=False, idx=index: self._move(idx, 1))
        hl.addWidget(btn_down, alignment=Qt.AlignmentFlag.AlignVCenter)

        cb = QCheckBox()
        cb.setChecked(col.get("visible", True))
        cb.setFixedSize(28, 28)
        cb.setStyleSheet(
            "QCheckBox { border-bottom: none; padding: 0; }"
            "QCheckBox::indicator { width: 24px; height: 24px; }"
        )
        hl.addWidget(cb, alignment=Qt.AlignmentFlag.AlignVCenter)

        key_lbl = QLabel(col["key"])
        key_lbl.setFixedWidth(240)
        key_lbl.setStyleSheet("font-size: 12px; color: #6b7280;")
        hl.addWidget(key_lbl, alignment=Qt.AlignmentFlag.AlignVCenter)

        edit = QLineEdit(col.get("label", ""))
        edit.setPlaceholderText("表示名")
        hl.addWidget(edit, 1)

        is_last = index == total - 1
        if not is_last:
            row.setStyleSheet("QWidget#col_row { border-bottom: 1px solid #e5e7eb; }")

        return {"widget": row, "key": col["key"], "cb": cb, "edit": edit}

    def _move(self, index: int, direction: int) -> None:
        """行を上(-1)または下(+1)に移動する。"""
        new_index = index + direction
        if new_index < 0 or new_index >= len(self._columns):
            return
        # 現在のUI入力値を _columns に反映してからスワップ
        self._sync_to_columns()
        self._columns[index], self._columns[new_index] = (
            self._columns[new_index], self._columns[index]
        )
        self._rebuild()

    def _sync_to_columns(self) -> None:
        """UI上の編集値を _columns リストに反映する。"""
        for i, r in enumerate(self._rows):
            if i < len(self._columns):
                self._columns[i]["visible"] = r["cb"].isChecked()
                label = r["edit"].text().strip()
                self._columns[i]["label"] = label or self._columns[i]["key"]

    def collect(self) -> list[dict]:
        """現在の設定を返す（表示順を保持）。"""
        self._sync_to_columns()
        return [
            {
                "key": c["key"],
                "label": c.get("label", c["key"]),
                "visible": c.get("visible", True),
            }
            for c in self._columns
        ]


class TaskColumnsTab(QWidget):
    """タスク列設定タブ。分析対象とデータ確認の列設定を一つのタブにまとめる。"""

    def __init__(
        self,
        data_config_service: DataConfigService,
        csv_columns: list[str] | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._service = data_config_service
        self._csv_columns = csv_columns
        self._build_ui()

    def _build_ui(self) -> None:
        outer = QVBoxLayout(self)
        outer.setContentsMargins(16, 16, 16, 16)
        outer.setSpacing(12)

        # ── ヘッダー: 保存ボタン ──────────────────────��──────────
        header = QHBoxLayout()
        title = QLabel("タスクテーブルの表示列設定")
        title.setStyleSheet(_TITLE_STYLE)
        header.addWidget(title)
        header.addStretch()
        self._btn_save = QPushButton("保存")
        self._btn_save.setStyleSheet(
            "background: #3b82f6; color: white; border: none; "
            "border-radius: 6px; padding: 8px 24px; font-weight: 600;"
        )
        self._btn_save.clicked.connect(self._on_save)
        header.addWidget(self._btn_save)
        outer.addLayout(header)

        # ── スクロール領域 ─────────────────────────────���──────────
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )
        scroll.setFrameShape(QFrame.Shape.NoFrame)

        content = QWidget()
        cl = QVBoxLayout(content)
        cl.setContentsMargins(0, 0, 0, 0)
        cl.setSpacing(16)

        self._targets_editor = _ColumnListEditor(
            "分析対象（ターゲット）テーブル",
            "analysis_targets",
            self._service,
            csv_columns=self._csv_columns,
        )
        cl.addWidget(self._targets_editor)

        self._verify_editor = _ColumnListEditor(
            "データ確認（チェック）テーブル",
            "result_verification",
            self._service,
            csv_columns=self._csv_columns,
        )
        cl.addWidget(self._verify_editor)

        cl.addStretch()
        scroll.setWidget(content)
        outer.addWidget(scroll, 1)

    def _on_save(self) -> None:
        self._service.save_task_columns(
            "analysis_targets", self._targets_editor.collect()
        )
        self._service.save_task_columns(
            "result_verification", self._verify_editor.collect()
        )
        QMessageBox.information(self, "保存完了", "タスクテーブルの表示列設定を保存しました。")
