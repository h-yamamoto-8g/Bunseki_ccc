"""データページ — bunseki.csv の検索・閲覧・エクスポート"""
import os
from pathlib import Path
from datetime import date

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QFrame,
    QAbstractItemView, QLineEdit, QComboBox, QScrollArea,
    QDialog, QDialogButtonBox, QRadioButton, QButtonGroup,
    QFileDialog, QMessageBox, QDateEdit, QSizePolicy, QApplication,
)
from PySide6.QtCore import Qt, QDate
from PySide6.QtGui import QColor, QFont

_BG2    = "#161b27"
_BG3    = "#1e2535"
_BORDER = "#2a3349"
_TEXT   = "#e8eaf0"
_TEXT2  = "#8b93a8"
_TEXT3  = "#5a6278"
_ACCENT = "#4a8cff"
_SUCCESS= "#2ecc8a"
_WARN   = "#f5a623"
_DANGER = "#e85454"

_HEADERS = [
    ("sample_request_number",   "依頼番号"),
    ("sample_sampling_date",    "サンプル日時"),
    ("sample_job_number",       "JOB番号"),
    ("valid_sample_display_name", "サンプル名"),
    ("valid_holder_display_name", "ホルダ名"),
    ("valid_test_display_name", "試験項目名"),
    ("test_raw_data",           "データ"),
    ("test_reported_data",      "データ_報告用"),
    ("test_unit_name",          "単位"),
    ("test_upper_limit_spec_1", "上限値_1"),
    ("test_upper_limit_spec_2", "上限値_2"),
    ("test_upper_limit_spec_3", "上限値_3"),
    ("test_upper_limit_spec_4", "上限値_4"),
    ("test_lower_limit_spec_1", "下限値_1"),
    ("test_lower_limit_spec_2", "下限値_2"),
    ("test_lower_limit_spec_3", "下限値_3"),
    ("test_lower_limit_spec_4", "下限値_4"),
    ("test_judgment",           "判定"),
]


