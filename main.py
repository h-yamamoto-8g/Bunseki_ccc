import sys
import platform
from pathlib import Path

import matplotlib
matplotlib.use("QtAgg")
# 日本語フォント設定（macOS/Windows 両対応）
if platform.system() == "Darwin":
    matplotlib.rcParams["font.family"] = "Hiragino Sans"
else:
    matplotlib.rcParams["font.family"] = "Yu Gothic"
matplotlib.rcParams["axes.unicode_minus"] = False

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QHBoxLayout,
    QLabel, QStatusBar, QFrame,
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont

from app.config import APP_VERSION, DATA_PATH, CURRENT_USER
from app.data.loader import DataLoader
from app.widgets.sidebar import Sidebar
from app.pages.home_page import HomePage
from app.pages.tasks_page import TasksPage
from app.pages.data_page import DataPage
from app.pages.news_page import NewsPage
from app.pages.library_page import LibraryPage
from app.pages.log_page import LogPage
from app.pages.job_page import JobPage
from app.pages.settings_page import SettingsPage

# QStackedWidget のインデックス
_PAGE_IDX = {
    "home":     0,
    "tasks":    1,
    "data":     2,
    "news":     3,
    "library":  4,
    "log":      5,
    "job":      6,
    "settings": 7,
}


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(f"Bunseki ver.{APP_VERSION}")
        self.setMinimumSize(1280, 800)

        self.data_loader = DataLoader(DATA_PATH)
        self._setup_ui()
        self.showMaximized()

    def _setup_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        layout = QHBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Sidebar
        self.sidebar = Sidebar()
        self.sidebar.page_changed.connect(self._on_page_change)
        layout.addWidget(self.sidebar)

        # Pages
        self.home_page     = HomePage(self.data_loader)
        self.tasks_page    = TasksPage(self.data_loader)
        self.data_page     = DataPage(self.data_loader)
        self.news_page     = NewsPage()
        self.library_page  = LibraryPage()
        self.log_page      = LogPage()
        self.job_page      = JobPage()
        self.settings_page = SettingsPage()

        # Stacked widget
        self.content = QWidget()
        content_layout = QHBoxLayout(self.content)
        content_layout.setContentsMargins(0, 0, 0, 0)

        from PySide6.QtWidgets import QStackedWidget
        self.stack = QStackedWidget()
        self.stack.addWidget(self.home_page)      # 0
        self.stack.addWidget(self.tasks_page)     # 1
        self.stack.addWidget(self.data_page)      # 2
        self.stack.addWidget(self.news_page)      # 3
        self.stack.addWidget(self.library_page)   # 4
        self.stack.addWidget(self.log_page)       # 5
        self.stack.addWidget(self.job_page)       # 6
        self.stack.addWidget(self.settings_page)  # 7
        content_layout.addWidget(self.stack)
        layout.addWidget(self.content)

        # Status bar
        self.status_bar = QStatusBar()
        self.status_bar.showMessage("準備完了")
        self.setStatusBar(self.status_bar)
        user_lbl = QLabel(f"  {CURRENT_USER}  ")
        user_lbl.setStyleSheet(f"color:#5a6278; font-size:11px;")
        self.status_bar.addPermanentWidget(user_lbl)

        # Signals
        self.home_page.navigate_to_new_task.connect(self._open_new_task)
        self.home_page.navigate_to_task.connect(self._open_task)
        self.tasks_page.navigate_home.connect(self._go_home)

        # Show home
        self.stack.setCurrentIndex(0)
        self.home_page.refresh()

    def _on_page_change(self, page_id: str):
        idx = _PAGE_IDX.get(page_id, 0)
        self.stack.setCurrentIndex(idx)
        if page_id == "home":
            self.home_page.refresh()
        elif page_id == "tasks":
            self.tasks_page.show_list()
        elif page_id == "job":
            self.job_page._load_jobs()

    def _open_new_task(self):
        self.sidebar.set_active("tasks")
        self.stack.setCurrentIndex(1)
        self.tasks_page.start_new_task()

    def _open_task(self, task_id: str):
        self.sidebar.set_active("tasks")
        self.stack.setCurrentIndex(1)
        self.tasks_page.resume_task(task_id)

    def _go_home(self):
        self.sidebar.set_active("home")
        self.stack.setCurrentIndex(0)
        self.home_page.refresh()

    def set_status(self, message: str):
        self.status_bar.showMessage(message)


