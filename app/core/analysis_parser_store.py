"""分析結果パーサーの永続化層。

ホルダグループごとのパーサースクリプトおよびマッピング設定を保存する。

保存先:
    - パーサーコード: DATA_PATH/bunseki/config/analysis_parsers/{hg_code}.py
    - マッピング設定: hg_config.json 内の analysis_parser セクション
"""
from __future__ import annotations

import json
import logging
import shutil
from pathlib import Path

import app.config as _cfg
from app.core import hg_config_store

logger = logging.getLogger(__name__)


def _parsers_dir() -> Path:
    """パーサースクリプトの保存ディレクトリを返す。"""
    return _cfg.DATA_PATH / "bunseki" / "config" / "analysis_parsers"


def _attachments_dir() -> Path:
    """分析結果ファイルの添付保存ディレクトリを返す。"""
    return _cfg.DATA_PATH / "bunseki" / "attachments" / "analysis_results"


def _ensure() -> None:
    """必要なディレクトリを作成する。"""
    _parsers_dir().mkdir(parents=True, exist_ok=True)
    _attachments_dir().mkdir(parents=True, exist_ok=True)


# ── パーサーコード ────────────────────────────────────────────────────────────


def get_parser_code(hg_code: str) -> str | None:
    """指定ホルダグループのパーサーコードを返す。未登録なら None。

    Args:
        hg_code: ホルダグループコード。

    Returns:
        パーサーの Python ソースコード、または None。
    """
    _ensure()
    path = _parsers_dir() / f"{hg_code}.py"
    if not path.exists():
        return None
    try:
        return path.read_text(encoding="utf-8")
    except OSError:
        logger.exception("パーサーコードの読み込みに失敗: %s", hg_code)
        return None


def save_parser_code(hg_code: str, code: str) -> None:
    """パーサーコードを保存する。

    Args:
        hg_code: ホルダグループコード。
        code: Python ソースコード文字列。
    """
    _ensure()
    path = _parsers_dir() / f"{hg_code}.py"
    path.write_text(code, encoding="utf-8")
    logger.info("パーサーコードを保存: %s", hg_code)


def delete_parser_code(hg_code: str) -> None:
    """パーサーコードを削除する。

    Args:
        hg_code: ホルダグループコード。
    """
    path = _parsers_dir() / f"{hg_code}.py"
    if path.exists():
        path.unlink()
        logger.info("パーサーコードを削除: %s", hg_code)


def has_parser(hg_code: str) -> bool:
    """パーサーが登録済みか返す。

    Args:
        hg_code: ホルダグループコード。
    """
    return (_parsers_dir() / f"{hg_code}.py").exists()


# ── マッピング設定 ────────────────────────────────────────────────────────────


def get_parser_config(hg_code: str) -> dict:
    """パーサーのマッピング設定を返す。

    Args:
        hg_code: ホルダグループコード。

    Returns:
        ``{"sample_name_key": str, "key_mapping": {json_key: {"holder_code": str, "test_code": str}}}``
        未設定なら空の構造を返す。
    """
    cfg = hg_config_store.get_config(hg_code)
    return cfg.get(
        "analysis_parser",
        {"sample_name_key": "", "key_mapping": {}},
    )


def save_parser_config(
    hg_code: str,
    sample_name_key: str,
    key_mapping: dict[str, dict[str, str]],
) -> None:
    """パーサーのマッピング設定を保存する。

    Args:
        hg_code: ホルダグループコード。
        sample_name_key: JSON内のサンプル名を示すキー。
        key_mapping: ``{json_key: {"holder_code": str, "test_code": str}}``。
    """
    cfg = hg_config_store.get_config(hg_code)
    cfg["analysis_parser"] = {
        "sample_name_key": sample_name_key,
        "key_mapping": key_mapping,
    }
    hg_config_store.set_config(hg_code, cfg)
    logger.info("パーサーマッピング設定を保存: %s", hg_code)


# ── 添付ファイル ──────────────────────────────────────────────────────────────


def save_attachment(task_id: str, source_path: str) -> Path:
    """分析結果ファイルを添付用ディレクトリにコピーして保存する。

    Args:
        task_id: タスクID。
        source_path: コピー元ファイルのパス。

    Returns:
        コピー先のパス。
    """
    _ensure()
    task_dir = _attachments_dir() / task_id
    task_dir.mkdir(parents=True, exist_ok=True)

    src = Path(source_path)
    dest = task_dir / src.name

    # 同名ファイルが既にある場合はサフィックスを付与
    counter = 1
    while dest.exists():
        dest = task_dir / f"{src.stem}_{counter}{src.suffix}"
        counter += 1

    shutil.copy2(str(src), str(dest))
    logger.info("分析結果ファイルを保存: %s → %s", source_path, dest)
    return dest


def get_attachments(task_id: str) -> list[Path]:
    """タスクに紐づく分析結果ファイル一覧を返す。

    Args:
        task_id: タスクID。

    Returns:
        添付ファイルのパスリスト。
    """
    task_dir = _attachments_dir() / task_id
    if not task_dir.exists():
        return []
    return sorted(task_dir.iterdir())
