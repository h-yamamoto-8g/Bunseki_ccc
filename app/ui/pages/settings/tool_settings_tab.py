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
            "入力ツール（Excel）",
            "データを書き込む Excel ファイルのパスと、書き込み先のシート名・開始セルを設定します。",
        )
        tl = tool_section.layout()

        lbl_path = QLabel("Excel ファイルパス")
        lbl_path.setStyleSheet(_LABEL_STYLE)
        tl.addWidget(lbl_path)
        self._input_tool = QLineEdit(
            self._service.get_tool_path("input_tool_path")
        )
        self._input_tool.setPlaceholderText(
            r"例: C:\Tools\入力ツール.xlsx"
        )
        self._input_tool.setStyleSheet(_INPUT_STYLE)
        tl.addWidget(self._input_tool)

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
