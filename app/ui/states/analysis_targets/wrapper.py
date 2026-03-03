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

        hg_code = task.get("holder_group_code", "")
        jobs = task.get("job_numbers", [])

        self.loading_changed.emit(True, "分析対象データを取得しています...")
        QApplication.processEvents()
        samples = self._data_service.get_analysis_targets(hg_code, jobs)
        self.loading_changed.emit(False, "")

        sd = task.get("state_data", {}).get("analysis_targets", {})
        deleted_codes = set(sd.get("deleted_codes", []))
        added_samples = list(sd.get("added_samples", []))

        self._ui.set_samples(samples, deleted_codes, added_samples)
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

    # ── Handlers ─────────────────────────────────────────────────────────────

    def _on_print(self) -> None:
        table = self._ui.table
        col_count = table.columnCount() - 1  # 最終列（削除ボタン）を除外

        headers = [
            table.horizontalHeaderItem(c).text() for c in range(col_count)
        ]
        rows = []
        for r in range(table.rowCount()):
            rows.append([
                (table.item(r, c).text() if table.item(r, c) else "")
                for c in range(col_count)
            ])

        hg_name = self._task.get("holder_group_name", "")
        title = f"分析対象一覧 — {hg_name}" if hg_name else "分析対象一覧"

        dlg = PrintPreviewDialog(title, headers, rows, self)
        dlg.exec()

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

    def _on_print(self) -> None:
        """サンプル一覧を印刷する。"""
        printer = QPrinter(QPrinter.PrinterMode.HighResolution)
        dlg = QPrintDialog(printer, self)
        if dlg.exec() != QDialog.DialogCode.Accepted:
            return

        doc = QTextDocument()
        doc.setHtml(self._build_print_html())
        doc.print_(printer)

    def _build_print_html(self) -> str:
        """印刷用 HTML を生成する。"""
        task = self._task
        task_name = task.get("task_name", "")
        hg_name = task.get("holder_group_name", "")
        jobs = "、".join(task.get("job_numbers", []))
        now = datetime.now().strftime("%Y-%m-%d %H:%M")

        # 表示中サンプル（削除済み除外）
        visible = [
            s for s in self._ui._samples
            if s["valid_sample_set_code"] not in self._ui._deleted_codes
        ]
        # 追加サンプル
        added = self._ui._added_samples

        rows_html = ""
        for s in visible:
            median = f"{s['median']:.3g}" if s.get("median") is not None else "—"
            max_v = f"{s['max']:.3g}" if s.get("max") is not None else "—"
            min_v = f"{s['min']:.3g}" if s.get("min") is not None else "—"
            rows_html += (
                f"<tr>"
                f"<td>{s.get('sample_job_number', '')}</td>"
                f"<td>{s.get('sample_sampling_date', '')}</td>"
                f"<td>{s.get('valid_sample_display_name', '')}</td>"
                f"<td style='text-align:right; border:1px solid #999; padding:4px 8px;'>{median}</td>"
                f"<td style='text-align:right; border:1px solid #999; padding:4px 8px;'>{max_v}</td>"
                f"<td style='text-align:right; border:1px solid #999; padding:4px 8px;'>{min_v}</td>"
                f"</tr>"
            )
        for name in added:
            rows_html += (
                f"<tr>"
                f"<td></td><td></td>"
                f"<td style='color:#7c3aed; border:1px solid #999; padding:4px 8px;'>{name}（追加）</td>"
                f"<td>—</td><td>—</td><td>—</td>"
                f"</tr>"
            )

        total = len(visible) + len(added)

        return (
            "<html><head><style>"
            "body { font-family: 'Yu Gothic UI', sans-serif; font-size: 11pt; }"
            "h2 { margin: 0 0 4px; font-size: 14pt; }"
            ".meta { color: #555; font-size: 10pt; margin-bottom: 8px; }"
            "table { border-collapse: collapse; width: 100%; margin-top: 8px; }"
            "th, td { border: 1px solid #999; padding: 4px 8px; font-size: 10pt; }"
            "th { background: #e8e8e8; font-weight: bold; }"
            ".footer { margin-top: 12px; font-size: 9pt; color: #888; }"
            "</style></head><body>"
            f"<h2>分析対象サンプル一覧</h2>"
            f"<div class='meta'>"
            f"タスク: {task_name}　／　分析項目: {hg_name}　／　JOB番号: {jobs}"
            f"</div>"
            f"<div class='meta'>サンプル数: {total}</div>"
            "<table>"
            "<tr><th>JOB番号</th><th>採取日</th><th>サンプル名</th>"
            "<th>中央値</th><th>最大値</th><th>最小値</th></tr>"
            f"{rows_html}"
            "</table>"
            f"<div class='footer'>印刷日時: {now}　　ユーザー: {_cfg.CURRENT_USER}</div>"
            "</body></html>"
        )
