"""ResultVerificationUI — データ確認テーブル・チェックリストの純粋レイアウト（generated UI 使用）。

ビジネスロジック・task_store・DataLoader の import 禁止。
"""
from __future__ import annotations

import pandas as pd
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView,
    QAbstractItemView, QCheckBox, QDialog, QApplication,
    QSplitter,
)
from PySide6.QtCore import Signal, Qt, QSize
from PySide6.QtGui import QColor, QFont
from app.ui.widgets.icon_utils import get_icon

from app.ui.generated.ui_stateresultverification import Ui_StateResultVerification
from app.services.hg_config_service import DEFAULT_VERIFY_CHECKLIST


class ResultVerificationUI(QWidget):
    """データ確認テーブル (純粋レイアウト)。

    Signals:
        next_requested(checks): チェックリスト値と共に次へ
        back_requested(): 戻る
        graph_requested(hg_code, vsset, vtest, unit, test_name): グラフ表示要求
    """

    next_requested = Signal(list)
    back_requested = Signal()
    graph_requested = Signal(str, str, str, str, str)  # hg, vsset, vtest, unit, test_name

    def __init__(self, parent=None):
        super().__init__(parent)
        self._checks: list[QCheckBox] = []

        self._form = Ui_StateResultVerification()
        self._form.setupUi(self)

        # ── グローバル QSS でリセットされるデフォルト spacing を明示設定 ──
        self._form.verticalLayout.setSpacing(8)
        self._form.verticalLayout.setContentsMargins(8, 8, 8, 8)

        # エイリアス
        self.tab_widget = self._form.tabWidget_data
        self.next_btn   = self._form.btn_next
        self._check_layout = self._form.horizontalLayout

        # デフォルトチェックリストで初期化
        self._build_checks(list(DEFAULT_VERIFY_CHECKLIST))

        self._form.btn_next.setEnabled(False)
        self._form.btn_back.setVisible(False)
        self._form.btn_next.setText("完了")
        self._form.btn_next.clicked.connect(self._on_next)

    # ── Public API ────────────────────────────────────────────────────────────

    def set_check_items(self, items: list[str]) -> None:
        """チェックリスト項目を動的に差し替える。"""
        self._build_checks(items)

    def _build_checks(self, items: list[str]) -> None:
        """チェックボックスを再構築する。"""
        for cb in self._checks:
            cb.deleteLater()
        self._checks.clear()
        # stretch も除去
        while self._check_layout.count():
            item = self._check_layout.takeAt(0)
            w = item.widget()
            if w:
                w.deleteLater()

        for text in items:
            cb = QCheckBox(text)
            cb.setStyleSheet("font-size:12px; color:#334155;")
            cb.stateChanged.connect(self._update_next_btn)
            self._check_layout.addWidget(cb)
            self._checks.append(cb)
        self._check_layout.addStretch()
        self._update_next_btn()

    def build_tabs(
        self,
        df: pd.DataFrame,
        hg_code: str,
        anomaly_fn,
        extract_numeric_fn,
    ) -> None:
        """結果データからタブを構築する。"""
        self._hg_code = hg_code
        self._anomaly_fn = anomaly_fn
        self._extract_numeric_fn = extract_numeric_fn
        self.tab_widget.clear()

        if df.empty:
            self.tab_widget.addTab(QLabel("データがありません"), "（なし）")
            return

        groups = df.groupby("valid_holder_display_name", sort=False)
        for holder_name, group_df in groups:
            tab = self._build_tab(group_df, hg_code, str(holder_name))
            self.tab_widget.addTab(tab, str(holder_name))

    def restore_checks(self, saved: list[bool], readonly: bool) -> None:
        for cb, v in zip(self._checks, saved):
            cb.setChecked(v)
            cb.setEnabled(not readonly)
        self.next_btn.setVisible(not readonly)
        self._update_next_btn()

    # ── Internal ──────────────────────────────────────────────────────────────

    def _build_tab(
        self, df: pd.DataFrame, hg_code: str, holder_name: str
    ) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 8, 0, 0)

        headers = ["サンプル名", "試験項目名", "データ", "単位",
                   "最上限基準値", "最下限基準値", "異常フラグ", ""]
        table = QTableWidget(0, len(headers))
        table.setHorizontalHeaderLabels(headers)
        table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        table.setAlternatingRowColors(True)
        table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        table.setColumnWidth(7, 44)
        table.verticalHeader().setDefaultSectionSize(36)
        table.setStyleSheet("""
            QTableWidget { border:none; }
            QHeaderView::section { background:#f1f5f9; font-weight:bold; color:#475569;
                                    padding:6px; border:none; border-bottom:1px solid #e2e8f0; }
        """)
        table.verticalHeader().setVisible(False)

        for _, row in df.iterrows():
            self._add_data_row(table, row, hg_code)
            QApplication.processEvents()

        layout.addWidget(table)
        return widget

    def _add_data_row(
        self, table: QTableWidget, row: pd.Series, hg_code: str
    ) -> None:
        r = table.rowCount()
        table.insertRow(r)

        upper_specs = [row.get(f"test_upper_limit_spec_{i}") for i in range(1, 5)]
        lower_specs = [row.get(f"test_lower_limit_spec_{i}") for i in range(1, 5)]
        upper_vals = [v for v in upper_specs if pd.notna(v)]
        lower_vals = [v for v in lower_specs if pd.notna(v)]
        upper_lim = f"{min(upper_vals):.4g}" if upper_vals else "—"
        lower_lim = f"{max(lower_vals):.4g}" if lower_vals else "—"

        grade_raw = str(row.get("test_grade_code", ""))
        trend_ok = row.get("trend_enabled") == True

        # 優先度1: test_grade_code の判定
        if grade_raw in ("NN", "--") or grade_raw in ("nan", "None"):
            # NN / -- → 異常なし
            flag_text = "NN"
            is_anomaly = False
        elif grade_raw and grade_raw not in ("",):
            # NN/-- 以外の値がある → 異常
            flag_text = grade_raw
            is_anomaly = True
        else:
            # grade_code が空 → 優先度2: 基準値チェック → 優先度3: mean±2σ
            raw_num = self._extract_numeric_fn(str(row.get("test_raw_data", "")))

            # 優先度2: 基準値超過チェック (U{N}/L{N})
            from app.core.loader import DataLoader
            spec_label = None
            if raw_num is not None:
                spec_label = DataLoader.check_spec_violation(row, raw_num)

            if spec_label:
                flag_text = spec_label
                is_anomaly = True
            elif trend_ok:
                # 優先度3: mean±2σ チェック (異常なしのもののみ)
                is_anomaly = self._anomaly_fn(row, hg_code)
                if is_anomaly is True:
                    flag_text = "異常"
                elif is_anomaly is False:
                    flag_text = "正常"
                else:
                    flag_text = "—"
            else:
                # 基準値も問題なし → NN
                flag_text = "NN"
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
            if col in (4, 5):
                try:
                    raw_num = self._extract_numeric_fn(str(row.get("test_raw_data", "")))
                    if raw_num is not None:
                        if col == 4 and upper_vals and raw_num > min(upper_vals):
                            item.setBackground(QColor("#fef9c3"))
                        if col == 5 and lower_vals and raw_num < max(lower_vals):
                            item.setBackground(QColor("#fef9c3"))
                except Exception:
                    pass
            table.setItem(r, col, item)

        vsset = str(row.get("valid_sample_set_code", ""))
        vtest = str(row.get("valid_test_set_code", ""))
        unit  = str(row.get("test_unit_name", ""))
        test_name = str(row.get("valid_test_display_name", ""))

        trend_btn = QPushButton()
        trend_btn.setIcon(get_icon(":/icons/graph.svg", "#4a8cff", 14))
        trend_btn.setIconSize(QSize(14, 14))
        trend_btn.setFixedSize(28, 28)
        trend_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        trend_btn.setToolTip("トレンドグラフ")
        trend_btn.setStyleSheet(
            "QPushButton { background:#eff6ff; border:1px solid #bfdbfe;"
            " border-radius:4px; padding:0; min-height:0; min-width:0; }"
            "QPushButton:hover { background:#dbeafe; border-color:#4a8cff; }"
        )
        trend_btn.clicked.connect(
            lambda _=False, hg=hg_code, vs=vsset, vt=vtest, u=unit, tn=test_name:
                self.graph_requested.emit(hg, vs, vt, u, tn)
        )
        cell_w = QWidget()
        cell_w.setStyleSheet("background:transparent;")
        cell_l = QHBoxLayout(cell_w)
        cell_l.setContentsMargins(4, 4, 4, 4)
        cell_l.setAlignment(Qt.AlignmentFlag.AlignCenter)
        cell_l.addWidget(trend_btn)
        table.setCellWidget(r, 7, cell_w)

    def _update_next_btn(self) -> None:
        self.next_btn.setEnabled(all(cb.isChecked() for cb in self._checks))

    def _on_next(self) -> None:
        self.next_requested.emit([cb.isChecked() for cb in self._checks])


