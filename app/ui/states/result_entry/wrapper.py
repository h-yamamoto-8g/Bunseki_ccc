"""ResultEntryState — データ入力ステートのUIラッパー。"""
from __future__ import annotations

import csv
import os
import subprocess
import sys
import webbrowser
from pathlib import Path

from PySide6.QtWidgets import QWidget, QVBoxLayout, QMessageBox
from PySide6.QtCore import Signal

import app.config as _cfg
from app.services.task_service import TaskService
from app.services.data_service import DataService
from app.services.data_config_service import DataConfigService
from app.services.data_update_service import run_all as _run_data_update
from app.ui.dialogs.loading_dialog import LoadingDialog, LoadingOverlay
from .state import ResultEntryUI

# ─────────────────────────────────────────────────────────────────────────────
# Lab-Aid / 入力ツール の起動パス設定
# ─────────────────────────────────────────────────────────────────────────────
_LABAID_PATH = ""
_INPUT_TOOL_PATH = ""  # CSV を処理する外部ツールのパス


class ResultEntryState(QWidget):
    go_next = Signal()
    go_back = Signal()

    def __init__(
        self,
        task_service: TaskService,
        data_service: DataService,
        parent=None,
    ) -> None:
        super().__init__(parent)
        self._task_service = task_service
        self._data_service = data_service
        self._data_config = DataConfigService()
        self._task: dict = {}

        self._ui = ResultEntryUI()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self._ui)

        self._ui.done_requested.connect(self._on_done)
        self._ui.back_requested.connect(self.go_back)
        self._ui.data_update_requested.connect(self._on_data_update)
        self._ui.labaid_requested.connect(self._open_labaid)
        self._ui.save_temp_requested.connect(self._on_save_temp)
        self._ui.csv_export_requested.connect(self._on_csv_export)
        self._ui.open_tool_requested.connect(self._open_input_tool)

    def load_task(self, task: dict, readonly: bool = False) -> None:
        self._task = task
        hg_code = task.get("holder_group_code", "")
        jobs = task.get("job_numbers", [])

        # 列設定
        try:
            csv_columns = self._data_service.get_csv_columns()
        except Exception:
            csv_columns = None
        all_cols = self._data_config.get_task_columns(
            "result_entry", csv_columns=csv_columns,
        )
        visible_cols = [c for c in all_cols if c.get("visible", True)]
        self._ui.set_column_config(visible_cols)

        # サンプルコード取得
        sd = task.get("state_data", {}).get("analysis_targets", {})
        vsset_codes = sd.get("valid_sample_set_codes", [])

        # データ取得（ホルダーごとにグルーピング）
        grouped: dict[str, list[dict]] = {}

        def _load() -> None:
            nonlocal grouped
            df = self._data_service.get_result_data(hg_code, jobs, vsset_codes)
            if df is not None and not df.empty:
                for _, row in df.iterrows():
                    holder_name = str(row.get("valid_holder_display_name", ""))
                    grouped.setdefault(holder_name, []).append(row.to_dict())

        LoadingOverlay.run_with_overlay(
            _load, msg="データ入力テーブルを取得しています...",
        )

        self._ui.set_data(grouped)

        # 一時保存データの復元
        entry_sd = task.get("state_data", {}).get("result_entry", {})
        saved_input = entry_sd.get("input_data", {})
        if saved_input:
            self._ui.restore_input_data(saved_input)

        self._ui.set_readonly(readonly)

    def set_state_done(self, done: bool) -> None:
        self._ui.set_state_done(done)

    # ── Handlers ──────────────────────────────────────────────────────────────

    def _on_done(self) -> None:
        self._task = self._task_service.save_result_entry(self._task["task_id"])
        self.go_next.emit()

    def _on_save_temp(self, all_data: list[dict]) -> None:
        """一時保存: 入力データを state_data に保存する。"""
        input_map: dict[str, str] = {}
        for row in all_data:
            key = row.get("_row_key", "")
            val = row.get("input_data", "")
            if key and val:
                input_map[key] = val

        # state_data.result_entry に保存
        task = self._task_service.get_task(self._task["task_id"])
        if not task:
            return
        sd = dict(task.get("state_data", {}))
        entry = dict(sd.get("result_entry", {}))
        entry["input_data"] = input_map
        sd["result_entry"] = entry
        from app.core import task_store
        task_store.update_task_field(self._task["task_id"], state_data=sd)
        self._task = self._task_service.get_task(self._task["task_id"])

        QMessageBox.information(self, "一時保存完了", "入力データを一時保存しました。")

    def _on_csv_export(self, all_data: list[dict]) -> None:
        """CSV出力: タスク名でCSVファイルを出力する。"""
        task_name = self._task.get("task_name", "export")
        output_dir = _cfg.DATA_PATH / "bunseki" / "entry"
        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = output_dir / f"{task_name}.csv"

        # CSV出力列の構成
        csv_headers = [
            "sample_request_number",
            "valid_holder_set_code",
            "valid_test_set_code",
            "test_unit_name",
            "input_data",
        ]
        csv_labels = ["依頼番号", "ホルダコード", "試験コード", "単位", "入力データ"]

        # 元データからコード値を取得するためにキーマップを構築
        hg_code = self._task.get("holder_group_code", "")
        jobs = self._task.get("job_numbers", [])
        sd = self._task.get("state_data", {}).get("analysis_targets", {})
        vsset_codes = sd.get("valid_sample_set_codes", [])

        df = self._data_service.get_result_data(hg_code, jobs, vsset_codes)
        code_map: dict[str, dict] = {}
        if df is not None and not df.empty:
            for _, row in df.iterrows():
                key = (
                    f"{row.get('sample_request_number', '')}_"
                    f"{row.get('valid_holder_set_code', '')}_"
                    f"{row.get('valid_test_set_code', '')}"
                )
                code_map[key] = row.to_dict()

        rows_out: list[list[str]] = []
        for row in all_data:
            row_key = row.get("_row_key", "")
            source = code_map.get(row_key, {})
            csv_row = [
                str(source.get("sample_request_number", "")),
                str(source.get("valid_holder_set_code", "")),
                str(source.get("valid_test_set_code", "")),
                str(source.get("test_unit_name", "")),
                row.get("input_data", ""),
            ]
            rows_out.append(csv_row)

        with open(output_path, "w", newline="", encoding="utf-8-sig") as f:
            writer = csv.writer(f)
            writer.writerow(csv_labels)
            writer.writerows(rows_out)

        # 一時保存も同時に行う
        self._on_save_temp(all_data)

        reply = QMessageBox.information(
            self,
            "CSV出力完了",
            f"CSVファイルを出力しました。\n{output_path}\n\n入力ツールを起動しますか？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            self._open_input_tool()

    def _open_labaid(self) -> None:
        path = _LABAID_PATH.strip()
        if not path:
            QMessageBox.information(self, "Lab-Aid", "Lab-Aidを起動します（デモ）")
            return
        try:
            if path.startswith(("http://", "https://")):
                webbrowser.open(path)
            else:
                subprocess.Popen([path])
        except Exception as e:
            QMessageBox.warning(self, "Lab-Aid 起動エラー", str(e))

    def _open_input_tool(self) -> None:
        """入力ツールを起動する。"""
        path = _INPUT_TOOL_PATH.strip()
        if not path:
            # パス未設定: CSVファイルを直接開く
            task_name = self._task.get("task_name", "export")
            csv_path = _cfg.DATA_PATH / "bunseki" / "entry" / f"{task_name}.csv"
            if csv_path.exists():
                self._open_file(str(csv_path))
            else:
                QMessageBox.information(
                    self, "入力ツール",
                    "CSVファイルが見つかりません。先にCSV出力を行ってください。",
                )
            return
        try:
            if path.startswith(("http://", "https://")):
                webbrowser.open(path)
            else:
                subprocess.Popen([path])
        except Exception as e:
            QMessageBox.warning(self, "入力ツール起動エラー", str(e))

    @staticmethod
    def _open_file(filepath: str) -> None:
        if sys.platform == "win32":
            os.startfile(filepath)
        elif sys.platform == "darwin":
            subprocess.Popen(["open", filepath])
        else:
            subprocess.Popen(["xdg-open", filepath])

    def _on_data_update(self) -> None:
        dlg = LoadingDialog(_run_data_update, parent=self)
        dlg.exec()
        if dlg.error():
            QMessageBox.warning(self, "データ更新エラー", dlg.error())
