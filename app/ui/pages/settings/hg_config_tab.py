"""タスク設定タブ — 分析項目×ステータス別レイアウト。

分析項目（ホルダグループ）ごとに、タスクのステータス別に
設定項目を縦長ブロックで表示する。
"""
from __future__ import annotations

from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QFontMetrics
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from app.services.hg_config_service import HgConfigService
from app.ui.widgets.icon_utils import get_icon


class _ElidedLabel(QLabel):
    """横幅に収まらないテキストを「...」で省略するラベル。"""

    def __init__(self, text: str, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._full_text = text
        self.setToolTip(text)
        self.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Preferred)
        self.setMinimumWidth(0)
        self._update_elided()

    def resizeEvent(self, event) -> None:  # noqa: N802
        super().resizeEvent(event)
        self._update_elided()

    def _update_elided(self) -> None:
        fm = QFontMetrics(self.font())
        elided = fm.elidedText(
            self._full_text, Qt.TextElideMode.ElideMiddle, self.width()
        )
        super().setText(elided)


def _make_delete_button() -> QPushButton:
    """共通の削除ボタンを生成する。"""
    btn = QPushButton()
    btn.setIcon(get_icon(":/icons/cancel.svg", "#ef4444", 14))
    btn.setIconSize(QSize(14, 14))
    btn.setFixedSize(28, 28)
    btn.setCursor(Qt.CursorShape.PointingHandCursor)
    btn.setToolTip("削除")
    btn.setStyleSheet(
        "QPushButton { background:transparent; border:1px solid #e5e7eb;"
        " border-radius:4px; padding:0; min-height:0; min-width:0; }"
        "QPushButton:hover { background:rgba(239,68,68,0.10);"
        " border-color:#ef4444; }"
    )
    return btn


# ── ステータス定義 ────────────────────────────────────────────────────────────

STATUS_DEFS: list[tuple[str, str]] = [
    ("task_setup",          "起票"),
    ("analysis_targets",    "サンプル"),
    ("analysis",            "分析"),
    ("result_entry",        "入力"),
    ("result_verification", "チェック"),
    ("submission",          "フロー"),
    ("completed",           "終了"),
]


# ── 再利用可能なチェックリストエディタ ─────────────────────────────────────

class _ChecklistEditor(QWidget):
    """チェックリスト項目の追加・削除ができるウィジェット。"""

    def __init__(self, title: str, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._items: list[str] = []
        self._rows: list[QWidget] = []

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)

        lbl = QLabel(title)
        lbl.setStyleSheet("font-weight: 600; font-size: 13px; color: #374151;")
        layout.addWidget(lbl)

        # 項目リスト領域（子ブロック）
        self._list_block = QFrame()
        self._list_block.setObjectName("list_block")
        self._list_block.setStyleSheet(
            "QFrame#list_block { background: #ffffff; border: 1px solid #e5e7eb; "
            "border-radius: 6px; }"
            "QFrame#list_block QWidget { background: #ffffff; }"
        )
        list_bl = QVBoxLayout(self._list_block)
        list_bl.setContentsMargins(12, 4, 12, 4)
        list_bl.setSpacing(0)
        self._list_layout = QVBoxLayout()
        self._list_layout.setSpacing(0)
        list_bl.addLayout(self._list_layout)
        self._list_block.setVisible(False)
        layout.addWidget(self._list_block)

        # 追加行
        add_row = QHBoxLayout()
        add_row.setSpacing(6)
        self._input = QLineEdit()
        self._input.setPlaceholderText("項目を入力")
        self._input.returnPressed.connect(self._on_add)
        add_row.addWidget(self._input, 1)

        btn_add = QPushButton("追加")
        btn_add.setStyleSheet(
            "background: #3b82f6; color: white; border: none; "
            "border-radius: 4px; padding: 4px 12px; font-weight: 600;"
        )
        btn_add.clicked.connect(self._on_add)
        add_row.addWidget(btn_add)
        layout.addLayout(add_row)

    def set_items(self, items: list[str]) -> None:
        self._items = list(items)
        self._rebuild()

    def get_items(self) -> list[str]:
        return list(self._items)

    def _rebuild(self) -> None:
        for row in self._rows:
            row.deleteLater()
        self._rows.clear()
        self._list_block.setVisible(bool(self._items))

        for i, text in enumerate(self._items):
            row = QWidget()
            hl = QHBoxLayout(row)
            hl.setContentsMargins(8, 4, 16, 4)
            hl.setSpacing(12)

            cb = QCheckBox(text)
            cb.setChecked(False)
            cb.setEnabled(False)
            cb.setSizePolicy(
                QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Preferred
            )
            cb.setMinimumWidth(0)
            if i == len(self._items) - 1:
                cb.setStyleSheet("border-bottom: none;")
            hl.addWidget(cb, 1)

            btn_del = _make_delete_button()
            idx = i
            btn_del.clicked.connect(lambda _=False, j=idx: self._on_remove(j))
            hl.addWidget(btn_del, alignment=Qt.AlignmentFlag.AlignVCenter)

            self._list_layout.addWidget(row)
            self._rows.append(row)

    def _on_add(self) -> None:
        text = self._input.text().strip()
        if not text:
            return
        self._items.append(text)
        self._input.clear()
        self._rebuild()

    def _on_remove(self, idx: int) -> None:
        if 0 <= idx < len(self._items):
            self._items.pop(idx)
            self._rebuild()


