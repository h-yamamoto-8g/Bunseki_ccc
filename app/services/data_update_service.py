"""
データ更新・正規化サービス。

起動時およびデータ入力ステートの「データ更新」ボタン押下時に呼び出す。

責務:
    - 外部 Extractor ツール（lab_aid_extract.exe）を実行して「最新年」の生データCSVを取得する
    - 外部 ETL ツール（lab_aid_etl.exe）を実行して正規化済み bunseki.csv を生成する
    - 異常時は統一例外を送出する

設計方針:
    - UIはこのサービスの例外のみ扱う（UIに subprocess / パス解決の詳細を漏らさない）
    - subprocess 等のOS操作は本サービス内で完結させる
    - 外部ツールの戻り値は「終了コード + result.json（Extractor）」を正とする
"""

from __future__ import annotations

import json
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Final, Optional

# Windows で子プロセスのコンソールウィンドウを表示しない
_CREATE_NO_WINDOW: Final[int] = 0x08000000 if sys.platform == "win32" else 0

from app.config import DATA_PATH


# ── 実行フラグ ──────────────────────────────────────────────────────────────
# True  : 実行する
# False : スキップ（ツール未準備のため一時無効化）
ENABLED: bool = True


# ── 外部ツール設定 ──────────────────────────────────────────────────────────
# Extractor（Lab-AidからCSVを出す）
EXTRACTOR_EXE_PATH: Final[Path] = (
    DATA_PATH / "_common" / "tools" / "lab_aid_extractor" / "dist" / "lab_aid_extract.exe"
)

# Extractor が操作する xlsm（dist に同梱している前提。別運用なら絶対パスに変更）
EXTRACTOR_XLSM_PATH: Final[Path] = (
    DATA_PATH / "_common" / "tools" / "lab_aid_extractor" / "dist" / "lab_aid_extractor.xlsm"
)

# Extractor の result.json（exe フォルダに出すより、ログ管理しやすい場所へ固定推奨）
EXTRACTOR_RESULT_JSON_PATH: Final[Path] = (
    DATA_PATH / "_common" / "tools" / "lab_aid_extractor" / "dist" / "result.json"
)

# 生データCSVの出力先（必要ならアプリ側のデータ配置ルールに合わせて変更）
RAW_OUT_DIR: Final[Path] = DATA_PATH / "_common" / "data" / "lab_aid" / "raw"

# domain_code（最低限 WH を想定。運用で複数あるなら呼び出し側で可変にする）
DOMAIN_CODE: Final[str] = "WH"

# ETL（merge/normalize/build）
ETL_EXE_PATH: Final[Path] = (
    DATA_PATH / "_common" / "tools" / "lab_aid_etl" / "dist" / "lab_aid_etl.exe"
)
PROFILE_NAME: Final[str] = "bunseki"


# ── 例外定義 ────────────────────────────────────────────────────────────────
class DataUpdateError(Exception):
    """データ取得処理エラー（Extractor系）"""


class NormalizationError(Exception):
    """正規化処理エラー（ETL系）"""


# ── Extractor result.json モデル（最低限） ─────────────────────────────────
@dataclass(frozen=True)
class ExtractorResult:
    """
    役割:
        - Extractor が出力する result.json をアプリ側で扱いやすくする DTO。
    手順:
        - json を dict として読み込み、必要キーだけ取り出す。
    """

    ok: bool
    message: str
    csv_path: Optional[str]
    details: dict[str, Any]

    @staticmethod
    def from_json(path: Path) -> "ExtractorResult":
        # 何をしているか:
        # - result.json を読み込み、想定キーが無い場合も落ちないように default を設定して取り出す。
        data = json.loads(path.read_text(encoding="utf-8"))
        return ExtractorResult(
            ok=bool(data.get("ok", False)),
            message=str(data.get("message", "")),
            csv_path=data.get("csv_path"),
            details=dict(data.get("details", {}) or {}),
        )


