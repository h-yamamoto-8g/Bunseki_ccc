"""TasksPageUI — タスク一覧と状態遷移バーの純粋レイアウト。

ビジネスロジック・task_store・DataLoader の import 禁止。
"""
from __future__ import annotations

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QFrame,
    QAbstractItemView, QComboBox, QDialog,
    QMessageBox, QMenu, QStackedWidget,
)
from PySide6.QtCore import Signal, Qt, QSize
from PySide6.QtGui import QColor, QFont, QIcon

# ui_taskspage.py と ui_taskstates.py が同名クラスを持つため alias で区別
from app.ui.generated.ui_taskspage import Ui_TasksPage as _UiListPage
import app.config as _cfg
from app.config import STATE_LABELS
from app.ui.widgets.icon_utils import get_icon

# ── ステートアイコンマップ ─────────────────────────────────────────────────────
_STATE_ICONS: dict[str, str] = {
    "task_setup":          ":/icons/start.svg",
    "analysis_targets":    ":/icons/sample-list.svg",
    "analysis":            ":/icons/analysis.svg",
    "result_entry":        ":/icons/data-input.svg",
    "result_verification": ":/icons/graph.svg",
    "submission":          ":/icons/flow.svg",
    "completed":           ":/icons/end.svg",
}


def _make_status_widget(state_id: str, label: str, color: str) -> QWidget:
    """アイコン + テキストのステータスセルウィジェットを生成する。"""
    w = QWidget()
    w.setStyleSheet("background:transparent;")
    h = QHBoxLayout(w)
    h.setContentsMargins(6, 2, 6, 2)
    h.setSpacing(5)
    h.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
    svg = _STATE_ICONS.get(state_id, "")
    if svg:
        ic = QLabel()
        ic.setFixedSize(14, 14)
        ic.setPixmap(get_icon(svg, color, 14).pixmap(14, 14))
        ic.setStyleSheet("background:transparent; border:none;")
        h.addWidget(ic)
    lbl = QLabel(label)
    lbl.setStyleSheet(
        f"color:{color}; font-size:12px; font-weight:600;"
        " background:transparent; border:none;"
    )
    h.addWidget(lbl)
    h.addStretch()
    return w


# ── Design tokens — グローバル QSS (_GLOBAL_QSS in main.py) と完全一致 ─────────
_BG     = "#f5f7fa"
_BG2    = "#ffffff"
_BG3    = "#f9fafb"
_BG4    = "#f3f4f6"
_BORDER = "#e5e7eb"
_TEXT   = "#333333"
_TEXT2  = "#6b7280"
_TEXT3  = "#9ca3af"
_ACCENT = "#3b82f6"
_SUCCESS= "#10b981"
_WARN   = "#f59e0b"
_DANGER = "#ef4444"


class _FilterTabs(QFrame):
    tab_changed = Signal(str)

    def __init__(self, tabs: list[str], parent=None):
        super().__init__(parent)
        self.setObjectName("FilterTabs")
        self.setStyleSheet(
            f"QFrame#FilterTabs {{ background:{_BG3}; border-radius:8px; border:none; }}"
        )
        self._btns: dict[str, QPushButton] = {}
        self._active: str = tabs[0] if tabs else ""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(3, 3, 3, 3)
        layout.setSpacing(2)
        for tab in tabs:
            btn = QPushButton(tab)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setStyleSheet(self._inactive_style())
            btn.clicked.connect(lambda _=False, t=tab: self._select(t))
            layout.addWidget(btn)
            self._btns[tab] = btn
        if tabs:
            self._select(tabs[0])

    def _inactive_style(self):
        return (
            f"QPushButton {{ background:transparent; color:{_TEXT2};"
            f" border:none; padding:4px 12px; border-radius:5px;"
            f" font-size:12px; font-weight:500; }}"
            f"QPushButton:hover {{ background:{_BG4}; color:{_TEXT}; }}"
        )

    def _active_style(self):
        return (
            f"QPushButton {{ background:{_BG2}; color:{_ACCENT};"
            f" border:none; padding:4px 12px; border-radius:5px;"
            f" font-size:12px; font-weight:600; }}"
        )

    def _select(self, tab: str):
        self._active = tab
        for t, btn in self._btns.items():
            btn.setStyleSheet(self._active_style() if t == tab else self._inactive_style())
        self.tab_changed.emit(tab)



