"""サイドバーナビゲーションとステップナビゲーションウィジェット。

MainWindow.ui の frame_sidebar / widget_step の仕様に基づく実装。
デザインは docs/CLAUDE.md に従いホワイトベースで統一する。
アイコンは resources/assets/ の SVG を resources_rc 経由で使用する。
"""
from __future__ import annotations

from typing import Optional

import app.ui.generated.resources_rc  # noqa: F401  Qt リソース登録

from PySide6.QtCore import Qt, QSize, Signal
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QSizePolicy,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from PySide6.QtGui import QPainter, QPainterPath, QBrush, QColor as _QColor, QPen

from app.ui.widgets.icon_utils import get_icon

# ─── デザイントークン（ライトテーマ） ──────────────────────────────────────
_BG = "#ffffff"
_BORDER = "#e5e7eb"
_TEXT = "#333333"
_TEXT2 = "#6b7280"
_ACCENT = "#3b82f6"
_ACTIVE_BG = "#eff6ff"
_SUCCESS_BG = "#6ba37a"
_SUCCESS_FG = "#059669"
_MUTED_BG = "#f3f4f6"
_EDITED_BG = "#fef3c7"
_EDITED_FG = "#d97706"
_EDITED_BORDER = "#f59e0b"

_ICON_SIZE = QSize(22, 22)

# ─── ページ情報 ──────────────────────────────────────────────────────────────
# key: page_id, value: (表示名, SVGリソースパス)
PAGE_INFO: dict[str, tuple[str, str]] = {
    "home":     ("ホーム",    ":/icons/home.svg"),
    "tasks":    ("タスク",    ":/icons/task.svg"),
    "data":     ("データ",    ":/icons/data.svg"),
    "news":     ("ニュース",  ":/icons/news.svg"),
    "library":  ("ライブラリ", ":/icons/library.svg"),
    "log":      ("ログ",      ":/icons/logs.svg"),
    "job":      ("ジョブ",    ":/icons/job-number.svg"),
    "settings": ("設定",      ":/icons/setting.svg"),
}

# ─── ステップ定義 ─────────────────────────────────────────────────────────────
# (state_id, SVGリソースパス, ツールチップ)
STEP_DEFS: list[tuple[str, str, str]] = [
    ("task_setup",          ":/icons/start.svg",       "起票"),
    ("analysis_targets",    ":/icons/sample-list.svg", "サンプル"),
    ("analysis",            ":/icons/analysis.svg",    "分析"),
    ("result_entry",        ":/icons/data-input.svg",  "入力"),
    ("result_verification", ":/icons/graph.svg",       "チェック"),
    ("submission",          ":/icons/flow.svg",        "フロー"),
    ("completed",           ":/icons/end.svg",         "終了"),
]


class _NavButton(QToolButton):
    """サイドバーのナビゲーションボタン（SVGアイコン上・テキスト下）。

    Args:
        page_id: ページID。
        label: 表示ラベル。
        svg_path: Qt リソースの SVG パス。
        parent: 親ウィジェット。
    """

    def __init__(
        self,
        page_id: str,
        label: str,
        svg_path: str,
        parent: Optional[QWidget] = None,
    ) -> None:
        super().__init__(parent)
        self._page_id = page_id
        self._label = label
        self._svg_path = svg_path
        self.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextUnderIcon)
        self.setFixedSize(60, 56)
        self.setIconSize(_ICON_SIZE)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setToolTip(label)
        self.setText(label)
        self.set_active(False)

    def set_active(self, active: bool) -> None:
        """アクティブ状態を切り替える。

        Args:
            active: アクティブの場合 True。
        """
        if active:
            self.setIcon(get_icon(self._svg_path, _ACCENT))
            self.setStyleSheet(f"""
                QToolButton {{
                    background: {_ACTIVE_BG};
                    color: {_ACCENT};
                    border: none;
                    border-radius: 8px;
                    font-size: 9px;
                    font-weight: 600;
                    padding: 2px;
                }}
                QToolButton:hover {{ background: #dbeafe; }}
            """)
        else:
            self.setIcon(get_icon(self._svg_path, _TEXT2))
            self.setStyleSheet(f"""
                QToolButton {{
                    background: transparent;
                    color: {_TEXT2};
                    border: none;
                    border-radius: 8px;
                    font-size: 9px;
                    font-weight: 500;
                    padding: 2px;
                }}
                QToolButton:hover {{
                    background: #f3f4f6;
                    color: {_TEXT};
                }}
            """)


