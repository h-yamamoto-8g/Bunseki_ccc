"""JOBマスタのサービス層。

UIはこのクラスのみを通じてJOBを操作する。
core.job_store にのみ依存し、UIに依存しない。
"""
from __future__ import annotations

from datetime import date

from app.core import job_store


class JobService:
    """JOBマスタ操作のビジネスロジック。"""

    def get_all_jobs(self) -> list[dict]:
        return job_store.get_all()

    def get_job(self, job_id: str) -> dict | None:
        return job_store.get(job_id)

    def create_job(
        self,
        job_number: str,
        start_date: str,
        end_date: str,
        created_by: str,
        notes: str = "",
    ) -> dict:
        return job_store.create(job_number, start_date, end_date, created_by, notes)

    def update_job(self, job_id: str, **fields) -> dict | None:
        return job_store.update(job_id, **fields)

    def delete_job(self, job_id: str) -> bool:
        return job_store.delete(job_id)

    def get_valid_job_numbers(self) -> list[str]:
        """本日が有効期間内にある有効JOBのjob_numberリストを返す。

        is_active=True かつ start_date <= today <= end_date のJOBを抽出する。
        """
        today = date.today().isoformat()
        result = []
        for job in job_store.get_all():
            if not job.get("is_active", True):
                continue
            start = job.get("start_date", "")
            end = job.get("end_date", "")
            if start and end and start <= today <= end:
                result.append(job["job_number"])
        return result
