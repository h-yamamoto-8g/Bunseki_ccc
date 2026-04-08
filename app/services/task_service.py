"""タスクのCRUD・状態遷移・フィルタ・統計をまとめたサービス層。

UIはこのクラスのみを通じてタスクを操作する。
core.task_store にのみ依存し、UI / DataLoader に依存しない。
"""
from __future__ import annotations

from datetime import datetime
from uuid import uuid4

from app.core import task_store


class TaskService:
    """タスク操作のビジネスロジック。Core(task_store)のみに依存。"""

    # ── CRUD ─────────────────────────────────────────────────────────────────

    def get_all_tasks(self) -> list[dict]:
        return task_store.load_tasks()

    def get_task(self, task_id: str) -> dict | None:
        return task_store.get_task(task_id)

    def delete_task(self, task_id: str) -> bool:
        """タスクを削除する。成功したら True を返す。"""
        return task_store.delete_task(task_id)

    # ── フィルタ・集計 ────────────────────────────────────────────────────────

    def filter_tasks(self, tasks: list[dict], filter_key: str) -> list[dict]:
        """filter_key: '全件'|'進行中'|'終了'|'マイタスク'|user_name"""
        if filter_key == "進行中":
            return [t for t in tasks if t.get("status") not in ("終了",)]
        elif filter_key == "終了":
            return [t for t in tasks if t.get("status") == "終了"]
        elif filter_key == "マイタスク":
            from app.config import CURRENT_USER
            return [t for t in tasks if t.get("assigned_to") == CURRENT_USER]
        elif filter_key not in ("全件", ""):
            # user_name 直接指定フィルタ（後方互換）
            return [t for t in tasks if t.get("assigned_to") == filter_key]
        return list(tasks)

    def get_task_stats(self, tasks: list[dict]) -> dict:
        """統計チップ用の集計値を返す。"""
        now = datetime.now()
        month_pfx = now.strftime("%Y-%m")
        return {
            "in_progress": sum(1 for t in tasks if t.get("status") == "進行中"),
            "circulation": sum(1 for t in tasks if t.get("status") == "回覧中"),
            "done_month": sum(
                1 for t in tasks
                if t.get("status") == "終了"
                and t.get("updated_at", "").startswith(month_pfx)
            ),
            "total": len(tasks),
        }

    # ── 状態遷移 ──────────────────────────────────────────────────────────────

    def create_task_setup(
        self, hg_code: str, hg_name: str, job_numbers: list[str]
    ) -> dict:
        """新規タスクを起票して返す。"""
        return task_store.create_task(hg_code, hg_name, job_numbers)

    def update_task_setup(
        self,
        task_id: str,
        hg_code: str,
        hg_name: str,
        job_numbers: list[str],
        in_edit: bool,
    ) -> dict:
        """既存タスクの起票情報を更新して返す。

        in_edit=True の場合は元タスクを削除し新規タスクを起票する。
        """
        if in_edit:
            task_store.delete_task(task_id)
            return task_store.create_task(hg_code, hg_name, job_numbers)
        task = task_store.get_task(task_id)
        return task

    def save_analysis_targets(
        self,
        task_id: str,
        vsset_codes: list[str],
        deleted_codes: list[str],
        added_samples: list[str],
        in_edit: bool,
    ) -> dict:
        """分析対象を保存して返す。"""
        if in_edit:
            task_store.invalidate_after(task_id, "analysis_targets")

        state_data = {
            "valid_sample_set_codes": vsset_codes,
            "deleted_codes": deleted_codes,
            "added_samples": added_samples,
            "completed": True,
        }
        task_store.update_task_state(task_id, "analysis_targets", state_data)

        # 初回通過時のみ次ステートをセット
        task = task_store.get_task(task_id)
        if task and task.get("current_state") == "analysis_targets":
            task_store.update_task_state(task_id, "analysis")

        return task_store.get_task(task_id)

    def save_analysis(
        self,
        task_id: str,
        pre_checks: list[bool],
        post_checks: list[bool],
    ) -> dict:
        """分析準備チェックリストを保存して返す。"""
        state_data = {
            "pre_checks": pre_checks,
            "post_checks": post_checks,
            "completed": True,
        }
        task_store.update_task_state(task_id, "analysis", state_data)
        task_store.update_task_state(task_id, "result_entry")
        return task_store.get_task(task_id)

    def save_result_entry(self, task_id: str) -> dict:
        """データ入力完了を記録して返す。"""
        task_store.update_task_state(task_id, "result_entry", {"completed": True})
        task_store.update_task_state(task_id, "result_verification")
        return task_store.get_task(task_id)

    def save_result_verification(
        self, task_id: str, checks: list[bool]
    ) -> dict:
        """データ確認チェックリストを保存して返す。"""
        state_data = {
            "checks": checks,
            "completed": True,
        }
        task_store.update_task_state(task_id, "result_verification", state_data)
        task_store.update_task_state(task_id, "submission")
        return task_store.get_task(task_id)

    def save_submission(
        self,
        task_id: str,
        reviewers: list[str],
        comment: str,
        attachments: list[str],
    ) -> dict:
        """回覧送信: 最初の確認者に送る。"""
        task = task_store.get_task(task_id)
        existing = task.get("state_data", {}).get("submission", {})
        comments = list(existing.get("comments", []))
        if not comments and comment.strip():
            comments.append(
                {
                    "id": f"cm_{uuid4().hex}",
                    "author": task.get("created_by", ""),
                    "text": comment.strip(),
                    "created_at": datetime.now().isoformat(),
                    "pending": False,
                }
            )

        state_data = {
            "reviewers": reviewers,
            "current_reviewer_index": 0,
            "comment": comment,
            "comments": comments,
            "attachments": attachments,
            "completed": False,
        }
        task_store.update_task_state(task_id, "submission", state_data)
        task_store.update_task_field(
            task_id, status="回覧中", assigned_to=reviewers[0]
        )
        return task_store.get_task(task_id)

    def forward_submission(self, task_id: str) -> dict:
        """次の確認者へ送信する。"""
        task = task_store.get_task(task_id)
        sd = task["state_data"]["submission"]
        idx = sd["current_reviewer_index"] + 1
        sd["current_reviewer_index"] = idx
        task_store.update_task_state(task_id, "submission", sd)
        task_store.update_task_field(
            task_id, assigned_to=sd["reviewers"][idx]
        )
        return task_store.get_task(task_id)

    def update_submission_reviewers(self, task_id: str, reviewers: list[str]) -> dict:
        """回覧中の確認者リストを更新する。"""
        task = task_store.get_task(task_id)
        sd = task.get("state_data", {}).get("submission", {})
        current_idx = int(sd.get("current_reviewer_index", 0))
        if not reviewers:
            return task

        # 現在担当者より前は固定。担当者以降のみ更新対象にする。
        original = list(sd.get("reviewers", []))
        if original and 0 <= current_idx < len(original):
            fixed = original[: current_idx + 1]
            suffix = [r for r in reviewers if r not in fixed]
            merged = fixed + suffix
        else:
            merged = list(reviewers)

        sd["reviewers"] = merged
        self._save_submission_state_data(task_id, sd)
        return task_store.get_task(task_id)

    def add_submission_comment(self, task_id: str, author: str, text: str) -> dict:
        """回覧コメントを追加する（pending=True）。"""
        body = text.strip()
        if not body:
            return task_store.get_task(task_id)
        task = task_store.get_task(task_id)
        sd = task.get("state_data", {}).get("submission", {})
        comments = list(sd.get("comments", []))
        comments.append(
            {
                "id": f"cm_{uuid4().hex}",
                "author": author,
                "text": body,
                "created_at": datetime.now().isoformat(),
                "pending": True,
            }
        )
        sd["comments"] = comments
        self._save_submission_state_data(task_id, sd)
        return task_store.get_task(task_id)

    def delete_submission_comment(
        self, task_id: str, comment_id: str, requested_by: str
    ) -> dict:
        """未引き渡し（pending）の自コメントのみ削除する。"""
        task = task_store.get_task(task_id)
        sd = task.get("state_data", {}).get("submission", {})
        comments = list(sd.get("comments", []))
        kept: list[dict] = []
        for c in comments:
            if c.get("id") != comment_id:
                kept.append(c)
                continue
            if c.get("author") != requested_by or not c.get("pending", False):
                kept.append(c)
        sd["comments"] = kept
        self._save_submission_state_data(task_id, sd)
        return task_store.get_task(task_id)

    def finalize_submission_comments(self, task_id: str, author: str) -> dict:
        """引き渡し時に、担当者の pending コメントを確定する。"""
        task = task_store.get_task(task_id)
        sd = task.get("state_data", {}).get("submission", {})
        comments = list(sd.get("comments", []))
        changed = False
        for c in comments:
            if c.get("author") == author and c.get("pending", False):
                c["pending"] = False
                changed = True
        if changed:
            sd["comments"] = comments
            self._save_submission_state_data(task_id, sd)
        return task_store.get_task(task_id)

    def reclaim_submission(self, task_id: str) -> dict:
        """取り戻し/差し戻し: 起票者に戻す。"""
        task = task_store.get_task(task_id)
        sd = task.get("state_data", {}).get("submission", {})
        sd["current_reviewer_index"] = 0
        all_state_data = dict(task.get("state_data", {}))
        all_state_data["submission"] = sd
        task_store.update_task_field(
            task_id,
            current_state="submission",
            state_data=all_state_data,
            status="進行中",
            assigned_to=task["created_by"],
        )
        return task_store.get_task(task_id)

    def complete_task(self, task_id: str) -> dict:
        """タスクを終了状態にして返す。"""
        task_store.update_task_state(task_id, "completed", {"completed": True})
        return task_store.get_task(task_id)

    def handover_task(
        self, task_id: str, new_assignee: str, operated_by: str
    ) -> dict:
        """担当者を変更して返す。"""
        task_store.handover_task(task_id, new_assignee, operated_by)
        return task_store.get_task(task_id)

    # ── ヘルパー ──────────────────────────────────────────────────────────────

    def is_task_readonly(self, task: dict) -> bool:
        return task.get("status") == "終了"

    def is_setup_done(self, task: dict) -> bool:
        return task.get("state_data", {}).get("task_setup", {}).get("completed", False)

    def _save_submission_state_data(self, task_id: str, submission_data: dict) -> None:
        """current_state/status を変えずに submission の state_data だけ更新する。"""
        task = task_store.get_task(task_id)
        all_state_data = dict(task.get("state_data", {}))
        all_state_data["submission"] = submission_data
        task_store.update_task_field(task_id, state_data=all_state_data)
