"""SubmissionState — 回覧ステートのUIラッパー。

SubmissionUI のシグナルを受け取り、TaskService / DataService を介して
タスク状態の保存・添付ファイルコピー・Outlook メール作成などを実行する。
"""
from __future__ import annotations

import shutil
from datetime import datetime
from pathlib import Path

from PySide6.QtWidgets import QWidget, QVBoxLayout, QMessageBox
from PySide6.QtCore import Signal

import app.config as _cfg
from app.services.task_service import TaskService
from app.services.data_service import DataService
from app.services.circulation_mail_service import CirculationMailService
from app.ui.dialogs.loading_dialog import LoadingDialog
from .state import SubmissionUI


def _attachments_root():
    return _cfg.DATA_PATH / "bunseki" / "attachments"


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
        self._mail_service = CirculationMailService(data_service)
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
        self._ui.comment_add_requested.connect(self._on_add_comment)
        self._ui.comment_delete_requested.connect(self._on_delete_comment)

    # ── Public API ────────────────────────────────────────────────────────────

    def load_task(self, task: dict, readonly: bool = False) -> None:
        """タスクデータをUIにロードする。"""
        self._task = task

        reviewers = self._data_service.get_reviewers()
        user_names = [u["name"] for u in reviewers]
        self._ui.set_available_users(user_names)

        self._ui.set_creator(task.get("created_by", ""))
        self._ui.set_current_user(_cfg.CURRENT_USER)

        sd = task.get("state_data", {}).get("submission", {})
        self._ui.set_reviewers(sd.get("reviewers", []))
        comments = list(sd.get("comments", []))
        legacy_comment = str(sd.get("comment", "")).strip()
        if not comments and legacy_comment:
            comments = [
                {
                    "id": "legacy_comment",
                    "author": task.get("created_by", ""),
                    "text": legacy_comment,
                    "created_at": task.get("updated_at", ""),
                    "pending": False,
                }
            ]
        self._ui.set_comments(comments)
        self._ui.set_comment("")
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
        comment_text = comment.strip()
        if comment_text:
            self._task = self._task_service.add_submission_comment(
                task_id, _cfg.CURRENT_USER, comment_text
            )
            self._task = self._task_service.finalize_submission_comments(
                task_id, _cfg.CURRENT_USER
            )
            self._ui.clear_draft_comment()

        stored_paths = self._copy_attachments(task_id, attachments)

        LoadingDialog(
            lambda: self._record_sigma_anomalies(task_id), parent=self
        ).exec()

        submission_data = (
            self._task.get("state_data", {}).get("submission", {})
            if self._task
            else {}
        )
        comments = submission_data.get("comments", [])
        base_comment = comments[-1]["text"] if comments else ""

        self._task = self._task_service.save_submission(
            task_id, reviewers, base_comment, stored_paths
        )

        self._ui.apply_mode("sent_analyst", current_reviewer_index=0)

        self._send_circulation_mail(reviewers[0], base_comment)

    def _on_forward(self) -> None:
        """確認者 → 次の確認者へ送信。"""
        task_id = self._task["task_id"]
        self._task = self._task_service.update_submission_reviewers(
            task_id, self._ui.get_reviewers()
        )

        draft = self._ui.get_draft_comment()
        if draft:
            self._task = self._task_service.add_submission_comment(
                task_id, _cfg.CURRENT_USER, draft
            )
            self._ui.clear_draft_comment()
        self._task = self._task_service.finalize_submission_comments(
            task_id, _cfg.CURRENT_USER
        )

        self._task = self._task_service.forward_submission(task_id)

        sd = self._task.get("state_data", {}).get("submission", {})
        new_idx = sd.get("current_reviewer_index", 0)
        reviewers = sd.get("reviewers", [])
        next_reviewer = reviewers[new_idx] if new_idx < len(reviewers) else ""

        mode, idx = self._determine_mode(self._task, readonly=False)
        self._ui.apply_mode(mode, current_reviewer_index=idx)

        self._send_circulation_mail(next_reviewer, "", is_forward=True)

    def _on_return(self) -> None:
        """確認者 → 分析者へ差し戻し。"""
        task_id = self._task["task_id"]
        draft = self._ui.get_draft_comment()
        if draft:
            self._task = self._task_service.add_submission_comment(
                task_id, _cfg.CURRENT_USER, draft
            )
            self._ui.clear_draft_comment()
        self._task = self._task_service.finalize_submission_comments(
            task_id, _cfg.CURRENT_USER
        )
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
        task_id = self._task["task_id"]
        draft = self._ui.get_draft_comment()
        if draft:
            self._task = self._task_service.add_submission_comment(
                task_id, _cfg.CURRENT_USER, draft
            )
            self._ui.clear_draft_comment()
        self._task = self._task_service.finalize_submission_comments(
            task_id, _cfg.CURRENT_USER
        )
        self._task = self._task_service.complete_task(self._task["task_id"])

        # 完了通知メールを送信
        self._send_complete_email()

        self.go_next.emit()

    def _send_complete_email(self) -> None:
        """タスク完了通知メールを作成する。"""
        task = self._task
        sd = task.get("state_data", {}).get("submission", {})
        reviewers = sd.get("reviewers", [])
        creator = task.get("created_by", "")

        # To: 分析者 + 全確認者（自分は除外）
        to_names: set[str] = set()
        if creator:
            to_names.add(creator)
        for name in reviewers:
            if name:
                to_names.add(name)
        to_names.discard(_cfg.CURRENT_USER)

        to_emails: list[str] = []
        for name in to_names:
            email = self._data_service.get_user_email(name)
            if email:
                to_emails.append(email)

        if not to_emails:
            return

        result: dict = {}
        LoadingDialog(
            lambda: result.update(
                anomalies=self._mail_service.detect_anomalies(task)
            ),
            parent=self,
        ).exec()
        anomalies = result.get("anomalies", [])
        subject = self._mail_service.build_subject(
            task, anomalies, is_complete=True
        )
        html = self._mail_service.build_html(
            task, "", anomalies, is_complete=True
        )

        # To: 分析者のみ、CC: 残りの確認者 + 異常メール受信者
        creator_email = self._data_service.get_user_email(creator)
        cc_emails = [e for e in to_emails if e != creator_email]
        to_str, cc_str = self._mail_service.collect_to_cc(
            task, creator, bool(anomalies),
            to_emails_override=[creator_email] if creator_email else [],
            extra_cc=cc_emails,
        )
        ok, err = self._mail_service.open_outlook(to_str, cc_str, subject, html)
        if not ok:
            QMessageBox.warning(self, "メール作成", err)

    def _on_add_comment(self, text: str) -> None:
        task_id = self._task.get("task_id", "")
        if not task_id:
            return
        self._task = self._task_service.add_submission_comment(
            task_id, _cfg.CURRENT_USER, text
        )
        self._ui.clear_draft_comment()
        comments = (
            self._task.get("state_data", {})
            .get("submission", {})
            .get("comments", [])
        )
        self._ui.set_comments(comments)

    def _on_delete_comment(self, comment_id: str) -> None:
        if not comment_id:
            return
        task_id = self._task.get("task_id", "")
        if not task_id:
            return
        self._task = self._task_service.delete_submission_comment(
            task_id, comment_id, _cfg.CURRENT_USER
        )
        comments = (
            self._task.get("state_data", {})
            .get("submission", {})
            .get("comments", [])
        )
        self._ui.set_comments(comments)

    # ── Private helpers ───────────────────────────────────────────────────────

    def _copy_attachments(self, task_id: str, files: list[dict]) -> list[dict]:
        """添付ファイルを app_data/bunseki/attachments/{task_id}/ にコピーする。

        保存パスは DATA_PATH からの相対パスで返す（SharePoint 共有対応）。
        """
        if not files:
            return []
        dest_dir = _attachments_root() / task_id
        dest_dir.mkdir(parents=True, exist_ok=True)
        stored: list[dict] = []
        for att in files:
            src_path = att["path"] if isinstance(att, dict) else att
            added_by = att.get("added_by", "") if isinstance(att, dict) else ""
            src = Path(src_path)
            if not src.exists():
                stored.append({"path": src_path, "added_by": added_by})
                continue
            dest = dest_dir / src.name
            shutil.copy2(src, dest)
            # DATA_PATH からの相対パスで保存（ユーザー間で共有可能にする）
            rel = str(dest.relative_to(_cfg.DATA_PATH))
            stored.append({"path": rel, "added_by": added_by})
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

    # ── 回覧メール ─────────────────────────────────────────────────────────

    def _send_circulation_mail(
        self,
        to_name: str,
        comment: str,
        *,
        is_forward: bool = False,
    ) -> None:
        """回覧 / 転送メールを作成して Outlook で表示する。"""
        task = self._task
        ms = self._mail_service

        result: dict = {}
        LoadingDialog(
            lambda: result.update(anomalies=ms.detect_anomalies(task)),
            parent=self,
        ).exec()
        anomalies = result.get("anomalies", [])
        has_anomaly = bool(anomalies)

        to_str, cc_str = ms.collect_to_cc(task, to_name, has_anomaly)
        subject = ms.build_subject(task, anomalies)
        html = ms.build_html(
            task, comment, anomalies, is_forward=is_forward
        )

        ok, err = ms.open_outlook(to_str, cc_str, subject, html)
        if not ok:
            QMessageBox.warning(self, "メール作成", err)
