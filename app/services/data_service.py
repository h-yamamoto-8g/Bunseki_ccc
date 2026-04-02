"""データクエリのサービス層。Core(DataLoader)のみに依存。"""
from __future__ import annotations

import pandas as pd

from app.core.loader import DataLoader
from app.core import hg_config_store
from app.services.hg_config_service import (
    DEFAULT_PRE_CHECKLIST,
    DEFAULT_POST_CHECKLIST,
    DEFAULT_VERIFY_CHECKLIST,
)

_DEFAULT_ANALYSIS_CONFIG = {
    "pre_documents": [],
    "post_documents": [],
    "pre_checklist": list(DEFAULT_PRE_CHECKLIST),
    "post_checklist": list(DEFAULT_POST_CHECKLIST),
    "verify_checklist": list(DEFAULT_VERIFY_CHECKLIST),
}


class DataService:
    """データクエリのサービス層。Core(DataLoader)のみに依存。"""

    def __init__(self, loader: DataLoader) -> None:
        self._loader = loader

    # ── Master ───────────────────────────────────────────────────────────────

    def get_users(self) -> list[dict]:
        """アクティブユーザー一覧を返す。"""
        return self._loader.get_users()

    def get_reviewers(self) -> list[dict]:
        """確認者権限を持つアクティブユーザー一覧を返す。"""
        return [u for u in self._loader.get_users() if u.get("is_reviewer")]

    def get_user_email(self, name: str) -> str:
        """ユーザー名からメールアドレスを返す。見つからない場合は空文字。"""
        for u in self._loader.get_users():
            if u.get("name") == name:
                return u.get("email", "")
        return ""

    def get_anomaly_mail_recipients(self) -> list[str]:
        """異常メール受信者（is_anomaly_mail=True）のメールアドレスを返す。"""
        return [
            u["email"]
            for u in self._loader.get_users()
            if u.get("is_anomaly_mail") and u.get("is_active") and u.get("email")
        ]

    def get_holder_groups(self) -> list[dict]:
        return self._loader.get_holder_groups()

    def get_valid_samples(self) -> list[dict]:
        return self._loader.get_valid_samples()

    # ── Analysis ─────────────────────────────────────────────────────────────

    def get_analysis_targets(
        self, hg_code: str, jobs: list[str]
    ) -> dict[str, list[dict]]:
        return self._loader.get_analysis_targets(hg_code, jobs)

    def get_result_data(
        self,
        hg_code: str,
        jobs: list[str],
        vsset_codes: list[str],
    ) -> pd.DataFrame:
        return self._loader.get_result_data(hg_code, jobs, vsset_codes)

    def get_trend_data(
        self, hg_code: str, vsset: str, vtest: str
    ) -> list[dict]:
        return self._loader.get_trend_data(hg_code, vsset, vtest)

    def get_anomaly_bounds(
        self, hg_code: str, vsset: str, vtest: str
    ) -> dict:
        return self._loader.get_anomaly_bounds(hg_code, vsset, vtest)

    def get_spec_limits(
        self, hg_code: str, vsset: str, vtest: str
    ) -> dict:
        return self._loader.get_spec_limits(hg_code, vsset, vtest)

    def calculate_anomaly(self, row, hg_code: str):
        return self._loader.calculate_anomaly(row, hg_code)

    def extract_numeric(self, text: str):
        return self._loader.extract_numeric(text)

    # ── Config ───────────────────────────────────────────────────────────────

    def get_analysis_config(self, hg_code: str) -> dict:
        """hg_config_store から指定ホルダグループの設定を返す。"""
        cfg = hg_config_store.get_config(hg_code)
        if cfg:
            result = dict(_DEFAULT_ANALYSIS_CONFIG)
            result.update(cfg)
            return result
        return dict(_DEFAULT_ANALYSIS_CONFIG)

    # ── Anomaly records ───────────────────────────────────────────────────────

    def save_anomaly_records(self, records: list[dict]) -> None:
        """2σ超過レコードを保存する。"""
        from app.core import anomaly_store
        anomaly_store.save_anomaly_records(records)

    def load_anomaly_records(self) -> list[dict]:
        """保存済み2σ超過レコードを返す。"""
        from app.core import anomaly_store
        return anomaly_store.load_anomalies()

    # ── Data page ─────────────────────────────────────────────────────────────

    def get_data_page(self, **filters) -> pd.DataFrame:
        return self._loader.get_data_page(**filters)

    def get_dropdown_values(self) -> dict:
        return self._loader.get_dropdown_values()
