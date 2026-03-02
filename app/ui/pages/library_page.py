"""ライブラリページ — 実装中"""
from PySide6.QtWidgets import QWidget
from .data_page import _build_placeholder


class LibraryPage(QWidget):
    def __init__(self, task_service=None, parent=None):
        super().__init__(parent)
        _build_placeholder(self, "ライブラリ", "回覧時の添付資料を一覧で管理・閲覧")
