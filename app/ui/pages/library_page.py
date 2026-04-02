"""ライブラリページ — タスク回覧時の添付資料を一覧表示。"""
from __future__ import annotations

import os
import platform
import subprocess
from pathlib import Path

from PySide6.QtCore import Qt, QSize
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

import app.config as _cfg
from app.services.task_service import TaskService
from app.ui.widgets.icon_utils import get_icon
from app.ui.widgets.table_utils import enable_row_numbers_and_sort

# ── デザイントークン ──────────────────────────────────────────────────────────
_BG2 = "#ffffff"
_BG3 = "#f9fafb"
_TEXT = "#333333"
_TEXT2 = "#6b7280"
_TEXT3 = "#9ca3af"
_ACCENT = "#3b82f6"
_BORDER = "#e5e7eb"
_FRAME_STYLE = (
    "QFrame#lib_section { background: #ffffff; border: 1px solid #e5e7eb; "
    "border-radius: 8px; }"
    "QFrame#lib_section QWidget { background: #ffffff; }"
)
_TITLE_STYLE = "font-size: 14px; font-weight: 700; color: #1f2937; border: none;"


def _make_separator() -> QWidget:
    sep = QWidget()
    sep.setFixedHeight(1)
    sep.setStyleSheet("background: #e5e7eb;")
    return sep


