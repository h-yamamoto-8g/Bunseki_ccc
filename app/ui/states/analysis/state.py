"""AnalysisUI — 分析ステートの純粋レイアウト。

分析前/分析後の2ブロック構成。
各ブロック内にドキュメント・チェックリスト・ログセクションをタイトル+下線で配置。
ビジネスロジック・task_store・DataLoader の import 禁止。
"""
from __future__ import annotations

import os
import subprocess
import sys
from datetime import date

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QCheckBox, QScrollArea, QFrame, QSizePolicy,
    QTableWidget, QTableWidgetItem, QHeaderView,
    QAbstractItemView, QDialog, QLineEdit, QComboBox,
    QDialogButtonBox, QSpinBox, QMessageBox,
)
from PySide6.QtCore import Signal, Qt
from PySide6.QtGui import QColor

from app.ui.widgets.date_edit import DateEdit


# ── スタイル定数 ──────────────────────────────────────────────────────────────

_BLOCK_STYLE = (
    "QFrame#analysis_block { background: #ffffff; border: 1px solid #e5e7eb; "
    "border-radius: 8px; }"
    "QFrame#analysis_block QWidget { background: #ffffff; }"
    "QFrame#analysis_block QCheckBox { background: #ffffff; }"
)
_BLOCK_TITLE_STYLE = (
    "font-size: 16px; font-weight: 800; color: #1e40af; border: none;"
    " padding: 4px 0;"
)
_SECTION_TITLE_STYLE = (
    "font-size: 14px; font-weight: 700; color: #1f2937; border: none;"
)
_ACCENT = "#3b82f6"
_BORDER = "#e2e8f0"
_TEXT = "#1e293b"
_TEXT2 = "#64748b"
_DANGER = "#ef4444"


def _make_separator() -> QWidget:
    sep = QWidget()
    sep.setFixedHeight(1)
    sep.setStyleSheet("background: #e5e7eb;")
    return sep


def _make_block_separator() -> QWidget:
    sep = QWidget()
    sep.setFixedHeight(2)
    sep.setStyleSheet("background: #bfdbfe;")
    return sep


def _open_location(location: str, loc_type: str) -> None:
    if loc_type == "link":
        from PySide6.QtCore import QUrl
        from PySide6.QtGui import QDesktopServices
        QDesktopServices.openUrl(QUrl(location))
    else:
        # 相対パスの場合は同期ルートからの絶対パスに復元
        from app.config import to_absolute_path
        if not os.path.isabs(location):
            path = os.path.normpath(to_absolute_path(location))
        else:
            path = os.path.normpath(location)
        if sys.platform == "win32":
            os.startfile(path)  # noqa: S606
        elif sys.platform == "darwin":
            subprocess.Popen(["open", path])  # noqa: S603,S607
        else:
            subprocess.Popen(["xdg-open", path])  # noqa: S603,S607


# ── 試薬ログ閲覧ウィジェット ─────────────────────────────────────────────────

_TABLE_STYLE = (
    f"QTableWidget {{ border:1px solid {_BORDER}; border-radius:6px;"
    f" background:#ffffff; gridline-color:{_BORDER}; }}"
    f"QHeaderView::section {{ background:#f1f5f9; color:{_TEXT};"
    f" font-size:12px; font-weight:600; padding:4px;"
    f" border:none; border-bottom:1px solid {_BORDER}; }}"
    f"QTableWidget::item {{ padding:4px 6px; font-size:12px; color:{_TEXT}; }}"
)


