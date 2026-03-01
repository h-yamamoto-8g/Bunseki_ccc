import re
import json
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
            self._df = pd.read_csv(
                self.csv_path,
                low_memory=False,
                dtype={
                    "sample_job_number": str,
                    "test_raw_data": str,
                    "test_judgment": str,
                    "trend_enabled": str,
                },
            )
            # Normalize boolean
            self._df["trend_enabled"] = self._df["trend_enabled"].str.lower().map(
                {"true": True, "false": False, "1": True, "0": False}
            )
        return self._df

    # ── Master data ──────────────────────────────────────────────────────────

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

    def get_analysis_targets(self, holder_group_code: str, job_numbers: list) -> list[dict]:
        """Return unique samples for given holder_group and job numbers with stats."""
        df = self.df
        job_str = [str(j) for j in job_numbers]

        mask = (df["holder_group_code"] == holder_group_code) & (
            df["sample_job_number"].isin(job_str)
        )
        filtered = df[mask]
        if filtered.empty:
            return []

        unique = filtered.drop_duplicates(subset=["valid_sample_set_code"])
        results = []
        for _, row in unique.iterrows():
            vsset = row["valid_sample_set_code"]
            stats = self._sample_stats(holder_group_code, vsset)
            results.append(
                {
                    "valid_sample_set_code": vsset,
                    "valid_sample_display_name": row.get("valid_sample_display_name", vsset),
                    "sample_job_number": row.get("sample_job_number", ""),
                    "sample_sampling_date": self._fmt_date(row.get("sample_sampling_date")),
                    **stats,
                }
            )
        return results

    def _sample_stats(self, holder_group_code: str, vsset_code: str) -> dict:
        df = self.df
        mask = (
            (df["holder_group_code"] == holder_group_code)
            & (df["valid_sample_set_code"].str.upper() == vsset_code.upper())
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
        nums = self._numeric_values(df[hist_mask]["test_raw_data"])

        if len(nums) < 3:
            return None

        mean = float(np.mean(nums))
        std = float(np.std(nums, ddof=1))
        if std == 0:
            return False

        return current < (mean - 2 * std) or current > (mean + 2 * std)

    def get_anomaly_bounds(self, holder_group_code: str, vsset_code: str, vtest_code: str) -> dict:
        """Return mean, std, lower/upper bounds for trend graph overlay."""
        df = self.df
        mask = (
            (df["holder_group_code"] == holder_group_code)
            & (df["valid_sample_set_code"].str.upper() == vsset_code.upper())
            & (df["valid_test_set_code"].str.upper() == vtest_code.upper())
            & (df["trend_enabled"] == True)
        )
        nums = self._numeric_values(df[mask]["test_raw_data"])
        if len(nums) < 3:
            return {}
        mean = float(np.mean(nums))
        std = float(np.std(nums, ddof=1))
        return {
            "mean": mean,
            "std": std,
            "upper": mean + 2 * std,
            "lower": mean - 2 * std,
        }

    # ── Trend graph data ──────────────────────────────────────────────────────

    def get_trend_data(
        self, holder_group_code: str, vsset_code: str, vtest_code: str
    ) -> list[dict]:
        """Return time-series data for trend graph."""
        df = self.df
        mask = (
            (df["holder_group_code"] == holder_group_code)
            & (df["valid_sample_set_code"].str.upper() == vsset_code.upper())
            & (df["valid_test_set_code"].str.upper() == vtest_code.upper())
            & (df["trend_enabled"] == True)
        )
        hist = df[mask].copy()
        rows = []
        for _, row in hist.iterrows():
            n = self.extract_numeric(str(row.get("test_raw_data", "")))
            if n is not None:
                rows.append(
                    {
                        "date": self._fmt_date(row.get("sample_sampling_date")),
                        "value": n,
                    }
                )
        return rows

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
            df = df[df["test_judgment"].astype(str) == "NN"]
        elif judgment_filter == "異常":
            df = df[df["test_judgment"].astype(str) != "NN"]

        return df.head(limit).copy()

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
    def _fmt_date(val) -> str:
        if val is None or (isinstance(val, float) and np.isnan(val)):
            return ""
        s = str(int(float(val)))
        # YYYYMMDDHHMMSS or YYYYMM...
        if len(s) >= 8:
            return f"{s[:4]}-{s[4:6]}-{s[6:8]}"
        if len(s) >= 6:
            return f"{s[:4]}-{s[4:6]}"
        return s
