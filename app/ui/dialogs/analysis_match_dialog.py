"""分析結果の照合ダイアログ。

パーサーで読み込んだ分析結果と、テーブルのサンプルを手動照合するためのダイアログ。
ファジーマッチングで事前選択し、ユーザーが確認・修正した後に「適用」で
input_data に値を書き込む。
"""
from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QPushButton,
    QSizePolicy,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from app.services.analysis_result_service import AnalysisResultService


# ── スタイル定数 ──────────────────────────────────────────────────────────────

_BORDER = "#e2e8f0"
_TEXT = "#1e293b"
_ACCENT = "#3b82f6"

_TABLE_STYLE = (
    f"QTableWidget {{ border: 1px solid {_BORDER}; border-radius: 6px;"
    f" background: #ffffff; gridline-color: {_BORDER}; }}"
    f"QHeaderView::section {{ background: #f1f5f9; color: {_TEXT};"
    f" font-size: 12px; font-weight: 600; padding: 4px;"
    f" border: none; border-bottom: 1px solid {_BORDER}; }}"
    f"QTableWidget::item {{ padding: 4px 6px; font-size: 12px; color: {_TEXT}; }}"
)

_BTN_PRIMARY = (
    f"QPushButton {{ background: {_ACCENT}; color: white; border: none;"
    f" padding: 8px 24px; border-radius: 6px; font-size: 13px; font-weight: 600; }}"
    f"QPushButton:hover {{ background: #2563eb; }}"
)
_BTN_SECONDARY = (
    f"QPushButton {{ background: #ffffff; color: #64748b; border: 1px solid {_BORDER};"
    f" padding: 8px 24px; border-radius: 6px; font-size: 13px; font-weight: 600; }}"
    f"QPushButton:hover {{ background: #f1f5f9; }}"
)


