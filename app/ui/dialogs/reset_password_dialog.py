"""パスワードリセットダイアログ。"""
from __future__ import annotations

from PySide6.QtWidgets import QDialog, QMessageBox, QWidget

from app.ui.generated.ui_resetpassworddialog import Ui_ResetPasswordDialog


class ResetPasswordDialog(QDialog):
    """パスワードリセットダイアログ。"""

    def __init__(self, user_id: str, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.ui = Ui_ResetPasswordDialog()
        self.ui.setupUi(self)
        self.setWindowTitle("パスワード再設定")
        self.ui.label_picup_id.setText(user_id)

        self.ui.btn_update.clicked.connect(self._on_update)
        self.ui.btn_cancel.clicked.connect(self.reject)

    def _on_update(self) -> None:
        pw = self.ui.input_new_password.text()
        confirm = self.ui.input_confirl_password.text()
        if not pw:
            QMessageBox.warning(self, "入力エラー", "新パスワードを入力してください。")
            return
        if pw != confirm:
            QMessageBox.warning(self, "入力エラー", "パスワードが一致しません。")
            return
        self.accept()

    def get_password(self) -> str:
        return self.ui.input_new_password.text()
