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

# ── タスクステート列のデフォルト表示キー ──────────────────────────────────────

_ANALYSIS_TARGETS_DEFAULT_VISIBLE = {
    "sample_request_number",
    "sample_job_number",
    "sample_sampling_date",
    "valid_sample_display_name",
}

_RESULT_VERIFICATION_DEFAULT_VISIBLE = {
    "valid_sample_display_name",
    "valid_test_display_name",
    "test_raw_data",
    "test_unit_name",
}

# 計算列（CSVには存在しないがテーブルで使える特殊列）
_ANALYSIS_TARGETS_EXTRA = [
    {"key": "median", "label": "中央値", "visible": True},
    {"key": "max",    "label": "最大値", "visible": True},
    {"key": "min",    "label": "最小値", "visible": True},
]

_RESULT_VERIFICATION_EXTRA = [
    {"key": "upper_limit",  "label": "最上限基準値", "visible": True},
    {"key": "lower_limit",  "label": "最下限基準値", "visible": True},
    {"key": "anomaly_flag", "label": "異常フラグ",   "visible": True},
]

_TASK_DEFAULT_VISIBLE: dict[str, set[str]] = {
    "analysis_targets": _ANALYSIS_TARGETS_DEFAULT_VISIBLE,
    "result_verification": _RESULT_VERIFICATION_DEFAULT_VISIBLE,
}

_TASK_EXTRA_COLUMNS: dict[str, list[dict]] = {
    "analysis_targets": _ANALYSIS_TARGETS_EXTRA,
    "result_verification": _RESULT_VERIFICATION_EXTRA,
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

    def get_task_columns(
        self, scope: str, csv_columns: list[str] | None = None,
    ) -> list[dict]:
        """タスクステートの列設定を返す。

        csv_columns が渡された場合、bunseki.csv の全列 + 計算列をマージする。

        Args:
            scope: "analysis_targets" または "result_verification"
            csv_columns: bunseki.csv の実ヘッダー一覧
        """
        cfg = data_config_store.load()
        saved: list[dict] | None = cfg.get(f"{scope}_columns")
        default_visible = _TASK_DEFAULT_VISIBLE.get(scope, set())
        extras = _TASK_EXTRA_COLUMNS.get(scope, [])

        if csv_columns is not None:
            return self._merge_task(saved or [], csv_columns, default_visible, extras)

        if saved:
            # csv_columns なしでも計算列が漏れていたら末尾に追加
            saved_keys = {c["key"] for c in saved}
            merged = list(saved)
            for e in extras:
                if e["key"] not in saved_keys:
                    merged.append(dict(e))
            return merged

        # 初回: csv_columns もない場合は空
        return []

    def _merge_task(
        self,
        saved: list[dict],
        csv_columns: list[str],
        default_visible: set[str],
        extras: list[dict],
    ) -> list[dict]:
        """保存済み設定と CSV 列 + 計算列をマージする。

        保存済みの順序を優先し、新規列は末尾に追加する。
        """
        all_keys = set(csv_columns) | {e["key"] for e in extras}
        saved_map = {c["key"]: c for c in saved}
        result: list[dict] = []
        used: set[str] = set()

        # 保存済みの順序を優先
        for c in saved:
            if c["key"] in all_keys:
                result.append(c)
                used.add(c["key"])

        # 未保存の CSV 列を末尾に追加
        for key in csv_columns:
            if key not in used:
                result.append({
                    "key": key,
                    "label": key,
                    "visible": key in default_visible,
                })
                used.add(key)

        # 未保存の計算列を末尾に追加
        for e in extras:
            if e["key"] not in used:
                result.append(dict(e))

        return result

    def save_task_columns(self, scope: str, columns: list[dict]) -> None:
        """タスクステートの列設定を保存する。"""
        cfg = data_config_store.load()
        cfg[f"{scope}_columns"] = columns
        data_config_store.save(cfg)