def main():
    app = QApplication(sys.argv)
    app.setFont(QFont("Helvetica Neue", 10))
    app.setStyle("Fusion")

    # Global dark stylesheet (matches bunseki_ui.html)
    app.setStyleSheet("""
        /* ── Base ── */
        QWidget {
            font-family: "Yu Gothic UI", "Noto Sans JP", sans-serif;
            font-size: 13px;
            color: #e8eaf0;
            background-color: #0f1117;
        }
        QMainWindow { background: #0f1117; }

        /* ── Frame / Card ── */
        QFrame {
            color: #e8eaf0;
        }

        /* ── Table ── */
        QTableWidget {
            background: #161b27;
            color: #e8eaf0;
            gridline-color: #2a3349;
            border: 1px solid #2a3349;
            border-radius: 8px;
        }
        QTableWidget::item {
            color: #e8eaf0;
            background: transparent;
            padding: 2px 8px;
            border: none;
        }
        QTableWidget::item:alternate {
            background: #1e2535;
        }
        QTableWidget::item:selected {
            background: #4a8cff;
            color: white;
        }
        QHeaderView::section {
            color: #5a6278;
            background: #161b27;
            border: none;
            border-bottom: 1px solid #2a3349;
            padding: 8px 12px;
            font-size: 11px;
            font-weight: bold;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }

        /* ── ComboBox ── */
        QComboBox {
            color: #e8eaf0;
            background: #1e2535;
            border: 1px solid #2a3349;
            border-radius: 6px;
            padding: 6px 10px;
            min-height: 32px;
        }
        QComboBox:hover  { border-color: #334166; }
        QComboBox:focus  { border-color: #4a8cff; }
        QComboBox:disabled { color: #5a6278; background: #161b27; }
        QComboBox::drop-down { border: none; }
        QComboBox QAbstractItemView {
            color: #e8eaf0;
            background: #1e2535;
            selection-background-color: #4a8cff;
            selection-color: white;
            outline: none;
            border: 1px solid #2a3349;
        }

        /* ── LineEdit / TextEdit ── */
        QLineEdit {
            color: #e8eaf0;
            background: #1e2535;
            border: 1px solid #2a3349;
            border-radius: 6px;
            padding: 6px 10px;
            min-height: 32px;
        }
        QLineEdit:hover  { border-color: #334166; }
        QLineEdit:focus  { border-color: #4a8cff; }
        QLineEdit:disabled { color: #5a6278; background: #161b27; }
        QTextEdit {
            color: #e8eaf0;
            background: #1e2535;
            border: 1px solid #2a3349;
            border-radius: 6px;
            padding: 6px 10px;
        }
        QTextEdit:focus { border-color: #4a8cff; }

        /* ── TabBar ── */
        QTabBar::tab {
            color: #5a6278;
            background: transparent;
            border: none;
            padding: 8px 16px;
            font-size: 13px;
        }
        QTabBar::tab:selected {
            color: #4a8cff;
            border-bottom: 2px solid #4a8cff;
        }
        QTabBar::tab:hover { color: #8b93a8; background: #1e2535; }
        QTabWidget::pane {
            border: 1px solid #2a3349;
            background: #161b27;
        }

        /* ── CheckBox ── */
        QCheckBox { color: #c8cad4; spacing: 8px; }
        QCheckBox::indicator {
            width: 16px; height: 16px;
            border: 1px solid #334166;
            border-radius: 3px;
            background: #1e2535;
        }
        QCheckBox::indicator:checked {
            background: #4a8cff;
            border-color: #4a8cff;
        }
        QCheckBox:disabled { color: #5a6278; }

        /* ── Labels ── */
        QLabel { color: #e8eaf0; background: transparent; }

        /* ── MessageBox / Dialog ── */
        QMessageBox { background: #161b27; }
        QMessageBox QLabel { color: #e8eaf0; }
        QDialog { background: #161b27; }
        QDialogButtonBox QPushButton {
            background: #1e2535; color: #e8eaf0;
            border: 1px solid #334166; border-radius: 6px;
            padding: 6px 16px; min-width: 72px;
        }
        QDialogButtonBox QPushButton:hover { border-color: #4a8cff; color: #4a8cff; }

        /* ── GroupBox ── */
        QGroupBox {
            color: #8b93a8;
            border: 1px solid #2a3349;
            border-radius: 8px;
            margin-top: 12px;
            padding-top: 18px;
            font-size: 11px;
            font-weight: bold;
        }
        QGroupBox::title {
            subcontrol-origin: margin;
            left: 12px; top: -6px;
            color: #8b93a8;
            background: #0f1117;
            padding: 0 4px;
        }

        /* ── ScrollBar ── */
        QScrollArea  { border: none; background: transparent; }
        QScrollBar:vertical {
            width: 6px; background: transparent;
        }
        QScrollBar::handle:vertical {
            background: #334166; border-radius: 3px; min-height: 20px;
        }
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
        QScrollBar:horizontal {
            height: 6px; background: transparent;
        }
        QScrollBar::handle:horizontal {
            background: #334166; border-radius: 3px;
        }
        QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal { width: 0; }

        /* ── Splitter ── */
        QSplitter::handle { background: #2a3349; }

        /* ── StatusBar ── */
        QStatusBar {
            background: #161b27;
            color: #5a6278;
            border-top: 1px solid #2a3349;
            font-size: 11px;
        }

        /* ── Calendar ── */
        QCalendarWidget QWidget { background: #1e2535; color: #e8eaf0; }
        QCalendarWidget QToolButton {
            color: #e8eaf0; background: #1e2535;
            border: none; padding: 4px 8px;
        }
        QCalendarWidget QToolButton:hover { background: #252d3e; }
        QCalendarWidget QMenu { color: #e8eaf0; background: #1e2535; }
        QCalendarWidget QSpinBox { color: #e8eaf0; background: #1e2535; border: none; }
        QCalendarWidget QAbstractItemView:enabled { color: #e8eaf0; background: #1e2535; }
        QCalendarWidget QAbstractItemView:disabled { color: #5a6278; }
        QCalendarWidget QAbstractItemView:selected { background: #4a8cff; color: white; }
    """)

    window = MainWindow()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