class Sidebar(QWidget):
    """アプリケーションサイドバーナビゲーション（75px 幅）。

    MainWindow.ui の frame_sidebar 仕様に準拠。
    左右にスペーサーを配置し、ナビボタンを中央揃えにする。

    Signals:
        page_changed (str): ページが変更された時に page_id を送出する。
    """

    page_changed = Signal(str)
    guide_toggle_requested = Signal()

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setFixedWidth(75)
        self.setObjectName("frame_sidebar")
        self._buttons: dict[str, _NavButton] = {}
        self._setup_ui()

    def _setup_ui(self) -> None:
        """UIを構築する。"""
        vl = QVBoxLayout(self)
        vl.setContentsMargins(0, 10, 0, 10)
        vl.setSpacing(2)

        # サイドコンテンツ開閉ボタン
        self.btn_toggle_guide = QToolButton(self)
        self.btn_toggle_guide.setObjectName("btn_toggle_guide")
        self.btn_toggle_guide.setFixedSize(44, 44)
        self.btn_toggle_guide.setIconSize(QSize(24, 24))
        self.btn_toggle_guide.setIcon(
            get_icon(":/icons/bulging-left.svg", _TEXT2, size=24)
        )
        self.btn_toggle_guide.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_toggle_guide.setToolTip("ガイドパネルの開閉")
        self.btn_toggle_guide.setStyleSheet("""
            QToolButton#btn_toggle_guide {
                background: transparent;
                border: none;
            }
            QToolButton#btn_toggle_guide:hover {
                background: #e5e7eb;
                border-radius: 10px;
            }
        """)
        self.btn_toggle_guide.clicked.connect(
            lambda: self.guide_toggle_requested.emit()
        )
        vl.addWidget(self.btn_toggle_guide, alignment=Qt.AlignmentFlag.AlignHCenter)
        vl.addSpacing(10)

        for page_id, (name, svg_path) in PAGE_INFO.items():
            btn = _NavButton(page_id, name, svg_path, parent=self)
            btn.clicked.connect(
                lambda _checked=False, pid=page_id: self._on_click(pid)
            )
            vl.addWidget(btn, alignment=Qt.AlignmentFlag.AlignHCenter)
            self._buttons[page_id] = btn

        vl.addStretch()

        self.set_active("home")

    def _on_click(self, page_id: str) -> None:
        """ナビボタンのクリック処理。

        Args:
            page_id: クリックされたページID。
        """
        self.set_active(page_id)
        self.page_changed.emit(page_id)

    def set_active(self, page_id: str) -> None:
        """アクティブなページを設定する。

        Args:
            page_id: アクティブにするページID。
        """
        for pid, btn in self._buttons.items():
            btn.set_active(pid == page_id)

    def set_guide_expanded(self, expanded: bool) -> None:
        """開閉状態に合わせてトグルボタンのアイコンを切り替える。"""
        svg = ":/icons/bulging-left.svg" if expanded else ":/icons/bulging-right.svg"
        self.btn_toggle_guide.setIcon(get_icon(svg, _TEXT2, size=24))



class _CircleButton(QToolButton):
    """円形に描画されるステップボタン。

    QSS の border-radius が QWidget のグローバル background-color に
    上書きされる Qt の問題を回避するため、paintEvent で円形背景を自前描画する。
    """

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self._bg_color = _QColor(_MUTED_BG)
        self._border_color: _QColor | None = _QColor(_BORDER)

    def set_circle_style(
        self, bg: str, border: str | None = None
    ) -> None:
        self._bg_color = _QColor(bg)
        self._border_color = _QColor(border) if border else None
        self.update()

    def paintEvent(self, event) -> None:  # noqa: N802
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        rect = self.rect().adjusted(1, 1, -1, -1)
        center = rect.center()
        radius = min(rect.width(), rect.height()) / 2.0

        # 円形背景
        path = QPainterPath()
        path.addEllipse(center.x() - radius, center.y() - radius,
                        radius * 2, radius * 2)
        p.fillPath(path, QBrush(self._bg_color))

        # 円形ボーダー
        if self._border_color:
            p.setPen(QPen(self._border_color, 1))
            p.drawEllipse(center.x() - radius, center.y() - radius,
                          radius * 2, radius * 2)

        # アイコン（中央に描画）
        ico = self.icon()
        if not ico.isNull():
            sz = self.iconSize()
            pm = ico.pixmap(sz)
            x = (self.width() - pm.width()) // 2
            y = (self.height() - pm.height()) // 2
            p.drawPixmap(x, y, pm)

        p.end()
        # super().paintEvent を呼ばない — QToolButton のデフォルト描画が
        # 四角い背景を塗ってしまうのを防ぐ


