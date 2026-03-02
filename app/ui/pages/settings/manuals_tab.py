"""マニュアル管理タブ。

プログラムで構築（.uiファイル不要）。
ManualService を通じてHTMLマニュアルのアップロード・プレビュー・削除を行う。
"""
from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QStandardItem, QStandardItemModel
from PySide6.QtWidgets import (
    QDialog,
    QFileDialog,
    QHBoxLayout,
    QMessageBox,
    QPushButton,
    QTextBrowser,
    QVBoxLayout,
    QWidget,
)

from app.services.manual_service import ManualService

_COLUMNS = ["カテゴリ", "名前", "ステータス"]


class ManualsTab(QWidget):
    """マニュアル管理タブ。"""

    def __init__(
        self, manual_service: ManualService, parent: QWidget | None = None
    ) -> None:
        super().__init__(parent)
        self.manual_service = manual_service
        self._build_ui()
        self._connect_signals()
        self.load_entries()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        # テーブル
        from PySide6.QtWidgets import QTableView, QHeaderView

        self._model = QStandardItemModel()
        self._model.setHorizontalHeaderLabels(_COLUMNS)

        self.table = QTableView()
        self.table.setModel(self._model)
        self.table.setSelectionBehavior(QTableView.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QTableView.SelectionMode.SingleSelection)
        self.table.setEditTriggers(QTableView.EditTrigger.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Stretch
        )
        self.table.verticalHeader().setVisible(False)
        layout.addWidget(self.table, 1)

        # ボタン行
        btn_row = QHBoxLayout()
        btn_row.setSpacing(8)

        self.btn_upload = QPushButton("アップロード")
        self.btn_upload.setStyleSheet(
            "background: #3b82f6; color: white; border: none; "
            "border-radius: 6px; padding: 8px 20px; font-weight: 600;"
        )
        btn_row.addWidget(self.btn_upload)

        self.btn_preview = QPushButton("プレビュー")
        self.btn_preview.setStyleSheet(
            "background: #10b981; color: white; border: none; "
            "border-radius: 6px; padding: 8px 20px; font-weight: 600;"
        )
        btn_row.addWidget(self.btn_preview)

        self.btn_delete = QPushButton("削除")
        self.btn_delete.setStyleSheet(
            "background: #ef4444; color: white; border: none; "
            "border-radius: 6px; padding: 8px 20px; font-weight: 600;"
        )
        btn_row.addWidget(self.btn_delete)

        btn_row.addStretch()
        layout.addLayout(btn_row)

    def _connect_signals(self) -> None:
        self.btn_upload.clicked.connect(self._on_upload)
        self.btn_preview.clicked.connect(self._on_preview)
        self.btn_delete.clicked.connect(self._on_delete)

    # ── データ読み込み ─────────────────────────────────────────────────────────

    def load_entries(self) -> None:
        """エントリ一覧をテーブルに反映する。"""
        self._model.removeRows(0, self._model.rowCount())
        self._entries = self.manual_service.get_all_entries()
        for entry in self._entries:
            cat_item = QStandardItem(entry["category"])
            name_item = QStandardItem(entry["name"])
            status_text = "登録済み" if entry["registered"] else "未登録"
            status_item = QStandardItem(status_text)
            if entry["registered"]:
                status_item.setForeground(Qt.GlobalColor.darkGreen)
            else:
                status_item.setForeground(Qt.GlobalColor.gray)
            for item in (cat_item, name_item, status_item):
                item.setEditable(False)
            self._model.appendRow([cat_item, name_item, status_item])

    # ── 選択中エントリ取得 ─────────────────────────────────────────────────────

    def _selected_entry(self) -> dict | None:
        indexes = self.table.selectionModel().selectedRows()
        if not indexes:
            QMessageBox.information(self, "選択", "エントリを選択してください。")
            return None
        row = indexes[0].row()
        return self._entries[row]

    # ── アップロード ───────────────────────────────────────────────────────────

    def _on_upload(self) -> None:
        entry = self._selected_entry()
        if not entry:
            return
        path, _ = QFileDialog.getOpenFileName(
            self,
            f"HTMLファイルを選択 — {entry['name']}",
            "",
            "HTML Files (*.html *.htm);;All Files (*)",
        )
        if not path:
            return
        err = self.manual_service.upload_manual(entry["key"], Path(path))
        if err:
            QMessageBox.warning(self, "エラー", err)
            return
        QMessageBox.information(
            self, "完了", f"「{entry['name']}」のマニュアルを登録しました。"
        )
        self.load_entries()

    # ── プレビュー ─────────────────────────────────────────────────────────────

    def _on_preview(self) -> None:
        entry = self._selected_entry()
        if not entry:
            return
        html = self.manual_service.get_manual_html(entry["key"])
        if not html:
            QMessageBox.information(
                self, "プレビュー", f"「{entry['name']}」のマニュアルは未登録です。"
            )
            return

        dlg = QDialog(self)
        dlg.setWindowTitle(f"プレビュー — {entry['name']}")
        dlg.resize(700, 500)
        layout = QVBoxLayout(dlg)
        browser = QTextBrowser()
        browser.setHtml(html)
        layout.addWidget(browser)
        btn_close = QPushButton("閉じる")
        btn_close.clicked.connect(dlg.accept)
        layout.addWidget(btn_close, alignment=Qt.AlignmentFlag.AlignRight)
        dlg.exec()

    # ── 削除 ───────────────────────────────────────────────────────────────────

    def _on_delete(self) -> None:
        entry = self._selected_entry()
        if not entry:
            return
        if not entry["registered"]:
            QMessageBox.information(
                self, "削除", f"「{entry['name']}」のマニュアルは未登録です。"
            )
            return
        ret = QMessageBox.question(
            self,
            "確認",
            f"「{entry['name']}」のマニュアルを削除しますか？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if ret != QMessageBox.StandardButton.Yes:
            return
        err = self.manual_service.delete_manual(entry["key"])
        if err:
            QMessageBox.warning(self, "エラー", err)
            return
        self.load_entries()
