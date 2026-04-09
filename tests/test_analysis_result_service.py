"""analysis_result_service モジュールのユニットテスト。"""
from __future__ import annotations

import pytest

from app.services.analysis_result_service import AnalysisResultService


class TestFuzzyMatchSamples:
    """fuzzy_match_samples のテスト。"""

    def setup_method(self) -> None:
        self.service = AnalysisResultService()

    def test_exact_match(self) -> None:
        """完全一致で 1.0 スコアを返す。"""
        result = self.service.fuzzy_match_samples(["DW1"], ["DW1"])
        assert result["DW1"] == ("DW1", 1.0)

    def test_close_match(self) -> None:
        """類似文字列で高スコアを返す。"""
        result = self.service.fuzzy_match_samples(["DW1"], ["DW-1", "BL"])
        best_name, score = result["DW1"]
        assert best_name == "DW-1"
        assert score > 0.5

    def test_no_candidates(self) -> None:
        """候補がない場合は空文字・スコア0を返す。"""
        result = self.service.fuzzy_match_samples(["DW1"], [])
        assert result["DW1"] == ("", 0.0)

    def test_multiple_system_names(self) -> None:
        """複数のシステム名に対してそれぞれマッチする。"""
        result = self.service.fuzzy_match_samples(
            ["DW1", "DW2"],
            ["DW-1", "DW-2"],
        )
        assert result["DW1"][0] == "DW-1"
        assert result["DW2"][0] == "DW-2"

    def test_case_insensitive(self) -> None:
        """大文字小文字を区別しないマッチング。"""
        result = self.service.fuzzy_match_samples(["dw1"], ["DW1"])
        assert result["dw1"][0] == "DW1"
        assert result["dw1"][1] == 1.0


class TestApplyMapping:
    """apply_mapping のテスト。"""

    def setup_method(self) -> None:
        self.service = AnalysisResultService()

    def test_basic_mapping(self) -> None:
        """基本的なマッピングが正しく動作する。"""
        parsed_data = [
            {"sample_name": "DW1", "pH": "7.2", "COD": "15.3"},
            {"sample_name": "DW2", "pH": "6.8", "COD": "12.1"},
        ]
        sample_mapping = {"DW1_display": "DW1", "DW2_display": "DW2"}
        key_mapping = {
            "pH": {"holder_code": "H1", "test_code": "T_pH"},
            "COD": {"holder_code": "H1", "test_code": "T_COD"},
        }
        table_rows = [
            {
                "_row_key": "REQ1_H1_T_pH",
                "valid_sample_display_name": "DW1_display",
                "valid_holder_set_code": "H1",
                "valid_test_set_code": "T_pH",
            },
            {
                "_row_key": "REQ1_H1_T_COD",
                "valid_sample_display_name": "DW1_display",
                "valid_holder_set_code": "H1",
                "valid_test_set_code": "T_COD",
            },
            {
                "_row_key": "REQ2_H1_T_pH",
                "valid_sample_display_name": "DW2_display",
                "valid_holder_set_code": "H1",
                "valid_test_set_code": "T_pH",
            },
        ]
        result = self.service.apply_mapping(
            parsed_data, sample_mapping, key_mapping, "sample_name", table_rows,
        )
        assert result["REQ1_H1_T_pH"] == "7.2"
        assert result["REQ1_H1_T_COD"] == "15.3"
        assert result["REQ2_H1_T_pH"] == "6.8"

    def test_missing_mapping(self) -> None:
        """マッピングがない test_code の行は結果に含まれない。"""
        parsed_data = [{"sample_name": "DW1", "pH": "7.2"}]
        sample_mapping = {"DW1": "DW1"}
        key_mapping = {"pH": {"holder_code": "H1", "test_code": "T_pH"}}
        table_rows = [
            {
                "_row_key": "REQ1_H1_T_SS",
                "valid_sample_display_name": "DW1",
                "valid_holder_set_code": "H1",
                "valid_test_set_code": "T_SS",  # マッピングなし
            },
        ]
        result = self.service.apply_mapping(
            parsed_data, sample_mapping, key_mapping, "sample_name", table_rows,
        )
        assert result == {}

    def test_unmatched_sample(self) -> None:
        """照合されていないサンプルの行は結果に含まれない。"""
        parsed_data = [{"sample_name": "DW1", "pH": "7.2"}]
        sample_mapping = {}  # 照合なし
        key_mapping = {"pH": {"holder_code": "H1", "test_code": "T_pH"}}
        table_rows = [
            {
                "_row_key": "REQ1_H1_T_pH",
                "valid_sample_display_name": "DW1",
                "valid_holder_set_code": "H1",
                "valid_test_set_code": "T_pH",
            },
        ]
        result = self.service.apply_mapping(
            parsed_data, sample_mapping, key_mapping, "sample_name", table_rows,
        )
        assert result == {}


class TestDetectDuplicateValues:
    """detect_duplicate_values のテスト。"""

    def setup_method(self) -> None:
        self.service = AnalysisResultService()

    def test_no_duplicates(self) -> None:
        """重複がない場合は空セットを返す。"""
        result = self.service.detect_duplicate_values(
            {"key1": "val1", "key2": "val2"},
        )
        assert result == set()

    def test_with_duplicates(self) -> None:
        """重複がある場合はそのキーを返す。"""
        result = self.service.detect_duplicate_values(
            {"key1": "same", "key2": "same", "key3": "other"},
        )
        assert result == {"key1", "key2"}

    def test_empty_values_ignored(self) -> None:
        """空値は重複検出の対象外。"""
        result = self.service.detect_duplicate_values(
            {"key1": "", "key2": ""},
        )
        assert result == set()
