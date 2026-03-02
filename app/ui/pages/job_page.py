"""ジョブページ — 実装中"""
from PySide6.QtWidgets import QWidget
from .data_page import _build_placeholder


class JobPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        _build_placeholder(self, "ジョブ", "JOB番号の設定・管理（CRUD）")

    def _load_jobs(self) -> None:
        """main.py からページ切替時に呼ばれる（実装中につきスキップ）。"""
        pass
