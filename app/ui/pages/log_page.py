"""ログページ — 実装中"""
from PySide6.QtWidgets import QWidget
from .data_page import _build_placeholder


class LogPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        _build_placeholder(self, "ログ", "分析装置・試薬の使用ログ記録")
