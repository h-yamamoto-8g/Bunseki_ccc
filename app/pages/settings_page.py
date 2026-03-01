"""設定ページ — アプリケーション設定・ユーザー管理"""
import json
from pathlib import Path
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QScrollArea, QLineEdit, QFileDialog, QMessageBox,
    QGroupBox, QTableWidget, QTableWidgetItem, QHeaderView,
    QAbstractItemView, QDialog, QDialogButtonBox, QFormLayout,
    QTabWidget, QTextEdit, QComboBox,
)
from PySide6.QtCore import Qt
import json

from app.config import DATA_PATH, APP_VERSION, CURRENT_USER

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

_SETTINGS_PATH = DATA_PATH / "bunseki" / "config" / "settings.json"
_USERS_PATH    = DATA_PATH / "bunseki" / "config" / "users.json"
_HG_CONFIG_PATH = DATA_PATH / "bunseki" / "config" / "hg_config.json"

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


def _section_label(text: str) -> QLabel:
    lbl = QLabel(text)
    lbl.setStyleSheet(f"font-size:11px; font-weight:700; color:{_TEXT3}; letter-spacing:1px;")
    return lbl


def _field_label(text: str) -> QLabel:
    lbl = QLabel(text)
    lbl.setStyleSheet(f"font-size:11px; font-weight:600; color:{_TEXT2};")
    return lbl


def _make_card() -> QFrame:
    card = QFrame()
    card.setStyleSheet(f"""
        QFrame {{
            background:{_BG2};
            border:1px solid {_BORDER};
            border-radius:8px;
        }}
    """)
    return card


