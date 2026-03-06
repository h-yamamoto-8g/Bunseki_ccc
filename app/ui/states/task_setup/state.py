"""TaskSetupUI — 起票フォームの純粋レイアウト（generated UI 使用）。

ビジネスロジック・task_store・DataLoader の import 禁止。
"""
from __future__ import annotations

from PySide6.QtWidgets import QWidget, QPushButton, QFrame, QLabel, QHBoxLayout
from PySide6.QtCore import Signal, Qt, QSize

from app.ui.generated.ui_statesetup import Ui_PageStateStart
from app.ui.widgets.icon_utils import get_icon


class TaskSetupUI(QWidget):
    """起票フォーム (純粋レイアウト)。

    Signals:
        form_submitted(hg_code, hg_name, job_numbers): 起票/保存ボタン押下
        edit_requested(): 編集ボタン押下
        cancelled(): キャンセル/戻るボタン押下
        next_requested(): 進むボタン押下
    """

    form_submitted = Signal(str, str, list)
    edit_requested = Signal()
    cancelled = Signal()
    next_requested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._job_numbers: list[str] = []
        self._hg_list: list[dict] = []
        # True のとき btn_create は「編集」として動作する
        self._edit_btn_active = False

        self._form = Ui_PageStateStart()
        self._form.setupUi(self)

        # 「進む」ボタンを btn_create の後ろに追加
        self._btn_next = QPushButton("完了")
        self._btn_next.setMinimumSize(QSize(100, 50))
        self._btn_next.setMaximumSize(QSize(100, 50))
        self._btn_next.setVisible(False)
        action_layout = self._form.widget_action.layout()
        # btn_create の直後（右スペーサーの前）に挿入
        idx = action_layout.indexOf(self._form.btn_create)
        action_layout.insertWidget(idx + 1, self._btn_next)

        # 生成ウィジェットとシグナルを接続
        self._form.btn_job_number_add.clicked.connect(self._add_job)
        self._form.btn_cancel.clicked.connect(self.cancelled)
        self._btn_next.clicked.connect(self.next_requested)
        # btn_create を「起票 / 保存 / 編集」共用ボタンとして使う
        self._form.btn_create.clicked.connect(self._on_primary_btn)

        # 「次へ →」ボタンを動的に追加（起票完了後のナビゲーション用）
        self._btn_next = QPushButton("完了")
        self._btn_next.setMinimumSize(QSize(100, 50))
        self._btn_next.setMaximumSize(QSize(100, 50))
        self._btn_next.setVisible(False)
        self._btn_next.clicked.connect(self.next_requested)
        self._form.horizontalLayout_5.insertWidget(
            self._form.horizontalLayout_5.indexOf(self._form.btn_create) + 1,
            self._btn_next,
        )

    # ── Public API ────────────────────────────────────────────────────────────

    def set_holder_groups(self, hg_list: list[dict]) -> None:
        self._hg_list = hg_list
        self._form.comboBox_holder_groups.clear()
        for g in hg_list:
            self._form.comboBox_holder_groups.addItem(
                g["holder_group_name"], g["holder_group_code"]
            )
        # placeholderText により currentIndex が -1 になるため先頭を選択
        if hg_list:
            self._form.comboBox_holder_groups.setCurrentIndex(0)

    def set_task_data(self, hg_code: str, job_numbers: list[str]) -> None:
        for i in range(self._form.comboBox_holder_groups.count()):
            if self._form.comboBox_holder_groups.itemData(i) == hg_code:
                self._form.comboBox_holder_groups.setCurrentIndex(i)
                break
        self._job_numbers = list(job_numbers)
        self._form.input_job_number.clear()
        self._refresh_tags()

    def set_readonly(self, readonly: bool) -> None:
        self._set_editable(not readonly)

    def show_new_mode(self) -> None:
        self._job_numbers = []
        self._edit_btn_active = False
        self._form.btn_create.setVisible(True)
        self._form.btn_create.setText("起票")
        self._form.btn_cancel.setVisible(True)
        self._form.btn_cancel.setText("キャンセル")
        self._btn_next.setVisible(False)
        self._form.input_job_number.clear()
        self._set_editable(True)  # 内部で _refresh_tags() を呼ぶため重複呼び出し不要

    def show_existing_mode(self, readonly: bool) -> None:
        if readonly:
            self._edit_btn_active = False
            self._set_editable(False)
            self._form.btn_create.setVisible(False)
            self._form.btn_cancel.setText("閉じる")
            self._btn_next.setVisible(False)
        else:
            self._edit_btn_active = True
            self._set_editable(False)
            self._form.btn_create.setVisible(True)
            self._form.btn_create.setText("編集")
            self._form.btn_cancel.setText("戻る")
            self._btn_next.setVisible(True)

    def show_edit_mode(self) -> None:
        self._edit_btn_active = False
        self._set_editable(True)
        self._form.btn_create.setText("保存")
        self._form.btn_create.setVisible(True)
        self._form.btn_cancel.setText("キャンセル")
        self._btn_next.setVisible(False)

    # ── Internal ──────────────────────────────────────────────────────────────

    def _on_primary_btn(self) -> None:
        """btn_create クリック — モードに応じて「起票/保存」または「編集」として動作。"""
        if self._edit_btn_active:
            self.edit_requested.emit()
        else:
            self._submit()

    def _set_editable(self, editable: bool) -> None:
        self._form.comboBox_holder_groups.setEnabled(editable)
        self._form.input_job_number.setEnabled(editable)
        self._form.btn_job_number_add.setEnabled(editable)
        self._refresh_tags()

    def _add_job(self) -> None:
        txt = self._form.input_job_number.text().strip()
        if txt and txt not in self._job_numbers:
            self._job_numbers.append(txt)
            self._form.input_job_number.clear()
            self._refresh_tags()

    def _refresh_tags(self) -> None:
        layout = self._form.scroll_job_numbers_contents.layout()
        while layout.count():
            item = layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        editable = self._form.comboBox_holder_groups.isEnabled()
        for job in self._job_numbers:
            layout.addWidget(self._make_tag(job, editable))
        layout.addStretch()

    def _make_tag(self, text: str, removable: bool) -> QFrame:
        frame = QFrame()
        frame.setObjectName("JobTag")
        frame.setStyleSheet(
            "QFrame#JobTag {"
            " background: rgba(59,130,246,0.10);"
            " border: 1px solid rgba(59,130,246,0.25);"
            " border-radius: 4px;"
            "}"
        )
        hl = QHBoxLayout(frame)
        hl.setContentsMargins(8, 3, 4 if removable else 8, 3)
        hl.setSpacing(4)

        lbl = QLabel(text)
        lbl.setStyleSheet(
            "color: #3b82f6; font-size: 12px; font-weight: 500;"
            " background: transparent; border: none;"
        )
        hl.addWidget(lbl)

        if removable:
            rm = QPushButton()
            rm.setIcon(get_icon(":/icons/cancel.svg", "#6b7280", 12))
            rm.setIconSize(QSize(12, 12))
            rm.setFixedSize(18, 18)
            rm.setCursor(Qt.CursorShape.PointingHandCursor)
            rm.setToolTip(f"「{text}」を削除")
            rm.setStyleSheet(
                "QPushButton { background: transparent; border: none;"
                " padding: 0; min-height: 0; min-width: 0; border-radius: 3px; }"
                "QPushButton:hover { background: rgba(239,68,68,0.12); }"
            )
            rm.clicked.connect(lambda _=False, t=text: self._remove_job(t))
            hl.addWidget(rm)

        return frame

    def _remove_job(self, text: str) -> None:
        if text in self._job_numbers:
            self._job_numbers.remove(text)
            self._refresh_tags()

    def _submit(self) -> None:
        from PySide6.QtWidgets import QMessageBox
        idx = self._form.comboBox_holder_groups.currentIndex()
        if idx < 0:
            QMessageBox.warning(self, "入力エラー", "ホルダグループを選択してください。")
            return
        hg_code = self._form.comboBox_holder_groups.itemData(idx)
        hg_name = self._form.comboBox_holder_groups.currentText()
        if not hg_code:
            QMessageBox.warning(self, "入力エラー", "ホルダグループを選択してください。")
            return
        self.form_submitted.emit(hg_code, hg_name, list(self._job_numbers))