class StepNavigation(QWidget):
    """タスクのステップナビゲーション（横並び、ヘッダーバー）。

    各ステップは SVG アイコンボタン + HLine コネクタで横に並ぶ。

    Signals:
        step_clicked (str): ステップがクリックされた時に state_id を送出する。
    """

    step_clicked = Signal(str)

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setFixedHeight(50)
        self.setObjectName("widget_step")
        self.setAutoFillBackground(True)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self._step_buttons: dict[str, _CircleButton] = {}
        self._active_step: str = ""
        self._current_state: str = ""  # タスクの実際の進捗ステート
        self._edited_steps: set[str] = set()
        self._step_svg: dict[str, str] = {s[0]: s[1] for s in STEP_DEFS}
        self._setup_ui()

    def _setup_ui(self) -> None:
        """UIを構築する。"""
        hl = QHBoxLayout(self)
        hl.setContentsMargins(20, 4, 20, 4)
        hl.setSpacing(0)
        hl.addStretch()

        for i, (state_id, svg_path, label) in enumerate(STEP_DEFS):
            if i > 0:
                # ステップ間の HLine コネクタ
                line = QFrame()
                line.setFrameShape(QFrame.Shape.HLine)
                line.setFrameShadow(QFrame.Shadow.Plain)
                line.setFixedHeight(2)
                line.setMinimumWidth(18)
                line.setMaximumWidth(40)
                line.setStyleSheet(f"background: {_BORDER}; border: none;")
                hl.addWidget(line, alignment=Qt.AlignmentFlag.AlignVCenter)

            btn = _CircleButton()
            btn.setFixedSize(43, 43)
            btn.setIconSize(QSize(20, 20))
            btn.setToolTip(label)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setObjectName(f"btn_step_{state_id}")
            btn.setStyleSheet(
                "QToolButton { background: transparent; border: none; }"
            )
            btn.clicked.connect(
                lambda _checked=False, sid=state_id: (
                    print(f"[DEBUG] step_clicked: {sid}"),
                    self.step_clicked.emit(sid),
                )
            )
            self._step_buttons[state_id] = btn
            hl.addWidget(btn, alignment=Qt.AlignmentFlag.AlignVCenter)

        hl.addStretch()
        self._update_styles()

    # ─── スタイル更新 ──────────────────────────────────────────────────────

    def _update_styles(self) -> None:
        """全ステップボタンのスタイルを現在状態に合わせて更新する。

        色分けルール:
        - 表示中のステップ (_active_step): 青塗り
        - 編集済み: アンバー塗り
        - タスクの実際の進捗 (_current_state) 以前: 薄緑背景・グレーアイコン（完了済み）
        - _current_state より先: グレー背景（未到達）
        """
        step_ids = [s[0] for s in STEP_DEFS]
        # タスクの実際の進捗位置で完了済み判定する
        progress_idx = (
            step_ids.index(self._current_state)
            if self._current_state in step_ids
            else -1
        )

        for i, (state_id, svg_path, _label) in enumerate(STEP_DEFS):
            btn = self._step_buttons[state_id]
            edited = state_id in self._edited_steps

            if state_id == self._active_step:
                btn.setIcon(get_icon(svg_path, "#ffffff"))
                btn.set_circle_style(_ACCENT)
                btn.setStyleSheet(f"""
                    QToolButton {{
                        background: transparent;
                        border: none;
                        border-radius: 22px;
                    }}
                """)
            elif edited:
                btn.setIcon(get_icon(svg_path, _EDITED_FG))
                btn.set_circle_style(_EDITED_BG, _EDITED_BORDER)
                btn.setStyleSheet(f"""
                    QToolButton {{
                        background: transparent;
                        border: none;
                        border-radius: 22px;
                    }}
                    QToolButton:hover {{
                        background: transparent;
                    }}
                """)
            elif progress_idx >= 0 and i < progress_idx:
                btn.setIcon(get_icon(svg_path, "#ffffff"))
                btn.set_circle_style(_SUCCESS_BG)
                btn.setStyleSheet(f"""
                    QToolButton {{
                        background: transparent;
                        border: none;
                        border-radius: 22px;
                    }}
                """)
            else:
                btn.setIcon(get_icon(svg_path, _TEXT2))
                btn.set_circle_style(_MUTED_BG, _BORDER)
                btn.setStyleSheet(f"""
                    QToolButton {{
                        background: transparent;
                        border: none;
                        border-radius: 22px;
                    }}
                    QToolButton:hover {{
                        background: transparent;
                    }}
                """)

    # ─── 公開 API ──────────────────────────────────────────────────────────

    def set_active_step(
        self, state_id: str, current_state: str = ""
    ) -> None:
        """アクティブなステップを設定する。

        Args:
            state_id: 表示中のステートID。
            current_state: タスクの実際の進捗ステートID。
                           空文字の場合は state_id と同じとみなす。
        """
        self._active_step = state_id
        self._current_state = current_state or state_id
        self._update_styles()

    def clear(self) -> None:
        """アクティブステップをリセットする。"""
        self._active_step = ""
        self._current_state = ""
        self._update_styles()

    def mark_edited(self, state_id: str) -> None:
        """指定ステップを「編集済み」として amber 色でハイライトする。

        Args:
            state_id: 編集済みにするステートID。
        """
        self._edited_steps.add(state_id)
        self._update_styles()

    def clear_edited(self) -> None:
        """全ステップの編集済みマークを解除する。"""
        self._edited_steps.clear()
        self._update_styles()

