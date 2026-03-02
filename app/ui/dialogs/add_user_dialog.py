"""ユーザー追加/編集ダイアログ。"""
from __future__ import annotations

from PySide6.QtGui import QFont
from PySide6.QtWidgets import QCheckBox, QDialog, QHBoxLayout, QWidget

from app.ui.generated.ui_adduserdialog import Ui_AddUserDialog


class AddUserDialog(QDialog):
    """ユーザー追加ダイアログ。

    edit_data が指定された場合は編集モードとして動作する。
    """

    def __init__(
        self, edit_data: dict | None = None, parent: QWidget | None = None
    ) -> None:
        super().__init__(parent)
        self.ui = Ui_AddUserDialog()
        self.ui.setupUi(self)
        self._edit_mode = edit_data is not None

        # ── 役割チェックボックス行を追加（有効/管理者の前に挿入）──
        self._add_role_checkboxes()

        if self._edit_mode:
            self.setWindowTitle("ユーザー編集")
            self.ui.btn_add.setText("更新")
            self.ui.input_id.setText(edit_data.get("id", ""))
            self.ui.input_name.setText(edit_data.get("name", ""))
            self.ui.input_email.setText(edit_data.get("email", ""))
            self.ui.widget_init_password.setVisible(False)
            self.ui.checkBox_active.setChecked(edit_data.get("is_active", True))
            self.ui.checkBox_admin.setChecked(edit_data.get("is_admin", False))
            self.cb_analyst.setChecked(edit_data.get("is_analyst", False))
            self.cb_reviewer.setChecked(edit_data.get("is_reviewer", False))
            self.cb_anomaly_mail.setChecked(edit_data.get("is_anomaly_mail", False))
        else:
            self.setWindowTitle("ユーザー追加")
            self.cb_analyst.setChecked(True)

        self.ui.btn_add.clicked.connect(self.accept)
        self.ui.btn_cancel.clicked.connect(self.reject)

    def _add_role_checkboxes(self) -> None:
        """分析者/確認者/異常メール受信者のチェックボックス行を追加する。"""
        font = QFont()
        font.setPointSize(10)

        row = QWidget()
        row.setObjectName("widget_roles")
        hl = QHBoxLayout(row)
        hl.setContentsMargins(0, 0, 0, 0)

        self.cb_analyst = QCheckBox("分析者")
        self.cb_analyst.setFont(font)
        hl.addWidget(self.cb_analyst)

        self.cb_reviewer = QCheckBox("確認者")
        self.cb_reviewer.setFont(font)
        hl.addWidget(self.cb_reviewer)

        self.cb_anomaly_mail = QCheckBox("異常メール受信者")
        self.cb_anomaly_mail.setFont(font)
        hl.addWidget(self.cb_anomaly_mail)

        # widget_checkBox (有効/管理者行) の前に挿入
        idx = self.ui.verticalLayout.indexOf(self.ui.widget_checkBox)
        self.ui.verticalLayout.insertWidget(idx, row)

    @property
    def is_edit_mode(self) -> bool:
        return self._edit_mode

    def get_data(self) -> dict:
        """入力データを辞書で返す。"""
        return {
            "id": self.ui.input_id.text().strip(),
            "name": self.ui.input_name.text().strip(),
            "email": self.ui.input_email.text().strip(),
            "password": self.ui.input_init_password.text(),
            "is_active": self.ui.checkBox_active.isChecked(),
            "is_admin": self.ui.checkBox_admin.isChecked(),
            "is_analyst": self.cb_analyst.isChecked(),
            "is_reviewer": self.cb_reviewer.isChecked(),
            "is_anomaly_mail": self.cb_anomaly_mail.isChecked(),
        }
