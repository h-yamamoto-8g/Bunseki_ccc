"""ログページ — 分析装置の使用履歴 / 調整試薬管理。"""
from __future__ import annotations

from datetime import date

from PySide6.QtCore import Qt, QUrl
from PySide6.QtGui import QColor, QDesktopServices
from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTabWidget,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from app.config import CURRENT_USER
from app.core.reagent_store import SHELF_LIFE_TYPES, SHELF_LIFE_LABELS, calc_expiry
from app.services.data_service import DataService
from app.services.log_service import LogService
from app.ui.widgets.date_edit import DateEdit
from app.ui.widgets.table_utils import enable_row_numbers_and_sort

# ── デザイントークン ──────────────────────────────────────────────────────────
_BG2 = "#ffffff"
_TEXT = "#1e293b"
_TEXT2 = "#64748b"
_ACCENT = "#3b82f6"
_BORDER = "#e2e8f0"
_DANGER = "#ef4444"

_BTN_PRIMARY = (
    f"QPushButton {{ background:{_ACCENT}; color:white; border:none;"
    f" padding:4px 12px; border-radius:5px; font-size:12px; font-weight:600; }}"
    f"QPushButton:hover {{ background:#2563eb; }}"
)
_BTN_SECONDARY = (
    f"QPushButton {{ background:{_BG2}; color:{_TEXT2}; border:1px solid {_BORDER};"
    f" padding:4px 12px; border-radius:5px; font-size:12px; font-weight:600; }}"
    f"QPushButton:hover {{ background:#f1f5f9; }}"
)
_BTN_DANGER = (
    f"QPushButton {{ background:#fef2f2; color:{_DANGER}; border:1px solid #fecaca;"
    f" padding:4px 12px; border-radius:5px; font-size:12px; font-weight:600; }}"
    f"QPushButton:hover {{ background:#fee2e2; }}"
)
_TABLE_STYLE = (
    f"QTableWidget {{ border:1px solid {_BORDER}; border-radius:6px;"
    f" background:{_BG2}; gridline-color:{_BORDER}; }}"
    f"QHeaderView::section {{ background:#f1f5f9; color:{_TEXT};"
    f" font-size:12px; font-weight:600; padding:6px;"
    f" border:none; border-bottom:1px solid {_BORDER}; }}"
    f"QTableWidget::item {{ padding:4px 8px; font-size:12px; color:{_TEXT}; }}"
)


class LogPage(QWidget):
    """ログページ — タブで分析装置 / 調整試薬を切り替え。"""

    def __init__(
        self,
        log_service: LogService,
        data_service: DataService,
        parent: QWidget | None = None,
    ):
        super().__init__(parent)
        self._svc = log_service
        self._ds = data_service
        self._build_ui()

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(24, 16, 24, 16)
        root.setSpacing(12)

        title = QLabel("ログ")
        title.setStyleSheet(f"font-size:18px; font-weight:700; color:{_TEXT};")
        root.addWidget(title)

        self.tabs = QTabWidget()
        self.tabs.setStyleSheet(
            f"QTabWidget::pane {{ border:1px solid {_BORDER}; border-radius:6px;"
            f" background:{_BG2}; }}"
            f"QTabBar::tab {{ padding:6px 16px; font-size:12px; font-weight:600;"
            f" border:1px solid {_BORDER}; border-bottom:none; border-radius:4px 4px 0 0;"
            f" background:#f1f5f9; color:{_TEXT2}; margin-right:2px; }}"
            f"QTabBar::tab:selected {{ background:{_BG2}; color:{_TEXT}; }}"
        )

        self._equipment_tab = EquipmentTab(self._svc, self._ds)
        self._reagent_tab = ReagentTab(self._svc, self._ds)

        self.tabs.addTab(self._equipment_tab, "分析装置")
        self.tabs.addTab(self._reagent_tab, "調整試薬")
        root.addWidget(self.tabs, 1)

    def refresh(self) -> None:
        self._equipment_tab.refresh()
        self._reagent_tab.refresh()


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  分析装置タブ
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


