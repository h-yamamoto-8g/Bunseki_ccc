"""
normalize_service

役割:
- full.csv を読み、以下列を付与して full_normalized.csv を生成する
  - valid_sample_set_code
  - valid_holder_set_code
  - valid_test_set_code
  - holder_group_code
  - test_domain_code（extractのフィルタ簡略化・検証容易化のため追加）

手順:
1) CSVを1行ずつ読み込む（ストリーム）
2) sample_code/holder_code/test_code を逆引き辞書で set_code に変換
3) unknown_policy=unknown の場合、未知は "UNKNOWN" を入れて継続
4) holder_group_code を valid_holder_set_code から付与（未知は UNKNOWN/UNGROUPED）
5) test_domain_code を valid_test_set_code から付与
6) 元の行＋追加列を出力CSVへ書き込む
"""

from __future__ import annotations

import csv
import os
from typing import Dict, List

from .errors import InputError
from .master_loader import MasterData


def _map_code(code: str, mapping: Dict[str, str], unknown_policy: str, counter: Dict[str, int], key: str) -> str:
    """
    役割:
    - code を set_code に写像する（未知時の挙動を unknown_policy で制御）

    手順:
    1) mappingにあれば set_code
    2) なければカウント加算し、unknown_policy に従って値を返す
    """
    if code in mapping:
        return mapping[code]

    counter[key] += 1
    if unknown_policy == "unknown":
        return "UNKNOWN"
    if unknown_policy == "empty":
        return ""
    # unknown_policy="error" は今回は採用しないが拡張余地として残す
    raise ValueError(f"Unknown code ({key}): {code}")


def normalize_full_csv(
    in_csv: str,
    out_csv: str,
    master: MasterData,
    encoding: str,
    delimiter: str,
    unknown_policy: str = "unknown",
) -> Dict[str, object]:
    """
    役割:
    - full.csv を正規化して out_csv を生成する
    - unknown件数などの統計を返す（result.json 用）

    手順:
    1) 入力存在チェック
    2) DictReader/DictWriter でストリーム処理
    3) 追加列を付与して書き込み
    """
    if not os.path.isfile(in_csv):
        raise InputError(f"Input CSV not found: {in_csv}")

    os.makedirs(os.path.dirname(out_csv) or ".", exist_ok=True)

    unknown_counts = {"sample": 0, "holder": 0, "test": 0}
    input_rows = 0

    with open(in_csv, "r", encoding=encoding, newline="") as rf, open(out_csv, "w", encoding=encoding, newline="") as wf:
        reader = csv.DictReader(rf, delimiter=delimiter)

        # 追加列
        extra_cols = [
            "valid_sample_set_code",
            "valid_holder_set_code",
            "valid_test_set_code",
            "holder_group_code",
            "test_domain_code",
        ]
        fieldnames: List[str] = list(reader.fieldnames or [])
        for c in extra_cols:
            if c not in fieldnames:
                fieldnames.append(c)

        writer = csv.DictWriter(wf, fieldnames=fieldnames, delimiter=delimiter)
        writer.writeheader()

        for row in reader:
            input_rows += 1

            sample_code = str(row.get("sample_code", "")).strip()
            holder_code = str(row.get("holder_code", "")).strip()
            test_code = str(row.get("test_code", "")).strip()

            row["valid_sample_set_code"] = _map_code(sample_code, master.sample_code_to_set, unknown_policy, unknown_counts, "sample")
            row["valid_holder_set_code"] = _map_code(holder_code, master.holder_code_to_set, unknown_policy, unknown_counts, "holder")
            row["valid_test_set_code"] = _map_code(test_code, master.test_code_to_set, unknown_policy, unknown_counts, "test")

            # holder_group_code
            holder_set = row["valid_holder_set_code"]
            if holder_set in ("", "UNKNOWN"):
                row["holder_group_code"] = "UNKNOWN" if holder_set == "UNKNOWN" else ""
            else:
                row["holder_group_code"] = master.holder_set_to_group.get(holder_set, "UNGROUPED")

            # test_domain_code（extractで domain_code==WH を評価するため）
            test_set = row["valid_test_set_code"]
            if test_set in ("", "UNKNOWN"):
                row["test_domain_code"] = ""
            else:
                row["test_domain_code"] = master.test_set_to_domain.get(test_set, "")

            writer.writerow(row)

    return {
        "input_rows": input_rows,
        "unknown_counts": unknown_counts,
    }