class AnalysisMatchDialog(QDialog):
    """分析結果の照合ダイアログ。

    Args:
        parsed_data: パーサー出力。
        sample_name_key: JSON 内のサンプル名キー。
        key_mapping: ``{json_key: {"holder_code": str, "test_code": str}}``。
        table_rows: テーブル行データ（_row_key, valid_sample_display_name,
                    valid_holder_set_code, valid_test_set_code を含む）。
        file_name: 読み込みファイル名（表示用）。
        analysis_service: 分析結果サービス。
        parent: 親ウィジェット。
    """

    def __init__(
        self,
        parsed_data: list[dict[str, str]],
        sample_name_key: str,
        key_mapping: dict[str, dict[str, str]],
        table_rows: list[dict],
        file_name: str,
        analysis_service: AnalysisResultService,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._parsed_data = parsed_data
        self._sample_name_key = sample_name_key
        self._key_mapping = key_mapping
        self._table_rows = table_rows
        self._file_name = file_name
        self._service = analysis_service

        # 結果
        self._result_values: dict[str, str] = {}
        self._sample_mapping: dict[str, str] = {}

        self.setWindowTitle("分析結果の照合")
        self.setMinimumSize(800, 600)
        self.resize(900, 700)
        self.setModal(True)

        self._build_ui()
        self._populate()

    @property
    def result_values(self) -> dict[str, str]:
        """適用された input_data 値。{row_key: value}。"""
        return self._result_values

    @property
    def sample_mapping(self) -> dict[str, str]:
        """サンプル照合結果。{system_name: analysis_name}。"""
        return self._sample_mapping

    # ── UI 構築 ───────────────────────────────────────────────────────────────

    def _build_ui(self) -> None:
        outer = QVBoxLayout(self)
        outer.setContentsMargins(16, 16, 16, 16)
        outer.setSpacing(12)

        # ヘッダー
        lbl_file = QLabel(f"読み込みファイル: {self._file_name}")
        lbl_file.setStyleSheet("font-size: 13px; color: #374151;")
        outer.addWidget(lbl_file)

        lbl_records = QLabel(f"レコード数: {len(self._parsed_data)} 件")
        lbl_records.setStyleSheet("font-size: 12px; color: #6b7280;")
        outer.addWidget(lbl_records)

        # ── サンプル照合テーブル ──────────────────────────────────
        lbl_match = QLabel("サンプル照合")
        lbl_match.setStyleSheet("font-weight: 600; font-size: 14px; color: #1f2937;")
        outer.addWidget(lbl_match)

        self._match_table = QTableWidget()
        self._match_table.setColumnCount(3)
        self._match_table.setHorizontalHeaderLabels(
            ["サンプル名 (システム)", "分析名 (分析結果)", "一致率"],
        )
        self._match_table.setStyleSheet(_TABLE_STYLE)
        self._match_table.setMaximumHeight(220)
        hh = self._match_table.horizontalHeader()
        hh.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        hh.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        hh.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self._match_table.verticalHeader().setVisible(False)
        outer.addWidget(self._match_table)

        # ── プレビューテーブル ────────────────────────────────────
        lbl_preview = QLabel("プレビュー")
        lbl_preview.setStyleSheet("font-weight: 600; font-size: 14px; color: #1f2937;")
        outer.addWidget(lbl_preview)

        self._preview_table = QTableWidget()
        self._preview_table.setStyleSheet(_TABLE_STYLE)
        self._preview_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        hh2 = self._preview_table.horizontalHeader()
        self._preview_table.verticalHeader().setVisible(False)
        outer.addWidget(self._preview_table, 1)

        # ── ボタン ────────────────────────────────────────────────
        btn_bar = QHBoxLayout()
        btn_bar.addStretch()

        btn_cancel = QPushButton("キャンセル")
        btn_cancel.setStyleSheet(_BTN_SECONDARY)
        btn_cancel.clicked.connect(self.reject)
        btn_bar.addWidget(btn_cancel)

        self._btn_apply = QPushButton("適用")
        self._btn_apply.setStyleSheet(_BTN_PRIMARY)
        self._btn_apply.clicked.connect(self._on_apply)
        btn_bar.addWidget(self._btn_apply)

        outer.addLayout(btn_bar)

    # ── データ投入 ────────────────────────────────────────────────────────────

    def _populate(self) -> None:
        """ファジーマッチングとプレビューを初期化する。"""
        # 分析結果のサンプル名一覧
        analysis_names: list[str] = []
        for record in self._parsed_data:
            name = record.get(self._sample_name_key, "")
            if name and name not in analysis_names:
                analysis_names.append(name)

        # システム側のユニークサンプル名一覧
        system_names: list[str] = []
        seen: set[str] = set()
        for row in self._table_rows:
            name = str(row.get("valid_sample_display_name", ""))
            if name and name not in seen:
                system_names.append(name)
                seen.add(name)

        # ファジーマッチング
        matches = self._service.fuzzy_match_samples(system_names, analysis_names)

        # 照合テーブルに表示
        self._match_table.setRowCount(len(system_names))
        self._combo_widgets: dict[str, QComboBox] = {}

        for row, sys_name in enumerate(system_names):
            # システムサンプル名
            item = QTableWidgetItem(sys_name)
            item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self._match_table.setItem(row, 0, item)

            # 分析名ドロップダウン
            combo = QComboBox()
            combo.addItem("")  # 空選択
            for ana_name in analysis_names:
                combo.addItem(ana_name)
            self._match_table.setCellWidget(row, 1, combo)
            self._combo_widgets[sys_name] = combo

            # ファジーマッチ結果を事前選択
            best_name, score = matches.get(sys_name, ("", 0.0))
            if best_name:
                idx = combo.findText(best_name)
                if idx >= 0:
                    combo.setCurrentIndex(idx)

            # 一致率表示
            score_pct = int(score * 100)
            score_item = QTableWidgetItem(f"{score_pct}%")
            score_item.setFlags(score_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            score_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            if score_pct < 60:
                score_item.setForeground(QColor("#ef4444"))
            elif score_pct < 80:
                score_item.setForeground(QColor("#f59e0b"))
            else:
                score_item.setForeground(QColor("#10b981"))
            self._match_table.setItem(row, 2, score_item)

            # ドロップダウン変更時にプレビューを更新
            combo.currentTextChanged.connect(self._update_preview)

        self._update_preview()

    def _update_preview(self) -> None:
        """サンプル照合に基づいてプレビューテーブルを更新する。"""
        # 現在の照合結果を収集
        sample_mapping: dict[str, str] = {}
        for sys_name, combo in self._combo_widgets.items():
            ana_name = combo.currentText()
            if ana_name:
                sample_mapping[sys_name] = ana_name

        # マッピング適用
        input_values = self._service.apply_mapping(
            self._parsed_data,
            sample_mapping,
            self._key_mapping,
            self._sample_name_key,
            self._table_rows,
        )

        # 重複検出
        duplicate_keys = self._service.detect_duplicate_values(input_values)

        # 既存のinput_dataを取得
        existing_input: dict[str, str] = {}
        for row in self._table_rows:
            key = row.get("_row_key", "")
            val = row.get("input_data", "")
            if key and val:
                existing_input[key] = val

        # プレビューテーブルを構築
        # 値がある行のみ表示
        preview_rows: list[dict] = []
        for row in self._table_rows:
            row_key = row.get("_row_key", "")
            new_val = input_values.get(row_key, "")
            if new_val:
                preview_rows.append({
                    "sample": str(row.get("valid_sample_display_name", "")),
                    "test": str(row.get("valid_test_display_name", "")),
                    "current": existing_input.get(row_key, ""),
                    "new": new_val,
                    "row_key": row_key,
                    "is_duplicate": row_key in duplicate_keys,
                })

        self._preview_table.setColumnCount(4)
        self._preview_table.setHorizontalHeaderLabels(
            ["サンプル名", "試験項目", "現在値", "新値"],
        )
        self._preview_table.setRowCount(len(preview_rows))

        hh = self._preview_table.horizontalHeader()
        for c in range(4):
            hh.setSectionResizeMode(c, QHeaderView.ResizeMode.Stretch)

        for r, prow in enumerate(preview_rows):
            for c, key in enumerate(["sample", "test", "current", "new"]):
                item = QTableWidgetItem(prow[key])
                item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)

                # 色分け
                if prow["is_duplicate"]:
                    item.setBackground(QColor("#fee2e2"))  # 薄赤: 重複
                elif prow["current"] and prow["current"] != prow["new"]:
                    item.setBackground(QColor("#fef3c7"))  # 薄黄: 上書き
                elif key == "new":
                    item.setBackground(QColor("#d1fae5"))  # 薄緑: 新規

                self._preview_table.setItem(r, c, item)

    # ── 適用 ──────────────────────────────────────────────────────────────────

    def _on_apply(self) -> None:
        """照合結果を適用して閉じる。"""
        # 最終的な照合結果を収集
        sample_mapping: dict[str, str] = {}
        for sys_name, combo in self._combo_widgets.items():
            ana_name = combo.currentText()
            if ana_name:
                sample_mapping[sys_name] = ana_name

        # マッピング適用
        self._result_values = self._service.apply_mapping(
            self._parsed_data,
            sample_mapping,
            self._key_mapping,
            self._sample_name_key,
            self._table_rows,
        )
        self._sample_mapping = sample_mapping

        self.accept()
