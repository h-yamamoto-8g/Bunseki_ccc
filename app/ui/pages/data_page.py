"""データページ — bunseki.csv の検索・閲覧・CSVエクスポート。"""
from __future__ import annotations

import numpy as np
import pandas as pd
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QColor, QFont
from PySide6.QtWidgets import (
    QComboBox,
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QVBoxLayout,
    QWidget,
)

from app.services.data_config_service import DataConfigService
from app.services.data_service import DataService
from app.ui.states.result_verification.state import TrendDialog
from app.ui.widgets.date_edit import DateEdit
from app.ui.widgets.icon_utils import get_icon
from app.ui.widgets.table_utils import enable_row_numbers_and_sort


def _build_placeholder(widget: QWidget, title: str, description: str = "") -> None:
    """未実装ページ向けの簡易プレースホルダーUIを構築する。"""
    lay = QVBoxLayout(widget)
    lay.setContentsMargins(40, 40, 40, 40)
    lbl_title = QLabel(title)
    lbl_title.setStyleSheet("font-size:20px; font-weight:700; color:#334155;")
    lay.addWidget(lbl_title)
    if description:
        lbl_desc = QLabel(description)
        lbl_desc.setStyleSheet("font-size:13px; color:#94a3b8; margin-top:4px;")
        lay.addWidget(lbl_desc)
    lbl_wip = QLabel("実装予定")
    lbl_wip.setStyleSheet(
        "font-size:12px; color:#64748b; background:#f1f5f9;"
        " border-radius:4px; padding:4px 10px; margin-top:8px;"
    )
    lbl_wip.setFixedWidth(80)
    lay.addWidget(lbl_wip)
    lay.addStretch()


# ── デザイントークン ──────────────────────────────────────────────────────────
_BG = "#f5f7fa"
_BG2 = "#ffffff"
_BG3 = "#f9fafb"
_TEXT = "#333333"
_TEXT2 = "#6b7280"
_TEXT3 = "#9ca3af"
_ACCENT = "#3b82f6"
_DANGER = "#ef4444"
_BORDER = "#e5e7eb"

_PAGE_SIZE = 500

# ── 表示テーブル列定義 ────────────────────────────────────────────────────────
_COLUMNS = [
    ("サンプリング日", "sample_sampling_date"),
    ("依頼番号",       "sample_request_number"),
    ("JOB番号",        "sample_job_number"),
    ("ホルダ名",       "valid_holder_display_name"),
    ("サンプル名",     "valid_sample_display_name"),
    ("試験項目",       "valid_test_display_name"),
    ("データ",         "test_raw_data"),
    ("単位",           "test_unit_name"),
    ("判定",           "test_grade_code"),
]