class _TakeoverDialog(QDialog):
    """他人のタスクを自分が引き継ぐ際の確認ダイアログ。"""

    def __init__(self, task: dict, parent=None):
        super().__init__(parent)
        self._task = task
        self.setWindowTitle("タスクの引き継ぎ確認")
        self.setFixedWidth(440)
        self.setModal(True)
        self._build_ui()

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(24, 24, 24, 24)
        root.setSpacing(16)

        title = QLabel("このタスクを引き継ぎますか？")
        title.setStyleSheet(f"font-size:15px; font-weight:700; color:{_TEXT};")
        root.addWidget(title)

        div = QFrame()
        div.setFixedHeight(1)
        div.setStyleSheet(f"QFrame {{ background:{_BORDER}; }}")
        root.addWidget(div)

        # 警告フレーム
        warn_frame = QFrame()
        warn_frame.setObjectName("TakeoverWarn")
        warn_frame.setStyleSheet(
            "QFrame#TakeoverWarn {"
            " background:rgba(245,158,11,0.08);"
            " border:1px solid rgba(245,158,11,0.30);"
            " border-radius:8px; }"
        )
        wl = QVBoxLayout(warn_frame)
        wl.setContentsMargins(14, 12, 14, 12)
        wl.setSpacing(6)

        current_assignee = self._task.get("assigned_to", "不明")
        warn_lbl = QLabel(f"⚠  このタスクは現在「{current_assignee}」さんが担当中です。")
        warn_lbl.setStyleSheet(f"color:#d97706; font-size:13px; font-weight:600;")
        warn_lbl.setWordWrap(True)
        wl.addWidget(warn_lbl)

        detail_lbl = QLabel(
            "引き継ぐと担当者があなたに変更されます。\n"
            "この操作は引き継ぎ履歴に記録され、元に戻せません。"
        )
        detail_lbl.setStyleSheet(f"color:{_TEXT2}; font-size:12px;")
        detail_lbl.setWordWrap(True)
        wl.addWidget(detail_lbl)
        root.addWidget(warn_frame)

        # タスク情報
        info_frame = QFrame()
        info_frame.setObjectName("TakeoverInfo")
        info_frame.setStyleSheet(
            f"QFrame#TakeoverInfo {{ background:{_BG3};"
            f" border:1px solid {_BORDER}; border-radius:8px; }}"
        )
        il = QVBoxLayout(info_frame)
        il.setContentsMargins(14, 10, 14, 10)
        il.setSpacing(4)
        il.addWidget(QLabel(f"タスク名: {self._task.get('task_name', '')}"))
        il.addWidget(QLabel(f"現在の担当者: {current_assignee}"))
        root.addWidget(info_frame)

        div2 = QFrame()
        div2.setFixedHeight(1)
        div2.setStyleSheet(f"QFrame {{ background:{_BORDER}; }}")
        root.addWidget(div2)

        btn_row = QHBoxLayout()
        btn_row.setSpacing(8)
        btn_row.addStretch()

        cancel_btn = QPushButton("キャンセル")
        cancel_btn.clicked.connect(self.reject)
        btn_row.addWidget(cancel_btn)

        confirm_btn = QPushButton("引き継ぐ")
        confirm_btn.setStyleSheet(
            f"QPushButton {{ background:{_ACCENT}; color:white; border:none;"
            f" padding:6px 16px; border-radius:6px; font-size:12px; font-weight:500; }}"
            f"QPushButton:hover {{ background:#2563eb; }}"
        )
        confirm_btn.clicked.connect(self.accept)
        btn_row.addWidget(confirm_btn)
        root.addLayout(btn_row)


