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
