"""データ表示設定の永続化層。

data_config.json に列の表示/非表示・表示名を保存する。
"""
from __future__ import annotations

import json

import app.config as _cfg


def _config_path():
    return _cfg.DATA_PATH / "bunseki" / "config" / "data_config.json"


def _ensure() -> None:
    _config_path().parent.mkdir(parents=True, exist_ok=True)


def load() -> dict:
    """データ表示設定を読み込む。"""
    _ensure()
    if not _config_path().exists():
        return {}
    try:
        return json.loads(_config_path().read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}


def save(data: dict) -> None:
    """データ表示設定を保存する。"""
    _ensure()
    _config_path().write_text(
        json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8"
    )
