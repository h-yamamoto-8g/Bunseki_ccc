"""HTMLマニュアルの永続化層。

manuals/ ディレクトリにHTMLファイルとメタデータJSONを保存する。
"""
from __future__ import annotations

import json
from pathlib import Path

from app.config import DATA_PATH

MANUALS_DIR = DATA_PATH / "bunseki" / "manuals"
MANUALS_META = MANUALS_DIR / "manuals.json"


def _ensure() -> None:
    MANUALS_DIR.mkdir(parents=True, exist_ok=True)


def load_meta() -> dict[str, str]:
    """メタデータ（キー→ファイル名マッピング）を読み込む。"""
    _ensure()
    if not MANUALS_META.exists():
        return {}
    try:
        return json.loads(MANUALS_META.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}


def save_meta(meta: dict[str, str]) -> None:
    """メタデータを保存する。"""
    _ensure()
    MANUALS_META.write_text(
        json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8"
    )


def get_html(key: str) -> str | None:
    """キーに対応するHTMLファイルの内容を返す。未登録なら None。"""
    meta = load_meta()
    filename = meta.get(key)
    if not filename:
        return None
    path = MANUALS_DIR / filename
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
    (MANUALS_DIR / filename).write_text(html_content, encoding="utf-8")
    meta = load_meta()
    meta[key] = filename
    save_meta(meta)


def delete_html(key: str) -> None:
    """HTMLファイルを削除し、メタデータから除去する。"""
    meta = load_meta()
    filename = meta.pop(key, None)
    if filename:
        path = MANUALS_DIR / filename
        if path.exists():
            path.unlink()
    save_meta(meta)
