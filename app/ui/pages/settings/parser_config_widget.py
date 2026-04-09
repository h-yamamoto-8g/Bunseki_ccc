"""パーサー設定ウィジェット — 分析結果パーサーの登録・テスト・マッピング設定。

HgConfigTab の「入力」ステータスブロックに埋め込まれる。
"""
from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QFileDialog,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QMessageBox,
    QPlainTextEdit,
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

_EDITOR_STYLE = (
    f"QPlainTextEdit {{ background: #1e293b; color: #e2e8f0;"
    f" border: 1px solid {_BORDER}; border-radius: 6px;"
    f" font-family: 'Consolas', 'Courier New', monospace;"
    f" font-size: 12px; padding: 8px; }}"
)

_BTN_PRIMARY = (
    "QPushButton { background: #3b82f6; color: white; border: none;"
    " padding: 6px 16px; border-radius: 5px; font-size: 12px; font-weight: 600; }"
    "QPushButton:hover { background: #2563eb; }"
)
_BTN_SECONDARY = (
    f"QPushButton {{ background: #ffffff; color: #64748b; border: 1px solid {_BORDER};"
    f" padding: 6px 16px; border-radius: 5px; font-size: 12px; font-weight: 600; }}"
    f"QPushButton:hover {{ background: #f1f5f9; }}"
)
_BTN_DANGER = (
    "QPushButton { background: #ef4444; color: white; border: none;"
    " padding: 6px 16px; border-radius: 5px; font-size: 12px; font-weight: 600; }"
    "QPushButton:hover { background: #dc2626; }"
)
_TABLE_STYLE = (
    f"QTableWidget {{ border: 1px solid {_BORDER}; border-radius: 6px;"
    f" background: #ffffff; gridline-color: {_BORDER}; }}"
    f"QHeaderView::section {{ background: #f1f5f9; color: {_TEXT};"
    f" font-size: 12px; font-weight: 600; padding: 4px;"
    f" border: none; border-bottom: 1px solid {_BORDER}; }}"
    f"QTableWidget::item {{ padding: 4px 6px; font-size: 12px; color: {_TEXT}; }}"
)

_SECTION_LABEL_STYLE = "font-weight: 600; font-size: 13px; color: #374151;"
_HINT_STYLE = "font-size: 11px; color: #9ca3af;"

_FULLSCREEN_EDITOR_STYLE = (
    "QPlainTextEdit { background: #1e293b; color: #e2e8f0;"
    " border: none; font-family: 'Consolas', 'Courier New', monospace;"
    " font-size: 14px; padding: 16px; line-height: 1.6; }"
)


