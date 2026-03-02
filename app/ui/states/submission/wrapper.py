"""SubmissionState — 回覧ステートのUIラッパー。

SubmissionUI のシグナルを受け取り、TaskService / DataService を介して
タスク状態の保存・添付ファイルコピー・Outlook メール作成などを実行する。
"""
from __future__ import annotations

import shutil
from datetime import datetime
from pathlib import Path

from PySide6.QtWidgets import QWidget, QVBoxLayout, QMessageBox, QApplication
from PySide6.QtCore import Signal

import app.config as _cfg
from app.config import DATA_PATH
from app.services.task_service import TaskService
from app.services.data_service import DataService
from .state import SubmissionUI

_ATTACHMENTS_ROOT = DATA_PATH / "bunseki" / "attachments"


class SubmissionState(QWidget):
    """回覧ステートのUIラッパー。"""

    go_next = Signal()
    go_back = Signal()
    loading_changed = Signal(bool, str)

    def __init__(
        self,
        task_service: TaskService,
        data_service: DataService,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._task_service = task_service
        self._data_service = data_service
        self._task: dict = {}

        self._ui = SubmissionUI()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self._ui)

        self._ui.send_requested.connect(self._on_send)
        self._ui.back_requested.connect(self.go_back)
        self._ui.forward_requested.connect(self._on_forward)
        self._ui.return_requested.connect(self._on_return)
        self._ui.complete_requested.connect(self._on_complete)
        self._ui.reclaim_requested.connect(self._on_reclaim)

    # ── Public API ────────────────────────────────────────────────────────────

    def load_task(self, task: dict, readonly: bool = False) -> None:
        """タスクデータをUIにロードする。"""
        self._task = task

        reviewers = self._data_service.get_reviewers()
        user_names = [u["name"] for u in reviewers]
        self._ui.set_available_users(user_names)

        self._ui.set_creator(task.get("created_by", ""))

        sd = task.get("state_data", {}).get("submission", {})
        self._ui.set_reviewers(sd.get("reviewers", []))
        self._ui.set_comment(sd.get("comment", ""))
        self._ui.set_attachments(sd.get("attachments", []))

        mode, current_idx = self._determine_mode(task, readonly)
        self._ui.apply_mode(mode, current_reviewer_index=current_idx)

    # ── Mode determination ────────────────────────────────────────────────────

    def _determine_mode(self, task: dict, readonly: bool) -> tuple[str, int]:
        """タスク状態からUIモードと現在の確認者インデックスを返す。"""
        sd = task.get("state_data", {}).get("submission", {})
        current_idx = sd.get("current_reviewer_index", 0)

        if readonly:
            return "readonly", current_idx

        reviewers = sd.get("reviewers", [])
        if not reviewers:
            return "edit", 0

        status = task.get("status", "")

        if status == "回覧中":
            creator = task.get("created_by", "")
            if _cfg.CURRENT_USER == creator:
                return "sent_analyst", current_idx

            current_reviewer = (
                reviewers[current_idx] if current_idx < len(reviewers) else ""
            )
            if _cfg.CURRENT_USER == current_reviewer:
                if current_idx >= len(reviewers) - 1:
                    return "reviewer_last", current_idx
                return "reviewer_mid", current_idx

            return "readonly", current_idx

        return "edit", 0

    # ── Handlers ──────────────────────────────────────────────────────────────

    def _on_send(self, comment: str, attachments: list[str]) -> None:
        """分析者 → 最初の確認者へ送信。"""
        reviewers = self._ui.get_reviewers()
        if not reviewers:
            QMessageBox.warning(
                self, "確認者未選択", "確認者を1人以上追加してください。"
            )
            return

        task_id = self._task["task_id"]

        stored_paths = self._copy_attachments(task_id, attachments)

        self.loading_changed.emit(True, "異常データを集計しています...")
        QApplication.processEvents()
        self._record_sigma_anomalies(task_id)
        self.loading_changed.emit(False, "")

        self._task = self._task_service.save_submission(
            task_id, reviewers, comment, stored_paths
        )

        self._ui.apply_mode("sent_analyst", current_reviewer_index=0)

        sent_via_outlook = self._open_outlook_email(reviewers[0], comment)
        if not sent_via_outlook:
            QMessageBox.information(
                self,
                "送信完了",
                f"確認者「{reviewers[0]}」に回覧しました。\n"
                "（Outlook はWindows環境でのみ起動します）",
            )

    def _on_forward(self) -> None:
        """確認者 → 次の確認者へ送信。"""
        task_id = self._task["task_id"]
        self._task = self._task_service.forward_submission(task_id)

        sd = self._task.get("state_data", {}).get("submission", {})
        new_idx = sd.get("current_reviewer_index", 0)
        reviewers = sd.get("reviewers", [])
        next_reviewer = reviewers[new_idx] if new_idx < len(reviewers) else ""

        mode, idx = self._determine_mode(self._task, readonly=False)
        self._ui.apply_mode(mode, current_reviewer_index=idx)

        sent_via_outlook = self._open_outlook_email(
            next_reviewer, "", is_forward=True
        )
        if not sent_via_outlook:
            QMessageBox.information(
                self,
                "回覧",
                f"次の確認者「{next_reviewer}」に回覧しました。\n"
                "（Outlook はWindows環境でのみ起動します）",
            )

    def _on_return(self) -> None:
        """確認者 → 分析者へ差し戻し。"""
        task_id = self._task["task_id"]
        self._task = self._task_service.reclaim_submission(task_id)

        mode, idx = self._determine_mode(self._task, readonly=False)
        self._ui.apply_mode(mode, current_reviewer_index=idx)

        creator = self._task.get("created_by", "")
        QMessageBox.information(
            self,
            "差し戻し",
            f"分析者「{creator}」に差し戻しました。",
        )

    def _on_reclaim(self) -> None:
        """分析者が回覧を取り戻す。"""
        task_id = self._task["task_id"]
        self._task = self._task_service.reclaim_submission(task_id)

        mode, idx = self._determine_mode(self._task, readonly=False)
        self._ui.apply_mode(mode, current_reviewer_index=idx)

        QMessageBox.information(
            self,
            "取り戻し",
            "回覧を取り戻しました。再送信できます。",
        )

    def _on_complete(self) -> None:
        """最後の確認者がタスクを終了する。"""
        self._task = self._task_service.complete_task(self._task["task_id"])
        self.go_next.emit()

    # ── Private helpers ───────────────────────────────────────────────────────

    def _copy_attachments(self, task_id: str, files: list[str]) -> list[str]:
        """添付ファイルを app_data/bunseki/attachments/{task_id}/ にコピーする。"""
        if not files:
            return []
        dest_dir = _ATTACHMENTS_ROOT / task_id
        dest_dir.mkdir(parents=True, exist_ok=True)
        stored: list[str] = []
        for src_path in files:
            src = Path(src_path)
            if not src.exists():
                stored.append(src_path)
                continue
            dest = dest_dir / src.name
            shutil.copy2(src, dest)
            stored.append(str(dest))
        return stored

    def _record_sigma_anomalies(self, task_id: str) -> None:
        """mean±2σ超過データを anomalies.json に記録する。"""
        task = self._task
        hg_code = task.get("holder_group_code", "")
        jobs = task.get("job_numbers", [])
        vsset_codes = (
            task.get("state_data", {})
            .get("analysis_targets", {})
            .get("valid_sample_set_codes", [])
        )
        if not hg_code or not jobs:
            return

        df = self._data_service.get_result_data(hg_code, jobs, vsset_codes)
        if df.empty:
            return

        submitted_at = datetime.now().isoformat()
        records: list[dict] = []
        for _, row in df.iterrows():
            is_anomaly = self._data_service.calculate_anomaly(row, hg_code)
            if is_anomaly is True:
                records.append(
                    {
                        "task_id": task_id,
                        "submitted_at": submitted_at,
                        "sample_request_number": str(
                            row.get("sample_request_number", "")
                        ),
                        "sample_job_number": str(
                            row.get("sample_job_number", "")
                        ),
                        "valid_sample_set_code": str(
                            row.get("valid_sample_set_code", "")
                        ),
                        "valid_holder_set_code": str(
                            row.get("valid_holder_set_code", "")
                        ),
                        "valid_test_set_code": str(
                            row.get("valid_test_set_code", "")
                        ),
                        "valid_sample_display_name": str(
                            row.get("valid_sample_display_name", "")
                        ),
                        "valid_test_display_name": str(
                            row.get("valid_test_display_name", "")
                        ),
                        "test_raw_data": str(row.get("test_raw_data", "")),
                        "test_unit_name": str(row.get("test_unit_name", "")),
                    }
                )
        if records:
            self._data_service.save_anomaly_records(records)

    # ── Outlook メール ────────────────────────────────────────────────────────

    def _open_outlook_email(
        self, reviewer: str, comment: str, is_forward: bool = False
    ) -> bool:
        """Outlook でメールを作成して表示する（Windows / pywin32 のみ）。"""
        try:
            import win32com.client as win32  # type: ignore
        except ImportError:
            return False

        task = self._task
        task_name = task.get("task_name", "")
        reviewer_email = self._data_service.get_user_email(reviewer)

        anomaly_rows = self._get_anomaly_rows_html()
        has_anomaly = bool(anomaly_rows)

        subject_prefix = "[Bunseki] "
        if has_anomaly:
            subject_prefix += "⚠ 異常データあり - "
        subject = f"{subject_prefix}分析結果の回覧 - {task_name}"

        html_body = self._build_email_html(
            task, reviewer, comment, anomaly_rows, is_forward
        )

        try:
            outlook = win32.Dispatch("Outlook.Application")
            mail = outlook.CreateItem(0)
            mail.To = reviewer_email or reviewer
            mail.Subject = subject
            mail.HTMLBody = html_body
            mail.Display()
            return True
        except Exception as e:
            QMessageBox.warning(
                self, "Outlook エラー", f"メール作成に失敗しました:\n{e}"
            )
            return False

    def _get_anomaly_rows_html(self) -> str:
        """回覧対象タスクの2σ超過行をHTMLテーブル行として返す。"""
        task = self._task
        hg_code = task.get("holder_group_code", "")
        jobs = task.get("job_numbers", [])
        vsset_codes = (
            task.get("state_data", {})
            .get("analysis_targets", {})
            .get("valid_sample_set_codes", [])
        )
        if not hg_code or not jobs:
            return ""
        df = self._data_service.get_result_data(hg_code, jobs, vsset_codes)
        if df.empty:
            return ""

        rows_html = ""
        for _, row in df.iterrows():
            is_anomaly = self._data_service.calculate_anomaly(row, hg_code)
            if is_anomaly is True:
                rows_html += (
                    "<tr style='background:#fff1f2;'>"
                    "<td style='padding:4px 8px;'>"
                    f"{row.get('valid_sample_display_name', '')}</td>"
                    "<td style='padding:4px 8px;'>"
                    f"{row.get('valid_test_display_name', '')}</td>"
                    "<td style='padding:4px 8px; font-weight:bold; color:#dc2626;'>"
                    f"{row.get('test_raw_data', '')}</td>"
                    "<td style='padding:4px 8px;'>"
                    f"{row.get('test_unit_name', '')}</td>"
                    "</tr>"
                )
        return rows_html

    def _build_email_html(
        self,
        task: dict,
        reviewer: str,
        comment: str,
        anomaly_rows_html: str,
        is_forward: bool,
    ) -> str:
        """回覧メールのHTML本文を生成する。"""
        task_name = task.get("task_name", "")
        hg_name = task.get("holder_group_name", "")
        jobs_str = "、".join(task.get("job_numbers", []))
        created_by = task.get("created_by", "")
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M")

        action_label = "次の確認者への回覧" if is_forward else "分析結果の回覧"

        warning_block = ""
        if anomaly_rows_html:
            warning_block = (
                "<div style='background:#fef2f2; border:1px solid #fca5a5;"
                " border-radius:6px; padding:12px 16px; margin:16px 0;'>"
                "<p style='margin:0 0 8px; font-weight:bold; color:#dc2626;'>"
                "⚠ 以下のサンプルで mean±2σ を超過するデータが検出されました"
                "</p>"
                "<table style='border-collapse:collapse; width:100%; font-size:13px;'>"
                "<thead><tr style='background:#fee2e2;'>"
                "<th style='padding:4px 8px; text-align:left;'>サンプル名</th>"
                "<th style='padding:4px 8px; text-align:left;'>試験項目</th>"
                "<th style='padding:4px 8px; text-align:left;'>データ</th>"
                "<th style='padding:4px 8px; text-align:left;'>単位</th>"
                f"</tr></thead><tbody>{anomaly_rows_html}</tbody></table>"
                "</div>"
            )

        comment_block = ""
        if comment.strip():
            escaped = comment.replace(chr(10), "<br>")
            comment_block = (
                "<div style='background:#f8fafc; border-left:3px solid #3b82f6;"
                " padding:8px 12px; margin:12px 0;'>"
                f"<p style='margin:0; font-size:13px; color:#374151;'>{escaped}</p>"
                "</div>"
            )

        return (
            "<html><body style='font-family:\"Segoe UI\",\"Yu Gothic UI\",sans-serif;"
            " font-size:14px; color:#1e293b;'>"
            "<div style='max-width:680px; margin:0 auto; background:#ffffff;'>"
            "<div style='background:#1e3a5f; padding:16px 24px;"
            " border-radius:8px 8px 0 0;'>"
            f"<h2 style='margin:0; color:white; font-size:16px;'>"
            f"Bunseki — {action_label}</h2>"
            f"<p style='margin:4px 0 0; color:#94a3b8; font-size:12px;'>{now_str}</p>"
            "</div>"
            "<div style='padding:20px 24px; border:1px solid #e2e8f0; border-top:none;'>"
            f"<p style='margin:0 0 12px;'>{reviewer} 様</p>"
            f"<p style='margin:0 0 16px;'>"
            f"下記タスクの{action_label}が届きました。ご確認をお願いいたします。</p>"
            "<table style='border-collapse:collapse; font-size:13px; margin-bottom:12px;'>"
            "<tr><td style='padding:4px 8px; color:#64748b; width:120px;'>タスク名</td>"
            f"<td style='padding:4px 8px; font-weight:bold;'>{task_name}</td></tr>"
            "<tr><td style='padding:4px 8px; color:#64748b;'>ホルダグループ</td>"
            f"<td style='padding:4px 8px;'>{hg_name}</td></tr>"
            "<tr><td style='padding:4px 8px; color:#64748b;'>JOB番号</td>"
            f"<td style='padding:4px 8px;'>{jobs_str}</td></tr>"
            "<tr><td style='padding:4px 8px; color:#64748b;'>起票者</td>"
            f"<td style='padding:4px 8px;'>{created_by}</td></tr>"
            "</table>"
            f"{warning_block}"
            f"{comment_block}"
            "</div>"
            "<div style='background:#f8fafc; padding:10px 24px; border:1px solid #e2e8f0;"
            " border-top:none; border-radius:0 0 8px 8px;'>"
            "<p style='margin:0; font-size:11px; color:#94a3b8;'>"
            f"このメールは Bunseki ver.{_cfg.APP_VERSION} から自動生成されました。"
            "</p></div></div></body></html>"
        )
