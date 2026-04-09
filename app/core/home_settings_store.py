"""ホームページ設定の永続化ストア。

app_data/bunseki/settings/home.json に保存する。
"""
from __future__ import annotations

import json
from pathlib import Path

import app.config as _cfg


def _path() -> Path:
    return _cfg.DATA_PATH / "bunseki" / "settings" / "home.json"


def _load() -> dict:
    if not _path().exists():
        return {}
    try:
        return json.loads(_path().read_text(encoding="utf-8"))
    except Exception:
        return {}


def _save(data: dict) -> None:
    _path().parent.mkdir(parents=True, exist_ok=True)
    _path().write_text(
        json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8"
    )


def get_calendar_url() -> str:
    """カレンダーのURLを取得する。"""
    return _load().get("calendar_url", "")


def set_calendar_url(url: str) -> None:
    """カレンダーのURLを保存する。"""
    data = _load()
    data["calendar_url"] = url
    _save(data)


# ── タスクフィルタ ────────────────────────────────────────────────────────────


def get_last_task_filter() -> str:
    """最後に使用したタスクフィルタを取得する。"""
    return _load().get("last_task_filter", "全件")


def set_last_task_filter(filter_key: str) -> None:
    """最後に使用したタスクフィルタを保存する。"""
    data = _load()
    data["last_task_filter"] = filter_key
    _save(data)


# ── 表示件数 ──────────────────────────────────────────────────────────────────


def get_page_sizes() -> dict[str, int]:
    """ページ表示件数の設定を取得する。

    Returns:
        ``{"tasks": int, "data": int, "library": int}``
    """
    defaults = {"tasks": 100, "data": 500, "library": 50}
    stored = _load().get("page_sizes", {})
    return {k: stored.get(k, v) for k, v in defaults.items()}


def set_page_sizes(sizes: dict[str, int]) -> None:
    """ページ表示件数の設定を保存する。"""
    data = _load()
    data["page_sizes"] = sizes
    _save(data)


# ── タスク保持 ────────────────────────────────────────────────────────────────


# ── メールテンプレート ────────────────────────────────────────────────────────

DEFAULT_MAIL_CONFIG: dict[str, str] = {
    "subject_prefix": "[Bunseki]",
    "header_color": "#1e3a5f",
    "complete_color": "#166534",
    "footer_text": "",
}


def get_mail_config() -> dict[str, str]:
    """メールテンプレート設定を取得する。"""
    stored = _load().get("mail_config", {})
    return {k: stored.get(k, v) for k, v in DEFAULT_MAIL_CONFIG.items()}


def set_mail_config(config: dict[str, str]) -> None:
    """メールテンプレート設定を保存する。"""
    data = _load()
    data["mail_config"] = config
    _save(data)


# ── 日付フォーマット ──────────────────────────────────────────────────────────

# フォーマット選択肢
DATE_FORMAT_OPTIONS: list[dict[str, str]] = [
    {"label": "YYYY-MM-DD", "date": "YYYY-MM-DD", "datetime": "YYYY-MM-DD HH:mm"},
    {"label": "YYYY/MM/DD", "date": "YYYY/MM/DD", "datetime": "YYYY/MM/DD HH:mm"},
    {"label": "YYYY年MM月DD日", "date": "YYYY年MM月DD日", "datetime": "YYYY年MM月DD日 HH:mm"},
]


def get_date_format() -> str:
    """日付フォーマットのラベルを取得する。デフォルト: 'YYYY-MM-DD'。"""
    return _load().get("date_format", "YYYY-MM-DD")


def set_date_format(fmt_label: str) -> None:
    """日付フォーマットのラベルを保存する。"""
    data = _load()
    data["date_format"] = fmt_label
    _save(data)


def get_date_format_strings() -> dict[str, str]:
    """現在の日付フォーマット文字列を返す。

    Returns:
        ``{"date": str, "datetime": str}``
    """
    label = get_date_format()
    for opt in DATE_FORMAT_OPTIONS:
        if opt["label"] == label:
            return {"date": opt["date"], "datetime": opt["datetime"]}
    return {"date": "YYYY-MM-DD", "datetime": "YYYY-MM-DD HH:mm"}


# ── タスク保持 ────────────────────────────────────────────────────────────────


# ── 印刷設定 ──────────────────────────────────────────────────────────────────

PAPER_SIZE_OPTIONS: list[str] = ["A4", "A3", "B4", "B5", "Letter"]
ORIENTATION_OPTIONS: list[str] = ["横 (Landscape)", "縦 (Portrait)"]

DEFAULT_PRINT_CONFIG: dict[str, str | float] = {
    "paper_size": "A4",
    "orientation": "横 (Landscape)",
    "margin": 10.0,
}


def get_print_config() -> dict:
    """印刷設定を取得する。"""
    stored = _load().get("print_config", {})
    return {k: stored.get(k, v) for k, v in DEFAULT_PRINT_CONFIG.items()}


def set_print_config(config: dict) -> None:
    """印刷設定を保存する。"""
    data = _load()
    data["print_config"] = config
    _save(data)


# ── タスク保持 ────────────────────────────────────────────────────────────────


def get_task_retention_days() -> int:
    """タスク保持期間（日数）を取得する。0 = 無制限。"""
    return _load().get("task_retention_days", 0)


def set_task_retention_days(days: int) -> None:
    """タスク保持期間（日数）を保存する。0 = 無制限。"""
    data = _load()
    data["task_retention_days"] = days
    _save(data)
