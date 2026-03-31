"""Bunseki アプリケーションエントリポイント。

MainWindow.ui の設計仕様に基づき、以下のレイアウトを構築する。

    QMainWindow
    └─ centralwidget (QHBoxLayout)
       ├─ frame_sidebar        (75px)
       └─ widget_main
          ├─ widget_header    (50px 固定高)
          ├─ widget_step      (50px 固定高, ステップナビ横並び, タスク時のみ表示)
          ├─ stack_pages      (QStackedWidget, 8ページ)
          └─ widget_statusbar (35px 固定高)

デザイン: ホワイトベース (#f5f7fa 背景、#333333 テキスト)。
"""
from __future__ import annotations

import pathlib
import platform
import sys
import time
from typing import TYPE_CHECKING, Optional

import builtins
_original_import = builtins.__import__

from PySide6.QtCore import Qt, QElapsedTimer, QSize, QTimer, QThread, Signal
from PySide6.QtGui import QFont, QPixmap
from PySide6.QtWidgets import (
    QApplication,
    QDialog,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QSplashScreen,
    QStackedWidget,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

# PySide6のshibokensupportがbuiltins.__import__をパッチしてsixと競合するため復元
builtins.__import__ = _original_import

# PyInstaller frozen環境ではshibokensupportのfeature検出を無効化する。
# shibokensupport.feature._mod_uses_pyside が inspect.getsource() を呼び、
# six._SixMetaPathImporter に _path 属性がなく AttributeError になるのを防止。
if getattr(sys, "frozen", False):
    try:
        import shibokensupport.feature as _sbk_feature
        _sbk_feature._mod_uses_pyside = lambda *_a, **_kw: False
    except Exception:
        pass

# ─── 重いモジュールはスプラッシュ表示後に遅延インポート ─────────────────────
# matplotlib, app.* モジュールは _load_app_modules() で読み込む
# TYPE_CHECKING ブロック: 静的解析用（実行時は読み込まれない）
if TYPE_CHECKING:
    import app.config as _cfg
    from app.config import APP_VERSION, load_data_path, reload_paths, set_current_user
    from app.core.loader import DataLoader
    from app.services.data_service import DataService
    from app.services.data_update_service import run_all as _run_data_update
    from app.services.hg_config_service import HgConfigService
    from app.services.job_service import JobService
    from app.services.task_service import TaskService
    from app.services.user_service import UserService
    from app.ui.dialogs.loading_dialog import LoadingOverlay
    from app.ui.dialogs.logon_dialog import LogonDialog
    from app.ui.dialogs.setup_root_dialog import SetupRootDialog
    from app.ui.pages.data_page import DataPage
    from app.ui.pages.home.wrapper import HomePage
    from app.ui.pages.job_page import JobPage
    from app.ui.pages.library_page import LibraryPage
    from app.ui.pages.log_page import LogPage
    from app.ui.pages.news_page import NewsPage
    from app.ui.pages.settings.page import SettingsPage
    from app.ui.pages.tasks.wrapper import TasksPage
    from app.ui.styles import GLOBAL_QSS
    from app.ui.widgets.icon_utils import get_icon
    from app.ui.widgets.sidebar import PAGE_INFO, Sidebar, StepNavigation

_cfg: app.config = None  # type: ignore[assignment]  # app.config (遅延)

_SPLASH_MIN_MS = 1500  # スプラッシュ最低表示時間 (ms)


class _DataUpdateWorker(QThread):
    """別スレッドでデータ更新を実行し、完了/エラーをシグナルで通知。"""

    finished = Signal()
    error = Signal(str)

    def __init__(self, func: object, parent: object = None) -> None:
        super().__init__(parent)  # type: ignore[arg-type]
        self._func = func

    def run(self) -> None:
        try:
            self._func()  # type: ignore[operator]
            self.finished.emit()
        except Exception as e:
            self.error.emit(str(e))



def _show_splash(qapp: QApplication) -> tuple[QSplashScreen | None, QElapsedTimer]:
    """QSplashScreen を表示して返す。

    frozen 環境では PyInstaller Splash (pyi_splash) が起動直後から
    表示されているため QSplashScreen は生成しない。
    """
    timer = QElapsedTimer()
    timer.start()

    if getattr(sys, "frozen", False):
        # PyInstaller Splash がすでに表示中 → QSplashScreen 不要
        return None, timer

    base = pathlib.Path(__file__).resolve().parent
    splash_path = base / "resources" / "assets" / "splash.png"
    pixmap = QPixmap(str(splash_path))
    splash = QSplashScreen(pixmap, Qt.WindowType.WindowStaysOnTopHint)
    splash.show()
    qapp.processEvents()
    return splash, timer


def _load_app_modules(qapp: QApplication) -> None:
    """スプラッシュ表示中に重いモジュールを読み込み、globals に注入する。"""
    g = globals()

    import matplotlib
    matplotlib.use("QtAgg")
    if platform.system() == "Darwin":
        matplotlib.rcParams["font.family"] = "Hiragino Sans"
    else:
        matplotlib.rcParams["font.family"] = "Yu Gothic"
    matplotlib.rcParams["axes.unicode_minus"] = False
    qapp.processEvents()

    import app.ui.generated.resources_rc  # noqa: F401  Qt リソース登録
    qapp.processEvents()

    import app.config as _cfg_mod
    from app.config import APP_VERSION, load_data_path, reload_paths, set_current_user
    from app.ui.styles import GLOBAL_QSS
    qapp.processEvents()

    from app.core.loader import DataLoader
    from app.services.task_service import TaskService
    from app.services.data_service import DataService
    from app.services.data_update_service import run_all as _run_data_update
    from app.services.hg_config_service import HgConfigService
    from app.services.job_service import JobService
    from app.services.user_service import UserService
    qapp.processEvents()

    from app.ui.dialogs.loading_dialog import LoadingOverlay
    from app.ui.dialogs.logon_dialog import LogonDialog
    from app.ui.dialogs.setup_root_dialog import SetupRootDialog
    from app.ui.pages.data_page import DataPage
    from app.ui.pages.home.wrapper import HomePage
    from app.ui.pages.job_page import JobPage
    from app.ui.pages.library_page import LibraryPage
    from app.ui.pages.log_page import LogPage
    from app.ui.pages.news_page import NewsPage
    from app.ui.pages.settings.page import SettingsPage
    from app.ui.pages.tasks.wrapper import TasksPage
    from app.ui.widgets.icon_utils import get_icon
    from app.ui.widgets.sidebar import PAGE_INFO, Sidebar, StepNavigation
    qapp.processEvents()

    # globals に注入
    g["_cfg"] = _cfg_mod
    g["APP_VERSION"] = APP_VERSION
    g["load_data_path"] = load_data_path
    g["reload_paths"] = reload_paths
    g["set_current_user"] = set_current_user
    g["GLOBAL_QSS"] = GLOBAL_QSS
    g["DataLoader"] = DataLoader
    g["TaskService"] = TaskService
    g["DataService"] = DataService
    g["_run_data_update"] = _run_data_update
    g["HgConfigService"] = HgConfigService
    g["JobService"] = JobService
    g["UserService"] = UserService
    g["LogonDialog"] = LogonDialog
    g["SetupRootDialog"] = SetupRootDialog
    g["LoadingOverlay"] = LoadingOverlay
    g["DataPage"] = DataPage
    g["HomePage"] = HomePage
    g["JobPage"] = JobPage
    g["LibraryPage"] = LibraryPage
    g["LogPage"] = LogPage
    g["NewsPage"] = NewsPage
    g["SettingsPage"] = SettingsPage
    g["TasksPage"] = TasksPage
    g["get_icon"] = get_icon
    g["PAGE_INFO"] = PAGE_INFO
    g["Sidebar"] = Sidebar
    g["StepNavigation"] = StepNavigation


# ─── ページインデックス ───────────────────────────────────────────────────────
_PAGE_IDX: dict[str, int] = {
    "home":     0,
    "tasks":    1,
    "data":     2,
    "news":     3,
    "library":  4,
    "log":      5,
    "job":      6,
    "settings": 7,
}


class MainWindow(QMainWindow):
    """Bunseki メインウィンドウ。

    MainWindow.ui の設計仕様に基づく構成:
    - サイドバー (75px)
    - ヘッダー: アクティブページ名 / タスク名 / 新規作成ボタン
    - ステップナビ: 横並びアイコン (タスク時のみ表示)
    - ページスタック (8 ページ)
    - カスタムステータスバー

    Args:
        parent: 親ウィジェット。
    """

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setWindowTitle(f"Bunseki ver.{APP_VERSION}")
        self.setMinimumSize(1280, 800)
        self.data_loader = DataLoader(_cfg.DATA_PATH)
        self.task_service = TaskService()
        self.data_service = DataService(self.data_loader)
        self.user_service = UserService()
        self.hg_config_service = HgConfigService()
        self.job_service = JobService()
        self._in_task_mode = False
        self._setup_ui()
        self._connect_signals()
        self.showMaximized()

    # ─── UI 構築 ─────────────────────────────────────────────────────────────

    def _setup_ui(self) -> None:
        """ウィンドウ全体のUIを構築する。"""
        central = QWidget()
        self.setCentralWidget(central)
        root = QHBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # ① サイドバー ─────────────────────────────────────────────────────
        self.sidebar = Sidebar()
        root.addWidget(self.sidebar)

        # ② メインエリア ───────────────────────────────────────────────────
        widget_main = self._build_widget_main()
        root.addWidget(widget_main, 1)

    def _build_widget_main(self) -> QWidget:
        """widget_main (ヘッダー + ステップナビ + スタック + ステータスバー) を構築する。

        Returns:
            構築した QWidget。
        """
        widget = QWidget()
        widget.setObjectName("widget_main")
        vl = QVBoxLayout(widget)
        vl.setContentsMargins(0, 0, 0, 0)
        vl.setSpacing(0)

        vl.addWidget(self._build_header())

        # widget_step: ステップナビゲーション（横並び、タスクモード時のみ表示）
        self.step_nav = StepNavigation()
        self.step_nav.setObjectName("widget_step")
        self.step_nav.setVisible(False)
        vl.addWidget(self.step_nav)

        vl.addWidget(self._build_stack())
        vl.addWidget(self._build_statusbar())

        return widget

    def _build_header(self) -> QWidget:
        """widget_header (50px 高) を構築する。

        Returns:
            構築した QWidget。
        """
        header = QWidget()
        header.setFixedHeight(50)
        header.setObjectName("widget_header")

        hl = QHBoxLayout(header)
        hl.setContentsMargins(16, 8, 16, 8)
        hl.setSpacing(12)

        # btn_active_page: 現在のページ名 + アイコン
        self.btn_active_page = QToolButton()
        self.btn_active_page.setObjectName("btn_active_page")
        self.btn_active_page.setToolButtonStyle(
            Qt.ToolButtonStyle.ToolButtonTextBesideIcon
        )
        self.btn_active_page.setIconSize(QSize(24, 24))
        self.btn_active_page.setIcon(get_icon(":/icons/home.svg", "#333333", size=24))
        self.btn_active_page.setText("ホーム")
        self.btn_active_page.setFixedHeight(34)
        hl.addWidget(self.btn_active_page)

        hl.addStretch()

        # label_active_tasks_name: タスク作業中にタスク名を表示
        self.label_active_tasks_name = QLabel()
        self.label_active_tasks_name.setObjectName("label_active_tasks_name")
        self.label_active_tasks_name.setAlignment(Qt.AlignmentFlag.AlignCenter)
        hl.addWidget(self.label_active_tasks_name)

        hl.addStretch()

        # btn_add_task: 新規タスク作成ボタン
        self.btn_add_task = QToolButton()
        self.btn_add_task.setObjectName("btn_add_task")
        self.btn_add_task.setToolButtonStyle(
            Qt.ToolButtonStyle.ToolButtonTextBesideIcon
        )
        self.btn_add_task.setIconSize(QSize(20, 20))
        self.btn_add_task.setIcon(get_icon(":/icons/add.svg", "#ffffff", size=20))
        self.btn_add_task.setText("新規作成")
        self.btn_add_task.setFixedHeight(34)
        hl.addWidget(self.btn_add_task)

        return header

    def _build_stack(self) -> QStackedWidget:
        """stack_pages (8 ページ) を構築する。

        Returns:
            構築した QStackedWidget。
        """
        self.stack = QStackedWidget()
        self.stack.setObjectName("stack_pages")
        self.stack.setContentsMargins(0, 0, 0, 0)

        self.home_page = HomePage(self.task_service)
        self.tasks_page = TasksPage(self.task_service, self.data_service, self.job_service)
        self.data_page = DataPage(self.data_service)
        self.news_page = NewsPage(self.data_service)
        self.library_page = LibraryPage(self.task_service)
        self.log_page = LogPage()
        self.job_page = JobPage(self.job_service)
        self.settings_page = SettingsPage(
            self.user_service,
            self.hg_config_service,
            self.data_service,
        )

        self.stack.addWidget(self.home_page)      # 0: home
        self.stack.addWidget(self.tasks_page)     # 1: tasks
        self.stack.addWidget(self.data_page)      # 2: data
        self.stack.addWidget(self.news_page)      # 3: news
        self.stack.addWidget(self.library_page)   # 4: library
        self.stack.addWidget(self.log_page)       # 5: log
        self.stack.addWidget(self.job_page)       # 6: job
        self.stack.addWidget(self.settings_page)  # 7: settings

        return self.stack

    def _build_statusbar(self) -> QWidget:
        """widget_statusbar (35px 高) を構築する。

        Returns:
            構築した QWidget。
        """
        bar = QWidget()
        bar.setFixedHeight(35)
        bar.setObjectName("widget_statusbar")

        hl = QHBoxLayout(bar)
        hl.setContentsMargins(12, 0, 12, 0)
        hl.setSpacing(8)

        # 通常ステータスラベル
        self.label_status = QLabel("準備完了")
        self.label_status.setObjectName("label_status")
        hl.addWidget(self.label_status)

        # ローディングインジケーター（スピナー + メッセージ）
        self.label_loading = QLabel()
        self.label_loading.setObjectName("label_loading")
        self.label_loading.setStyleSheet(
            "color: #3b82f6; font-size: 12px; font-weight: 500;"
        )
        self.label_loading.setVisible(False)
        hl.addWidget(self.label_loading)

        hl.addStretch()

        self.label_user = QLabel(_cfg.CURRENT_USER)
        self.label_user.setObjectName("label_user")
        hl.addWidget(self.label_user)

        # スピナーアニメーション用タイマー
        self._loading_timer = QTimer(self)
        self._loading_timer.setInterval(80)
        self._loading_timer.timeout.connect(self._tick_loading)
        self._loading_frame = 0
        self._loading_msg = ""

        return bar

    # ─── シグナル接続 ─────────────────────────────────────────────────────────

    def _connect_signals(self) -> None:
        """シグナルとスロットを接続し、初期状態を設定する。"""
        self.sidebar.page_changed.connect(self._on_page_change)
        self.btn_add_task.clicked.connect(self._open_new_task)
        self.step_nav.step_clicked.connect(self._on_step_clicked)

        self.home_page.navigate_to_new_task.connect(self._open_new_task)
        self.home_page.navigate_to_task.connect(self._open_task)
        self.home_page.navigate_to_news.connect(self._open_news)
        self.tasks_page.navigate_home.connect(self._go_home)
        self.tasks_page.task_context_changed.connect(self.set_task_context)
        self.tasks_page.task_context_cleared.connect(self.clear_task_context)
        self.tasks_page.step_edited.connect(self.step_nav.mark_edited)
        self.tasks_page.loading_changed.connect(self._on_loading_changed)
        self.tasks_page.handover_available.connect(self._set_handover_available)

        # 初期表示
        self.stack.setCurrentIndex(0)
        self.home_page.refresh()

    # ─── スロット ─────────────────────────────────────────────────────────────

    def _on_page_change(self, page_id: str) -> None:
        """サイドバーのページ変更を処理する。

        Args:
            page_id: 遷移先ページID。
        """
        self._exit_task_mode()

        idx = _PAGE_IDX.get(page_id, 0)
        self.stack.setCurrentIndex(idx)

        name, svg_path = PAGE_INFO.get(page_id, ("", ""))
        self.btn_active_page.setText(name)
        self.btn_active_page.setIcon(get_icon(svg_path, "#333333", size=24) if svg_path else self.btn_active_page.icon())
        self.label_active_tasks_name.clear()
        self.step_nav.clear()

        if page_id == "home":
            self.home_page.refresh()
        elif page_id == "tasks":
            self.tasks_page.show_list()
        elif page_id == "data":
            self.data_page.refresh()
        elif page_id == "news":
            self.news_page.refresh()
        elif page_id == "job":
            self.job_page._load_jobs()

    def _on_step_clicked(self, state_id: str) -> None:
        """ステップナビのボタンクリックを処理する。

        タスクが開かれていない場合はタスクページの一覧へ遷移する。

        Args:
            state_id: クリックされたステートID。
        """
        # tasks ページが表示されていない場合は切り替え
        if self.stack.currentIndex() != _PAGE_IDX["tasks"]:
            self.sidebar.set_active("tasks")
            self.stack.setCurrentIndex(_PAGE_IDX["tasks"])
            self.btn_active_page.setText("タスク")
            self.btn_active_page.setIcon(get_icon(":/icons/task.svg", "#333333", size=24))
        self.tasks_page.navigate_to_state(state_id)

    def _open_new_task(self) -> None:
        """新規タスク起票画面へ遷移する。"""
        self.sidebar.set_active("tasks")
        self.stack.setCurrentIndex(_PAGE_IDX["tasks"])
        self.btn_active_page.setText("タスク")
        self.btn_active_page.setIcon(get_icon(":/icons/task.svg", "#333333", size=24))
        self.label_active_tasks_name.clear()
        self.step_nav.clear()
        self.tasks_page.start_new_task()

    def _open_task(self, task_id: str) -> None:
        """既存タスクを再開する。

        Args:
            task_id: 再開するタスクID。
        """
        self.sidebar.set_active("tasks")
        self.stack.setCurrentIndex(_PAGE_IDX["tasks"])
        self.btn_active_page.setText("タスク")
        self.btn_active_page.setIcon(get_icon(":/icons/task.svg", "#333333", size=24))
        self.tasks_page.resume_task(task_id)

    def _go_home(self) -> None:
        """ホームページへ戻る。"""
        self.sidebar.set_active("home")
        self._on_page_change("home")

    def _open_news(self, news_id: str) -> None:
        """ニュースページを開いて対象ニュースを選択する。"""
        self.sidebar.set_active("news")
        self._on_page_change("news")
        self.news_page.select_news(news_id)

    # ─── 公開 API ─────────────────────────────────────────────────────────────

    def set_task_context(
        self, task_name: str, state_id: str, current_state: str = ""
    ) -> None:
        """タスク作業中のコンテキスト（タスク名・ステップ）を更新する。

        Args:
            task_name: ヘッダに表示するタスク名。
            state_id: 表示中のステートID。
            current_state: タスクの実際の進捗ステートID。
        """
        self._enter_task_mode()
        self.label_active_tasks_name.setText(task_name)
        self.step_nav.set_active_step(state_id, current_state=current_state)
        self.step_nav.setVisible(True)

    def clear_task_context(self) -> None:
        """タスクコンテキスト（タスク名・ステップハイライト）をリセットする。"""
        self._exit_task_mode()
        self.label_active_tasks_name.clear()
        self.step_nav.clear()
        self.step_nav.clear_edited()
        self.step_nav.setVisible(False)

    def _enter_task_mode(self) -> None:
        """共通ヘッダーをタスク編集モードに切り替える。"""
        if self._in_task_mode:
            return
        self._in_task_mode = True
        # btn_add_task: "新規作成" → "引き継ぎ"
        self.btn_add_task.clicked.disconnect()
        self.btn_add_task.clicked.connect(self.tasks_page.request_handover)
        self.btn_add_task.setText("引き継ぎ")
        self.btn_add_task.setIcon(get_icon(":/icons/switch.svg", "#ffffff", size=20))
        # btn_active_page: ページ名 → "一覧へ戻る"
        self.btn_active_page.clicked.connect(self._back_to_task_list)
        self.btn_active_page.setText("一覧へ戻る")
        self.btn_active_page.setIcon(get_icon(":/icons/return.svg", "#333333", size=24))

    def _exit_task_mode(self) -> None:
        """共通ヘッダーをタスク編集モードから通常モードに戻す。"""
        if not self._in_task_mode:
            return
        self._in_task_mode = False
        # btn_add_task: "引き継ぎ" → "新規作成" (必ず有効化して戻す)
        self.btn_add_task.setEnabled(True)
        self.btn_add_task.clicked.disconnect()
        self.btn_add_task.clicked.connect(self._open_new_task)
        self.btn_add_task.setText("新規作成")
        self.btn_add_task.setIcon(get_icon(":/icons/add.svg", "#ffffff", size=20))
        # btn_active_page: "一覧へ戻る" → "タスク"
        try:
            self.btn_active_page.clicked.disconnect(self._back_to_task_list)
        except RuntimeError:
            pass
        self.btn_active_page.setText("タスク")
        self.btn_active_page.setIcon(get_icon(":/icons/task.svg", "#333333", size=24))

    def _set_handover_available(self, available: bool) -> None:
        """引き継ぎボタンの有効/無効を切り替える。"""
        self.btn_add_task.setEnabled(available)

    def _back_to_task_list(self) -> None:
        """「一覧へ戻る」クリック: タスク一覧に戻る。"""
        self.tasks_page.show_list()

    # ─── ローディング表示 ─────────────────────────────────────────────────────

    _SPINNER_FRAMES = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]

    def _on_loading_changed(self, active: bool, msg: str) -> None:
        """loading_changed シグナルのスロット。"""
        if active:
            self.start_loading(msg)
        else:
            self.stop_loading()

    def start_loading(self, msg: str) -> None:
        """ローディングインジケーターを表示してアニメーションを開始する。

        Args:
            msg: ローディング中に表示するメッセージ。
        """
        self._loading_msg = msg
        self._loading_frame = 0
        self.label_status.setVisible(False)
        self.label_loading.setVisible(True)
        self.label_loading.setText(f"{self._SPINNER_FRAMES[0]}  {msg}")
        self._loading_timer.start()
        QApplication.processEvents()

    def stop_loading(self) -> None:
        """ローディングインジケーターを非表示にして通常状態に戻す。"""
        self._loading_timer.stop()
        self.label_loading.setVisible(False)
        self.label_status.setVisible(True)
        self.label_status.setText("準備完了")

    def _tick_loading(self) -> None:
        """スピナーフレームを1コマ進める。"""
        self._loading_frame = (self._loading_frame + 1) % len(self._SPINNER_FRAMES)
        frame = self._SPINNER_FRAMES[self._loading_frame]
        self.label_loading.setText(f"{frame}  {self._loading_msg}")

    def set_status(self, message: str) -> None:
        """ステータスバーのメッセージを更新する。

        Args:
            message: 表示するメッセージ。
        """
        self.label_status.setText(message)




