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
