"""調整試薬マスタ + 履歴の永続化ストア。

マスタ: app_data/bunseki/logs/reagents.json
履歴:   app_data/bunseki/logs/reagent_history.json
"""
from __future__ import annotations

import json
from datetime import datetime, date, timedelta
from pathlib import Path

import app.config as _cfg

# ── 保存可能期間 ─────────────────────────────────────────────────────────────
# shelf_life は日数(int)で管理する。0 は使い切り。


def calc_expiry(preparation_date: str, shelf_life_days: int) -> str:
    """調整日と保存可能日数から使用期限を計算して YYYY-MM-DD で返す。"""
    try:
        d = date.fromisoformat(preparation_date)
    except ValueError:
        return ""
    d += timedelta(days=shelf_life_days)
    return d.isoformat()


# ── マスタ ────────────────────────────────────────────────────────────────────

def _master_path() -> Path:
    return _cfg.DATA_PATH / "bunseki" / "logs" / "reagents.json"


def _load_master() -> list[dict]:
    if not _master_path().exists():
        return []
    try:
        return json.loads(_master_path().read_text(encoding="utf-8"))
    except Exception:
        return []


def _save_master(items: list[dict]) -> None:
    _master_path().parent.mkdir(parents=True, exist_ok=True)
    _master_path().write_text(
        json.dumps(items, ensure_ascii=False, indent=2), encoding="utf-8"
    )


def get_all() -> list[dict]:
    items = _load_master()
    return sorted(items, key=lambda x: x.get("created_at", ""), reverse=True)


def get(item_id: str) -> dict | None:
    for item in _load_master():
        if item.get("id") == item_id:
            return item
    return None


def create(
    name: str,
    shelf_life_days: int,
    holder_group_code: str,
    holder_group_name: str,
    created_by: str,
) -> dict:
    now = datetime.now()
    item = {
        "id": now.strftime("%Y%m%d%H%M%S%f"),
        "name": name,
        "shelf_life_days": shelf_life_days,
        "holder_group_code": holder_group_code,
        "holder_group_name": holder_group_name,
        "created_by": created_by,
        "created_at": now.isoformat(timespec="seconds"),
        "updated_at": now.isoformat(timespec="seconds"),
    }
    items = _load_master()
    items.append(item)
    _save_master(items)
    return item


def update(item_id: str, **fields) -> dict | None:
    items = _load_master()
    for item in items:
        if item.get("id") == item_id:
            item.update(fields)
            item["updated_at"] = datetime.now().isoformat(timespec="seconds")
            _save_master(items)
            return item
    return None


def delete(item_id: str) -> bool:
    items = _load_master()
    new_items = [x for x in items if x.get("id") != item_id]
    if len(new_items) == len(items):
        return False
    _save_master(new_items)
    return True


# ── 履歴 ─────────────────────────────────────────────────────────────────────

def _history_path() -> Path:
    return _cfg.DATA_PATH / "bunseki" / "logs" / "reagent_history.json"


def _load_history() -> list[dict]:
    if not _history_path().exists():
        return []
    try:
        return json.loads(_history_path().read_text(encoding="utf-8"))
    except Exception:
        return []


def _save_history(items: list[dict]) -> None:
    _history_path().parent.mkdir(parents=True, exist_ok=True)
    _history_path().write_text(
        json.dumps(items, ensure_ascii=False, indent=2), encoding="utf-8"
    )


def get_history(reagent_id: str) -> list[dict]:
    items = [h for h in _load_history() if h.get("reagent_id") == reagent_id]
    return sorted(items, key=lambda x: x.get("preparation_date", ""), reverse=True)


def get_all_history() -> list[dict]:
    items = _load_history()
    return sorted(items, key=lambda x: x.get("preparation_date", ""), reverse=True)


def create_history(
    reagent_id: str,
    preparation_date: str,
    shelf_life_days: int,
    prepared_by: str,
) -> dict:
    now = datetime.now()
    expiry = calc_expiry(preparation_date, shelf_life_days)
    item = {
        "id": now.strftime("%Y%m%d%H%M%S%f"),
        "reagent_id": reagent_id,
        "preparation_date": preparation_date,
        "expiry_date": expiry,
        "prepared_by": prepared_by,
        "created_at": now.isoformat(timespec="seconds"),
        "updated_at": now.isoformat(timespec="seconds"),
    }
    items = _load_history()
    items.append(item)
    _save_history(items)
    return item


def update_history(history_id: str, preparation_date: str, shelf_life_days: int) -> dict | None:
    items = _load_history()
    for item in items:
        if item.get("id") == history_id:
            item["preparation_date"] = preparation_date
            item["expiry_date"] = calc_expiry(preparation_date, shelf_life_days)
            item["updated_at"] = datetime.now().isoformat(timespec="seconds")
            _save_history(items)
            return item
    return None


def delete_history(history_id: str) -> bool:
    items = _load_history()
    new_items = [x for x in items if x.get("id") != history_id]
    if len(new_items) == len(items):
        return False
    _save_history(new_items)
    return True
