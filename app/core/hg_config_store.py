"""ホルダグループ別設定の永続化層。

hg_config.json にチェックリスト等の設定を保存し、
hg_manuals/ にホルダグループ別HTMLマニュアルを保存する。
"""
from __future__ import annotations

import json
from pathlib import Path

from app.config import DATA_PATH

HG_CONFIG_PATH = DATA_PATH / "bunseki" / "config" / "hg_config.json"
HG_MANUALS_DIR = DATA_PATH / "bunseki" / "config" / "hg_manuals"


def _ensure() -> None:
    HG_CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    HG_MANUALS_DIR.mkdir(parents=True, exist_ok=True)


# ── JSON 設定 ──────────────────────────────────────────────────────────────

def load_all() -> dict[str, dict]:
    """全ホルダグループの設定を読み込む。"""
    _ensure()
    if not HG_CONFIG_PATH.exists():
        return {}
    try:
        return json.loads(HG_CONFIG_PATH.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}


def save_all(data: dict[str, dict]) -> None:
    """全ホルダグループの設定を保存する。"""
    _ensure()
    HG_CONFIG_PATH.write_text(
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
    path = HG_MANUALS_DIR / f"{hg_code}.html"
    if not path.exists():
        return None
    try:
        return path.read_text(encoding="utf-8")
    except OSError:
        return None


def set_manual_html(hg_code: str, html_content: str) -> None:
    """ホルダグループのHTMLマニュアルを保存する。"""
    _ensure()
    (HG_MANUALS_DIR / f"{hg_code}.html").write_text(html_content, encoding="utf-8")


def delete_manual_html(hg_code: str) -> None:
    """ホルダグループのHTMLマニュアルを削除する。"""
    path = HG_MANUALS_DIR / f"{hg_code}.html"
    if path.exists():
        path.unlink()


def has_manual(hg_code: str) -> bool:
    """マニュアルが登録済みか返す。"""
    return (HG_MANUALS_DIR / f"{hg_code}.html").exists()
