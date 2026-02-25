"""
master_loader

役割:
- valid_*.json / holder_groups.json を読み込み、正規化に必要な辞書（逆引き）を構築する
- 同一 code が複数 set_code に属する「重複所属」を処理開始前に検出し停止する

手順:
1) 各JSON（schema_version, updated_at, items[]）から items[] を取得
2) sample/holder/test: code -> set_code の逆引き辞書を構築（重複所属は MasterDataError）
3) sample/holder/test: set_code -> domain_code を構築（extract時の domain_filter に使う）
4) holder_group: valid_holder_set_code -> holder_group_code の逆引きを構築（重複は MasterDataError）
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from typing import Any, Dict, List, Tuple

from .errors import MasterDataError


@dataclass(frozen=True)
class MasterData:
    """役割: 正規化・抽出に必要な辞書群をまとめる"""

    sample_code_to_set: Dict[str, str]
    holder_code_to_set: Dict[str, str]
    test_code_to_set: Dict[str, str]

    sample_set_to_domain: Dict[str, str]
    holder_set_to_domain: Dict[str, str]
    test_set_to_domain: Dict[str, str]

    holder_set_to_group: Dict[str, str]


def _read_items(path: str) -> List[dict[str, Any]]:
    """役割: master JSON を読み込み items[] を返す（形式不正は例外）"""
    with open(path, "r", encoding="utf-8") as f:
        obj = json.load(f)

    if not isinstance(obj, dict) or "items" not in obj or not isinstance(obj["items"], list):
        raise MasterDataError(f"Invalid master json format (missing items[]): {path}")

    return obj["items"]


def _build_reverse_map(items: List[dict[str, Any]], list_key: str) -> Dict[str, str]:
    """
    役割:
    - *_codes[] を逆引きし code -> set_code を作る
    - 同一 code が複数 set_code に所属する場合は MasterDataError

    手順:
    1) items を走査し set_code と codes[] を取得
    2) code が既に別 set_code で登録済みなら重複所属として停止
    """
    mapping: Dict[str, str] = {}
    dups: List[Tuple[str, str, str]] = []

    for it in items:
        if "set_code" not in it:
            raise MasterDataError(f"Missing set_code in items (key={list_key})")
        set_code = str(it["set_code"])

        codes = it.get(list_key, [])
        if not isinstance(codes, list):
            raise MasterDataError(f"Invalid {list_key} (not list) in set_code={set_code}")

        for c in codes:
            code = str(c)
            if code in mapping and mapping[code] != set_code:
                dups.append((code, mapping[code], set_code))
            else:
                mapping[code] = set_code

    if dups:
        code, a, b = dups[0]
        raise MasterDataError(f"Duplicate code detected: {code} appears in multiple set_code: [{a}, {b}]")

    return mapping


def _build_set_to_domain(items: List[dict[str, Any]]) -> Dict[str, str]:
    """役割: set_code -> domain_code を作る（domain_code が無い場合は空文字）"""
    out: Dict[str, str] = {}
    for it in items:
        set_code = str(it.get("set_code", ""))
        if not set_code:
            continue
        out[set_code] = str(it.get("domain_code", ""))
    return out


def load_master_data(master_dir: str) -> MasterData:
    """
    役割:
    - master_data/source 配下のJSONを読み、MasterData を返す

    手順:
    1) valid_samples / valid_holders / valid_tests / holder_groups の items[] を取得
    2) 逆引き辞書群を構築
    3) holder_group の逆引き辞書を構築（重複は停止）
    """
    samples = _read_items(os.path.join(master_dir, "valid_samples.json"))
    holders = _read_items(os.path.join(master_dir, "valid_holders.json"))
    tests = _read_items(os.path.join(master_dir, "valid_tests.json"))
    groups = _read_items(os.path.join(master_dir, "holder_groups.json"))

    sample_code_to_set = _build_reverse_map(samples, "sample_codes")
    holder_code_to_set = _build_reverse_map(holders, "holder_codes")
    test_code_to_set = _build_reverse_map(tests, "test_codes")

    sample_set_to_domain = _build_set_to_domain(samples)
    holder_set_to_domain = _build_set_to_domain(holders)
    test_set_to_domain = _build_set_to_domain(tests)

    holder_set_to_group: Dict[str, str] = {}
    group_dups: List[Tuple[str, str, str]] = []
    for g in groups:
        g_code = str(g.get("holder_group_code", ""))
        if not g_code:
            raise MasterDataError("Missing holder_group_code in holder_groups.json items[]")

        set_codes = g.get("valid_holder_set_codes", [])
        if not isinstance(set_codes, list):
            raise MasterDataError(f"Invalid valid_holder_set_codes (not list) in group={g_code}")

        for sc in set_codes:
            set_code = str(sc)
            if set_code in holder_set_to_group and holder_set_to_group[set_code] != g_code:
                group_dups.append((set_code, holder_set_to_group[set_code], g_code))
            else:
                holder_set_to_group[set_code] = g_code

    if group_dups:
        set_code, a, b = group_dups[0]
        raise MasterDataError(f"Duplicate holder_group mapping: {set_code} in [{a}, {b}]")

    return MasterData(
        sample_code_to_set=sample_code_to_set,
        holder_code_to_set=holder_code_to_set,
        test_code_to_set=test_code_to_set,
        sample_set_to_domain=sample_set_to_domain,
        holder_set_to_domain=holder_set_to_domain,
        test_set_to_domain=test_set_to_domain,
        holder_set_to_group=holder_set_to_group,
    )