def _load_settings() -> dict:
    if _SETTINGS_PATH.exists():
        try:
            return json.loads(_SETTINGS_PATH.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {}


def _load_users() -> list[dict]:
    if _USERS_PATH.exists():
        try:
            return json.loads(_USERS_PATH.read_text(encoding="utf-8")).get("users", [])
        except Exception:
            pass
    return [{"id": "U-001", "name": CURRENT_USER, "role": "分析者", "department": "SS部門", "active": True}]


def _save_users(users: list[dict]):
    _USERS_PATH.parent.mkdir(parents=True, exist_ok=True)
    _USERS_PATH.write_text(
        json.dumps({"users": users}, ensure_ascii=False, indent=2), encoding="utf-8"
    )


def _load_hg_config() -> dict:
    if _HG_CONFIG_PATH.exists():
        try:
            return json.loads(_HG_CONFIG_PATH.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {}


def _save_hg_config(data: dict):
    _HG_CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    _HG_CONFIG_PATH.write_text(
        json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8"
    )


# ─────────────────────────────────────────────────────────────────────────────
# 一般設定タブ
# ─────────────────────────────────────────────────────────────────────────────

class _GeneralTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._settings = _load_settings()
        self._setup_ui()

    def _setup_ui(self):
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)

        body = QWidget()
        bl = QVBoxLayout(body)
        bl.setContentsMargins(0, 16, 0, 16)
        bl.setSpacing(20)
        scroll.setWidget(body)

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.addWidget(scroll)

        # データパス
        bl.addWidget(_section_label("データソース"))
        path_card = _make_card()
        pc_l = QVBoxLayout(path_card)
        pc_l.setContentsMargins(16, 14, 16, 14)
        pc_l.setSpacing(12)
        pc_l.addWidget(_field_label("app_data フォルダパス"))
        path_row = QHBoxLayout()
        self.path_input = QLineEdit(str(self._settings.get("app_data_path", str(DATA_PATH))))
        path_row.addWidget(self.path_input)
        browse_btn = self._ghost_btn("参照…")
        browse_btn.clicked.connect(self._browse_path)
        path_row.addWidget(browse_btn)
        pc_l.addLayout(path_row)
        note = QLabel("SharePoint 同期フォルダを指定してください。変更後は再起動が必要です。")
        note.setStyleSheet(f"font-size:11px; color:{_TEXT3};")
        note.setWordWrap(True)
        pc_l.addWidget(note)
        bl.addWidget(path_card)

        # アプリ情報
        bl.addWidget(_section_label("アプリケーション情報"))
        info_card = _make_card()
        il = QVBoxLayout(info_card)
        il.setContentsMargins(16, 14, 16, 14)
        il.setSpacing(8)
        for label, value in [
            ("バージョン", f"ver.{APP_VERSION}"),
            ("Python", "3.11"),
            ("フレームワーク", "PySide6"),
            ("データ形式", "JSON / CSV"),
        ]:
            row = QHBoxLayout()
            lbl = QLabel(label)
            lbl.setStyleSheet(f"font-size:12px; color:{_TEXT3};")
            val = QLabel(value)
            val.setStyleSheet(f"font-size:12px; color:{_TEXT}; font-family:'Courier New',monospace;")
            row.addWidget(lbl)
            row.addStretch()
            row.addWidget(val)
            il.addLayout(row)
        bl.addWidget(info_card)

        # 保存ボタン
        save_btn = QPushButton("設定を保存")
        save_btn.setStyleSheet(f"""
            QPushButton {{ background:{_ACCENT}; color:white; border:none;
                          padding:8px 24px; border-radius:6px; font-size:13px; font-weight:500; }}
            QPushButton:hover {{ background:#5a9dff; }}
        """)
        save_btn.clicked.connect(self._save_settings)
        bl.addWidget(save_btn, alignment=Qt.AlignmentFlag.AlignLeft)
        bl.addStretch()

    def _ghost_btn(self, text: str) -> QPushButton:
        btn = QPushButton(text)
        btn.setStyleSheet(f"""
            QPushButton {{ background:{_BG3}; color:{_TEXT}; border:1px solid {_BORDER};
                          padding:5px 12px; border-radius:6px; font-size:12px; }}
            QPushButton:hover {{ border-color:{_ACCENT}; color:{_ACCENT}; }}
        """)
        return btn

    def _browse_path(self):
        path = QFileDialog.getExistingDirectory(self, "app_data フォルダを選択", str(DATA_PATH))
        if path:
            self.path_input.setText(path)

    def _save_settings(self):
        self._settings["app_data_path"] = self.path_input.text()
        try:
            _SETTINGS_PATH.parent.mkdir(parents=True, exist_ok=True)
            _SETTINGS_PATH.write_text(
                json.dumps(self._settings, ensure_ascii=False, indent=2), encoding="utf-8"
            )
            QMessageBox.information(self, "保存完了", "設定を保存しました。\n変更を反映するには再起動してください。")
        except Exception as e:
            QMessageBox.critical(self, "エラー", f"設定の保存に失敗しました:\n{e}")


# ─────────────────────────────────────────────────────────────────────────────
# ユーザー管理タブ
# ─────────────────────────────────────────────────────────────────────────────

class _UsersTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()
        self._load()

    def _setup_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 16, 0, 0)
        root.setSpacing(10)

        tb = QHBoxLayout()
        tb.setSpacing(8)
        add_btn = QPushButton("+ ユーザー追加")
        add_btn.setStyleSheet(f"""
            QPushButton {{ background:{_ACCENT}; color:white; border:none;
                          padding:6px 14px; border-radius:6px; font-size:12px; }}
            QPushButton:hover {{ background:#5a9dff; }}
        """)
        add_btn.clicked.connect(self._add_user)
        tb.addWidget(add_btn)

        edit_btn = QPushButton("編集")
        edit_btn.setStyleSheet(f"""
            QPushButton {{ background:{_BG3}; color:{_TEXT}; border:1px solid {_BORDER};
                          padding:6px 14px; border-radius:6px; font-size:12px; }}
            QPushButton:hover {{ border-color:{_ACCENT}; color:{_ACCENT}; }}
        """)
        edit_btn.clicked.connect(self._edit_user)
        tb.addWidget(edit_btn)

        del_btn = QPushButton("削除")
        del_btn.setStyleSheet(f"""
            QPushButton {{ background:{_BG3}; color:{_DANGER}; border:1px solid {_BORDER};
                          padding:6px 14px; border-radius:6px; font-size:12px; }}
            QPushButton:hover {{ border-color:{_DANGER}; }}
        """)
        del_btn.clicked.connect(self._delete_user)
        tb.addWidget(del_btn)
        tb.addStretch()
        root.addLayout(tb)

        cols = ["ID", "ユーザー名", "ロール", "所属部門", "有効"]
        self.table = QTableWidget(0, len(cols))
        self.table.setHorizontalHeaderLabels(cols)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setAlternatingRowColors(True)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.table.setStyleSheet(_TABLE_SS)
        self.table.verticalHeader().setVisible(False)
        self.table.doubleClicked.connect(self._edit_user)
        root.addWidget(self.table)

    def _load(self):
        users = _load_users()
        self._users = users
        self.table.setRowCount(0)
        for u in users:
            r = self.table.rowCount()
            self.table.insertRow(r)
            vals = [
                u.get("id", ""),
                u.get("name", ""),
                u.get("role", "分析者"),
                u.get("department", ""),
                "◯" if u.get("active", True) else "✕",
            ]
            for col, v in enumerate(vals):
                item = QTableWidgetItem(str(v))
                if col == 4:
                    from PySide6.QtGui import QColor
                    item.setForeground(QColor(_SUCCESS if v == "◯" else _DANGER))
                self.table.setItem(r, col, item)

    def _add_user(self):
        dlg = _UserDialog(parent=self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            users = _load_users()
            nums = [int(u["id"].replace("U-", "")) for u in users if u.get("id", "").startswith("U-") and u["id"][2:].isdigit()]
            new_id = f"U-{(max(nums)+1 if nums else 1):03d}"
            users.append({"id": new_id, **dlg.values()})
            _save_users(users)
            self._load()

    def _edit_user(self):
        row = self.table.currentRow()
        if row < 0:
            return
        user_id = self.table.item(row, 0).text()
        users = _load_users()
        target = next((u for u in users if u.get("id") == user_id), None)
        if not target:
            return
        dlg = _UserDialog(initial=target, parent=self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            target.update(dlg.values())
            _save_users(users)
            self._load()

    def _delete_user(self):
        row = self.table.currentRow()
        if row < 0:
            return
        user_id = self.table.item(row, 0).text()
        name = self.table.item(row, 1).text()
        reply = QMessageBox.question(self, "削除確認", f"ユーザー「{name}」を削除しますか？")
        if reply == QMessageBox.StandardButton.Yes:
            users = [u for u in _load_users() if u.get("id") != user_id]
            _save_users(users)
            self._load()


class _UserDialog(QDialog):
    def __init__(self, initial: dict | None = None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("ユーザー追加" if initial is None else "ユーザー編集")
        self.resize(360, 240)
        vl = QVBoxLayout(self)
        form = QFormLayout()
        self.name_input = QLineEdit(initial.get("name", "") if initial else "")
        self.role_combo = QComboBox()
        self.role_combo.addItems(["分析者", "確認者", "管理者"])
        if initial:
            idx = self.role_combo.findText(initial.get("role", "分析者"))
            if idx >= 0:
                self.role_combo.setCurrentIndex(idx)
        self.dept_input = QLineEdit(initial.get("department", "") if initial else "")
        self.active_combo = QComboBox()
        self.active_combo.addItems(["有効", "無効"])
        if initial and not initial.get("active", True):
            self.active_combo.setCurrentIndex(1)
        form.addRow("ユーザー名:", self.name_input)
        form.addRow("ロール:", self.role_combo)
        form.addRow("所属部門:", self.dept_input)
        form.addRow("状態:", self.active_combo)
        vl.addLayout(form)
        btns = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        btns.accepted.connect(self._accept)
        btns.rejected.connect(self.reject)
        vl.addWidget(btns)

    def _accept(self):
        if not self.name_input.text().strip():
            QMessageBox.warning(self, "入力エラー", "ユーザー名を入力してください。")
            return
        self.accept()

    def values(self) -> dict:
        return {
            "name": self.name_input.text().strip(),
            "role": self.role_combo.currentText(),
            "department": self.dept_input.text().strip(),
            "active": self.active_combo.currentIndex() == 0,
        }


# ─────────────────────────────────────────────────────────────────────────────
# ホルダグループ設定タブ
# ─────────────────────────────────────────────────────────────────────────────

class _HolderGroupTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()
        self._load()

    def _setup_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 16, 0, 0)
        root.setSpacing(10)

        # HG selector
        top = QHBoxLayout()
        top.addWidget(QLabel("ホルダグループ:"))
        self.hg_combo = QComboBox()
        self.hg_combo.setFixedWidth(200)
        self.hg_combo.currentTextChanged.connect(self._on_hg_change)
        top.addWidget(self.hg_combo)
        top.addStretch()
        root.addLayout(top)

        # JSON editor for the selected HG config
        root.addWidget(_field_label("設定（JSON形式）"))
        self.editor = QTextEdit()
        self.editor.setFont(__import__("PySide6.QtGui", fromlist=["QFont"]).QFont("Courier New", 11))
        self.editor.setPlaceholderText(
            '{\n'
            '  "analysis_links": [],\n'
            '  "manual_links": [],\n'
            '  "tool_links": [],\n'
            '  "pre_checklist": [],\n'
            '  "post_checklist": [],\n'
            '  "labaid_link": ""\n'
            '}'
        )
        root.addWidget(self.editor)

        btn_row = QHBoxLayout()
        save_btn = QPushButton("このHGの設定を保存")
        save_btn.setStyleSheet(f"""
            QPushButton {{ background:{_ACCENT}; color:white; border:none;
                          padding:7px 20px; border-radius:6px; font-size:12px; }}
            QPushButton:hover {{ background:#5a9dff; }}
        """)
        save_btn.clicked.connect(self._save_hg)
        btn_row.addWidget(save_btn)

        fmt_btn = QPushButton("整形")
        fmt_btn.setStyleSheet(f"""
            QPushButton {{ background:{_BG3}; color:{_TEXT}; border:1px solid {_BORDER};
                          padding:7px 14px; border-radius:6px; font-size:12px; }}
            QPushButton:hover {{ border-color:{_ACCENT}; color:{_ACCENT}; }}
        """)
        fmt_btn.clicked.connect(self._format_json)
        btn_row.addWidget(fmt_btn)
        btn_row.addStretch()
        root.addLayout(btn_row)

        note = QLabel(
            "analysis_links / manual_links / tool_links: URLの配列\n"
            "pre_checklist / post_checklist: チェック項目テキストの配列\n"
            "labaid_link: Lab-Aidの起動リンクまたはURI"
        )
        note.setStyleSheet(f"font-size:11px; color:{_TEXT3};")
        root.addWidget(note)

    def _load(self):
        # Load holder groups from master
        from app.config import DATA_PATH
        hg_path = DATA_PATH / "_common" / "master_data" / "source" / "holder_groups.json"
        self._hg_list = []
        if hg_path.exists():
            try:
                data = json.loads(hg_path.read_text(encoding="utf-8"))
                self._hg_list = [
                    g for g in data.get("items", []) if g.get("is_active", True)
                ]
            except Exception:
                pass
        self.hg_combo.clear()
        for g in self._hg_list:
            label = f"{g.get('holder_group_code','?')} — {g.get('holder_group_name','')}"
            self.hg_combo.addItem(label, g.get("holder_group_code"))

        self._hg_config = _load_hg_config()
        self._on_hg_change()

    def _on_hg_change(self):
        code = self.hg_combo.currentData()
        cfg = self._hg_config.get(code, {})
        self.editor.setPlainText(json.dumps(cfg, ensure_ascii=False, indent=2))

    def _format_json(self):
        try:
            parsed = json.loads(self.editor.toPlainText())
            self.editor.setPlainText(json.dumps(parsed, ensure_ascii=False, indent=2))
        except Exception as e:
            QMessageBox.warning(self, "JSON エラー", f"JSON の解析に失敗しました:\n{e}")

    def _save_hg(self):
        code = self.hg_combo.currentData()
        try:
            parsed = json.loads(self.editor.toPlainText())
        except Exception as e:
            QMessageBox.warning(self, "JSON エラー", f"JSON の解析に失敗しました:\n{e}")
            return
        self._hg_config[code] = parsed
        _save_hg_config(self._hg_config)
        QMessageBox.information(self, "保存完了", f"{code} の設定を保存しました。")


# ─────────────────────────────────────────────────────────────────────────────
# SettingsPage — main widget
# ─────────────────────────────────────────────────────────────────────────────

class SettingsPage(QWidget):
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
        title_lbl = QLabel("設定")
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

        h1 = QLabel("設定")
        h1.setStyleSheet(f"font-size:20px; font-weight:700; color:{_TEXT};")
        bl.addWidget(h1)

        tabs = QTabWidget()
        tabs.addTab(_GeneralTab(), "一般")
        tabs.addTab(_UsersTab(), "ユーザー管理")
        tabs.addTab(_HolderGroupTab(), "ホルダグループ")
        bl.addWidget(tabs)
