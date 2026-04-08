"""設定ページ — Ui_SettingPage ベース。

タブごとに個別ウィジェットを埋め込む構成。
今後タブを追加する場合は _setup_tabs() にウィジェットを追加する。
"""
from __future__ import annotations

from pathlib import Path

from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)
from PySide6.QtCore import Qt

import app.config as _cfg
from app.config import save_user_profile, reload_user_profile
from app.services.data_config_service import DataConfigService
from app.services.data_service import DataService
from app.services.hg_config_service import HgConfigService
from app.services.user_service import UserService
from app.ui.generated.ui_settingpage import Ui_SettingPage
from app.ui.pages.settings.data_tab import DataTab
from app.ui.pages.settings.hg_config_tab import HgConfigTab
from app.ui.pages.settings.home_tab import HomeTab
from app.ui.pages.settings.task_columns_tab import TaskColumnsTab
from app.ui.pages.settings.tool_settings_tab import ToolSettingsTab
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
        self._build_user_profile_section()
        self._setup_tabs()
        self.ui.tabs.setCurrentIndex(0)

    # ── USERPROFILE 設定セクション ───────────────────────────────────────────────

    def _build_user_profile_section(self) -> None:
        """タブの上に USERPROFILE 表示・変更セクションを挿入する。"""
        section = QWidget()
        section.setObjectName("widget_user_profile_section")
        section.setStyleSheet(
            "#widget_user_profile_section { background: #ffffff; "
            "border: 1px solid #e5e7eb; border-radius: 8px; }"
        )
        vl = QVBoxLayout(section)
        vl.setContentsMargins(16, 10, 16, 10)
        vl.setSpacing(6)

        hl = QHBoxLayout()
        hl.setSpacing(12)

        label = QLabel("USERPROFILE")
        label.setStyleSheet("font-weight: bold; font-size: 13px; border: none;")
        hl.addWidget(label)

        self.input_user_profile = QLineEdit(str(_cfg.USER_PROFILE))
        self.input_user_profile.setReadOnly(True)
        self.input_user_profile.setStyleSheet(
            "background: #f9fafb; color: #6b7280; border: 1px solid #e5e7eb; "
            "border-radius: 4px; padding: 4px 8px;"
        )
        hl.addWidget(self.input_user_profile, 1)

        self.btn_change_profile = QPushButton("変更")
        self.btn_change_profile.setStyleSheet(
            "background: #3b82f6; color: white; border: none; "
            "border-radius: 6px; padding: 6px 16px; font-weight: 600;"
        )
        self.btn_change_profile.clicked.connect(self._on_change_user_profile)
        hl.addWidget(self.btn_change_profile)
        vl.addLayout(hl)

        # 導出パスのプレビュー
        self._lbl_derived = QLabel()
        self._lbl_derived.setStyleSheet(
            "font-size: 11px; color: #6b7280; border: none;"
        )
        self._lbl_derived.setWordWrap(True)
        self._update_derived_preview(str(_cfg.USER_PROFILE))
        vl.addWidget(self._lbl_derived)

        self.ui.verticalLayout.insertWidget(0, section)

    def _update_derived_preview(self, profile_path: str) -> None:
        p = Path(profile_path)
        sync = p / "トクヤマグループ"
        data = p / "トクヤマグループ" / "環境分析課 - ドキュメント" / "app_data"
        self._lbl_derived.setText(
            f"同期環境: {sync}\n"
            f"データ保存先: {data}"
        )

    def _on_change_user_profile(self) -> None:
        """フォルダ選択ダイアログで USERPROFILE を変更する。"""
        from PySide6.QtWidgets import QFileDialog
        start_dir = str(_cfg.USER_PROFILE)
        folder = QFileDialog.getExistingDirectory(
            self, "ユーザープロファイルフォルダを選択", start_dir
        )
        if not folder:
            return
        new_path = Path(folder)
        if not new_path.exists() or not new_path.is_dir():
            return
        save_user_profile(new_path)
        reload_user_profile(new_path)
        self.input_user_profile.setText(str(new_path))
        self._update_derived_preview(str(new_path))
        QMessageBox.information(
            self,
            "USERPROFILE を変更しました",
            f"新しいプロファイル:\n{new_path}\n\n"
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

        # CSV列ヘッダーを取得（タスク列設定・データ設定の両方で使用）
        self.data_config_service = DataConfigService()
        try:
            csv_columns = self.data_service.get_csv_columns()
        except Exception:
            csv_columns = None

        # tab_tasks: タスク設定（分析項目別設定 + 表示列設定）
        holder_groups = self.data_service.get_holder_groups()
        self.hg_config_tab = HgConfigTab(self.hg_config_service, holder_groups)
        self.task_columns_tab = TaskColumnsTab(
            self.data_config_service, csv_columns=csv_columns,
        )
        self.tool_settings_tab = ToolSettingsTab(self.data_config_service)
        task_container = self._build_task_settings(
            self.hg_config_tab, self.task_columns_tab, self.tool_settings_tab,
        )
        self._embed(self.ui.tab_tasks, task_container)

        self._embed(self.ui.tab_news, _placeholder("ニュース設定（実装予定）"))

        # tab_data: データ設定
        self.data_tab = DataTab(self.data_config_service, csv_columns=csv_columns)
        self._embed(self.ui.tab_data, self.data_tab)
        self._embed(self.ui.tab_library, _placeholder("ライブラリ設定（実装予定）"))
        self._embed(self.ui.tab_logs, _placeholder("ログ設定（実装予定）"))
        self._embed(self.ui.tab_jobs, _placeholder("ジョブ設定（実装予定）"))

    @staticmethod
    def _build_task_settings(
        hg_tab: QWidget, columns_tab: QWidget, tool_tab: QWidget,
    ) -> QWidget:
        """分析項目設定・表示列設定・ツール設定をサブタブでまとめる。"""
        container = QWidget()
        vl = QVBoxLayout(container)
        vl.setContentsMargins(0, 0, 0, 0)
        sub_tabs = QTabWidget()
        sub_tabs.addTab(hg_tab, "分析項目設定")
        sub_tabs.addTab(columns_tab, "表示列設定")
        sub_tabs.addTab(tool_tab, "ツール設定")
        vl.addWidget(sub_tabs)
        return container

    @staticmethod
    def _embed(tab: QWidget, child: QWidget) -> None:
        """タブウィジェットに子ウィジェットを埋め込む。"""
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(child)
