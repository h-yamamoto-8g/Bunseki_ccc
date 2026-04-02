"""データ表示設定のサービス層。"""
from __future__ import annotations

from app.core import data_config_store

# データページでデフォルト表示する列（キー）
_DEFAULT_VISIBLE = {
    "sample_sampling_date",
    "sample_request_number",
    "sample_job_number",
    "valid_holder_display_name",
    "valid_sample_display_name",
    "valid_test_display_name",
    "test_raw_data",
    "test_unit_name",
    "test_grade_code",
}


class DataConfigService:
    """データ表示設定サービス。"""

    def get_columns(self, csv_columns: list[str] | None = None) -> list[dict]:
        """列設定を返す。csv_columns が渡されたら実CSVヘッダーと同期する。"""
        cfg = data_config_store.load()
        saved: list[dict] | None = cfg.get("columns")

        if csv_columns is not None:
            return self._merge(saved or [], csv_columns)

        if saved:
            return saved
        # csv_columns も saved もない場合は空
        return []

    def _merge(
        self, saved: list[dict], csv_columns: list[str],
    ) -> list[dict]:
        """保存済み設定と実CSV列をマージする。"""
        saved_map = {c["key"]: c for c in saved}
        result: list[dict] = []

        for key in csv_columns:
            if key in saved_map:
                result.append(saved_map[key])
            else:
                result.append({
                    "key": key,
                    "label": key,
                    "visible": key in _DEFAULT_VISIBLE,
                })
        return result

    def save_columns(self, columns: list[dict]) -> None:
        """列設定を保存する。"""
        cfg = data_config_store.load()
        cfg["columns"] = columns
        data_config_store.save(cfg)