class _ReagentReadonlyTable(QWidget):
    """試薬調整ログの閲覧用テーブル（該当分析項目のみ）。"""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._data: list[dict] = []
        vl = QVBoxLayout(self)
        vl.setContentsMargins(0, 0, 0, 0)
        vl.setSpacing(4)

        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(
            ["試薬名", "保存可能期間", "最新調整日", "使用期限", "状態"]
        )
        self.table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Stretch
        )
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.verticalHeader().setDefaultSectionSize(32)
        self.table.verticalHeader().setVisible(False)
        self.table.setMaximumHeight(200)
        self.table.setStyleSheet(_TABLE_STYLE)
        vl.addWidget(self.table)

    def set_data(self, reagents: list[dict]) -> None:
        self._data = reagents
        self._populate()

    def _populate(self) -> None:
        self.table.setRowCount(len(self._data))
        today = date.today().isoformat()
        for row, item in enumerate(self._data):
            self.table.setItem(row, 0, QTableWidgetItem(item.get("name", "")))
            days = item.get("shelf_life_days", 0)
            self.table.setItem(
                row, 1, QTableWidgetItem("使い切り" if days == 0 else f"{days}日")
            )
            self.table.setItem(
                row, 2, QTableWidgetItem(item.get("preparation_date", ""))
            )
            self.table.setItem(
                row, 3, QTableWidgetItem(item.get("expiry_date", ""))
            )
            expiry = item.get("expiry_date", "")
            prep = item.get("preparation_date", "")
            if not prep:
                status = QTableWidgetItem("未調整")
                status.setForeground(QColor("#94a3b8"))
            elif expiry and expiry >= today:
                status = QTableWidgetItem("有効")
                status.setForeground(QColor("#16a34a"))
            else:
                status = QTableWidgetItem("期限切れ")
                status.setForeground(QColor(_DANGER))
            self.table.setItem(row, 4, status)


# ── 試薬ログ編集ウィジェット ─────────────────────────────────────────────────

