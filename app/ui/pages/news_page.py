"""ニュースページ — 実装中"""
from PySide6.QtWidgets import QWidget
from .data_page import _build_placeholder


class NewsPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        _build_placeholder(self, "ニュース", "業務連絡・重要通知の掲示板")
