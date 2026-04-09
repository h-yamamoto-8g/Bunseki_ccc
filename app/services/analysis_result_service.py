"""分析結果の読み込みサービス。

パーサー実行・サンプル照合・キーマッピングを統合するサービス層。
Core (analysis_parser, analysis_parser_store) にのみ依存する。
"""
from __future__ import annotations

import logging
from difflib import SequenceMatcher
from pathlib import Path

from app.core import analysis_parser, analysis_parser_store

logger = logging.getLogger(__name__)


class AnalysisResultService:
    """分析結果の読み込み・照合・マッピングを行うサービス。"""

    # ── パーサー管理 ──────────────────────────────────────────────────────────

    def has_parser(self, hg_code: str) -> bool:
        """指定ホルダグループにパーサーが登録済みか返す。

        Args:
            hg_code: ホルダグループコード。
        """
        return analysis_parser_store.has_parser(hg_code)

    def get_parser_code(self, hg_code: str) -> str | None:
        """パーサーコードを取得する。

        Args:
            hg_code: ホルダグループコード。
        """
        return analysis_parser_store.get_parser_code(hg_code)

    def validate_parser(self, code: str) -> list[str]:
        """パーサーコードをバリデーションする。

        Args:
            code: Python ソースコード文字列。

        Returns:
            問題点のリスト。空リストなら問題なし。
        """
        return analysis_parser.validate_parser_code(code)

    def save_parser(self, hg_code: str, code: str) -> list[str]:
        """パーサーコードをバリデーションして保存する。

        Args:
            hg_code: ホルダグループコード。
            code: Python ソースコード文字列。

        Returns:
            バリデーションエラーのリスト。空リストなら保存成功。
        """
        errors = analysis_parser.validate_parser_code(code)
        if errors:
            return errors
        analysis_parser_store.save_parser_code(hg_code, code)
        return []

    def test_parser(self, code: str, file_path: str) -> list[dict[str, str]]:
        """パーサーコードをテスト実行する。

        Args:
            code: Python ソースコード文字列。
            file_path: テスト用ファイルのパス。

        Returns:
            パース結果。

        Raises:
            ValueError: バリデーションエラー時。
            Exception: パーサー実行中のエラー。
        """
        errors = analysis_parser.validate_parser_code(code)
        if errors:
            raise ValueError("\n".join(errors))
        return analysis_parser.execute_parser(code, file_path)

    # ── マッピング設定 ────────────────────────────────────────────────────────

    def get_parser_config(self, hg_code: str) -> dict:
        """パーサーのマッピング設定を取得する。

        Args:
            hg_code: ホルダグループコード。

        Returns:
            ``{"sample_name_key": str, "key_mapping": dict}``
        """
        return analysis_parser_store.get_parser_config(hg_code)

    def save_parser_config(
        self,
        hg_code: str,
        sample_name_key: str,
        key_mapping: dict[str, dict[str, str]],
    ) -> None:
        """パーサーのマッピング設定を保存する。

        Args:
            hg_code: ホルダグループコード。
            sample_name_key: JSON内のサンプル名キー。
            key_mapping: ``{json_key: {"holder_code": str, "test_code": str}}``。
        """
        analysis_parser_store.save_parser_config(hg_code, sample_name_key, key_mapping)

    # ── 分析結果の読み込み・照合 ──────────────────────────────────────────────

    def load_and_parse(self, hg_code: str, file_path: str) -> list[dict[str, str]]:
        """設定済みパーサーで分析結果ファイルを読み込む。

        Args:
            hg_code: ホルダグループコード。
            file_path: 分析結果ファイルのパス。

        Returns:
            パース結果の辞書リスト。

        Raises:
            FileNotFoundError: パーサーが未登録の場合。
            Exception: パーサー実行中のエラー。
        """
        code = analysis_parser_store.get_parser_code(hg_code)
        if code is None:
            raise FileNotFoundError(
                f"ホルダグループ {hg_code} のパーサーが登録されていません。"
            )
        return analysis_parser.execute_parser(code, file_path)

    def fuzzy_match_samples(
        self,
        system_names: list[str],
        analysis_names: list[str],
    ) -> dict[str, tuple[str, float]]:
        """システムのサンプル名と分析結果のサンプル名をファジーマッチングする。

        Args:
            system_names: システム側のサンプル名リスト (valid_sample_display_name)。
            analysis_names: 分析結果から取得したサンプル名リスト。

        Returns:
            ``{system_name: (best_analysis_name, score)}``。
            マッチ候補がない場合は ``("", 0.0)``。
        """
        result: dict[str, tuple[str, float]] = {}
        for sys_name in system_names:
            best_name = ""
            best_score = 0.0
            for ana_name in analysis_names:
                score = SequenceMatcher(
                    None, sys_name.lower(), ana_name.lower()
                ).ratio()
                if score > best_score:
                    best_score = score
                    best_name = ana_name
            result[sys_name] = (best_name, best_score)
        return result

    def apply_mapping(
        self,
        parsed_data: list[dict[str, str]],
        sample_mapping: dict[str, str],
        key_mapping: dict[str, dict[str, str]],
        sample_name_key: str,
        table_rows: list[dict],
    ) -> dict[str, str]:
        """照合結果とマッピングに基づき、input_data の値を生成する。

        Args:
            parsed_data: パーサーの出力 (list[dict[str, str]])。
            sample_mapping: ``{system_sample_name: analysis_sample_name}``。
            key_mapping: ``{json_key: {"holder_code": str, "test_code": str}}``。
            sample_name_key: JSON 内のサンプル名キー。
            table_rows: テーブルの行データ。各行は _row_key, valid_sample_display_name,
                        valid_holder_set_code, valid_test_set_code を含む。

        Returns:
            ``{row_key: value}`` の辞書。input_data に書き込む値。
        """
        # 分析名 → レコードのインデックスマップ
        analysis_records: dict[str, dict[str, str]] = {}
        for record in parsed_data:
            ana_name = record.get(sample_name_key, "")
            if ana_name:
                analysis_records[ana_name] = record

        # (holder_code, test_code) → json_key の逆引きマップ
        reverse_mapping: dict[tuple[str, str], str] = {}
        for json_key, mapping in key_mapping.items():
            holder = str(mapping.get("holder_code", ""))
            test = str(mapping.get("test_code", ""))
            if holder and test:
                reverse_mapping[(holder, test)] = json_key

        # 各行に対して値を算出
        input_values: dict[str, str] = {}
        for row in table_rows:
            row_key = row.get("_row_key", "")
            sys_name = str(row.get("valid_sample_display_name", ""))
            holder_code = str(row.get("valid_holder_set_code", ""))
            test_code = str(row.get("valid_test_set_code", ""))

            # このサンプルに対応する分析名を取得
            ana_name = sample_mapping.get(sys_name, "")
            if not ana_name:
                continue

            # 分析レコードを取得
            record = analysis_records.get(ana_name)
            if not record:
                continue

            # (holder_code, test_code) に対応する JSON キーを検索
            json_key = reverse_mapping.get((holder_code, test_code))
            if not json_key:
                continue

            # 値を取得
            value = record.get(json_key, "")
            if value:
                input_values[row_key] = value

        return input_values

    def detect_duplicate_values(
        self,
        input_values: dict[str, str],
    ) -> set[str]:
        """同一の値が複数行に書き込まれるケースを検出する。

        Args:
            input_values: ``{row_key: value}`` の辞書。

        Returns:
            重複値を持つ row_key のセット。
        """
        value_to_keys: dict[str, list[str]] = {}
        for key, val in input_values.items():
            if val:
                value_to_keys.setdefault(val, []).append(key)

        duplicate_keys: set[str] = set()
        for keys in value_to_keys.values():
            if len(keys) > 1:
                duplicate_keys.update(keys)
        return duplicate_keys

    # ── 添付ファイル ──────────────────────────────────────────────────────────

    def save_attachment(self, task_id: str, source_path: str) -> Path:
        """分析結果ファイルをタスクの添付として保存する。

        Args:
            task_id: タスクID。
            source_path: 分析結果ファイルのパス。

        Returns:
            保存先のパス。
        """
        return analysis_parser_store.save_attachment(task_id, source_path)

    def get_attachments(self, task_id: str) -> list[Path]:
        """タスクに紐づく分析結果ファイル一覧を返す。

        Args:
            task_id: タスクID。
        """
        return analysis_parser_store.get_attachments(task_id)
