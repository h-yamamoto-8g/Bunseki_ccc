import json
import os
import platform
from pathlib import Path

APP_VERSION = "1.0"

# ─── ユーザーローカル設定 ───────────────────────────────────────────────────
# ブートストラップ設定は ~/.bunseki/settings.json に保存する。
LOCAL_SETTINGS_DIR = Path.home() / ".bunseki"
LOCAL_SETTINGS_PATH = LOCAL_SETTINGS_DIR / "settings.json"

# ─── USERPROFILE ベースのパス導出 ─────────────────────────────────────────────
_SYNC_ROOT_SUFFIX = "トクヤマグループ"
_DATA_PATH_SUFFIX = os.path.join(
    "トクヤマグループ", "環境分析課 - ドキュメント", "app_data"
)


def _load_settings() -> dict:
    if LOCAL_SETTINGS_PATH.exists():
        try:
            return json.loads(LOCAL_SETTINGS_PATH.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            pass
    return {}


def _save_settings(settings: dict) -> None:
    LOCAL_SETTINGS_DIR.mkdir(parents=True, exist_ok=True)
    LOCAL_SETTINGS_PATH.write_text(
        json.dumps(settings, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


# ── USERPROFILE ──────────────────────────────────────────────────────────────

def load_user_profile() -> Path | None:
    """ローカル設定から USERPROFILE を読み込む。未設定なら None。"""
    raw = _load_settings().get("user_profile_path", "")
    if raw:
        p = Path(raw)
        if p.exists() and p.is_dir():
            return p
    return None


def save_user_profile(path: Path) -> None:
    """USERPROFILE をローカル設定に保存する。"""
    settings = _load_settings()
    settings["user_profile_path"] = str(path)
    _save_settings(settings)


def _resolve_user_profile() -> Path:
    saved = load_user_profile()
    if saved is not None:
        return saved
    return Path.home()


USER_PROFILE = _resolve_user_profile()


def reload_user_profile(new_path: Path) -> None:
    """USERPROFILE と派生パスをすべて更新する。"""
    global USER_PROFILE
    USER_PROFILE = new_path
    reload_sync_root(new_path / _SYNC_ROOT_SUFFIX)
    reload_paths(new_path / _DATA_PATH_SUFFIX)


# ── DATA_PATH (USERPROFILE から導出) ─────────────────────────────────────────

def load_data_path() -> Path | None:
    """ローカル設定から DATA_PATH を読み込む。未設定なら None。"""
    # まず USERPROFILE から導出を試みる
    up = load_user_profile()
    if up is not None:
        derived = up / _DATA_PATH_SUFFIX
        if derived.exists() and derived.is_dir():
            return derived
    # フォールバック: 旧 app_data_path 設定
    raw = _load_settings().get("app_data_path", "")
    if raw:
        p = Path(raw)
        if p.exists() and p.is_dir():
            return p
    return None


def save_data_path(path: Path) -> None:
    """DATA_PATH をローカル設定に保存する。"""
    settings = _load_settings()
    settings["app_data_path"] = str(path)
    _save_settings(settings)


def _resolve_data_path() -> Path:
    saved = load_data_path()
    if saved is not None:
        return saved
    if platform.system() == "Windows":
        return Path.home() / _DATA_PATH_SUFFIX
    return Path.home() / "app_data"


DATA_PATH = _resolve_data_path()

# Derived paths
COMMON_DATA_PATH = DATA_PATH / "_common"
MASTER_DATA_PATH = COMMON_DATA_PATH / "master_data" / "source"
BUNSEKI_CSV_PATH = COMMON_DATA_PATH / "data" / "lab_aid" / "normalized" / "bunseki.csv"
TASKS_PATH = DATA_PATH / "bunseki" / "tasks"
LOGS_PATH = DATA_PATH / "bunseki" / "logs"


def reload_paths(new_data_path: Path) -> None:
    """DATA_PATH と派生パスをモジュールレベルで更新する。"""
    global DATA_PATH, COMMON_DATA_PATH, MASTER_DATA_PATH
    global BUNSEKI_CSV_PATH, TASKS_PATH, LOGS_PATH
    DATA_PATH = new_data_path
    COMMON_DATA_PATH = DATA_PATH / "_common"
    MASTER_DATA_PATH = COMMON_DATA_PATH / "master_data" / "source"
    BUNSEKI_CSV_PATH = COMMON_DATA_PATH / "data" / "lab_aid" / "normalized" / "bunseki.csv"
    TASKS_PATH = DATA_PATH / "bunseki" / "tasks"
    LOGS_PATH = DATA_PATH / "bunseki" / "logs"

# Current user
CURRENT_USER = "デモユーザー"
CURRENT_USER_ID = ""


def set_current_user(user_id: str, name: str) -> None:
    """ログイン後にカレントユーザーを設定する。"""
    global CURRENT_USER, CURRENT_USER_ID
    CURRENT_USER = name
    CURRENT_USER_ID = user_id

# State definitions
STATE_LABELS = {
    "task_setup": "起票",
    "analysis_targets": "サンプル",
    "analysis": "分析",
    "result_entry": "入力",
    "result_verification": "チェック",
    "submission": "フロー",
    "completed": "終了",
}

STATE_ORDER = [
    "task_setup",
    "analysis_targets",
    "analysis",
    "result_entry",
    "result_verification",
    "submission",
    "completed",
]

STATUS_LABELS = {
    "進行中": "#3b82f6",
    "回覧中": "#f59e0b",
    "終了": "#10b981",
}


# ── SharePoint 同期パスのユーティリティ ──────────────────────────────────────

def load_sync_root() -> Path | None:
    """USERPROFILE から同期ルートを導出する。"""
    up = load_user_profile()
    if up is not None:
        derived = up / _SYNC_ROOT_SUFFIX
        if derived.exists() and derived.is_dir():
            return derived
    # フォールバック: 旧 sync_root_path 設定
    raw = _load_settings().get("sync_root_path", "")
    if raw:
        p = Path(raw)
        if p.exists() and p.is_dir():
            return p
    return None


def save_sync_root(path: Path) -> None:
    """同期ルートをローカル設定に保存する。"""
    settings = _load_settings()
    settings["sync_root_path"] = str(path)
    _save_settings(settings)


def _resolve_sync_root() -> Path:
    saved = load_sync_root()
    if saved is not None:
        return saved
    if platform.system() == "Windows":
        return Path.home() / _SYNC_ROOT_SUFFIX
    return Path.home()


SYNC_ROOT = _resolve_sync_root()


def reload_sync_root(new_path: Path) -> None:
    """同期ルートをモジュールレベルで更新する。"""
    global SYNC_ROOT
    SYNC_ROOT = new_path


def get_sync_root() -> Path:
    """SharePoint 同期フォルダのルートを返す。"""
    return SYNC_ROOT


def to_relative_path(absolute_path: str) -> str | None:
    """絶対パスを同期ルートからの相対パスに変換する。

    同期ルート配下でなければ None を返す。
    """
    try:
        rel = Path(absolute_path).resolve().relative_to(get_sync_root().resolve())
        return str(rel)
    except (ValueError, OSError):
        return None


def to_absolute_path(relative_path: str) -> str:
    """同期ルートからの相対パスを絶対パスに変換する。"""
    return str(get_sync_root() / relative_path)


def is_under_sync_root(absolute_path: str) -> bool:
    """絶対パスが同期ルート配下かどうかを判定する。"""
    try:
        Path(absolute_path).resolve().relative_to(get_sync_root().resolve())
        return True
    except (ValueError, OSError):
        return False


# Sidebar pages
SIDEBAR_PAGES = [
    ("home",     "⌂",  "ホーム"),
    ("tasks",    "✓",  "タスク"),
    ("data",     "≡",  "データ"),
    ("news",     "✉",  "ニュース"),
    ("library",  "□",  "ライブラリ"),
    ("log",      "≀",  "ログ"),
    ("job",      "⚙",  "ジョブ"),
    ("settings", "✦",  "設定"),
]
