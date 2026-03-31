"""ニュースページ — 業務連絡・重要通知の掲示板。"""
from __future__ import annotations

import webbrowser
from datetime import datetime

from PySide6.QtCore import Qt, QRect, QSize, Signal
from PySide6.QtGui import QColor, QFont
from PySide6.QtWidgets import (
    QCheckBox, QDialog, QDialogButtonBox,
    QFrame, QHBoxLayout, QLabel, QLayout, QLayoutItem,
    QLineEdit, QListWidget, QListWidgetItem, QMessageBox,
    QPushButton, QScrollArea, QSizePolicy,
    QTextEdit, QVBoxLayout, QWidget,
)


class _FlowLayout(QLayout):
    """横方向に並べて幅を超えたら折り返す簡易フローレイアウト。"""

    def __init__(
        self, parent: QWidget | None = None, h_spacing: int = 6, v_spacing: int = 4
    ) -> None:
        super().__init__(parent)
        self._h_spacing = h_spacing
        self._v_spacing = v_spacing
        self._items: list[QLayoutItem] = []

    def addItem(self, item: QLayoutItem) -> None:  # noqa: N802
        self._items.append(item)

    def insertWidget(self, index: int, widget: QWidget) -> None:  # noqa: N802
        """指定位置にウィジェットを挿入する。"""
        from PySide6.QtWidgets import QWidgetItem
        self.addChildWidget(widget)
        item = QWidgetItem(widget)
        self._items.insert(index, item)
        self.invalidate()

    def count(self) -> int:
        return len(self._items)

    def itemAt(self, index: int) -> QLayoutItem | None:  # noqa: N802
        if 0 <= index < len(self._items):
            return self._items[index]
        return None

    def takeAt(self, index: int) -> QLayoutItem | None:  # noqa: N802
        if 0 <= index < len(self._items):
            return self._items.pop(index)
        return None

    def sizeHint(self) -> QSize:  # noqa: N802
        return self.minimumSize()

    def minimumSize(self) -> QSize:  # noqa: N802
        size = QSize()
        for item in self._items:
            size = size.expandedTo(item.minimumSize())
        m = self.contentsMargins()
        size += QSize(m.left() + m.right(), m.top() + m.bottom())
        return size

    def setGeometry(self, rect: QRect) -> None:  # noqa: N802
        super().setGeometry(rect)
        self._do_layout(rect)

    def hasHeightForWidth(self) -> bool:  # noqa: N802
        return True

    def heightForWidth(self, width: int) -> int:  # noqa: N802
        return self._do_layout(QRect(0, 0, width, 0), dry_run=True)

    def _do_layout(self, rect: QRect, dry_run: bool = False) -> int:
        m = self.contentsMargins()
        effective = rect.adjusted(m.left(), m.top(), -m.right(), -m.bottom())
        x = effective.x()
        y = effective.y()
        line_height = 0

        for item in self._items:
            w = item.sizeHint().width()
            h = item.sizeHint().height()
            if x + w > effective.right() + 1 and line_height > 0:
                x = effective.x()
                y += line_height + self._v_spacing
                line_height = 0
            if not dry_run:
                item.setGeometry(QRect(x, y, w, h))
            x += w + self._h_spacing
            line_height = max(line_height, h)

        return y + line_height - rect.y() + m.bottom()


from app.config import CURRENT_USER
from app.core import news_store
from app.services.data_service import DataService
from app.ui.widgets.date_edit import DateEdit

# ── デザイントークン ──────────────────────────────────────────────────────────
_BG   = "#f8fafc"
_BG2  = "#ffffff"
_TEXT = "#1e293b"
_TEXT2 = "#64748b"
_ACCENT = "#3b82f6"
_BORDER = "#e2e8f0"
_DANGER = "#ef4444"
_IMPORTANT_BG = "#fef2f2"
_IMPORTANT_BORDER = "#fecaca"
_IMPORTANT_FG = "#dc2626"


