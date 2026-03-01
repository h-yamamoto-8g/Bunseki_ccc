"""ログページ — 分析装置・試薬の使用ログ記録"""
import json
from datetime import datetime, date, timedelta
from pathlib import Path


def _add_months(d: date, months: int) -> date:
    """月を加算（月末日超過は月末に丸める）"""
    month = d.month - 1 + months
    year = d.year + month // 12
    month = month % 12 + 1
    import calendar
    last_day = calendar.monthrange(year, month)[1]
    return date(year, month, min(d.day, last_day))

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QTableWidget, QTableWidgetItem, QHeaderView,
    QAbstractItemView, QComboBox, QDialog, QDialogButtonBox,
    QFormLayout, QLineEdit, QDateEdit, QSpinBox, QMessageBox,
    QTabWidget, QScrollArea,
)
from PySide6.QtCore import Qt, QDate
from PySide6.QtGui import QColor, QFont

from app.config import DATA_PATH, CURRENT_USER

_BG2    = "#161b27"
_BG3    = "#1e2535"
_BORDER = "#2a3349"
_TEXT   = "#e8eaf0"
_TEXT2  = "#8b93a8"
_TEXT3  = "#5a6278"
_ACCENT = "#4a8cff"
_SUCCESS= "#2ecc8a"
_WARN   = "#f5a623"
_DANGER = "#e85454"

_INSTRUMENT_LOG_PATH = DATA_PATH / "bunseki" / "logs" / "instrument_log.json"
_REAGENT_LOG_PATH    = DATA_PATH / "bunseki" / "logs" / "reagent_log.json"

_TABLE_SS = f"""
    QTableWidget {{ background:{_BG2}; color:{_TEXT}; border:1px solid {_BORDER};
                   border-radius:8px; gridline-color:{_BORDER}; }}
    QTableWidget::item {{ color:{_TEXT}; border:none; padding:2px 8px; }}
    QTableWidget::item:alternate {{ background:{_BG3}; }}
    QTableWidget::item:selected {{ background:{_ACCENT}; color:white; }}
    QHeaderView::section {{ background:{_BG2}; color:{_TEXT3}; border:none;
        border-bottom:1px solid {_BORDER}; padding:8px 12px;
        font-size:11px; font-weight:bold; }}
"""


# ─────────────────────────────────────────────────────────────────────────────
# JSON helpers
# ─────────────────────────────────────────────────────────────────────────────

