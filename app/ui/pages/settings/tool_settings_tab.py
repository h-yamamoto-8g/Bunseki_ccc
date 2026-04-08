"""ツール設定タブ — Lab-Aid / 入力ツール のパスを設定する。"""
from __future__ import annotations

import os

from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from app.services.data_config_service import DataConfigService

_FRAME_STYLE = (
    "QFrame#tool_section { background: #ffffff; border: 1px solid #e5e7eb; "
    "border-radius: 8px; }"
    "QFrame#tool_section QWidget { background: #ffffff; }"
)
_TITLE_STYLE = "font-size: 14px; font-weight: 700; color: #1f2937; border: none;"
_LABEL_STYLE = "font-size: 12px; color: #6b7280; border: none;"
_INPUT_STYLE = (
    "background: #f9fafb; border: 1px solid #e5e7eb; "
    "border-radius: 4px; padding: 6px 8px;"
)
_PREVIEW_STYLE = (
    "font-size: 11px; color: #6b7280; border: none; padding: 2px 0 0 2px;"
)
_PREVIEW_ERROR_STYLE = (
    "font-size: 11px; color: #ef4444; border: none; padding: 2px 0 0 2px;"
)


def _expand_path(raw: str) -> str:
    """環境変数を展開してパスを返す。"""
    return os.path.expandvars(raw.strip()) if raw.strip() else ""


def _preview_text(raw: str) -> tuple[str, bool]:
    """プレビュー用テキストと正常かどうかを返す。"""
    raw = raw.strip()
    if not raw:
        return "", True
    if raw.startswith(("http://", "https://")):
        return f"URL: {raw}", True
    expanded = _expand_path(raw)
    if expanded != raw:
        # 環境変数が含まれていた
        if os.path.exists(expanded):
            return f"展開先: {expanded}", True
        return f"展開先: {expanded}  (ファイルが見つかりません)", False
    if os.path.exists(raw):
        return f"パス: {raw}", True
    return f"パス: {raw}  (ファイルが見つかりません)", False


