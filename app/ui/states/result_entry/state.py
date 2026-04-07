"""ResultEntryUI — データ入力ステートの純粋レイアウト。

分析項目（ホルダー）ごとにタブ分けしたテーブルを表示。
「データ入力」列のみ編集可能。一時保存・CSV出力・ツール起動ボタンを右上に配置。
"""
from __future__ import annotations

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QTabWidget,
    QAbstractItemView, QFrame,
)
from PySide6.QtCore import Signal, Qt
from PySide6.QtGui import QColor

from app.ui.widgets.icon_utils import get_icon

# ── スタイル定数 ──────────────────────────────────────────────────────────────

_ACCENT = "#3b82f6"
_BORDER = "#e2e8f0"
_TEXT = "#1e293b"
_TEXT2 = "#64748b"

_BTN_PRIMARY = (
    f"QPushButton {{ background:{_ACCENT}; color:white; border:none;"
    f" padding:4px 12px; border-radius:5px; font-size:12px; font-weight:600; }}"
    f"QPushButton:hover {{ background:#2563eb; }}"
)
_BTN_SECONDARY = (
    f"QPushButton {{ background:#ffffff; color:{_TEXT2}; border:1px solid {_BORDER};"
    f" padding:4px 12px; border-radius:5px; font-size:12px; font-weight:600; }}"
    f"QPushButton:hover {{ background:#f1f5f9; }}"
)
_TABLE_STYLE = (
    f"QTableWidget {{ border:1px solid {_BORDER}; border-radius:6px;"
    f" background:#ffffff; gridline-color:{_BORDER}; }}"
    f"QHeaderView::section {{ background:#f1f5f9; color:{_TEXT};"
    f" font-size:12px; font-weight:600; padding:4px;"
    f" border:none; border-bottom:1px solid {_BORDER}; }}"
    f"QTableWidget::item {{ padding:4px 6px; font-size:12px; color:{_TEXT}; }}"
)


