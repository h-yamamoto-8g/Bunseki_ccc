"""ログインダイアログ。"""
from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QDialog, QWidget

from app.services.user_service import UserService
from app.ui.generated.ui_logonnormaldialog import Ui_LogonNormalDialog


class LogonDialog(QDialog):
    """ユーザーID・パスワードで認証するログインダイアログ。

    認証成功時に accept() し、authenticated_user() でユーザー情報を取得できる。
    """

    def __init__(
        self, user_service: UserService, parent: QWidget | None = None
    ) -> None:
        super().__init__(parent)
        self.user_service = user_service
        self._user: dict | None = None

        self.ui = Ui_LogonNormalDialog()
        self.ui.setupUi(self)

        self.setWindowFlags(
            self.windowFlags()
            & ~Qt.WindowType.WindowContextHelpButtonHint
            | Qt.WindowType.WindowStaysOnTopHint
        )

        self.ui.btn_logon.clicked.connect(self._on_logon)
        self.ui.btn_cancel.clicked.connect(self.reject)

    def _on_logon(self) -> None:
        """ログオンボタン押下時の処理。"""
        user_id = self.ui.input_id.text()
        password = self.ui.input_password.text()

        result = self.user_service.authenticate(user_id, password)
        if isinstance(result, str):
            # エラーメッセージ
            self.ui.label_message.setText(result)
            self.ui.label_message.setStyleSheet("color: red;")
            self.ui.input_password.clear()
            self.ui.input_password.setFocus()
            return

        # 認証成功
        self._user = result
        self.accept()

    def authenticated_user(self) -> dict | None:
        """認証に成功したユーザー辞書を返す。未認証なら None。"""
        return self._user
