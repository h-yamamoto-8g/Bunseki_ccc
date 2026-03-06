import re
import json
from datetime import datetime, timedelta
import numpy as np
import pandas as pd
from pathlib import Path


class DataLoader:
    def __init__(self, data_path: Path):
        self.data_path = data_path
        self.common_path = data_path / "_common"
        self.master_path = self.common_path / "master_data" / "source"
        self.csv_path = self.common_path / "data" / "lab_aid" / "normalized" / "bunseki.csv"
        self._df: pd.DataFrame | None = None

    @property
    def df(self) -> pd.DataFrame:
        if self._df is None:
            for enc in ("utf-8-sig", "cp932", "utf-8"):
                try:
                    self._df = pd.read_csv(
                        self.csv_path,
                        encoding=enc,
                        low_memory=False,
                        dtype={
                            "sample_job_number": str,
                            "test_raw_data": str,
                            "test_judgment": str,
                            "test_grade_code": str,
                            "trend_enabled": str,
                        },
                    )
                    break
                except UnicodeDecodeError:
                    continue
            else:
                raise RuntimeError(f"bunseki.csv のエンコーディングを判定できません: {self.csv_path}")
            # Normalize boolean
            self._df["trend_enabled"] = self._df["trend_enabled"].str.lower().map(
                {"true": True, "false": False, "1": True, "0": False}
            )
        return self._df

    # ── Master data ──────────────────────────────────────────────────────────

    def get_users(self) -> list[dict]:
        """users.json からアクティブユーザーの一覧を返す。"""
        path = self.data_path / "bunseki" / "config" / "users.json"
        if not path.exists():
            return []
        with open(path, encoding="utf-8") as f:
            users = json.load(f)
        return [u for u in users if u.get("is_active", True)]

    def get_holder_groups(self) -> list[dict]:
        path = self.master_path / "holder_groups.json"
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        items = [g for g in data["items"] if g.get("is_active", True)]
        return sorted(items, key=lambda x: x.get("sort_order", 999))

    def get_valid_samples(self) -> list[dict]:
        path = self.master_path / "valid_samples.json"
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        items = [s for s in data["items"] if s.get("is_active", True)]
        return sorted(items, key=lambda x: x.get("sort_order", 999))

    # ── Analysis targets ─────────────────────────────────────────────────────

    def get_analysis_targets(
        self, holder_group_code: str, job_numbers: list
    ) -> dict[str, list[dict]]:
        """Return samples grouped by valid_test_display_name.

        Returns ``{test_display_name: [sample_dict, ...]}``.
        Stats are computed per (valid_sample_set_code, valid_holder_set_code,
        valid_test_set_code) with trend_enabled=True.
        """
        df = self.df
        job_str = [str(j) for j in job_numbers]

        mask = (df["holder_group_code"] == holder_group_code) & (
            df["sample_job_number"].isin(job_str)
        )
        filtered = df[mask]
        if filtered.empty:
            return {}

        unique = filtered.drop_duplicates(
            subset=["sample_request_number", "valid_sample_set_code",
                     "valid_test_set_code"]
        )
        stats_cache: dict[tuple, dict] = {}
        grouped: dict[str, list[dict]] = {}
        for _, row in unique.iterrows():
            vsset = row["valid_sample_set_code"]
            vhset = str(row.get("valid_holder_set_code", ""))
            vtset = str(row.get("valid_test_set_code", ""))
            test_name = str(row.get("valid_test_display_name", vtset))
            req_no = row.get("sample_request_number", "")

            cache_key = (vsset, vhset, vtset)
            if cache_key not in stats_cache:
                stats_cache[cache_key] = self._sample_stats(vsset, vhset, vtset)
            stats = stats_cache[cache_key]

            sample = {
                "valid_sample_set_code": vsset,
                "valid_sample_display_name": row.get("valid_sample_display_name", vsset),
                "sample_request_number": req_no,
                "sample_job_number": row.get("sample_job_number", ""),
                "sample_sampling_date": self._fmt_date(
                    row.get("sample_sampling_date"), include_time=True
                ),
                **stats,
            }
            grouped.setdefault(test_name, []).append(sample)
        return grouped

    def _sample_stats(
        self, vsset_code: str, vhset_code: str, vtset_code: str
    ) -> dict:
        df = self.df
        mask = (
            (df["valid_sample_set_code"].str.upper() == vsset_code.upper())
            & (df["valid_holder_set_code"].astype(str).str.upper() == vhset_code.upper())
            & (df["valid_test_set_code"].astype(str).str.upper() == vtset_code.upper())
            & (df["trend_enabled"] == True)
        )
        nums = self._numeric_values(df[mask]["test_raw_data"])
        if nums:
            return {
                "median": float(np.median(nums)),
                "max": float(np.max(nums)),
                "min": float(np.min(nums)),
            }
        return {"median": None, "max": None, "min": None}

    # ── Result data ───────────────────────────────────────────────────────────

    def get_result_data(
        self,
        holder_group_code: str,
        job_numbers: list,
        valid_sample_set_codes: list,
    ) -> pd.DataFrame:
        """Get result rows for result_verification, grouped by valid_holder_display_name."""
        df = self.df
        job_str = [str(j) for j in job_numbers]
        vsset_upper = [s.upper() for s in valid_sample_set_codes]

        mask = (df["holder_group_code"] == holder_group_code) & (
            df["sample_job_number"].isin(job_str)
        )
        filtered = df[mask]
        if valid_sample_set_codes:
            filtered = filtered[
                filtered["valid_sample_set_code"].str.upper().isin(vsset_upper)
            ]
        return filtered.copy()

    # ── Anomaly detection ─────────────────────────────────────────────────────

    def calculate_anomaly(self, row: pd.Series, holder_group_code: str) -> bool | None:
        """
        Returns True = anomaly, False = normal, None = cannot determine.
        Uses mean ± 2σ over historical data for the same sample+test combination.
        最低12件の履歴データが必要。
        """
        if not row.get("trend_enabled"):
            return None

        current = self.extract_numeric(str(row.get("test_raw_data", "")))
        if current is None:
            return None

        vsset = str(row.get("valid_sample_set_code", ""))
        vtest = str(row.get("valid_test_set_code", ""))

        df = self.df
        hist_mask = (
            (df["holder_group_code"] == holder_group_code)
            & (df["valid_sample_set_code"].str.upper() == vsset.upper())
            & (df["valid_test_set_code"].str.upper() == vtest.upper())
            & (df["trend_enabled"] == True)
        )
        nums = self._numeric_values(self._cutoff_5yr(df[hist_mask])["test_raw_data"])

        if len(nums) < 12:
            return None

        mean = float(np.mean(nums))
        std = float(np.std(nums, ddof=1))
        if std == 0:
            return False

        return current < (mean - 2 * std) or current > (mean + 2 * std)

    @staticmethod
    def _cutoff_5yr(df: pd.DataFrame) -> pd.DataFrame:
        """sample_sampling_date 列で最新日から過去5年のみに絞り込む。"""
        col = "sample_sampling_date"
        if col not in df.columns or df.empty:
            return df
        raw = df[col].dropna()
        if raw.empty:
            return df
        max_raw = str(int(float(raw.max())))[:8]  # YYYYMMDD
        try:
            max_dt = datetime.strptime(max_raw, "%Y%m%d")
        except ValueError:
            return df
        cutoff = (max_dt - timedelta(days=5 * 365)).strftime("%Y%m%d")
        return df[df[col].astype(str).str[:8] >= cutoff]

    def get_anomaly_bounds(self, holder_group_code: str, vsset_code: str, vtest_code: str) -> dict:
        """Return mean, std, lower/upper bounds for trend graph overlay (過去5年)."""
        df = self.df
        mask = (
            (df["holder_group_code"] == holder_group_code)
            & (df["valid_sample_set_code"].str.upper() == vsset_code.upper())
            & (df["valid_test_set_code"].str.upper() == vtest_code.upper())
            & (df["trend_enabled"] == True)
        )
        nums = self._numeric_values(self._cutoff_5yr(df[mask])["test_raw_data"])
        if len(nums) < 12:
            return {}
        mean = float(np.mean(nums))
        std = float(np.std(nums, ddof=1))
        return {
            "mean": mean,
            "std": std,
            "upper": mean + 2 * std,
            "lower": mean - 2 * std,
        }

    @staticmethod
    def check_spec_violation(row: pd.Series, raw_num: float) -> str | None:
        """基準値超過チェック。超過していれば U{N} / L{N} を返す。

        各 spec レベル 1-4 を個別にチェックし、超過している中で
        最も厳しい（上限なら最小値、下限なら最大値）spec の番号を返す。
        """
        upper_hit: tuple[int, float] | None = None
        lower_hit: tuple[int, float] | None = None

        for i in range(1, 5):
            v_u = row.get(f"test_upper_limit_spec_{i}")
            if v_u is not None and pd.notna(v_u):
                try:
                    spec_val = float(v_u)
                except (ValueError, TypeError):
                    continue
                if raw_num > spec_val:
                    if upper_hit is None or spec_val < upper_hit[1]:
                        upper_hit = (i, spec_val)

            v_l = row.get(f"test_lower_limit_spec_{i}")
            if v_l is not None and pd.notna(v_l):
                try:
                    spec_val = float(v_l)
                except (ValueError, TypeError):
                    continue
                if raw_num < spec_val:
                    if lower_hit is None or spec_val > lower_hit[1]:
                        lower_hit = (i, spec_val)

        # 上限・下限の両方で超過している場合、上限優先
        if upper_hit:
            return f"U{upper_hit[0]}"
        if lower_hit:
            return f"L{lower_hit[0]}"
        return None

    # ── Trend graph data ──────────────────────────────────────────────────────

    def get_trend_data(
        self, holder_group_code: str, vsset_code: str, vtest_code: str
    ) -> list[dict]:
        """Return time-series data for trend graph — 過去5年分のみ (includes judgment)."""
        df = self.df
        mask = (
            (df["holder_group_code"] == holder_group_code)
            & (df["valid_sample_set_code"].str.upper() == vsset_code.upper())
            & (df["valid_test_set_code"].str.upper() == vtest_code.upper())
            & (df["trend_enabled"] == True)
        )
        hist = self._cutoff_5yr(df[mask]).copy()
        rows = []
        for _, row in hist.iterrows():
            n = self.extract_numeric(str(row.get("test_raw_data", "")))
            if n is not None:
                grade_raw = str(row.get("test_grade_code", ""))
                rows.append(
                    {
                        "date": self._fmt_date(row.get("sample_sampling_date")),
                        "value": n,
                        "raw": str(row.get("test_raw_data", "")),
                        "unit": str(row.get("test_unit_name", "")),
                        "judgment": grade_raw if grade_raw not in ("nan", "None", "NN", "--", "") else "OK",
                    }
                )
        return rows

    def get_spec_limits(
        self, holder_group_code: str, vsset_code: str, vtest_code: str
    ) -> dict:
        """Return spec limits (最上下限基準値) for trend graph overlay.
        最新行（sample_sampling_date が最大）の spec 列のみを使用する。
        """
        df = self.df
        mask = (
            (df["holder_group_code"] == holder_group_code)
            & (df["valid_sample_set_code"].str.upper() == vsset_code.upper())
            & (df["valid_test_set_code"].str.upper() == vtest_code.upper())
        )
        filtered = df[mask]
        if filtered.empty:
            return {}
        # 最新行のみ
        latest = filtered.sort_values("sample_sampling_date", ascending=False).iloc[0]
        upper_vals: list[float] = []
        lower_vals: list[float] = []
        for i in range(1, 5):
            col_u = f"test_upper_limit_spec_{i}"
            col_l = f"test_lower_limit_spec_{i}"
            v_u = latest.get(col_u)
            v_l = latest.get(col_l)
            if v_u is not None and pd.notna(v_u) and isinstance(v_u, (int, float)):
                upper_vals.append(float(v_u))
            if v_l is not None and pd.notna(v_l) and isinstance(v_l, (int, float)):
                lower_vals.append(float(v_l))
        return {
            "spec_upper": min(upper_vals) if upper_vals else None,
            "spec_lower": max(lower_vals) if lower_vals else None,
        }

    # ── Data page ─────────────────────────────────────────────────────────────

    def get_data_page(
        self,
        date_from: str = "",
        date_to:   str = "",
        request_no: str = "",
        job_no: str = "",
        sample_names: list[str] | None = None,
        holder_names: list[str] | None = None,
        test_names: list[str] | None = None,
        judgment_filter: str = "全て",
        limit: int = 500,
    ) -> pd.DataFrame:
        """bunseki.csv をフィルタして返す（最大 limit 件）"""
        df = self.df.copy()

        # 日付フィルタ（sample_sampling_date: YYYYMMDDHHMMSS数値）
        if date_from:
            try:
                df = df[df["sample_sampling_date"].astype(str).str[:8] >= date_from.replace("-", "")]
            except Exception:
                pass
        if date_to:
            try:
                df = df[df["sample_sampling_date"].astype(str).str[:8] <= date_to.replace("-", "")]
            except Exception:
                pass
        if request_no:
            df = df[df["sample_request_number"].astype(str).str.contains(request_no, na=False)]
        if job_no:
            df = df[df["sample_job_number"].astype(str).str.contains(job_no, na=False)]
        if sample_names:
            df = df[df["valid_sample_display_name"].isin(sample_names)]
        if holder_names:
            df = df[df["valid_holder_display_name"].isin(holder_names)]
        if test_names:
            df = df[df["valid_test_display_name"].isin(test_names)]
        if judgment_filter == "NN":
            df = df[df["test_grade_code"].astype(str).isin(["NN", "--"])]
        elif judgment_filter == "異常":
            df = df[~df["test_grade_code"].astype(str).isin(["NN", "--", "", "nan", "None"])]

        return df.copy() if limit == 0 else df.head(limit).copy()

    def get_dropdown_values(self) -> dict[str, list[str]]:
        """データページのドロップダウン用ユニーク値を返す"""
        df = self.df
        return {
            "samples": sorted(df["valid_sample_display_name"].dropna().unique().tolist()),
            "holders": sorted(df["valid_holder_display_name"].dropna().unique().tolist()),
            "tests":   sorted(df["valid_test_display_name"].dropna().unique().tolist()),
        }

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _numeric_values(self, series: pd.Series) -> list[float]:
        result = []
        for v in series.dropna():
            n = self.extract_numeric(str(v))
            if n is not None:
                result.append(n)
        return result

    @staticmethod
    def extract_numeric(s: str) -> float | None:
        """Extract the first numeric value from a string, ignoring prefixes like <, >."""
        if not s or s in ("nan", "None", ""):
            return None
        cleaned = re.sub(r"[<>≤≥≦≧*~\s]", "", s)
        try:
            return float(cleaned)
        except (ValueError, TypeError):
            return None

    @staticmethod
    def _fmt_date(val, include_time: bool = False) -> str:
        if val is None or (isinstance(val, float) and np.isnan(val)):
            return ""
        s = str(int(float(val)))
        # YYYYMMDDHHMMSS or YYYYMM...
        if len(s) >= 8:
            base = f"{s[:4]}-{s[4:6]}-{s[6:8]}"
            if include_time and len(s) >= 12:
                base += f" {s[8:10]}:{s[10:12]}"
            return base
        if len(s) >= 6:
            return f"{s[:4]}-{s[4:6]}"
        return s
