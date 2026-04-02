"""アプリケーション全体のグローバル QSS (ライトテーマ)。

使い方:
    from app.ui.styles import GLOBAL_QSS
    app.setStyleSheet(GLOBAL_QSS)
"""

GLOBAL_QSS = """
/* ── ベース ── */
QWidget {
    font-family: "Yu Gothic UI", "Hiragino Sans", "Noto Sans JP", sans-serif;
    font-size: 13px;
    color: #333333;
}
QMainWindow { background: #f5f7fa; }

/* ── サイドバー ── */
QWidget#frame_sidebar {
    background: #ffffff;
    border-right: none;
}

/* ── メインエリア ── */
QWidget#widget_main {
    background: #f5f7fa;
}
QStackedWidget#stack_pages {
    background: #f5f7fa;
}

/* ── ヘッダー ── */
QWidget#widget_header {
    background: #ffffff;
    border-bottom: 1px solid #e5e7eb;
}
QToolButton#btn_active_page {
    color: #333333;
    font-size: 14px;
    font-weight: 600;
    background: transparent;
    border: none;
}
QToolButton#btn_active_page:hover { color: #3b82f6; }
QLabel#label_active_tasks_name {
    color: #6b7280;
    font-size: 13px;
}
QToolButton#btn_add_task {
    background: #3b82f6;
    color: white;
    border: none;
    border-radius: 6px;
    padding: 4px 12px;
    font-size: 13px;
    font-weight: 600;
}
QToolButton#btn_add_task:hover { background: #2563eb; }

/* ── ステータスバー ── */
QWidget#widget_statusbar {
    background: #f9fafb;
    border-top: 1px solid #e5e7eb;
}
QLabel#label_status { color: #6b7280; font-size: 11px; }
QLabel#label_user   { color: #9ca3af; font-size: 11px; }

/* ── ステップナビ ── */
QWidget#widget_step {
    background: #ffffff;
    border-bottom: 1px solid #e5e7eb;
}

/* ── ページスタック ── */

/* ── テーブル ── */
QTableWidget, QTableView {
    background: #ffffff;
    color: #333333;
    gridline-color: #e5e7eb;
    border: 1px solid #e5e7eb;
    border-radius: 8px;
}
QTableWidget::item, QTableView::item {
    color: #333333;
    background: transparent;
    padding: 4px 8px;
    border: none;
}
QTableWidget::item:alternate, QTableView::item:alternate {
    background: #f9fafb;
}
QTableWidget::item:selected, QTableView::item:selected {
    background: #dbeafe;
    color: #1e293b;
}
QHeaderView::section {
    color: #6b7280;
    background: #f9fafb;
    border: none;
    border-bottom: 1px solid #e5e7eb;
    padding: 8px 12px;
    font-size: 11px;
    font-weight: bold;
}

/* ── コンボボックス ── */
QComboBox {
    color: #333333;
    background: #ffffff;
    border: 1px solid #d1d5db;
    border-radius: 6px;
    padding: 5px 10px;
    min-height: 32px;
}
QComboBox:hover  { border-color: #9ca3af; }
QComboBox:focus  { border-color: #3b82f6; }
QComboBox:disabled { color: #9ca3af; background: #f3f4f6; }
QComboBox::drop-down { border: none; }
QComboBox QAbstractItemView {
    color: #333333;
    background: #ffffff;
    selection-background-color: #3b82f6;
    selection-color: white;
    outline: none;
    border: 1px solid #e5e7eb;
}

/* ── LineEdit / TextEdit ── */
QLineEdit {
    color: #333333;
    background: #ffffff;
    border: 1px solid #d1d5db;
    border-radius: 6px;
    padding: 5px 10px;
    min-height: 32px;
}
QLineEdit:hover  { border-color: #9ca3af; }
QLineEdit:focus  { border-color: #3b82f6; }
QLineEdit:disabled { color: #9ca3af; background: #f3f4f6; }
QTextEdit {
    color: #333333;
    background: #ffffff;
    border: 1px solid #d1d5db;
    border-radius: 6px;
    padding: 5px 10px;
}
QTextEdit:focus { border-color: #3b82f6; }
QPlainTextEdit {
    color: #333333;
    background: #ffffff;
    border: 1px solid #d1d5db;
    border-radius: 6px;
    padding: 5px 10px;
}
QPlainTextEdit:focus { border-color: #3b82f6; }

/* ── チェックボックス ── */
QCheckBox { color: #333333; spacing: 8px; }
QCheckBox::indicator {
    width: 16px; height: 16px;
    border: 1px solid #d1d5db;
    border-radius: 3px;
    background: #ffffff;
}
QCheckBox::indicator:checked {
    background: #3b82f6;
    border-color: #3b82f6;
}
QCheckBox:disabled { color: #9ca3af; }

/* ── プッシュボタン ── */
QPushButton {
    color: #333333;
    background: #ffffff;
    border: 1px solid #d1d5db;
    border-radius: 6px;
    padding: 5px 14px;
    min-height: 32px;
}
QPushButton:hover { border-color: #3b82f6; color: #3b82f6; }
QPushButton:disabled { color: #9ca3af; background: #f3f4f6; border-color: #e5e7eb; }

/* ── ツールボタン ── */
QToolButton {
    background: transparent;
    border: none;
}

/* ── タブバー ── */
QTabBar::tab {
    color: #6b7280;
    background: transparent;
    border: none;
    padding: 8px 16px;
    font-size: 13px;
}
QTabBar::tab:selected {
    color: #3b82f6;
    border-bottom: 2px solid #3b82f6;
}
QTabBar::tab:hover { color: #374151; background: #f3f4f6; }
QTabWidget::pane {
    border: 1px solid #e5e7eb;
    background: #ffffff;
}

/* ── ラベル ── */
QLabel { color: #333333; background: transparent; }

/* ── メッセージボックス / ダイアログ ── */
QMessageBox { background: #ffffff; }
QMessageBox QLabel { color: #333333; }
QDialog { background: #f9fafb; }
QDialogButtonBox QPushButton {
    background: #ffffff;
    color: #333333;
    border: 1px solid #d1d5db;
    border-radius: 6px;
    padding: 6px 16px;
    min-width: 72px;
}
QDialogButtonBox QPushButton:hover { border-color: #3b82f6; color: #3b82f6; }

/* ── グループボックス ── */
QGroupBox {
    color: #6b7280;
    border: 1px solid #e5e7eb;
    border-radius: 8px;
    margin-top: 12px;
    padding-top: 16px;
    font-size: 11px;
    font-weight: bold;
    background: #ffffff;
}
QGroupBox::title {
    subcontrol-origin: margin;
    left: 12px; top: -6px;
    color: #6b7280;
    background: #ffffff;
    padding: 0 4px;
}

/* ── スクロールバー ── */
QScrollArea  { border: none; background: transparent; }
QScrollBar:vertical {
    width: 6px; background: transparent;
}
QScrollBar::handle:vertical {
    background: #d1d5db; border-radius: 3px; min-height: 20px;
}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
QScrollBar:horizontal {
    height: 6px; background: transparent;
}
QScrollBar::handle:horizontal {
    background: #d1d5db; border-radius: 3px;
}
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal { width: 0; }

/* ── スプリッター ── */
QSplitter::handle { background: #e5e7eb; }

/* ── カレンダー ── */
QCalendarWidget QWidget { background: #ffffff; }
QCalendarWidget QToolButton {
    color: #333333; background: #ffffff;
    border: none; padding: 4px 8px;
}
QCalendarWidget QToolButton:hover { background: #f3f4f6; }
QCalendarWidget QMenu { color: #333333; background: #ffffff; }
QCalendarWidget QSpinBox { color: #333333; background: #ffffff; border: none; }
QCalendarWidget QAbstractItemView:enabled { background: #ffffff; }
QCalendarWidget QAbstractItemView:disabled { color: #9ca3af; }
QCalendarWidget QAbstractItemView:selected { background: #3b82f6; color: white; }

/* ── フレーム（カード） ── */
QFrame { color: #333333; }
"""
