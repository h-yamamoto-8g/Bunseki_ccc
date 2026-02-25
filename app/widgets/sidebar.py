from PySide6.QtWidgets import QWidget, QVBoxLayout, QPushButton, QLabel
from PySide6.QtCore import Signal, Qt
from app.config import SIDEBAR_PAGES, APP_VERSION


class Sidebar(QWidget):
    page_changed = Signal(str)

    def __init__(self):
        super().__init__()
        self.setFixedWidth(172)
        self.setObjectName("Sidebar")
        self.setStyleSheet("""
            QWidget#Sidebar {
                background-color: #1e293b;
                border-right: 1px solid #334155;
            }
        """)
        self._buttons: dict[str, QPushButton] = {}
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        title = QLabel(f"Bunseki v{APP_VERSION}")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("""
            color: #f1f5f9;
            font-size: 15px;
            font-weight: bold;
            padding: 18px 8px 14px 8px;
            border-bottom: 1px solid #334155;
        """)
        layout.addWidget(title)

        for page_id, icon, name in SIDEBAR_PAGES:
            btn = QPushButton(f" {icon}  {name}")
            btn.setFixedHeight(46)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setStyleSheet(self._style(False))
            btn.clicked.connect(lambda _=False, pid=page_id: self._click(pid))
            layout.addWidget(btn)
            self._buttons[page_id] = btn

        layout.addStretch()
        self.set_active("home")

    def _style(self, active: bool) -> str:
        if active:
            return """
                QPushButton {
                    background-color: #2563eb;
                    color: #ffffff;
                    border: none;
                    text-align: left;
                    padding-left: 18px;
                    font-size: 13px;
                }
            """
        return """
            QPushButton {
                background-color: transparent;
                color: #94a3b8;
                border: none;
                text-align: left;
                padding-left: 18px;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #334155;
                color: #f1f5f9;
            }
        """

    def _click(self, page_id: str):
        self.set_active(page_id)
        self.page_changed.emit(page_id)

    def set_active(self, page_id: str):
        for pid, btn in self._buttons.items():
            btn.setStyleSheet(self._style(pid == page_id))
