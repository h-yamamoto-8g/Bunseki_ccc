"""ユーザーデータの CRUD（JSON 永続化）。

データ形式:
    [
        {
            "id": "user01",
            "name": "山田太郎",
            "email": "yamada@example.com",
            "password": "",
            "is_active": true,
            "is_admin": false,
            "is_analyst": true,
            "is_reviewer": false,
            "is_anomaly_mail": false
        },
        ...
    ]
"""
from __future__ import annotations

import json
from pathlib import Path

from app.config import DATA_PATH

USERS_FILE = DATA_PATH / "bunseki" / "config" / "users.json"

_DEFAULTS = {
    "id": "",
    "name": "",
    "email": "",
    "password": "",
    "is_active": True,
    "is_admin": False,
    "is_analyst": False,
    "is_reviewer": False,
    "is_anomaly_mail": False,
}


def _normalize(users: list[dict]) -> list[dict]:
    """欠落フィールドを補完し、id 未設定なら自動採番する。

    旧 ``role`` フィールドから ``is_analyst`` / ``is_reviewer`` へ自動マイグレーション。
    """
    existing_ids = {u.get("id", "") for u in users if u.get("id")}
    counter = 1
    for u in users:
        # 旧 role → 新 bool フラグへ変換
        if "role" in u:
            role = u.pop("role")
            u.setdefault("is_analyst", role in ("analyst", "admin"))
            u.setdefault("is_reviewer", role == "reviewer")
        # デフォルト値で欠落フィールドを補完
        for key, default in _DEFAULTS.items():
            u.setdefault(key, default)
        # id が空なら自動採番
        if not u["id"]:
            while f"user_{counter:03d}" in existing_ids:
                counter += 1
            u["id"] = f"user_{counter:03d}"
            existing_ids.add(u["id"])
            counter += 1
    return users


def _ensure() -> None:
    USERS_FILE.parent.mkdir(parents=True, exist_ok=True)


def load_users() -> list[dict]:
    _ensure()
    if not USERS_FILE.exists():
        return []
    try:
        raw = json.loads(USERS_FILE.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return []
    return _normalize(raw)


def save_users(users: list[dict]) -> None:
    _ensure()
    USERS_FILE.write_text(
        json.dumps(users, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def get_user(user_id: str) -> dict | None:
    for u in load_users():
        if u.get("id") == user_id:
            return u
    return None


def add_user(user: dict) -> None:
    users = load_users()
    users.append(user)
    save_users(users)


def update_user(user_id: str, updates: dict) -> bool:
    users = load_users()
    for u in users:
        if u.get("id") == user_id:
            u.update(updates)
            save_users(users)
            return True
    return False


def delete_user(user_id: str) -> bool:
    users = load_users()
    new = [u for u in users if u.get("id") != user_id]
    if len(new) == len(users):
        return False
    save_users(new)
    return True
