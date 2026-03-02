"""ニュースの永続化ストア。app_data/bunseki/news/news.json に保存する。"""
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from app.config import DATA_PATH

_NEWS_PATH = DATA_PATH / "bunseki" / "news" / "news.json"


def _load() -> list[dict]:
    if not _NEWS_PATH.exists():
        return []
    try:
        return json.loads(_NEWS_PATH.read_text(encoding="utf-8"))
    except Exception:
        return []


def _save(items: list[dict]) -> None:
    _NEWS_PATH.parent.mkdir(parents=True, exist_ok=True)
    _NEWS_PATH.write_text(
        json.dumps(items, ensure_ascii=False, indent=2), encoding="utf-8"
    )


def get_all() -> list[dict]:
    """全ニュースを新しい順で返す。"""
    items = _load()
    return sorted(items, key=lambda x: x.get("created_at", ""), reverse=True)


def get(news_id: str) -> dict | None:
    for item in _load():
        if item.get("id") == news_id:
            return item
    return None


def create(
    title: str,
    body: str,
    created_by: str,
    target_tests: list[str] | None = None,
    target_period_from: str = "",
    target_period_to: str = "",
    links: list[dict] | None = None,
) -> dict:
    """ニュースを新規作成して返す。"""
    now = datetime.now()
    news_id = now.strftime("%Y%m%d%H%M%S")
    item = {
        "id": news_id,
        "title": title,
        "body": body,
        "created_by": created_by,
        "created_at": now.isoformat(timespec="seconds"),
        "target_tests": target_tests or [],
        "target_period_from": target_period_from,
        "target_period_to": target_period_to,
        "links": links or [],
    }
    items = _load()
    items.append(item)
    _save(items)
    return item


def update(news_id: str, **fields) -> dict | None:
    """指定 ID のニュースを更新して返す。"""
    items = _load()
    for item in items:
        if item.get("id") == news_id:
            item.update(fields)
            _save(items)
            return item
    return None


def delete(news_id: str) -> bool:
    """指定 ID のニュースを削除する。成功時 True。"""
    items = _load()
    new_items = [x for x in items if x.get("id") != news_id]
    if len(new_items) == len(items):
        return False
    _save(new_items)
    return True