# ── Trend graph dialog ────────────────────────────────────────────────────────

def _short_date(date_str: str) -> str:
    """'YYYY/MM/DD HH:MM' 等を 'MM/DD' に短縮する。"""
    s = str(date_str).strip()
    for sep in ("/", "-"):
        parts = s.split(sep)
        if len(parts) >= 3:
            try:
                return f"{int(parts[1]):02d}/{int(parts[2][:2]):02d}"
            except (ValueError, IndexError):
                pass
    return s[:5]


class TrendDialog(QDialog):
    """モダンなトレンドグラフダイアログ。

    Args:
        data: [{"date", "value", "raw", "unit", "judgment"}, ...]
        bounds: {"mean", "std", "upper", "lower"} — mean±2σ
        spec: {"spec_upper", "spec_lower"} — 最上下限基準値
        unit: 単位文字列
        test_name: 試験項目名
    """

    def __init__(
        self,
        data: list[dict],
        bounds: dict,
        spec: dict,
        unit: str,
        test_name: str,
        parent=None,
    ):
        super().__init__(parent)
        self.setWindowTitle(f"トレンドグラフ  —  {test_name}")
        self.resize(1100, 720)
        self.setMinimumSize(700, 480)
        self.setStyleSheet("background:#f8fafc;")

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 16, 20, 16)
        main_layout.setSpacing(12)

        # タイトル & 統計チップ
        main_layout.addWidget(self._build_header(test_name, unit, data, bounds))

        # QSplitter（グラフ上 / テーブル下）
        splitter = QSplitter(Qt.Orientation.Vertical)
        splitter.setChildrenCollapsible(False)
        splitter.setStyleSheet("QSplitter::handle { background:#e2e8f0; height:4px; }")
        splitter.addWidget(self._build_chart(data, bounds, spec, unit))
        splitter.addWidget(self._build_table(data, unit))
        splitter.setStretchFactor(0, 2)
        splitter.setStretchFactor(1, 1)
        splitter.setSizes([380, 200])
        main_layout.addWidget(splitter, 1)

        # 閉じるボタン
        close_btn = QPushButton("閉じる")
        close_btn.setFixedWidth(120)
        close_btn.setStyleSheet("""
            QPushButton {
                background:#1e3a5f; color:white; border:none;
                padding:8px 20px; border-radius:6px; font-size:13px;
            }
            QPushButton:hover { background:#2a4f7a; }
        """)
        close_btn.clicked.connect(self.accept)
        main_layout.addWidget(close_btn, alignment=Qt.AlignmentFlag.AlignRight)

    # ── ヘッダー（タイトル + 統計チップ） ────────────────────────────────────

    def _build_header(
        self, test_name: str, unit: str, data: list[dict], bounds: dict
    ) -> QWidget:
        w = QWidget()
        w.setStyleSheet("background:#1e3a5f; border-radius:8px;")
        vlay = QVBoxLayout(w)
        vlay.setContentsMargins(20, 14, 20, 14)
        vlay.setSpacing(10)

        title = QLabel(test_name)
        title.setStyleSheet(
            "font-size:16px; font-weight:700; color:white; background:transparent;"
        )
        vlay.addWidget(title)

        chips_row = QHBoxLayout()
        chips_row.setSpacing(10)

        n = len(data) if data else 0
        anomaly_n = sum(1 for d in (data or []) if d.get("judgment", "OK") != "OK")
        chip_defs: list[tuple[str, str, str]] = [
            ("N", str(n), "#3b82f6"),
            ("異常", str(anomaly_n), "#ef4444" if anomaly_n > 0 else "#6b7280"),
        ]
        if bounds:
            mean_v = bounds.get("mean")
            upper_v = bounds.get("upper")
            lower_v = bounds.get("lower")
            if mean_v is not None:
                chip_defs.append(("平均", f"{mean_v:.4g} {unit}", "#10b981"))
            if upper_v is not None and lower_v is not None:
                chip_defs.append(("±2σ範囲", f"{lower_v:.4g} 〜 {upper_v:.4g}", "#f59e0b"))

        for label, value, color in chip_defs:
            chip = QWidget()
            chip.setStyleSheet(
                "background:rgba(255,255,255,0.12); border-radius:6px;"
                "border:1px solid rgba(255,255,255,0.2);"
            )
            chip_lay = QHBoxLayout(chip)
            chip_lay.setContentsMargins(10, 6, 10, 6)
            chip_lay.setSpacing(6)
            lbl = QLabel(label)
            lbl.setStyleSheet(
                "color:rgba(255,255,255,0.65); font-size:11px; background:transparent;"
            )
            val_lbl = QLabel(value)
            val_lbl.setStyleSheet(
                f"color:{color}; font-size:13px; font-weight:700; background:transparent;"
            )
            chip_lay.addWidget(lbl)
            chip_lay.addWidget(val_lbl)
            chips_row.addWidget(chip)

        chips_row.addStretch()
        row_w = QWidget()
        row_w.setStyleSheet("background:transparent;")
        row_w.setLayout(chips_row)
        vlay.addWidget(row_w)
        return w

    # ── グラフ ────────────────────────────────────────────────────────────────

    def _build_chart(
        self,
        data: list[dict],
        bounds: dict,
        spec: dict,
        unit: str,
    ) -> QWidget:
        import matplotlib
        matplotlib.use("QtAgg")
        import matplotlib.pyplot as plt
        from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas

        fig, ax = plt.subplots(figsize=(12, 4.5), dpi=96)
        fig.patch.set_facecolor("#ffffff")
        ax.set_facecolor("#ffffff")

        dates: list[str] = []
        vals: list[float] = []
        judgments: list[str] = []

        if data:
            dates = [d["date"] for d in data]
            vals = [d["value"] for d in data]
            judgments = [d.get("judgment", "OK") for d in data]
            n = len(vals)

            # 実線でプロット接続
            if n >= 2:
                ax.plot(
                    range(n), vals,
                    color="#93c5fd", linewidth=1.8, zorder=2, solid_capstyle="round",
                )

            # マーカー（通常: 中抜き円 / 異常: 塗り菱形）
            normal_x = [i for i, j in enumerate(judgments) if j == "OK"]
            normal_y = [vals[i] for i in normal_x]
            anomaly_x = [i for i, j in enumerate(judgments) if j != "OK"]
            anomaly_y = [vals[i] for i in anomaly_x]

            if normal_x:
                ax.scatter(
                    normal_x, normal_y,
                    facecolors="white", edgecolors="#2563eb",
                    linewidths=1.5, s=38, zorder=4,
                )
            if anomaly_x:
                ax.scatter(
                    anomaly_x, anomaly_y,
                    color="#ef4444", marker="D", s=52, zorder=5,
                    label="異常値",
                )

            ax.set_xlim(-0.5, n - 0.5)

            # 2σ帯 & 基準線
            if bounds:
                ax.axhline(
                    bounds["mean"], color="#10b981", lw=1.5, zorder=3,
                    label=f"平均  {bounds['mean']:.4g}",
                )
                ax.axhline(
                    bounds["upper"], color="#f97316", lw=1, ls="--", zorder=3,
                    label=f"+2σ  {bounds['upper']:.4g}",
                )
                ax.axhline(
                    bounds["lower"], color="#f97316", lw=1, ls="--", zorder=3,
                    label=f"−2σ  {bounds['lower']:.4g}",
                )
                ax.fill_between(
                    [-0.5, n - 0.5], bounds["lower"], bounds["upper"],
                    alpha=0.06, color="#3b82f6", zorder=1,
                )

            spec_upper = spec.get("spec_upper") if spec else None
            spec_lower = spec.get("spec_lower") if spec else None
            if spec_upper is not None:
                ax.axhline(
                    spec_upper, color="#dc2626", lw=1.5, ls=":",
                    label=f"上限  {spec_upper:.4g}",
                )
            if spec_lower is not None:
                ax.axhline(
                    spec_lower, color="#dc2626", lw=1.5, ls=":",
                    label=f"下限  {spec_lower:.4g}",
                )

            # X軸ラベル（最大14点）
            short_dates = [_short_date(d) for d in dates]
            max_ticks = 14
            if n <= max_ticks:
                tick_pos = list(range(n))
                tick_lbl = short_dates
            else:
                step = max(n // max_ticks, 1)
                tick_pos = list(range(0, n, step))
                tick_lbl = [short_dates[i] for i in tick_pos]
            ax.set_xticks(tick_pos)
            ax.set_xticklabels(
                tick_lbl, rotation=30, ha="right", fontsize=9, color="#64748b"
            )

        else:
            ax.text(
                0.5, 0.5, "データなし", transform=ax.transAxes,
                ha="center", va="center", fontsize=14, color="#9ca3af",
            )

        # スパイン・グリッド
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
        ax.spines["left"].set_color("#e2e8f0")
        ax.spines["bottom"].set_color("#e2e8f0")
        ax.yaxis.grid(True, color="#f1f5f9", linewidth=1, zorder=0)
        ax.xaxis.grid(False)
        ax.set_ylabel(unit, fontsize=10, color="#64748b", labelpad=8)
        ax.tick_params(axis="y", colors="#94a3b8", labelsize=9)
        ax.tick_params(axis="x", length=0)

        if data:
            legend = ax.legend(
                fontsize=9, loc="upper left",
                framealpha=0.9, edgecolor="#e2e8f0", facecolor="white",
            )
            for text in legend.get_texts():
                text.set_color("#374151")

        fig.tight_layout(pad=1.2)

        # ダークツールチップ
        annot = ax.annotate(
            "", xy=(0, 0), xytext=(14, 14),
            textcoords="offset points",
            bbox=dict(boxstyle="round,pad=0.5", fc="#1e293b", ec="none"),
            arrowprops=dict(arrowstyle="-", color="#475569", lw=0.5),
            color="white", fontsize=9,
        )
        annot.set_visible(False)

        def _on_hover(event):
            if event.inaxes != ax or not vals:
                if annot.get_visible():
                    annot.set_visible(False)
                    fig.canvas.draw_idle()
                return
            if event.xdata is None:
                return
            idx = int(round(event.xdata))
            if 0 <= idx < len(vals):
                annot.xy = (idx, vals[idx])
                d_str = dates[idx] if dates else str(idx)
                j_str = judgments[idx] if judgments else "OK"
                icon = "⚠ " if j_str != "OK" else ""
                annot.set_text(f"{icon}{d_str}\n{vals[idx]:.4g} {unit}")
                annot.set_visible(True)
            else:
                annot.set_visible(False)
            fig.canvas.draw_idle()

        fig.canvas.mpl_connect("motion_notify_event", _on_hover)

        canvas = FigureCanvas(fig)
        canvas.setMinimumHeight(280)
        wrapper = QWidget()
        wrapper.setStyleSheet("background:white; border-radius:6px;")
        wlay = QVBoxLayout(wrapper)
        wlay.setContentsMargins(4, 4, 4, 4)
        wlay.addWidget(canvas)
        return wrapper

    # ── データテーブル ────────────────────────────────────────────────────────

    def _build_table(self, data: list[dict], unit: str) -> QWidget:
        wrapper = QWidget()
        wrapper.setStyleSheet("background:white; border-radius:6px;")
        wlay = QVBoxLayout(wrapper)
        wlay.setContentsMargins(8, 8, 8, 8)
        wlay.setSpacing(4)

        header_lbl = QLabel("データ一覧")
        header_lbl.setStyleSheet(
            "font-size:11px; font-weight:600; color:#64748b; background:transparent;"
        )
        wlay.addWidget(header_lbl)

        tbl = QTableWidget(0, 4)
        tbl.setHorizontalHeaderLabels(["日時", "データ", "単位", "判定"])
        tbl.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        tbl.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        tbl.verticalHeader().setVisible(False)
        tbl.setShowGrid(False)
        tbl.setAlternatingRowColors(True)
        tbl.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        tbl.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Fixed)
        tbl.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)
        tbl.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.Fixed)
        tbl.setColumnWidth(1, 110)
        tbl.setColumnWidth(2, 70)
        tbl.setColumnWidth(3, 80)
        tbl.setStyleSheet("""
            QTableWidget {
                border:none; font-size:12px;
                alternate-background-color:#f8fafc;
            }
            QHeaderView::section {
                background:#f1f5f9; color:#64748b; font-weight:600;
                padding:6px 8px; border:none; border-bottom:2px solid #e2e8f0;
            }
            QTableWidget::item { padding:5px 8px; }
        """)

        for i, row_data in enumerate(data or []):
            tbl.insertRow(i)
            judgment = row_data.get("judgment", "OK")
            is_anomaly = judgment != "OK"
            judg_text = f"⚠ {judgment}" if is_anomaly else "✓"

            cells = [
                row_data.get("date", ""),
                row_data.get("raw", str(row_data.get("value", ""))),
                row_data.get("unit", unit),
                judg_text,
            ]
            for col, val in enumerate(cells):
                item = QTableWidgetItem(str(val))
                align = (
                    Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
                    if col == 1
                    else Qt.AlignmentFlag.AlignCenter
                )
                item.setTextAlignment(align)
                if is_anomaly:
                    item.setBackground(QColor("#fff1f2"))
                    if col == 3:
                        item.setForeground(QColor("#dc2626"))
                        item.setFont(QFont("", -1, QFont.Weight.Bold))
                elif col == 3:
                    item.setForeground(QColor("#10b981"))
                tbl.setItem(i, col, item)

        wlay.addWidget(tbl)
        return wrapper
