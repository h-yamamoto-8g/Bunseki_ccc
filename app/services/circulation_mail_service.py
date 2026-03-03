"""回覧メール作成サービス。

回覧送信・転送・完了時のメール宛先構築、異常検出（2σ超過 + 基準値超過）、
公式HTMLメール本文生成、Outlook 起動を一元管理する。
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime

import pandas as pd

import app.config as _cfg
from app.services.data_service import DataService


# ── 異常レコード DTO ──────────────────────────────────────────────────────────

@dataclass
class AnomalyRecord:
    """メール本文に表示する異常行。"""

    sample_name: str
    test_name: str
    value: str
    unit: str
    kind: str  # "2σ超過" | "基準値超過" | judgment テキスト


# ── サービス本体 ──────────────────────────────────────────────────────────────

class CirculationMailService:
    """回覧メールの宛先・本文・送信を管理するサービス。"""

    def __init__(self, data_service: DataService) -> None:
        self._ds = data_service

    # ── 異常検出 ──────────────────────────────────────────────────────────────

    def detect_anomalies(self, task: dict) -> list[AnomalyRecord]:
        """タスクの結果データから 2σ超過・基準値超過を全て検出する。

        result_verification/state.py の判定ロジックと同一基準で判定する。
        """
        hg_code = task.get("holder_group_code", "")
        jobs = task.get("job_numbers", [])
        vsset_codes = (
            task.get("state_data", {})
            .get("analysis_targets", {})
            .get("valid_sample_set_codes", [])
        )
        if not hg_code or not jobs:
            return []

        df = self._ds.get_result_data(hg_code, jobs, vsset_codes)
        if df.empty:
            return []

        records: list[AnomalyRecord] = []
        for _, row in df.iterrows():
            rec = self._check_row(row, hg_code)
            if rec:
                records.append(rec)
        return records

    def _check_row(self, row: pd.Series, hg_code: str) -> AnomalyRecord | None:
        """1行ごとに判定 → 異常なら AnomalyRecord を返す。"""
        judgment_raw = str(row.get("test_judgment", ""))

        # 1) test_judgment に値がある → そのまま異常扱い
        if judgment_raw and judgment_raw not in ("nan", "None", "NN", ""):
            return AnomalyRecord(
                sample_name=str(row.get("valid_sample_display_name", "")),
                test_name=str(row.get("valid_test_display_name", "")),
                value=str(row.get("test_raw_data", "")),
                unit=str(row.get("test_unit_name", "")),
                kind=judgment_raw,
            )

        # 2) 基準値超過チェック
        raw_num = self._ds.extract_numeric(str(row.get("test_raw_data", "")))
        if raw_num is not None:
            upper_vals = [
                row.get(f"test_upper_limit_spec_{i}")
                for i in range(1, 5)
                if pd.notna(row.get(f"test_upper_limit_spec_{i}"))
            ]
            lower_vals = [
                row.get(f"test_lower_limit_spec_{i}")
                for i in range(1, 5)
                if pd.notna(row.get(f"test_lower_limit_spec_{i}"))
            ]
            spec_over = False
            if upper_vals and raw_num > min(upper_vals):
                spec_over = True
            elif lower_vals and raw_num < max(lower_vals):
                spec_over = True

            if spec_over:
                return AnomalyRecord(
                    sample_name=str(row.get("valid_sample_display_name", "")),
                    test_name=str(row.get("valid_test_display_name", "")),
                    value=str(row.get("test_raw_data", "")),
                    unit=str(row.get("test_unit_name", "")),
                    kind="基準値超過",
                )

        # 3) mean±2σ チェック
        trend_enabled = row.get("trend_enabled") is True
        if trend_enabled:
            is_anomaly = self._ds.calculate_anomaly(row, hg_code)
            if is_anomaly is True:
                return AnomalyRecord(
                    sample_name=str(row.get("valid_sample_display_name", "")),
                    test_name=str(row.get("valid_test_display_name", "")),
                    value=str(row.get("test_raw_data", "")),
                    unit=str(row.get("test_unit_name", "")),
                    kind="2σ超過",
                )

        return None

    # ── 宛先構築 ──────────────────────────────────────────────────────────────

    def collect_to_cc(
        self,
        task: dict,
        to_name: str,
        has_anomaly: bool,
        *,
        to_emails_override: list[str] | None = None,
        extra_cc: list[str] | None = None,
    ) -> tuple[str, str]:
        """To / CC のメールアドレス文字列を返す。

        To  = 回覧先（次の確認者）のみ
        CC  = 自分よりフローが前のユーザー
        異常時: CC に is_anomaly_mail=True のユーザーを追加

        Returns:
            (to_str, cc_str) — セミコロン区切り。
        """
        sd = task.get("state_data", {}).get("submission", {})
        reviewers = sd.get("reviewers", [])
        current_idx = sd.get("current_reviewer_index", 0)
        creator = task.get("created_by", "")

        # ---- To ----
        if to_emails_override:
            to_str = "; ".join(to_emails_override)
        else:
            to_email = self._ds.get_user_email(to_name)
            to_str = to_email or to_name

        # ---- CC: 起票者 + 自分より前の確認者 ----
        cc_names: set[str] = set()
        if creator:
            cc_names.add(creator)
        for name in reviewers[:current_idx]:
            if name:
                cc_names.add(name)
        # 自分と To を除外
        cc_names.discard(_cfg.CURRENT_USER)
        cc_names.discard(to_name)

        cc_emails: list[str] = []
        seen: set[str] = set()
        if to_emails_override:
            seen.update(to_emails_override)
        else:
            seen.add(to_str)

        for name in cc_names:
            email = self._ds.get_user_email(name)
            if email and email not in seen:
                cc_emails.append(email)
                seen.add(email)

        # extra_cc（完了メール等で呼び出し元から追加される CC）
        for addr in (extra_cc or []):
            if addr and addr not in seen:
                cc_emails.append(addr)
                seen.add(addr)

        # ---- 異常時: is_anomaly_mail ユーザーを追加 ----
        if has_anomaly:
            for addr in self._ds.get_anomaly_mail_recipients():
                if addr not in seen:
                    cc_emails.append(addr)
                    seen.add(addr)

        return to_str, "; ".join(cc_emails)

    # ── HTML 本文生成 ─────────────────────────────────────────────────────────

    def build_subject(
        self,
        task: dict,
        anomalies: list[AnomalyRecord],
        *,
        is_complete: bool = False,
    ) -> str:
        """メール件名を生成する。"""
        task_name = task.get("task_name", "")
        prefix = "[Bunseki] "
        if anomalies:
            prefix += "⚠ 異常データあり - "
        if is_complete:
            return f"{prefix}タスク完了通知 - {task_name}"
        return f"{prefix}分析結果の回覧 - {task_name}"

    def build_html(
        self,
        task: dict,
        comment: str,
        anomalies: list[AnomalyRecord],
        *,
        is_forward: bool = False,
        is_complete: bool = False,
    ) -> str:
        """公式感のあるHTMLメール本文を生成する。"""
        task_name = task.get("task_name", "")
        hg_name = task.get("holder_group_name", "")
        jobs_str = "、".join(task.get("job_numbers", []))
        created_by = task.get("created_by", "")
        now_str = datetime.now().strftime("%Y年%m月%d日 %H:%M")

        if is_complete:
            action_label = "タスク完了通知"
            header_bg = "#166534"
        elif is_forward:
            action_label = "分析結果の確認依頼"
            header_bg = "#1e3a5f"
        else:
            action_label = "分析結果の回覧"
            header_bg = "#1e3a5f"

        # ── パーツ組み立て ──
        complete_badge = ""
        if is_complete:
            complete_badge = (
                "<div style='background:#f0fdf4; border:1px solid #86efac;"
                " border-radius:6px; padding:14px 18px; margin:0 0 20px;'>"
                "<p style='margin:0; font-weight:bold; color:#166534; font-size:14px;'>"
                "&#10003; タスク完了</p></div>"
            )

        anomaly_block = self._build_anomaly_block(anomalies) if anomalies else ""

        comment_block = ""
        if comment.strip():
            escaped = comment.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
            escaped = escaped.replace(chr(10), "<br>")
            comment_block = (
                "<div style='background:#f8fafc; border-left:3px solid #3b82f6;"
                " padding:10px 14px; margin:16px 0;'>"
                "<p style='margin:0 0 4px; font-size:11px; color:#64748b;"
                " font-weight:600;'>コメント</p>"
                f"<p style='margin:0; font-size:13px; color:#374151;'>{escaped}</p>"
                "</div>"
            )

        return (
            "<html><head><meta charset='utf-8'></head>"
            "<body style='margin:0; padding:0; background:#f1f5f9;"
            " font-family:\"Yu Gothic UI\",\"Segoe UI\",\"Hiragino Sans\",sans-serif;"
            " font-size:14px; color:#1e293b;'>"
            "<div style='max-width:680px; margin:20px auto; background:#ffffff;"
            " border-radius:8px; overflow:hidden;"
            " box-shadow:0 1px 3px rgba(0,0,0,0.08);'>"
            # ── ヘッダー ──
            f"<div style='background:{header_bg}; padding:20px 28px;'>"
            "<table style='width:100%; border:none;'><tr>"
            "<td style='padding:0; border:none;'>"
            f"<h2 style='margin:0; color:#ffffff; font-size:17px;"
            f" font-weight:700; letter-spacing:0.3px;'>Bunseki</h2>"
            f"<p style='margin:4px 0 0; color:#94a3b8; font-size:12px;'>"
            f"{action_label}</p></td>"
            "<td style='padding:0; border:none; text-align:right; vertical-align:top;'>"
            f"<span style='color:#94a3b8; font-size:11px;'>{now_str}</span>"
            "</td></tr></table></div>"
            # ── 本文 ──
            "<div style='padding:24px 28px;'>"
            f"{complete_badge}"
            # ── タスク情報テーブル ──
            "<table style='border-collapse:collapse; width:100%; font-size:13px;"
            " margin-bottom:16px; border:1px solid #e2e8f0; border-radius:6px;'>"
            "<tr style='background:#f8fafc;'>"
            "<td style='padding:8px 14px; color:#64748b; width:130px;"
            " border-bottom:1px solid #e2e8f0; font-weight:600;'>タスク名</td>"
            f"<td style='padding:8px 14px; border-bottom:1px solid #e2e8f0;"
            f" font-weight:bold;'>{task_name}</td></tr>"
            "<tr><td style='padding:8px 14px; color:#64748b;"
            " border-bottom:1px solid #e2e8f0; font-weight:600;'>ホルダグループ</td>"
            f"<td style='padding:8px 14px;"
            f" border-bottom:1px solid #e2e8f0;'>{hg_name}</td></tr>"
            "<tr style='background:#f8fafc;'>"
            "<td style='padding:8px 14px; color:#64748b;"
            " border-bottom:1px solid #e2e8f0; font-weight:600;'>JOB番号</td>"
            f"<td style='padding:8px 14px;"
            f" border-bottom:1px solid #e2e8f0;'>{jobs_str}</td></tr>"
            "<tr><td style='padding:8px 14px; color:#64748b;"
            " font-weight:600;'>分析担当者</td>"
            f"<td style='padding:8px 14px;'>{created_by}</td></tr>"
            "</table>"
            # ── 異常ブロック ──
            f"{anomaly_block}"
            # ── コメント ──
            f"{comment_block}"
            "</div>"
            # ── フッター ──
            "<div style='background:#f8fafc; padding:12px 28px;"
            " border-top:1px solid #e2e8f0;'>"
            "<p style='margin:0; font-size:11px; color:#94a3b8;'>"
            f"このメールは Bunseki ver.{_cfg.APP_VERSION} から自動生成されました。"
            "</p></div></div></body></html>"
        )

    def _build_anomaly_block(self, anomalies: list[AnomalyRecord]) -> str:
        """異常データブロックの HTML を生成する。"""
        rows = ""
        for i, a in enumerate(anomalies):
            bg = "#fff1f2" if i % 2 == 0 else "#ffffff"
            kind_color = "#dc2626" if a.kind == "基準値超過" else "#b91c1c"
            rows += (
                f"<tr style='background:{bg};'>"
                f"<td style='padding:6px 10px; border-bottom:1px solid #fecaca;'>"
                f"{a.sample_name}</td>"
                f"<td style='padding:6px 10px; border-bottom:1px solid #fecaca;'>"
                f"{a.test_name}</td>"
                f"<td style='padding:6px 10px; border-bottom:1px solid #fecaca;"
                f" font-weight:bold; color:#dc2626;'>{a.value}</td>"
                f"<td style='padding:6px 10px; border-bottom:1px solid #fecaca;'>"
                f"{a.unit}</td>"
                f"<td style='padding:6px 10px; border-bottom:1px solid #fecaca;"
                f" color:{kind_color}; font-weight:600;'>{a.kind}</td>"
                "</tr>"
            )

        sigma_count = sum(1 for a in anomalies if a.kind == "2σ超過")
        spec_count = sum(1 for a in anomalies if a.kind == "基準値超過")
        other_count = len(anomalies) - sigma_count - spec_count
        summary_parts: list[str] = []
        if spec_count:
            summary_parts.append(f"基準値超過 {spec_count}件")
        if sigma_count:
            summary_parts.append(f"2σ超過 {sigma_count}件")
        if other_count:
            summary_parts.append(f"その他 {other_count}件")
        summary_text = "、".join(summary_parts)

        return (
            "<div style='background:#fef2f2; border:1px solid #fca5a5;"
            " border-radius:6px; padding:14px 18px; margin:0 0 16px;'>"
            "<p style='margin:0 0 4px; font-weight:bold; color:#dc2626;"
            " font-size:14px;'>"
            "&#9888; 異常データが検出されました</p>"
            f"<p style='margin:0 0 10px; font-size:12px; color:#991b1b;'>"
            f"{summary_text}</p>"
            "<table style='border-collapse:collapse; width:100%; font-size:13px;'>"
            "<thead><tr style='background:#fee2e2;'>"
            "<th style='padding:6px 10px; text-align:left;"
            " border-bottom:1px solid #fca5a5;'>サンプル名</th>"
            "<th style='padding:6px 10px; text-align:left;"
            " border-bottom:1px solid #fca5a5;'>試験項目</th>"
            "<th style='padding:6px 10px; text-align:left;"
            " border-bottom:1px solid #fca5a5;'>データ</th>"
            "<th style='padding:6px 10px; text-align:left;"
            " border-bottom:1px solid #fca5a5;'>単位</th>"
            "<th style='padding:6px 10px; text-align:left;"
            " border-bottom:1px solid #fca5a5;'>種別</th>"
            f"</tr></thead><tbody>{rows}</tbody></table></div>"
        )

    # ── Outlook 起動 ──────────────────────────────────────────────────────────

    def open_outlook(
        self, to: str, cc: str, subject: str, html_body: str
    ) -> tuple[bool, str]:
        """Outlook でメールを作成して表示する（Windows / pywin32 のみ）。

        Returns:
            (True, "") : メール作成・表示成功。
            (False, msg): 失敗理由。
        """
        try:
            import win32com.client as win32  # type: ignore
        except ImportError:
            return False, "pywin32 が未導入のため Outlook を起動できません。"

        try:
            outlook = win32.Dispatch("Outlook.Application")
            mail = outlook.CreateItem(0)
            mail.To = to
            if cc:
                mail.CC = cc
            mail.Subject = subject
            mail.HTMLBody = html_body
            mail.Display()
            return True, ""
        except Exception as e:
            return False, f"Outlook メール作成に失敗しました:\n{e}"