class EquipmentTab(QWidget):
    """分析装置マスタ一覧 — 名前・リンク・分析項目。"""

    def __init__(self, svc: LogService, ds: DataService, parent: QWidget | None = None):
        super().__init__(parent)
        self._svc = svc
        self._ds = ds
        self._data: list[dict] = []
        self._build_ui()

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(12, 12, 12, 12)
        root.setSpacing(8)

        header = QHBoxLayout()
        header.addStretch()

        self.btn_edit = QPushButton("編集")
        self.btn_edit.setFixedHeight(28)
        self.btn_edit.setStyleSheet(_BTN_SECONDARY)
        self.btn_edit.clicked.connect(self._on_edit_selected)
        header.addWidget(self.btn_edit)

        self.btn_del = QPushButton("削除")
        self.btn_del.setFixedHeight(28)
        self.btn_del.setStyleSheet(_BTN_DANGER)
        self.btn_del.clicked.connect(self._on_delete_selected)
        header.addWidget(self.btn_del)

        self.btn_new = QPushButton("+ 新規")
        self.btn_new.setFixedHeight(28)
        self.btn_new.setStyleSheet(_BTN_PRIMARY)
        self.btn_new.clicked.connect(self._on_new)
        header.addWidget(self.btn_new)

        root.addLayout(header)

        self.table = QTableWidget()
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(["分析装置名", "リンク", "分析項目"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.verticalHeader().setDefaultSectionSize(36)
        self.table.setStyleSheet(_TABLE_STYLE)
        self.table.doubleClicked.connect(self._on_open_link)
        enable_row_numbers_and_sort(self.table, self._on_sort)
        root.addWidget(self.table, 1)

    _SORT_KEYS = ["name", "link", "holder_group_name"]

    def _on_sort(self, col: int, ascending: bool) -> None:
        if col < len(self._SORT_KEYS):
            key = self._SORT_KEYS[col]
            self._data.sort(key=lambda x: x.get(key, ""), reverse=not ascending)
            self._populate(self._data)

    def refresh(self) -> None:
        self._data = self._svc.get_all_equipment()
        self._populate(self._data)

    def _populate(self, items: list[dict]) -> None:
        self.table.setRowCount(len(items))
        for row, item in enumerate(items):
            self.table.setItem(row, 0, QTableWidgetItem(item.get("name", "")))
            link_item = QTableWidgetItem(item.get("link", ""))
            link_item.setForeground(QColor(_ACCENT))
            self.table.setItem(row, 1, link_item)
            self.table.setItem(row, 2, QTableWidgetItem(item.get("holder_group_name", "")))

    def _get_selected_id(self) -> str | None:
        row = self.table.currentRow()
        if row < 0 or row >= len(self._data):
            QMessageBox.information(self, "選択なし", "行を選択してください。")
            return None
        return self._data[row]["id"]

    def _on_open_link(self) -> None:
        row = self.table.currentRow()
        if row < 0 or row >= len(self._data):
            return
        link = self._data[row].get("link", "")
        if link:
            QDesktopServices.openUrl(QUrl.fromLocalFile(link))

    def _on_new(self) -> None:
        hg = self._ds.get_holder_groups()
        dlg = EquipmentDialog(holder_groups=hg, parent=self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            d = dlg.result_data()
            self._svc.create_equipment(
                name=d["name"], link=d["link"],
                holder_group_code=d["holder_group_code"],
                holder_group_name=d["holder_group_name"],
                created_by=CURRENT_USER,
            )
            self.refresh()

    def _on_edit_selected(self) -> None:
        item_id = self._get_selected_id()
        if not item_id:
            return
        item = self._svc.get_equipment(item_id)
        if not item:
            return
        hg = self._ds.get_holder_groups()
        dlg = EquipmentDialog(holder_groups=hg, item=item, parent=self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            d = dlg.result_data()
            self._svc.update_equipment(
                item_id, name=d["name"], link=d["link"],
                holder_group_code=d["holder_group_code"],
                holder_group_name=d["holder_group_name"],
            )
            self.refresh()

    def _on_delete_selected(self) -> None:
        item_id = self._get_selected_id()
        if not item_id:
            return
        item = self._svc.get_equipment(item_id)
        if not item:
            return
        reply = QMessageBox.question(
            self, "削除確認",
            f"「{item.get('name', '')}」を削除しますか？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            self._svc.delete_equipment(item_id)
            self.refresh()


# ── 分析装置ダイアログ ─────────────────────────────────────────────────────────


class EquipmentDialog(QDialog):
    def __init__(
        self,
        holder_groups: list[dict],
        item: dict | None = None,
        parent: QWidget | None = None,
    ):
        super().__init__(parent)
        self._item = item
        self._hg = holder_groups
        self.setWindowTitle("分析装置編集" if item else "分析装置作成")
        self.resize(460, 220)
        self._build_ui()
        if item:
            self._load(item)

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(20, 16, 20, 16)
        root.setSpacing(12)

        self.edit_name = QLineEdit()
        self.edit_name.setPlaceholderText("例: ICP-OES")
        _style_input(self.edit_name)
        root.addLayout(_row("装置名 *", self.edit_name))

        self.edit_link = QLineEdit()
        self.edit_link.setPlaceholderText("Excelファイルのパス")
        _style_input(self.edit_link)
        root.addLayout(_row("リンク", self.edit_link))

        self.combo_hg = QComboBox()
        self.combo_hg.setFixedHeight(30)
        for hg in self._hg:
            self.combo_hg.addItem(
                hg.get("holder_group_name", ""),
                hg.get("holder_group_code", ""),
            )
        root.addLayout(_row("分析項目 *", self.combo_hg))

        root.addStretch()
        btns = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        btns.button(QDialogButtonBox.StandardButton.Ok).setText("保存")
        btns.button(QDialogButtonBox.StandardButton.Cancel).setText("キャンセル")
        btns.accepted.connect(self._on_ok)
        btns.rejected.connect(self.reject)
        root.addWidget(btns)

    def _load(self, item: dict) -> None:
        self.edit_name.setText(item.get("name", ""))
        self.edit_link.setText(item.get("link", ""))
        idx = self.combo_hg.findData(item.get("holder_group_code", ""))
        if idx >= 0:
            self.combo_hg.setCurrentIndex(idx)

    def _on_ok(self) -> None:
        if not self.edit_name.text().strip():
            QMessageBox.warning(self, "入力エラー", "装置名を入力してください。")
            return
        if self.combo_hg.currentIndex() < 0:
            QMessageBox.warning(self, "入力エラー", "分析項目を選択してください。")
            return
        self.accept()

    def result_data(self) -> dict:
        return {
            "name": self.edit_name.text().strip(),
            "link": self.edit_link.text().strip(),
            "holder_group_code": self.combo_hg.currentData(),
            "holder_group_name": self.combo_hg.currentText(),
        }


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  調整試薬タブ
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


class ReagentTab(QWidget):
    """調整試薬マスタ + 履歴管理。

    上半分: マスタ一覧
    下半分: 選択した試薬の調整履歴
    """

    def __init__(self, svc: LogService, ds: DataService, parent: QWidget | None = None):
        super().__init__(parent)
        self._svc = svc
        self._ds = ds
        self._master_data: list[dict] = []
        self._history_data: list[dict] = []
        self._selected_reagent: dict | None = None
        self._build_ui()

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(12, 12, 12, 12)
        root.setSpacing(8)

        # ── マスタ部 ──
        master_header = QHBoxLayout()
        lbl = QLabel("試薬マスタ")
        lbl.setStyleSheet(f"font-size:14px; font-weight:600; color:{_TEXT};")
        master_header.addWidget(lbl)
        master_header.addStretch()

        self.btn_m_edit = QPushButton("編集")
        self.btn_m_edit.setFixedHeight(28)
        self.btn_m_edit.setStyleSheet(_BTN_SECONDARY)
        self.btn_m_edit.clicked.connect(self._on_master_edit)
        master_header.addWidget(self.btn_m_edit)

        self.btn_m_del = QPushButton("削除")
        self.btn_m_del.setFixedHeight(28)
        self.btn_m_del.setStyleSheet(_BTN_DANGER)
        self.btn_m_del.clicked.connect(self._on_master_delete)
        master_header.addWidget(self.btn_m_del)

        self.btn_m_new = QPushButton("+ 新規")
        self.btn_m_new.setFixedHeight(28)
        self.btn_m_new.setStyleSheet(_BTN_PRIMARY)
        self.btn_m_new.clicked.connect(self._on_master_new)
        master_header.addWidget(self.btn_m_new)

        root.addLayout(master_header)

        self.master_table = QTableWidget()
        self.master_table.setColumnCount(3)
        self.master_table.setHorizontalHeaderLabels(["試薬名", "保存可能期間", "分析項目"])
        self.master_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.master_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.master_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.master_table.verticalHeader().setDefaultSectionSize(36)
        self.master_table.setStyleSheet(_TABLE_STYLE)
        self.master_table.clicked.connect(self._on_master_selected)
        enable_row_numbers_and_sort(self.master_table, self._on_master_sort)
        root.addWidget(self.master_table, 1)

        # ── 履歴部 ──
        hist_header = QHBoxLayout()
        self.lbl_history = QLabel("調整履歴")
        self.lbl_history.setStyleSheet(f"font-size:14px; font-weight:600; color:{_TEXT};")
        hist_header.addWidget(self.lbl_history)
        hist_header.addStretch()

        self.btn_h_edit = QPushButton("編集")
        self.btn_h_edit.setFixedHeight(28)
        self.btn_h_edit.setStyleSheet(_BTN_SECONDARY)
        self.btn_h_edit.clicked.connect(self._on_history_edit)
        hist_header.addWidget(self.btn_h_edit)

        self.btn_h_del = QPushButton("削除")
        self.btn_h_del.setFixedHeight(28)
        self.btn_h_del.setStyleSheet(_BTN_DANGER)
        self.btn_h_del.clicked.connect(self._on_history_delete)
        hist_header.addWidget(self.btn_h_del)

        self.btn_h_new = QPushButton("+ 調整記録")
        self.btn_h_new.setFixedHeight(28)
        self.btn_h_new.setStyleSheet(_BTN_PRIMARY)
        self.btn_h_new.clicked.connect(self._on_history_new)
        hist_header.addWidget(self.btn_h_new)

        root.addLayout(hist_header)

        self.history_table = QTableWidget()
        self.history_table.setColumnCount(4)
        self.history_table.setHorizontalHeaderLabels(
            ["調整日", "使用期限", "状態", "調整者"]
        )
        self.history_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.history_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.history_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.history_table.verticalHeader().setDefaultSectionSize(36)
        self.history_table.setStyleSheet(_TABLE_STYLE)
        enable_row_numbers_and_sort(self.history_table, self._on_history_sort)
        root.addWidget(self.history_table, 1)

    # ── マスタ操作 ────────────────────────────────────────────────────────────

    _MASTER_SORT_KEYS = ["name", "shelf_life", "holder_group_name"]

    def _on_master_sort(self, col: int, ascending: bool) -> None:
        if col < len(self._MASTER_SORT_KEYS):
            key = self._MASTER_SORT_KEYS[col]
            self._master_data.sort(key=lambda x: x.get(key, ""), reverse=not ascending)
            self._populate_master(self._master_data)

    def refresh(self) -> None:
        self._master_data = self._svc.get_all_reagents()
        self._populate_master(self._master_data)
        self._selected_reagent = None
        self._history_data = []
        self._populate_history([])
        self.lbl_history.setText("調整履歴")

    def _populate_master(self, items: list[dict]) -> None:
        self.master_table.setRowCount(len(items))
        for row, item in enumerate(items):
            self.master_table.setItem(row, 0, QTableWidgetItem(item.get("name", "")))
            shelf = SHELF_LIFE_LABELS.get(item.get("shelf_life", ""), item.get("shelf_life", ""))
            self.master_table.setItem(row, 1, QTableWidgetItem(shelf))
            self.master_table.setItem(row, 2, QTableWidgetItem(item.get("holder_group_name", "")))

    def _on_master_selected(self) -> None:
        row = self.master_table.currentRow()
        if row < 0 or row >= len(self._master_data):
            return
        self._selected_reagent = self._master_data[row]
        reagent_id = self._selected_reagent["id"]
        self._history_data = self._svc.get_reagent_history(reagent_id)
        self._populate_history(self._history_data)
        self.lbl_history.setText(f"調整履歴 — {self._selected_reagent.get('name', '')}")

    def _get_selected_master_id(self) -> str | None:
        row = self.master_table.currentRow()
        if row < 0 or row >= len(self._master_data):
            QMessageBox.information(self, "選択なし", "試薬を選択してください。")
            return None
        return self._master_data[row]["id"]

    def _on_master_new(self) -> None:
        hg = self._ds.get_holder_groups()
        dlg = ReagentDialog(holder_groups=hg, parent=self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            d = dlg.result_data()
            self._svc.create_reagent(
                name=d["name"], shelf_life=d["shelf_life"],
                holder_group_code=d["holder_group_code"],
                holder_group_name=d["holder_group_name"],
                created_by=CURRENT_USER,
            )
            self.refresh()

    def _on_master_edit(self) -> None:
        item_id = self._get_selected_master_id()
        if not item_id:
            return
        item = self._svc.get_reagent(item_id)
        if not item:
            return
        hg = self._ds.get_holder_groups()
        dlg = ReagentDialog(holder_groups=hg, item=item, parent=self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            d = dlg.result_data()
            self._svc.update_reagent(
                item_id, name=d["name"], shelf_life=d["shelf_life"],
                holder_group_code=d["holder_group_code"],
                holder_group_name=d["holder_group_name"],
            )
            self.refresh()

    def _on_master_delete(self) -> None:
        item_id = self._get_selected_master_id()
        if not item_id:
            return
        item = self._svc.get_reagent(item_id)
        if not item:
            return
        reply = QMessageBox.question(
            self, "削除確認",
            f"「{item.get('name', '')}」を削除しますか？\n関連する調整履歴も削除されます。",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            for h in self._svc.get_reagent_history(item_id):
                self._svc.delete_reagent_history(h["id"])
            self._svc.delete_reagent(item_id)
            self.refresh()

    # ── 履歴操作 ──────────────────────────────────────────────────────────────

    _HISTORY_SORT_KEYS = ["preparation_date", "expiry_date", "", "prepared_by"]

    def _on_history_sort(self, col: int, ascending: bool) -> None:
        if col < len(self._HISTORY_SORT_KEYS) and self._HISTORY_SORT_KEYS[col]:
            key = self._HISTORY_SORT_KEYS[col]
            self._history_data.sort(key=lambda x: x.get(key, ""), reverse=not ascending)
            self._populate_history(self._history_data)

    def _populate_history(self, items: list[dict]) -> None:
        self.history_table.setRowCount(len(items))
        today = date.today().isoformat()
        for row, item in enumerate(items):
            self.history_table.setItem(
                row, 0, QTableWidgetItem(item.get("preparation_date", ""))
            )
            self.history_table.setItem(
                row, 1, QTableWidgetItem(item.get("expiry_date", ""))
            )
            expiry = item.get("expiry_date", "")
            if expiry and expiry >= today:
                status = QTableWidgetItem("有効")
                status.setForeground(QColor("#16a34a"))
            else:
                status = QTableWidgetItem("期限切れ")
                status.setForeground(QColor("#94a3b8"))
            self.history_table.setItem(row, 2, status)
            self.history_table.setItem(
                row, 3, QTableWidgetItem(item.get("prepared_by", ""))
            )

    def _get_selected_history_id(self) -> str | None:
        row = self.history_table.currentRow()
        if row < 0 or row >= len(self._history_data):
            QMessageBox.information(self, "選択なし", "履歴行を選択してください。")
            return None
        return self._history_data[row]["id"]

    def _on_history_new(self) -> None:
        if not self._selected_reagent:
            QMessageBox.information(self, "選択なし", "まず試薬を選択してください。")
            return
        shelf = self._selected_reagent.get("shelf_life", "")
        dlg = ReagentHistoryDialog(shelf_life=shelf, parent=self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            self._svc.create_reagent_history(
                reagent_id=self._selected_reagent["id"],
                preparation_date=dlg.result_date(),
                shelf_life=shelf,
                prepared_by=CURRENT_USER,
            )
            self._on_master_selected()

    def _on_history_edit(self) -> None:
        if not self._selected_reagent:
            QMessageBox.information(self, "選択なし", "まず試薬を選択してください。")
            return
        hist_id = self._get_selected_history_id()
        if not hist_id:
            return
        row = self.history_table.currentRow()
        current_date = self._history_data[row].get("preparation_date", "")
        shelf = self._selected_reagent.get("shelf_life", "")
        dlg = ReagentHistoryDialog(
            shelf_life=shelf, current_date=current_date, parent=self,
        )
        if dlg.exec() == QDialog.DialogCode.Accepted:
            self._svc.update_reagent_history(
                hist_id, preparation_date=dlg.result_date(), shelf_life=shelf,
            )
            self._on_master_selected()

    def _on_history_delete(self) -> None:
        hist_id = self._get_selected_history_id()
        if not hist_id:
            return
        reply = QMessageBox.question(
            self, "削除確認", "この調整記録を削除しますか？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            self._svc.delete_reagent_history(hist_id)
            self._on_master_selected()


# ── 調整試薬ダイアログ ─────────────────────────────────────────────────────────


class ReagentDialog(QDialog):
    def __init__(
        self,
        holder_groups: list[dict],
        item: dict | None = None,
        parent: QWidget | None = None,
    ):
        super().__init__(parent)
        self._item = item
        self._hg = holder_groups
        self.setWindowTitle("試薬編集" if item else "試薬作成")
        self.resize(460, 240)
        self._build_ui()
        if item:
            self._load(item)

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(20, 16, 20, 16)
        root.setSpacing(12)

        self.edit_name = QLineEdit()
        self.edit_name.setPlaceholderText("例: 塩酸(1+1)")
        _style_input(self.edit_name)
        root.addLayout(_row("試薬名 *", self.edit_name))

        self.combo_shelf = QComboBox()
        self.combo_shelf.setFixedHeight(30)
        for code, label in SHELF_LIFE_TYPES:
            self.combo_shelf.addItem(label, code)
        root.addLayout(_row("保存期間 *", self.combo_shelf))

        self.combo_hg = QComboBox()
        self.combo_hg.setFixedHeight(30)
        for hg in self._hg:
            self.combo_hg.addItem(
                hg.get("holder_group_name", ""),
                hg.get("holder_group_code", ""),
            )
        root.addLayout(_row("分析項目 *", self.combo_hg))

        root.addStretch()
        btns = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        btns.button(QDialogButtonBox.StandardButton.Ok).setText("保存")
        btns.button(QDialogButtonBox.StandardButton.Cancel).setText("キャンセル")
        btns.accepted.connect(self._on_ok)
        btns.rejected.connect(self.reject)
        root.addWidget(btns)

    def _load(self, item: dict) -> None:
        self.edit_name.setText(item.get("name", ""))
        idx_shelf = self.combo_shelf.findData(item.get("shelf_life", ""))
        if idx_shelf >= 0:
            self.combo_shelf.setCurrentIndex(idx_shelf)
        idx_hg = self.combo_hg.findData(item.get("holder_group_code", ""))
        if idx_hg >= 0:
            self.combo_hg.setCurrentIndex(idx_hg)

    def _on_ok(self) -> None:
        if not self.edit_name.text().strip():
            QMessageBox.warning(self, "入力エラー", "試薬名を入力してください。")
            return
        if self.combo_hg.currentIndex() < 0:
            QMessageBox.warning(self, "入力エラー", "分析項目を選択してください。")
            return
        self.accept()

    def result_data(self) -> dict:
        return {
            "name": self.edit_name.text().strip(),
            "shelf_life": self.combo_shelf.currentData(),
            "holder_group_code": self.combo_hg.currentData(),
            "holder_group_name": self.combo_hg.currentText(),
        }


# ── 調整履歴ダイアログ ─────────────────────────────────────────────────────────


class ReagentHistoryDialog(QDialog):
    """調整日を入力 → 使用期限を自動計算して表示。"""

    def __init__(
        self,
        shelf_life: str,
        current_date: str = "",
        parent: QWidget | None = None,
    ):
        super().__init__(parent)
        self._shelf_life = shelf_life
        self.setWindowTitle("調整記録")
        self.resize(400, 180)
        self._build_ui()
        if current_date:
            self.edit_date.setText(current_date)
            self._update_expiry()

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(20, 16, 20, 16)
        root.setSpacing(12)

        self.edit_date = DateEdit()
        self.edit_date.textChanged.connect(self._update_expiry)
        root.addLayout(_row("調整日 *", self.edit_date))

        self.lbl_expiry = QLabel("—")
        self.lbl_expiry.setStyleSheet(f"font-size:13px; color:{_TEXT}; font-weight:600;")
        root.addLayout(_row("使用期限", self.lbl_expiry))

        shelf_label = SHELF_LIFE_LABELS.get(self._shelf_life, self._shelf_life)
        lbl_shelf = QLabel(shelf_label)
        lbl_shelf.setStyleSheet(f"font-size:12px; color:{_TEXT2};")
        root.addLayout(_row("保存期間", lbl_shelf))

        root.addStretch()
        btns = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        btns.button(QDialogButtonBox.StandardButton.Ok).setText("保存")
        btns.button(QDialogButtonBox.StandardButton.Cancel).setText("キャンセル")
        btns.accepted.connect(self._on_ok)
        btns.rejected.connect(self.reject)
        root.addWidget(btns)

    def _update_expiry(self) -> None:
        d = self.edit_date.text().strip()
        if d:
            expiry = calc_expiry(d, self._shelf_life)
            self.lbl_expiry.setText(expiry if expiry else "—")
        else:
            self.lbl_expiry.setText("—")

    def _on_ok(self) -> None:
        if not self.edit_date.text().strip():
            QMessageBox.warning(self, "入力エラー", "調整日を入力してください。")
            return
        if not self.edit_date.isValid():
            QMessageBox.warning(self, "入力エラー", "日付はYYYY-MM-DD形式で入力してください。")
            return
        self.accept()

    def result_date(self) -> str:
        return self.edit_date.text().strip()


# ── 共通ヘルパー ──────────────────────────────────────────────────────────────


def _row(label: str, widget: QWidget) -> QHBoxLayout:
    hl = QHBoxLayout()
    lbl = QLabel(label)
    lbl.setFixedWidth(90)
    lbl.setStyleSheet(f"font-size:12px; font-weight:600; color:{_TEXT2};")
    hl.addWidget(lbl)
    hl.addWidget(widget, 1)
    return hl


def _style_input(w: QLineEdit) -> None:
    w.setFixedHeight(30)
    w.setStyleSheet(
        f"QLineEdit {{ border:1px solid {_BORDER}; border-radius:4px;"
        f" padding:4px 8px; font-size:12px; color:{_TEXT}; }}"
        f"QLineEdit:focus {{ border-color:{_ACCENT}; }}"
    )
