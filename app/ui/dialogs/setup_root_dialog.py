"""SetupRootDialog: データ保存先(app_data)パス設定ダイアログ。"""
from __future__ import annotations

from pathlib import Path

from PySide6.QtWidgets import QDialog, QFileDialog, QWidget

from app.config import save_data_path
from app.ui.generated.ui_setuprootdialog import Ui_SetupRootDialog


class SetupRootDialog(QDialog):
    """データ保存先フォルダを選択・設定するダイアログ。

    Args:
        current_path: 現在の設定パス（あれば入力欄に表示）。
        parent: 親ウィジェット。
    """

    def __init__(
        self, current_path: str = "", parent: QWidget | None = None
    ) -> None:
        super().__init__(parent)
        self.ui = Ui_SetupRootDialog()
        self.ui.setupUi(self)
        self.setWindowTitle("データ保存先の設定")

        if current_path:
            self.ui.input_data_path.setText(current_path)

        self.ui.btn_reference.clicked.connect(self._browse)
        self.ui.btn_ok.clicked.connect(self._on_ok)
        self.ui.btn_cancel.clicked.connect(self.reject)

    def _browse(self) -> None:
        """フォルダ選択ダイアログを開く。"""
        start_dir = self.ui.input_data_path.text() or str(Path.home())
        folder = QFileDialog.getExistingDirectory(
            self, "データ保存先フォルダを選択", start_dir
        )
        if folder:
            self.ui.input_data_path.setText(folder)

    def _on_ok(self) -> None:
        """入力パスを検証し、有効なら保存してダイアログを閉じる。"""
        path_text = self.ui.input_data_path.text().strip()
        if not path_text:
            self.ui.label_message.setText("パスを入力してください。")
            return

        p = Path(path_text)
        if not p.exists() or not p.is_dir():
            self.ui.label_message.setText(
                "指定されたフォルダが存在しません。正しいパスを選択してください。"
            )
            return

        save_data_path(p)
        self.accept()

    def selected_path(self) -> Path:
        """ユーザーが選択したパスを返す。"""
        return Path(self.ui.input_data_path.text().strip())
