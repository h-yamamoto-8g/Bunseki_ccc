"""ツール設定タブ — Lab-Aid / 入力ツール のパスを設定する。"""
from __future__ import annotations

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
            "Lab-Aid のパスまたは URL を設定します。",
        )
        self._input_labaid = QLineEdit(
            self._service.get_tool_path("labaid_path")
        )
        self._input_labaid.setPlaceholderText(
            "例: C:\\LabAid\\LabAid.exe  または  http://192.168.x.x/labaid/"
        )
        self._input_labaid.setStyleSheet(_INPUT_STYLE)
        labaid_section.layout().addWidget(self._input_labaid)
        outer.addWidget(labaid_section)

        # ── 入力ツール ────────────────────────────────────────
        tool_section = self._make_section(
            "入力ツール",
            "CSV出力後に起動するツールのパスまたは URL を設定します。\n"
            "空欄の場合はCSVファイルを直接開きます。",
        )
        self._input_tool = QLineEdit(
            self._service.get_tool_path("input_tool_path")
        )
        self._input_tool.setPlaceholderText(
            "例: C:\\Tools\\InputTool.exe  （空欄でCSVを直接開く）"
        )
        self._input_tool.setStyleSheet(_INPUT_STYLE)
        tool_section.layout().addWidget(self._input_tool)
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

    def _on_save(self) -> None:
        self._service.save_tool_path(
            "labaid_path", self._input_labaid.text().strip()
        )
        self._service.save_tool_path(
            "input_tool_path", self._input_tool.text().strip()
        )
        QMessageBox.information(self, "保存完了", "ツール設定を保存しました。")