class _ReagentEditTable(QWidget):
    """試薬調整ログの編集用テーブル（該当分析項目のみ）。"""

    reagent_changed = Signal(str, dict)  # (action, data) action="create"|"update"

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._data: list[dict] = []
        self._hg_code = ""
        self._hg_name = ""
        vl = QVBoxLayout(self)
        vl.setContentsMargins(0, 0, 0, 0)
        vl.setSpacing(4)

        # ヘッダー
        hl = QHBoxLayout()
        hl.addStretch()
        self.btn_edit = QPushButton("編集")
        self.btn_edit.setFixedHeight(26)
        self.btn_edit.setStyleSheet(
            f"QPushButton {{ background:#ffffff; color:{_TEXT2}; border:1px solid {_BORDER};"
            f" padding:2px 10px; border-radius:4px; font-size:12px; }}"
            f"QPushButton:hover {{ background:#f1f5f9; }}"
        )
        self.btn_edit.clicked.connect(self._on_edit)
        hl.addWidget(self.btn_edit)

        self.btn_new = QPushButton("+ 新規")
        self.btn_new.setFixedHeight(26)
        self.btn_new.setStyleSheet(
            f"QPushButton {{ background:{_ACCENT}; color:white; border:none;"
            f" padding:2px 10px; border-radius:4px; font-size:12px; font-weight:600; }}"
            f"QPushButton:hover {{ background:#2563eb; }}"
        )
        self.btn_new.clicked.connect(self._on_new)
        hl.addWidget(self.btn_new)
        vl.addLayout(hl)

        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(
            ["試薬名", "保存可能期間", "最新調整日", "使用期限", "状態"]
        )
        self.table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Stretch
        )
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.verticalHeader().setDefaultSectionSize(32)
        self.table.verticalHeader().setVisible(False)
        self.table.setMaximumHeight(200)
        self.table.setStyleSheet(_TABLE_STYLE)
        vl.addWidget(self.table)

    def set_context(self, hg_code: str, hg_name: str) -> None:
        self._hg_code = hg_code
        self._hg_name = hg_name

    def set_data(self, reagents: list[dict]) -> None:
        self._data = reagents
        self._populate()

    def set_readonly(self, readonly: bool) -> None:
        self.btn_edit.setVisible(not readonly)
        self.btn_new.setVisible(not readonly)

    def _populate(self) -> None:
        self.table.setRowCount(len(self._data))
        today = date.today().isoformat()
        for row, item in enumerate(self._data):
            self.table.setItem(row, 0, QTableWidgetItem(item.get("name", "")))
            days = item.get("shelf_life_days", 0)
            self.table.setItem(
                row, 1, QTableWidgetItem("使い切り" if days == 0 else f"{days}日")
            )
            self.table.setItem(
                row, 2, QTableWidgetItem(item.get("preparation_date", ""))
            )
            self.table.setItem(
                row, 3, QTableWidgetItem(item.get("expiry_date", ""))
            )
            expiry = item.get("expiry_date", "")
            prep = item.get("preparation_date", "")
            if not prep:
                status = QTableWidgetItem("未調整")
                status.setForeground(QColor("#94a3b8"))
            elif expiry and expiry >= today:
                status = QTableWidgetItem("有効")
                status.setForeground(QColor("#16a34a"))
            else:
                status = QTableWidgetItem("期限切れ")
                status.setForeground(QColor(_DANGER))
            self.table.setItem(row, 4, status)

    def _get_selected(self) -> dict | None:
        row = self.table.currentRow()
        if row < 0 or row >= len(self._data):
            QMessageBox.information(self, "選択なし", "行を選択してください。")
            return None
        return self._data[row]

    def _on_edit(self) -> None:
        item = self._get_selected()
        if not item:
            return
        dlg = _ReagentEditDialog(item=item, parent=self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            data = dlg.result_data()
            data["id"] = item["id"]
            self.reagent_changed.emit("update", data)

    def _on_new(self) -> None:
        dlg = _ReagentEditDialog(
            hg_code=self._hg_code, hg_name=self._hg_name, parent=self,
        )
        if dlg.exec() == QDialog.DialogCode.Accepted:
            self.reagent_changed.emit("create", dlg.result_data())


# ── 分析装置ログ編集ウィジェット ─────────────────────────────────────────────

class _EquipmentEditTable(QWidget):
    """分析装置ログの編集用テーブル（該当分析項目のみ）。"""

    equipment_changed = Signal(str, dict)  # (action, data)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._data: list[dict] = []
        self._hg_code = ""
        self._hg_name = ""
        vl = QVBoxLayout(self)
        vl.setContentsMargins(0, 0, 0, 0)
        vl.setSpacing(4)

        # ヘッダー
        hl = QHBoxLayout()
        hl.addStretch()
        self.btn_edit = QPushButton("編集")
        self.btn_edit.setFixedHeight(26)
        self.btn_edit.setStyleSheet(
            f"QPushButton {{ background:#ffffff; color:{_TEXT2}; border:1px solid {_BORDER};"
            f" padding:2px 10px; border-radius:4px; font-size:12px; }}"
            f"QPushButton:hover {{ background:#f1f5f9; }}"
        )
        self.btn_edit.clicked.connect(self._on_edit)
        hl.addWidget(self.btn_edit)

        self.btn_new = QPushButton("+ 新規")
        self.btn_new.setFixedHeight(26)
        self.btn_new.setStyleSheet(
            f"QPushButton {{ background:{_ACCENT}; color:white; border:none;"
            f" padding:2px 10px; border-radius:4px; font-size:12px; font-weight:600; }}"
            f"QPushButton:hover {{ background:#2563eb; }}"
        )
        self.btn_new.clicked.connect(self._on_new)
        hl.addWidget(self.btn_new)
        vl.addLayout(hl)

        self.table = QTableWidget()
        self.table.setColumnCount(2)
        self.table.setHorizontalHeaderLabels(["分析装置名", "リンク"])
        self.table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Stretch
        )
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.verticalHeader().setDefaultSectionSize(32)
        self.table.verticalHeader().setVisible(False)
        self.table.setMaximumHeight(200)
        self.table.setStyleSheet(_TABLE_STYLE)
        vl.addWidget(self.table)

    def set_context(self, hg_code: str, hg_name: str) -> None:
        self._hg_code = hg_code
        self._hg_name = hg_name

    def set_data(self, equipment: list[dict]) -> None:
        self._data = equipment
        self._populate()

    def set_readonly(self, readonly: bool) -> None:
        self.btn_edit.setVisible(not readonly)
        self.btn_new.setVisible(not readonly)

    def _populate(self) -> None:
        self.table.setRowCount(len(self._data))
        for row, item in enumerate(self._data):
            self.table.setItem(row, 0, QTableWidgetItem(item.get("name", "")))
            link_item = QTableWidgetItem(item.get("link", ""))
            link_item.setForeground(QColor(_ACCENT))
            self.table.setItem(row, 1, link_item)

    def _get_selected(self) -> dict | None:
        row = self.table.currentRow()
        if row < 0 or row >= len(self._data):
            QMessageBox.information(self, "選択なし", "行を選択してください。")
            return None
        return self._data[row]

    def _on_edit(self) -> None:
        item = self._get_selected()
        if not item:
            return
        dlg = _EquipmentEditDialog(item=item, parent=self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            data = dlg.result_data()
            data["id"] = item["id"]
            self.equipment_changed.emit("update", data)

    def _on_new(self) -> None:
        dlg = _EquipmentEditDialog(
            hg_code=self._hg_code, hg_name=self._hg_name, parent=self,
        )
        if dlg.exec() == QDialog.DialogCode.Accepted:
            self.equipment_changed.emit("create", dlg.result_data())


# ── ダイアログ ───────────────────────────────────────────────────────────────

def _dlg_row(label: str, widget: QWidget) -> QHBoxLayout:
    hl = QHBoxLayout()
    lbl = QLabel(label)
    lbl.setFixedWidth(90)
    lbl.setStyleSheet(f"font-size:12px; font-weight:600; color:{_TEXT2};")
    hl.addWidget(lbl)
    hl.addWidget(widget, 1)
    return hl


class _ReagentEditDialog(QDialog):
    """試薬の新規作成・編集ダイアログ（分析ステート内埋め込み用）。"""

    def __init__(
        self,
        item: dict | None = None,
        hg_code: str = "",
        hg_name: str = "",
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._item = item
        self._hg_code = hg_code or (item.get("holder_group_code", "") if item else "")
        self._hg_name = hg_name or (item.get("holder_group_name", "") if item else "")
        self.setWindowTitle("試薬編集" if item else "試薬作成")
        self.resize(460, 280)
        self._build_ui()
        if item:
            self._load(item)

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(20, 16, 20, 16)
        root.setSpacing(12)

        self.edit_name = QLineEdit()
        self.edit_name.setPlaceholderText("例: 塩酸(1+1)")
        self.edit_name.setFixedHeight(30)
        root.addLayout(_dlg_row("試薬名 *", self.edit_name))

        shelf_w = QWidget()
        shelf_l = QHBoxLayout(shelf_w)
        shelf_l.setContentsMargins(0, 0, 0, 0)
        self.spin_shelf = QSpinBox()
        self.spin_shelf.setFixedHeight(30)
        self.spin_shelf.setRange(0, 9999)
        self.spin_shelf.setSuffix(" 日")
        self.spin_shelf.setSpecialValueText("使い切り")
        self.spin_shelf.valueChanged.connect(self._update_expiry)
        shelf_l.addWidget(self.spin_shelf)
        shelf_l.addWidget(QLabel("（0 = 使い切り）"))
        root.addLayout(_dlg_row("保存日数 *", shelf_w))

        self.edit_date = DateEdit()
        self.edit_date.textChanged.connect(self._update_expiry)
        root.addLayout(_dlg_row("最新調整日", self.edit_date))

        self.lbl_expiry = QLabel("—")
        self.lbl_expiry.setStyleSheet(f"font-size:13px; color:{_TEXT}; font-weight:600;")
        root.addLayout(_dlg_row("使用期限", self.lbl_expiry))

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
        self.spin_shelf.setValue(item.get("shelf_life_days", 0))
        self.edit_date.setText(item.get("preparation_date", ""))
        self._update_expiry()

    def _update_expiry(self) -> None:
        from app.core.reagent_store import calc_expiry
        d = self.edit_date.text().strip()
        days = self.spin_shelf.value()
        if d:
            expiry = calc_expiry(d, days)
            self.lbl_expiry.setText(expiry if expiry else "—")
        else:
            self.lbl_expiry.setText("—")

    def _on_ok(self) -> None:
        if not self.edit_name.text().strip():
            QMessageBox.warning(self, "入力エラー", "試薬名を入力してください。")
            return
        d = self.edit_date.text().strip()
        if d and not self.edit_date.isValid():
            QMessageBox.warning(self, "入力エラー", "日付はYYYY-MM-DD形式で入力してください。")
            return
        self.accept()

    def result_data(self) -> dict:
        return {
            "name": self.edit_name.text().strip(),
            "shelf_life_days": self.spin_shelf.value(),
            "preparation_date": self.edit_date.text().strip(),
            "holder_group_code": self._hg_code,
            "holder_group_name": self._hg_name,
        }


class _EquipmentEditDialog(QDialog):
    """分析装置の新規作成・編集ダイアログ。"""

    def __init__(
        self,
        item: dict | None = None,
        hg_code: str = "",
        hg_name: str = "",
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._item = item
        self._hg_code = hg_code or (item.get("holder_group_code", "") if item else "")
        self._hg_name = hg_name or (item.get("holder_group_name", "") if item else "")
        self.setWindowTitle("分析装置編集" if item else "分析装置作成")
        self.resize(460, 200)
        self._build_ui()
        if item:
            self._load(item)

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(20, 16, 20, 16)
        root.setSpacing(12)

        self.edit_name = QLineEdit()
        self.edit_name.setPlaceholderText("例: ICP-OES")
        self.edit_name.setFixedHeight(30)
        root.addLayout(_dlg_row("装置名 *", self.edit_name))

        self.edit_link = QLineEdit()
        self.edit_link.setPlaceholderText("Excelファイルのパス")
        self.edit_link.setFixedHeight(30)
        root.addLayout(_dlg_row("リンク", self.edit_link))

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

    def _on_ok(self) -> None:
        if not self.edit_name.text().strip():
            QMessageBox.warning(self, "入力エラー", "装置名を入力してください。")
            return
        self.accept()

    def result_data(self) -> dict:
        return {
            "name": self.edit_name.text().strip(),
            "link": self.edit_link.text().strip(),
            "holder_group_code": self._hg_code,
            "holder_group_name": self._hg_name,
        }


# ── メイン UI ────────────────────────────────────────────────────────────────

class AnalysisUI(QWidget):
    """分析ステート (純粋レイアウト)。

    Signals:
        finish_requested(pre_checks, post_checks): 完了ボタン押下
        back_requested(): 戻る
        reagent_changed(): 試薬データが変更された
        equipment_changed(): 装置データが変更された
    """

    finish_requested = Signal(list, list)
    back_requested = Signal()
    reagent_changed = Signal(str, dict)    # (action, data)
    equipment_changed = Signal(str, dict)  # (action, data)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._pre_checks: list[QCheckBox] = []
        self._post_checks: list[QCheckBox] = []
        self._check_all_btns: list[QPushButton] = []
        self._build_ui()

    def _build_ui(self) -> None:
        outer = QVBoxLayout(self)
        outer.setContentsMargins(8, 8, 8, 8)
        outer.setSpacing(8)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)

        content = QWidget()
        self._content_layout = QVBoxLayout(content)
        self._content_layout.setContentsMargins(0, 0, 0, 0)
        self._content_layout.setSpacing(16)
        self._content_layout.addStretch()
        scroll.setWidget(content)
        outer.addWidget(scroll, 1)

        # ── ナビゲーションボタン ──
        action_bar = QWidget()
        hl = QHBoxLayout(action_bar)
        hl.addStretch()

        self.back_btn = QPushButton("戻る")
        self.back_btn.setMinimumSize(100, 50)
        self.back_btn.setMaximumSize(100, 50)
        self.back_btn.setVisible(False)
        self.back_btn.clicked.connect(self.back_requested)
        hl.addWidget(self.back_btn)

        self.finish_btn = QPushButton("完了")
        self.finish_btn.setMinimumSize(100, 50)
        self.finish_btn.setMaximumSize(100, 50)
        self.finish_btn.setEnabled(False)
        self.finish_btn.clicked.connect(self._on_finish)
        hl.addWidget(self.finish_btn)

        hl.addStretch()
        outer.addWidget(action_bar)

    # ── Public API ────────────────────────────────────────────────────────────

    def set_config(self, cfg: dict) -> None:
        self._clear_content()

        # ═══════════════════ 分析前ブロック ═══════════════════
        pre_block = self._make_block("分析前")
        pre_vl = pre_block.layout()

        # 分析前ドキュメント
        pre_docs = cfg.get("pre_documents", [])
        pre_vl.addWidget(self._make_section_title("分析前ドキュメント"))
        pre_vl.addWidget(_make_separator())
        pre_vl.addWidget(self._make_docs_content(pre_docs))

        # 分析前チェックリスト
        pre_items = cfg.get("pre_checklist", [])
        pre_vl.addWidget(self._make_section_title("分析前チェックリスト"))
        pre_vl.addWidget(_make_separator())
        checks_w, self._pre_checks = self._make_checklist_content(pre_items)
        pre_vl.addWidget(checks_w)

        # 試薬調整ログ（閲覧）
        pre_vl.addWidget(self._make_section_title("試薬調整ログ"))
        pre_vl.addWidget(_make_separator())
        self._reagent_readonly = _ReagentReadonlyTable()
        pre_vl.addWidget(self._reagent_readonly)

        self._content_layout.addWidget(pre_block)

        # ═══════════════════ 分析後ブロック ═══════════════════
        post_block = self._make_block("分析後")
        post_vl = post_block.layout()

        # 分析後ドキュメント
        post_docs = cfg.get("post_documents", [])
        post_vl.addWidget(self._make_section_title("分析後ドキュメント"))
        post_vl.addWidget(_make_separator())
        post_vl.addWidget(self._make_docs_content(post_docs))

        # 分析後チェックリスト
        post_items = cfg.get("post_checklist", [])
        post_vl.addWidget(self._make_section_title("分析後チェックリスト"))
        post_vl.addWidget(_make_separator())
        checks_w2, self._post_checks = self._make_checklist_content(post_items)
        post_vl.addWidget(checks_w2)

        # 試薬調整ログ（編集）
        post_vl.addWidget(self._make_section_title("試薬調整ログ"))
        post_vl.addWidget(_make_separator())
        self._reagent_edit = _ReagentEditTable()
        self._reagent_edit.reagent_changed.connect(self.reagent_changed)
        post_vl.addWidget(self._reagent_edit)

        # 分析装置ログ（編集）
        post_vl.addWidget(self._make_section_title("分析装置ログ"))
        post_vl.addWidget(_make_separator())
        self._equipment_edit = _EquipmentEditTable()
        self._equipment_edit.equipment_changed.connect(self.equipment_changed)
        post_vl.addWidget(self._equipment_edit)

        self._content_layout.addWidget(post_block)
        self._content_layout.addStretch()
        self._update_finish_btn()

    def set_reagents(self, reagents: list[dict]) -> None:
        self._reagent_readonly.set_data(reagents)
        self._reagent_edit.set_data(reagents)

    def set_equipment(self, equipment: list[dict]) -> None:
        self._equipment_edit.set_data(equipment)

    def set_log_context(self, hg_code: str, hg_name: str) -> None:
        self._reagent_edit.set_context(hg_code, hg_name)
        self._equipment_edit.set_context(hg_code, hg_name)

    def restore_checks(
        self, pre_saved: list[bool], post_saved: list[bool], readonly: bool
    ) -> None:
        for cb, val in zip(self._pre_checks, pre_saved):
            cb.setChecked(bool(val))
            cb.setEnabled(not readonly)
        for cb, val in zip(self._post_checks, post_saved):
            cb.setChecked(bool(val))
            cb.setEnabled(not readonly)
        self.finish_btn.setVisible(not readonly)
        for btn in self._check_all_btns:
            btn.setVisible(not readonly)
        self._reagent_edit.set_readonly(readonly)
        self._equipment_edit.set_readonly(readonly)
        self._update_finish_btn()

    # ── Internal — ブロック/セクション構築 ────────────────────────────────────

    def _clear_content(self) -> None:
        self._pre_checks = []
        self._post_checks = []
        self._check_all_btns = []
        while self._content_layout.count():
            item = self._content_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

    def _make_block(self, title: str) -> QFrame:
        """分析前/分析後の大ブロックを生成する。"""
        block = QFrame()
        block.setObjectName("analysis_block")
        block.setStyleSheet(_BLOCK_STYLE)
        vl = QVBoxLayout(block)
        vl.setContentsMargins(20, 16, 20, 16)
        vl.setSpacing(16)

        lbl = QLabel(title)
        lbl.setStyleSheet(_BLOCK_TITLE_STYLE)
        vl.addWidget(lbl)
        vl.addWidget(_make_block_separator())

        return block

    def _make_section_title(self, title: str) -> QLabel:
        lbl = QLabel(title)
        lbl.setStyleSheet(_SECTION_TITLE_STYLE)
        return lbl

    def _make_docs_content(self, docs: list[dict]) -> QWidget:
        w = QWidget()
        vl = QVBoxLayout(w)
        vl.setContentsMargins(0, 0, 0, 8)
        vl.setSpacing(4)

        if not docs:
            lbl = QLabel("ドキュメントなし")
            lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            lbl.setStyleSheet("color: #9ca3af; font-size: 13px; padding: 8px;")
            vl.addWidget(lbl)
            return w

        for doc in docs:
            row = QWidget()
            rl = QHBoxLayout(row)
            rl.setContentsMargins(0, 0, 0, 0)
            rl.setSpacing(8)

            name = doc.get("name", "")
            location = doc.get("location", "")
            loc_type = doc.get("type", "path")
            icon = "🔗" if loc_type == "link" else "📁"
            lbl = QLabel(f"{icon}  {name}")
            lbl.setStyleSheet("font-size: 13px; color: #334155;")
            rl.addWidget(lbl, 1)

            if location:
                btn = QPushButton("開く")
                btn.setFixedWidth(60)
                btn.setStyleSheet(
                    "QPushButton { background: #3b82f6; color: white; border: none; "
                    "border-radius: 4px; padding: 4px 8px; font-weight: 600; }"
                    "QPushButton:hover { background: #2563eb; }"
                )
                btn.clicked.connect(
                    lambda _=False, loc=location, t=loc_type: _open_location(loc, t)
                )
                rl.addWidget(btn)

            vl.addWidget(row)
        return w

    def _make_checklist_content(
        self, items: list[str]
    ) -> tuple[QWidget, list[QCheckBox]]:
        w = QWidget()
        vl = QVBoxLayout(w)
        vl.setContentsMargins(0, 0, 0, 8)
        vl.setSpacing(4)

        checks: list[QCheckBox] = []
        if not items:
            lbl = QLabel("チェック項目なし")
            lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            lbl.setStyleSheet("color: #9ca3af; font-size: 13px; padding: 8px;")
            vl.addWidget(lbl)
            return w, checks

        btn_all = QPushButton("一括チェック")
        btn_all.setMinimumSize(100, 35)
        btn_all.setMaximumSize(100, 50)
        btn_all.clicked.connect(lambda: self._check_all(checks))
        vl.addWidget(btn_all)
        self._check_all_btns.append(btn_all)

        for i, text in enumerate(items):
            label = text if isinstance(text, str) else text.get("label", str(text))
            cb = QCheckBox(label)
            is_last = i == len(items) - 1
            if is_last:
                cb.setStyleSheet("color: #334155; border-bottom: none;")
            else:
                cb.setStyleSheet("color: #334155;")
            cb.stateChanged.connect(self._update_finish_btn)
            cb.stateChanged.connect(
                lambda _, c=cb, last=is_last: self._apply_strikethrough(c, last)
            )
            vl.addWidget(cb)
            checks.append(cb)

        return w, checks

    # ── Internal — ユーティリティ ─────────────────────────────────────────────

    @staticmethod
    def _apply_strikethrough(cb: QCheckBox, is_last: bool = False) -> None:
        font = cb.font()
        font.setStrikeOut(cb.isChecked())
        cb.setFont(font)
        border = "border-bottom: none;" if is_last else ""
        if cb.isChecked():
            cb.setStyleSheet(f"color: #9ca3af; {border}")
        else:
            cb.setStyleSheet(f"color: #334155; {border}")

    def _check_all(self, checkboxes: list[QCheckBox]) -> None:
        for cb in checkboxes:
            if cb.isEnabled():
                cb.setChecked(True)

    def _update_finish_btn(self) -> None:
        all_checked = all(
            cb.isChecked() for cb in self._pre_checks + self._post_checks
        )
        self.finish_btn.setEnabled(all_checked)

    def _on_finish(self) -> None:
        pre = [cb.isChecked() for cb in self._pre_checks]
        post = [cb.isChecked() for cb in self._post_checks]
        self.finish_requested.emit(pre, post)