class DataPage(QWidget):
    def __init__(self, data_loader, parent=None):
        super().__init__(parent)
        self.data_loader = data_loader
        self._current_df = None
        self._setup_ui()
        self._init_dropdowns()

    # ── UI ───────────────────────────────────────────────────────────────────

    def _setup_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # Topbar
        topbar = QFrame()
        topbar.setFixedHeight(48)
        topbar.setStyleSheet(f"QFrame {{ background:{_BG2}; border-bottom:1px solid {_BORDER}; }}")
        tl = QHBoxLayout(topbar)
        tl.setContentsMargins(20, 0, 20, 0)
        tl.addWidget(self._muted("データ"))
        tl.addStretch()
        export_btn = QPushButton("↓ CSVエクスポート")
        export_btn.setStyleSheet(f"""
            QPushButton {{ background:{_BG3}; color:{_TEXT}; border:1px solid {_BORDER};
                          padding:5px 12px; border-radius:6px; font-size:12px; }}
            QPushButton:hover {{ border-color:{_ACCENT}; color:{_ACCENT}; }}
        """)
        export_btn.clicked.connect(self._export_csv)
        tl.addWidget(export_btn)
        root.addWidget(topbar)

        # Scroll body
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        root.addWidget(scroll)

        body = QWidget()
        bl = QVBoxLayout(body)
        bl.setContentsMargins(20, 20, 20, 20)
        bl.setSpacing(12)
        scroll.setWidget(body)

        h1 = QLabel("データ")
        h1.setStyleSheet(f"font-size:20px; font-weight:700; color:{_TEXT};")
        bl.addWidget(h1)
        sub = QLabel("過去の分析データ一覧 — bunseki.csv（最大500件）")
        sub.setStyleSheet(f"font-size:12px; color:{_TEXT3};")
        bl.addWidget(sub)

        # Filter card
        fcard = QFrame()
        fcard.setStyleSheet(f"QFrame {{ background:{_BG2}; border:1px solid {_BORDER}; border-radius:8px; }}")
        grid = QVBoxLayout(fcard)
        grid.setContentsMargins(16, 12, 16, 12)
        grid.setSpacing(10)

        # Row 1: date, request_no, job_no
        row1 = QHBoxLayout()
        row1.setSpacing(16)

        self.date_from = QDateEdit()
        self.date_from.setCalendarPopup(True)
        self.date_from.setDisplayFormat("yyyy-MM-dd")
        self.date_from.setDate(QDate(2020, 1, 1))
        self.date_from.setFixedWidth(130)

        self.date_to = QDateEdit()
        self.date_to.setCalendarPopup(True)
        self.date_to.setDisplayFormat("yyyy-MM-dd")
        self.date_to.setDate(QDate.currentDate())
        self.date_to.setFixedWidth(130)

        self.request_input = QLineEdit()
        self.request_input.setPlaceholderText("部分一致...")
        self.request_input.setFixedWidth(140)

        self.job_input = QLineEdit()
        self.job_input.setPlaceholderText("部分一致...")
        self.job_input.setFixedWidth(140)

        row1.addLayout(self._col("期間（開始）", self.date_from))
        row1.addLayout(self._col("期間（終了）", self.date_to))
        row1.addLayout(self._col("依頼番号", self.request_input))
        row1.addLayout(self._col("JOB番号", self.job_input))
        row1.addStretch()
        grid.addLayout(row1)

        # Row 2: sample, holder, test, judgment
        row2 = QHBoxLayout()
        row2.setSpacing(16)

        self.sample_combo = QComboBox()
        self.sample_combo.setFixedWidth(170)
        self.sample_combo.addItem("全て")

        self.holder_combo = QComboBox()
        self.holder_combo.setFixedWidth(170)
        self.holder_combo.addItem("全て")

        self.test_combo = QComboBox()
        self.test_combo.setFixedWidth(170)
        self.test_combo.addItem("全て")

        self.judgment_combo = QComboBox()
        self.judgment_combo.setFixedWidth(120)
        self.judgment_combo.addItems(["全て", "NN", "異常"])

        row2.addLayout(self._col("サンプル名", self.sample_combo))
        row2.addLayout(self._col("ホルダ名", self.holder_combo))
        row2.addLayout(self._col("試験項目名", self.test_combo))
        row2.addLayout(self._col("判定", self.judgment_combo))
        row2.addStretch()

        search_btn = QPushButton("絞り込む")
        search_btn.setStyleSheet(f"""
            QPushButton {{ background:{_ACCENT}; color:white; border:none;
                          padding:6px 14px; border-radius:6px; font-size:12px; }}
            QPushButton:hover {{ background:#5a9dff; }}
        """)
        search_btn.clicked.connect(self._search)
        row2.addWidget(search_btn, alignment=Qt.AlignmentFlag.AlignBottom)
        grid.addLayout(row2)
        bl.addWidget(fcard)

        self.count_lbl = QLabel("条件を入力して「絞り込む」を押してください")
        self.count_lbl.setStyleSheet(f"font-size:11px; color:{_TEXT3};")
        bl.addWidget(self.count_lbl)

        # Table
        col_labels = [h for _, h in _HEADERS]
        self.table = QTableWidget(0, len(col_labels))
        self.table.setHorizontalHeaderLabels(col_labels)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setAlternatingRowColors(True)
        # stretch サンプル名列
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        self.table.setStyleSheet(f"""
            QTableWidget {{ background:{_BG2}; color:{_TEXT}; border:1px solid {_BORDER};
                           border-radius:8px; gridline-color:{_BORDER}; }}
            QTableWidget::item {{ color:{_TEXT}; border:none; padding:2px 8px; }}
            QTableWidget::item:alternate {{ background:{_BG3}; }}
            QTableWidget::item:selected {{ background:{_ACCENT}; color:white; }}
            QHeaderView::section {{ background:{_BG2}; color:{_TEXT3}; border:none;
                border-bottom:1px solid {_BORDER}; padding:8px 12px;
                font-size:11px; font-weight:bold; }}
        """)
        self.table.verticalHeader().setVisible(False)
        bl.addWidget(self.table)
        bl.addStretch()

    def _col(self, label_text: str, widget) -> QVBoxLayout:
        c = QVBoxLayout()
        c.setSpacing(3)
        lbl = QLabel(label_text)
        lbl.setStyleSheet(f"font-size:10px; color:{_TEXT3};")
        c.addWidget(lbl)
        c.addWidget(widget)
        return c

    def _muted(self, text: str) -> QLabel:
        lbl = QLabel(text)
        lbl.setStyleSheet(f"font-size:13px; font-weight:600; color:{_TEXT2};")
        return lbl

    # ── Data ─────────────────────────────────────────────────────────────────

    def _init_dropdowns(self):
        try:
            opts = self.data_loader.get_dropdown_values()
            self.sample_combo.addItems(opts.get("samples", []))
            self.holder_combo.addItems(opts.get("holders", []))
            self.test_combo.addItems(opts.get("tests", []))
        except Exception:
            pass

    def _search(self):
        date_from = self.date_from.date().toString("yyyy-MM-dd")
        date_to   = self.date_to.date().toString("yyyy-MM-dd")
        request_no = self.request_input.text().strip()
        job_no     = self.job_input.text().strip()
        sample  = self.sample_combo.currentText()
        holder  = self.holder_combo.currentText()
        test    = self.test_combo.currentText()
        judgment = self.judgment_combo.currentText()

        sample_names = [sample] if sample != "全て" else None
        holder_names = [holder] if holder != "全て" else None
        test_names   = [test]   if test   != "全て" else None

        self.count_lbl.setText("検索中...")
        QApplication.processEvents()

        try:
            df = self.data_loader.get_data_page(
                date_from=date_from,
                date_to=date_to,
                request_no=request_no,
                job_no=job_no,
                sample_names=sample_names,
                holder_names=holder_names,
                test_names=test_names,
                judgment_filter=judgment,
                limit=500,
            )
        except Exception as e:
            self.count_lbl.setText(f"エラー: {e}")
            return

        self._current_df = df
        self.table.setRowCount(0)

        if df is None or df.empty:
            self.count_lbl.setText("該当データなし")
            return

        for _, row in df.iterrows():
            r = self.table.rowCount()
            self.table.insertRow(r)

            judgment_val = str(row.get("test_judgment", ""))
            is_anom = judgment_val not in ("NN", "", "nan", "None")

            for col, (key, _) in enumerate(_HEADERS):
                raw = row.get(key, "")
                if key == "sample_sampling_date":
                    s = str(int(float(raw))) if raw and str(raw) not in ("nan", "") else ""
                    v = f"{s[:4]}-{s[4:6]}-{s[6:8]} {s[8:10]}:{s[10:12]}" if len(s) >= 12 else s
                elif key == "test_judgment":
                    v = judgment_val if judgment_val not in ("nan", "None", "") else "NN"
                else:
                    v = "" if str(raw) in ("nan", "None") else str(raw)

                item = QTableWidgetItem(v)
                if key == "test_judgment" and is_anom:
                    item.setForeground(QColor(_DANGER))
                    item.setFont(QFont("", -1, QFont.Weight.Bold))
                elif key == "test_judgment":
                    item.setForeground(QColor(_SUCCESS))
                self.table.setItem(r, col, item)
            QApplication.processEvents()

        self.count_lbl.setText(f"{len(df)} 件（最大500件）")

    def _export_csv(self):
        if self._current_df is None:
            # フィルタなしで全件
            ask_all = True
        else:
            dlg = _ExportDialog(self)
            if dlg.exec() != QDialog.DialogCode.Accepted:
                return
            ask_all = dlg.export_all()

        dest, _ = QFileDialog.getSaveFileName(
            self, "エクスポート先を選択", "bunseki_export.csv", "CSV (*.csv)"
        )
        if not dest:
            return

        try:
            if ask_all or self._current_df is None:
                df = self.data_loader.get_data_page(limit=999999)
            else:
                df = self._current_df

            col_keys = [k for k, _ in _HEADERS]
            out_cols = [k for k in col_keys if k in df.columns]
            df[out_cols].to_csv(dest, index=False, encoding="utf-8-sig")
            QMessageBox.information(self, "完了", f"エクスポートしました:\n{dest}")

            # 保存先フォルダを開く
            import subprocess, sys
            folder = str(Path(dest).parent)
            if sys.platform == "darwin":
                subprocess.run(["open", folder], check=False)
            elif sys.platform == "win32":
                subprocess.run(["explorer", folder], check=False)
        except Exception as e:
            QMessageBox.critical(self, "エラー", f"エクスポートに失敗しました:\n{e}")


class _ExportDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("CSVエクスポート")
        self.resize(320, 140)
        vl = QVBoxLayout(self)
        vl.setSpacing(12)

        lbl = QLabel("出力範囲を選択してください:")
        lbl.setStyleSheet(f"color:{_TEXT};")
        vl.addWidget(lbl)

        self._rb_all = QRadioButton("全データ（bunseki.csv 全件）")
        self._rb_filtered = QRadioButton("フィルタリング済みデータ（現在の表示）")
        self._rb_filtered.setChecked(True)
        for rb in (self._rb_all, self._rb_filtered):
            rb.setStyleSheet(f"color:{_TEXT};")
            vl.addWidget(rb)

        btns = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        btns.accepted.connect(self.accept)
        btns.rejected.connect(self.reject)
        vl.addWidget(btns)

    def export_all(self) -> bool:
        return self._rb_all.isChecked()
