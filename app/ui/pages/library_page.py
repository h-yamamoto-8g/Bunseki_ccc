"""ライブラリページ — タスク回覧時の添付資料をタスク単位でグルーピング表示。"""
from __future__ import annotations

import os
import platform
import subprocess
from pathlib import Path

from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QColor, QFont
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

# ── デザイントークン ──────────────────────────────────────────────────────────
_BG2 = "#ffffff"
_BG3 = "#f9fafb"
_TEXT = "#333333"
_TEXT2 = "#6b7280"
_TEXT3 = "#9ca3af"
_ACCENT = "#3b82f6"
_BORDER = "#e5e7eb"
_GROUP_BG = "#f0f5ff"
_GROUP_COLOR = "#1e40af"

_FRAME_STYLE = (
    "QFrame#lib_section { background: #ffffff; border: 1px solid #e5e7eb; "
    "border-radius: 8px; }"
    "QFrame#lib_section QWidget { background: #ffffff; }"
)
_TITLE_STYLE = "font-size: 14px; font-weight: 700; color: #1f2937; border: none;"

_PAGE_SIZE = 50  # タスク単位のページネーション


def _make_separator() -> QWidget:
    sep = QWidget()
    sep.setFixedHeight(1)
    sep.setStyleSheet("background: #e5e7eb;")
    return sep


