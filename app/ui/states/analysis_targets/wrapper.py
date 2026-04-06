"""AnalysisTargetsState — 分析対象ステートのUIラッパー。"""
from __future__ import annotations

from datetime import datetime

from PySide6.QtWidgets import QWidget, QVBoxLayout, QMessageBox, QDialog, QApplication
from PySide6.QtCore import Signal
from PySide6.QtGui import QTextDocument
from PySide6.QtPrintSupport import QPrintDialog, QPrinter

import app.config as _cfg
from app.services.task_service import TaskService
from app.services.data_service import DataService
from app.services.data_config_service import DataConfigService
from app.ui.dialogs.loading_dialog import LoadingOverlay
from .state import AnalysisTargetsUI, AddSampleDialog
from .print_preview import PrintPreviewDialog


class AnalysisTargetsState(QWidget):
    go_next = Signal()
    go_back = Signal()
    step_edited = Signal(str)       # 編集済みになった state_id を送出
    loading_changed = Signal(bool, str)  # (is_loading, message)

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
        self._readonly = False
        self._edit_mode = False

        self._ui = AnalysisTargetsUI()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self._ui)

        self._ui.next_requested.connect(self._on_next)
        self._ui.back_requested.connect(self.go_back)
        self._ui.add_sample_requested.connect(self._on_add_sample)
        self._ui.delete_row_requested.connect(self._ui.apply_delete)
        self._ui.edit_requested.connect(self._on_edit_requested)
        self._ui.content_edited.connect(
            lambda: self.step_edited.emit("analysis_targets")
        )
        self._ui.print_btn.clicked.connect(self._on_print)

    # ── Public API ────────────────────────────────────────────────────────────

    def load_task(self, task: dict, readonly: bool = False) -> None:
        self._task = task
        self._readonly = readonly
        self._edit_mode = False
        self._ui.edited_badge.setVisible(False)

        # 列設定を読み込んで UI にセット（CSV全列 + 計算列）
        try:
            csv_columns = self._data_service.get_csv_columns()
        except Exception:
            csv_columns = None
        all_cols = self._data_config.get_task_columns(
            "analysis_targets", csv_columns=csv_columns,
        )
        visible_cols = [c for c in all_cols if c.get("visible", True)]
        self._ui.set_column_config(visible_cols)

        hg_code = task.get("holder_group_code", "")
        jobs = task.get("job_numbers", [])

        result: dict = {}
        LoadingOverlay.run_with_overlay(
            lambda: result.update(grouped=self._data_service.get_analysis_targets(hg_code, jobs)),
            msg="分析対象データを取得しています...",
        )
        grouped = result.get("grouped", {})

        sd = task.get("state_data", {}).get("analysis_targets", {})
        deleted_codes = set(sd.get("deleted_codes", []))
        added_samples = list(sd.get("added_samples", []))

        self._ui.set_samples(grouped, deleted_codes, added_samples)
        self._ui.set_editable(False)

        if readonly:
            self._ui.show_edit_btn(False)
            self._ui.set_nav_visible(False)
        else:
            self._ui.set_nav_visible(True)
            if task.get("current_state") != "analysis_targets":
                self._ui.show_edit_btn(True)
            else:
                self._ui.set_editable(True)
                self._ui.show_edit_btn(False)

    def set_state_done(self, done: bool) -> None:
        """完了済みステートなら完了ボタンを無効化して「完了済み」にする。"""
        if done:
            self._ui._form.btn_next.setEnabled(False)
            self._ui._form.btn_next.setText("完了済み")
        else:
            self._ui._form.btn_next.setText("完了")

    # ── Handlers ─────────────────────────────────────────────────────────────

    def _on_print(self) -> None:
        """現在のタブのサンプル一覧を印刷する。"""
        printer = QPrinter(QPrinter.PrinterMode.HighResolution)
        dlg = QPrintDialog(printer, self)
        if dlg.exec() != QDialog.DialogCode.Accepted:
            return

        doc = QTextDocument()
        doc.setHtml(self._build_print_html())
        doc.print_(printer)

    def _on_edit_requested(self) -> None:
        self._edit_mode = True
        self._ui.set_editable(True)
        self._ui.show_edit_btn(False)

    def _on_add_sample(self) -> None:
        valid_samples = self._data_service.get_valid_samples()
        dlg = AddSampleDialog(valid_samples, self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            name = dlg.selected_name()
            if name:
                self._ui.add_free_sample(name)

    def _on_next(
        self,
        vsset_codes: list,
        deleted_codes: list,
        added_samples: list,
    ) -> None:
        task_id = self._task["task_id"]
        current = self._task.get("current_state", "analysis_targets")
        in_edit = self._edit_mode and current not in ("analysis_targets", "task_setup")

        if in_edit:
            reply = QMessageBox.question(
                self,
                "確認",
                "分析対象を変更すると、以降のステートのデータが初期化されます。\n続行しますか？",
                QMessageBox.StandardButton.Ok | QMessageBox.StandardButton.Cancel,
            )
            if reply != QMessageBox.StandardButton.Ok:
                return

        self._task = self._task_service.save_analysis_targets(
            task_id, vsset_codes, deleted_codes, added_samples, in_edit
        )
        self.go_next.emit()

    # ── 印刷 ─────────────────────────────────────────────────────────────────

    def _build_print_html(self) -> str:
        """印刷用 HTML を生成する（全タブ分）。"""
        from app.ui.states.analysis_targets.state import AnalysisTargetsUI

        task = self._task
        task_name = task.get("task_name", "")
        hg_name = task.get("holder_group_name", "")
        jobs = "、".join(task.get("job_numbers", []))
        now = datetime.now().strftime("%Y-%m-%d %H:%M")

        vis_cols = self._ui._visible_columns()
        grouped = self._ui._grouped_samples
        deleted = self._ui._deleted_codes
        added = self._ui._added_samples

        # ヘッダー行
        th_html = "".join(f"<th>{c['label']}</th>" for c in vis_cols)

        tables_html = ""
        total = 0
        for test_name, samples in grouped.items():
            visible = [s for s in samples
                       if s["valid_sample_set_code"] not in deleted]
            total += len(visible)

            rows_html = ""
            for s in visible:
                cells = "".join(
                    f"<td>{AnalysisTargetsUI._extract_cell(s, c['key'])}</td>"
                    for c in vis_cols
                )
                rows_html += f"<tr>{cells}</tr>"

            tables_html += (
                f"<h3>{test_name}</h3>"
                f"<table><tr>{th_html}</tr>{rows_html}</table>"
            )

        # 追加サンプル
        if added:
            total += len(added)
            added_rows = ""
            for name in added:
                dummy = {
                    "valid_sample_set_code": f"FREE_{name}",
                    "valid_sample_display_name": name,
                    "sample_request_number": "", "sample_job_number": "",
                    "sample_sampling_date": "",
                    "median": None, "max": None, "min": None,
                }
                cells = "".join(
                    f"<td>{AnalysisTargetsUI._extract_cell(dummy, c['key'])}</td>"
                    for c in vis_cols
                )
                added_rows += f"<tr>{cells}</tr>"
            tables_html += (
                "<h3>追加サンプル</h3>"
                f"<table><tr>{th_html}</tr>{added_rows}</table>"
            )

        return (
            "<html><head><style>"
            "body { font-family: 'Yu Gothic UI', sans-serif; font-size: 11pt; }"
            "h2 { margin: 0 0 4px; font-size: 14pt; }"
            "h3 { margin: 12px 0 4px; font-size: 12pt; }"
            ".meta { color: #555; font-size: 10pt; margin-bottom: 8px; }"
            "table { border-collapse: collapse; width: 100%; margin-top: 4px; }"
            "th, td { border: 1px solid #999; padding: 4px 8px; font-size: 10pt; }"
            "th { background: #e8e8e8; font-weight: bold; }"
            ".footer { margin-top: 12px; font-size: 9pt; color: #888; }"
            "</style></head><body>"
            f"<h2>分析対象サンプル一覧</h2>"
            f"<div class='meta'>"
            f"タスク: {task_name}　／　分析項目: {hg_name}　／　JOB番号: {jobs}"
            f"</div>"
            f"<div class='meta'>サンプル数: {total}</div>"
            f"{tables_html}"
            f"<div class='footer'>印刷日時: {now}　　ユーザー: {_cfg.CURRENT_USER}</div>"
            "</body></html>"
        )
