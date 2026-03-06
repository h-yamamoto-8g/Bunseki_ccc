"""AnalysisTargetsUI — 分析対象テーブルの純粋レイアウト（generated UI 使用）。

ビジネスロジック・task_store・DataLoader の import 禁止。
"""
from __future__ import annotations

from PySide6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView,
    QAbstractItemView, QComboBox, QLineEdit, QDialog,
    QDialogButtonBox, QTabWidget, QApplication,
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
        self._grouped_samples: dict[str, list[dict]] = {}
        self._deleted_codes: set[str] = set()
        self._added_samples: list[str] = []
        self._edit_mode = False

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

        # ── QTableView → QTabWidget に置換 ─────────────────────────────
        tgt_layout = self._form.verticalLayout_2
        tgt_layout.removeWidget(self._form.tableView_targets)
        self._form.tableView_targets.deleteLater()

        self.tab_widget = QTabWidget()
        tgt_layout.addWidget(self.tab_widget)

        # ── シグナル接続 ──────────────────────────────────────────────────
        self.edit_btn.clicked.connect(self.edit_requested)
        self._form.btn_back.clicked.connect(self.back_requested)
        self._form.btn_next.clicked.connect(self._go_next)

    # ── Public API ────────────────────────────────────────────────────────────

    def set_samples(
        self,
        grouped_samples: dict[str, list[dict]],
        deleted_codes: set[str],
        added_samples: list[str],
    ) -> None:
        self._grouped_samples = grouped_samples
        self._deleted_codes = set(deleted_codes)
        self._added_samples = list(added_samples)
        self._rebuild_tabs()

    def set_editable(self, editable: bool) -> None:
        self._edit_mode = editable
        self.add_sample_btn.setVisible(editable)
        self._rebuild_tabs()

    def show_edit_btn(self, visible: bool) -> None:
        self.edit_btn.setVisible(visible)

    def set_nav_visible(self, visible: bool) -> None:
        self._form.btn_next.setVisible(visible)
        self._form.btn_back.setVisible(visible)

    def add_free_sample(self, name: str) -> None:
        if name and name not in self._added_samples:
            self._added_samples.append(name)
            self.edited_badge.setVisible(True)
            self.content_edited.emit()
            self._rebuild_tabs()

    def apply_delete(self, code: str, is_free: bool) -> None:
        if is_free:
            name = code.removeprefix("FREE_")
            if name in self._added_samples:
                self._added_samples.remove(name)
        else:
            self._deleted_codes.add(code)
        self.edited_badge.setVisible(True)
        self.content_edited.emit()
        self._rebuild_tabs()

    # ── Internal ──────────────────────────────────────────────────────────────

    _HEADERS = ["依頼番号", "JOB番号", "採取日", "サンプル名", "中央値", "最大値", "最小値", ""]

    _TARGET_SORT_KEYS = [
        "sample_request_number", "sample_job_number", "sample_sampling_date",
        "valid_sample_display_name",
    ]

    def _rebuild_tabs(self) -> None:
        current_idx = self.tab_widget.currentIndex()
        self.tab_widget.clear()

        if not self._grouped_samples:
            self.tab_widget.addTab(QLabel("データがありません"), "（なし）")
            return

        for test_name, samples in self._grouped_samples.items():
            table = self._build_table(samples)
            self.tab_widget.addTab(table, test_name)

        if 0 <= current_idx < self.tab_widget.count():
            self.tab_widget.setCurrentIndex(current_idx)

    def _build_table(self, samples: list[dict]) -> QTableWidget:
        table = QTableWidget(0, len(self._HEADERS))
        table.setHorizontalHeaderLabels(self._HEADERS)
        table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        table.setAlternatingRowColors(True)
        hh = table.horizontalHeader()
        hh.setMinimumSectionSize(60)
        for i, mode in enumerate([
            QHeaderView.ResizeMode.ResizeToContents,  # 依頼番号
            QHeaderView.ResizeMode.ResizeToContents,  # JOB番号
            QHeaderView.ResizeMode.ResizeToContents,  # 採取日
            QHeaderView.ResizeMode.Stretch,           # サンプル名
            QHeaderView.ResizeMode.ResizeToContents,  # 中央値
            QHeaderView.ResizeMode.ResizeToContents,  # 最大値
            QHeaderView.ResizeMode.ResizeToContents,  # 最小値
            QHeaderView.ResizeMode.Fixed,             # 削除
        ]):
            hh.setSectionResizeMode(i, mode)
        table.setColumnWidth(7, 44)
        vh = table.verticalHeader()
        vh.setDefaultSectionSize(36)

        # ソート用データ保持
        table._samples = samples  # type: ignore[attr-defined]

        def _on_sort(col: int, ascending: bool, tbl: QTableWidget = table) -> None:
            if col < len(self._TARGET_SORT_KEYS):
                key = self._TARGET_SORT_KEYS[col]
                tbl._samples.sort(  # type: ignore[attr-defined]
                    key=lambda s: str(s.get(key, "")), reverse=not ascending,
                )
                self._refresh_table(tbl, tbl._samples)  # type: ignore[attr-defined]

        enable_row_numbers_and_sort(table, _on_sort)

        self._refresh_table(table, samples)
        return table

    def _refresh_table(self, table: QTableWidget, samples: list[dict]) -> None:
        table.setRowCount(0)
        visible = [s for s in samples
                   if s["valid_sample_set_code"] not in self._deleted_codes]
        for s in visible:
            self._add_row(table, s, free=False)
        # 追加サンプルは最初のタブのみに表示
        if self.tab_widget.indexOf(table) == 0:
            for name in self._added_samples:
                self._add_row(table, {
                    "valid_sample_set_code": f"FREE_{name}",
                    "valid_sample_display_name": name,
                    "sample_request_number": "",
                    "sample_job_number": "",
                    "sample_sampling_date": "",
                    "median": None, "max": None, "min": None,
                }, free=True)

    def _add_row(self, table: QTableWidget, s: dict, free: bool) -> None:
        row = table.rowCount()
        table.insertRow(row)
        median = f"{s['median']:.3g}" if s.get("median") is not None else "—"
        max_v  = f"{s['max']:.3g}"    if s.get("max")    is not None else "—"
        min_v  = f"{s['min']:.3g}"    if s.get("min")    is not None else "—"
        vals = [
            s.get("sample_request_number", ""),
            s.get("sample_job_number", ""),
            s.get("sample_sampling_date", ""),
            s.get("valid_sample_display_name", ""),
            median, max_v, min_v,
        ]
        for col, v in enumerate(vals):
            item = QTableWidgetItem(str(v))
            item.setData(Qt.ItemDataRole.UserRole, s["valid_sample_set_code"])
            if free:
                item.setForeground(QColor("#7c3aed"))
            table.setItem(row, col, item)

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
            table.setCellWidget(row, 7, cell_w)

    def _go_next(self) -> None:
        visible_codes = []
        for samples in self._grouped_samples.values():
            for s in samples:
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
