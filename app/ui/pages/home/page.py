"""HomePageUI — ホームページの純粋レイアウト（generated UI 使用）。

ビジネスロジック・task_store・DataLoader の import 禁止。
"""
from __future__ import annotations

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QFrame,
    QAbstractItemView, QDialog,
)
from PySide6.QtCore import Signal, Qt, QSize, QUrl
from PySide6.QtGui import QColor, QFont, QIcon

from app.ui.generated.ui_homepage import Ui_HomePage
from app.ui.widgets.icon_utils import get_icon
from app.ui.widgets.table_utils import enable_row_numbers_and_sort
from app.core import news_store

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

_TAG_COLORS = {
    "進行中": _ACCENT,
    "回覧中": _WARN,
    "終了":   _SUCCESS,
}

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


class HomePageUI(QWidget):
    """ホームページ (純粋レイアウト)。

    Signals:
        navigate_to_new_task: 新規タスク作成ボタン押下
        navigate_to_task(task_id): タスクを開くボタン押下
    """

    navigate_to_new_task = Signal()
    navigate_to_task = Signal(str)
    navigate_to_news = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        # ─ 警告バナー ─────────────────────────────────────────────────────────
        self.warn_banner = QFrame()
        self.warn_banner.setObjectName("WarnBanner")
        self.warn_banner.setStyleSheet("""
            QFrame#WarnBanner {
                background: rgba(245,158,11,0.08);
                border-bottom: 1px solid rgba(245,158,11,0.3);
            }
        """)
        wb = QHBoxLayout(self.warn_banner)
        wb.setContentsMargins(20, 8, 20, 8)
        self.warn_lbl = QLabel()
        self.warn_lbl.setStyleSheet(f"color:{_WARN}; font-size:12px;")
        self.warn_lbl.setWordWrap(True)
        wb.addWidget(self.warn_lbl)
        reissue_btn = QPushButton("再起票")
        reissue_btn.setStyleSheet(f"""
            QPushButton {{ background:{_DANGER}; color:white; border:none;
                padding:4px 12px; border-radius:4px; font-size:12px; }}
        """)
        reissue_btn.clicked.connect(self.navigate_to_new_task)
        wb.addWidget(reissue_btn)
        self.warn_banner.setVisible(False)
        outer.addWidget(self.warn_banner)

        # ─ 生成 UI を埋め込み ─────────────────────────────────────────────────
        content = QWidget()
        content.setStyleSheet(f"background:{_BG};")
        self._form = Ui_HomePage()
        self._form.setupUi(content)
        content.layout().setContentsMargins(20, 16, 20, 16)
        content.layout().setSpacing(8)
        outer.addWidget(content, 1)

        # ── マイタスク: tableView_mytasks → QTableWidget ────────────────────
        layout3 = self._form.verticalLayout_3
        layout3.setSpacing(8)
        layout3.removeWidget(self._form.tableView_mytasks)
        self._form.tableView_mytasks.deleteLater()

        headers = ["作成日時", "ホルダグループ", "JOB番号", "ステータス", "最終更新", ""]
        self.my_table = self._make_table(headers)
        self.my_table.doubleClicked.connect(self._on_double_click)
        layout3.addWidget(self.my_table)

        # ── ニュース: tableView_news → ニュース一覧 ──────────────────────
        layout4 = self._form.verticalLayout_4
        layout4.setSpacing(8)
        layout4.removeWidget(self._form.tableView_news)
        self._form.tableView_news.deleteLater()

        self.news_container = QFrame()
        self.news_container.setObjectName("NewsContainer")
        self.news_container.setStyleSheet(
            f"QFrame#NewsContainer {{ background:{_BG2}; border:1px solid {_BORDER}; border-radius:8px; }}"
        )
        self._news_layout = QVBoxLayout(self.news_container)
        self._news_layout.setContentsMargins(0, 0, 0, 0)
        self._news_layout.setSpacing(0)
        layout4.addWidget(self.news_container)

        # ── カレンダー: WebEngineView に設定URLを読み込む ──────────────────
        from app.core import home_settings_store
        self._calendar_view = self._form.webEngineView
        cal_url = home_settings_store.get_calendar_url()
        if cal_url:
            self._calendar_view.setUrl(QUrl(cal_url))
        else:
            self._calendar_view.setHtml(
                '<html><body style="display:flex;align-items:center;'
                'justify-content:center;height:100%;margin:0;'
                f'font-family:sans-serif;color:{_TEXT3};font-size:13px;">'
                '設定からカレンダーURLを登録してください'
                '</body></html>'
            )

        # ── カレンダーラベル行に最大化ボタンを追加 ────────────────────────────
        layout2 = self._form.verticalLayout_2
        layout2.removeWidget(self._form.label_calendar)
        cal_header = QHBoxLayout()
        cal_header.setContentsMargins(0, 0, 0, 0)
        cal_header.addWidget(self._form.label_calendar)
        cal_header.addStretch()
        btn_expand = QPushButton("⛶")
        btn_expand.setFixedSize(24, 24)
        btn_expand.setToolTip("カレンダーを最大化")
        btn_expand.setStyleSheet(
            f"QPushButton {{ background:transparent; border:1px solid {_BORDER};"
            f" border-radius:4px; font-size:14px; color:{_TEXT2}; }}"
            f"QPushButton:hover {{ background:#f1f5f9; }}"
        )
        btn_expand.clicked.connect(self._on_expand_calendar)
        cal_header.addWidget(btn_expand)
        layout2.insertLayout(0, cal_header)

        # ── マイタスク : ニュース = 1:1 ────────────────────────────────────
        self._form.horizontalLayout.setStretch(0, 1)
        self._form.horizontalLayout.setStretch(1, 1)

        # ── ラベルスタイル ──────────────────────────────────────────────────
        lbl_style = f"font-size:13px; font-weight:600; color:{_TEXT2}; border:none;"
        self._form.label_mytasks.setStyleSheet(lbl_style)
        self._form.label_news.setStyleSheet(lbl_style)
        self._form.label_calendar.setStyleSheet(lbl_style)
        self._form.widget_top.setStyleSheet(f"background:{_BG};")
        self._form.widget_bottom.setStyleSheet(f"background:{_BG};")

        # ── 上部(タスク+ニュース) : 下部(カレンダー) の比率調整 ──────────────
        self._form.verticalLayout.setStretch(0, 1)
        self._form.verticalLayout.setStretch(1, 3)

    # ── Public API ────────────────────────────────────────────────────────────

    def _on_expand_calendar(self) -> None:
        """カレンダーをフルスクリーンダイアログで表示する。"""
        from app.core import home_settings_store
        from PySide6.QtWebEngineWidgets import QWebEngineView

        cal_url = home_settings_store.get_calendar_url()
        if not cal_url:
            return

        dlg = QDialog(self)
        dlg.setWindowTitle("カレンダー")
        dlg.resize(1200, 800)
        layout = QVBoxLayout(dlg)
        layout.setContentsMargins(0, 0, 0, 0)
        web = QWebEngineView()
        web.setUrl(QUrl(cal_url))
        layout.addWidget(web)
        dlg.showMaximized()
        dlg.exec()

    def reload_calendar(self) -> None:
        """設定変更後にカレンダーURLを再読み込みする。"""
        from app.core import home_settings_store
        cal_url = home_settings_store.get_calendar_url()
        if cal_url:
            self._calendar_view.setUrl(QUrl(cal_url))
        else:
            self._calendar_view.setHtml(
                '<html><body style="display:flex;align-items:center;'
                'justify-content:center;height:100%;margin:0;'
                f'font-family:sans-serif;color:{_TEXT3};font-size:13px;">'
                '設定からカレンダーURLを登録してください'
                '</body></html>'
            )

    def set_my_tasks(self, tasks: list[dict]) -> None:
        self._fill_table(tasks)

    def set_other_tasks(self, tasks: list[dict]) -> None:
        pass

    def refresh_news(self) -> None:
        """ニュース一覧を最新の状態に更新する。"""
        # 既存の子ウィジェットをクリア
        while self._news_layout.count():
            item = self._news_layout.takeAt(0)
            if w := item.widget():
                w.deleteLater()

        items = news_store.get_all()
        if not items:
            lbl = QLabel("ニュースはありません")
            lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            lbl.setStyleSheet(f"color:{_TEXT3}; font-size:12px; border:none; padding:16px;")
            self._news_layout.addWidget(lbl)
            return

        for news in items[:10]:  # 最新10件
            card = self._build_news_card(news)
            self._news_layout.addWidget(card)
        self._news_layout.addStretch()

    def _build_news_card(self, news: dict) -> QWidget:
        """ニュース1件分のカードウィジェットを構築する。"""
        news_id = news.get("id", "")
        is_important = news.get("is_important", False)
        card = QWidget()
        bg = "#fef2f2" if is_important else "transparent"
        card.setStyleSheet(
            f"background:{bg}; border-bottom:1px solid {_BORDER};"
        )
        vl = QVBoxLayout(card)
        vl.setContentsMargins(12, 8, 12, 8)
        vl.setSpacing(2)

        # タイトル行
        title_row = QHBoxLayout()
        title_row.setSpacing(6)
        if is_important:
            badge = QLabel("重要")
            badge.setStyleSheet(
                "background:#dc2626; color:white;"
                " border-radius:3px; padding:1px 6px; border:none;"
                " font-size:10px; font-weight:700;"
            )
            badge.setFixedHeight(18)
            title_row.addWidget(badge)
        title = QLabel(news.get("title", "（無題）"))
        title_color = "#dc2626" if is_important else _TEXT
        title.setStyleSheet(
            f"font-size:12px; font-weight:600; color:{title_color}; border:none;"
        )
        title.setWordWrap(False)
        title_row.addWidget(title, 1)

        # 開くボタン
        btn_open = QPushButton("開く")
        btn_open.setFixedHeight(22)
        btn_open.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_open.setStyleSheet(
            f"QPushButton {{ background:transparent; color:{_ACCENT}; border:none;"
            f" font-size:11px; font-weight:600; min-height:0px; padding:2px 6px; }}"
            f"QPushButton:hover {{ text-decoration:underline; }}"
        )
        btn_open.clicked.connect(
            lambda _=False, nid=news_id: self.navigate_to_news.emit(nid)
        )
        title_row.addWidget(btn_open)
        vl.addLayout(title_row)

        # 日付
        created_at = news.get("created_at", "")[:10]
        meta = QLabel(f"{created_at}  {news.get('created_by', '')}")
        meta.setStyleSheet(f"font-size:10px; color:{_TEXT3}; border:none;")
        vl.addWidget(meta)

        return card

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _make_table(self, headers: list[str]) -> QTableWidget:
        t = QTableWidget(0, len(headers))
        t.setHorizontalHeaderLabels(headers)
        t.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        t.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        t.setAlternatingRowColors(True)
        hh = t.horizontalHeader()
        hh.setMinimumSectionSize(60)
        hh.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)  # 作成日時
        hh.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)           # ホルダグループ
        hh.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)  # JOB番号
        hh.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)  # ステータス
        hh.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)  # 最終更新
        hh.setSectionResizeMode(5, QHeaderView.ResizeMode.Fixed)             # 操作
        t.setColumnWidth(5, 44)
        vh = t.verticalHeader()
        vh.setDefaultSectionSize(36)
        enable_row_numbers_and_sort(t, self._on_sort_column)
        return t

    _HOME_SORT_KEYS = ["created_at", "holder_group_name", None, None, "updated_at"]

    def _on_sort_column(self, col: int, ascending: bool) -> None:
        if not hasattr(self, "_my_tasks_data"):
            return
        key = self._HOME_SORT_KEYS[col] if col < len(self._HOME_SORT_KEYS) else None
        if key:
            self._my_tasks_data.sort(
                key=lambda t: t.get(key, ""), reverse=not ascending,
            )
            self._fill_table(self._my_tasks_data)

    def _fill_table(self, tasks: list[dict]) -> None:
        from app.config import STATE_LABELS
        self._my_tasks_data = tasks
        self.my_table.setRowCount(0)
        icon_open = QIcon(":/icons/step.svg")
        _btn_qss = (
            "QPushButton { border:1px solid #e5e7eb; border-radius:4px;"
            " background:#ffffff; padding:0; min-height:0; min-width:0; }"
            "QPushButton:hover { border-color:#3b82f6; background:#eff6ff; }"
        )
        for t in tasks:
            row = self.my_table.rowCount()
            self.my_table.insertRow(row)
            state_label = STATE_LABELS.get(t.get("current_state", ""), "")
            status = t.get("status", "")
            job_str = ", ".join(t.get("job_numbers", []))
            updated = t.get("updated_at", "")[:16].replace("T", " ")
            created = t.get("created_at", "")[:16].replace("T", " ")
            vals = [
                created, t.get("holder_group_name", ""), job_str,
                "",  # col 3: テキストは setCellWidget で表示
                updated,
            ]
            for col, v in enumerate(vals):
                item = QTableWidgetItem(str(v))
                item.setData(Qt.ItemDataRole.UserRole, t.get("task_id"))
                self.my_table.setItem(row, col, item)

            # col 3: アイコン + テキストのステータスウィジェット
            s_color = _TAG_COLORS.get(status, _TEXT2)
            self.my_table.setCellWidget(
                row, 3,
                _make_status_widget(t.get("current_state", ""), state_label, s_color),
            )

            task_id = t.get("task_id")
            act_btn = QPushButton()
            act_btn.setIcon(icon_open)
            act_btn.setIconSize(QSize(15, 15))
            act_btn.setFixedSize(28, 28)
            act_btn.setToolTip("開く")
            act_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            act_btn.setStyleSheet(_btn_qss)
            act_btn.clicked.connect(
                lambda _=False, tid=task_id: self.navigate_to_task.emit(tid)
            )
            cell_w = QWidget()
            cell_w.setStyleSheet("background:transparent;")
            cell_l = QHBoxLayout(cell_w)
            cell_l.setContentsMargins(4, 4, 4, 4)
            cell_l.setAlignment(Qt.AlignmentFlag.AlignCenter)
            cell_l.addWidget(act_btn)
            self.my_table.setCellWidget(row, 5, cell_w)

    def _on_double_click(self, index) -> None:
        item = self.my_table.item(index.row(), 0)
        if item:
            task_id = item.data(Qt.ItemDataRole.UserRole)
            if task_id:
                self.navigate_to_task.emit(task_id)
