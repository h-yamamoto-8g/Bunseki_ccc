"""ユーザー管理のサービス層。

UIはこのクラスのみを通じてユーザーを操作する。
core.user_store にのみ依存し、UI に依存しない。
"""
from __future__ import annotations

import hashlib

from app.core import user_store


class UserService:
    """ユーザー操作のビジネスロジック。"""

    # ── 参照 ──────────────────────────────────────────────────────────────────

    def get_all_users(self) -> list[dict]:
        return user_store.load_users()

    def get_user(self, user_id: str) -> dict | None:
        return user_store.get_user(user_id)

    # ── 作成 ──────────────────────────────────────────────────────────────────

    def add_user(
        self,
        user_id: str,
        name: str,
        email: str,
        password: str,
        is_active: bool = True,
        is_admin: bool = False,
        is_analyst: bool = False,
        is_reviewer: bool = False,
        is_anomaly_mail: bool = False,
    ) -> str | None:
        """ユーザーを追加する。成功なら None、失敗ならエラーメッセージ。"""
        if not user_id.strip():
            return "IDを入力してください。"
        if not name.strip():
            return "名前を入力してください。"
        if user_store.get_user(user_id):
            return f"ID '{user_id}' は既に使用されています。"

        user_store.add_user({
            "id": user_id.strip(),
            "name": name.strip(),
            "email": email.strip(),
            "password": self._hash_password(password) if password else "",
            "is_active": is_active,
            "is_admin": is_admin,
            "is_analyst": is_analyst,
            "is_reviewer": is_reviewer,
            "is_anomaly_mail": is_anomaly_mail,
        })
        return None

    # ── 更新 ──────────────────────────────────────────────────────────────────

    def update_user(
        self,
        user_id: str,
        name: str,
        email: str,
        is_active: bool,
        is_admin: bool,
        is_analyst: bool,
        is_reviewer: bool,
        is_anomaly_mail: bool,
        new_id: str | None = None,
    ) -> str | None:
        """ユーザー情報を更新する。成功なら None、失敗ならエラーメッセージ。"""
        if not name.strip():
            return "名前を入力してください。"
        updates: dict = {
            "name": name.strip(),
            "email": email.strip(),
            "is_active": is_active,
            "is_admin": is_admin,
            "is_analyst": is_analyst,
            "is_reviewer": is_reviewer,
            "is_anomaly_mail": is_anomaly_mail,
        }
        if new_id and new_id != user_id:
            updates["id"] = new_id.strip()
        ok = user_store.update_user(user_id, updates)
        if not ok:
            return f"ユーザー '{user_id}' が見つかりません。"
        return None

    def reset_password(self, user_id: str, new_password: str) -> str | None:
        """パスワードをリセットする。成功なら None。"""
        if not new_password:
            return "パスワードを入力してください。"
        ok = user_store.update_user(
            user_id, {"password": self._hash_password(new_password)}
        )
        if not ok:
            return f"ユーザー '{user_id}' が見つかりません。"
        return None

    def toggle_active(self, user_id: str) -> str | None:
        """有効/無効を切り替える。成功なら None。"""
        user = user_store.get_user(user_id)
        if not user:
            return f"ユーザー '{user_id}' が見つかりません。"
        ok = user_store.update_user(
            user_id, {"is_active": not user.get("is_active", True)}
        )
        if not ok:
            return "更新に失敗しました。"
        return None

    # ── 認証 ──────────────────────────────────────────────────────────────────

    def authenticate(self, user_id: str, password: str) -> dict | str:
        """ユーザーIDとパスワードで認証する。

        Returns:
            成功時: ユーザー辞書。失敗時: エラーメッセージ文字列。
        """
        if not user_id.strip():
            return "ユーザーIDを入力してください。"
        if not password:
            return "パスワードを入力してください。"

        user = user_store.get_user(user_id.strip())
        if not user:
            return "ユーザーIDまたはパスワードが正しくありません。"
        if not user.get("is_active", True):
            return "このアカウントは無効になっています。"
        if user.get("password", "") != self._hash_password(password):
            return "ユーザーIDまたはパスワードが正しくありません。"
        return user

    # ── 内部 ──────────────────────────────────────────────────────────────────

    @staticmethod
    def _hash_password(password: str) -> str:
        return hashlib.sha256(password.encode("utf-8")).hexdigest()
