"""AnalysisTargetsUI — 分析対象テーブルの純粋レイアウト（generated UI 使用）。

ビジネスロジック・task_store・DataLoader の import 禁止。
"""
from __future__ import annotations

from PySide6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView,
    QAbstractItemView, QComboBox, QLineEdit, QDialog,
    QDialogButtonBox, QApplication,
)
from PySide6.QtCore import Signal, Qt, QSize
from PySide6.QtGui import QColor

from app.ui.widgets.icon_utils import get_icon
from app.ui.widgets.table_utils import enable_row_numbers_and_sort

from app.ui.generated.ui_stateanalysistargets import Ui_PageStateTarget


class AnalysisTargetsUI(QWidget):
    """分析対象テーブル (純粋レイアウト)。

    Signals:
        next_requested(vsset_codes, deleted_codes, added_samples): 次へ
        back_requested(): 戻る
        add_sample_requested(): サンプル追加ダイアログ要求
        delete_row_requested(code, is_free): 行削除要求
        edit_requested(): 編集ボタン押下
    """

    next_requested = Signal(list, list, list)
    back_requested = Signal()
    add_sample_requested = Signal()
    delete_row_requested = Signal(str, bool)
    edit_requested = Signal()
    content_edited = Signal()   # サンプル追加/削除で内容変更時

    def __init__(self, parent=None):
        super().__init__(parent)
        self._flat_samples: list[dict] = []
        self._deleted_codes: set[str] = set()
        self._added_samples: list[str] = []
        self._edit_mode = False
        self._column_config: list[dict] = []  # 表示列設定

        self._form = Ui_PageStateTarget()
        self._form.setupUi(self)

        # ── グローバル QSS でリセットされるデフォルト spacing を明示設定 ──
        self._form.verticalLayout.setSpacing(8)
        self._form.verticalLayout.setContentsMargins(8, 8, 8, 8)

        # ── 生成ヘッダーを除去 (タスク情報は共通ヘッダーで表示) ──────────
        self._form.verticalLayout.removeWidget(self._form.widget_header)
        self._form.widget_header.setVisible(False)

        # ── アクションバー ────────────────────────────────────────────────
        _action_bar = QWidget()
        _action_bar.setMaximumHeight(44)
        _ab = QHBoxLayout(_action_bar)
        _ab.setContentsMargins(0, 4, 0, 4)
        _ab.setSpacing(8)

        self.edited_badge = QLabel("編集済み")
        self.edited_badge.setStyleSheet(
            "color:#f59e0b; font-size:11px; font-weight:600;"
            " background:rgba(245,158,11,0.08); border:1px solid rgba(245,158,11,0.3);"
            " border-radius:4px; padding:2px 8px;"
        )
        self.edited_badge.setVisible(False)
        _ab.addWidget(self.edited_badge)
        _ab.addStretch()

        self.add_sample_btn = QPushButton("＋ サンプル追加")
        self.add_sample_btn.setFixedHeight(30)
        self.add_sample_btn.setVisible(False)
        self.add_sample_btn.clicked.connect(self.add_sample_requested)
        _ab.addWidget(self.add_sample_btn)

        self.print_btn = QPushButton("印刷")
        self.print_btn.setFixedHeight(30)
        _ab.addWidget(self.print_btn)

        self.edit_btn = QPushButton("編集")
        self.edit_btn.setFixedHeight(30)
        self.edit_btn.setVisible(False)
        _ab.addWidget(self.edit_btn)

        self._form.verticalLayout.insertWidget(0, _action_bar)

        # ── QTableView → 単一テーブルに置換 ────────────────────────────
        tgt_layout = self._form.verticalLayout_2
        tgt_layout.removeWidget(self._form.tableView_targets)
        self._form.tableView_targets.deleteLater()

        self._table = QTableWidget()
        tgt_layout.addWidget(self._table)

        # ── シグナル接続 ──────────────────────────────────────────────────
        self.edit_btn.clicked.connect(self.edit_requested)
        self._form.btn_back.setVisible(False)
        self._form.btn_next.setText("完了")
        self._form.btn_next.clicked.connect(self._go_next)

    # ── Public API ────────────────────────────────────────────────────────────

    def set_column_config(self, columns: list[dict]) -> None:
        """表示列設定をセットする。columns は visible=True のもののみ。"""
        self._column_config = columns

    def set_samples(
        self,
        flat_samples: list[dict],
        deleted_codes: set[str],
        added_samples: list[str],
    ) -> None:
        self._flat_samples = flat_samples
        self._deleted_codes = set(deleted_codes)
        self._added_samples = list(added_samples)
        self._rebuild_table()

    def set_editable(self, editable: bool) -> None:
        self._edit_mode = editable
        self.add_sample_btn.setVisible(editable)
        self._rebuild_table()

    def show_edit_btn(self, visible: bool) -> None:
        self.edit_btn.setVisible(visible)

    def set_nav_visible(self, visible: bool) -> None:
        """完了ボタンの表示を制御する。"""
        self._form.btn_next.setVisible(visible)

    def add_free_sample(self, name: str) -> None:
        if name and name not in self._added_samples:
            self._added_samples.append(name)
            self.edited_badge.setVisible(True)
            self.content_edited.emit()
            self._rebuild_table()

    def apply_delete(self, code: str, is_free: bool) -> None:
        if is_free:
            name = code.removeprefix("FREE_")
            if name in self._added_samples:
                self._added_samples.remove(name)
        else:
            self._deleted_codes.add(code)
        self.edited_badge.setVisible(True)
        self.content_edited.emit()
        self._rebuild_table()

    # ── Internal ──────────────────────────────────────────────────────────────

    # 列キー → Stretch にする列
    _STRETCH_KEYS = {"valid_sample_display_name"}

    # ソート可能な列キー
    _SORTABLE_KEYS = {
        "sample_request_number", "sample_job_number",
        "sample_sampling_date", "valid_sample_display_name",
    }

    def _visible_columns(self) -> list[dict]:
        """表示対象の列設定を返す。未設定時はフォールバック。"""
        if self._column_config:
            return self._column_config
        return [
            {"key": "sample_request_number", "label": "依頼番号", "visible": True},
            {"key": "sample_job_number", "label": "JOB番号", "visible": True},
            {"key": "sample_sampling_date", "label": "採取日", "visible": True},
            {"key": "valid_sample_display_name", "label": "サンプル名", "visible": True},
            {"key": "median", "label": "中央値", "visible": True},
            {"key": "max", "label": "最大値", "visible": True},
            {"key": "min", "label": "最小値", "visible": True},
        ]

    def _rebuild_table(self) -> None:
        vis_cols = self._visible_columns()
        headers = [c["label"] for c in vis_cols] + [""]
        table = self._table
        table.clear()
        table.setColumnCount(len(headers))
        table.setHorizontalHeaderLabels(headers)
        table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        table.setAlternatingRowColors(True)
        hh = table.horizontalHeader()
        hh.setMinimumSectionSize(60)
        for i, c in enumerate(vis_cols):
            if c["key"] in self._STRETCH_KEYS:
                hh.setSectionResizeMode(i, QHeaderView.ResizeMode.Stretch)
            else:
                hh.setSectionResizeMode(i, QHeaderView.ResizeMode.ResizeToContents)
        # 操作列 (末尾)
        action_col = len(vis_cols)
        hh.setSectionResizeMode(action_col, QHeaderView.ResizeMode.Fixed)
        table.setColumnWidth(action_col, 44)
        vh = table.verticalHeader()
        vh.setDefaultSectionSize(36)

        # ソート用データ保持
        table._samples = list(self._flat_samples)  # type: ignore[attr-defined]

        def _on_sort(col: int, ascending: bool, tbl: QTableWidget = table) -> None:
            if col < len(vis_cols) and vis_cols[col]["key"] in self._SORTABLE_KEYS:
                key = vis_cols[col]["key"]
                tbl._samples.sort(  # type: ignore[attr-defined]
                    key=lambda s: str(s.get(key, "")), reverse=not ascending,
                )
                self._refresh_table(tbl, tbl._samples)  # type: ignore[attr-defined]

        enable_row_numbers_and_sort(table, _on_sort)

        self._refresh_table(table, table._samples)  # type: ignore[attr-defined]

    def _refresh_table(self, table: QTableWidget, samples: list[dict]) -> None:
        table.setRowCount(0)
        visible = [s for s in samples
                   if s["valid_sample_set_code"] not in self._deleted_codes]
        for s in visible:
            self._add_row(table, s, free=False)
        for name in self._added_samples:
            self._add_row(table, {
                "valid_sample_set_code": f"FREE_{name}",
                "valid_sample_display_name": name,
                "sample_request_number": "",
                "sample_job_number": "",
                "sample_sampling_date": "",
                "median": None, "max": None, "min": None,
            }, free=True)

    @staticmethod
    def _extract_cell(s: dict, key: str) -> str:
        """列キーからセル表示値を取得する。"""
        if key in ("median", "max", "min"):
            v = s.get(key)
            return f"{v:.3g}" if v is not None else "—"
        v = s.get(key, "")
        if v is None:
            return ""
        s_val = str(v)
        return "" if s_val in ("nan", "None") else s_val

    def _add_row(self, table: QTableWidget, s: dict, free: bool) -> None:
        vis_cols = self._visible_columns()
        row = table.rowCount()
        table.insertRow(row)

        for col, c in enumerate(vis_cols):
            text = self._extract_cell(s, c["key"])
            item = QTableWidgetItem(text)
            item.setData(Qt.ItemDataRole.UserRole, s["valid_sample_set_code"])
            if free:
                item.setForeground(QColor("#7c3aed"))
            table.setItem(row, col, item)

        action_col = len(vis_cols)
        if self._edit_mode:
            cell_w = QWidget()
            cell_w.setStyleSheet("background:transparent;")
            cell_l = QHBoxLayout(cell_w)
            cell_l.setContentsMargins(4, 4, 4, 4)
            cell_l.setAlignment(Qt.AlignmentFlag.AlignCenter)
            del_btn = QPushButton()
            del_btn.setIcon(get_icon(":/icons/cancel.svg", "#ef4444", 14))
            del_btn.setIconSize(QSize(14, 14))
            del_btn.setFixedSize(28, 28)
            del_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            del_btn.setToolTip("削除")
            del_btn.setStyleSheet(
                "QPushButton { background:transparent; border:1px solid #e5e7eb;"
                " border-radius:4px; padding:0; min-height:0; min-width:0; }"
                "QPushButton:hover { background:rgba(239,68,68,0.10);"
                " border-color:#ef4444; }"
            )
            code = s["valid_sample_set_code"]
            del_btn.clicked.connect(
                lambda _=False, c=code, f=free: self.delete_row_requested.emit(c, f)
            )
            cell_l.addWidget(del_btn)
            table.setCellWidget(row, action_col, cell_w)

    def _go_next(self) -> None:
        visible_codes = []
        for s in self._flat_samples:
            code = s["valid_sample_set_code"]
            if code not in self._deleted_codes and code not in visible_codes:
                visible_codes.append(code)
        self.next_requested.emit(
            visible_codes,
            list(self._deleted_codes),
            list(self._added_samples),
        )


class AddSampleDialog(QDialog):
    def __init__(self, valid_samples: list[dict], parent=None):
        super().__init__(parent)
        self.setWindowTitle("サンプル追加")
        self.setFixedSize(400, 220)
        self._name = ""

        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.addWidget(QLabel("サンプル名をリストから選択、または自由記入してください。"))

        self.combo = QComboBox()
        self.combo.addItem("")
        for s in valid_samples:
            self.combo.addItem(s["display_name"], s["set_code"])
        layout.addWidget(self.combo)

        layout.addWidget(QLabel("または自由記入:"))
        self.line = QLineEdit()
        self.line.setPlaceholderText("サンプル名を入力")
        layout.addWidget(self.line)

        btns = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        btns.accepted.connect(self._accept)
        btns.rejected.connect(self.reject)
        layout.addWidget(btns)

    def _accept(self) -> None:
        free = self.line.text().strip()
        self._name = free if free else self.combo.currentText()
        self.accept()

    def selected_name(self) -> str:
        return self._name
