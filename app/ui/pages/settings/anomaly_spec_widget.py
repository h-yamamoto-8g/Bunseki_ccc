"""異常検出・基準値列の設定ウィジェット。

HgConfigTab の「チェック」ステータスブロックに埋め込まれる。
"""
from __future__ import annotations

from PySide6.QtCore import Qt, QSize
from PySide6.QtWidgets import (
    QComboBox,
    QDoubleSpinBox,
    QFormLayout,
    QFrame,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QPushButton,
    QSpinBox,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from app.services.hg_config_service import (
    DEFAULT_ANOMALY_MIN_POINTS,
    DEFAULT_ANOMALY_SIGMA,
    DEFAULT_ANOMALY_TREND_YEARS,
    DEFAULT_SPEC_COLUMNS,
    HgConfigService,
)

# ── スタイル定数 ──────────────────────────────────────────────────────────────

_BORDER = "#e2e8f0"
_TEXT = "#1e293b"
_SECTION_LABEL = "font-weight: 600; font-size: 13px; color: #374151;"
_HINT = "font-size: 11px; color: #9ca3af;"
_FRAME_STYLE = (
    "QFrame#anomaly_frame { background: #ffffff; border: 1px solid #e5e7eb;"
    " border-radius: 6px; }"
    "QFrame#anomaly_frame QWidget { background: #ffffff; }"
)
_TABLE_STYLE = (
    f"QTableWidget {{ border: 1px solid {_BORDER}; border-radius: 6px;"
    f" background: #ffffff; gridline-color: {_BORDER}; }}"
    f"QHeaderView::section {{ background: #f1f5f9; color: {_TEXT};"
    f" font-size: 12px; font-weight: 600; padding: 4px;"
    f" border: none; border-bottom: 1px solid {_BORDER}; }}"
    f"QTableWidget::item {{ padding: 4px 6px; font-size: 12px; color: {_TEXT}; }}"
)
_BTN_ADD = (
    "QPushButton { background: #3b82f6; color: white; border: none;"
    " padding: 4px 12px; border-radius: 4px; font-weight: 600; font-size: 12px; }"
    "QPushButton:hover { background: #2563eb; }"
)
_BTN_DEL = (
    "QPushButton { background: #ef4444; color: white; border: none;"
    " padding: 2px 8px; border-radius: 4px; font-size: 11px; font-weight: 600;"
    " min-height: 0; min-width: 0; }"
    "QPushButton:hover { background: #dc2626; }"
)


class AnomalyConfigWidget(QWidget):
    """異常検出設定ウィジェット。

    σ倍率、最低データ件数、トレンド期間を設定する。
    """

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._build_ui()

    def _build_ui(self) -> None:
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(8)

        lbl = QLabel("異常検出設定")
        lbl.setStyleSheet(_SECTION_LABEL)
        outer.addWidget(lbl)

        hint = QLabel("mean ± Nσ の閾値でデータの異常を判定します")
        hint.setStyleSheet(_HINT)
        outer.addWidget(hint)

        frame = QFrame()
        frame.setObjectName("anomaly_frame")
        frame.setStyleSheet(_FRAME_STYLE)
        form = QFormLayout(frame)
        form.setContentsMargins(16, 12, 16, 12)
        form.setSpacing(10)

        # σ倍率
        self._spin_sigma = QDoubleSpinBox()
        self._spin_sigma.setRange(0.5, 5.0)
        self._spin_sigma.setSingleStep(0.5)
        self._spin_sigma.setDecimals(1)
        self._spin_sigma.setSuffix(" σ")
        self._spin_sigma.setValue(DEFAULT_ANOMALY_SIGMA)
        form.addRow("σ倍率:", self._spin_sigma)

        # 最低データ件数
        self._spin_min = QSpinBox()
        self._spin_min.setRange(3, 100)
        self._spin_min.setSuffix(" 件")
        self._spin_min.setValue(DEFAULT_ANOMALY_MIN_POINTS)
        form.addRow("最低データ件数:", self._spin_min)

        # トレンド期間
        self._spin_years = QSpinBox()
        self._spin_years.setRange(1, 20)
        self._spin_years.setSuffix(" 年")
        self._spin_years.setValue(DEFAULT_ANOMALY_TREND_YEARS)
        form.addRow("トレンド期間:", self._spin_years)

        outer.addWidget(frame)

    def set_config(self, cfg: dict) -> None:
        """設定値をUIに反映する。

        Args:
            cfg: ``{"sigma": float, "min_points": int, "trend_years": int}``
        """
        self._spin_sigma.setValue(cfg.get("sigma", DEFAULT_ANOMALY_SIGMA))
        self._spin_min.setValue(cfg.get("min_points", DEFAULT_ANOMALY_MIN_POINTS))
        self._spin_years.setValue(cfg.get("trend_years", DEFAULT_ANOMALY_TREND_YEARS))

    def get_config(self) -> dict:
        """現在の設定値を返す。"""
        return {
            "sigma": self._spin_sigma.value(),
            "min_points": self._spin_min.value(),
            "trend_years": self._spin_years.value(),
        }


class SpecColumnsWidget(QWidget):
    """基準値列設定ウィジェット。

    bunseki.csv のどの列が基準値に該当するかと、基準値名を設定する。
    """

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._build_ui()

    def _build_ui(self) -> None:
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(8)

        lbl = QLabel("基準値列設定")
        lbl.setStyleSheet(_SECTION_LABEL)
        outer.addWidget(lbl)

        hint = QLabel("bunseki.csv のどの列が基準値の上限・下限に当たるかを設定します")
        hint.setStyleSheet(_HINT)
        outer.addWidget(hint)

        # テーブル
        self._table = QTableWidget()
        self._table.setColumnCount(4)
        self._table.setHorizontalHeaderLabels(
            ["基準値名", "上限列名", "下限列名", ""],
        )
        self._table.setStyleSheet(_TABLE_STYLE)
        self._table.setMaximumHeight(220)
        self._table.verticalHeader().setVisible(False)
        hh = self._table.horizontalHeader()
        hh.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        hh.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        hh.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        hh.setSectionResizeMode(3, QHeaderView.ResizeMode.Fixed)
        hh.resizeSection(3, 40)
        outer.addWidget(self._table)

        # 追加ボタン
        btn_row = QHBoxLayout()
        btn_row.addStretch()
        self._btn_add = QPushButton("行を追加")
        self._btn_add.setStyleSheet(_BTN_ADD)
        self._btn_add.clicked.connect(self._on_add_row)
        btn_row.addWidget(self._btn_add)
        outer.addLayout(btn_row)

    def set_columns(self, spec_columns: list[dict[str, str]]) -> None:
        """設定値をUIに反映する。

        Args:
            spec_columns: ``[{"upper_column": str, "lower_column": str, "name": str}, ...]``
        """
        self._table.setRowCount(len(spec_columns))
        for row, spec in enumerate(spec_columns):
            self._table.setItem(row, 0, QTableWidgetItem(spec.get("name", "")))
            self._table.setItem(row, 1, QTableWidgetItem(spec.get("upper_column", "")))
            self._table.setItem(row, 2, QTableWidgetItem(spec.get("lower_column", "")))
            self._set_delete_btn(row)

    def get_columns(self) -> list[dict[str, str]]:
        """現在の設定値を返す。"""
        result: list[dict[str, str]] = []
        for row in range(self._table.rowCount()):
            name = (self._table.item(row, 0) or QTableWidgetItem("")).text().strip()
            upper = (self._table.item(row, 1) or QTableWidgetItem("")).text().strip()
            lower = (self._table.item(row, 2) or QTableWidgetItem("")).text().strip()
            if name or upper or lower:
                result.append({
                    "name": name,
                    "upper_column": upper,
                    "lower_column": lower,
                })
        return result

    def _on_add_row(self) -> None:
        row = self._table.rowCount()
        self._table.insertRow(row)
        self._table.setItem(row, 0, QTableWidgetItem(""))
        self._table.setItem(row, 1, QTableWidgetItem(""))
        self._table.setItem(row, 2, QTableWidgetItem(""))
        self._set_delete_btn(row)

    def _set_delete_btn(self, row: int) -> None:
        btn = QPushButton("×")
        btn.setFixedSize(24, 24)
        btn.setStyleSheet(_BTN_DEL)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.clicked.connect(lambda _=False, r=row: self._on_remove_row(r))
        self._table.setCellWidget(row, 3, btn)

    def _on_remove_row(self, row: int) -> None:
        if 0 <= row < self._table.rowCount():
            self._table.removeRow(row)
            # 削除ボタンの行番号を再設定
            for r in range(self._table.rowCount()):
                self._set_delete_btn(r)
