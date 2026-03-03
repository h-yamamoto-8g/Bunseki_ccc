"""JOBマスタの永続化ストア。app_data/bunseki/jobs/jobs.json に保存する。"""
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

import app.config as _cfg


def _jobs_path():
    return _cfg.DATA_PATH / "bunseki" / "jobs" / "jobs.json"


def _load() -> list[dict]:
    if not _jobs_path().exists():
        return []
    try:
        return json.loads(_jobs_path().read_text(encoding="utf-8"))
    except Exception:
        return []


def _save(items: list[dict]) -> None:
    _jobs_path().parent.mkdir(parents=True, exist_ok=True)
    _jobs_path().write_text(
        json.dumps(items, ensure_ascii=False, indent=2), encoding="utf-8"
    )


def get_all() -> list[dict]:
    """全JOBを作成日降順で返す。"""
    items = _load()
    return sorted(items, key=lambda x: x.get("created_at", ""), reverse=True)


def get(job_id: str) -> dict | None:
    for item in _load():
        if item.get("id") == job_id:
            return item
    return None


def create(
    job_number: str,
    start_date: str,
    end_date: str,
    created_by: str,
    notes: str = "",
) -> dict:
    """JOBを新規作成して返す。"""
    now = datetime.now()
    job_id = now.strftime("%Y%m%d%H%M%S")
    item = {
        "id": job_id,
        "job_number": job_number,
        "start_date": start_date,
        "end_date": end_date,
        "notes": notes,
        "is_active": True,
        "created_by": created_by,
        "created_at": now.isoformat(timespec="seconds"),
        "updated_at": now.isoformat(timespec="seconds"),
    }
    items = _load()
    items.append(item)
    _save(items)
    return item


def update(job_id: str, **fields) -> dict | None:
    """指定IDのJOBを更新して返す。"""
    items = _load()
    for item in items:
        if item.get("id") == job_id:
            item.update(fields)
            item["updated_at"] = datetime.now().isoformat(timespec="seconds")
            _save(items)
            return item
    return None


def delete(job_id: str) -> bool:
    """指定IDのJOBを削除する。成功時True。"""
    items = _load()
    new_items = [x for x in items if x.get("id") != job_id]
    if len(new_items) == len(items):
        return False
    _save(new_items)
    return True