class ResultEntryUI(QWidget):
    """データ入力ステート (純粋レイアウト)。

    Signals:
        done_requested(): 入力完了ボタン押下
        back_requested(): 戻る
        labaid_requested(): Lab-Aid 起動ボタン押下
        data_update_requested(): データ更新ボタン押下
        save_temp_requested(data): 一時保存要求
        csv_export_requested(data): CSV出力要求
        open_tool_requested(): 入力ツール起動要求
    """

    done_requested = Signal()
    back_requested = Signal()
    labaid_requested = Signal()
    data_update_requested = Signal()
    save_temp_requested = Signal(list)
    csv_export_requested = Signal(list)
    open_tool_requested = Signal()

    _INPUT_COL_KEY = "input_data"

    def __init__(self, parent=None):
        super().__init__(parent)
        self._column_config: list[dict] = []
        self._grouped_data: dict[str, list[dict]] = {}
        self._tables: dict[str, QTableWidget] = {}
        self._build_ui()

    def _build_ui(self) -> None:
        outer = QVBoxLayout(self)
        outer.setContentsMargins(8, 8, 8, 8)
        outer.setSpacing(8)

        # ── アクションバー ────────────────────────────────────────
        action_bar = QWidget()
        action_bar.setMaximumHeight(44)
        ab = QHBoxLayout(action_bar)
        ab.setContentsMargins(0, 4, 0, 4)
        ab.setSpacing(8)

        # 左側: データ更新
        self._btn_data_update = QPushButton("データ更新")
        self._btn_data_update.setIcon(get_icon(":/icons/data.svg", _ACCENT))
        self._btn_data_update.setMinimumWidth(100)
        self._btn_data_update.setFixedHeight(30)
        self._btn_data_update.setStyleSheet(_BTN_SECONDARY)
        self._btn_data_update.clicked.connect(self.data_update_requested)
        ab.addWidget(self._btn_data_update)

        # Lab-Aid起動
        self._btn_labaid = QPushButton("Lab-Aid")
        self._btn_labaid.setFixedHeight(30)
        self._btn_labaid.setStyleSheet(_BTN_SECONDARY)
        self._btn_labaid.clicked.connect(self.labaid_requested)
        ab.addWidget(self._btn_labaid)

        ab.addStretch()

        # 右側: 一時保存・CSV出力・入力ツール
        self._btn_save_temp = QPushButton("一時保存")
        self._btn_save_temp.setFixedHeight(30)
        self._btn_save_temp.setStyleSheet(_BTN_SECONDARY)
        self._btn_save_temp.clicked.connect(self._on_save_temp)
        ab.addWidget(self._btn_save_temp)

        self._btn_csv = QPushButton("CSV出力")
        self._btn_csv.setFixedHeight(30)
        self._btn_csv.setStyleSheet(_BTN_PRIMARY)
        self._btn_csv.clicked.connect(self._on_csv_export)
        ab.addWidget(self._btn_csv)

        self._btn_open_tool = QPushButton("入力ツール")
        self._btn_open_tool.setFixedHeight(30)
        self._btn_open_tool.setStyleSheet(_BTN_SECONDARY)
        self._btn_open_tool.clicked.connect(self.open_tool_requested)
        ab.addWidget(self._btn_open_tool)

        outer.addWidget(action_bar)

        # ── タブウィジェット ──────────────────────────────────────
        self._tab_widget = QTabWidget()
        outer.addWidget(self._tab_widget, 1)

        # ── ナビゲーションボタン ──────────────────────────────────
        nav_bar = QWidget()
        hl = QHBoxLayout(nav_bar)
        hl.addStretch()

        self._btn_back = QPushButton("戻る")
        self._btn_back.setMinimumSize(100, 50)
        self._btn_back.setMaximumSize(100, 50)
        self._btn_back.setVisible(False)
        self._btn_back.clicked.connect(self.back_requested)
        hl.addWidget(self._btn_back)

        self._btn_done = QPushButton("完了")
        self._btn_done.setMinimumSize(100, 50)
        self._btn_done.setMaximumSize(100, 50)
        self._btn_done.clicked.connect(self.done_requested)
        hl.addWidget(self._btn_done)

        hl.addStretch()
        outer.addWidget(nav_bar)

    # ── Public API ────────────────────────────────────────────────────────────

    def set_column_config(self, columns: list[dict]) -> None:
        self._column_config = columns

    def set_data(self, grouped: dict[str, list[dict]]) -> None:
        self._grouped_data = grouped
        self._rebuild_tabs()

    def restore_input_data(self, saved: dict[str, str]) -> None:
        """一時保存データを復元する。saved は {row_key: value} 形式。"""
        for holder_name, table in self._tables.items():
            vis_cols = self._visible_columns()
            input_col_idx = self._get_input_col_idx(vis_cols)
            if input_col_idx < 0:
                continue
            for row in range(table.rowCount()):
                key_item = table.item(row, 0)
                if not key_item:
                    continue
                row_key = key_item.data(Qt.ItemDataRole.UserRole)
                if row_key and row_key in saved:
                    table.setItem(row, input_col_idx, QTableWidgetItem(saved[row_key]))

    def set_readonly(self, readonly: bool) -> None:
        self._btn_done.setVisible(not readonly)
        self._btn_labaid.setVisible(not readonly)
        self._btn_data_update.setVisible(not readonly)
        self._btn_save_temp.setVisible(not readonly)
        self._btn_csv.setVisible(not readonly)
        self._btn_open_tool.setVisible(not readonly)

    def set_state_done(self, done: bool) -> None:
        if done:
            self._btn_done.setEnabled(False)
            self._btn_done.setText("完了済み")
        else:
            self._btn_done.setText("完了")

    # ── Internal ──────────────────────────────────────────────────────────────

    def _visible_columns(self) -> list[dict]:
        if self._column_config:
            return self._column_config
        return [
            {"key": "sample_request_number", "label": "依頼番号", "visible": True},
            {"key": "valid_sample_display_name", "label": "サンプル名", "visible": True},
            {"key": "valid_holder_display_name", "label": "ホルダ名", "visible": True},
            {"key": "valid_test_display_name", "label": "試験項目名", "visible": True},
            {"key": "test_unit_name", "label": "単位", "visible": True},
            {"key": self._INPUT_COL_KEY, "label": "データ入力", "visible": True},
        ]

    def _get_input_col_idx(self, vis_cols: list[dict]) -> int:
        for i, c in enumerate(vis_cols):
            if c["key"] == self._INPUT_COL_KEY:
                return i
        return -1

    def _rebuild_tabs(self) -> None:
        self._tab_widget.clear()
        self._tables.clear()

        if not self._grouped_data:
            self._tab_widget.addTab(QLabel("データがありません"), "（なし）")
            return

        for holder_name, rows in self._grouped_data.items():
            table = self._build_table(rows)
            self._tables[holder_name] = table
            self._tab_widget.addTab(table, holder_name)

    def _build_table(self, rows: list[dict]) -> QTableWidget:
        vis_cols = self._visible_columns()
        headers = [c["label"] for c in vis_cols]
        table = QTableWidget(len(rows), len(headers))
        table.setHorizontalHeaderLabels(headers)
        table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        table.setAlternatingRowColors(True)
        table.setStyleSheet(_TABLE_STYLE)

        hh = table.horizontalHeader()
        hh.setMinimumSectionSize(60)
        input_col_idx = self._get_input_col_idx(vis_cols)

        for i, c in enumerate(vis_cols):
            if c["key"] == "valid_sample_display_name":
                hh.setSectionResizeMode(i, QHeaderView.ResizeMode.Stretch)
            else:
                hh.setSectionResizeMode(i, QHeaderView.ResizeMode.ResizeToContents)

        vh = table.verticalHeader()
        vh.setDefaultSectionSize(32)
        vh.setVisible(False)

        for r, row_data in enumerate(rows):
            # 行のユニークキー（CSV出力用）
            row_key = (
                f"{row_data.get('sample_request_number', '')}_"
                f"{row_data.get('valid_holder_set_code', '')}_"
                f"{row_data.get('valid_test_set_code', '')}"
            )

            for col_i, c in enumerate(vis_cols):
                if c["key"] == self._INPUT_COL_KEY:
                    # 入力列 — 編集可能
                    item = QTableWidgetItem("")
                    item.setFlags(
                        item.flags() | Qt.ItemFlag.ItemIsEditable
                    )
                    item.setBackground(QColor("#fffbeb"))
                    table.setItem(r, col_i, item)
                else:
                    # 表示列 — 読み取り専用
                    val = row_data.get(c["key"], "")
                    text = "" if val is None or str(val) in ("nan", "None") else str(val)
                    item = QTableWidgetItem(text)
                    item.setFlags(
                        item.flags() & ~Qt.ItemFlag.ItemIsEditable
                    )
                    table.setItem(r, col_i, item)

                # 最初の列にユニークキーを格納
                if col_i == 0:
                    item.setData(Qt.ItemDataRole.UserRole, row_key)

        return table

    def _collect_all_data(self) -> list[dict]:
        """全タブのテーブルデータを収集する。"""
        vis_cols = self._visible_columns()
        result: list[dict] = []
        for holder_name, table in self._tables.items():
            for r in range(table.rowCount()):
                row_dict: dict[str, str] = {"_holder_tab": holder_name}
                for col_i, c in enumerate(vis_cols):
                    item = table.item(r, col_i)
                    row_dict[c["key"]] = item.text() if item else ""
                    if col_i == 0 and item:
                        row_dict["_row_key"] = item.data(Qt.ItemDataRole.UserRole) or ""
                result.append(row_dict)
        return result

    def _on_save_temp(self) -> None:
        self.save_temp_requested.emit(self._collect_all_data())

    def _on_csv_export(self) -> None:
        self.csv_export_requested.emit(self._collect_all_data())