class _HandoverDialog(QDialog):
    def __init__(self, task: dict, users: list[str] | None = None, parent=None):
        super().__init__(parent)
        self._task = task
        self._users = users or []
        self.new_assignee: str = ""
        self.setWindowTitle("担当者の引き継ぎ")
        self.setFixedWidth(420)
        self.setModal(True)
        self._build_ui()

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(24, 24, 24, 24)
        root.setSpacing(16)

        title = QLabel("担当者の引き継ぎ")
        title.setStyleSheet(f"font-size:15px; font-weight:700; color:{_TEXT};")
        root.addWidget(title)

        div = QFrame()
        div.setFixedHeight(1)
        div.setStyleSheet(f"QFrame {{ background:{_BORDER}; }}")
        root.addWidget(div)

        info_frame = QFrame()
        info_frame.setObjectName("HandoverInfo")
        info_frame.setStyleSheet(
            f"QFrame#HandoverInfo {{ background:{_BG3}; border:1px solid {_BORDER}; border-radius:8px; }}"
        )
        info_l = QVBoxLayout(info_frame)
        info_l.setContentsMargins(14, 12, 14, 12)
        info_l.setSpacing(6)
        info_l.addWidget(QLabel(f"タスク: {self._task.get('task_name', '')}"))
        info_l.addWidget(QLabel(f"現在の担当者: {self._task.get('assigned_to', '未割り当て')}"))
        root.addWidget(info_frame)

        sel_lbl = QLabel("引き継ぎ先")
        sel_lbl.setStyleSheet(f"font-size:11px; font-weight:600; color:{_TEXT2};")
        root.addWidget(sel_lbl)

        self._combo = QComboBox()
        self._combo.setEditable(True)
        self._combo.setInsertPolicy(QComboBox.InsertPolicy.InsertAtTop)
        known = sorted({_cfg.CURRENT_USER} | set(self._users))
        for u in known:
            self._combo.addItem(u)
        self._combo.setCurrentText("")
        root.addWidget(self._combo)

        if self._task.get("assigned_to") != _cfg.CURRENT_USER:
            takeover_btn = QPushButton(f"自分が引き継ぐ ({_cfg.CURRENT_USER})")
            takeover_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            takeover_btn.clicked.connect(lambda: self._combo.setCurrentText(_cfg.CURRENT_USER))
            root.addWidget(takeover_btn)

        div2 = QFrame()
        div2.setFixedHeight(1)
        div2.setStyleSheet(f"QFrame {{ background:{_BORDER}; }}")
        root.addWidget(div2)

        btn_row = QHBoxLayout()
        btn_row.setSpacing(8)
        btn_row.addStretch()
        cancel_btn = QPushButton("キャンセル")
        cancel_btn.clicked.connect(self.reject)
        btn_row.addWidget(cancel_btn)
        confirm_btn = QPushButton("引き継ぎを確定")
        confirm_btn.setStyleSheet(
            f"QPushButton {{ background:{_ACCENT}; color:white; border:none;"
            f" padding:6px 16px; border-radius:6px; font-size:12px; font-weight:500; }}"
            f"QPushButton:hover {{ background:#2563eb; }}"
        )
        confirm_btn.clicked.connect(self._on_confirm)
        btn_row.addWidget(confirm_btn)
        root.addLayout(btn_row)

    def _on_confirm(self):
        name = self._combo.currentText().strip()
        if not name:
            QMessageBox.warning(self, "入力エラー", "引き継ぎ先を入力してください。")
            return
        if name == self._task.get("assigned_to"):
            QMessageBox.warning(self, "入力エラー", "現在の担当者と同じです。")
            return
        self.new_assignee = name
        self.accept()


