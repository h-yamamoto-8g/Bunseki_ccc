"""ResultEntryState — データ入力ステートのUIラッパー。"""
from __future__ import annotations

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
        self._ui.transfer_requested.connect(self._on_transfer)
        self._ui.verify_requested.connect(self._on_verify)

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

    def _on_transfer(self, all_data: list[dict]) -> None:
        """入力ツール(Excel)の指定シート・セルにデータを書き込んで開く。"""
        from app.ui.pages.settings.tool_settings_tab import _expand_path
        excel_path = _expand_path(
            self._data_config.get_tool_path("input_tool_path")
        )
        sheet_name = self._data_config.get_tool_path("input_tool_sheet").strip()
        start_cell = self._data_config.get_tool_path("input_tool_cell").strip()

        if not excel_path:
            QMessageBox.warning(
                self, "入力ツール",
                "Excel ファイルのパスが設定されていません。\n設定画面で設定してください。",
            )
            return
        if not Path(excel_path).exists():
            QMessageBox.warning(
                self, "入力ツール",
                f"Excel ファイルが見つかりません。\n{excel_path}",
            )
            return

        # CSV出力列の設定を取得
        try:
            csv_columns = self._data_service.get_csv_columns()
        except Exception:
            csv_columns = None
        export_cols = self._data_config.get_task_columns(
            "result_entry_csv_export", csv_columns=csv_columns,
        )
        visible_export = [c for c in export_cols if c.get("visible", True)]
        csv_headers = [c["key"] for c in visible_export]
        csv_labels = [c["label"] for c in visible_export]

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
            out_row: list[str] = []
            for col_key in csv_headers:
                if col_key == "input_data":
                    out_row.append(row.get("input_data", ""))
                else:
                    out_row.append(str(source.get(col_key, "")))
            rows_out.append(out_row)

        # Excel に書き込み
        try:
            from openpyxl import load_workbook
            from openpyxl.utils.cell import coordinate_from_string, column_index_from_string

            wb = load_workbook(excel_path, keep_vba=True)

            if sheet_name and sheet_name in wb.sheetnames:
                ws = wb[sheet_name]
            elif sheet_name:
                ws = wb.create_sheet(sheet_name)
            else:
                ws = wb.active

            # 開始セルの解析（デフォルト A1）
            cell_ref = start_cell or "A1"
            col_letter, start_row = coordinate_from_string(cell_ref)
            start_col = column_index_from_string(col_letter)

            # データ行を書き込み
            for ri, data_row in enumerate(rows_out):
                for ci, val in enumerate(data_row):
                    ws.cell(
                        row=start_row + ri,
                        column=start_col + ci,
                        value=val,
                    )

            wb.save(excel_path)
        except PermissionError:
            QMessageBox.warning(
                self,
                "Excel 書き込みエラー",
                "ファイルへのアクセスが拒否されました。\n"
                "Excel でファイルが開かれている場合は閉じてから\n"
                "再度お試しください。\n\n"
                f"{excel_path}",
            )
            return
        except Exception as e:
            QMessageBox.warning(self, "Excel 書き込みエラー", str(e))
            return

        # 一時保存も同時に行う
        self._on_save_temp(all_data)

        # Excel を開く
        self._open_file(excel_path)

    def _open_labaid(self) -> None:
        from app.ui.pages.settings.tool_settings_tab import _expand_path
        path = _expand_path(
            self._data_config.get_tool_path("labaid_path")
        )
        if not path:
            QMessageBox.information(self, "Lab-Aid", "Lab-Aidのパスが設定されていません。\n設定画面で設定してください。")
            return
        try:
            if path.startswith(("http://", "https://")):
                webbrowser.open(path)
            else:
                self._open_file(path)
        except Exception as e:
            QMessageBox.warning(self, "Lab-Aid 起動エラー", str(e))

    @staticmethod
    def _open_file(filepath: str) -> None:
        if sys.platform == "win32":
            os.startfile(filepath)
        elif sys.platform == "darwin":
            subprocess.Popen(["open", filepath])
        else:
            subprocess.Popen(["xdg-open", filepath])

    def _on_verify(self) -> None:
        """入力データと bunseki.csv の data_raw_data を照合する。"""
        hg_code = self._task.get("holder_group_code", "")
        jobs = self._task.get("job_numbers", [])
        sd = self._task.get("state_data", {}).get("analysis_targets", {})
        vsset_codes = sd.get("valid_sample_set_codes", [])

        df = self._data_service.get_result_data(hg_code, jobs, vsset_codes)
        raw_map: dict[str, str] = {}
        if df is not None and not df.empty:
            for _, row in df.iterrows():
                key = (
                    f"{row.get('sample_request_number', '')}_"
                    f"{row.get('valid_holder_set_code', '')}_"
                    f"{row.get('valid_test_set_code', '')}"
                )
                val = row.get("data_raw_data", "")
                if val is None:
                    raw_map[key] = ""
                elif isinstance(val, float):
                    if val != val:
                        raw_map[key] = ""
                    elif val.is_integer():
                        raw_map[key] = str(int(val))
                    else:
                        raw_map[key] = str(val)
                else:
                    s = str(val)
                    raw_map[key] = "" if s in ("nan", "None") else s

        all_data = self._ui._collect_all_data()
        mismatch_keys: set[str] = set()
        for row in all_data:
            row_key = row.get("_row_key", "")
            input_val = row.get("input_data", "").strip()
            raw_val = raw_map.get(row_key, "").strip()
            if not input_val:
                continue
            if input_val != raw_val:
                mismatch_keys.add(row_key)

        self._ui.highlight_mismatches(mismatch_keys)

        if mismatch_keys:
            QMessageBox.warning(
                self, "データ照合",
                f"{len(mismatch_keys)} 件の不一致があります。",
            )
        else:
            QMessageBox.information(self, "データ照合", "すべてのデータが一致しています。")

    def _on_data_update(self) -> None:
        dlg = LoadingDialog(_run_data_update, parent=self)
        dlg.exec()
        if dlg.error():
            QMessageBox.warning(self, "データ更新エラー", dlg.error())
