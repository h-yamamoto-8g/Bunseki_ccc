"""調整試薬マスタの永続化ストア。

app_data/bunseki/logs/reagents.json に保存する。
各レコードに change_log (変更履歴) を内包する。
"""
from __future__ import annotations

import json
from datetime import datetime, date, timedelta
from pathlib import Path

import app.config as _cfg


# ── 使用期限の計算 ────────────────────────────────────────────────────────────


def calc_expiry(preparation_date: str, shelf_life_days: int) -> str:
    """調整日と保存可能日数から使用期限を計算して YYYY-MM-DD で返す。"""
    try:
        d = date.fromisoformat(preparation_date)
    except ValueError:
        return ""
    d += timedelta(days=shelf_life_days)
    return d.isoformat()


# ── 永続化 ────────────────────────────────────────────────────────────────────


def _path() -> Path:
    return _cfg.DATA_PATH / "bunseki" / "logs" / "reagents.json"


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


# ── CRUD ──────────────────────────────────────────────────────────────────────


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
    shelf_life_days: int,
    holder_group_code: str,
    holder_group_name: str,
    created_by: str,
    preparation_date: str = "",
) -> dict:
    now = datetime.now()
    expiry = calc_expiry(preparation_date, shelf_life_days) if preparation_date else ""
    item = {
        "id": now.strftime("%Y%m%d%H%M%S%f"),
        "name": name,
        "shelf_life_days": shelf_life_days,
        "holder_group_code": holder_group_code,
        "holder_group_name": holder_group_name,
        "preparation_date": preparation_date,
        "expiry_date": expiry,
        "created_by": created_by,
        "created_at": now.isoformat(timespec="seconds"),
        "updated_at": now.isoformat(timespec="seconds"),
        "change_log": [
            {
                "timestamp": now.isoformat(timespec="seconds"),
                "user": created_by,
                "action": "作成",
            }
        ],
    }
    items = _load()
    items.append(item)
    _save(items)
    return item


def update(item_id: str, updated_by: str, **fields) -> dict | None:
    """指定IDの試薬を更新する。変更内容を change_log に追記する。"""
    items = _load()
    for item in items:
        if item.get("id") == item_id:
            changes: list[str] = []
            for key, new_val in fields.items():
                old_val = item.get(key)
                if old_val != new_val:
                    changes.append(f"{key}: {old_val} → {new_val}")
                item[key] = new_val

            # preparation_date が変更された場合、expiry_date を再計算
            if "preparation_date" in fields:
                shelf = item.get("shelf_life_days", 0)
                prep = item.get("preparation_date", "")
                item["expiry_date"] = calc_expiry(prep, shelf) if prep else ""
            elif "shelf_life_days" in fields:
                prep = item.get("preparation_date", "")
                shelf = item.get("shelf_life_days", 0)
                item["expiry_date"] = calc_expiry(prep, shelf) if prep else ""

            now = datetime.now().isoformat(timespec="seconds")
            item["updated_at"] = now

            if changes:
                log = item.setdefault("change_log", [])
                log.append({
                    "timestamp": now,
                    "user": updated_by,
                    "action": "更新",
                    "details": "; ".join(changes),
                })

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