class LibraryPage(QWidget):
    """ライブラリページ — 回覧添付資料の一覧・検索・閲覧。"""

    def __init__(
        self,
        task_service: TaskService | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._ts = task_service
        self._all_items: list[dict] = []
        self._build_ui()

    # ── UI 構築 ───────────────────────────────────────────────────────────────

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(20, 16, 20, 16)
        root.setSpacing(12)

        root.addWidget(self._build_filter_section())
        root.addWidget(self._build_action_bar())
        root.addWidget(self._build_table(), 1)

    def _build_filter_section(self) -> QFrame:
        frame = QFrame()
        frame.setObjectName("lib_section")
        frame.setStyleSheet(_FRAME_STYLE)
        vl = QVBoxLayout(frame)
        vl.setContentsMargins(16, 12, 16, 12)
        vl.setSpacing(8)

        title = QLabel("検索")
        title.setStyleSheet(_TITLE_STYLE)
        vl.addWidget(title)
        vl.addWidget(_make_separator())

        row = QHBoxLayout()
        row.setSpacing(12)

        lbl_task = QLabel("タスク名")
        lbl_task.setStyleSheet(f"font-size: 12px; color: {_TEXT2};")
        row.addWidget(lbl_task)
        self._edit_task = QLineEdit()
        self._edit_task.setPlaceholderText("部分一致")
        row.addWidget(self._edit_task, 1)

        lbl_file = QLabel("ファイル名")
        lbl_file.setStyleSheet(f"font-size: 12px; color: {_TEXT2};")
        row.addWidget(lbl_file)
        self._edit_file = QLineEdit()
        self._edit_file.setPlaceholderText("部分一致")
        row.addWidget(self._edit_file, 1)

        lbl_user = QLabel("添付者")
        lbl_user.setStyleSheet(f"font-size: 12px; color: {_TEXT2};")
        row.addWidget(lbl_user)
        self._edit_user = QLineEdit()
        self._edit_user.setPlaceholderText("部分一致")
        row.addWidget(self._edit_user, 1)

        btn_search = QPushButton("検索")
        btn_search.setStyleSheet(
            f"background: {_ACCENT}; color: white; border: none; "
            "border-radius: 6px; padding: 8px 20px; font-weight: 600;"
        )
        btn_search.clicked.connect(self._on_search)
        row.addWidget(btn_search)

        btn_clear = QPushButton("クリア")
        btn_clear.clicked.connect(self._on_clear)
        row.addWidget(btn_clear)

        vl.addLayout(row)
        return frame

    def _build_action_bar(self) -> QWidget:
        bar = QWidget()
        hl = QHBoxLayout(bar)
        hl.setContentsMargins(0, 0, 0, 0)

        self._label_count = QLabel("検索ボタンを押してデータを表示")
        self._label_count.setStyleSheet(f"font-size: 12px; color: {_TEXT2};")
        hl.addWidget(self._label_count)
        hl.addStretch()
        return bar

    def _build_table(self) -> QTableWidget:
        self._table = QTableWidget()
        headers = ["タスク名", "ファイル名", "添付者", "タスク状態", ""]
        self._table.setColumnCount(len(headers))
        self._table.setHorizontalHeaderLabels(headers)
        self._table.setAlternatingRowColors(True)
        self._table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self._table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self._table.verticalHeader().setDefaultSectionSize(40)
        enable_row_numbers_and_sort(self._table, self._on_sort)

        header = self._table.horizontalHeader()
        header.setDefaultAlignment(
            Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter
        )
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.Fixed)
        self._table.setColumnWidth(4, 44)

        self._table.setStyleSheet(
            f"QTableWidget {{"
            f"  background:{_BG2}; alternate-background-color:{_BG3};"
            f"  border:1px solid {_BORDER}; border-radius:8px;"
            f"  gridline-color:{_BORDER}; font-size:13px; color:{_TEXT};"
            f"}}"
            f"QTableWidget::item {{ padding:4px 8px; }}"
            f"QTableWidget::item:selected {{ background:#dbeafe; color:#1e293b; }}"
            f"QHeaderView::section {{"
            f"  background:{_BG3}; color:{_TEXT2}; font-size:11px; font-weight:600;"
            f"  padding:8px 12px; border:none; border-bottom:1px solid {_BORDER};"
            f"}}"
        )
        return self._table

    # ── Public API ────────────────────────────────────────────────────────────

    def refresh(self) -> None:
        """ページ表示時に全添付資料を収集して表示する。"""
        self._collect_all()
        self._apply_filter()

    # ── 内部処理 ──────────────────────────────────────────────────────────────

    def _collect_all(self) -> None:
        """全タスクから添付資料を収集する。"""
        self._all_items.clear()
        if not self._ts:
            return
        for task in self._ts.get_all_tasks():
            task_name = task.get("task_name", "")
            status = task.get("status", "")
            sub_data = task.get("state_data", {}).get("submission", {})
            attachments = sub_data.get("attachments", [])
            for att in attachments:
                if isinstance(att, dict):
                    path = att.get("path", "")
                    added_by = att.get("added_by", "")
                else:
                    path = str(att)
                    added_by = ""
                filename = Path(path).name if path else ""
                self._all_items.append({
                    "task_name": task_name,
                    "filename": filename,
                    "added_by": added_by,
                    "status": status,
                    "path": path,
                })

    def _apply_filter(self) -> None:
        """フィルタ条件を適用してテーブルを更新する。"""
        task_q = self._edit_task.text().strip().lower()
        file_q = self._edit_file.text().strip().lower()
        user_q = self._edit_user.text().strip().lower()

        filtered = []
        for item in self._all_items:
            if task_q and task_q not in item["task_name"].lower():
                continue
            if file_q and file_q not in item["filename"].lower():
                continue
            if user_q and user_q not in item["added_by"].lower():
                continue
            filtered.append(item)

        self._populate_table(filtered)
        self._label_count.setText(
            f"{len(filtered)} 件表示 / 全 {len(self._all_items)} 件"
        )

    def _populate_table(self, items: list[dict]) -> None:
        self._table.setRowCount(len(items))
        for row_idx, item in enumerate(items):
            self._table.setItem(
                row_idx, 0, QTableWidgetItem(item["task_name"])
            )
            self._table.setItem(
                row_idx, 1, QTableWidgetItem(item["filename"])
            )
            self._table.setItem(
                row_idx, 2, QTableWidgetItem(item["added_by"])
            )
            self._table.setItem(
                row_idx, 3, QTableWidgetItem(item["status"])
            )

            # 開くボタン
            btn = QPushButton()
            btn.setIcon(get_icon(":/icons/link.svg", _ACCENT, 14))
            btn.setIconSize(QSize(14, 14))
            btn.setFixedSize(28, 28)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setToolTip("ファイルを開く")
            btn.setStyleSheet(
                "QPushButton { background:#eff6ff; border:1px solid #bfdbfe;"
                " border-radius:4px; padding:0; min-height:0; min-width:0; }"
                "QPushButton:hover { background:#dbeafe; border-color:#4a8cff; }"
            )
            path = item["path"]
            btn.clicked.connect(
                lambda _=False, p=path: self._open_file(p)
            )
            cell_w = QWidget()
            cell_w.setStyleSheet("background:transparent;")
            cell_l = QHBoxLayout(cell_w)
            cell_l.setContentsMargins(4, 4, 4, 4)
            cell_l.setAlignment(Qt.AlignmentFlag.AlignCenter)
            cell_l.addWidget(btn)
            self._table.setCellWidget(row_idx, 4, cell_w)

    def _on_search(self) -> None:
        self._collect_all()
        self._apply_filter()
        if not self._all_items:
            self._label_count.setText("添付資料が登録されたタスクはありません")

    def _on_clear(self) -> None:
        self._edit_task.clear()
        self._edit_file.clear()
        self._edit_user.clear()
        self._table.setRowCount(0)
        self._all_items.clear()
        self._label_count.setText("検索ボタンを押してデータを表示")

    def _on_sort(self, col: int, ascending: bool) -> None:
        keys = ["task_name", "filename", "added_by", "status"]
        if 0 <= col < len(keys):
            key = keys[col]
            self._all_items.sort(
                key=lambda x: x.get(key, "").lower(),
                reverse=not ascending,
            )
            self._apply_filter()

    @staticmethod
    def _open_file(rel_path: str) -> None:
        """添付ファイルをOSのデフォルトアプリで開く。"""
        p = Path(rel_path)
        if not p.is_absolute():
            p = _cfg.DATA_PATH / p
        if not p.exists():
            from PySide6.QtWidgets import QMessageBox
            QMessageBox.warning(None, "ファイルが見つかりません", str(p))
            return
        try:
            if platform.system() == "Windows":
                os.startfile(str(p))
            elif platform.system() == "Darwin":
                subprocess.run(["open", str(p)], check=False)
            else:
                subprocess.run(["xdg-open", str(p)], check=False)
        except Exception as e:
            from PySide6.QtWidgets import QMessageBox
            QMessageBox.warning(None, "ファイルを開けません", str(e))
