import sys
from pathlib import Path
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

        # Main content area (no QStackedWidget — manual show/hide for simplicity)
        self.home_page = HomePage(self.data_loader)
        self.tasks_page = TasksPage(self.data_loader)
        self.placeholder = self._placeholder_page()

        # Wrap pages in a container
        self.content = QWidget()
        content_layout = QHBoxLayout(self.content)
        content_layout.setContentsMargins(0, 0, 0, 0)

        # Use a simple stacked approach
        from PySide6.QtWidgets import QStackedWidget
        self.stack = QStackedWidget()
        self.stack.addWidget(self.home_page)   # 0
        self.stack.addWidget(self.tasks_page)  # 1
        self.stack.addWidget(self.placeholder) # 2  (other pages)
        content_layout.addWidget(self.stack)
        layout.addWidget(self.content)

        # Status bar
        self.status_bar = QStatusBar()
        self.status_bar.showMessage("準備完了")
        self.setStatusBar(self.status_bar)
        user_lbl = QLabel(f"  ログオン: {CURRENT_USER}  ")
        user_lbl.setStyleSheet("color:#374151; font-size:12px;")
        self.status_bar.addPermanentWidget(user_lbl)

        # Signals
        self.home_page.navigate_to_new_task.connect(self._open_new_task)
        self.home_page.navigate_to_task.connect(self._open_task)
        self.tasks_page.navigate_home.connect(self._go_home)

        # Show home
        self.stack.setCurrentIndex(0)
        self.home_page.refresh()

    def _placeholder_page(self) -> QWidget:
        w = QWidget()
        layout = QHBoxLayout(w)
        lbl = QLabel("このページはデモ対象外です")
        lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl.setStyleSheet("color:#94a3b8; font-size:18px;")
        layout.addWidget(lbl)
        return w

    def _on_page_change(self, page_id: str):
        if page_id == "home":
            self.stack.setCurrentIndex(0)
            self.home_page.refresh()
        elif page_id == "tasks":
            self.stack.setCurrentIndex(1)
            self.tasks_page.show_list()
        else:
            self.stack.setCurrentIndex(2)

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

    # Global stylesheet
    app.setStyleSheet("""
        QWidget {
            font-family: "Helvetica Neue", "Yu Gothic UI", "Noto Sans JP", sans-serif;
            color: #1e293b;
        }
        QMainWindow { background: #f8fafc; }

        /* ── Table ── */
        QTableWidget {
            background: white;
            color: #1e293b;
            gridline-color: #f1f5f9;
        }
        QTableWidget::item {
            color: #1e293b;
            background: white;
            padding: 2px 4px;
        }
        QTableWidget::item:alternate {
            background: #f8fafc;
            color: #1e293b;
        }
        QTableWidget::item:selected {
            background: #2563eb;
            color: white;
        }
        QHeaderView::section {
            color: #374151;
            background: #f8fafc;
        }

        /* ── ComboBox ── */
        QComboBox {
            color: #1e293b;
            background: white;
        }
        QComboBox QAbstractItemView {
            color: #1e293b;
            background: white;
            selection-background-color: #2563eb;
            selection-color: white;
            outline: none;
        }

        /* ── LineEdit / TextEdit ── */
        QLineEdit  { color: #1e293b; background: white; }
        QTextEdit  { color: #1e293b; background: white; }

        /* ── TabBar ── */
        QTabBar::tab          { color: #6b7280; padding: 8px 16px; font-size: 13px; }
        QTabBar::tab:selected { color: #2563eb; }
        QTabWidget::pane      { border: 1px solid #e2e8f0; }

        /* ── CheckBox ── */
        QCheckBox { color: #374151; }

        /* ── Labels in dialogs ── */
        QLabel { color: #1e293b; }

        /* ── MessageBox ── */
        QMessageBox QLabel { color: #1e293b; }

        /* ── ScrollBar ── */
        QScrollArea { border: none; }
        QScrollBar:vertical {
            width: 8px; background: #f1f5f9; border-radius: 4px;
        }
        QScrollBar::handle:vertical { background: #cbd5e1; border-radius: 4px; }
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
    """)

    window = MainWindow()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
