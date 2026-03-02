"""HTMLマニュアル管理のサービス層。Core(manual_store)のみに依存。"""
from __future__ import annotations

from pathlib import Path

from app.core import manual_store

# 管理対象の全エントリ定義
_ENTRIES: list[tuple[str, str, str]] = [
    # (key, category_label, display_name)
    ("page:home",     "ページ", "ホーム"),
    ("page:tasks",    "ページ", "タスク"),
    ("page:data",     "ページ", "データ"),
    ("page:news",     "ページ", "ニュース"),
    ("page:library",  "ページ", "ライブラリ"),
    ("page:log",      "ページ", "ログ"),
    ("page:job",      "ページ", "ジョブ"),
    ("page:settings", "ページ", "設定"),
    ("state:task_setup",          "ステート", "起票"),
    ("state:analysis_targets",    "ステート", "分析対象"),
    ("state:analysis",            "ステート", "分析準備"),
    ("state:result_entry",        "ステート", "データ入力"),
    ("state:result_verification", "ステート", "データ確認"),
    ("state:submission",          "ステート", "回覧"),
    ("state:completed",           "ステート", "終了"),
]


class ManualService:
    """HTMLマニュアル管理サービス。"""

    def get_all_entries(self) -> list[dict]:
        """全15エントリの一覧を返す（登録状況付き）。"""
        meta = manual_store.load_meta()
        result = []
        for key, category, name in _ENTRIES:
            result.append({
                "key": key,
                "category": category,
                "name": name,
                "registered": key in meta,
            })
        return result

    def get_manual_html(self, key: str) -> str | None:
        """キーに対応するマニュアルHTMLを返す。"""
        return manual_store.get_html(key)

    def upload_manual(self, key: str, source_path: Path) -> str | None:
        """HTMLファイルをコピーして登録する。エラー時はメッセージを返す。"""
        if not source_path.exists():
            return "ファイルが見つかりません。"
        try:
            content = source_path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            return "ファイルの読み込みに失敗しました。"
        manual_store.set_html(key, content)
        return None

    def delete_manual(self, key: str) -> str | None:
        """マニュアルを削除する。エラー時はメッセージを返す。"""
        try:
            manual_store.delete_html(key)
        except OSError:
            return "削除に失敗しました。"
        return None
