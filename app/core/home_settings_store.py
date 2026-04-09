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


def get_task_retention_days() -> int:
    """タスク保持期間（日数）を取得する。0 = 無制限。"""
    return _load().get("task_retention_days", 0)


def set_task_retention_days(days: int) -> None:
    """タスク保持期間（日数）を保存する。0 = 無制限。"""
    data = _load()
    data["task_retention_days"] = days
    _save(data)
