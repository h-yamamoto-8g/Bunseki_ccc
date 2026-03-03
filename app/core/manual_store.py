"""HTMLマニュアルの永続化層。

manuals/ ディレクトリにHTMLファイルとメタデータJSONを保存する。
"""
from __future__ import annotations

import json
from pathlib import Path

import app.config as _cfg


def _manuals_dir():
    return _cfg.DATA_PATH / "bunseki" / "manuals"


def _ensure() -> None:
    _manuals_dir().mkdir(parents=True, exist_ok=True)


def load_meta() -> dict[str, str]:
    """メタデータ（キー→ファイル名マッピング）を読み込む。"""
    _ensure()
    meta_path = _manuals_dir() / "manuals.json"
    if not meta_path.exists():
        return {}
    try:
        return json.loads(meta_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}


def save_meta(meta: dict[str, str]) -> None:
    """メタデータを保存する。"""
    _ensure()
    (_manuals_dir() / "manuals.json").write_text(
        json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8"
    )


def get_html(key: str) -> str | None:
    """キーに対応するHTMLファイルの内容を返す。未登録なら None。"""
    meta = load_meta()
    filename = meta.get(key)
    if not filename:
        return None
    path = _manuals_dir() / filename
    if not path.exists():
        return None
    try:
        return path.read_text(encoding="utf-8")
    except OSError:
        return None


def set_html(key: str, html_content: str) -> None:
    """HTMLファイルを保存し、メタデータを更新する。"""
    _ensure()
    category, name = key.split(":", 1)
    filename = f"{category}_{name}.html"
    (_manuals_dir() / filename).write_text(html_content, encoding="utf-8")
    meta = load_meta()
    meta[key] = filename
    save_meta(meta)


def delete_html(key: str) -> None:
    """HTMLファイルを削除し、メタデータから除去する。"""
    meta = load_meta()
    filename = meta.pop(key, None)
    if filename:
        path = _manuals_dir() / filename
        if path.exists():
            path.unlink()
    save_meta(meta)