class LibraryPage(QWidget):
    """ライブラリページ — 回覧添付資料をタスク単位でグルーピング表示。"""

    def __init__(
        self,
        task_service: TaskService | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._ts = task_service
        self._all_groups: list[dict] = []  # タスク単位のグループ
        self._filtered_groups: list[dict] = []
        self._display_limit: int = _PAGE_SIZE
        self._build_ui()

    # ── UI 構築 ───────────────────────────────────────────────────────────────

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(20, 16, 20, 16)
        root.setSpacing(12)

        root.addWidget(self._build_filter_section())
        root.addWidget(self._build_action_bar())
        root.addWidget(self._build_table(), 1)
        root.addWidget(self._build_pager_bar())

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
        headers = ["", "ファイル名", "添付者", ""]
        self._table.setColumnCount(len(headers))
        self._table.setHorizontalHeaderLabels(headers)
        self._table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self._table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self._table.verticalHeader().setVisible(False)
        self._table.verticalHeader().setDefaultSectionSize(36)
        self._table.setShowGrid(False)

        header = self._table.horizontalHeader()
        header.setDefaultAlignment(
            Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter
        )
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Fixed)
        self._table.setColumnWidth(0, 32)
        self._table.setColumnWidth(3, 44)

        self._table.setStyleSheet(
            f"QTableWidget {{"
            f"  background:{_BG2};"
            f"  border:1px solid {_BORDER}; border-radius:8px;"
            f"  font-size:13px; color:{_TEXT};"
            f"}}"
            f"QTableWidget::item {{ padding:4px 8px; }}"
            f"QTableWidget::item:selected {{ background:#dbeafe; color:#1e293b; }}"
            f"QHeaderView::section {{"
            f"  background:{_BG3}; color:{_TEXT2}; font-size:11px; font-weight:600;"
            f"  padding:8px 12px; border:none; border-bottom:1px solid {_BORDER};"
            f"}}"
        )

        # ダブルクリックでファイルを開く
        self._table.cellDoubleClicked.connect(self._on_cell_double_clicked)

        return self._table

    def _build_pager_bar(self) -> QWidget:
        bar = QWidget()
        hl = QHBoxLayout(bar)
        hl.setContentsMargins(0, 0, 0, 0)
        hl.addStretch()

        self._btn_load_more = QPushButton(f"さらに {_PAGE_SIZE} 件読み込む")
        self._btn_load_more.setVisible(False)
        self._btn_load_more.clicked.connect(self._on_load_more)
        hl.addWidget(self._btn_load_more)

        self._btn_load_all = QPushButton("全件読み込む")
        self._btn_load_all.setVisible(False)
        self._btn_load_all.clicked.connect(self._on_load_all)
        hl.addWidget(self._btn_load_all)

        hl.addStretch()
        return bar

    # ── Public API ────────────────────────────────────────────────────────────

    def refresh(self) -> None:
        self._collect_all()
        self._apply_filter()

    # ── 内部処理 ──────────────────────────────────────────────────────────────

    def _collect_all(self) -> None:
        """全タスクから添付資料をタスク単位で収集する。"""
        self._all_groups.clear()
        if not self._ts:
            return
        for task in self._ts.get_all_tasks():
            sub_data = task.get("state_data", {}).get("submission", {})
            attachments = sub_data.get("attachments", [])
            if not attachments:
                continue

            reviewers = sub_data.get("reviewers", [])
            flow_str = " → ".join(reviewers) if reviewers else ""
            files: list[dict] = []
            for att in attachments:
                if isinstance(att, dict):
                    path = att.get("path", "")
                    added_by = att.get("added_by", "")
                else:
                    path = str(att)
                    added_by = ""
                files.append({
                    "filename": Path(path).name if path else "",
                    "added_by": added_by,
                    "path": path,
                })

            self._all_groups.append({
                "task_name": task.get("task_name", ""),
                "status": task.get("status", ""),
                "created_by": task.get("created_by", ""),
                "flow": flow_str,
                "files": files,
            })

    def _apply_filter(self) -> None:
        task_q = self._edit_task.text().strip().lower()
        file_q = self._edit_file.text().strip().lower()
        user_q = self._edit_user.text().strip().lower()

        filtered: list[dict] = []
        for group in self._all_groups:
            if task_q and task_q not in group["task_name"].lower():
                continue

            if file_q or user_q:
                matched_files = []
                for f in group["files"]:
                    if file_q and file_q not in f["filename"].lower():
                        continue
                    if user_q and user_q not in f["added_by"].lower():
                        continue
                    matched_files.append(f)
                if not matched_files:
                    continue
                filtered.append({**group, "files": matched_files})
            else:
                filtered.append(group)

        self._filtered_groups = filtered
        self._display_limit = _PAGE_SIZE
        self._refresh_table()

    def _refresh_table(self) -> None:
        total_groups = len(self._filtered_groups)
        shown_groups = min(self._display_limit, total_groups)
        groups_to_show = self._filtered_groups[:shown_groups]

        total_files = sum(len(g["files"]) for g in self._filtered_groups)
        shown_files = sum(len(g["files"]) for g in groups_to_show)

        self._label_count.setText(
            f"{shown_groups} タスク ({shown_files} ファイル) / "
            f"全 {total_groups} タスク ({total_files} ファイル)"
        )

        self._populate_table(groups_to_show)

        has_more = shown_groups < total_groups
        self._btn_load_more.setVisible(has_more)
        self._btn_load_all.setVisible(has_more)

    def _populate_table(self, groups: list[dict]) -> None:
        self._table.setRowCount(0)
        self._row_path_map: dict[int, str] = {}  # row_idx → file path

        total_rows = sum(1 + len(g["files"]) for g in groups)
        self._table.setRowCount(total_rows)

        row_idx = 0
        for group in groups:
            # ── グループヘッダー行 ────────────────────────────────
            header_text = (
                f"  ■  {group['task_name']}    [{group['status']}]"
                f"    起票: {group['created_by']}"
            )
            if group["flow"]:
                header_text += f"    回覧: {group['flow']}"

            # 全4列をスパンしたヘッダー行
            self._table.setSpan(row_idx, 0, 1, 4)
            header_item = QTableWidgetItem(header_text)
            header_item.setBackground(QColor(_GROUP_BG))
            header_item.setForeground(QColor(_GROUP_COLOR))
            font = QFont()
            font.setBold(True)
            font.setPointSize(10)
            header_item.setFont(font)
            header_item.setFlags(
                Qt.ItemFlag.ItemIsEnabled  # 選択不可
            )
            self._table.setItem(row_idx, 0, header_item)
            self._table.setRowHeight(row_idx, 40)
            row_idx += 1

            # ── ファイル行 ────────────────────────────────────────
            for file_info in group["files"]:
                # 列0: インデント用空白
                indent = QTableWidgetItem("")
                indent.setFlags(Qt.ItemFlag.ItemIsEnabled)
                self._table.setItem(row_idx, 0, indent)

                # 列1: ファイル名（リンク風ボタン）
                path = file_info["path"]
                file_btn = QPushButton(file_info["filename"])
                file_btn.setCursor(Qt.CursorShape.PointingHandCursor)
                file_btn.setFlat(True)
                file_btn.setStyleSheet(
                    f"QPushButton {{ font-size:13px; color:{_ACCENT};"
                    " text-decoration:underline; border:none;"
                    " background:transparent; text-align:left; padding:4px 8px;"
                    " min-height:0; }}"
                    "QPushButton:hover { color:#1d4ed8; }"
                )
                file_btn.clicked.connect(
                    lambda _=False, p=path: self._open_file(p)
                )
                self._table.setCellWidget(row_idx, 1, file_btn)
                self._row_path_map[row_idx] = path

                # 列2: 添付者
                self._table.setItem(
                    row_idx, 2, QTableWidgetItem(file_info["added_by"])
                )

                # 列3: 開くボタン
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
                btn.clicked.connect(
                    lambda _=False, p=path: self._open_file(p)
                )
                cell_w = QWidget()
                cell_w.setStyleSheet("background:transparent;")
                cell_l = QHBoxLayout(cell_w)
                cell_l.setContentsMargins(4, 4, 4, 4)
                cell_l.setAlignment(Qt.AlignmentFlag.AlignCenter)
                cell_l.addWidget(btn)
                self._table.setCellWidget(row_idx, 3, cell_w)

                row_idx += 1

    # ── イベント ──────────────────────────────────────────────────────────────

    def _on_cell_double_clicked(self, row: int, _col: int) -> None:
        """ファイル行をダブルクリックで開く。"""
        path = self._row_path_map.get(row)
        if path:
            self._open_file(path)

    def _on_search(self) -> None:
        self._collect_all()
        self._apply_filter()
        if not self._all_groups:
            self._label_count.setText("添付資料が登録されたタスクはありません")

    def _on_clear(self) -> None:
        self._edit_task.clear()
        self._edit_file.clear()
        self._edit_user.clear()
        self._table.setRowCount(0)
        self._all_groups.clear()
        self._filtered_groups.clear()
        self._label_count.setText("検索ボタンを押してデータを表示")
        self._btn_load_more.setVisible(False)
        self._btn_load_all.setVisible(False)

    def _on_load_more(self) -> None:
        self._display_limit += _PAGE_SIZE
        self._refresh_table()

    def _on_load_all(self) -> None:
        self._display_limit = len(self._filtered_groups)
        self._refresh_table()

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