class DataPage(QWidget):
    """bunseki.csv の検索・閲覧・CSVエクスポートページ。"""

    def __init__(self, data_service: DataService, parent: QWidget | None = None):
        super().__init__(parent)
        self._ds = data_service
        self._data_config = DataConfigService()
        self._visible_columns: list[tuple[str, str]] = []  # (label, key)
        self._all_df: pd.DataFrame | None = None   # 検索結果全件（表示制限なし）
        self._display_limit: int = _PAGE_SIZE
        self._load_column_config()
        self._build_ui()

    def _load_column_config(self) -> None:
        """設定から表示列を読み込む。"""
        try:
            csv_columns = self._ds.get_csv_columns()
        except Exception:
            csv_columns = None
        cols = self._data_config.get_columns(csv_columns=csv_columns)
        self._visible_columns = [
            (c["label"], c["key"])
            for c in cols if c.get("visible", True)
        ]

    # ── UI 構築 ───────────────────────────────────────────────────────────────

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(20, 16, 20, 16)
        root.setSpacing(12)

        root.addWidget(self._build_filter_section())
        root.addWidget(self._build_action_bar())
        root.addWidget(self._build_table(), 1)
        root.addWidget(self._build_pager_bar())

    # ── フィルターセクション ──────────────────────────────────────────────────

    def _build_filter_section(self) -> QFrame:
        frame = QFrame()
        frame.setStyleSheet(
            f"QFrame {{ background:{_BG2}; border:1px solid {_BORDER}; border-radius:8px; }}"
        )
        vl = QVBoxLayout(frame)
        vl.setContentsMargins(16, 12, 16, 12)
        vl.setSpacing(8)

        # Row 1: サンプリング日 + 依頼番号
        row1 = QHBoxLayout()
        row1.setSpacing(12)
        row1.addWidget(self._label("サンプリング日"))
        self.edit_date_from = DateEdit()
        self.edit_date_from.setFixedWidth(170)
        row1.addWidget(self.edit_date_from)
        row1.addWidget(self._label("〜"))
        self.edit_date_to = DateEdit()
        self.edit_date_to.setFixedWidth(170)
        row1.addWidget(self.edit_date_to)
        row1.addSpacing(20)
        row1.addWidget(self._label("依頼番号"))
        self.edit_request_no = self._input("部分一致", 140)
        row1.addWidget(self.edit_request_no)
        row1.addStretch()
        vl.addLayout(row1)

        # Row 2: JOB番号 + ホルダ + 判定
        row2 = QHBoxLayout()
        row2.setSpacing(12)
        row2.addWidget(self._label("JOB番号"))
        self.edit_job_no = self._input("部分一致", 140)
        row2.addWidget(self.edit_job_no)
        row2.addSpacing(20)
        row2.addWidget(self._label("ホルダ"))
        self.combo_holder = self._combo(200)
        row2.addWidget(self.combo_holder)
        row2.addSpacing(20)
        row2.addWidget(self._label("判定"))
        self.combo_judgment = QComboBox()
        self.combo_judgment.addItems(["全て", "NN", "異常"])
        self.combo_judgment.setFixedWidth(100)
        self._style_combo(self.combo_judgment)
        row2.addWidget(self.combo_judgment)
        row2.addStretch()
        vl.addLayout(row2)

        # Row 3: サンプル名 + 試験項目
        row3 = QHBoxLayout()
        row3.setSpacing(12)
        row3.addWidget(self._label("サンプル名"))
        self.combo_sample = self._combo(240)
        row3.addWidget(self.combo_sample)
        row3.addSpacing(20)
        row3.addWidget(self._label("試験項目"))
        self.combo_test = self._combo(240)
        row3.addWidget(self.combo_test)
        row3.addStretch()
        vl.addLayout(row3)

        # Row 4: ボタン
        row4 = QHBoxLayout()
        row4.setSpacing(8)
        row4.addStretch()
        self.btn_clear = QPushButton("クリア")
        self.btn_clear.setFixedHeight(32)
        self.btn_clear.setStyleSheet(
            f"QPushButton {{ background:{_BG3}; color:{_TEXT}; border:1px solid {_BORDER};"
            f" padding:6px 16px; border-radius:6px; font-size:12px; font-weight:600; }}"
            f"QPushButton:hover {{ background:{_BG}; }}"
        )
        self.btn_clear.clicked.connect(self._on_clear)
        row4.addWidget(self.btn_clear)
        self.btn_search = QPushButton("検索")
        self.btn_search.setFixedHeight(32)
        self.btn_search.setStyleSheet(
            f"QPushButton {{ background:{_ACCENT}; color:white; border:none;"
            f" padding:6px 16px; border-radius:6px; font-size:12px; font-weight:600; }}"
            f"QPushButton:hover {{ background:#2563eb; }}"
        )
        self.btn_search.clicked.connect(self._on_search)
        row4.addWidget(self.btn_search)
        vl.addLayout(row4)

        return frame

    # ── アクションバー ────────────────────────────────────────────────────────

    def _build_action_bar(self) -> QWidget:
        bar = QWidget()
        hl = QHBoxLayout(bar)
        hl.setContentsMargins(0, 0, 0, 0)
        hl.setSpacing(8)

        self.label_count = QLabel("検索ボタンを押してデータを表示")
        self.label_count.setStyleSheet(f"font-size:12px; font-weight:500; color:{_TEXT2};")
        hl.addWidget(self.label_count)
        hl.addStretch()

        self.btn_csv = QPushButton("CSV出力")
        self.btn_csv.setIcon(get_icon(":/icons/download.svg", _ACCENT, 16))
        self.btn_csv.setIconSize(QSize(16, 16))
        self.btn_csv.setFixedHeight(30)
        self.btn_csv.setStyleSheet(
            f"QPushButton {{ background:{_BG2}; color:{_ACCENT}; border:1px solid {_ACCENT};"
            f" padding:4px 14px; border-radius:6px; font-size:12px; font-weight:600; }}"
            f"QPushButton:hover {{ background:#eff6ff; }}"
        )
        self.btn_csv.clicked.connect(self._on_export_csv)
        hl.addWidget(self.btn_csv)

        return bar

    # ── テーブル ──────────────────────────────────────────────────────────────

    def _build_table(self) -> QTableWidget:
        self.table = QTableWidget()
        self._apply_table_columns()
        return self._style_table()

    def _apply_table_columns(self) -> None:
        """表示列設定をテーブルに反映する。"""
        cols = self._visible_columns
        col_count = len(cols) + 1  # +1 for graph button
        self.table.setColumnCount(col_count)
        self.table.setHorizontalHeaderLabels([c[0] for c in cols] + [""])
    def _style_table(self) -> QTableWidget:
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.verticalHeader().setDefaultSectionSize(36)
        enable_row_numbers_and_sort(self.table, self._on_sort_column)

        header = self.table.horizontalHeader()
        header.setDefaultAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        n = len(self._visible_columns)
        graph_col = n  # グラフボタン列
        for i in range(n):
            header.setSectionResizeMode(i, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(graph_col, QHeaderView.ResizeMode.Fixed)
        self.table.setColumnWidth(graph_col, 44)

        self.table.setStyleSheet(
            f"QTableWidget {{"
            f"  background:{_BG2}; alternate-background-color:{_BG3};"
            f"  border:1px solid {_BORDER}; border-radius:8px;"
            f"  gridline-color:{_BORDER}; font-size:13px; color:{_TEXT};"
            f"}}"
            f"QTableWidget::item {{ padding:4px 8px; }}"
            f"QTableWidget::item:selected {{ background:#dbeafe; color:#1e293b; }}"
            f"QHeaderView::section {{"
            f"  background:{_BG3}; color:{_TEXT2}; font-size:11px; font-weight:600;"
            f"  padding:8px 12px; border:none; border-bottom:1px solid {_BORDER};"
            f"}}"
        )
        return self.table

    # ── ページャーバー ────────────────────────────────────────────────────────

    def _build_pager_bar(self) -> QWidget:
        bar = QWidget()
        hl = QHBoxLayout(bar)
        hl.setContentsMargins(0, 0, 0, 0)
        hl.setSpacing(8)
        hl.addStretch()

        _btn_style = (
            f"QPushButton {{ background:{_BG3}; color:{_TEXT}; border:1px solid {_BORDER};"
            f" padding:5px 14px; border-radius:6px; font-size:12px; }}"
            f"QPushButton:hover {{ background:{_BG}; }}"
        )

        self.btn_load_more = QPushButton(f"さらに {_PAGE_SIZE} 件読み込む")
        self.btn_load_more.setFixedHeight(30)
        self.btn_load_more.setStyleSheet(_btn_style)
        self.btn_load_more.clicked.connect(self._on_load_more)
        self.btn_load_more.setVisible(False)
        hl.addWidget(self.btn_load_more)

        self.btn_load_all = QPushButton("全件読み込む")
        self.btn_load_all.setFixedHeight(30)
        self.btn_load_all.setStyleSheet(_btn_style)
        self.btn_load_all.clicked.connect(self._on_load_all)
        self.btn_load_all.setVisible(False)
        hl.addWidget(self.btn_load_all)

        return bar

    # ── 公開API ───────────────────────────────────────────────────────────────

    def refresh(self) -> None:
        """ページ表示時に呼ばれる。列設定とドロップダウンをリロードする。"""
        self._load_column_config()
        self._apply_table_columns()
        self._load_dropdowns()

    # ── 内部処理 ──────────────────────────────────────────────────────────────

    def _load_dropdowns(self) -> None:
        vals = self._ds.get_dropdown_values()

        for combo, key in [
            (self.combo_holder, "holders"),
            (self.combo_sample, "samples"),
            (self.combo_test,   "tests"),
        ]:
            combo.blockSignals(True)
            combo.clear()
            combo.addItem("全て")
            combo.addItems(vals.get(key, []))
            combo.blockSignals(False)

    def _collect_filters(self) -> dict:
        filters: dict = {}
        if v := self.edit_date_from.text().strip():
            filters["date_from"] = v
        if v := self.edit_date_to.text().strip():
            filters["date_to"] = v
        if v := self.edit_request_no.text().strip():
            filters["request_no"] = v
        if v := self.edit_job_no.text().strip():
            filters["job_no"] = v
        if (h := self.combo_holder.currentText()) and h != "全て":
            filters["holder_names"] = [h]
        if (s := self.combo_sample.currentText()) and s != "全て":
            filters["sample_names"] = [s]
        if (t := self.combo_test.currentText()) and t != "全て":
            filters["test_names"] = [t]
        if (j := self.combo_judgment.currentText()) != "全て":
            filters["judgment_filter"] = j
        return filters

    def _on_search(self) -> None:
        self._display_limit = _PAGE_SIZE
        # limit=0 で全件取得してキャッシュ
        self._all_df = self._ds.get_data_page(**self._collect_filters(), limit=0)
        self._refresh_table()

    def _on_load_more(self) -> None:
        self._display_limit += _PAGE_SIZE
        self._refresh_table()

    def _on_load_all(self) -> None:
        if self._all_df is not None:
            self._display_limit = len(self._all_df)
        self._refresh_table()

    def _on_sort_column(self, col: int, ascending: bool) -> None:
        if self._all_df is not None and 0 <= col < len(self._visible_columns):
            col_key = self._visible_columns[col][1]
            self._all_df = self._all_df.sort_values(
                col_key, ascending=ascending, na_position="last",
            )
        self._refresh_table()

    def _refresh_table(self) -> None:
        if self._all_df is None:
            return
        total = len(self._all_df)
        shown = min(self._display_limit, total)
        self.label_count.setText(f"{shown} 件表示 / 全 {total} 件")
        self._populate_table(self._all_df.iloc[:shown])
        has_more = shown < total
        self.btn_load_more.setVisible(has_more)
        self.btn_load_all.setVisible(has_more)

    def _on_clear(self) -> None:
        self.edit_date_from.clear()
        self.edit_date_to.clear()
        self.edit_request_no.clear()
        self.edit_job_no.clear()
        self.combo_holder.setCurrentIndex(0)
        self.combo_sample.setCurrentIndex(0)
        self.combo_test.setCurrentIndex(0)
        self.combo_judgment.setCurrentIndex(0)
        self.table.setRowCount(0)
        self._all_df = None
        self.label_count.setText("検索ボタンを押してデータを表示")
        self.btn_load_more.setVisible(False)
        self.btn_load_all.setVisible(False)

    def _populate_table(self, df: pd.DataFrame) -> None:
        self.table.setRowCount(len(df))
        for row_idx in range(len(df)):
            row = df.iloc[row_idx]
            for col_idx, (_, col_key) in enumerate(self._visible_columns):
                val = row.get(col_key, "")
                text = self._format_cell(col_key, val)
                item = QTableWidgetItem(text)

                if col_key == "test_grade_code":
                    judgment_str = str(val) if val is not None else ""
                    if judgment_str not in ("NN", "--", "", "nan", "None"):
                        item.setBackground(QColor("#fef2f2"))
                        item.setForeground(QColor(_DANGER))
                        font = item.font()
                        font.setBold(True)
                        item.setFont(font)

                self.table.setItem(row_idx, col_idx, item)

            # グラフボタン (最終列)
            hg   = str(row.get("holder_group_code", ""))
            vs   = str(row.get("valid_sample_set_code", ""))
            vt   = str(row.get("valid_test_set_code", ""))
            unit = str(row.get("test_unit_name", ""))
            tname = str(row.get("valid_test_display_name", ""))
            btn = QPushButton()
            btn.setIcon(get_icon(":/icons/graph.svg", "#4a8cff", 14))
            btn.setIconSize(QSize(14, 14))
            btn.setFixedSize(28, 28)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setToolTip("トレンドグラフ")
            btn.setStyleSheet(
                "QPushButton { background:#eff6ff; border:1px solid #bfdbfe;"
                " border-radius:4px; padding:0; min-height:0; min-width:0; }"
                "QPushButton:hover { background:#dbeafe; border-color:#4a8cff; }"
            )
            btn.clicked.connect(
                lambda _=False, h=hg, v=vs, t=vt, u=unit, n=tname:
                    self._on_graph_row(h, v, t, u, n)
            )
            cell_w = QWidget()
            cell_w.setStyleSheet("background:transparent;")
            cell_l = QHBoxLayout(cell_w)
            cell_l.setContentsMargins(4, 4, 4, 4)
            cell_l.setAlignment(Qt.AlignmentFlag.AlignCenter)
            cell_l.addWidget(btn)
            self.table.setCellWidget(row_idx, len(self._visible_columns), cell_w)

    def _on_graph_row(
        self, hg_code: str, vsset: str, vtest: str, unit: str, test_name: str
    ) -> None:
        data   = self._ds.get_trend_data(hg_code, vsset, vtest)
        bounds = self._ds.get_anomaly_bounds(hg_code, vsset, vtest)
        spec   = self._ds.get_spec_limits(hg_code, vsset, vtest)
        dlg = TrendDialog(data, bounds, spec, unit, test_name, self)
        dlg.exec()

    def _on_export_csv(self) -> None:
        if self._all_df is None or self._all_df.empty:
            QMessageBox.information(
                self, "CSV出力", "エクスポートするデータがありません。\n先に検索を実行してください。"
            )
            return

        path, _ = QFileDialog.getSaveFileName(
            self, "CSV出力", "bunseki_export.csv", "CSV (*.csv)"
        )
        if not path:
            return

        # 全列・全件（表示制限なし）を出力
        export_df = self._all_df.copy()

        # サンプリング日を読みやすい形式に変換
        if "sample_sampling_date" in export_df.columns:
            export_df["sample_sampling_date"] = export_df["sample_sampling_date"].apply(
                lambda v: self._format_cell("sample_sampling_date", v)
            )

        export_df.to_csv(path, index=False, encoding="utf-8-sig")
        QMessageBox.information(
            self, "CSV出力",
            f"CSVを出力しました。\n{len(export_df):,} 件 / 全列\n{path}"
        )

    # ── ヘルパー ──────────────────────────────────────────────────────────────

    @staticmethod
    def _format_cell(col_key: str, val) -> str:
        if val is None or (isinstance(val, float) and np.isnan(val)):
            return ""
        if col_key == "sample_sampling_date":
            s = str(int(float(val)))
            if len(s) >= 8:
                return f"{s[:4]}-{s[4:6]}-{s[6:8]}"
            return s
        return str(val)

    def _input(self, placeholder: str, width: int) -> QLineEdit:
        w = QLineEdit()
        w.setPlaceholderText(placeholder)
        w.setFixedWidth(width)
        self._style_input(w)
        return w

    def _combo(self, width: int) -> QComboBox:
        c = QComboBox()
        c.setFixedWidth(width)
        self._style_combo(c)
        return c

    @staticmethod
    def _label(text: str) -> QLabel:
        lbl = QLabel(text)
        lbl.setStyleSheet(f"font-size:12px; font-weight:600; color:{_TEXT2}; border:none;")
        return lbl

    @staticmethod
    def _style_input(widget: QLineEdit) -> None:
        widget.setFixedHeight(30)
        widget.setStyleSheet(
            f"QLineEdit {{ border:1px solid {_BORDER}; border-radius:4px;"
            f" padding:4px 8px; font-size:12px; color:{_TEXT}; background:{_BG2}; }}"
            f"QLineEdit:focus {{ border-color:{_ACCENT}; }}"
        )

    @staticmethod
    def _style_combo(widget: QComboBox) -> None:
        widget.setFixedHeight(30)
        widget.setStyleSheet(
            f"QComboBox {{ border:1px solid {_BORDER}; border-radius:4px;"
            f" padding:4px 8px; font-size:12px; color:{_TEXT}; background:{_BG2}; }}"
            f"QComboBox:focus {{ border-color:{_ACCENT}; }}"
            f"QComboBox::drop-down {{ border:none; width:20px; }}"
        )
