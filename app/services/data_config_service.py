"""データ表示設定のサービス層。"""
from __future__ import annotations

from app.core import data_config_store

# bunseki.csv の全列定義（内部キー, デフォルト表示名）
ALL_COLUMNS: list[tuple[str, str]] = [
    ("sample_sampling_date",       "サンプリング日"),
    ("sample_request_number",      "依頼番号"),
    ("sample_job_number",          "JOB番号"),
    ("valid_holder_display_name",  "ホルダ名"),
    ("valid_sample_display_name",  "サンプル名"),
    ("valid_test_display_name",    "試験項目"),
    ("test_raw_data",              "データ"),
    ("test_unit_name",             "単位"),
    ("test_grade_code",            "判定"),
]

# デフォルトではすべて表示
_DEFAULT_COLUMNS: list[dict] = [
    {"key": key, "label": label, "visible": True}
    for key, label in ALL_COLUMNS
]


class DataConfigService:
    """データ表示設定サービス。"""

    def get_columns(self) -> list[dict]:
        """列設定を返す。未保存ならデフォルト。"""
        cfg = data_config_store.load()
        columns = cfg.get("columns")
        if not columns:
            return [dict(c) for c in _DEFAULT_COLUMNS]
        # 新しい列がCSVに追加された場合に追随
        saved_keys = {c["key"] for c in columns}
        for key, label in ALL_COLUMNS:
            if key not in saved_keys:
                columns.append({"key": key, "label": label, "visible": True})
        return columns

    def save_columns(self, columns: list[dict]) -> None:
        """列設定を保存する。"""
        cfg = data_config_store.load()
        cfg["columns"] = columns
        data_config_store.save(cfg)
