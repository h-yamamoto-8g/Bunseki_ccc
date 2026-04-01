"""分析装置マスタの永続化ストア。app_data/bunseki/logs/equipment.json に保存する。"""
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

import app.config as _cfg


def _path() -> Path:
    return _cfg.DATA_PATH / "bunseki" / "logs" / "equipment.json"


def _load() -> list[dict]:
    if not _path().exists():
        return []
    try:
        return json.loads(_path().read_text(encoding="utf-8"))
    except Exception:
        return []


def _save(items: list[dict]) -> None:
    _path().parent.mkdir(parents=True, exist_ok=True)
    _path().write_text(
        json.dumps(items, ensure_ascii=False, indent=2), encoding="utf-8"
    )


def get_all() -> list[dict]:
    items = _load()
    return sorted(items, key=lambda x: x.get("created_at", ""), reverse=True)


def get(item_id: str) -> dict | None:
    for item in _load():
        if item.get("id") == item_id:
            return item
    return None


def create(
    name: str,
    link: str,
    holder_group_code: str,
    holder_group_name: str,
    created_by: str,
) -> dict:
    now = datetime.now()
    item = {
        "id": now.strftime("%Y%m%d%H%M%S%f"),
        "name": name,
        "link": link,
        "holder_group_code": holder_group_code,
        "holder_group_name": holder_group_name,
        "created_by": created_by,
        "created_at": now.isoformat(timespec="seconds"),
        "updated_at": now.isoformat(timespec="seconds"),
    }
    items = _load()
    items.append(item)
    _save(items)
    return item


def update(item_id: str, **fields) -> dict | None:
    items = _load()
    for item in items:
        if item.get("id") == item_id:
            item.update(fields)
            item["updated_at"] = datetime.now().isoformat(timespec="seconds")
            _save(items)
            return item
    return None


def delete(item_id: str) -> bool:
    items = _load()
    new_items = [x for x in items if x.get("id") != item_id]
    if len(new_items) == len(items):
        return False
    _save(new_items)
    return True
