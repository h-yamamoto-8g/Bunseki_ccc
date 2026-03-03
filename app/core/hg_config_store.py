"""ホルダグループ別設定の永続化層。

hg_config.json にチェックリスト等の設定を保存し、
hg_manuals/ にホルダグループ別HTMLマニュアルを保存する。
"""
from __future__ import annotations

import json
from pathlib import Path

import app.config as _cfg


def _config_path():
    return _cfg.DATA_PATH / "bunseki" / "config" / "hg_config.json"


def _manuals_dir():
    return _cfg.DATA_PATH / "bunseki" / "config" / "hg_manuals"


def _ensure() -> None:
    _config_path().parent.mkdir(parents=True, exist_ok=True)
    _manuals_dir().mkdir(parents=True, exist_ok=True)


# ── JSON 設定 ──────────────────────────────────────────────────────────────

def load_all() -> dict[str, dict]:
    """全ホルダグループの設定を読み込む。"""
    _ensure()
    if not _config_path().exists():
        return {}
    try:
        return json.loads(_config_path().read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}


def save_all(data: dict[str, dict]) -> None:
    """全ホルダグループの設定を保存する。"""
    _ensure()
    _config_path().write_text(
        json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8"
    )


def get_config(hg_code: str) -> dict:
    """指定ホルダグループの設定を返す（存在しない場合は空dict）。"""
    return load_all().get(hg_code, {})


def set_config(hg_code: str, config: dict) -> None:
    """指定ホルダグループの設定を保存する。"""
    data = load_all()
    data[hg_code] = config
    save_all(data)


# ── HTMLマニュアル ─────────────────────────────────────────────────────────

def get_manual_html(hg_code: str) -> str | None:
    """ホルダグループのHTMLマニュアルを返す。未登録なら None。"""
    _ensure()
    path = _manuals_dir() / f"{hg_code}.html"
    if not path.exists():
        return None
    try:
        return path.read_text(encoding="utf-8")
    except OSError:
        return None


def set_manual_html(hg_code: str, html_content: str) -> None:
    """ホルダグループのHTMLマニュアルを保存する。"""
    _ensure()
    (_manuals_dir() / f"{hg_code}.html").write_text(html_content, encoding="utf-8")


def delete_manual_html(hg_code: str) -> None:
    """ホルダグループのHTMLマニュアルを削除する。"""
    path = _manuals_dir() / f"{hg_code}.html"
    if path.exists():
        path.unlink()


def has_manual(hg_code: str) -> bool:
    """マニュアルが登録済みか返す。"""
    return (_manuals_dir() / f"{hg_code}.html").exists()