class CodeEditorDialog(QDialog):
    """パーサーコードの全画面編集ダイアログ。

    Args:
        code: 初期コード文字列。
        parent: 親ウィジェット。
    """

    def __init__(self, code: str, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("パーサーコード編集")
        self.setModal(True)
        self.showMaximized()

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        # ── ツールバー ────────────────────────────────────────────
        toolbar = QWidget()
        toolbar.setStyleSheet("background: #0f172a;")
        toolbar.setFixedHeight(48)
        tb = QHBoxLayout(toolbar)
        tb.setContentsMargins(16, 0, 16, 0)
        tb.setSpacing(12)

        lbl = QLabel("パーサーコード編集")
        lbl.setStyleSheet(
            "color: #e2e8f0; font-size: 14px; font-weight: 600;"
        )
        tb.addWidget(lbl)

        hint = QLabel(
            "parse(file_path: str) -> list[dict[str, str]] を定義してください"
        )
        hint.setStyleSheet("color: #64748b; font-size: 12px;")
        tb.addWidget(hint)

        tb.addStretch()

        btn_cancel = QPushButton("キャンセル")
        btn_cancel.setStyleSheet(
            "QPushButton { background: transparent; color: #94a3b8;"
            " border: 1px solid #334155; padding: 6px 20px;"
            " border-radius: 5px; font-size: 12px; font-weight: 600; }"
            "QPushButton:hover { background: #1e293b; color: #e2e8f0; }"
        )
        btn_cancel.clicked.connect(self.reject)
        tb.addWidget(btn_cancel)

        btn_ok = QPushButton("適用して閉じる")
        btn_ok.setStyleSheet(
            "QPushButton { background: #3b82f6; color: white;"
            " border: none; padding: 6px 20px;"
            " border-radius: 5px; font-size: 12px; font-weight: 600; }"
            "QPushButton:hover { background: #2563eb; }"
        )
        btn_ok.clicked.connect(self.accept)
        tb.addWidget(btn_ok)

        outer.addWidget(toolbar)

        # ── エディタ ──────────────────────────────────────────────
        self._editor = QPlainTextEdit()
        self._editor.setStyleSheet(_FULLSCREEN_EDITOR_STYLE)
        self._editor.setTabStopDistance(32)
        self._editor.setPlainText(code)
        outer.addWidget(self._editor, 1)

    @property
    def code(self) -> str:
        """編集後のコードを返す。"""
        return self._editor.toPlainText()


_DEFAULT_CODE = '''def parse(file_path: str) -> list[dict[str, str]]:
    """分析結果ファイルを読み込み、辞書のリストを返す。

    Args:
        file_path: 分析結果ファイルの絶対パス

    Returns:
        すべてのキー・値が文字列の辞書のリスト。
    """
    import csv

    results = []
    with open(file_path, encoding="cp932") as f:
        reader = csv.DictReader(f)
        for row in reader:
            results.append({
                "sample_name": row["サンプル名"],
                # 必要なキーを追加:
                # "pH": row["pH値"],
            })
    return results
'''


class ParserConfigWidget(QWidget):
    """パーサー設定ウィジェット。

    Args:
        analysis_service: 分析結果サービス。
        parent: 親ウィジェット。
    """

    def __init__(
        self,
        analysis_service: AnalysisResultService,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._service = analysis_service
        self._hg_code: str = ""
        self._test_result: list[dict[str, str]] = []
        self._holder_test_options: list[dict] = []
        self._build_ui()
        self._connect_signals()

    def set_hg_code(self, hg_code: str) -> None:
        """ホルダグループコードを設定してUIを更新する。

        Args:
            hg_code: ホルダグループコード。
        """
        self._hg_code = hg_code
        self._load_parser()

    def set_holder_test_options(self, options: list[dict]) -> None:
        """キーマッピングで使用するホルダ・テストの選択肢を設定する。

        Args:
            options: ``[{"holder_code": str, "holder_name": str,
                         "test_code": str, "test_name": str}, ...]``
        """
        self._holder_test_options = options

    def save(self) -> None:
        """現在の設定を保存する。"""
        if not self._hg_code:
            return
        self._on_save_code()
        self._on_save_mapping()

    # ── UI 構築 ───────────────────────────────────────────────────────────────

    def _build_ui(self) -> None:
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(12)

        # ── コードエディタセクション ──────────────────────────────
        lbl_code = QLabel("パーサーコード")
        lbl_code.setStyleSheet(_SECTION_LABEL_STYLE)
        outer.addWidget(lbl_code)

        hint = QLabel(
            "parse(file_path: str) -> list[dict[str, str]] を定義してください。"
            " 使用可能モジュール: csv, json, re, pandas, pdfplumber 等"
        )
        hint.setStyleSheet(_HINT_STYLE)
        hint.setWordWrap(True)
        outer.addWidget(hint)

        self._code_editor = QPlainTextEdit()
        self._code_editor.setStyleSheet(_EDITOR_STYLE)
        self._code_editor.setMinimumHeight(200)
        self._code_editor.setMaximumHeight(350)
        self._code_editor.setTabStopDistance(32)
        outer.addWidget(self._code_editor)

        # コード操作ボタン
        code_btns = QHBoxLayout()
        code_btns.setSpacing(8)

        self._btn_fullscreen = QPushButton("全画面で編集")
        self._btn_fullscreen.setStyleSheet(_BTN_SECONDARY)
        code_btns.addWidget(self._btn_fullscreen)

        self._btn_upload_code = QPushButton("ファイルから読み込み")
        self._btn_upload_code.setStyleSheet(_BTN_SECONDARY)
        code_btns.addWidget(self._btn_upload_code)

        self._btn_save_code = QPushButton("コードを保存")
        self._btn_save_code.setStyleSheet(_BTN_PRIMARY)
        code_btns.addWidget(self._btn_save_code)

        self._btn_delete_code = QPushButton("削除")
        self._btn_delete_code.setStyleSheet(_BTN_DANGER)
        code_btns.addWidget(self._btn_delete_code)

        code_btns.addStretch()
        outer.addLayout(code_btns)

        # ── テスト実行セクション ──────────────────────────────────
        lbl_test = QLabel("テスト実行")
        lbl_test.setStyleSheet(_SECTION_LABEL_STYLE)
        outer.addWidget(lbl_test)

        test_row = QHBoxLayout()
        test_row.setSpacing(8)

        self._lbl_test_file = QLabel("ファイル未選択")
        self._lbl_test_file.setStyleSheet("color: #9ca3af; font-size: 12px;")
        self._lbl_test_file.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred,
        )
        test_row.addWidget(self._lbl_test_file)

        self._btn_select_test = QPushButton("テストファイルを選択")
        self._btn_select_test.setStyleSheet(_BTN_SECONDARY)
        test_row.addWidget(self._btn_select_test)

        self._btn_run_test = QPushButton("テスト実行")
        self._btn_run_test.setStyleSheet(_BTN_PRIMARY)
        self._btn_run_test.setEnabled(False)
        test_row.addWidget(self._btn_run_test)

        outer.addLayout(test_row)

        # テスト結果
        self._lbl_test_status = QLabel("")
        self._lbl_test_status.setStyleSheet("font-size: 12px;")
        self._lbl_test_status.setVisible(False)
        outer.addWidget(self._lbl_test_status)

        self._test_table = QTableWidget()
        self._test_table.setStyleSheet(_TABLE_STYLE)
        self._test_table.setMaximumHeight(200)
        self._test_table.setVisible(False)
        self._test_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        outer.addWidget(self._test_table)

        # ── マッピング設定セクション ──────────────────────────────
        lbl_mapping = QLabel("キーマッピング設定")
        lbl_mapping.setStyleSheet(_SECTION_LABEL_STYLE)
        outer.addWidget(lbl_mapping)

        # サンプル名キー
        sample_key_row = QHBoxLayout()
        sample_key_row.setSpacing(8)
        sample_key_row.addWidget(QLabel("サンプル名キー:"))
        self._combo_sample_key = QComboBox()
        self._combo_sample_key.setMinimumWidth(200)
        sample_key_row.addWidget(self._combo_sample_key)
        sample_key_row.addStretch()
        outer.addLayout(sample_key_row)

        # マッピングテーブル
        self._mapping_table = QTableWidget()
        self._mapping_table.setColumnCount(3)
        self._mapping_table.setHorizontalHeaderLabels(
            ["JSONキー", "holder_code", "test_code"],
        )
        self._mapping_table.setStyleSheet(_TABLE_STYLE)
        self._mapping_table.setMaximumHeight(250)
        hh = self._mapping_table.horizontalHeader()
        hh.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        hh.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        hh.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        outer.addWidget(self._mapping_table)

        # マッピング保存ボタン
        mapping_btns = QHBoxLayout()
        mapping_btns.addStretch()
        self._btn_save_mapping = QPushButton("マッピングを保存")
        self._btn_save_mapping.setStyleSheet(_BTN_PRIMARY)
        mapping_btns.addWidget(self._btn_save_mapping)
        outer.addLayout(mapping_btns)

    def _connect_signals(self) -> None:
        self._btn_fullscreen.clicked.connect(self._on_open_fullscreen)
        self._btn_upload_code.clicked.connect(self._on_upload_code)
        self._btn_save_code.clicked.connect(self._on_save_code)
        self._btn_delete_code.clicked.connect(self._on_delete_code)
        self._btn_select_test.clicked.connect(self._on_select_test_file)
        self._btn_run_test.clicked.connect(self._on_run_test)
        self._btn_save_mapping.clicked.connect(self._on_save_mapping)

    # ── データ読み込み ────────────────────────────────────────────────────────

    def _load_parser(self) -> None:
        """保存済みパーサーコードとマッピング設定を読み込む。"""
        code = self._service.get_parser_code(self._hg_code)
        if code:
            self._code_editor.setPlainText(code)
        else:
            self._code_editor.setPlainText(_DEFAULT_CODE)

        cfg = self._service.get_parser_config(self._hg_code)
        self._load_mapping_config(cfg)

        # テスト結果リセット
        self._test_result = []
        self._test_table.setVisible(False)
        self._lbl_test_status.setVisible(False)
        self._lbl_test_file.setText("ファイル未選択")
        self._btn_run_test.setEnabled(False)
        self._test_file_path = ""

    def _load_mapping_config(self, cfg: dict) -> None:
        """マッピング設定をUIに反映する。"""
        sample_key = cfg.get("sample_name_key", "")
        key_mapping = cfg.get("key_mapping", {})

        # サンプル名キーの復元
        self._combo_sample_key.clear()
        if sample_key:
            self._combo_sample_key.addItem(sample_key)

        # マッピングテーブルの復元
        self._mapping_table.setRowCount(len(key_mapping))
        for row, (json_key, mapping) in enumerate(key_mapping.items()):
            # JSONキー (読み取り専用)
            item = QTableWidgetItem(json_key)
            item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self._mapping_table.setItem(row, 0, item)

            # holder_code (編集可能 or ドロップダウン)
            holder_item = QTableWidgetItem(mapping.get("holder_code", ""))
            self._mapping_table.setItem(row, 1, holder_item)

            # test_code (編集可能 or ドロップダウン)
            test_item = QTableWidgetItem(mapping.get("test_code", ""))
            self._mapping_table.setItem(row, 2, test_item)

    # ── コード操作ハンドラ ────────────────────────────────────────────────────

    def _on_open_fullscreen(self) -> None:
        """全画面ダイアログでコードを編集する。"""
        dlg = CodeEditorDialog(self._code_editor.toPlainText(), parent=self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            self._code_editor.setPlainText(dlg.code)

    def _on_upload_code(self) -> None:
        """ファイルからPythonコードを読み込む。"""
        path, _ = QFileDialog.getOpenFileName(
            self, "パーサーコードを選択", "", "Python Files (*.py);;All Files (*)",
        )
        if not path:
            return
        try:
            code = Path(path).read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError) as e:
            QMessageBox.warning(self, "読み込みエラー", str(e))
            return
        self._code_editor.setPlainText(code)

    def _on_save_code(self) -> None:
        """コードをバリデーションして保存する。"""
        if not self._hg_code:
            return
        code = self._code_editor.toPlainText().strip()
        if not code:
            QMessageBox.warning(self, "保存エラー", "コードが空です。")
            return

        errors = self._service.save_parser(self._hg_code, code)
        if errors:
            QMessageBox.warning(
                self, "バリデーションエラー",
                "以下の問題が見つかりました:\n\n" + "\n".join(f"- {e}" for e in errors),
            )
            return
        QMessageBox.information(self, "保存完了", "パーサーコードを保存しました。")

    def _on_delete_code(self) -> None:
        """パーサーコードを削除する。"""
        if not self._hg_code:
            return
        reply = QMessageBox.question(
            self, "確認",
            "パーサーコードを削除しますか？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            from app.core import analysis_parser_store
            analysis_parser_store.delete_parser_code(self._hg_code)
            self._code_editor.setPlainText(_DEFAULT_CODE)
            QMessageBox.information(self, "削除完了", "パーサーコードを削除しました。")

    # ── テスト実行ハンドラ ────────────────────────────────────────────────────

    def _on_select_test_file(self) -> None:
        """テストファイルを選択する。"""
        path, _ = QFileDialog.getOpenFileName(
            self, "テストファイルを選択", "",
            "Data Files (*.csv *.txt *.tsv *.pdf);;All Files (*)",
        )
        if not path:
            return
        self._test_file_path = path
        self._lbl_test_file.setText(Path(path).name)
        self._lbl_test_file.setStyleSheet("color: #1f2937; font-size: 12px;")
        self._btn_run_test.setEnabled(True)

    def _on_run_test(self) -> None:
        """テスト実行を行う。"""
        code = self._code_editor.toPlainText().strip()
        if not code:
            QMessageBox.warning(self, "テストエラー", "コードが空です。")
            return

        try:
            result = self._service.test_parser(code, self._test_file_path)
        except Exception as e:
            self._lbl_test_status.setText(f"エラー: {e}")
            self._lbl_test_status.setStyleSheet("color: #ef4444; font-size: 12px;")
            self._lbl_test_status.setVisible(True)
            self._test_table.setVisible(False)
            return

        self._test_result = result
        self._show_test_result(result)
        self._update_mapping_from_result(result)

    def _show_test_result(self, result: list[dict[str, str]]) -> None:
        """テスト結果をプレビューテーブルに表示する。"""
        if not result:
            self._lbl_test_status.setText("結果: 0 件のレコード")
            self._lbl_test_status.setStyleSheet("color: #f59e0b; font-size: 12px;")
            self._lbl_test_status.setVisible(True)
            self._test_table.setVisible(False)
            return

        self._lbl_test_status.setText(f"成功: {len(result)} 件のレコード")
        self._lbl_test_status.setStyleSheet("color: #10b981; font-size: 12px;")
        self._lbl_test_status.setVisible(True)

        # キーを取得
        keys = list(result[0].keys())
        self._test_table.setColumnCount(len(keys))
        self._test_table.setHorizontalHeaderLabels(keys)
        self._test_table.setRowCount(len(result))

        for r, record in enumerate(result):
            for c, key in enumerate(keys):
                item = QTableWidgetItem(record.get(key, ""))
                item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                self._test_table.setItem(r, c, item)

        hh = self._test_table.horizontalHeader()
        for c in range(len(keys)):
            hh.setSectionResizeMode(c, QHeaderView.ResizeMode.ResizeToContents)
        self._test_table.setVisible(True)

    def _update_mapping_from_result(self, result: list[dict[str, str]]) -> None:
        """テスト結果からサンプル名キーのドロップダウンとマッピングテーブルを更新する。"""
        if not result:
            return

        keys = list(result[0].keys())

        # サンプル名キードロップダウンを更新
        current_sample_key = self._combo_sample_key.currentText()
        self._combo_sample_key.clear()
        for key in keys:
            self._combo_sample_key.addItem(key)
        # 以前の選択を復元
        idx = self._combo_sample_key.findText(current_sample_key)
        if idx >= 0:
            self._combo_sample_key.setCurrentIndex(idx)

        # 既存のマッピングを取得
        existing_mapping: dict[str, dict[str, str]] = {}
        for row in range(self._mapping_table.rowCount()):
            json_key_item = self._mapping_table.item(row, 0)
            holder_item = self._mapping_table.item(row, 1)
            test_item = self._mapping_table.item(row, 2)
            if json_key_item:
                existing_mapping[json_key_item.text()] = {
                    "holder_code": holder_item.text() if holder_item else "",
                    "test_code": test_item.text() if test_item else "",
                }

        # サンプル名キーを除外したキーでマッピングテーブルを再構築
        sample_key = self._combo_sample_key.currentText()
        mapping_keys = [k for k in keys if k != sample_key]

        self._mapping_table.setRowCount(len(mapping_keys))
        for row, json_key in enumerate(mapping_keys):
            # JSONキー (読み取り専用)
            item = QTableWidgetItem(json_key)
            item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self._mapping_table.setItem(row, 0, item)

            # 既存マッピングを復元
            existing = existing_mapping.get(json_key, {})
            holder_item = QTableWidgetItem(existing.get("holder_code", ""))
            self._mapping_table.setItem(row, 1, holder_item)

            test_item = QTableWidgetItem(existing.get("test_code", ""))
            self._mapping_table.setItem(row, 2, test_item)

    # ── マッピング保存ハンドラ ────────────────────────────────────────────────

    def _on_save_mapping(self) -> None:
        """マッピング設定を保存する。"""
        if not self._hg_code:
            return

        sample_key = self._combo_sample_key.currentText()
        key_mapping: dict[str, dict[str, str]] = {}

        for row in range(self._mapping_table.rowCount()):
            json_key_item = self._mapping_table.item(row, 0)
            holder_item = self._mapping_table.item(row, 1)
            test_item = self._mapping_table.item(row, 2)

            if not json_key_item:
                continue

            json_key = json_key_item.text()
            holder_code = holder_item.text() if holder_item else ""
            test_code = test_item.text() if test_item else ""

            if holder_code or test_code:
                key_mapping[json_key] = {
                    "holder_code": holder_code,
                    "test_code": test_code,
                }

        self._service.save_parser_config(self._hg_code, sample_key, key_mapping)
        QMessageBox.information(self, "保存完了", "マッピング設定を保存しました。")
