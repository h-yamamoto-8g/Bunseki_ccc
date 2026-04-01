"""ログページのサービス層。

分析装置マスタと調整試薬マスタの操作を提供する。
UIはこのクラスのみを通じてデータを操作する。
"""
from __future__ import annotations

from app.core import equipment_store, reagent_store


class LogService:
    """ログ機能のビジネスロジック。"""

    # ── 分析装置 ──────────────────────────────────────────────────────────────

    def get_all_equipment(self) -> list[dict]:
        return equipment_store.get_all()

    def get_equipment(self, item_id: str) -> dict | None:
        return equipment_store.get(item_id)

    def create_equipment(
        self,
        name: str,
        link: str,
        holder_group_code: str,
        holder_group_name: str,
        created_by: str,
    ) -> dict:
        return equipment_store.create(
            name, link, holder_group_code, holder_group_name, created_by,
        )

    def update_equipment(self, item_id: str, **fields) -> dict | None:
        return equipment_store.update(item_id, **fields)

    def delete_equipment(self, item_id: str) -> bool:
        return equipment_store.delete(item_id)

    # ── 調整試薬マスタ ────────────────────────────────────────────────────────

    def get_all_reagents(self) -> list[dict]:
        return reagent_store.get_all()

    def get_reagent(self, item_id: str) -> dict | None:
        return reagent_store.get(item_id)

    def create_reagent(
        self,
        name: str,
        shelf_life_days: int,
        holder_group_code: str,
        holder_group_name: str,
        created_by: str,
        preparation_date: str = "",
    ) -> dict:
        return reagent_store.create(
            name, shelf_life_days, holder_group_code, holder_group_name,
            created_by, preparation_date,
        )

    def update_reagent(self, item_id: str, updated_by: str, **fields) -> dict | None:
        return reagent_store.update(item_id, updated_by, **fields)

    def delete_reagent(self, item_id: str) -> bool:
        return reagent_store.delete(item_id)