# ── データ取得（Extractor実行） ─────────────────────────────────────────────
def run_data_update(domain_code: str = DOMAIN_CODE) -> None:
    """
    データソース（Lab-Aid）から最新データを取得し、ローカルに保存する。

    役割:
        - lab_aid_extract.exe を起動し、最新年（= 現在年）のCSVを出力させる。
        - result.json を読み取り、失敗時は DataUpdateError を送出する。

    手順:
        1) 実行フラグを確認
        2) 必要ファイル（exe/xlsm）と出力先フォルダの存在を確認
        3) 実行前の result.json の mtime を控える（削除できないケースの誤判定防止）
        4) Extractor を subprocess で実行（--domain-code, --year, --xlsm-path, --out-dir, --result-json）
        5) result.json が生成/更新されたことを確認し、ok=false なら DataUpdateError
    """
    if not ENABLED:
        return

    # 「最新年」= 現在年（運用定義。年度運用にするならここを差し替える）
    year = datetime.now().year

    exe_path = EXTRACTOR_EXE_PATH
    xlsm_path = EXTRACTOR_XLSM_PATH
    out_dir = RAW_OUT_DIR
    result_json = EXTRACTOR_RESULT_JSON_PATH

    # --- 1) パスの存在確認 ---------------------------------------------------
    if not exe_path.exists():
        raise DataUpdateError(f"Extractor exe が見つかりません: {exe_path}")

    if not xlsm_path.exists():
        raise DataUpdateError(f"Extractor xlsm が見つかりません: {xlsm_path}")

    out_dir.mkdir(parents=True, exist_ok=True)
    result_json.parent.mkdir(parents=True, exist_ok=True)

    # --- 2) 実行前の状態を記録（古い result.json 読み込み誤判定を防ぐ） ----------
    before_mtime = result_json.stat().st_mtime if result_json.exists() else None

    # 古い result.json が残って誤判定しないように削除（できれば削除）
    if result_json.exists():
        try:
            result_json.unlink()
            before_mtime = None  # 消せたなら「前回結果」は存在しない扱いにする
        except OSError:
            # 削除できない場合は mtime 比較で「更新されたか」を必ず見る
            pass

    # --- 3) コマンド組み立て -------------------------------------------------
    # 何をしているか:
    # - Extractor の CLI 仕様（main.py の argparse）に合わせて引数を渡す。
    cmd = [
        str(exe_path),
        "--domain-code",
        domain_code,
        "--year",
        str(year),
        "--xlsm-path",
        str(xlsm_path),
        "--out-dir",
        str(out_dir),
        "--result-json",
        str(result_json),
    ]

    # --- 4) 実行 -------------------------------------------------------------
    try:
        # 何をしているか:
        # - capture_output=True で stdout/stderr を回収し、失敗時に例外メッセージへ含める。
        proc = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=False,
            cwd=str(exe_path.parent),
            creationflags=_CREATE_NO_WINDOW,
        )
    except Exception as e:
        raise DataUpdateError(f"Extractor実行失敗: {e}") from e

    # --- 5) result.json を優先して判定 --------------------------------------
    if not result_json.exists():
        # result.json が出ないのはツール側の異常（起動失敗/権限/クラッシュ等）
        raise DataUpdateError(
            "Extractorのresult.jsonが生成されませんでした。\n"
            f"returncode={proc.returncode}\n"
            f"stdout:\n{proc.stdout}\n"
            f"stderr:\n{proc.stderr}"
        )

    after_mtime = result_json.stat().st_mtime
    if before_mtime is not None and after_mtime == before_mtime:
        raise DataUpdateError("Extractorのresult.jsonが更新されていません（古い結果の可能性）")

    extractor_result = ExtractorResult.from_json(result_json)

    if not extractor_result.ok:
        raise DataUpdateError(
            "Extractorが失敗しました。\n"
            f"message: {extractor_result.message}\n"
            f"details: {extractor_result.details}"
        )

    if not extractor_result.csv_path:
        raise DataUpdateError(
            "Extractorは成功扱いですが csv_path が空です。\n"
            f"message: {extractor_result.message}\n"
            f"details: {extractor_result.details}"
        )

    csv_path = Path(extractor_result.csv_path)
    if not csv_path.exists():
        raise DataUpdateError(f"Extractor出力CSVが見つかりません: {csv_path}")


# ── 正規化処理（ETL実行） ───────────────────────────────────────────────────
import os

def run_normalization() -> None:
    if not ENABLED:
        return

    exe_path = ETL_EXE_PATH
    if not exe_path.exists():
        raise NormalizationError(f"ETL exe が見つかりません: {exe_path}")

    cmd = [str(exe_path), "build", "--profile", PROFILE_NAME]
    cwd = str(exe_path.parent)  # dist を想定

    proc = subprocess.run(
        cmd,
        cwd=cwd,                 # ★これが重要
        capture_output=True,
        text=True,
        check=False,
        env=os.environ.copy(),   # 念のため明示
        creationflags=_CREATE_NO_WINDOW,
    )

    if proc.returncode != 0:
        raise NormalizationError(
            f"ETL異常終了 (code={proc.returncode})\n"
            f"cmd={cmd}\n"
            f"cwd={cwd}\n"
            f"stdout:\n{proc.stdout}\n"
            f"stderr:\n{proc.stderr}"
        )


# ── 一括実行 ─────────────────────────────────────────────────────────────────
def run_all(domain_code: str = DOMAIN_CODE) -> None:
    """
    データ更新と正規化を順番に実行する。

    役割:
        - 「データ更新」ボタン等から呼び出す統一入口。
    手順:
        1) run_data_update(domain_code)
        2) run_normalization()
    """
    if not ENABLED:
        return

    run_data_update(domain_code=domain_code)
    run_normalization()