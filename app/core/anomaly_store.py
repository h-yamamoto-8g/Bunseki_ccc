"""anomaly_store — mean±2σ超過データの永続化。

回覧送信時に超過が検出されたレコードを JSON に追記する。
[page]data 画面での 2σ超過表示に使用する。
"""
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from app.config import DATA_PATH

ANOMALY_FILE = DATA_PATH / "bunseki" / "data" / "anomalies.json"


def _ensure() -> None:
    ANOMALY_FILE.parent.mkdir(parents=True, exist_ok=True)


def load_anomalies() -> list[dict]:
    """保存済み2σ超過レコードを全件返す。"""
    _ensure()
    if not ANOMALY_FILE.exists():
        return []
    with open(ANOMALY_FILE, encoding="utf-8") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return []


def save_anomaly_records(records: list[dict]) -> None:
    """records を anomalies.json に追記する（task_id ごとに上書き更新）。"""
    if not records:
        return
    _ensure()
    existing = load_anomalies()

    # 同 task_id の既存レコードを削除して再登録（べき等性）
    task_id = records[0].get("task_id", "")
    existing = [r for r in existing if r.get("task_id") != task_id]
    existing.extend(records)

    with open(ANOMALY_FILE, "w", encoding="utf-8") as f:
        json.dump(existing, f, ensure_ascii=False, indent=2, default=str)
