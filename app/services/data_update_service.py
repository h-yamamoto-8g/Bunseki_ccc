"""データ更新・正規化サービス。

起動時およびデータ入力ステートの「データ更新」ボタン押下時に呼び出す。

# ── 実行フラグ ──────────────────────────────────────────────────────────────
# True  : 実行する
# False : スキップ（ツール未準備のため一時無効化）
# 実装完了後に True に切り替えること。
ENABLED = False
"""
from __future__ import annotations

# ── 実行フラグ ──────────────────────────────────────────────────────────────
# True  : 実行する
# False : スキップ（ツール未準備のため一時無効化）
ENABLED: bool = False


def run_data_update() -> None:
    """データソースから最新データを取得し、ローカルに保存する。

    TODO: 実装内容
        - データソース（Lab-Aid 等）から最新の分析データを取得する
        - 取得したデータを所定のディレクトリに保存する
    """
    if not ENABLED:
        return

    # TODO: データ取得処理を実装する
    raise NotImplementedError("run_data_update は未実装です")


def run_normalization() -> None:
    """取得済みデータを正規化フォーマットに変換し bunseki.csv を更新する。

    TODO: 実装内容
        - 取得したデータを正規化フォーマット（bunseki.csv スキーマ）に変換する
        - _common/data/lab_aid/normalized/bunseki.csv に書き出す
    """
    if not ENABLED:
        return

    # TODO: 正規化処理を実装する
    raise NotImplementedError("run_normalization は未実装です")


def run_all() -> None:
    """データ更新と正規化を順番に実行する。

    実行順序:
        1. run_data_update()  — データ取得
        2. run_normalization() — 正規化・CSV 書き出し

    ENABLED = False の場合は何もせずに返る。
    """
    if not ENABLED:
        return

    run_data_update()
    run_normalization()