def _load_instrument_log() -> dict:
    if _INSTRUMENT_LOG_PATH.exists():
        try:
            return json.loads(_INSTRUMENT_LOG_PATH.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {"devices": [], "entries": []}


def _save_instrument_log(data: dict):
    _INSTRUMENT_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    _INSTRUMENT_LOG_PATH.write_text(
        json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8"
    )


def _load_reagent_log() -> dict:
    if _REAGENT_LOG_PATH.exists():
        try:
            return json.loads(_REAGENT_LOG_PATH.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {"reagents": [], "entries": []}


def _save_reagent_log(data: dict):
    _REAGENT_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    _REAGENT_LOG_PATH.write_text(
        json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8"
    )


def _next_id(items: list, prefix: str) -> str:
    nums = []
    for it in items:
        try:
            nums.append(int(it.get("id", "0").replace(prefix, "")))
        except ValueError:
            pass
    return f"{prefix}{(max(nums) + 1) if nums else 1:03d}"


# ─────────────────────────────────────────────────────────────────────────────
# 装置ログ タブ
# ─────────────────────────────────────────────────────────────────────────────

class InstrumentLogTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()
        self._load()

    def _setup_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(20, 16, 20, 16)
        root.setSpacing(10)

        # toolbar
        tb = QHBoxLayout()
        tb.setSpacing(8)

        self.device_combo = QComboBox()
        self.device_combo.setFixedWidth(180)
        self.device_combo.currentTextChanged.connect(self._filter_entries)
        tb.addWidget(QLabel("装置:"))
        tb.addWidget(self.device_combo)
        tb.addStretch()

        add_device_btn = self._btn("+ 装置追加", _BG3, _TEXT)
        add_device_btn.clicked.connect(self._add_device)
        tb.addWidget(add_device_btn)

        add_btn = self._btn("+ エントリ追加", _ACCENT, "white")
        add_btn.clicked.connect(self._add_entry)
        tb.addWidget(add_btn)

        del_btn = self._btn("削除", _BG3, _DANGER)
        del_btn.clicked.connect(self._delete_entry)
        tb.addWidget(del_btn)

        root.addLayout(tb)

        # table
        self.table = QTableWidget(0, 6)
        self.table.setHorizontalHeaderLabels(["ID", "日時", "使用時間(分)", "ユーザー", "備考", "装置名"])
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setAlternatingRowColors(True)
        self.table.setColumnHidden(5, True)  # device name used for filtering
        self.table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch)
        self.table.setStyleSheet(_TABLE_SS)
        self.table.verticalHeader().setVisible(False)
        root.addWidget(self.table)

    def _btn(self, text, bg, color) -> QPushButton:
        btn = QPushButton(text)
        btn.setStyleSheet(f"""
            QPushButton {{ background:{bg}; color:{color}; border:none;
                          padding:5px 12px; border-radius:6px; font-size:12px; }}
            QPushButton:hover {{ opacity:0.85; }}
        """)
        return btn

    def _load(self):
        data = _load_instrument_log()
        self._data = data

        # populate device combo
        current = self.device_combo.currentText()
        self.device_combo.blockSignals(True)
        self.device_combo.clear()
        self.device_combo.addItem("全て")
        for d in data.get("devices", []):
            self.device_combo.addItem(d["name"])
        if current:
            idx = self.device_combo.findText(current)
            if idx >= 0:
                self.device_combo.setCurrentIndex(idx)
        self.device_combo.blockSignals(False)
        self._filter_entries()

    def _filter_entries(self):
        data = self._data
        device_filter = self.device_combo.currentText()
        entries = data.get("entries", [])
        if device_filter and device_filter != "全て":
            entries = [e for e in entries if e.get("device_name") == device_filter]

        self.table.setRowCount(0)
        for e in sorted(entries, key=lambda x: x.get("datetime", ""), reverse=True):
            r = self.table.rowCount()
            self.table.insertRow(r)
            for col, key in enumerate(["id", "datetime", "duration_min", "user", "memo", "device_name"]):
                self.table.setItem(r, col, QTableWidgetItem(str(e.get(key, ""))))

    def _add_device(self):
        dlg = _DeviceDialog(self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            values = dlg.values()
            data = _load_instrument_log()
            new_id = _next_id(data.get("devices", []), "D-")
            data.setdefault("devices", []).append({"id": new_id, **values})
            _save_instrument_log(data)
            self._data = data
            self._load()

    def _add_entry(self):
        data = self._data
        devices = [d["name"] for d in data.get("devices", [])]
        if not devices:
            QMessageBox.warning(self, "装置未登録", "先に装置を追加してください。")
            return
        dlg = _InstrumentEntryDialog(devices, self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            values = dlg.values()
            data = _load_instrument_log()
            new_id = _next_id(data.get("entries", []), "IL-")
            data.setdefault("entries", []).append({"id": new_id, **values})
            _save_instrument_log(data)
            self._data = data
            self._filter_entries()

    def _delete_entry(self):
        rows = self.table.selectedItems()
        if not rows:
            return
        entry_id = self.table.item(self.table.currentRow(), 0).text()
        reply = QMessageBox.question(self, "確認", f"ID: {entry_id} を削除しますか？")
        if reply == QMessageBox.StandardButton.Yes:
            data = _load_instrument_log()
            data["entries"] = [e for e in data.get("entries", []) if e.get("id") != entry_id]
            _save_instrument_log(data)
            self._data = data
            self._filter_entries()


# ─────────────────────────────────────────────────────────────────────────────
# 試薬ログ タブ
# ─────────────────────────────────────────────────────────────────────────────

class ReagentLogTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()
        self._load()

    def _setup_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(20, 16, 20, 16)
        root.setSpacing(10)

        # toolbar
        tb = QHBoxLayout()
        tb.setSpacing(8)

        self.reagent_combo = QComboBox()
        self.reagent_combo.setFixedWidth(180)
        self.reagent_combo.currentTextChanged.connect(self._filter_entries)
        tb.addWidget(QLabel("試薬:"))
        tb.addWidget(self.reagent_combo)
        tb.addStretch()

        add_reagent_btn = self._btn("+ 試薬マスタ追加", _BG3, _TEXT)
        add_reagent_btn.clicked.connect(self._add_reagent)
        tb.addWidget(add_reagent_btn)

        add_btn = self._btn("+ ログ追加", _ACCENT, "white")
        add_btn.clicked.connect(self._add_entry)
        tb.addWidget(add_btn)

        del_btn = self._btn("削除", _BG3, _DANGER)
        del_btn.clicked.connect(self._delete_entry)
        tb.addWidget(del_btn)

        root.addLayout(tb)

        # table
        cols = ["ID", "試薬名", "作成者", "保存期限", "最新作成日", "設置期限", "ステータス"]
        self.table = QTableWidget(0, len(cols))
        self.table.setHorizontalHeaderLabels(cols)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setAlternatingRowColors(True)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.table.setStyleSheet(_TABLE_SS)
        self.table.verticalHeader().setVisible(False)
        root.addWidget(self.table)

        note = QLabel("※ 保存期限: 最新作成日 + マスタの設定期限(月)で計算")
        note.setStyleSheet(f"font-size:11px; color:{_TEXT3};")
        root.addWidget(note)

    def _btn(self, text, bg, color) -> QPushButton:
        btn = QPushButton(text)
        btn.setStyleSheet(f"""
            QPushButton {{ background:{bg}; color:{color}; border:none;
                          padding:5px 12px; border-radius:6px; font-size:12px; }}
            QPushButton:hover {{ opacity:0.85; }}
        """)
        return btn

    def _load(self):
        data = _load_reagent_log()
        self._data = data

        current = self.reagent_combo.currentText()
        self.reagent_combo.blockSignals(True)
        self.reagent_combo.clear()
        self.reagent_combo.addItem("全て")
        for r in data.get("reagents", []):
            self.reagent_combo.addItem(r["name"])
        if current:
            idx = self.reagent_combo.findText(current)
            if idx >= 0:
                self.reagent_combo.setCurrentIndex(idx)
        self.reagent_combo.blockSignals(False)
        self._filter_entries()

    def _filter_entries(self):
        data = self._data
        reagent_filter = self.reagent_combo.currentText()
        entries = data.get("entries", [])
        if reagent_filter and reagent_filter != "全て":
            entries = [e for e in entries if e.get("reagent_name") == reagent_filter]

        # Build a lookup: reagent_name → shelf_life_months
        shelf_map = {r["name"]: r.get("shelf_life_months", 3) for r in data.get("reagents", [])}
        # Most recent creation date per reagent
        recent_map: dict[str, str] = {}
        for e in entries:
            rn = e.get("reagent_name", "")
            cd = e.get("created_date", "")
            if cd and (rn not in recent_map or cd > recent_map[rn]):
                recent_map[rn] = cd

        today = date.today()

        self.table.setRowCount(0)
        for e in sorted(entries, key=lambda x: x.get("created_date", ""), reverse=True):
            r = self.table.rowCount()
            self.table.insertRow(r)

            rname = e.get("reagent_name", "")
            created_str = e.get("created_date", "")
            install_expiry_str = e.get("install_expiry", "")

            # 保存期限計算
            try:
                created_d = date.fromisoformat(created_str)
                months = shelf_map.get(rname, 3)
                shelf_expiry = _add_months(created_d, months)
                shelf_expiry_str = shelf_expiry.isoformat()
            except Exception:
                shelf_expiry = None
                shelf_expiry_str = ""

            most_recent = recent_map.get(rname, "")

            # ステータス判定 (設置期限優先)
            check_date = None
            try:
                check_date = date.fromisoformat(install_expiry_str) if install_expiry_str else shelf_expiry
            except Exception:
                check_date = shelf_expiry

            if check_date is None:
                status = "不明"
                row_color = None
            elif check_date < today:
                status = "期限切れ"
                row_color = _DANGER
            elif check_date <= today + timedelta(days=30):
                status = "要注意"
                row_color = _WARN
            else:
                status = "正常"
                row_color = None

            vals = [
                e.get("id", ""),
                rname,
                e.get("creator", ""),
                shelf_expiry_str,
                most_recent,
                install_expiry_str,
                status,
            ]
            for col, v in enumerate(vals):
                item = QTableWidgetItem(str(v))
                if col == 6 and row_color:
                    item.setForeground(QColor(row_color))
                    item.setFont(QFont("", -1, QFont.Weight.Bold))
                self.table.setItem(r, col, item)

    def _add_reagent(self):
        dlg = _ReagentMasterDialog(self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            values = dlg.values()
            data = _load_reagent_log()
            new_id = _next_id(data.get("reagents", []), "RM-")
            data.setdefault("reagents", []).append({"id": new_id, **values})
            _save_reagent_log(data)
            self._data = data
            self._load()

    def _add_entry(self):
        data = self._data
        reagents = [r["name"] for r in data.get("reagents", [])]
        if not reagents:
            QMessageBox.warning(self, "試薬未登録", "先に試薬マスタを追加してください。")
            return
        dlg = _ReagentEntryDialog(reagents, self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            values = dlg.values()
            data = _load_reagent_log()
            new_id = _next_id(data.get("entries", []), "RE-")
            data.setdefault("entries", []).append({"id": new_id, **values})
            _save_reagent_log(data)
            self._data = data
            self._filter_entries()

    def _delete_entry(self):
        rows = self.table.selectedItems()
        if not rows:
            return
        entry_id = self.table.item(self.table.currentRow(), 0).text()
        reply = QMessageBox.question(self, "確認", f"ID: {entry_id} を削除しますか？")
        if reply == QMessageBox.StandardButton.Yes:
            data = _load_reagent_log()
            data["entries"] = [e for e in data.get("entries", []) if e.get("id") != entry_id]
            _save_reagent_log(data)
            self._data = data
            self._filter_entries()


# ─────────────────────────────────────────────────────────────────────────────
# Dialogs
# ─────────────────────────────────────────────────────────────────────────────

class _DeviceDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("装置追加")
        self.resize(360, 200)
        vl = QVBoxLayout(self)
        form = QFormLayout()
        self.name_input = QLineEdit()
        self.manager_input = QLineEdit()
        self.phone_input = QLineEdit()
        form.addRow("装置名:", self.name_input)
        form.addRow("管理担当者:", self.manager_input)
        form.addRow("電話番号:", self.phone_input)
        vl.addLayout(form)
        btns = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        btns.accepted.connect(self.accept)
        btns.rejected.connect(self.reject)
        vl.addWidget(btns)

    def values(self) -> dict:
        return {
            "name": self.name_input.text().strip(),
            "manager": self.manager_input.text().strip(),
            "phone": self.phone_input.text().strip(),
        }


class _InstrumentEntryDialog(QDialog):
    def __init__(self, devices: list[str], parent=None):
        super().__init__(parent)
        self.setWindowTitle("使用記録追加")
        self.resize(380, 260)
        vl = QVBoxLayout(self)
        form = QFormLayout()
        self.device_combo = QComboBox()
        self.device_combo.addItems(devices)
        self.dt_input = QLineEdit(datetime.now().strftime("%Y-%m-%d %H:%M"))
        self.duration_spin = QSpinBox()
        self.duration_spin.setRange(1, 9999)
        self.duration_spin.setValue(30)
        self.user_input = QLineEdit(CURRENT_USER)
        self.memo_input = QLineEdit()
        form.addRow("装置名:", self.device_combo)
        form.addRow("日時:", self.dt_input)
        form.addRow("使用時間(分):", self.duration_spin)
        form.addRow("ユーザー:", self.user_input)
        form.addRow("備考:", self.memo_input)
        vl.addLayout(form)
        btns = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        btns.accepted.connect(self.accept)
        btns.rejected.connect(self.reject)
        vl.addWidget(btns)

    def values(self) -> dict:
        return {
            "device_name": self.device_combo.currentText(),
            "datetime": self.dt_input.text().strip(),
            "duration_min": self.duration_spin.value(),
            "user": self.user_input.text().strip(),
            "memo": self.memo_input.text().strip(),
        }


class _ReagentMasterDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("試薬マスタ追加")
        self.resize(360, 200)
        vl = QVBoxLayout(self)
        form = QFormLayout()
        self.name_input = QLineEdit()
        self.shelf_spin = QSpinBox()
        self.shelf_spin.setRange(1, 120)
        self.shelf_spin.setValue(3)
        self.shelf_spin.setSuffix(" ヶ月")
        self.memo_input = QLineEdit()
        form.addRow("試薬名:", self.name_input)
        form.addRow("設定期限:", self.shelf_spin)
        form.addRow("備考:", self.memo_input)
        vl.addLayout(form)
        btns = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        btns.accepted.connect(self.accept)
        btns.rejected.connect(self.reject)
        vl.addWidget(btns)

    def values(self) -> dict:
        return {
            "name": self.name_input.text().strip(),
            "shelf_life_months": self.shelf_spin.value(),
            "memo": self.memo_input.text().strip(),
        }


class _ReagentEntryDialog(QDialog):
    def __init__(self, reagents: list[str], parent=None):
        super().__init__(parent)
        self.setWindowTitle("試薬ログ追加")
        self.resize(380, 240)
        vl = QVBoxLayout(self)
        form = QFormLayout()
        self.reagent_combo = QComboBox()
        self.reagent_combo.addItems(reagents)
        self.creator_input = QLineEdit(CURRENT_USER)
        self.created_input = QDateEdit(QDate.currentDate())
        self.created_input.setCalendarPopup(True)
        self.created_input.setDisplayFormat("yyyy-MM-dd")
        self.install_expiry_input = QDateEdit(QDate.currentDate())
        self.install_expiry_input.setCalendarPopup(True)
        self.install_expiry_input.setDisplayFormat("yyyy-MM-dd")
        form.addRow("試薬名:", self.reagent_combo)
        form.addRow("作成者:", self.creator_input)
        form.addRow("作成日:", self.created_input)
        form.addRow("設置期限:", self.install_expiry_input)
        vl.addLayout(form)
        btns = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        btns.accepted.connect(self.accept)
        btns.rejected.connect(self.reject)
        vl.addWidget(btns)

    def values(self) -> dict:
        return {
            "reagent_name": self.reagent_combo.currentText(),
            "creator": self.creator_input.text().strip(),
            "created_date": self.created_input.date().toString("yyyy-MM-dd"),
            "install_expiry": self.install_expiry_input.date().toString("yyyy-MM-dd"),
        }


# ─────────────────────────────────────────────────────────────────────────────
# LogPage — main widget
# ─────────────────────────────────────────────────────────────────────────────

class LogPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # Topbar
        topbar = QFrame()
        topbar.setFixedHeight(48)
        topbar.setStyleSheet(f"QFrame {{ background:{_BG2}; border-bottom:1px solid {_BORDER}; }}")
        tl = QHBoxLayout(topbar)
        tl.setContentsMargins(20, 0, 20, 0)
        title_lbl = QLabel("ログ")
        title_lbl.setStyleSheet(f"font-size:13px; font-weight:600; color:{_TEXT2};")
        tl.addWidget(title_lbl)
        tl.addStretch()
        root.addWidget(topbar)

        # Body
        body = QWidget()
        bl = QVBoxLayout(body)
        bl.setContentsMargins(20, 16, 20, 16)
        bl.setSpacing(8)
        root.addWidget(body)

        h1 = QLabel("ログ")
        h1.setStyleSheet(f"font-size:20px; font-weight:700; color:{_TEXT};")
        bl.addWidget(h1)
        sub = QLabel("分析装置・試薬の使用記録")
        sub.setStyleSheet(f"font-size:12px; color:{_TEXT3};")
        bl.addWidget(sub)

        # Tabs
        tabs = QTabWidget()
        tabs.setTabPosition(QTabWidget.TabPosition.North)
        self.instrument_tab = InstrumentLogTab()
        self.reagent_tab = ReagentLogTab()
        tabs.addTab(self.instrument_tab, "装置ログ")
        tabs.addTab(self.reagent_tab, "試薬ログ")
        bl.addWidget(tabs)
