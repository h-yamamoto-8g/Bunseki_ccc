"""ホルダグループ別設定のサービス層。Core(hg_config_store)のみに依存。"""
from __future__ import annotations

from pathlib import Path

from app.core import hg_config_store

# デフォルトチェックリスト（設定未保存時に使用）
DEFAULT_PRE_CHECKLIST: list[str] = [
    "試薬の有効期限を確認した",
    "装置の校正が完了している",
    "サンプル容器にラベルが正しく記載されている",
    "ブランクサンプルを準備した",
]

DEFAULT_POST_CHECKLIST: list[str] = [
    "全サンプルの測定が完了した",
    "装置のログを保存した",
    "試薬の使用量を記録した",
    "廃液を適切に処理した",
]

DEFAULT_VERIFY_CHECKLIST: list[str] = [
    "データ値の範囲を確認した",
    "異常フラグを確認した",
    "基準値との比較を確認した",
]

# 異常検出のデフォルト設定
DEFAULT_ANOMALY_SIGMA: float = 2.0
DEFAULT_ANOMALY_MIN_POINTS: int = 12
DEFAULT_ANOMALY_TREND_YEARS: int = 5

# 基準値列のデフォルト設定
DEFAULT_SPEC_COLUMNS: list[dict[str, str]] = [
    {
        "upper_column": "test_upper_limit_spec_1",
        "lower_column": "test_lower_limit_spec_1",
        "name": "基準値1",
    },
    {
        "upper_column": "test_upper_limit_spec_2",
        "lower_column": "test_lower_limit_spec_2",
        "name": "基準値2",
    },
    {
        "upper_column": "test_upper_limit_spec_3",
        "lower_column": "test_lower_limit_spec_3",
        "name": "基準値3",
    },
    {
        "upper_column": "test_upper_limit_spec_4",
        "lower_column": "test_lower_limit_spec_4",
        "name": "基準値4",
    },
]


class HgConfigService:
    """ホルダグループ別設定サービス。"""

    def get_config(self, hg_code: str) -> dict:
        """デフォルトとマージ済みの設定を返す。"""
        cfg = hg_config_store.get_config(hg_code)
        return {
            "pre_checklist": cfg.get("pre_checklist", list(DEFAULT_PRE_CHECKLIST)),
            "post_checklist": cfg.get("post_checklist", list(DEFAULT_POST_CHECKLIST)),
            "verify_checklist": cfg.get("verify_checklist", list(DEFAULT_VERIFY_CHECKLIST)),
            "pre_documents": cfg.get("pre_documents", []),
            "post_documents": cfg.get("post_documents", []),
            "has_manual": hg_config_store.has_manual(hg_code),
        }

    # ── 異常検出設定 ──────────────────────────────────────────────────────────

    def get_anomaly_config(self, hg_code: str) -> dict:
        """異常検出の設定を返す。未設定時はデフォルト値。

        Returns:
            ``{"sigma": float, "min_points": int, "trend_years": int}``
        """
        cfg = hg_config_store.get_config(hg_code)
        ac = cfg.get("anomaly_config", {})
        return {
            "sigma": ac.get("sigma", DEFAULT_ANOMALY_SIGMA),
            "min_points": ac.get("min_points", DEFAULT_ANOMALY_MIN_POINTS),
            "trend_years": ac.get("trend_years", DEFAULT_ANOMALY_TREND_YEARS),
        }

    def save_anomaly_config(
        self,
        hg_code: str,
        sigma: float,
        min_points: int,
        trend_years: int,
    ) -> None:
        """異常検出の設定を保存する。"""
        cfg = hg_config_store.get_config(hg_code)
        cfg["anomaly_config"] = {
            "sigma": sigma,
            "min_points": min_points,
            "trend_years": trend_years,
        }
        hg_config_store.set_config(hg_code, cfg)

    # ── 基準値列設定 ──────────────────────────────────────────────────────────

    def get_spec_columns(self, hg_code: str) -> list[dict[str, str]]:
        """基準値列の設定を返す。未設定時はデフォルト値。

        Returns:
            ``[{"upper_column": str, "lower_column": str, "name": str}, ...]``
        """
        cfg = hg_config_store.get_config(hg_code)
        return cfg.get("spec_columns", list(DEFAULT_SPEC_COLUMNS))

    def save_spec_columns(
        self,
        hg_code: str,
        spec_columns: list[dict[str, str]],
    ) -> None:
        """基準値列の設定を保存する。"""
        cfg = hg_config_store.get_config(hg_code)
        cfg["spec_columns"] = spec_columns
        hg_config_store.set_config(hg_code, cfg)

    # ── 確認者設定 ────────────────────────────────────────────────────────────

    def get_default_reviewers(self) -> list[str]:
        """デフォルトの確認者リストを返す。

        Returns:
            確認者名のリスト。
        """
        cfg = hg_config_store.get_config("_global")
        return cfg.get("default_reviewers", [])

    def save_default_reviewers(self, reviewers: list[str]) -> None:
        """デフォルトの確認者リストを保存する。"""
        cfg = hg_config_store.get_config("_global")
        cfg["default_reviewers"] = reviewers
        hg_config_store.set_config("_global", cfg)

    # ── 既存メソッド ──────────────────────────────────────────────────────────

    def save_checklists(
        self,
        hg_code: str,
        pre_checklist: list[str],
        post_checklist: list[str],
        verify_checklist: list[str],
    ) -> None:
        """チェックリスト3種を保存する。"""
        cfg = hg_config_store.get_config(hg_code)
        cfg["pre_checklist"] = pre_checklist
        cfg["post_checklist"] = post_checklist
        cfg["verify_checklist"] = verify_checklist
        hg_config_store.set_config(hg_code, cfg)

    def save_documents(
        self,
        hg_code: str,
        pre_documents: list[dict[str, str]],
        post_documents: list[dict[str, str]],
    ) -> None:
        """分析前・分析後ドキュメント一覧を保存する。"""
        cfg = hg_config_store.get_config(hg_code)
        cfg["pre_documents"] = pre_documents
        cfg["post_documents"] = post_documents
        hg_config_store.set_config(hg_code, cfg)

    def get_manual_html(self, hg_code: str) -> str | None:
        return hg_config_store.get_manual_html(hg_code)

    def upload_manual(self, hg_code: str, source_path: Path) -> str | None:
        """HTMLファイルをコピーして登録する。エラー時はメッセージを返す。"""
        if not source_path.exists():
            return "ファイルが見つかりません。"
        try:
            content = source_path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            return "ファイルの読み込みに失敗しました。"
        hg_config_store.set_manual_html(hg_code, content)
        return None

    def delete_manual(self, hg_code: str) -> None:
        hg_config_store.delete_manual_html(hg_code)
