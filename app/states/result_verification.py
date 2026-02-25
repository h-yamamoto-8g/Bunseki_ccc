import numpy as np
import pandas as pd
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QFrame,
    QAbstractItemView, QTabWidget, QCheckBox, QDialog,
    QVBoxLayout as QDVBox, QSizePolicy,
)
from PySide6.QtCore import Signal, Qt
from PySide6.QtGui import QColor, QFont

import matplotlib
matplotlib.use("QtAgg")
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas

from app.data import task_store


VERIFY_CHECKS = [
    "データ値の範囲を確認した",
    "異常フラグを確認した",
    "基準値との比較を確認した",
]


class ResultVerificationState(QWidget):
    go_next = Signal()
    go_back = Signal()

    def __init__(self, data_loader, parent=None):
        super().__init__(parent)
        self.data_loader = data_loader
        self._task: dict = {}
        self._readonly = False
        self._checks: list[QCheckBox] = []
        self._setup_ui()

    def _setup_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(32, 24, 32, 16)
        root.setSpacing(16)

        # Title
        self.title_lbl = QLabel("データ確認")
        self.title_lbl.setStyleSheet("font-size:20px; font-weight:bold; color:#1e293b;")
        root.addWidget(self.title_lbl)

        # Legend
        legend = QHBoxLayout()
        for color, label in [("#fee2e2", "異常（平均±2σ外）"), ("#fef9c3", "規格外")]:
            dot = QLabel()
            dot.setFixedSize(14, 14)
            dot.setStyleSheet(f"background:{color}; border:1px solid #d1d5db; border-radius:3px;")
            legend.addWidget(dot)
            legend.addWidget(QLabel(label))
            legend.addSpacing(16)
        legend.addStretch()
        root.addLayout(legend)

        # Tabs (by valid_holder_display_name)
        self.tab_widget = QTabWidget()
        self.tab_widget.setStyleSheet("""
            QTabBar::tab          { padding:8px 16px; font-size:13px; color:#6b7280; }
            QTabBar::tab:selected { color:#2563eb; border-bottom:2px solid #2563eb; }
            QTabBar::tab:hover    { color:#374151; background:#f1f5f9; }
            QTabWidget::pane      { border:1px solid #e2e8f0; }
        """)
        root.addWidget(self.tab_widget)

        # Confirm checklist
        check_frame = QFrame()
        check_frame.setStyleSheet("""
            QFrame { background:white; border:1px solid #e2e8f0; border-radius:8px; }
        """)
        cf = QHBoxLayout(check_frame)
        cf.setContentsMargins(16, 10, 16, 10)
        cf.setSpacing(24)
        self._checks = []
        for item in VERIFY_CHECKS:
            cb = QCheckBox(item)
            cb.setStyleSheet("font-size:12px; color:#374151;")
            cb.stateChanged.connect(self._update_next_btn)
            cf.addWidget(cb)
            self._checks.append(cb)
        cf.addStretch()
        root.addWidget(check_frame)

        # Navigation
        nav = QHBoxLayout()
        self.back_btn = QPushButton("← 戻る")
        self.back_btn.setStyleSheet("""
            QPushButton { background:#f1f5f9; color:#374151; border:1px solid #d1d5db;
                          padding:8px 20px; border-radius:6px; font-size:13px; }
            QPushButton:hover { background:#e2e8f0; }
        """)
        self.back_btn.clicked.connect(self.go_back)
        nav.addWidget(self.back_btn)
        nav.addStretch()
        self.next_btn = QPushButton("回覧へ →")
        self.next_btn.setEnabled(False)
        self.next_btn.setStyleSheet("""
            QPushButton { background:#2563eb; color:white; border:none;
                          padding:8px 24px; border-radius:6px; font-size:13px; font-weight:bold; }
            QPushButton:hover { background:#1d4ed8; }
            QPushButton:disabled { background:#93c5fd; }
        """)
        self.next_btn.clicked.connect(self._go_next)
        nav.addWidget(self.next_btn)
        root.addLayout(nav)

    # ── Public API ────────────────────────────────────────────────────────────

    def load_task(self, task: dict, readonly: bool = False):
        self._task = task
        self._readonly = readonly
        task_name = task.get("task_name", "")
        self.title_lbl.setText(f"データ確認  —  {task_name}")

        hg_code = task.get("holder_group_code", "")
        jobs = task.get("job_numbers", [])
        vsset_codes = (
            task.get("state_data", {})
            .get("analysis_targets", {})
            .get("valid_sample_set_codes", [])
        )

        # Load data
        df = self.data_loader.get_result_data(hg_code, jobs, vsset_codes)
        self._build_tabs(df, hg_code)

        # Restore checks
        sd = task.get("state_data", {}).get("result_verification", {})
        saved = sd.get("checks", [False] * len(VERIFY_CHECKS))
        for cb, v in zip(self._checks, saved):
            cb.setChecked(v)
            cb.setEnabled(not readonly)

        self.next_btn.setVisible(not readonly)
        self._update_next_btn()

    # ── Tab building ──────────────────────────────────────────────────────────

    def _build_tabs(self, df: pd.DataFrame, hg_code: str):
        self.tab_widget.clear()

        if df.empty:
            self.tab_widget.addTab(QLabel("データがありません"), "（なし）")
            return

        groups = df.groupby("valid_holder_display_name", sort=False)
        for holder_name, group_df in groups:
            tab = self._build_tab(group_df, hg_code, str(holder_name))
            self.tab_widget.addTab(tab, str(holder_name))

    def _build_tab(self, df: pd.DataFrame, hg_code: str, holder_name: str) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 8, 0, 0)

        headers = ["サンプル名", "試験項目名", "データ", "単位",
                   "最上限基準値", "最下限基準値", "異常フラグ", "トレンド"]
        table = QTableWidget(0, len(headers))
        table.setHorizontalHeaderLabels(headers)
        table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        table.setAlternatingRowColors(True)
        table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        table.setColumnWidth(7, 70)
        table.setStyleSheet("""
            QTableWidget { border:none; }
            QHeaderView::section { background:#f8fafc; font-weight:bold; color:#374151;
                                    padding:6px; border:none; border-bottom:1px solid #e2e8f0; }
        """)
        table.verticalHeader().setVisible(False)

        for _, row in df.iterrows():
            self._add_data_row(table, row, hg_code)

        layout.addWidget(table)
        return widget

    def _add_data_row(self, table: QTableWidget, row: pd.Series, hg_code: str):
        r = table.rowCount()
        table.insertRow(r)

        # Upper/lower spec limits
        upper_specs = [row.get(f"test_upper_limit_spec_{i}") for i in range(1, 5)]
        lower_specs = [row.get(f"test_lower_limit_spec_{i}") for i in range(1, 5)]
        upper_vals = [v for v in upper_specs if pd.notna(v)]
        lower_vals = [v for v in lower_specs if pd.notna(v)]
        upper_lim = f"{min(upper_vals):.4g}" if upper_vals else "—"
        lower_lim = f"{max(lower_vals):.4g}" if lower_vals else "—"

        # Anomaly flag
        judgment_raw = str(row.get("test_judgment", ""))
        trend_ok = row.get("trend_enabled") == True

        if judgment_raw and judgment_raw not in ("nan", "None", "NN", ""):
            flag_text = judgment_raw
            is_anomaly = True
        elif trend_ok:
            is_anomaly = self.data_loader.calculate_anomaly(row, hg_code)
            if is_anomaly is True:
                flag_text = "異常"
            elif is_anomaly is False:
                flag_text = "正常"
            else:
                flag_text = "—"
        else:
            flag_text = "—"
            is_anomaly = False

        values = [
            str(row.get("valid_sample_display_name", "")),
            str(row.get("valid_test_display_name", "")),
            str(row.get("test_raw_data", "")),
            str(row.get("test_unit_name", "")),
            upper_lim,
            lower_lim,
            flag_text,
        ]

        for col, v in enumerate(values):
            item = QTableWidgetItem(str(v) if v not in ("nan", "None") else "")
            if col == 6 and is_anomaly:
                item.setBackground(QColor("#fee2e2"))
                item.setForeground(QColor("#dc2626"))
                item.setFont(QFont("", -1, QFont.Weight.Bold))
            # Highlight spec violations
            if col in (4, 5):
                try:
                    raw_num = self.data_loader.extract_numeric(str(row.get("test_raw_data", "")))
                    if raw_num is not None:
                        if col == 4 and upper_vals and raw_num > min(upper_vals):
                            item.setBackground(QColor("#fef9c3"))
                        if col == 5 and lower_vals and raw_num < max(lower_vals):
                            item.setBackground(QColor("#fef9c3"))
                except Exception:
                    pass
            table.setItem(r, col, item)

        # Trend button
        trend_btn = QPushButton("グラフ")
        trend_btn.setStyleSheet("""
            QPushButton { background:#eff6ff; color:#2563eb; border:1px solid #bfdbfe;
                          padding:2px 8px; border-radius:4px; font-size:11px; }
            QPushButton:hover { background:#dbeafe; }
        """)
        vsset = str(row.get("valid_sample_set_code", ""))
        vtest = str(row.get("valid_test_set_code", ""))
        unit = str(row.get("test_unit_name", ""))
        test_name = str(row.get("valid_test_display_name", ""))
        trend_btn.clicked.connect(
            lambda _=False, hg=hg_code, vs=vsset, vt=vtest, u=unit, tn=test_name:
                self._show_trend(hg, vs, vt, u, tn)
        )
        table.setCellWidget(r, 7, trend_btn)

    def _show_trend(self, hg_code: str, vsset: str, vtest: str, unit: str, test_name: str):
        data = self.data_loader.get_trend_data(hg_code, vsset, vtest)
        bounds = self.data_loader.get_anomaly_bounds(hg_code, vsset, vtest)

        dlg = TrendDialog(data, bounds, unit, test_name, self)
        dlg.exec()

    def _update_next_btn(self):
        all_ok = all(cb.isChecked() for cb in self._checks)
        self.next_btn.setEnabled(all_ok)

    def _go_next(self):
        task_id = self._task["task_id"]
        state_data = {
            "checks": [cb.isChecked() for cb in self._checks],
            "completed": True,
        }
        task_store.update_task_state(task_id, "result_verification", state_data)
        task_store.update_task_state(task_id, "submission")
        self._task = task_store.get_task(task_id)
        self.go_next.emit()


