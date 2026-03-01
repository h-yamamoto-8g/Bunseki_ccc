from pathlib import Path
from PySide6.QtWidgets import QWidget, QVBoxLayout, QPushButton, QLabel
from PySide6.QtCore import Signal, Qt, QByteArray
from PySide6.QtGui import QPixmap, QPainter, QColor
from PySide6.QtSvg import QSvgRenderer

from app.config import SIDEBAR_PAGES, APP_VERSION

# ── Design tokens ─────────────────────────────────────────────────────────────
_BG         = "#161b27"
_BORDER     = "#2a3349"
_TEXT3      = "#5a6278"
_ACCENT     = "#4a8cff"
_BG4        = "#252d3e"
_ACCENT_GL  = "rgba(74,140,255,0.15)"

# assets ディレクトリ
_ASSETS = Path(__file__).parent.parent.parent / "assets"

# ページIDごとのSVGファイル名
_ICON_FILES: dict[str, str] = {
    "home":     "home.svg",
    "tasks":    "task.svg",
    "data":     "data.svg",
    "news":     "news.svg",
    "library":  "library.svg",
    "log":      "logs.svg",
    "job":      "job-number.svg",
    "settings": "setting.svg",
}


def _load_svg_pixmap(svg_path: Path, color: str, size: int = 20) -> QPixmap:
    """SVGファイルを読み込み、fill色を置換してQPixmapに変換する"""
    if not svg_path.exists():
        return QPixmap()
    content = svg_path.read_text(encoding="utf-8")
    # パスのfill色を指定色に置換
    content = content.replace('fill="#333333"', f'fill="{color}"')
    content = content.replace("fill='#333333'", f"fill='{color}'")
    data = QByteArray(content.encode("utf-8"))
    renderer = QSvgRenderer(data)
    pixmap = QPixmap(size, size)
    pixmap.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pixmap)
    renderer.render(painter)
    painter.end()
    return pixmap


class _NavButton(QPushButton):
    """SVGアイコン + ラベルの縦並びナビボタン"""

    def __init__(self, page_id: str, label: str, parent=None):
        super().__init__(parent)
        self._page_id = page_id
        self._label_text = label
        self._svg_path = _ASSETS / _ICON_FILES.get(page_id, "home.svg")
        self.setFixedSize(44, 52)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setToolTip(label)

        # レイアウト（アイコン + ラベル）
        from PySide6.QtWidgets import QVBoxLayout, QLabel
        vl = QVBoxLayout(self)
        vl.setContentsMargins(0, 6, 0, 4)
        vl.setSpacing(3)
        vl.setAlignment(Qt.AlignmentFlag.AlignHCenter)

        self._icon_lbl = QLabel()
        self._icon_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._icon_lbl.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        vl.addWidget(self._icon_lbl)

        self._text_lbl = QLabel(label)
        self._text_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._text_lbl.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        vl.addWidget(self._text_lbl)

        self.activate(False)

    def activate(self, active: bool):
        color = _ACCENT if active else _TEXT3
        bg    = _ACCENT_GL if active else "transparent"
        font_w = "600" if active else "500"
        self.setStyleSheet(f"""
            QPushButton {{
                background: {bg};
                border: none;
                border-radius: 8px;
            }}
            QPushButton:hover {{
                background: {_BG4 if not active else _ACCENT_GL};
            }}
        """)
        px = _load_svg_pixmap(self._svg_path, color, 20)
        self._icon_lbl.setPixmap(px)
        self._text_lbl.setStyleSheet(
            f"font-size:9px; font-weight:{font_w}; color:{color}; letter-spacing:0.3px;"
        )


class Sidebar(QWidget):
    page_changed = Signal(str)

    def __init__(self):
        super().__init__()
        self.setFixedWidth(64)
        self.setObjectName("Sidebar")
        self.setStyleSheet(f"""
            QWidget#Sidebar {{
                background-color: {_BG};
                border-right: 1px solid {_BORDER};
            }}
        """)
        self._buttons: dict[str, _NavButton] = {}
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 12, 10, 12)
        layout.setSpacing(2)
        layout.setAlignment(Qt.AlignmentFlag.AlignHCenter)

        # アプリロゴバッジ
        logo_px = _load_svg_pixmap(_ASSETS / "app-logo.svg", "white", 22)
        logo = QLabel()
        logo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        logo.setFixedSize(36, 36)
        if not logo_px.isNull():
            logo.setPixmap(logo_px)
        else:
            logo.setText("B")
        logo.setStyleSheet(f"""
            QLabel {{
                background: {_ACCENT};
                border-radius: 10px;
                color: white;
                font-size: 16px;
                font-weight: 700;
            }}
        """)
        layout.addWidget(logo, alignment=Qt.AlignmentFlag.AlignHCenter)
        layout.addSpacing(12)

        for page_id, _icon, name in SIDEBAR_PAGES:
            btn = _NavButton(page_id, name)
            btn.clicked.connect(lambda _=False, pid=page_id: self._click(pid))
            layout.addWidget(btn, alignment=Qt.AlignmentFlag.AlignHCenter)
            self._buttons[page_id] = btn

        layout.addStretch()

        # ユーザーアバター
        user_lbl = QLabel("山")
        user_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        user_lbl.setFixedSize(32, 32)
        user_lbl.setStyleSheet("""
            QLabel {
                background: qlineargradient(x1:0,y1:0,x2:1,y2:1,
                    stop:0 #4a8cff, stop:1 #2d63cc);
                color: white;
                font-size: 12px;
                font-weight: 600;
                border-radius: 16px;
            }
        """)
        layout.addWidget(user_lbl, alignment=Qt.AlignmentFlag.AlignHCenter)

        self.set_active("home")

    def _click(self, page_id: str):
        self.set_active(page_id)
        self.page_changed.emit(page_id)

    def set_active(self, page_id: str):
        for pid, btn in self._buttons.items():
            btn.activate(pid == page_id)
