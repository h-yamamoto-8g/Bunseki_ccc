"""設定ページ — Ui_SettingPage ベース。

タブごとに個別ウィジェットを埋め込む構成。
今後タブを追加する場合は _setup_tabs() にウィジェットを追加する。
"""
from __future__ import annotations

from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)
from PySide6.QtCore import Qt

import app.config as _cfg
from app.config import save_data_path, reload_paths
from app.services.data_config_service import DataConfigService
from app.services.data_service import DataService
from app.services.hg_config_service import HgConfigService
from app.services.user_service import UserService
from app.ui.dialogs.setup_root_dialog import SetupRootDialog
from app.ui.generated.ui_settingpage import Ui_SettingPage
from app.ui.pages.settings.data_tab import DataTab
from app.ui.pages.settings.hg_config_tab import HgConfigTab
from app.ui.pages.settings.home_tab import HomeTab
from app.ui.pages.settings.users_tab import UsersTab


def _placeholder(text: str) -> QWidget:
    """未実装タブ用プレースホルダー。"""
    w = QWidget()
    layout = QVBoxLayout(w)
    label = QLabel(text)
    label.setAlignment(Qt.AlignmentFlag.AlignCenter)
    label.setStyleSheet("color: #9ca3af; font-size: 14px;")
    layout.addWidget(label)
    return w


class SettingsPage(QWidget):
    """設定ページ。

    Args:
        user_service: ユーザー管理サービス。
        parent: 親ウィジェット。
    """

    def __init__(
        self,
        user_service: UserService,
        hg_config_service: HgConfigService,
        data_service: DataService,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.user_service = user_service
        self.hg_config_service = hg_config_service
        self.data_service = data_service
        self.ui = Ui_SettingPage()
        self.ui.setupUi(self)
        self._build_data_path_section()
        self._setup_tabs()
        self.ui.tabs.setCurrentIndex(0)

    # ── data_path 設定セクション ───────────────────────────────────────────────

    def _build_data_path_section(self) -> None:
        """タブの上に data_path 表示・変更セクションを挿入する。"""
        section = QWidget()
        section.setObjectName("widget_data_path_section")
        section.setStyleSheet(
            "#widget_data_path_section { background: #ffffff; "
            "border: 1px solid #e5e7eb; border-radius: 8px; }"
        )
        hl = QHBoxLayout(section)
        hl.setContentsMargins(16, 10, 16, 10)
        hl.setSpacing(12)

        label = QLabel("データ保存先")
        label.setStyleSheet("font-weight: bold; font-size: 13px; border: none;")
        hl.addWidget(label)

        self.input_data_path = QLineEdit(str(_cfg.DATA_PATH))
        self.input_data_path.setReadOnly(True)
        self.input_data_path.setStyleSheet(
            "background: #f9fafb; color: #6b7280; border: 1px solid #e5e7eb; "
            "border-radius: 4px; padding: 4px 8px;"
        )
        hl.addWidget(self.input_data_path, 1)

        self.btn_change_path = QPushButton("変更")
        self.btn_change_path.setStyleSheet(
            "background: #3b82f6; color: white; border: none; "
            "border-radius: 6px; padding: 6px 16px; font-weight: 600;"
        )
        self.btn_change_path.clicked.connect(self._on_change_data_path)
        hl.addWidget(self.btn_change_path)

        # verticalLayout の先頭 (index 0) に挿入（tabs の前）
        self.ui.verticalLayout.insertWidget(0, section)

    def _on_change_data_path(self) -> None:
        """SetupRootDialog を開いてデータ保存先を変更する。"""
        dlg = SetupRootDialog(current_path=str(_cfg.DATA_PATH), parent=self)
        if dlg.exec() != dlg.DialogCode.Accepted:
            return

        new_path = dlg.selected_path()
        reload_paths(new_path)
        self.input_data_path.setText(str(new_path))

        QMessageBox.information(
            self,
            "データ保存先を変更しました",
            f"新しいデータ保存先:\n{new_path}\n\n"
            "変更を完全に反映するにはアプリケーションを再起動してください。",
        )

    # ── タブ構成 ──────────────────────────────────────────────────────────────

    def _setup_tabs(self) -> None:
        """各タブにウィジェットを埋め込む。"""
        # tab_users: ユーザー管理
        self.users_tab = UsersTab(self.user_service)
        self._embed(self.ui.tab_users, self.users_tab)

        # tab_home: ホーム設定
        self.home_tab = HomeTab()
        self._embed(self.ui.tab_home, self.home_tab)
        # tab_tasks: タスク設定（分析項目別設定）
        holder_groups = self.data_service.get_holder_groups()
        self.hg_config_tab = HgConfigTab(self.hg_config_service, holder_groups)
        self._embed(self.ui.tab_tasks, self.hg_config_tab)

        self._embed(self.ui.tab_news, _placeholder("ニュース設定（実装予定）"))
        # tab_data: データ設定
        self.data_config_service = DataConfigService()
        self.data_tab = DataTab(self.data_config_service)
        self._embed(self.ui.tab_data, self.data_tab)
        self._embed(self.ui.tab_library, _placeholder("ライブラリ設定（実装予定）"))
        self._embed(self.ui.tab_logs, _placeholder("ログ設定（実装予定）"))
        self._embed(self.ui.tab_jobs, _placeholder("ジョブ設定（実装予定）"))

    @staticmethod
    def _embed(tab: QWidget, child: QWidget) -> None:
        """タブウィジェットに子ウィジェットを埋め込む。"""
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(child)
