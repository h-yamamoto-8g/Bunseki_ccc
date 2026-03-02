"""ユーザー管理タブ。

Ui_UsersTab を使用し、UserService を通じてユーザーCRUDを行う。
"""
from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QStandardItem, QStandardItemModel
from PySide6.QtWidgets import QMessageBox, QWidget

from app.services.user_service import UserService
from app.ui.dialogs.add_user_dialog import AddUserDialog
from app.ui.dialogs.reset_password_dialog import ResetPasswordDialog
from app.ui.generated.ui_userstab import Ui_UsersTab

_COLUMNS = ["ID", "名前", "メールアドレス", "分析者", "確認者", "異常メール", "有効", "管理者"]


class UsersTab(QWidget):
    """ユーザー管理タブ。"""

    def __init__(self, user_service: UserService, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.user_service = user_service

        self.ui = Ui_UsersTab()
        self.ui.setupUi(self)

        self._model = QStandardItemModel()
        self._model.setHorizontalHeaderLabels(_COLUMNS)
        self.ui.tableView_users.setModel(self._model)
        self.ui.tableView_users.setSelectionBehavior(
            self.ui.tableView_users.SelectionBehavior.SelectRows
        )
        self.ui.tableView_users.setSelectionMode(
            self.ui.tableView_users.SelectionMode.SingleSelection
        )
        self.ui.tableView_users.setEditTriggers(
            self.ui.tableView_users.EditTrigger.NoEditTriggers
        )
        self.ui.tableView_users.setAlternatingRowColors(True)

        self.ui.btn_reload.clicked.connect(self.load_users)
        self.ui.btn_add.clicked.connect(self._on_add)
        self.ui.btn_edit.clicked.connect(self._on_edit)
        self.ui.btn_password_reset.clicked.connect(self._on_reset_password)
        self.ui.btn_active_switch.clicked.connect(self._on_toggle_active)

        self.load_users()

    # ── データ読み込み ────────────────────────────────────────────────────────

    def load_users(self) -> None:
        """ユーザー一覧をテーブルに反映する。"""
        self._model.removeRows(0, self._model.rowCount())
        for u in self.user_service.get_all_users():
            row = [
                QStandardItem(u.get("id", "")),
                QStandardItem(u.get("name", "")),
                QStandardItem(u.get("email", "")),
                self._check_item(u.get("is_analyst", False)),
                self._check_item(u.get("is_reviewer", False)),
                self._check_item(u.get("is_anomaly_mail", False)),
                QStandardItem("有効" if u.get("is_active", True) else "無効"),
                self._check_item(u.get("is_admin", False)),
            ]
            # 有効列の色分け
            if not u.get("is_active", True):
                row[6].setForeground(Qt.GlobalColor.red)
            for item in row:
                item.setEditable(False)
            self._model.appendRow(row)

        self.ui.tableView_users.resizeColumnsToContents()

    # ── 選択中ユーザー取得 ────────────────────────────────────────────────────

    def _selected_user_id(self) -> str | None:
        indexes = self.ui.tableView_users.selectionModel().selectedRows()
        if not indexes:
            QMessageBox.information(self, "選択", "ユーザーを選択してください。")
            return None
        return self._model.item(indexes[0].row(), 0).text()

    # ── 追加 ──────────────────────────────────────────────────────────────────

    def _on_add(self) -> None:
        dlg = AddUserDialog(parent=self.window())
        if dlg.exec() != dlg.DialogCode.Accepted:
            return
        data = dlg.get_data()
        err = self.user_service.add_user(
            user_id=data["id"],
            name=data["name"],
            email=data["email"],
            password=data["password"],
            is_active=data["is_active"],
            is_admin=data["is_admin"],
            is_analyst=data["is_analyst"],
            is_reviewer=data["is_reviewer"],
            is_anomaly_mail=data["is_anomaly_mail"],
        )
        if err:
            QMessageBox.warning(self.window(), "エラー", err)
            return
        self.load_users()

    # ── 編集 ──────────────────────────────────────────────────────────────────

    def _on_edit(self) -> None:
        uid = self._selected_user_id()
        if not uid:
            return
        user = self.user_service.get_user(uid)
        if not user:
            QMessageBox.warning(self.window(), "エラー", "ユーザーデータの取得に失敗しました。")
            return

        dlg = AddUserDialog(edit_data=user, parent=self.window())
        if dlg.exec() != dlg.DialogCode.Accepted:
            return
        data = dlg.get_data()
        new_id = data["id"]
        # ID変更チェック: 新IDが別ユーザーと重複していないか
        if new_id != uid and self.user_service.get_user(new_id):
            QMessageBox.warning(self.window(), "エラー", f"ID '{new_id}' は既に使用されています。")
            return
        err = self.user_service.update_user(
            user_id=uid,
            new_id=new_id,
            name=data["name"],
            email=data["email"],
            is_active=data["is_active"],
            is_admin=data["is_admin"],
            is_analyst=data["is_analyst"],
            is_reviewer=data["is_reviewer"],
            is_anomaly_mail=data["is_anomaly_mail"],
        )
        if err:
            QMessageBox.warning(self.window(), "エラー", err)
            return
        self.load_users()

    # ── パスワードリセット ────────────────────────────────────────────────────

    def _on_reset_password(self) -> None:
        uid = self._selected_user_id()
        if not uid:
            return

        dlg = ResetPasswordDialog(uid, parent=self.window())
        if dlg.exec() != dlg.DialogCode.Accepted:
            return
        err = self.user_service.reset_password(uid, dlg.get_password())
        if err:
            QMessageBox.warning(self.window(), "エラー", err)
            return
        QMessageBox.information(self.window(), "完了", "パスワードを更新しました。")

    # ── 有効/無効切替 ─────────────────────────────────────────────────────────

    def _on_toggle_active(self) -> None:
        uid = self._selected_user_id()
        if not uid:
            return
        user = self.user_service.get_user(uid)
        if not user:
            return
        current = "有効" if user.get("is_active", True) else "無効"
        new = "無効" if user.get("is_active", True) else "有効"
        ret = QMessageBox.question(
            self.window(),
            "確認",
            f"ユーザー '{user.get('name', uid)}' を {current} → {new} に変更しますか？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if ret != QMessageBox.StandardButton.Yes:
            return
        err = self.user_service.toggle_active(uid)
        if err:
            QMessageBox.warning(self.window(), "エラー", err)
            return
        self.load_users()

    # ── ヘルパー ──────────────────────────────────────────────────────────────

    @staticmethod
    def _check_item(value: bool) -> QStandardItem:
        """bool 値をチェックマーク文字で表示する QStandardItem を返す。"""
        item = QStandardItem("○" if value else "")
        if value:
            item.setForeground(Qt.GlobalColor.darkGreen)
        return item