def _ensure_data_path(qapp: QApplication) -> bool:
    """DATA_PATH が有効か確認し、未設定または無効ならダイアログで設定を促す。

    Returns:
        True: 有効なパスが設定済み。False: ユーザーがキャンセル。
    """
    # ユーザーが明示的にパスを保存済み かつ 有効なら OK
    if load_data_path() is not None:
        return True

    # 未設定 → 設定ダイアログを表示（フォールバックパスを初期値として提示）
    dlg = SetupRootDialog(str(_cfg.DATA_PATH))
    if dlg.exec() == QDialog.DialogCode.Accepted:
        new_path = dlg.selected_path()
        reload_paths(new_path)
        return True
    return False


def _login(qapp: QApplication) -> bool:
    """ログインダイアログを表示し、認証を行う。

    Returns:
        True: ログイン成功。False: キャンセル。
    """
    user_service = UserService()
    dlg = LogonDialog(user_service)
    dlg.raise_()
    dlg.activateWindow()
    if dlg.exec() != QDialog.DialogCode.Accepted:
        return False
    user = dlg.authenticated_user()
    if user:
        set_current_user(user.get("id", ""), user.get("name", ""))
    return True


def main() -> None:
    """アプリケーションを起動する。"""
    qapp = QApplication(sys.argv)

    # スプラッシュを最速で表示
    splash, timer = _show_splash(qapp)

    # スプラッシュ表示中に重いモジュールをロード (matplotlib, app.*)
    _load_app_modules(qapp)

    # 外観設定（GLOBAL_QSS は _load_app_modules で読み込み済み）
    if platform.system() == "Darwin":
        qapp.setFont(QFont("Hiragino Sans", 12))
    else:
        qapp.setFont(QFont("Yu Gothic UI", 10))
    qapp.setStyle("Fusion")
    qapp.setStyleSheet(GLOBAL_QSS)

    if not _ensure_data_path(qapp):
        sys.exit(0)

    # 最低表示時間を保証 (dev 環境の QSplashScreen 用)
    if splash is not None:
        remaining = _SPLASH_MIN_MS - timer.elapsed()
        if remaining > 0:
            deadline = timer.elapsed() + remaining
            while timer.elapsed() < deadline:
                qapp.processEvents()
                time.sleep(0.01)
        splash.close()

    # PyInstaller Splash を閉じる (frozen 環境のみ)
    try:
        import pyi_splash  # type: ignore[import-not-found]
        pyi_splash.close()
    except ImportError:
        pass

    if not _login(qapp):
        sys.exit(0)

    # ログイン後にデータ更新・正規化を実行 (ローディング表示付き)
    overlay = LoadingOverlay()
    overlay.start()

    _update_error: list[str] = []
    _update_done = False

    worker = _DataUpdateWorker(_run_data_update)

    def _on_finished() -> None:
        nonlocal _update_done
        _update_done = True

    def _on_error(msg: str) -> None:
        nonlocal _update_done
        _update_error.append(msg)
        _update_done = True

    worker.finished.connect(_on_finished)
    worker.error.connect(_on_error)
    worker.start()

    # イベントループを回しながらワーカー完了を待つ (アニメーション継続)
    while not _update_done:
        qapp.processEvents()
        QThread.msleep(50)

    worker.wait()
    overlay.stop()

    if _update_error:
        from PySide6.QtWidgets import QMessageBox
        QMessageBox.warning(None, "データ更新エラー", _update_error[0])  # type: ignore[arg-type]

    window = MainWindow()
    sys.exit(qapp.exec())


if __name__ == "__main__":
    main()
