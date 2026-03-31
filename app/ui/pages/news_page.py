"""ニュースページ — 業務連絡・重要通知の掲示板。"""
from __future__ import annotations

import webbrowser
from datetime import datetime

from PySide6.QtCore import Qt, QSize, Signal
from PySide6.QtGui import QColor, QFont
from PySide6.QtWidgets import (
    QCheckBox, QDialog, QDialogButtonBox,
    QFrame, QHBoxLayout, QLabel,
    QLineEdit, QListWidget, QListWidgetItem, QMessageBox,
    QPushButton, QScrollArea, QSizePolicy,
    QTextEdit, QVBoxLayout, QWidget,
)

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
    """ニュース一覧 + 編集フォーム。"""

    def __init__(self, data_service: DataService, parent: QWidget | None = None):
        super().__init__(parent)
        self._ds = data_service
        self._selected_id: str | None = None
        self._is_new = False
        self._build_ui()

    # ── UI 構築 ───────────────────────────────────────────────────────────────

    def _build_ui(self) -> None:
        root = QHBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)
        root.addWidget(self._build_list_panel(), 0)
        root.addWidget(self._build_edit_panel(), 1)

    # ── 左: 一覧パネル ────────────────────────────────────────────────────────

    def _build_list_panel(self) -> QWidget:
        panel = QWidget()
        panel.setFixedWidth(320)
        panel.setStyleSheet(f"background:{_BG2};")
        vl = QVBoxLayout(panel)
        vl.setContentsMargins(0, 0, 0, 0)
        vl.setSpacing(0)

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

        self.list_widget = QListWidget()
        self.list_widget.setStyleSheet(
            "QListWidget { border:none; background:transparent; }"
            "QListWidget::item { border-bottom:1px solid #f1f5f9; padding:0; }"
            "QListWidget::item:selected { background:#eff6ff; }"
        )
        self.list_widget.currentItemChanged.connect(self._on_item_selected)
        vl.addWidget(self.list_widget, 1)
        return panel

    # ── 右: 編集パネル ────────────────────────────────────────────────────────

    def _build_edit_panel(self) -> QWidget:
        self.edit_panel = QWidget()
        self.edit_panel.setStyleSheet(f"background:{_BG};")
        panel_vl = QVBoxLayout(self.edit_panel)
        panel_vl.setContentsMargins(0, 0, 0, 0)
        panel_vl.setSpacing(0)

        # 空の状態
        self.empty_lbl = QLabel("ニュースを選択、または新規作成してください")
        self.empty_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.empty_lbl.setStyleSheet(f"font-size:14px; color:{_TEXT2};")
        panel_vl.addWidget(self.empty_lbl)

        # 編集フォーム（スクロール）
        self.form_scroll = QScrollArea()
        self.form_scroll.setWidgetResizable(True)
        self.form_scroll.setStyleSheet("QScrollArea { border:none; background:transparent; }")
        self.form_scroll.setVisible(False)

        form_w = QWidget()
        form_w.setStyleSheet(f"background:{_BG};")
        form_vl = QVBoxLayout(form_w)
        form_vl.setContentsMargins(24, 20, 24, 20)
        form_vl.setSpacing(12)

        def row(label: str, widget: QWidget) -> QHBoxLayout:
            hl = QHBoxLayout()
            lbl = QLabel(label)
            lbl.setFixedWidth(110)
            lbl.setStyleSheet(f"font-size:12px; font-weight:600; color:{_TEXT2};")
            hl.addWidget(lbl)
            hl.addWidget(widget, 1)
            return hl

        # タイトル
        self.edit_title = QLineEdit()
        self.edit_title.setPlaceholderText("ニュースタイトル")
        self.edit_title.setStyleSheet(
            f"QLineEdit {{ border:1px solid {_BORDER}; border-radius:4px;"
            f" padding:4px 8px; font-size:12px; color:{_TEXT}; }}"
            f"QLineEdit:focus {{ border-color:{_ACCENT}; }}"
        )
        form_vl.addLayout(row("タイトル *", self.edit_title))

        # 分析項目
        tests_w = QWidget()
        tests_w.setFixedHeight(54)
        tests_w.setStyleSheet("background:transparent;")
        tests_hl = QHBoxLayout(tests_w)
        tests_hl.setContentsMargins(0, 0, 0, 0)
        tests_hl.setSpacing(6)

        self._selected_tests: list[str] = []
        self._tags_scroll = QScrollArea()
        self._tags_scroll.setWidgetResizable(True)
        self._tags_scroll.setFixedHeight(50)
        self._tags_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self._tags_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self._tags_scroll.setStyleSheet(
            f"QScrollArea {{ border:1px solid {_BORDER}; border-radius:6px; background:#ffffff; }}"
        )
        self._tags_inner = QWidget()
        self._tags_inner.setStyleSheet("background:transparent;")
        self.tags_layout = QHBoxLayout(self._tags_inner)
        self.tags_layout.setContentsMargins(6, 4, 6, 4)
        self.tags_layout.setSpacing(6)
        self.tags_layout.addStretch()
        self._tags_scroll.setWidget(self._tags_inner)
        tests_hl.addWidget(self._tags_scroll, 1)

        btn_add_test = QPushButton("+")
        btn_add_test.setFixedSize(36, 36)
        btn_add_test.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_add_test.setStyleSheet(
            f"QPushButton {{ background:{_ACCENT}; color:white; border:none;"
            f" border-radius:6px; font-size:18px; font-weight:700;"
            f" min-height:0px; max-height:36px; padding:0px; text-align:center; }}"
            f"QPushButton:hover {{ background:#2563eb; }}"
        )
        btn_add_test.clicked.connect(self._open_test_select_dialog)
        tests_hl.addWidget(btn_add_test)
        form_vl.addLayout(row("分析項目", tests_w))

        # サンプル
        samples_w = QWidget()
        samples_w.setFixedHeight(54)
        samples_w.setStyleSheet("background:transparent;")
        samples_hl = QHBoxLayout(samples_w)
        samples_hl.setContentsMargins(0, 0, 0, 0)
        samples_hl.setSpacing(6)

        self._selected_samples: list[str] = []
        self._samples_scroll = QScrollArea()
        self._samples_scroll.setWidgetResizable(True)
        self._samples_scroll.setFixedHeight(50)
        self._samples_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self._samples_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self._samples_scroll.setStyleSheet(
            f"QScrollArea {{ border:1px solid {_BORDER}; border-radius:6px; background:#ffffff; }}"
        )
        self._samples_inner = QWidget()
        self._samples_inner.setStyleSheet("background:transparent;")
        self.samples_layout = QHBoxLayout(self._samples_inner)
        self.samples_layout.setContentsMargins(6, 4, 6, 4)
        self.samples_layout.setSpacing(6)
        self.samples_layout.addStretch()
        self._samples_scroll.setWidget(self._samples_inner)
        samples_hl.addWidget(self._samples_scroll, 1)

        btn_add_sample = QPushButton("+")
        btn_add_sample.setFixedSize(36, 36)
        btn_add_sample.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_add_sample.setStyleSheet(
            f"QPushButton {{ background:{_ACCENT}; color:white; border:none;"
            f" border-radius:6px; font-size:18px; font-weight:700;"
            f" min-height:0px; max-height:36px; padding:0px; text-align:center; }}"
            f"QPushButton:hover {{ background:#2563eb; }}"
        )
        btn_add_sample.clicked.connect(self._open_sample_select_dialog)
        samples_hl.addWidget(btn_add_sample)
        form_vl.addLayout(row("サンプル", samples_w))

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
        form_vl.addLayout(row("対象期間", period_w))

        # 本文
        lbl_body = QLabel("本文")
        lbl_body.setStyleSheet(f"font-size:12px; font-weight:600; color:{_TEXT2};")
        form_vl.addWidget(lbl_body)
        self.edit_body = QTextEdit()
        self.edit_body.setPlaceholderText("本文を入力してください")
        self.edit_body.setMinimumHeight(140)
        self.edit_body.setStyleSheet(
            f"QTextEdit {{ border:1px solid {_BORDER}; border-radius:6px;"
            f" padding:8px; font-size:13px; color:{_TEXT}; }}"
        )
        form_vl.addWidget(self.edit_body)

        # 添付リンク
        lbl_links = QLabel("添付リンク")
        lbl_links.setStyleSheet(f"font-size:12px; font-weight:600; color:{_TEXT2};")
        form_vl.addWidget(lbl_links)
        self.links_container = QVBoxLayout()
        self.links_container.setSpacing(6)
        form_vl.addLayout(self.links_container)

        self.btn_add_link = QPushButton("+ リンクを追加")
        self.btn_add_link.setStyleSheet(
            f"QPushButton {{ background:{_BG}; color:{_ACCENT}; border:1px dashed {_ACCENT};"
            f" border-radius:6px; font-size:12px; padding:8px 14px; }}"
            f"QPushButton:hover {{ background:#eff6ff; }}"
        )
        self.btn_add_link.clicked.connect(lambda: self._add_link_row())
        form_vl.addWidget(self.btn_add_link)

        # 重要フラグ
        self.chk_important = QCheckBox("重要（一覧の先頭に目立つように表示）")
        self.chk_important.setStyleSheet(
            f"QCheckBox {{ font-size:12px; color:{_IMPORTANT_FG}; font-weight:600; }}"
            f"QCheckBox::indicator:checked {{ background:{_IMPORTANT_FG}; border-color:{_IMPORTANT_FG}; }}"
        )
        form_vl.addWidget(self.chk_important)

        form_vl.addStretch()

        # 保存 / 削除ボタン
        btn_row = QHBoxLayout()
        btn_row.addStretch()
        self.btn_delete = QPushButton("削除")
        self.btn_delete.setStyleSheet(
            f"QPushButton {{ background:#fef2f2; color:{_DANGER}; border:1px solid #fecaca;"
            f" padding:6px 20px; border-radius:6px; font-size:13px; }}"
            f"QPushButton:hover {{ background:#fee2e2; }}"
        )
        self.btn_delete.clicked.connect(self._on_delete)
        btn_row.addWidget(self.btn_delete)

        self.btn_save = QPushButton("保存")
        self.btn_save.setStyleSheet(
            f"QPushButton {{ background:{_ACCENT}; color:white; border:none;"
            f" padding:6px 24px; border-radius:6px; font-size:13px; font-weight:600; }}"
            f"QPushButton:hover {{ background:#2563eb; }}"
        )
        self.btn_save.clicked.connect(self._on_save)
        btn_row.addWidget(self.btn_save)
        form_vl.addLayout(btn_row)

        self.form_scroll.setWidget(form_w)
        panel_vl.addWidget(self.form_scroll, 1)

        return self.edit_panel

    # ── 公開API ───────────────────────────────────────────────────────────────

    def refresh(self) -> None:
        self._reload_list()

    # ── 一覧操作 ──────────────────────────────────────────────────────────────

    def _reload_list(self) -> None:
        self.list_widget.blockSignals(True)
        self.list_widget.clear()
        for news in news_store.get_all():
            item = QListWidgetItem()
            item.setData(Qt.ItemDataRole.UserRole, news["id"])
            item.setSizeHint(QSize(0, 72))
            self.list_widget.addItem(item)
            card = self._build_list_card(news)
            self.list_widget.setItemWidget(item, card)
            if news["id"] == self._selected_id:
                self.list_widget.setCurrentItem(item)
        self.list_widget.blockSignals(False)
        if self._selected_id:
            news = news_store.get(self._selected_id)
            if news:
                self._load_form(news)
            else:
                self._clear_form()
        else:
            self._clear_form()

    def _build_list_card(self, news: dict) -> QWidget:
        is_important = news.get("is_important", False)
        w = QWidget()
        if is_important:
            w.setStyleSheet(
                f"background:{_IMPORTANT_BG}; border-left:3px solid {_IMPORTANT_FG};"
            )
        else:
            w.setStyleSheet("background:transparent;")
        vl = QVBoxLayout(w)
        vl.setContentsMargins(14, 10, 14, 10)
        vl.setSpacing(3)

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
        title.setStyleSheet(f"font-size:13px; font-weight:600; color:{title_color};")
        title.setWordWrap(False)
        title_row.addWidget(title, 1)
        vl.addLayout(title_row)

        meta = QLabel(f"{news.get('created_at', '')[:10]}  {news.get('created_by', '')}")
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
        self._is_new = False
        news = news_store.get(news_id)
        if news:
            self._load_form(news)

    # ── フォーム操作 ──────────────────────────────────────────────────────────

    def _clear_form(self) -> None:
        self._selected_id = None
        self._is_new = False
        self.empty_lbl.setVisible(True)
        self.form_scroll.setVisible(False)

    def _reset_form(self) -> None:
        """フォームを空にする。"""
        self.edit_title.clear()
        self._selected_tests.clear()
        self._rebuild_tags()
        self._selected_samples.clear()
        self._rebuild_sample_tags()
        self.edit_period_from.clear()
        self.edit_period_to.clear()
        self.edit_body.clear()
        # リンク行をクリア
        self._link_rows.clear()
        while self.links_container.count():
            item = self.links_container.takeAt(0)
            if w := item.widget():
                w.deleteLater()
        self.chk_important.setChecked(False)

    def _load_form(self, news: dict) -> None:
        """既存ニュースをフォームに読み込む。"""
        self._reset_form()
        self.empty_lbl.setVisible(False)
        self.form_scroll.setVisible(True)
        self.btn_delete.setVisible(not self._is_new)

        self.edit_title.setText(news.get("title", ""))
        for t in news.get("target_tests", []):
            self._add_test_tag(t)
        for s in news.get("target_samples", []):
            self._add_sample_tag(s)
        self.edit_period_from.setText(news.get("target_period_from", ""))
        self.edit_period_to.setText(news.get("target_period_to", ""))
        self.edit_body.setPlainText(news.get("body", ""))
        for link in news.get("links", []):
            self._add_link_row(link.get("label", ""), link.get("url", ""))
        self.chk_important.setChecked(news.get("is_important", False))

    def _show_new_form(self) -> None:
        """空のフォームを表示する。"""
        self._reset_form()
        self.empty_lbl.setVisible(False)
        self.form_scroll.setVisible(True)
        self.btn_delete.setVisible(False)

    def _on_new(self) -> None:
        self.list_widget.clearSelection()
        self._selected_id = None
        self._is_new = True
        self._show_new_form()

    def _on_save(self) -> None:
        title = self.edit_title.text().strip()
        if not title:
            QMessageBox.warning(self, "入力エラー", "タイトルを入力してください。")
            return
        data = self._collect_form_data()
        if self._is_new:
            item = news_store.create(
                title=data["title"],
                body=data["body"],
                created_by=CURRENT_USER,
                target_tests=data["target_tests"],
                target_samples=data["target_samples"],
                target_period_from=data["target_period_from"],
                target_period_to=data["target_period_to"],
                links=data["links"],
                is_important=data["is_important"],
            )
            self._selected_id = item["id"]
            self._is_new = False
        else:
            news_store.update(
                self._selected_id,
                title=data["title"],
                body=data["body"],
                target_tests=data["target_tests"],
                target_samples=data["target_samples"],
                target_period_from=data["target_period_from"],
                target_period_to=data["target_period_to"],
                links=data["links"],
                is_important=data["is_important"],
            )
        self._reload_list()

    def _on_delete(self) -> None:
        if not self._selected_id or self._is_new:
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

    def _collect_form_data(self) -> dict:
        links = [
            {"label": lbl.text().strip(), "url": url.text().strip()}
            for lbl, url in self._link_rows
            if url.text().strip()
        ]
        return {
            "title": self.edit_title.text().strip(),
            "body": self.edit_body.toPlainText(),
            "target_tests": list(self._selected_tests),
            "target_samples": list(self._selected_samples),
            "target_period_from": self.edit_period_from.text().strip(),
            "target_period_to": self.edit_period_to.text().strip(),
            "links": links,
            "is_important": self.chk_important.isChecked(),
        }

    # ── リンク行 ──────────────────────────────────────────────────────────────

    _link_rows: list[tuple[QLineEdit, QLineEdit]]

    def __init_subclass__(cls, **kw):
        super().__init_subclass__(**kw)

    def _add_link_row(self, label: str = "", url: str = "") -> None:
        if not hasattr(self, "_link_rows"):
            self._link_rows = []
        row_w = QWidget()
        hl = QHBoxLayout(row_w)
        hl.setContentsMargins(0, 0, 0, 0)
        hl.setSpacing(6)

        edit_label = QLineEdit(label)
        edit_label.setPlaceholderText("ラベル（例: 分析マニュアル）")
        edit_label.setStyleSheet(
            f"QLineEdit {{ border:1px solid {_BORDER}; border-radius:4px;"
            f" padding:4px 8px; font-size:12px; color:{_TEXT}; }}"
            f"QLineEdit:focus {{ border-color:{_ACCENT}; }}"
        )
        hl.addWidget(edit_label, 1)

        edit_url = QLineEdit(url)
        edit_url.setPlaceholderText("URL（例: https://...）")
        edit_url.setStyleSheet(
            f"QLineEdit {{ border:1px solid {_BORDER}; border-radius:4px;"
            f" padding:4px 8px; font-size:12px; color:{_TEXT}; }}"
            f"QLineEdit:focus {{ border-color:{_ACCENT}; }}"
        )
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
        tests = self._get_test_names()
        dlg = _TestSelectDialog(tests, list(self._selected_tests), parent=self)
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
        while self.tags_layout.count() > 1:
            item = self.tags_layout.takeAt(0)
            if w := item.widget():
                w.deleteLater()
        for i, t in enumerate(self._selected_tests):
            chip = self._make_tag_chip(t, self._remove_test_tag)
            self.tags_layout.insertWidget(i, chip)
        self._tags_inner.adjustSize()

    # ── サンプルタグ選択 ─────────────────────────────────────────────────────

    def _open_sample_select_dialog(self) -> None:
        samples = self._get_sample_names()
        dlg = _TestSelectDialog(samples, list(self._selected_samples), parent=self)
        dlg.setWindowTitle("サンプルの選択")
        if dlg.exec() == QDialog.DialogCode.Accepted:
            self._selected_samples = dlg.selected_tests()
            self._rebuild_sample_tags()

    def _add_sample_tag(self, text: str) -> None:
        if not text or text in self._selected_samples:
            return
        self._selected_samples.append(text)
        self._rebuild_sample_tags()

    def _remove_sample_tag(self, text: str) -> None:
        if text in self._selected_samples:
            self._selected_samples.remove(text)
            self._rebuild_sample_tags()

    def _rebuild_sample_tags(self) -> None:
        while self.samples_layout.count() > 1:
            item = self.samples_layout.takeAt(0)
            if w := item.widget():
                w.deleteLater()
        for i, t in enumerate(self._selected_samples):
            chip = self._make_tag_chip(t, self._remove_sample_tag)
            self.samples_layout.insertWidget(i, chip)
        self._samples_inner.adjustSize()

    # ── タグチップ ────────────────────────────────────────────────────────────

    def _make_tag_chip(self, text: str, remove_callback) -> QWidget:
        chip = QWidget()
        chip.setFixedHeight(32)
        chip.setStyleSheet(
            f"background:#eff6ff; border:1px solid #bfdbfe; border-radius:6px;"
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
        btn.clicked.connect(lambda _=False, t=text: remove_callback(t))
        hl.addWidget(btn)
        return chip

    # ── データ取得 ────────────────────────────────────────────────────────────

    def _get_test_names(self) -> list[str]:
        try:
            groups = self._ds.get_holder_groups()
            return [g["holder_group_name"] for g in groups if g.get("holder_group_name")]
        except Exception:
            return []

    def _get_sample_names(self) -> list[str]:
        try:
            samples = self._ds.get_valid_samples()
            return [
                s["display_name"]
                for s in samples
                if s.get("display_name")
                and s.get("domain_code") == "WH"
                and s.get("is_active", True)
            ]
        except Exception:
            return []


# ── 分析項目/サンプル選択ダイアログ ───────────────────────────────────────────

class _TestSelectDialog(QDialog):
    """チェックボックス一覧で項目を複数選択するダイアログ。"""

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

        header = QLabel("対象の分析項目を選択してください")
        header.setStyleSheet(f"font-size:13px; font-weight:600; color:{_TEXT};")
        root.addWidget(header)

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

        sel_row = QHBoxLayout()
        sel_row.setSpacing(8)
        btn_all = QPushButton("全選択")
        btn_all.setStyleSheet(
            f"QPushButton {{ font-size:11px; color:{_ACCENT}; background:transparent;"
            f" border:none; padding:2px 4px; min-height:0px; }}"
        )
        btn_all.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_all.clicked.connect(self._select_all)
        sel_row.addWidget(btn_all)
        btn_none = QPushButton("全解除")
        btn_none.setStyleSheet(
            f"QPushButton {{ font-size:11px; color:{_TEXT2}; background:transparent;"
            f" border:none; padding:2px 4px; min-height:0px; }}"
        )
        btn_none.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_none.clicked.connect(self._deselect_all)
        sel_row.addWidget(btn_none)
        sel_row.addStretch()
        root.addLayout(sel_row)

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

        self._lbl_count = QLabel()
        self._lbl_count.setStyleSheet(f"font-size:11px; color:{_TEXT2};")
        root.addWidget(self._lbl_count)
        self._update_count()
        for chk, _ in self._checks:
            chk.toggled.connect(lambda: self._update_count())

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
