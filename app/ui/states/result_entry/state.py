"""ResultEntryUI — データ入力ステートの純粋レイアウト（generated UI 使用）。"""
from __future__ import annotations

from PySide6.QtWidgets import QWidget, QVBoxLayout
from PySide6.QtCore import Signal

from app.ui.generated.ui_stateentry import Ui_PageStateEntry


class ResultEntryUI(QWidget):
    """データ入力ステート (純粋レイアウト)。

    Signals:
        done_requested(): 入力完了ボタン押下
        back_requested(): 戻る
        labaid_requested(): Lab-Aid 起動ボタン押下
    """

    done_requested = Signal()
    back_requested = Signal()
    labaid_requested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._form = Ui_PageStateEntry()
        self._form.setupUi(self)

        self._form.btn_labaid.clicked.connect(self.labaid_requested)
        self._form.btn_back.clicked.connect(self.back_requested)
        self._form.btn_next.clicked.connect(self.done_requested)

    def set_readonly(self, readonly: bool) -> None:
        self._form.btn_next.setVisible(not readonly)
        self._form.btn_back.setVisible(not readonly)
        self._form.btn_labaid.setVisible(not readonly)
