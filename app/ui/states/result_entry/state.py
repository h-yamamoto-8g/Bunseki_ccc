"""ResultEntryUI — データ入力ステートの純粋レイアウト（generated UI 使用）。"""
from __future__ import annotations

from PySide6.QtWidgets import QWidget, QVBoxLayout, QPushButton
from PySide6.QtCore import Signal

from app.ui.generated.ui_stateentry import Ui_PageStateEntry
from app.ui.widgets.icon_utils import get_icon


class ResultEntryUI(QWidget):
    """データ入力ステート (純粋レイアウト)。

    Signals:
        done_requested(): 入力完了ボタン押下
        back_requested(): 戻る
        labaid_requested(): Lab-Aid 起動ボタン押下
        data_update_requested(): データ更新ボタン押下
    """

    done_requested = Signal()
    back_requested = Signal()
    labaid_requested = Signal()
    data_update_requested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._form = Ui_PageStateEntry()
        self._form.setupUi(self)

        # ── グローバル QSS でリセットされるデフォルト spacing を明示設定 ──
        self._form.verticalLayout_2.setSpacing(8)
        self._form.verticalLayout_2.setContentsMargins(8, 8, 8, 8)

        # ── データ更新ボタンをアクションバー左端に追加 ──────────────────────
        self._btn_data_update = QPushButton("データ更新")
        self._btn_data_update.setIcon(get_icon(":/icons/data.svg", "#3b82f6"))
        self._btn_data_update.setMinimumWidth(120)
        self._btn_data_update.setToolTip("データの更新と正規化を実行します")
        self._btn_data_update.clicked.connect(self.data_update_requested)
        # スペーサーの前（左端）に挿入
        self._form.horizontalLayout_5.insertWidget(0, self._btn_data_update)

        self._form.btn_labaid.clicked.connect(self.labaid_requested)
        self._form.btn_back.setVisible(False)
        self._form.btn_next.setText("完了")
        self._form.btn_next.clicked.connect(self.done_requested)

    def set_readonly(self, readonly: bool) -> None:
        self._form.btn_next.setVisible(not readonly)
        self._form.btn_labaid.setVisible(not readonly)
        self._btn_data_update.setVisible(not readonly)
