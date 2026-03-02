from pathlib import Path

APP_VERSION = "1.0"
DATA_PATH = Path(r"C:\Users\12414\トクヤマグループ\環境分析課 - ドキュメント\app_data")

# Derived paths
COMMON_DATA_PATH = DATA_PATH / "_common"
MASTER_DATA_PATH = COMMON_DATA_PATH / "master_data" / "source"
BUNSEKI_CSV_PATH = COMMON_DATA_PATH / "data" / "lab_aid" / "normalized" / "bunseki.csv"
TASKS_PATH = DATA_PATH / "bunseki" / "tasks"
LOGS_PATH = DATA_PATH / "bunseki" / "logs"

# Current user (demo)
CURRENT_USER = "デモユーザー"

# State definitions
STATE_LABELS = {
    "task_setup": "起票",
    "analysis_targets": "分析対象",
    "analysis": "分析準備",
    "result_entry": "データ入力",
    "result_verification": "データ確認",
    "submission": "回覧",
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
