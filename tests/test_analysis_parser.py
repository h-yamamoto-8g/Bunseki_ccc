"""analysis_parser モジュールのユニットテスト。"""
from __future__ import annotations

import csv
import tempfile
from pathlib import Path

import pytest

from app.core.analysis_parser import (
    execute_parser,
    validate_parser_code,
)


# ── validate_parser_code テスト ──────────────────────────────────────────────


class TestValidateParserCode:
    """validate_parser_code のテスト。"""

    def test_valid_code(self) -> None:
        """正常なパーサーコードがエラーなしで通過する。"""
        code = (
            "def parse(file_path: str) -> list[dict[str, str]]:\n"
            "    return []\n"
        )
        errors = validate_parser_code(code)
        assert errors == []

    def test_missing_parse_function(self) -> None:
        """parse 関数がない場合にエラーを返す。"""
        code = "def foo(x): return x\n"
        errors = validate_parser_code(code)
        assert any("parse(file_path)" in e for e in errors)

    def test_wrong_args(self) -> None:
        """parse の引数が正しくない場合にエラーを返す。"""
        code = "def parse(a, b): return []\n"
        errors = validate_parser_code(code)
        assert any("引数" in e for e in errors)

    def test_syntax_error(self) -> None:
        """構文エラーがあるコード。"""
        code = "def parse(file_path):\n    return [\n"
        errors = validate_parser_code(code)
        assert any("構文エラー" in e for e in errors)

    def test_forbidden_module_subprocess(self) -> None:
        """subprocess の import を禁止する。"""
        code = (
            "import subprocess\n"
            "def parse(file_path: str) -> list[dict[str, str]]:\n"
            "    return []\n"
        )
        errors = validate_parser_code(code)
        assert any("subprocess" in e for e in errors)

    def test_forbidden_module_from_import(self) -> None:
        """from subprocess import の形式も禁止する。"""
        code = (
            "from subprocess import run\n"
            "def parse(file_path: str) -> list[dict[str, str]]:\n"
            "    return []\n"
        )
        errors = validate_parser_code(code)
        assert any("subprocess" in e for e in errors)

    def test_forbidden_call_eval(self) -> None:
        """eval() の呼び出しを禁止する。"""
        code = (
            "def parse(file_path: str) -> list[dict[str, str]]:\n"
            "    return eval('[]')\n"
        )
        errors = validate_parser_code(code)
        assert any("eval" in e for e in errors)

    def test_forbidden_os_system(self) -> None:
        """os.system() の呼び出しを禁止する。"""
        code = (
            "import os\n"
            "def parse(file_path: str) -> list[dict[str, str]]:\n"
            "    os.system('ls')\n"
            "    return []\n"
        )
        errors = validate_parser_code(code)
        assert any("os.system" in e for e in errors)

    def test_allowed_module_csv(self) -> None:
        """csv モジュールの import は許可する。"""
        code = (
            "import csv\n"
            "def parse(file_path: str) -> list[dict[str, str]]:\n"
            "    return []\n"
        )
        errors = validate_parser_code(code)
        assert errors == []

    def test_allowed_module_pandas(self) -> None:
        """pandas の import は許可する。"""
        code = (
            "import pandas\n"
            "def parse(file_path: str) -> list[dict[str, str]]:\n"
            "    return []\n"
        )
        errors = validate_parser_code(code)
        assert errors == []

    def test_allowed_module_pdfplumber(self) -> None:
        """pdfplumber の import は許可する。"""
        code = (
            "import pdfplumber\n"
            "def parse(file_path: str) -> list[dict[str, str]]:\n"
            "    return []\n"
        )
        errors = validate_parser_code(code)
        assert errors == []

    def test_unlisted_module(self) -> None:
        """許可リスト外のモジュールでエラーを返す。"""
        code = (
            "import sqlite3\n"
            "def parse(file_path: str) -> list[dict[str, str]]:\n"
            "    return []\n"
        )
        errors = validate_parser_code(code)
        assert any("sqlite3" in e for e in errors)


# ── execute_parser テスト ────────────────────────────────────────────────────


class TestExecuteParser:
    """execute_parser のテスト。"""

    def _make_csv(self, rows: list[dict[str, str]]) -> str:
        """テスト用の一時CSVファイルを作成する。"""
        tmp = tempfile.NamedTemporaryFile(
            mode="w", suffix=".csv", delete=False,
            newline="", encoding="utf-8",
        )
        writer = csv.DictWriter(tmp, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
        tmp.close()
        return tmp.name

    def test_basic_csv_parser(self) -> None:
        """基本的なCSVパーサーが正しく動作する。"""
        csv_path = self._make_csv([
            {"name": "DW1", "pH": "7.2", "COD": "15.3"},
            {"name": "DW2", "pH": "6.8", "COD": "12.1"},
        ])
        code = (
            "def parse(file_path: str) -> list[dict[str, str]]:\n"
            "    import csv\n"
            "    results = []\n"
            "    with open(file_path, encoding='utf-8') as f:\n"
            "        for row in csv.DictReader(f):\n"
            "            results.append({\n"
            "                'sample_name': row['name'],\n"
            "                'pH': row['pH'],\n"
            "                'COD': row['COD'],\n"
            "            })\n"
            "    return results\n"
        )
        result = execute_parser(code, csv_path)
        assert len(result) == 2
        assert result[0]["sample_name"] == "DW1"
        assert result[0]["pH"] == "7.2"
        assert result[1]["COD"] == "12.1"
        Path(csv_path).unlink()

    def test_invalid_return_type_not_list(self) -> None:
        """戻り値が list でない場合に TypeError を送出する。"""
        code = (
            "def parse(file_path: str):\n"
            "    return 'not a list'\n"
        )
        with pytest.raises(TypeError, match="list"):
            execute_parser(code, "dummy.csv")

    def test_invalid_return_type_not_dict(self) -> None:
        """リスト要素が dict でない場合に TypeError を送出する。"""
        code = (
            "def parse(file_path: str):\n"
            "    return ['not a dict']\n"
        )
        with pytest.raises(TypeError, match="dict"):
            execute_parser(code, "dummy.csv")

    def test_invalid_return_type_value_not_str(self) -> None:
        """dict 値が str でない場合に TypeError を送出する。"""
        code = (
            "def parse(file_path: str):\n"
            "    return [{'key': 123}]\n"
        )
        with pytest.raises(TypeError, match="str"):
            execute_parser(code, "dummy.csv")

    def test_missing_parse_function(self) -> None:
        """parse 関数がない場合に ValueError を送出する。"""
        code = "x = 1\n"
        with pytest.raises(ValueError, match="parse"):
            execute_parser(code, "dummy.csv")

    def test_empty_result(self) -> None:
        """空リストを返すパーサー。"""
        code = (
            "def parse(file_path: str) -> list[dict[str, str]]:\n"
            "    return []\n"
        )
        result = execute_parser(code, "dummy.csv")
        assert result == []