class TasksPageUI(QWidget):
    """タスクページ (リスト + 状態遷移バー) の純粋レイアウト。"""

    task_open_requested    = Signal(str)
    new_task_requested     = Signal()
    filter_changed         = Signal(str)
    back_to_list_requested = Signal()
    handover_requested     = Signal()
    task_delete_requested  = Signal(str)
    load_more_requested    = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # ページスタック（index 0: 一覧、1〜: 各ステート）
        self.stack = QStackedWidget()
        root.addWidget(self.stack)
        self.stack.addWidget(self._build_list_widget())

    def _build_list_widget(self) -> QWidget:
        """TasksPage.ui をベースにリスト画面を構築する。"""
        w = QWidget()
        w.setStyleSheet(f"background:{_BG};")

        _f = _UiListPage()
        _f.setupUi(w)
        _f.verticalLayout.setContentsMargins(0, 0, 0, 0)
        _f.verticalLayout.setSpacing(0)

        # widget_filter スタイル
        _f.widget_filter.setStyleSheet(
            f"background:{_BG}; border-bottom:1px solid {_BORDER};"
        )
        _f.horizontalLayout_2.setContentsMargins(20, 6, 20, 6)

        # セグメントバーを _FilterTabs で置換
        seg_layout = _f.horizontalLayout
        while seg_layout.count():
            item = seg_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        self.filter_tabs = _FilterTabs(["全件", "進行中", "終了", "マイタスク"])
        self.filter_tabs.tab_changed.connect(self.filter_changed)
        seg_layout.addWidget(self.filter_tabs)

        # HG / ユーザーコンボは将来実装のため非表示
        _f.comboBox_holder_groups.setVisible(False)
        _f.comboBox_users.setVisible(False)

        # 件数ラベルをフィルターバー右端に追加
        self.count_lbl = QLabel()
        self.count_lbl.setStyleSheet(f"color:{_TEXT3}; font-size:12px;")
        _f.horizontalLayout_2.addWidget(self.count_lbl)

        # widget_table スタイル
        _f.widget_table.setStyleSheet(f"background:{_BG};")
        _f.verticalLayout_2.setContentsMargins(20, 12, 20, 12)

        # tableView → QTableWidget に置換
        _f.verticalLayout_2.removeWidget(_f.tableView)
        _f.tableView.deleteLater()

        headers = ["作成日時", "ホルダグループ", "JOB番号", "ステータス", "担当者", "最終更新", ""]
        self.task_table = QTableWidget(0, len(headers))
        self.task_table.setHorizontalHeaderLabels(headers)
        self.task_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.task_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.task_table.setAlternatingRowColors(True)
        hh = self.task_table.horizontalHeader()
        hh.setMinimumSectionSize(60)
        for i, mode in enumerate([
            QHeaderView.ResizeMode.ResizeToContents,  # 作成日時
            QHeaderView.ResizeMode.Stretch,           # ホルダグループ
            QHeaderView.ResizeMode.ResizeToContents,  # JOB番号
            QHeaderView.ResizeMode.ResizeToContents,  # ステータス
            QHeaderView.ResizeMode.ResizeToContents,  # 担当者
            QHeaderView.ResizeMode.ResizeToContents,  # 最終更新
            QHeaderView.ResizeMode.Fixed,             # 操作
        ]):
            hh.setSectionResizeMode(i, mode)
        self.task_table.setColumnWidth(6, 88)
        vh = self.task_table.verticalHeader()
        vh.setVisible(False)
        vh.setDefaultSectionSize(36)   # 行の高さを確保
        self.task_table.doubleClicked.connect(self._on_row_double_click)
        _f.verticalLayout_2.addWidget(self.task_table)

        # 「さらに読み込む」ボタン（100件超過時のみ表示）
        self._load_more_btn = QPushButton("さらに読み込む")
        self._load_more_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._load_more_btn.setVisible(False)
        self._load_more_btn.clicked.connect(self.load_more_requested)
        _f.verticalLayout_2.addWidget(self._load_more_btn)

        return w

    # ── Public API ────────────────────────────────────────────────────────────

    def fill_table(self, tasks: list[dict]) -> None:
        self.task_table.setRowCount(0)
        icon_open = QIcon(":/icons/step.svg")
        icon_more = QIcon(":/icons/more.svg")

        for t in tasks:
            row = self.task_table.rowCount()
            self.task_table.insertRow(row)
            state_label = STATE_LABELS.get(t.get("current_state", ""), "")
            status = t.get("status", "")
            job_str = ", ".join(t.get("job_numbers", []))
            updated = t.get("updated_at", "")[:16].replace("T", " ")
            created = t.get("created_at", "")[:16].replace("T", " ")

            vals = [
                created, t.get("holder_group_name", ""), job_str,
                "",  # col 3: テキストは setCellWidget で表示
                t.get("assigned_to", ""), updated,
            ]
            for col, v in enumerate(vals):
                item = QTableWidgetItem(str(v))
                item.setData(Qt.ItemDataRole.UserRole, t["task_id"])
                self.task_table.setItem(row, col, item)

            # col 3: アイコン + テキストのステータスウィジェット
            s_color = (_ACCENT  if status == "進行中" else
                       _WARN    if status == "回覧中" else
                       _SUCCESS if status == "終了"  else _TEXT2)
            self.task_table.setCellWidget(
                row, 3,
                _make_status_widget(t.get("current_state", ""), state_label, s_color),
            )

            task_id = t["task_id"]
            action_w = QWidget()
            action_w.setStyleSheet("background:transparent;")
            al = QHBoxLayout(action_w)
            al.setContentsMargins(4, 4, 4, 4)
            al.setSpacing(4)

            _icon_btn_qss = (
                "QPushButton { border:1px solid #e5e7eb; border-radius:4px;"
                " background:#ffffff; padding:0; min-height:0; min-width:0; }"
                "QPushButton:hover { border-color:#3b82f6; background:#eff6ff; }"
            )

            open_btn = QPushButton()
            open_btn.setIcon(icon_open)
            open_btn.setIconSize(QSize(15, 15))
            open_btn.setFixedSize(28, 28)
            open_btn.setToolTip("開く")
            open_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            open_btn.setStyleSheet(_icon_btn_qss)
            open_btn.clicked.connect(
                lambda _=False, tid=task_id: self.task_open_requested.emit(tid)
            )
            al.addWidget(open_btn)

            more_btn = QPushButton()
            more_btn.setIcon(icon_more)
            more_btn.setIconSize(QSize(15, 15))
            more_btn.setFixedSize(28, 28)
            more_btn.setToolTip("メニュー")
            more_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            more_btn.setStyleSheet(_icon_btn_qss)
            more_btn.clicked.connect(
                lambda _=False, btn=more_btn, tid=task_id: self._show_more_menu(btn, tid)
            )
            al.addWidget(more_btn)

            self.task_table.setCellWidget(row, 6, action_w)

        self.count_lbl.setText(f"{len(tasks)} 件")

    def set_load_more_visible(self, visible: bool) -> None:
        self._load_more_btn.setVisible(visible)

    def show_list_view(self) -> None:
        self.stack.setCurrentIndex(0)

    def show_detail_view(self, task: dict, state: str) -> None:
        pass  # タスクコンテキストは共通ヘッダーで管理

    def get_handover_dialog(self, task: dict, users: list[str] | None = None) -> _HandoverDialog:
        return _HandoverDialog(task, users=users, parent=self)

    def get_takeover_dialog(self, task: dict) -> _TakeoverDialog:
        return _TakeoverDialog(task, parent=self)

    def _show_more_menu(self, btn: QPushButton, task_id: str) -> None:
        menu = QMenu(self)
        del_action = menu.addAction(QIcon(":/icons/delete.svg"), "削除")
        action = menu.exec(btn.mapToGlobal(btn.rect().bottomLeft()))
        if action == del_action:
            reply = QMessageBox.question(
                self, "削除の確認",
                "このタスクを削除しますか？\nこの操作は元に戻せません。",
                QMessageBox.StandardButton.Ok | QMessageBox.StandardButton.Cancel,
            )
            if reply == QMessageBox.StandardButton.Ok:
                self.task_delete_requested.emit(task_id)

    def _on_row_double_click(self, index) -> None:
        item = self.task_table.item(index.row(), 0)
        if item:
            task_id = item.data(Qt.ItemDataRole.UserRole)
            if task_id:
                self.task_open_requested.emit(task_id)
