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

# ── タスクステート列のデフォルト定義 ─────────────────────────────────────────

ANALYSIS_TARGETS_COLUMNS: list[dict] = [
    {"key": "sample_request_number",      "label": "依頼番号",   "visible": True},
    {"key": "sample_job_number",          "label": "JOB番号",    "visible": True},
    {"key": "sample_sampling_date",       "label": "採取日",     "visible": True},
    {"key": "valid_sample_display_name",  "label": "サンプル名", "visible": True},
    {"key": "median",                     "label": "中央値",     "visible": True},
    {"key": "max",                        "label": "最大値",     "visible": True},
    {"key": "min",                        "label": "最小値",     "visible": True},
]

RESULT_VERIFICATION_COLUMNS: list[dict] = [
    {"key": "valid_sample_display_name",  "label": "サンプル名",   "visible": True},
    {"key": "valid_test_display_name",    "label": "試験項目名",   "visible": True},
    {"key": "test_raw_data",              "label": "データ",       "visible": True},
    {"key": "test_unit_name",             "label": "単位",         "visible": True},
    {"key": "upper_limit",               "label": "最上限基準値", "visible": True},
    {"key": "lower_limit",               "label": "最下限基準値", "visible": True},
    {"key": "anomaly_flag",              "label": "異常フラグ",   "visible": True},
]

_TASK_COLUMN_DEFAULTS: dict[str, list[dict]] = {
    "analysis_targets": ANALYSIS_TARGETS_COLUMNS,
    "result_verification": RESULT_VERIFICATION_COLUMNS,
}


class DataConfigService:
    """データ表示設定サービス。"""

    # ── データページ列設定 ────────────────────────────────────────────────────

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

    # ── タスクステート列設定 ──────────────────────────────────────────────────

    def get_task_columns(self, scope: str) -> list[dict]:
        """タスクステートの列設定を返す。

        Args:
            scope: "analysis_targets" または "result_verification"
        """
        cfg = data_config_store.load()
        saved: list[dict] | None = cfg.get(f"{scope}_columns")
        defaults = _TASK_COLUMN_DEFAULTS.get(scope, [])

        if saved:
            # デフォルトに存在するがsavedにないキーを末尾に追加
            saved_keys = {c["key"] for c in saved}
            merged = list(saved)
            for d in defaults:
                if d["key"] not in saved_keys:
                    merged.append(dict(d))
            return merged

        return [dict(c) for c in defaults]

    def save_task_columns(self, scope: str, columns: list[dict]) -> None:
        """タスクステートの列設定を保存する。"""
        cfg = data_config_store.load()
        cfg[f"{scope}_columns"] = columns
        data_config_store.save(cfg)
