"""
ユーザーデータの CRUD（JSON 永続化）。

データ形式（基本形）:
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

互換対応:
    - {"items": [...]} 形式（ラップ形式）にも対応（将来/過去データ揺れ対策）
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import app.config as _cfg


def _users_file():
    return _cfg.DATA_PATH / "bunseki" / "config" / "users.json"

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


def _normalize(users: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """欠落フィールドを補完し、id 未設定なら自動採番する。

    役割:
        - ユーザー辞書に必須キーを補完して、アプリが常に同じ形で扱えるようにする。
        - 旧 ``role`` フィールドが存在する場合は、新しい bool フラグへマイグレーションする。

    手順:
        1) 既存の id 集合を作る（自動採番の重複を避けるため）
        2) 各ユーザーについて:
           - 旧 role があれば is_analyst / is_reviewer へ変換
           - _DEFAULTS を使って欠落キーを補完
           - id が空なら user_001 形式で自動採番
        3) 補完済みリストを返す
    """
    # 何をしているか:
    # - id が空のユーザーに採番するとき、既存 id と衝突しないように集合で保持する。
    existing_ids = {u.get("id", "") for u in users if u.get("id")}
    counter = 1

    for u in users:
        # 何をしているか:
        # - 旧データ互換: role を bool フラグに変換し、role は削除する。
        if "role" in u:
            role = u.pop("role")
            u.setdefault("is_analyst", role in ("analyst", "admin"))
            u.setdefault("is_reviewer", role == "reviewer")

        # 何をしているか:
        # - 欠落フィールドをデフォルト値で埋め、画面/ロジック側が KeyError にならないようにする。
        for key, default in _DEFAULTS.items():
            u.setdefault(key, default)

        # 何をしているか:
        # - id 未設定なら user_001, user_002... のように採番する（既存と衝突しないまで進める）。
        if not u["id"]:
            while f"user_{counter:03d}" in existing_ids:
                counter += 1
            u["id"] = f"user_{counter:03d}"
            existing_ids.add(u["id"])
            counter += 1

    return users


def _ensure() -> None:
    """users.json の保存先ディレクトリを作る。

    役割:
        - 初回起動やクリーン環境で users.json 保存先が無くて落ちるのを防ぐ。
    """
    _users_file().parent.mkdir(parents=True, exist_ok=True)


def _coerce_raw_to_user_list(raw: Any) -> list[dict[str, Any]]:
    """読み込んだ JSON を「list[dict]」に正規化する。

    役割:
        - users.json のフォーマット揺れ（list / dictラップ / 混入データ）を吸収する。
        - 想定外なら「原因がわかる形」で例外にする（静かに壊れたデータを使わない）。

    手順:
        1) raw が dict の場合: items/users の配列を探して取り出す
        2) raw が list の場合: そのまま users とする
        3) users の各要素が dict であることを検証（str混入などを弾く）
    """
    # 何をしているか:
    # - {"items":[...]} みたいなラップ形式を許容（将来/過去データの揺れ対策）。
    if isinstance(raw, dict):
        if isinstance(raw.get("items"), list):
            users = raw["items"]
        elif isinstance(raw.get("users"), list):
            users = raw["users"]
        else:
            raise ValueError(
                f"users.json の形式が不正です（dictだが items/users がありません）: keys={list(raw.keys())}"
            )
    elif isinstance(raw, list):
        users = raw
    else:
        raise ValueError(
            f"users.json の形式が不正です（list/dict ではありません）: type={type(raw).__name__}"
        )

    # 何をしているか:
    # - list の中身が dict 以外（strなど）だと _normalize で落ちるので、ここで早期に検出する。
    bad_types = {type(u).__name__ for u in users if not isinstance(u, dict)}
    if bad_types:
        raise ValueError(f"users.json の配列要素が不正です（dict以外が混在）: {bad_types}")

    return users  # type: ignore[return-value]


def load_users() -> list[dict[str, Any]]:
    """users.json を読み込み、正規化して返す。

    役割:
        - JSON を読み込み、互換吸収 → _normalize を通して返す。
    手順:
        1) 保存先確保
        2) ファイルが無ければ空配列
        3) JSON を読む
        4) 形式を検証し list[dict] に正規化
        5) _normalize を適用して返す
    """
    _ensure()
    if not _users_file().exists():
        return []

    try:
        raw = json.loads(_users_file().read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        # 何をしているか:
        # - 壊れたJSONでアプリ全体が落ちるのを防ぐ（必要ならここでログ出力に差し替え）。
        return []

    try:
        users = _coerce_raw_to_user_list(raw)
    except ValueError:
        # 何をしているか:
        # - 想定外形式を“黙って”使うと認証が壊れるので、いったん空で返してログイン不能を避ける。
        #   厳密運用なら raise にして UI へエラー表示させる方が望ましい。
        return []

    return _normalize(users)


def save_users(users: list[dict[str, Any]]) -> None:
    """users.json を保存する。

    役割:
        - UI/サービス層で編集された users を JSON に永続化する。
    手順:
        1) 保存先確保
        2) pretty json で書き込み
    """
    _ensure()
    _users_file().write_text(
        json.dumps(users, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def get_user(user_id: str) -> dict[str, Any] | None:
    """ユーザーIDで1件取得する。"""
    # 何をしているか:
    # - load_users() の正規化後データを走査し、id一致の最初のユーザーを返す。
    for u in load_users():
        if u.get("id") == user_id:
            return u
    return None


def add_user(user: dict[str, Any]) -> None:
    """ユーザーを追加する。"""
    # 何をしているか:
    # - 現在の users に append し、save する。
    users = load_users()
    users.append(user)
    save_users(users)


def update_user(user_id: str, updates: dict[str, Any]) -> bool:
    """ユーザーを更新する。見つかれば True。"""
    # 何をしているか:
    # - 該当ユーザーを探して update し、保存する。
    users = load_users()
    for u in users:
        if u.get("id") == user_id:
            u.update(updates)
            save_users(users)
            return True
    return False


def delete_user(user_id: str) -> bool:
    """ユーザーを削除する。見つかれば True。"""
    # 何をしているか:
    # - 該当ID以外のリストを作って保存する。
    users = load_users()
    new = [u for u in users if u.get("id") != user_id]
    if len(new) == len(users):
        return False
    save_users(new)
    return True