"""ニュースページ — 業務連絡・重要通知の掲示板"""
import json
from datetime import datetime
from pathlib import Path

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QScrollArea, QDialog, QDialogButtonBox, QTextEdit,
    QLineEdit, QComboBox, QCheckBox, QMessageBox, QFileDialog,
    QFormLayout, QAbstractItemView,
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor

from app.config import DATA_PATH, CURRENT_USER

_BG2    = "#161b27"
_BG3    = "#1e2535"
_BORDER = "#2a3349"
_TEXT   = "#e8eaf0"
_TEXT2  = "#8b93a8"
_TEXT3  = "#5a6278"
_ACCENT = "#4a8cff"
_WARN   = "#f5a623"
_DANGER = "#e85454"
_SUCCESS= "#2ecc8a"

_NEWS_PATH = DATA_PATH / "bunseki" / "news" / "news.json"

_FLAG_COLORS = {
    "重要": _WARN,
    "期限": _DANGER,
    "通知": _TEXT3,
    "情報": _SUCCESS,
}


def _load_news() -> list[dict]:
    if _NEWS_PATH.exists():
        try:
            return json.loads(_NEWS_PATH.read_text(encoding="utf-8")).get("items", [])
        except Exception:
            pass
    # デモデータ（初回のみ）
    return [
        {
            "id": "n001",
            "title": "【重要】試薬AXの調製手順変更について",
            "body": "3月5日より試薬AXの調製手順が変更になります。新しい手順書を確認の上、作業を行ってください。\n変更点：手順2.3の撹拌時間が5分→10分に変更。手順2.7の温度設定が25℃→30℃に変更。",
            "target": "SS",
            "flag": "重要",
            "date": "2026-03-01 10:00",
            "author": "管理者",
            "read": False,
            "link": "",
        },
        {
            "id": "n002",
            "title": "装置Bのメンテナンス完了のお知らせ",
            "body": "2月28日に実施した装置Bの定期メンテナンスが完了しました。本日より通常通りの使用が可能です。",
            "target": "全部門",
            "flag": "通知",
            "date": "2026-02-28 17:30",
            "author": "鈴木",
            "read": True,
            "link": "",
        },
        {
            "id": "n003",
            "title": "年度末データ提出期限について",
            "body": "年度末分析データの提出期限は3月31日（火）17:00です。期限までに全タスクを「終了」状態にしてください。",
            "target": "全部門",
            "flag": "期限",
            "date": "2026-02-25 09:00",
            "author": "管理者",
            "read": True,
            "link": "",
        },
    ]


def _save_news(items: list[dict]):
    _NEWS_PATH.parent.mkdir(parents=True, exist_ok=True)
    _NEWS_PATH.write_text(
        json.dumps({"items": items}, ensure_ascii=False, indent=2), encoding="utf-8"
    )


def _next_id(items: list[dict]) -> str:
    nums = []
    for it in items:
        try:
            nums.append(int(it["id"].replace("n", "")))
        except (KeyError, ValueError):
            pass
    return f"n{(max(nums) + 1) if nums else 1:03d}"


class NewsPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._items: list[dict] = []
        self._setup_ui()
        self._load()

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
        tl.setSpacing(12)
        title_lbl = QLabel("ニュース")
        title_lbl.setStyleSheet(f"font-size:13px; font-weight:600; color:{_TEXT2};")
        tl.addWidget(title_lbl)
        tl.addStretch()

        # フィルタ
        self.filter_combo = QComboBox()
        self.filter_combo.addItems(["全て", "重要", "未読", "通知", "期限"])
        self.filter_combo.setStyleSheet(f"""
            QComboBox {{ background:{_BG3}; border:1px solid {_BORDER}; border-radius:6px;
                        padding:4px 10px; color:{_TEXT}; font-size:12px; min-width:90px; }}
            QComboBox QAbstractItemView {{ background:{_BG3}; color:{_TEXT};
                selection-background-color:{_ACCENT}; }}
        """)
        self.filter_combo.currentTextChanged.connect(self._apply_filter)
        tl.addWidget(self.filter_combo)

        new_btn = QPushButton("+ 新規投稿")
        new_btn.setStyleSheet(f"""
            QPushButton {{ background:{_ACCENT}; color:white; border:none;
                          padding:5px 12px; border-radius:6px; font-size:12px; }}
            QPushButton:hover {{ background:#5a9dff; }}
        """)
        new_btn.clicked.connect(self._new_post)
        tl.addWidget(new_btn)

        del_btn = QPushButton("選択削除")
        del_btn.setStyleSheet(f"""
            QPushButton {{ background:{_BG3}; color:{_DANGER}; border:1px solid {_BORDER};
                          padding:5px 10px; border-radius:6px; font-size:12px; }}
            QPushButton:hover {{ border-color:{_DANGER}; }}
        """)
        del_btn.clicked.connect(self._delete_selected)
        tl.addWidget(del_btn)

        root.addWidget(topbar)

        # Scroll
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setFrameShape(QFrame.Shape.NoFrame)
        root.addWidget(self.scroll)

        self.body = QWidget()
        self.body_layout = QVBoxLayout(self.body)
        self.body_layout.setContentsMargins(20, 20, 20, 20)
        self.body_layout.setSpacing(8)
        self.scroll.setWidget(self.body)

        # Header
        h1 = QLabel("ニュース")
        h1.setStyleSheet(f"font-size:20px; font-weight:700; color:{_TEXT};")
        self.body_layout.addWidget(h1)
        sub = QLabel("業務連絡・重要通知の掲示板")
        sub.setStyleSheet(f"font-size:12px; color:{_TEXT3};")
        self.body_layout.addWidget(sub)

        self.count_lbl = QLabel("")
        self.count_lbl.setStyleSheet(f"font-size:11px; color:{_TEXT3};")
        self.body_layout.addWidget(self.count_lbl)

        self._card_area_layout = QVBoxLayout()
        self._card_area_layout.setSpacing(6)
        self.body_layout.addLayout(self._card_area_layout)
        self.body_layout.addStretch()

    def _load(self):
        self._items = _load_news()
        self._apply_filter()

    def _apply_filter(self):
        f = self.filter_combo.currentText() if hasattr(self, "filter_combo") else "全て"
        items = self._items
        if f == "重要":
            items = [n for n in items if n.get("flag") == "重要"]
        elif f == "未読":
            items = [n for n in items if not n.get("read", False)]
        elif f in ("通知", "期限"):
            items = [n for n in items if n.get("flag") == f]

        # Clear
        while self._card_area_layout.count():
            w = self._card_area_layout.takeAt(0)
            if w.widget():
                w.widget().deleteLater()

        for news in items:
            card = self._build_card(news)
            self._card_area_layout.addWidget(card)

        self.count_lbl.setText(f"{len(items)} 件")

    def _build_card(self, news: dict) -> QFrame:
        flag_color = _FLAG_COLORS.get(news.get("flag", "通知"), _TEXT3)
        card = QFrame()
        card.setStyleSheet(f"""
            QFrame {{
                background:{_BG2};
                border:1px solid {_BORDER};
                border-left: 3px solid {flag_color};
                border-radius:8px;
            }}
        """)
        cl = QVBoxLayout(card)
        cl.setContentsMargins(16, 12, 16, 12)
        cl.setSpacing(6)

        row1 = QHBoxLayout()
        row1.setSpacing(10)

        # Select checkbox
        cb = QCheckBox()
        cb.setProperty("news_id", news.get("id"))
        row1.addWidget(cb)

        # Unread dot
        dot = QLabel()
        dot.setFixedSize(10, 10)
        if not news.get("read", False):
            dot.setStyleSheet(f"background:{_ACCENT}; border-radius:5px;")
        else:
            dot.setStyleSheet(f"background:transparent; border:2px solid {_BORDER}; border-radius:5px;")
        row1.addWidget(dot)

        title = QLabel(news.get("title", ""))
        weight = "600" if not news.get("read", False) else "400"
        title.setStyleSheet(f"font-size:13px; font-weight:{weight}; color:{_TEXT};")
        row1.addWidget(title, 1)

        # Target tag
        if news.get("target"):
            tgt = QLabel(news["target"])
            tgt.setStyleSheet(f"color:{_ACCENT}; background:rgba(74,140,255,0.15); border-radius:4px; padding:2px 8px; font-size:11px;")
            row1.addWidget(tgt)

        # Flag tag
        flag_lbl = QLabel(news.get("flag", "通知"))
        flag_lbl.setStyleSheet(f"color:{flag_color}; border-radius:4px; padding:2px 8px; font-size:11px; border:1px solid {flag_color};")
        row1.addWidget(flag_lbl)

        date_lbl = QLabel(news.get("date", ""))
        date_lbl.setStyleSheet(f"font-size:11px; color:{_TEXT3};")
        row1.addWidget(date_lbl)

        author_lbl = QLabel(news.get("author", ""))
        author_lbl.setStyleSheet(f"font-size:12px; color:{_TEXT2};")
        row1.addWidget(author_lbl)

        open_btn = QPushButton("開く")
        open_btn.setStyleSheet(f"""
            QPushButton {{ background:{_BG3}; color:{_ACCENT}; border:1px solid {_BORDER};
                          padding:3px 10px; border-radius:4px; font-size:11px; }}
            QPushButton:hover {{ border-color:{_ACCENT}; }}
        """)
        n = news
        open_btn.clicked.connect(lambda _=False, item=n: self._open_news(item))
        row1.addWidget(open_btn)
        cl.addLayout(row1)

        preview = QLabel((news.get("body", ""))[:100] + ("…" if len(news.get("body", "")) > 100 else ""))
        preview.setStyleSheet(f"font-size:12px; color:{_TEXT2};")
        preview.setWordWrap(True)
        cl.addWidget(preview)

        return card

    def _open_news(self, news: dict):
        # Mark as read
        for it in self._items:
            if it.get("id") == news.get("id"):
                it["read"] = True
        _save_news(self._items)

        dlg = QDialog(self)
        dlg.setWindowTitle(news.get("title", ""))
        dlg.resize(580, 380)
        vl = QVBoxLayout(dlg)
        vl.setSpacing(12)
        vl.setContentsMargins(24, 20, 24, 20)

        title_lbl = QLabel(news.get("title", ""))
        title_lbl.setStyleSheet(f"font-size:15px; font-weight:700; color:{_TEXT};")
        title_lbl.setWordWrap(True)
        vl.addWidget(title_lbl)

        meta = f"{news.get('date','')}  {news.get('author','')}  対象: {news.get('target','')}"
        meta_lbl = QLabel(meta)
        meta_lbl.setStyleSheet(f"font-size:11px; color:{_TEXT3};")
        vl.addWidget(meta_lbl)

        if news.get("link"):
            link_lbl = QLabel(f"リンク: <a href='{news['link']}' style='color:{_ACCENT};'>{news['link']}</a>")
            link_lbl.setOpenExternalLinks(True)
            vl.addWidget(link_lbl)

        body_edit = QTextEdit()
        body_edit.setPlainText(news.get("body", ""))
        body_edit.setReadOnly(True)
        vl.addWidget(body_edit)

        btns = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        btns.rejected.connect(dlg.accept)
        vl.addWidget(btns)
        dlg.exec()
        self._apply_filter()

    def _new_post(self):
        dlg = _PostDialog(parent=self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            values = dlg.values()
            items = _load_news()
            new_id = _next_id(items)
            items.insert(0, {
                "id": new_id,
                "date": datetime.now().strftime("%Y-%m-%d %H:%M"),
                "author": CURRENT_USER,
                "read": True,
                **values,
            })
            _save_news(items)
            self._items = items
            self._apply_filter()

    def _delete_selected(self):
        # Collect checked IDs
        checked_ids = []
        for i in range(self._card_area_layout.count()):
            w = self._card_area_layout.itemAt(i).widget()
            if w is None:
                continue
            for cb in w.findChildren(QCheckBox):
                if cb.isChecked():
                    checked_ids.append(cb.property("news_id"))

        if not checked_ids:
            QMessageBox.information(self, "情報", "削除するニュースを選択してください（チェックボックス）。")
            return

        reply = QMessageBox.question(
            self, "削除確認",
            f"選択した {len(checked_ids)} 件のニュースを削除しますか？\nこの操作は元に戻せません。"
        )
        if reply == QMessageBox.StandardButton.Yes:
            items = [n for n in self._items if n.get("id") not in checked_ids]
            _save_news(items)
            self._items = items
            self._apply_filter()


class _PostDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("ニュース投稿")
        self.resize(520, 400)
        vl = QVBoxLayout(self)
        vl.setSpacing(10)
        vl.setContentsMargins(20, 16, 20, 16)

        form = QFormLayout()
        self.title_input = QLineEdit()
        self.title_input.setPlaceholderText("タイトルを入力...")
        self.target_input = QLineEdit()
        self.target_input.setPlaceholderText("例: SS, AB, 全部門")
        self.flag_combo = QComboBox()
        self.flag_combo.addItems(["通知", "重要", "期限", "情報"])
        self.link_input = QLineEdit()
        self.link_input.setPlaceholderText("https://...")
        form.addRow("タイトル:", self.title_input)
        form.addRow("対象:", self.target_input)
        form.addRow("フラグ:", self.flag_combo)
        form.addRow("リンク:", self.link_input)
        vl.addLayout(form)

        body_lbl = QLabel("内容:")
        body_lbl.setStyleSheet(f"color:{_TEXT2}; font-size:12px;")
        vl.addWidget(body_lbl)

        self.body_edit = QTextEdit()
        self.body_edit.setMinimumHeight(120)
        self.body_edit.setPlaceholderText("本文を入力...")
        vl.addWidget(self.body_edit)

        btns = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        btns.accepted.connect(self._accept)
        btns.rejected.connect(self.reject)
        vl.addWidget(btns)

    def _accept(self):
        if not self.title_input.text().strip():
            QMessageBox.warning(self, "入力エラー", "タイトルを入力してください。")
            return
        self.accept()

    def values(self) -> dict:
        return {
            "title": self.title_input.text().strip(),
            "body": self.body_edit.toPlainText().strip(),
            "target": self.target_input.text().strip() or "全部門",
            "flag": self.flag_combo.currentText(),
            "link": self.link_input.text().strip(),
            "read": False,
        }