class ToolSettingsTab(QWidget):
    """ツール設定タブ。"""

    def __init__(
        self,
        data_config_service: DataConfigService,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._service = data_config_service
        self._build_ui()

    def _build_ui(self) -> None:
        outer = QVBoxLayout(self)
        outer.setContentsMargins(16, 16, 16, 16)
        outer.setSpacing(12)

        # ── ヘッダー ──────────────────────────────────────────
        header = QHBoxLayout()
        title = QLabel("ツール設定")
        title.setStyleSheet(_TITLE_STYLE)
        header.addWidget(title)
        header.addStretch()
        self._btn_save = QPushButton("保存")
        self._btn_save.setStyleSheet(
            "background: #3b82f6; color: white; border: none; "
            "border-radius: 6px; padding: 8px 24px; font-weight: 600;"
        )
        self._btn_save.clicked.connect(self._on_save)
        header.addWidget(self._btn_save)
        outer.addLayout(header)

        # ── Lab-Aid ───────────────────────────────────────────
        labaid_section = self._make_section(
            "Lab-Aid",
            "Lab-Aid のアプリパスまたは URL を設定します。\n"
            "%APPDATA% などの環境変数が使えます。",
        )
        ll = labaid_section.layout()
        self._input_labaid = QLineEdit(
            self._service.get_tool_path("labaid_path")
        )
        self._input_labaid.setPlaceholderText(
            r"例: %APPDATA%\Microsoft\Windows\Start Menu\Programs\Lab-Aid v5\Lab-Aid v5 Client.appref-ms"
        )
        self._input_labaid.setStyleSheet(_INPUT_STYLE)
        ll.addWidget(self._input_labaid)

        self._preview_labaid = QLabel("")
        self._preview_labaid.setStyleSheet(_PREVIEW_STYLE)
        self._preview_labaid.setWordWrap(True)
        ll.addWidget(self._preview_labaid)
        self._input_labaid.textChanged.connect(
            lambda text: self._update_preview(text, self._preview_labaid)
        )
        self._update_preview(self._input_labaid.text(), self._preview_labaid)
        outer.addWidget(labaid_section)

        # ── 入力ツール ────────────────────────────────────────
        tool_section = self._make_section(
            "入力ツール（Excel）",
            "データを書き込む Excel ファイルのパスと、書き込み先のシート名・開始セルを設定します。\n"
            "%USERPROFILE% などの環境変数が使えます。",
        )
        tl = tool_section.layout()

        lbl_path = QLabel("Excel ファイルパス")
        lbl_path.setStyleSheet(_LABEL_STYLE)
        tl.addWidget(lbl_path)
        self._input_tool = QLineEdit(
            self._service.get_tool_path("input_tool_path")
        )
        self._input_tool.setPlaceholderText(
            r"例: %USERPROFILE%\Documents\入力ツール.xlsx"
        )
        self._input_tool.setStyleSheet(_INPUT_STYLE)
        tl.addWidget(self._input_tool)

        self._preview_tool = QLabel("")
        self._preview_tool.setStyleSheet(_PREVIEW_STYLE)
        self._preview_tool.setWordWrap(True)
        tl.addWidget(self._preview_tool)
        self._input_tool.textChanged.connect(
            lambda text: self._update_preview(text, self._preview_tool)
        )
        self._update_preview(self._input_tool.text(), self._preview_tool)

        row_widget = QWidget()
        row_widget.setStyleSheet("background: transparent;")
        rl = QHBoxLayout(row_widget)
        rl.setContentsMargins(0, 0, 0, 0)
        rl.setSpacing(12)

        lbl_sheet = QLabel("シート名")
        lbl_sheet.setStyleSheet(_LABEL_STYLE)
        lbl_sheet.setFixedWidth(60)
        rl.addWidget(lbl_sheet)
        self._input_sheet = QLineEdit(
            self._service.get_tool_path("input_tool_sheet")
        )
        self._input_sheet.setPlaceholderText("例: Sheet1")
        self._input_sheet.setStyleSheet(_INPUT_STYLE)
        rl.addWidget(self._input_sheet)

        lbl_cell = QLabel("開始セル")
        lbl_cell.setStyleSheet(_LABEL_STYLE)
        lbl_cell.setFixedWidth(60)
        rl.addWidget(lbl_cell)
        self._input_cell = QLineEdit(
            self._service.get_tool_path("input_tool_cell")
        )
        self._input_cell.setPlaceholderText("例: A1")
        self._input_cell.setStyleSheet(_INPUT_STYLE)
        self._input_cell.setFixedWidth(100)
        rl.addWidget(self._input_cell)

        tl.addWidget(row_widget)
        outer.addWidget(tool_section)

        outer.addStretch()

    @staticmethod
    def _make_section(title: str, description: str) -> QFrame:
        section = QFrame()
        section.setObjectName("tool_section")
        section.setStyleSheet(_FRAME_STYLE)
        vl = QVBoxLayout(section)
        vl.setContentsMargins(16, 12, 16, 12)
        vl.setSpacing(8)

        lbl_title = QLabel(title)
        lbl_title.setStyleSheet(
            "font-size: 13px; font-weight: 600; color: #374151; border: none;"
        )
        vl.addWidget(lbl_title)

        lbl_desc = QLabel(description)
        lbl_desc.setStyleSheet(_LABEL_STYLE)
        lbl_desc.setWordWrap(True)
        vl.addWidget(lbl_desc)

        return section

    @staticmethod
    def _update_preview(text: str, label: QLabel) -> None:
        preview, ok = _preview_text(text)
        label.setText(preview)
        label.setStyleSheet(_PREVIEW_STYLE if ok else _PREVIEW_ERROR_STYLE)

    def _on_save(self) -> None:
        self._service.save_tool_path(
            "labaid_path", self._input_labaid.text().strip()
        )
        self._service.save_tool_path(
            "input_tool_path", self._input_tool.text().strip()
        )
        self._service.save_tool_path(
            "input_tool_sheet", self._input_sheet.text().strip()
        )
        self._service.save_tool_path(
            "input_tool_cell", self._input_cell.text().strip()
        )
        QMessageBox.information(self, "保存完了", "ツール設定を保存しました。")
