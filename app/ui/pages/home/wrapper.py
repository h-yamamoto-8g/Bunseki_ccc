"""HomePage — ホームページのUIラッパー。"""
from __future__ import annotations

from PySide6.QtWidgets import QWidget, QVBoxLayout
from PySide6.QtCore import Signal

import app.config as _cfg
from app.services.task_service import TaskService
from .page import HomePageUI


class HomePage(QWidget):
    navigate_to_new_task = Signal()
    navigate_to_task = Signal(str)
    navigate_to_news = Signal(str)

    def __init__(self, task_service: TaskService, parent=None) -> None:
        super().__init__(parent)
        self._task_service = task_service

        self._ui = HomePageUI()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self._ui)

        self._ui.navigate_to_new_task.connect(self.navigate_to_new_task)
        self._ui.navigate_to_task.connect(self.navigate_to_task)
        self._ui.navigate_to_news.connect(self.navigate_to_news)

    def refresh(self) -> None:
        tasks = self._task_service.get_all_tasks()
        active = [t for t in tasks if t.get("status") != "終了"]

        my_tasks    = [t for t in active if t.get("assigned_to") == _cfg.CURRENT_USER]
        other_tasks = [t for t in active if t.get("assigned_to") != _cfg.CURRENT_USER]

        self._ui.set_my_tasks(my_tasks)
        self._ui.set_other_tasks(other_tasks)
        self._ui.set_stats(self._task_service.get_task_stats(tasks))
        self._ui.refresh_news()
        self._ui.warn_banner.setVisible(False)
