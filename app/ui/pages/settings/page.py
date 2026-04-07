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
    QTabWidget,
    QVBoxLayout,
    QWidget,
)
from PySide6.QtCore import Qt

import app.config as _cfg
from app.config import save_data_path, reload_paths, save_sync_root, reload_sync_root
from app.services.data_config_service import DataConfigService
from app.services.data_service import DataService
from app.services.hg_config_service import HgConfigService
from app.services.user_service import UserService
from app.ui.dialogs.setup_root_dialog import SetupRootDialog
from app.ui.generated.ui_settingpage import Ui_SettingPage
from app.ui.pages.settings.data_tab import DataTab
from app.ui.pages.settings.hg_config_tab import HgConfigTab
from app.ui.pages.settings.home_tab import HomeTab
from app.ui.pages.settings.task_columns_tab import TaskColumnsTab
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
        self._build_sync_root_section()
        self._build_data_path_section()
        self._build_tool_path_section()
        self._setup_tabs()
        self.ui.tabs.setCurrentIndex(0)

    # ── 同期環境設定セクション ─────────────────────────────────────────────────

    def _build_sync_root_section(self) -> None:
        """タブの上に同期環境パス表示・変更セクションを挿入する。"""
        section = QWidget()
        section.setObjectName("widget_sync_root_section")
        section.setStyleSheet(
            "#widget_sync_root_section { background: #ffffff; "
            "border: 1px solid #e5e7eb; border-radius: 8px; }"
        )
        hl = QHBoxLayout(section)
        hl.setContentsMargins(16, 10, 16, 10)
        hl.setSpacing(12)

        label = QLabel("同期環境")
        label.setStyleSheet("font-weight: bold; font-size: 13px; border: none;")
        hl.addWidget(label)

        self.input_sync_root = QLineEdit(str(_cfg.SYNC_ROOT))
        self.input_sync_root.setReadOnly(True)
        self.input_sync_root.setStyleSheet(
            "background: #f9fafb; color: #6b7280; border: 1px solid #e5e7eb; "
            "border-radius: 4px; padding: 4px 8px;"
        )
        hl.addWidget(self.input_sync_root, 1)

        self.btn_change_sync = QPushButton("変更")
        self.btn_change_sync.setStyleSheet(
            "background: #3b82f6; color: white; border: none; "
            "border-radius: 6px; padding: 6px 16px; font-weight: 600;"
        )
        self.btn_change_sync.clicked.connect(self._on_change_sync_root)
        hl.addWidget(self.btn_change_sync)

        # verticalLayout の先頭 (index 0) に挿入
        self.ui.verticalLayout.insertWidget(0, section)

    def _on_change_sync_root(self) -> None:
        """フォルダ選択ダイアログで同期環境パスを変更する。"""
        from PySide6.QtWidgets import QFileDialog
        start_dir = str(_cfg.SYNC_ROOT)
        folder = QFileDialog.getExistingDirectory(
            self, "同期環境フォルダを選択", start_dir
        )
        if not folder:
            return
        new_path = Path(folder)
        if not new_path.exists() or not new_path.is_dir():
            return
        save_sync_root(new_path)
        reload_sync_root(new_path)
        self.input_sync_root.setText(str(new_path))
        QMessageBox.information(
            self,
            "同期環境を変更しました",
            f"新しい同期環境:\n{new_path}\n\n"
            "変更を完全に反映するにはアプリケーションを再起動してください。",
        )

    # ── data_path 設定セクション ───────────────────────────────────────────────

    def _build_data_path_section(self) -> None:
        """同期環境セクションの下に data_path 表示・変更セクションを挿入する。"""
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

        # 同期環境セクション(index 0)の次 (index 1) に挿入
        self.ui.verticalLayout.insertWidget(1, section)

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

    # ── ツールパス設定セクション ─────────────────────────────────────────────

    def _build_tool_path_section(self) -> None:
        """ツールパス設定セクション（Lab-Aid / 入力ツール）を挿入する。"""
        from app.services.data_config_service import DataConfigService
        self._tool_config = DataConfigService()

        section = QWidget()
        section.setObjectName("widget_tool_path_section")
        section.setStyleSheet(
            "#widget_tool_path_section { background: #ffffff; "
            "border: 1px solid #e5e7eb; border-radius: 8px; }"
        )
        vl = QVBoxLayout(section)
        vl.setContentsMargins(16, 10, 16, 10)
        vl.setSpacing(8)

        title = QLabel("ツール設定")
        title.setStyleSheet("font-weight: bold; font-size: 13px; border: none;")
        vl.addWidget(title)

        # Lab-Aid パス
        row1 = QHBoxLayout()
        row1.setSpacing(8)
        lbl1 = QLabel("Lab-Aid")
        lbl1.setFixedWidth(80)
        lbl1.setStyleSheet("font-size: 12px; color: #6b7280; border: none;")
        row1.addWidget(lbl1)
        self._input_labaid = QLineEdit(self._tool_config.get_tool_path("labaid_path"))
        self._input_labaid.setPlaceholderText("Lab-Aid のパスまたは URL")
        self._input_labaid.setStyleSheet(
            "background: #f9fafb; border: 1px solid #e5e7eb; "
            "border-radius: 4px; padding: 4px 8px;"
        )
        row1.addWidget(self._input_labaid, 1)
        vl.addLayout(row1)

        # 入力ツールパス
        row2 = QHBoxLayout()
        row2.setSpacing(8)
        lbl2 = QLabel("入力ツール")
        lbl2.setFixedWidth(80)
        lbl2.setStyleSheet("font-size: 12px; color: #6b7280; border: none;")
        row2.addWidget(lbl2)
        self._input_tool = QLineEdit(self._tool_config.get_tool_path("input_tool_path"))
        self._input_tool.setPlaceholderText("入力ツールのパスまたは URL（空欄でCSVを直接開く）")
        self._input_tool.setStyleSheet(
            "background: #f9fafb; border: 1px solid #e5e7eb; "
            "border-radius: 4px; padding: 4px 8px;"
        )
        row2.addWidget(self._input_tool, 1)
        vl.addLayout(row2)

        # 保存ボタン
        btn_row = QHBoxLayout()
        btn_row.addStretch()
        btn_save_tool = QPushButton("保存")
        btn_save_tool.setStyleSheet(
            "background: #3b82f6; color: white; border: none; "
            "border-radius: 6px; padding: 6px 16px; font-weight: 600;"
        )
        btn_save_tool.clicked.connect(self._on_save_tool_paths)
        btn_row.addWidget(btn_save_tool)
        vl.addLayout(btn_row)

        # 同期環境(0) + データ保存先(1) の次 (index 2) に挿入
        self.ui.verticalLayout.insertWidget(2, section)

    def _on_save_tool_paths(self) -> None:
        self._tool_config.save_tool_path("labaid_path", self._input_labaid.text().strip())
        self._tool_config.save_tool_path("input_tool_path", self._input_tool.text().strip())
        QMessageBox.information(self, "保存完了", "ツール設定を保存しました。")

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
        task_container = self._build_task_settings(
            self.hg_config_tab, self.task_columns_tab
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
    def _build_task_settings(hg_tab: QWidget, columns_tab: QWidget) -> QWidget:
        """分析項目設定と表示列設定をサブタブでまとめる。"""
        container = QWidget()
        vl = QVBoxLayout(container)
        vl.setContentsMargins(0, 0, 0, 0)
        sub_tabs = QTabWidget()
        sub_tabs.addTab(hg_tab, "分析項目設定")
        sub_tabs.addTab(columns_tab, "表示列設定")
        vl.addWidget(sub_tabs)
        return container

    @staticmethod
    def _embed(tab: QWidget, child: QWidget) -> None:
        """タブウィジェットに子ウィジェットを埋め込む。"""
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(child)