# ── ドキュメントエディタ ──────────────────────────────────────────────────────

_DOC_ROW_STYLE = (
    "QWidget#doc_row { background: #ffffff; border: 1px solid #e5e7eb; "
    "border-radius: 6px; }"
)

_INPUT_STYLE = (
    "border: 1px solid #d1d5db; border-radius: 4px; padding: 4px 8px;"
)


def _classify_location(value: str) -> str:
    """入力値がリンクかパスかを判定する。"""
    v = value.strip()
    if v.startswith(("http://", "https://", "//")):
        return "link"
    return "path"


class _DocumentsEditor(QWidget):
    """ドキュメント（リンクまたはパス）を複数登録できるウィジェット。"""

    def __init__(self, title: str = "ドキュメント", parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._docs: list[dict[str, str]] = []
        self._rows: list[QWidget] = []

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        lbl = QLabel(title)
        lbl.setStyleSheet("font-weight: 600; font-size: 13px; color: #374151;")
        layout.addWidget(lbl)

        # 登録済みドキュメント一覧（子ブロック）
        self._list_block = QFrame()
        self._list_block.setObjectName("doc_list_block")
        self._list_block.setStyleSheet(
            "QFrame#doc_list_block { background: #ffffff; border: 1px solid #e5e7eb; "
            "border-radius: 6px; }"
            "QFrame#doc_list_block QWidget { background: #ffffff; }"
        )
        list_bl = QVBoxLayout(self._list_block)
        list_bl.setContentsMargins(12, 8, 12, 8)
        list_bl.setSpacing(6)
        self._list_layout = QVBoxLayout()
        self._list_layout.setSpacing(6)
        list_bl.addLayout(self._list_layout)
        self._list_block.setVisible(False)
        layout.addWidget(self._list_block)

        # 追加フォーム
        form = QWidget()
        fl = QVBoxLayout(form)
        fl.setContentsMargins(0, 4, 0, 0)
        fl.setSpacing(8)

        # 名前
        row_name = QHBoxLayout()
        row_name.setSpacing(6)
        lbl_name = QLabel("名前")
        lbl_name.setFixedWidth(70)
        lbl_name.setStyleSheet("font-size: 12px; color: #6b7280;")
        row_name.addWidget(lbl_name)
        self._input_name = QLineEdit()
        self._input_name.setPlaceholderText("ドキュメント名")
        row_name.addWidget(self._input_name, 1)
        fl.addLayout(row_name)

        # 場所（リンクまたはパス — 自動判定）
        row_loc = QHBoxLayout()
        row_loc.setSpacing(6)
        lbl_loc = QLabel("場所")
        lbl_loc.setFixedWidth(70)
        lbl_loc.setStyleSheet("font-size: 12px; color: #6b7280;")
        row_loc.addWidget(lbl_loc)
        self._input_location = QLineEdit()
        self._input_location.setPlaceholderText(
            "URL または ファイル/フォルダパス"
        )
        row_loc.addWidget(self._input_location, 1)
        fl.addLayout(row_loc)

        # 追加ボタン
        btn_row = QHBoxLayout()
        btn_row.addStretch()
        btn_add = QPushButton("追加")
        btn_add.setStyleSheet(
            "background: #3b82f6; color: white; border: none; "
            "border-radius: 4px; padding: 4px 16px; font-weight: 600;"
        )
        btn_add.clicked.connect(self._on_add)
        btn_row.addWidget(btn_add)
        fl.addLayout(btn_row)

        layout.addWidget(form)

    def set_documents(self, docs: list[dict[str, str]]) -> None:
        self._docs = [dict(d) for d in docs]
        self._rebuild()

    def get_documents(self) -> list[dict[str, str]]:
        return [dict(d) for d in self._docs]

    def _rebuild(self) -> None:
        for row in self._rows:
            row.deleteLater()
        self._rows.clear()
        self._list_block.setVisible(bool(self._docs))

        for i, doc in enumerate(self._docs):
            row = QWidget()
            hl = QHBoxLayout(row)
            hl.setContentsMargins(10, 8, 10, 8)
            hl.setSpacing(8)

            # 情報表示
            info_layout = QVBoxLayout()
            info_layout.setSpacing(2)

            name_text = doc.get("name", "（名前なし）")
            name_lbl = _ElidedLabel(name_text)
            name_lbl.setStyleSheet(
                "font-size: 13px; font-weight: 600; color: #1f2937; border: none;"
            )
            info_layout.addWidget(name_lbl)

            location = doc.get("location", "")
            loc_type = doc.get("type", "")
            if location:
                if loc_type == "link":
                    prefix = "リンク"
                    color = "#3b82f6"
                else:
                    prefix = "パス"
                    color = "#6b7280"
                loc_lbl = _ElidedLabel(f"{prefix}: {location}")
                loc_lbl.setStyleSheet(
                    f"font-size: 12px; color: {color}; border: none;"
                )
                loc_lbl.setTextInteractionFlags(
                    Qt.TextInteractionFlag.TextSelectableByMouse
                )
                info_layout.addWidget(loc_lbl)

            hl.addLayout(info_layout, 1)

            # 削除ボタン
            btn_del = QPushButton("×")
            btn_del.setFixedSize(32, 32)
            btn_del.setCursor(Qt.CursorShape.PointingHandCursor)
            btn_del.setStyleSheet(
                "QPushButton { background: #ef4444; color: #ffffff; "
                "border: none; border-radius: 16px; "
                "font-size: 18px; font-weight: bold; "
                "min-height: 0; min-width: 0; padding: 0; margin: 0 8px; }"
                "QPushButton:hover { background: #dc2626; }"
            )
            idx = i
            btn_del.clicked.connect(lambda _=False, j=idx: self._on_remove(j))
            hl.addWidget(btn_del, alignment=Qt.AlignmentFlag.AlignVCenter)

            self._list_layout.addWidget(row)
            self._rows.append(row)

    def _on_add(self) -> None:
        name = self._input_name.text().strip()
        location = self._input_location.text().strip()
        if not name:
            return
        doc: dict[str, str] = {
            "name": name,
            "location": location,
            "type": _classify_location(location) if location else "",
        }
        self._docs.append(doc)
        self._input_name.clear()
        self._input_location.clear()
        self._rebuild()

    def _on_remove(self, idx: int) -> None:
        if 0 <= idx < len(self._docs):
            self._docs.pop(idx)
            self._rebuild()


# ── ステータスブロック ────────────────────────────────────────────────────────

_FRAME_STYLE = (
    "QFrame#status_block { background: #ffffff; border: 1px solid #e5e7eb; "
    "border-radius: 8px; }"
    "QFrame#status_block QWidget { background: #ffffff; }"
)
_TITLE_STYLE = "font-size: 14px; font-weight: 700; color: #1f2937; border: none;"


def _make_separator() -> QWidget:
    """細い水平区切り線を生成する。"""
    sep = QWidget()
    sep.setFixedHeight(1)
    sep.setStyleSheet("background: #e5e7eb;")
    return sep


def _make_status_block(title: str, widgets: list[QWidget]) -> QFrame:
    """ステータス名付きブロックを生成する。"""
    group = QFrame()
    group.setObjectName("status_block")
    group.setStyleSheet(_FRAME_STYLE)
    vl = QVBoxLayout(group)
    vl.setContentsMargins(16, 12, 16, 12)
    vl.setSpacing(12)

    lbl_title = QLabel(title)
    lbl_title.setStyleSheet(_TITLE_STYLE)
    vl.addWidget(lbl_title)

    vl.addWidget(_make_separator())

    if not widgets:
        lbl = QLabel("設定項目なし")
        lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl.setStyleSheet("color: #9ca3af; font-size: 13px; padding: 12px;")
        vl.addWidget(lbl)
    else:
        for w in widgets:
            vl.addWidget(w)

    return group


# ── メインタブ ─────────────────────────────────────────────────────────────

class HgConfigTab(QWidget):
    """タスク設定タブ — 分析項目×ステータス別レイアウト。"""

    def __init__(
        self,
        hg_config_service: HgConfigService,
        holder_groups: list[dict],
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._service = hg_config_service
        self._holder_groups = holder_groups
        self._current_hg_code: str = ""
        self._build_ui()
        self._connect_signals()
        if holder_groups:
            self._combo.setCurrentIndex(0)
            self._on_hg_changed(0)

    def _build_ui(self) -> None:
        outer = QVBoxLayout(self)
        outer.setContentsMargins(16, 16, 16, 16)
        outer.setSpacing(12)

        # ── ヘッダー行: 分析項目選択 + 保存ボタン ─────────────────────────
        header = QHBoxLayout()
        header.setSpacing(12)

        header.addWidget(QLabel("分析項目:"))
        self._combo = QComboBox()
        self._combo.setMinimumWidth(250)
        for hg in self._holder_groups:
            self._combo.addItem(
                hg.get("holder_group_name", ""),
                hg.get("holder_group_code", ""),
            )
        header.addWidget(self._combo)
        header.addStretch()

        self._btn_save = QPushButton("保存")
        self._btn_save.setStyleSheet(
            "background: #3b82f6; color: white; border: none; "
            "border-radius: 6px; padding: 8px 24px; font-weight: 600;"
        )
        header.addWidget(self._btn_save)
        outer.addLayout(header)

        # ── スクロール領域 ────────────────────────────────────────────────
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )
        scroll.setFrameShape(QFrame.Shape.NoFrame)

        content = QWidget()
        self._content_layout = QVBoxLayout(content)
        self._content_layout.setContentsMargins(0, 0, 0, 0)
        self._content_layout.setSpacing(12)

        # ── ステータスごとのブロックを構築 ────────────────────────────────
        self._pre_docs_editor = _DocumentsEditor("分析前ドキュメント")
        self._pre_editor = _ChecklistEditor("分析前チェックリスト")
        self._post_docs_editor = _DocumentsEditor("分析後ドキュメント")
        self._post_editor = _ChecklistEditor("分析後チェックリスト")

        self._verify_editor = _ChecklistEditor("データ確認チェックリスト")

        status_widgets: dict[str, list[QWidget]] = {
            "analysis": [
                self._pre_docs_editor, self._pre_editor,
                self._post_docs_editor, self._post_editor,
            ],
            "result_verification": [self._verify_editor],
        }

        for status_id, status_name in STATUS_DEFS:
            widgets = status_widgets.get(status_id, [])
            block = _make_status_block(status_name, widgets)
            self._content_layout.addWidget(block)

        self._content_layout.addStretch()
        scroll.setWidget(content)
        outer.addWidget(scroll, 1)

    def _connect_signals(self) -> None:
        self._combo.currentIndexChanged.connect(self._on_hg_changed)
        self._btn_save.clicked.connect(self._on_save)

    # ── HG 切替 ───────────────────────────────────────────────────────────

    def _on_hg_changed(self, index: int) -> None:
        hg_code = self._combo.itemData(index) or ""
        self._current_hg_code = hg_code
        if not hg_code:
            return
        cfg = self._service.get_config(hg_code)
        self._pre_docs_editor.set_documents(cfg.get("pre_documents", []))
        self._pre_editor.set_items(cfg.get("pre_checklist", []))
        self._post_docs_editor.set_documents(cfg.get("post_documents", []))
        self._post_editor.set_items(cfg.get("post_checklist", []))
        self._verify_editor.set_items(cfg.get("verify_checklist", []))

    # ── 保存 ──────────────────────────────────────────────────────────────

    def _on_save(self) -> None:
        hg_code = self._current_hg_code
        if not hg_code:
            return
        self._service.save_checklists(
            hg_code,
            pre_checklist=self._pre_editor.get_items(),
            post_checklist=self._post_editor.get_items(),
            verify_checklist=self._verify_editor.get_items(),
        )
        self._service.save_documents(
            hg_code,
            pre_documents=self._pre_docs_editor.get_documents(),
            post_documents=self._post_docs_editor.get_documents(),
        )
        hg_name = self._combo.currentText()
        QMessageBox.information(
            self, "保存完了", f"「{hg_name}」の設定を保存しました。"
        )