class NewsPage(QWidget):
    """ニュース一覧 + 詳細 + 作成/編集ページ。"""

    def __init__(self, data_service: DataService, parent: QWidget | None = None):
        super().__init__(parent)
        self._ds = data_service
        self._selected_id: str | None = None
        self._build_ui()

    # ── UI 構築 ───────────────────────────────────────────────────────────────

    def _build_ui(self) -> None:
        root = QHBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        root.addWidget(self._build_list_panel(), 0)
        root.addWidget(self._build_detail_panel(), 1)

    # ── 左: 一覧パネル ────────────────────────────────────────────────────────

    def _build_list_panel(self) -> QWidget:
        panel = QWidget()
        panel.setFixedWidth(320)
        panel.setStyleSheet(f"background:{_BG2}; border-right:1px solid {_BORDER};")
        vl = QVBoxLayout(panel)
        vl.setContentsMargins(0, 0, 0, 0)
        vl.setSpacing(0)

        # ヘッダー
        header = QWidget()
        header.setFixedHeight(60)
        header.setStyleSheet(f"background:{_BG2}; border-bottom:1px solid {_BORDER};")
        hl = QHBoxLayout(header)
        hl.setContentsMargins(16, 0, 12, 0)
        title_lbl = QLabel("ニュース")
        title_lbl.setStyleSheet("font-size:15px; font-weight:700; color:#1e293b;")
        hl.addWidget(title_lbl)
        hl.addStretch()

        self.btn_new = QPushButton("+ 新規")
        self.btn_new.setFixedHeight(32)
        self.btn_new.setStyleSheet(
            f"QPushButton {{ background:{_ACCENT}; color:white; border:none;"
            f" padding:4px 14px; border-radius:6px; font-size:12px; font-weight:600;"
            f" min-height:0px; }}"
            f"QPushButton:hover {{ background:#2563eb; }}"
        )
        self.btn_new.clicked.connect(self._on_new)
        hl.addWidget(self.btn_new)
        vl.addWidget(header)

        # 一覧リスト
        self.list_widget = QListWidget()
        self.list_widget.setStyleSheet(
            "QListWidget { border:none; background:transparent; }"
            "QListWidget::item { border-bottom:1px solid #f1f5f9; padding:0; }"
            "QListWidget::item:selected { background:#eff6ff; }"
        )
        self.list_widget.currentItemChanged.connect(self._on_item_selected)
        vl.addWidget(self.list_widget, 1)

        return panel

    # ── 右: 詳細パネル ────────────────────────────────────────────────────────

    def _build_detail_panel(self) -> QWidget:
        self.detail_panel = QWidget()
        self.detail_panel.setStyleSheet(f"background:{_BG};")
        vl = QVBoxLayout(self.detail_panel)
        vl.setContentsMargins(24, 20, 24, 20)
        vl.setSpacing(0)

        # 空の状態
        self.empty_lbl = QLabel("ニュースを選択してください")
        self.empty_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.empty_lbl.setStyleSheet(f"font-size:14px; color:{_TEXT2};")
        vl.addWidget(self.empty_lbl)

        # 詳細コンテンツ（スクロール）
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setStyleSheet("QScrollArea { border:none; background:transparent; }")
        self.scroll.setVisible(False)

        self.detail_content = QWidget()
        self.detail_content.setStyleSheet(f"background:{_BG};")
        dc_vl = QVBoxLayout(self.detail_content)
        dc_vl.setContentsMargins(0, 0, 0, 0)
        dc_vl.setSpacing(16)

        # タイトル行
        title_row = QHBoxLayout()
        self.lbl_important_badge = QLabel("重要")
        self.lbl_important_badge.setStyleSheet(
            f"background:{_IMPORTANT_FG}; color:white;"
            f" border-radius:4px; padding:2px 10px;"
            f" font-size:12px; font-weight:700;"
        )
        self.lbl_important_badge.setFixedHeight(24)
        self.lbl_important_badge.setVisible(False)
        title_row.addWidget(self.lbl_important_badge)

        self.lbl_title = QLabel()
        self.lbl_title.setStyleSheet(
            "font-size:18px; font-weight:700; color:#1e293b;"
        )
        self.lbl_title.setWordWrap(True)
        title_row.addWidget(self.lbl_title, 1)

        self.btn_edit = QPushButton("編集")
        self.btn_edit.setFixedHeight(28)
        self.btn_edit.setStyleSheet(
            f"QPushButton {{ background:{_BG2}; color:{_TEXT2}; border:1px solid {_BORDER};"
            f" padding:4px 12px; border-radius:5px; font-size:12px;"
            f" min-height:0px; }}"
            f"QPushButton:hover {{ background:#f1f5f9; }}"
        )
        self.btn_edit.clicked.connect(self._on_edit)
        title_row.addWidget(self.btn_edit)

        self.btn_delete = QPushButton("削除")
        self.btn_delete.setFixedHeight(28)
        self.btn_delete.setStyleSheet(
            f"QPushButton {{ background:#fef2f2; color:{_DANGER}; border:1px solid #fecaca;"
            f" padding:4px 12px; border-radius:5px; font-size:12px;"
            f" min-height:0px; }}"
            f"QPushButton:hover {{ background:#fee2e2; }}"
        )
        self.btn_delete.clicked.connect(self._on_delete)
        title_row.addWidget(self.btn_delete)
        dc_vl.addLayout(title_row)

        # メタ情報チップ行
        self.meta_row = QHBoxLayout()
        self.meta_row.setSpacing(8)
        self.lbl_date = self._chip("", "#f1f5f9", _TEXT2)
        self.lbl_author = self._chip("", "#f1f5f9", _TEXT2)
        self.meta_row.addWidget(self.lbl_date)
        self.meta_row.addWidget(self.lbl_author)
        self.meta_row.addStretch()
        dc_vl.addLayout(self.meta_row)

        # 対象分析項目
        self.frame_tests = self._section_frame()
        dc_vl.addWidget(self.frame_tests)

        # 対象期間
        self.frame_period = self._section_frame()
        dc_vl.addWidget(self.frame_period)

        # 本文
        self.lbl_body = QLabel()
        self.lbl_body.setWordWrap(True)
        self.lbl_body.setStyleSheet(
            f"font-size:13px; color:{_TEXT}; line-height:1.6;"
            f" background:{_BG2}; border:1px solid {_BORDER};"
            f" border-radius:8px; padding:16px;"
        )
        self.lbl_body.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        self.lbl_body.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        dc_vl.addWidget(self.lbl_body)

        # 添付リンク
        self.frame_links = self._section_frame()
        dc_vl.addWidget(self.frame_links)

        dc_vl.addStretch()
        self.scroll.setWidget(self.detail_content)
        vl.addWidget(self.scroll, 1)

        return self.detail_panel

    # ── 公開API ───────────────────────────────────────────────────────────────

    def refresh(self) -> None:
        """ページ表示時に呼ばれる。"""
        self._reload_list()

    # ── 内部処理 ──────────────────────────────────────────────────────────────

    def _reload_list(self) -> None:
        self.list_widget.blockSignals(True)
        self.list_widget.clear()
        for news in news_store.get_all():
            item = QListWidgetItem()
            item.setData(Qt.ItemDataRole.UserRole, news["id"])
            item.setSizeHint(__import__("PySide6.QtCore", fromlist=["QSize"]).QSize(0, 72))
            self.list_widget.addItem(item)
            card = self._build_list_card(news)
            self.list_widget.setItemWidget(item, card)
            if news["id"] == self._selected_id:
                self.list_widget.setCurrentItem(item)
        self.list_widget.blockSignals(False)
        # 選択状態を維持
        if self._selected_id:
            news = news_store.get(self._selected_id)
            if news:
                self._show_detail(news)
            else:
                self._clear_detail()
        else:
            self._clear_detail()

    def _build_list_card(self, news: dict) -> QWidget:
        is_important = news.get("is_important", False)
        w = QWidget()
        if is_important:
            w.setStyleSheet(
                f"background:{_IMPORTANT_BG};"
                f" border-left:3px solid {_IMPORTANT_FG};"
            )
        else:
            w.setStyleSheet("background:transparent;")
        vl = QVBoxLayout(w)
        vl.setContentsMargins(14, 10, 14, 10)
        vl.setSpacing(3)

        # タイトル行（重要バッジ + タイトル）
        title_row = QHBoxLayout()
        title_row.setSpacing(6)
        if is_important:
            badge = QLabel("重要")
            badge.setStyleSheet(
                f"background:{_IMPORTANT_FG}; color:white;"
                f" border-radius:3px; padding:1px 6px;"
                f" font-size:10px; font-weight:700;"
            )
            badge.setFixedHeight(18)
            title_row.addWidget(badge)

        title = QLabel(news.get("title", "（無題）"))
        title_color = _IMPORTANT_FG if is_important else "#1e293b"
        title.setStyleSheet(
            f"font-size:13px; font-weight:600; color:{title_color};"
        )
        title.setWordWrap(False)
        title_row.addWidget(title, 1)
        vl.addLayout(title_row)

        meta = QLabel(
            f"{news.get('created_at', '')[:10]}  {news.get('created_by', '')}"
        )
        meta.setStyleSheet(f"font-size:11px; color:{_TEXT2};")
        vl.addWidget(meta)

        tests = news.get("target_tests", [])
        if tests:
            tl = QLabel("  ".join(tests[:3]) + ("…" if len(tests) > 3 else ""))
            tl.setStyleSheet("font-size:11px; color:#3b82f6;")
            vl.addWidget(tl)

        return w

    def _on_item_selected(self, current: QListWidgetItem, _prev) -> None:
        if not current:
            return
        news_id = current.data(Qt.ItemDataRole.UserRole)
        self._selected_id = news_id
        news = news_store.get(news_id)
        if news:
            self._show_detail(news)

    def _show_detail(self, news: dict) -> None:
        self.empty_lbl.setVisible(False)
        self.scroll.setVisible(True)

        is_important = news.get("is_important", False)
        self.lbl_important_badge.setVisible(is_important)
        self.lbl_title.setText(news.get("title", "（無題）"))

        created_at = news.get("created_at", "")[:10]
        self.lbl_date.setText(f"📅 {created_at}" if created_at else "")
        self.lbl_author.setText(f"👤 {news.get('created_by', '')}")

        # 対象分析項目
        tests = news.get("target_tests", [])
        self._fill_section(
            self.frame_tests,
            "対象分析項目",
            "  /  ".join(tests) if tests else "—",
            "#eff6ff", "#3b82f6",
        )

        # 対象期間
        period_from = news.get("target_period_from", "")
        period_to   = news.get("target_period_to", "")
        period_str  = "—"
        if period_from or period_to:
            period_str = f"{period_from} 〜 {period_to}"
        self._fill_section(self.frame_period, "対象期間", period_str, "#f0fdf4", "#16a34a")

        # 本文
        body = news.get("body", "").replace("\n", "<br>")
        self.lbl_body.setText(body)

        # 添付リンク
        links = news.get("links", [])
        self._fill_links(self.frame_links, links)

    def _clear_detail(self) -> None:
        self._selected_id = None
        self.empty_lbl.setVisible(True)
        self.scroll.setVisible(False)

    def _on_new(self) -> None:
        tests = self._get_test_names()
        dlg = NewsEditDialog(tests, parent=self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            data = dlg.result_data()
            item = news_store.create(
                title=data["title"],
                body=data["body"],
                created_by=CURRENT_USER,
                target_tests=data["target_tests"],
                target_period_from=data["target_period_from"],
                target_period_to=data["target_period_to"],
                links=data["links"],
                is_important=data["is_important"],
            )
            self._selected_id = item["id"]
            self._reload_list()

    def _on_edit(self) -> None:
        if not self._selected_id:
            return
        news = news_store.get(self._selected_id)
        if not news:
            return
        tests = self._get_test_names()
        dlg = NewsEditDialog(tests, news=news, parent=self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            data = dlg.result_data()
            news_store.update(
                self._selected_id,
                title=data["title"],
                body=data["body"],
                target_tests=data["target_tests"],
                target_period_from=data["target_period_from"],
                target_period_to=data["target_period_to"],
                links=data["links"],
                is_important=data["is_important"],
            )
            self._reload_list()

    def _on_delete(self) -> None:
        if not self._selected_id:
            return
        news = news_store.get(self._selected_id)
        if not news:
            return
        reply = QMessageBox.question(
            self, "削除確認",
            f"「{news.get('title', '')}」を削除しますか？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            news_store.delete(self._selected_id)
            self._selected_id = None
            self._reload_list()

    def _get_test_names(self) -> list[str]:
        try:
            groups = self._ds.get_holder_groups()
            return [g["holder_group_name"] for g in groups if g.get("holder_group_name")]
        except Exception:
            return []

    # ── UIヘルパー ────────────────────────────────────────────────────────────

    @staticmethod
    def _chip(text: str, bg: str, fg: str) -> QLabel:
        lbl = QLabel(text)
        lbl.setStyleSheet(
            f"background:{bg}; color:{fg}; border-radius:4px;"
            f" padding:3px 8px; font-size:11px; font-weight:500;"
        )
        return lbl

    @staticmethod
    def _section_frame() -> QFrame:
        frame = QFrame()
        frame.setStyleSheet(
            f"QFrame {{ background:{_BG2}; border:1px solid {_BORDER};"
            f" border-radius:8px; }}"
        )
        QVBoxLayout(frame).setContentsMargins(14, 10, 14, 10)
        return frame

    @staticmethod
    def _fill_section(
        frame: QFrame, heading: str, value: str, badge_bg: str, badge_fg: str
    ) -> None:
        lay = frame.layout()
        # 子ウィジェットをクリア
        while lay.count():
            item = lay.takeAt(0)
            if w := item.widget():
                w.deleteLater()

        hl = QHBoxLayout()
        hl.setSpacing(8)
        lbl_head = QLabel(heading)
        lbl_head.setStyleSheet(f"font-size:11px; font-weight:600; color:{_TEXT2};")
        hl.addWidget(lbl_head)
        lbl_val = QLabel(value)
        lbl_val.setStyleSheet(
            f"font-size:12px; font-weight:500; color:{badge_fg};"
            f" background:{badge_bg}; border-radius:4px; padding:2px 8px;"
        )
        lbl_val.setWordWrap(True)
        hl.addWidget(lbl_val, 1)
        # QHBoxLayout を QVBoxLayout に追加
        container = QWidget()
        container.setStyleSheet("background:transparent;")
        container.setLayout(hl)
        lay.addWidget(container)

    @staticmethod
    def _fill_links(frame: QFrame, links: list[dict]) -> None:
        lay = frame.layout()
        while lay.count():
            item = lay.takeAt(0)
            if w := item.widget():
                w.deleteLater()

        head = QLabel("添付リンク")
        head.setStyleSheet(f"font-size:11px; font-weight:600; color:{_TEXT2};")
        lay.addWidget(head)

        if not links:
            lbl = QLabel("—")
            lbl.setStyleSheet(f"font-size:12px; color:{_TEXT2};")
            lay.addWidget(lbl)
            return

        for link in links:
            url   = link.get("url", "")
            label = link.get("label", "") or url
            btn = QPushButton(f"🔗 {label}")
            btn.setStyleSheet(
                f"QPushButton {{ background:#eff6ff; color:#2563eb; border:none;"
                f" text-align:left; padding:4px 8px; border-radius:4px; font-size:12px; }}"
                f"QPushButton:hover {{ background:#dbeafe; }}"
            )
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            if url:
                btn.clicked.connect(lambda _=False, u=url: webbrowser.open(u))
            lay.addWidget(btn)


# ── 編集ダイアログ ─────────────────────────────────────────────────────────────

class NewsEditDialog(QDialog):
    """ニュース新規作成 / 編集ダイアログ。"""

    def __init__(
        self,
        available_tests: list[str],
        news: dict | None = None,
        parent: QWidget | None = None,
    ):
        super().__init__(parent)
        self._available_tests = available_tests
        self._news = news
        self._link_rows: list[tuple[QLineEdit, QLineEdit]] = []

        self.setWindowTitle("ニュース編集" if news else "ニュース作成")
        self.resize(620, 640)
        self.setMinimumSize(500, 480)
        self._build_ui()
        if news:
            self._load(news)

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(20, 16, 20, 16)
        root.setSpacing(12)

        def row(label: str, widget: QWidget) -> QHBoxLayout:
            hl = QHBoxLayout()
            lbl = QLabel(label)
            lbl.setFixedWidth(110)
            lbl.setStyleSheet(f"font-size:12px; font-weight:600; color:{_TEXT2};")
            hl.addWidget(lbl)
            hl.addWidget(widget, 1)
            return hl

        # 重要フラグ
        self.chk_important = QCheckBox("重要（一覧の先頭に目立つように表示）")
        self.chk_important.setStyleSheet(
            f"QCheckBox {{ font-size:12px; color:{_IMPORTANT_FG}; font-weight:600; }}"
            f"QCheckBox::indicator:checked {{ background:{_IMPORTANT_FG}; border-color:{_IMPORTANT_FG}; }}"
        )
        root.addWidget(self.chk_important)

        # タイトル
        self.edit_title = QLineEdit()
        self.edit_title.setPlaceholderText("ニュースタイトル")
        self._style_input(self.edit_title)
        root.addLayout(row("タイトル *", self.edit_title))

        # 分析項目（タグ選択）
        tests_w = QWidget()
        tests_w.setFixedHeight(44)
        tests_w.setStyleSheet("background:transparent;")
        tests_hl = QHBoxLayout(tests_w)
        tests_hl.setContentsMargins(0, 0, 0, 0)
        tests_hl.setSpacing(6)

        # 選択済みタグ（横スクロール）
        self._selected_tests: list[str] = []
        self._tags_scroll = QScrollArea()
        self._tags_scroll.setWidgetResizable(True)
        self._tags_scroll.setFixedHeight(40)
        self._tags_scroll.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAsNeeded
        )
        self._tags_scroll.setVerticalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )
        self._tags_scroll.setStyleSheet(
            f"QScrollArea {{ border:1px solid {_BORDER}; border-radius:6px;"
            f" background:#ffffff; }}"
        )
        self._tags_inner = QWidget()
        self._tags_inner.setStyleSheet("background:transparent;")
        self.tags_layout = QHBoxLayout(self._tags_inner)
        self.tags_layout.setContentsMargins(6, 4, 6, 4)
        self.tags_layout.setSpacing(6)
        self.tags_layout.addStretch()
        self._tags_scroll.setWidget(self._tags_inner)
        tests_hl.addWidget(self._tags_scroll, 1)

        # + ボタン
        self.btn_add_test = QPushButton("+")
        self.btn_add_test.setFixedSize(36, 36)
        self.btn_add_test.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_add_test.setStyleSheet(
            f"QPushButton {{ background:{_ACCENT}; color:white; border:none;"
            f" border-radius:6px; font-size:18px; font-weight:700;"
            f" min-height:0px; max-height:36px; padding:0px;"
            f" text-align:center; }}"
            f"QPushButton:hover {{ background:#2563eb; }}"
        )
        self.btn_add_test.clicked.connect(self._open_test_select_dialog)
        tests_hl.addWidget(self.btn_add_test)

        root.addLayout(row("分析項目", tests_w))

        # 対象期間
        period_w = QWidget()
        pl = QHBoxLayout(period_w)
        pl.setContentsMargins(0, 0, 0, 0)
        pl.setSpacing(8)
        self.edit_period_from = DateEdit()
        self.edit_period_from.setFixedWidth(170)
        pl.addWidget(self.edit_period_from)
        pl.addWidget(QLabel("〜"))
        self.edit_period_to = DateEdit()
        self.edit_period_to.setFixedWidth(170)
        pl.addWidget(self.edit_period_to)
        pl.addStretch()
        root.addLayout(row("対象期間", period_w))

        # 本文
        root.addWidget(self._label_text("本文"))
        self.edit_body = QTextEdit()
        self.edit_body.setPlaceholderText("本文を入力してください")
        self.edit_body.setMinimumHeight(140)
        self.edit_body.setStyleSheet(
            f"QTextEdit {{ border:1px solid {_BORDER}; border-radius:6px;"
            f" padding:8px; font-size:13px; color:{_TEXT}; }}"
        )
        root.addWidget(self.edit_body)

        # 添付リンク
        root.addWidget(self._label_text("添付リンク"))
        self.links_container = QVBoxLayout()
        self.links_container.setSpacing(6)
        root.addLayout(self.links_container)

        self.btn_add_link = QPushButton("+ リンクを追加")
        self.btn_add_link.setStyleSheet(
            f"QPushButton {{ background:{_BG}; color:{_ACCENT}; border:1px dashed {_ACCENT};"
            f" border-radius:6px; font-size:12px; padding:8px 14px; }}"
            f"QPushButton:hover {{ background:#eff6ff; }}"
        )
        self.btn_add_link.clicked.connect(lambda: self._add_link_row())
        root.addWidget(self.btn_add_link)

        root.addStretch()

        # ボタン
        btns = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        btns.button(QDialogButtonBox.StandardButton.Ok).setText("保存")
        btns.button(QDialogButtonBox.StandardButton.Cancel).setText("キャンセル")
        btns.accepted.connect(self._on_ok)
        btns.rejected.connect(self.reject)
        root.addWidget(btns)

    def _load(self, news: dict) -> None:
        self.chk_important.setChecked(news.get("is_important", False))
        self.edit_title.setText(news.get("title", ""))
        for t in news.get("target_tests", []):
            self._add_test_tag(t)
        self.edit_period_from.setText(news.get("target_period_from", ""))
        self.edit_period_to.setText(news.get("target_period_to", ""))
        self.edit_body.setPlainText(news.get("body", ""))
        for link in news.get("links", []):
            self._add_link_row(link.get("label", ""), link.get("url", ""))

    def _add_link_row(self, label: str = "", url: str = "") -> None:
        row_w = QWidget()
        hl = QHBoxLayout(row_w)
        hl.setContentsMargins(0, 0, 0, 0)
        hl.setSpacing(6)

        edit_label = QLineEdit(label)
        edit_label.setPlaceholderText("ラベル（例: 分析マニュアル）")
        self._style_input(edit_label)
        hl.addWidget(edit_label, 1)

        edit_url = QLineEdit(url)
        edit_url.setPlaceholderText("URL（例: https://...）")
        self._style_input(edit_url)
        hl.addWidget(edit_url, 2)

        btn_del = QPushButton("×")
        btn_del.setFixedSize(32, 32)
        btn_del.setStyleSheet(
            f"QPushButton {{ background:#fef2f2; color:{_DANGER}; border:none;"
            f" border-radius:6px; font-size:14px; font-weight:700;"
            f" min-height:0px; max-height:32px; padding:0px; }}"
            f"QPushButton:hover {{ background:#fee2e2; }}"
        )
        pair = (edit_label, edit_url)
        btn_del.clicked.connect(lambda _=False, p=pair, w=row_w: self._remove_link_row(p, w))
        hl.addWidget(btn_del)

        self._link_rows.append(pair)
        self.links_container.addWidget(row_w)

    def _remove_link_row(self, pair: tuple, row_w: QWidget) -> None:
        if pair in self._link_rows:
            self._link_rows.remove(pair)
        row_w.deleteLater()

    # ── タグ選択 ──────────────────────────────────────────────────────────────

    def _open_test_select_dialog(self) -> None:
        dlg = _TestSelectDialog(
            self._available_tests, list(self._selected_tests), parent=self
        )
        if dlg.exec() == QDialog.DialogCode.Accepted:
            self._selected_tests = dlg.selected_tests()
            self._rebuild_tags()

    def _add_test_tag(self, text: str) -> None:
        if not text or text in self._selected_tests:
            return
        self._selected_tests.append(text)
        self._rebuild_tags()

    def _remove_test_tag(self, text: str) -> None:
        if text in self._selected_tests:
            self._selected_tests.remove(text)
            self._rebuild_tags()

    def _rebuild_tags(self) -> None:
        # stretch以外を全て削除（末尾1つを残す）
        while self.tags_layout.count() > 1:
            item = self.tags_layout.takeAt(0)
            if w := item.widget():
                w.deleteLater()
        # 選択済みタグをstretchの前に挿入
        for i, t in enumerate(self._selected_tests):
            chip = self._make_tag_chip(t)
            self.tags_layout.insertWidget(i, chip)
        # スクロール内部のサイズを更新
        self._tags_inner.adjustSize()

    def _make_tag_chip(self, text: str) -> QWidget:
        chip = QWidget()
        chip.setFixedHeight(32)
        chip.setStyleSheet(
            f"background:#eff6ff; border:1px solid #bfdbfe;"
            f" border-radius:6px;"
        )
        hl = QHBoxLayout(chip)
        hl.setContentsMargins(10, 4, 6, 4)
        hl.setSpacing(4)
        lbl = QLabel(text)
        lbl.setStyleSheet("font-size:12px; color:#2563eb; font-weight:500; background:transparent; border:none;")
        hl.addWidget(lbl)
        btn = QPushButton("×")
        btn.setFixedSize(18, 18)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.setStyleSheet(
            "QPushButton { background:transparent; color:#3b82f6;"
            " border:none; font-size:13px; font-weight:700;"
            " min-height:0px; padding:0px; }"
            "QPushButton:hover { color:#1d4ed8; }"
        )
        btn.clicked.connect(lambda _=False, t=text: self._remove_test_tag(t))
        hl.addWidget(btn)
        return chip

    def _on_ok(self) -> None:
        if not self.edit_title.text().strip():
            QMessageBox.warning(self, "入力エラー", "タイトルを入力してください。")
            return
        self.accept()

    def result_data(self) -> dict:
        tests = list(self._selected_tests)
        links = [
            {"label": lbl.text().strip(), "url": url.text().strip()}
            for lbl, url in self._link_rows
            if url.text().strip()
        ]
        return {
            "title": self.edit_title.text().strip(),
            "body": self.edit_body.toPlainText(),
            "target_tests": tests,
            "target_period_from": self.edit_period_from.text().strip(),
            "target_period_to": self.edit_period_to.text().strip(),
            "links": links,
            "is_important": self.chk_important.isChecked(),
        }

    # ── ヘルパー ──────────────────────────────────────────────────────────────

    @staticmethod
    def _style_input(w: QLineEdit) -> None:
        w.setStyleSheet(
            f"QLineEdit {{ border:1px solid {_BORDER}; border-radius:4px;"
            f" padding:4px 8px; font-size:12px; color:{_TEXT}; }}"
            f"QLineEdit:focus {{ border-color:{_ACCENT}; }}"
        )

    @staticmethod
    def _label_text(text: str) -> QLabel:
        lbl = QLabel(text)
        lbl.setStyleSheet(f"font-size:12px; font-weight:600; color:{_TEXT2};")
        return lbl


# ── 分析項目選択ダイアログ ─────────────────────────────────────────────────────

class _TestSelectDialog(QDialog):
    """チェックボックス一覧で分析項目を複数選択するダイアログ。"""

    def __init__(
        self,
        available: list[str],
        current: list[str],
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle("対象分析項目の選択")
        self.setStyleSheet("QDialog { background:#f9fafb; }")
        self.setModal(True)
        self.resize(400, 480)
        self.setMinimumSize(320, 300)
        self._checks: list[tuple[QCheckBox, str]] = []
        self._build_ui(available, current)

    def _build_ui(self, available: list[str], current: list[str]) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(16, 12, 16, 12)
        root.setSpacing(10)

        # ヘッダー
        header = QLabel("対象の分析項目を選択してください")
        header.setStyleSheet(f"font-size:13px; font-weight:600; color:{_TEXT};")
        root.addWidget(header)

        # 検索フィルター
        self._edit_filter = QLineEdit()
        self._edit_filter.setPlaceholderText("検索...")
        self._edit_filter.setFixedHeight(30)
        self._edit_filter.setStyleSheet(
            f"QLineEdit {{ border:1px solid {_BORDER}; border-radius:4px;"
            f" padding:4px 8px; font-size:12px; color:{_TEXT}; }}"
            f"QLineEdit:focus {{ border-color:{_ACCENT}; }}"
        )
        self._edit_filter.textChanged.connect(self._on_filter)
        root.addWidget(self._edit_filter)

        # 全選択 / 全解除ボタン
        sel_row = QHBoxLayout()
        sel_row.setSpacing(8)
        btn_all = QPushButton("全選択")
        btn_all.setStyleSheet(
            f"QPushButton {{ font-size:11px; color:{_ACCENT}; background:transparent;"
            f" border:none; padding:2px 4px; min-height:0px; }}"
            f"QPushButton:hover {{ text-decoration:underline; }}"
        )
        btn_all.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_all.clicked.connect(self._select_all)
        sel_row.addWidget(btn_all)
        btn_none = QPushButton("全解除")
        btn_none.setStyleSheet(
            f"QPushButton {{ font-size:11px; color:{_TEXT2}; background:transparent;"
            f" border:none; padding:2px 4px; min-height:0px; }}"
            f"QPushButton:hover {{ text-decoration:underline; }}"
        )
        btn_none.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_none.clicked.connect(self._deselect_all)
        sel_row.addWidget(btn_none)
        sel_row.addStretch()
        root.addLayout(sel_row)

        # チェックボックス一覧（スクロール）
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border:none; background:transparent; }")

        list_w = QWidget()
        list_w.setStyleSheet("background:#ffffff; border-radius:6px;")
        self._list_vl = QVBoxLayout(list_w)
        self._list_vl.setContentsMargins(8, 8, 8, 8)
        self._list_vl.setSpacing(2)

        current_set = set(current)
        for name in available:
            chk = QCheckBox(name)
            chk.setChecked(name in current_set)
            chk.setStyleSheet(
                f"QCheckBox {{ font-size:12px; color:{_TEXT}; padding:4px 2px; }}"
                f"QCheckBox::indicator {{ width:16px; height:16px; }}"
                f"QCheckBox::indicator:checked {{ background:{_ACCENT}; border-color:{_ACCENT}; }}"
            )
            self._checks.append((chk, name))
            self._list_vl.addWidget(chk)

        self._list_vl.addStretch()
        scroll.setWidget(list_w)
        root.addWidget(scroll, 1)

        # 選択数ラベル
        self._lbl_count = QLabel()
        self._lbl_count.setStyleSheet(f"font-size:11px; color:{_TEXT2};")
        root.addWidget(self._lbl_count)
        self._update_count()
        for chk, _ in self._checks:
            chk.toggled.connect(lambda: self._update_count())

        # ボタン
        btns = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        btns.button(QDialogButtonBox.StandardButton.Ok).setText("決定")
        btns.button(QDialogButtonBox.StandardButton.Cancel).setText("キャンセル")
        btns.accepted.connect(self.accept)
        btns.rejected.connect(self.reject)
        root.addWidget(btns)

    def _select_all(self) -> None:
        for chk, _ in self._checks:
            if chk.isVisible():
                chk.setChecked(True)
        self._update_count()

    def _deselect_all(self) -> None:
        for chk, _ in self._checks:
            if chk.isVisible():
                chk.setChecked(False)
        self._update_count()

    def _on_filter(self, text: str) -> None:
        text_lower = text.lower()
        for chk, name in self._checks:
            chk.setVisible(text_lower in name.lower())

    def _update_count(self) -> None:
        n = sum(1 for chk, _ in self._checks if chk.isChecked())
        self._lbl_count.setText(f"{n} 件選択中")

    def selected_tests(self) -> list[str]:
        return [name for chk, name in self._checks if chk.isChecked()]