# ── Trend graph dialog ────────────────────────────────────────────────────────

class TrendDialog(QDialog):
    def __init__(self, data: list[dict], bounds: dict, unit: str, test_name: str, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"トレンドグラフ  —  {test_name}")
        self.resize(700, 420)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)

        fig, ax = plt.subplots(figsize=(9, 4.5), dpi=90)
        fig.patch.set_facecolor("#f8fafc")
        ax.set_facecolor("white")

        if data:
            dates = [d["date"] for d in data]
            vals = [d["value"] for d in data]
            ax.plot(range(len(vals)), vals, "o-", color="#2563eb", linewidth=1.5,
                    markersize=4, label="測定値")
            ax.set_xticks(range(len(dates)))
            ax.set_xticklabels(dates, rotation=45, ha="right", fontsize=8)

            if bounds:
                ax.axhline(bounds["mean"], color="#10b981", linestyle="--",
                           linewidth=1, label=f"平均 ({bounds['mean']:.3g})")
                ax.axhline(bounds["upper"], color="#ef4444", linestyle="--",
                           linewidth=1, label=f"+2σ ({bounds['upper']:.3g})")
                ax.axhline(bounds["lower"], color="#ef4444", linestyle="--",
                           linewidth=1, label=f"-2σ ({bounds['lower']:.3g})")
                ax.fill_between(range(len(vals)), bounds["lower"], bounds["upper"],
                                alpha=0.08, color="#2563eb")
        else:
            ax.text(0.5, 0.5, "データなし", transform=ax.transAxes,
                    ha="center", va="center", fontsize=14, color="#6b7280")

        ax.set_ylabel(unit, fontsize=10)
        ax.set_title(test_name, fontsize=11, fontweight="bold")
        ax.legend(fontsize=9)
        ax.grid(True, alpha=0.3)
        fig.tight_layout()

        canvas = FigureCanvas(fig)
        layout.addWidget(canvas)

        close_btn = QPushButton("閉じる")
        close_btn.setStyleSheet("""
            QPushButton { background:#f1f5f9; color:#374151; border:1px solid #d1d5db;
                          padding:6px 20px; border-radius:5px; }
            QPushButton:hover { background:#e2e8f0; }
        """)
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn, alignment=Qt.AlignmentFlag.AlignRight)
