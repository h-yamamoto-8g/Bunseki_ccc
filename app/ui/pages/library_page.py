"""ライブラリページ — タスク回覧時の添付資料をタスク単位でグルーピング表示。"""
from __future__ import annotations

import os
import platform
import subprocess
from datetime import datetime
from pathlib import Path

from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QColor, QFont
from PySide6.QtWidgets import (
    QComboBox,
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
from app.services.data_service import DataService
from app.services.task_service import TaskService
from app.ui.widgets.date_edit import DateEdit
from app.ui.widgets.icon_utils import get_icon

# ── デザイントークン ──────────────────────────────────────────────────────────
_BG2 = "#ffffff"
_BG3 = "#f9fafb"
_TEXT = "#333333"
_TEXT2 = "#6b7280"
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

_PAGE_SIZE = 50


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
        data_service: DataService | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._ts = task_service
        self._ds = data_service
        self._all_groups: list[dict] = []
        self._filtered_groups: list[dict] = []
        self._display_limit: int = _PAGE_SIZE
        self._row_path_map: dict[int, str] = {}
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

        # ── Row 1: シンプルな検索 ─────────────────────────────────
        row1 = QHBoxLayout()
        row1.setSpacing(8)

        lbl_simple = QLabel("キーワード")
        lbl_simple.setFixedWidth(70)
        lbl_simple.setStyleSheet(f"font-size: 12px; color: {_TEXT2};")
        row1.addWidget(lbl_simple)
        self._edit_simple = QLineEdit()
        self._edit_simple.setPlaceholderText("タスク名・ファイル名・添付者を横断検索")
        row1.addWidget(self._edit_simple, 1)

        btn_search = QPushButton("検索")
        btn_search.setStyleSheet(
            f"background: {_ACCENT}; color: white; border: none; "
            "border-radius: 6px; padding: 8px 20px; font-weight: 600;"
        )
        btn_search.clicked.connect(self._on_search)
        row1.addWidget(btn_search)

        btn_clear = QPushButton("クリア")
        btn_clear.clicked.connect(self._on_clear)
        row1.addWidget(btn_clear)

        vl.addLayout(row1)

        # ── Row 2: 期間, 分析項目, ユーザー ──────────────────────
        row2 = QHBoxLayout()
        row2.setSpacing(8)

        lbl_date = QLabel("期間")
        lbl_date.setFixedWidth(70)
        lbl_date.setStyleSheet(f"font-size: 12px; color: {_TEXT2};")
        row2.addWidget(lbl_date)
        self._date_from = DateEdit()
        self._date_from.setFixedWidth(150)
        row2.addWidget(self._date_from)
        lbl_tilde = QLabel("〜")
        lbl_tilde.setStyleSheet(f"color: {_TEXT2};")
        row2.addWidget(lbl_tilde)
        self._date_to = DateEdit()
        self._date_to.setFixedWidth(150)
        row2.addWidget(self._date_to)

        row2.addSpacing(16)

        lbl_hg = QLabel("分析項目")
        lbl_hg.setStyleSheet(f"font-size: 12px; color: {_TEXT2};")
        row2.addWidget(lbl_hg)
        self._combo_hg = QComboBox()
        self._combo_hg.setMinimumWidth(180)
        row2.addWidget(self._combo_hg)

        row2.addSpacing(16)

        lbl_user = QLabel("ユーザー")
        lbl_user.setStyleSheet(f"font-size: 12px; color: {_TEXT2};")
        row2.addWidget(lbl_user)
        self._combo_user = QComboBox()
        self._combo_user.setMinimumWidth(150)
        row2.addWidget(self._combo_user)

        row2.addStretch()
        vl.addLayout(row2)

        # ── Row 3: ファイル名, 拡張子 ────────────────────────────
        row3 = QHBoxLayout()
        row3.setSpacing(8)

        lbl_file = QLabel("ファイル名")
        lbl_file.setFixedWidth(70)
        lbl_file.setStyleSheet(f"font-size: 12px; color: {_TEXT2};")
        row3.addWidget(lbl_file)
        self._edit_file = QLineEdit()
        self._edit_file.setPlaceholderText("部分一致")
        row3.addWidget(self._edit_file, 1)

        row3.addSpacing(16)

        lbl_ext = QLabel("拡張子")
        lbl_ext.setStyleSheet(f"font-size: 12px; color: {_TEXT2};")
        row3.addWidget(lbl_ext)
        self._edit_ext = QLineEdit()
        self._edit_ext.setPlaceholderText("例: xlsx, pdf")
        self._edit_ext.setFixedWidth(150)
        row3.addWidget(self._edit_ext)

        row3.addStretch()
        vl.addLayout(row3)

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
        headers = ["", "ファイル名", "添付者"]
        self._table.setColumnCount(len(headers))
        self._table.setHorizontalHeaderLabels(headers)
        self._table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self._table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self._table.verticalHeader().setVisible(False)
        self._table.verticalHeader().setDefaultSectionSize(40)
        self._table.setShowGrid(False)

        header = self._table.horizontalHeader()
        header.setDefaultAlignment(
            Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter
        )
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)
        self._table.setColumnWidth(0, 44)
        self._table.setColumnWidth(2, 120)

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
        self._load_dropdowns()
        self._collect_all()
        self._apply_filter()

    # ── ドロップダウン ────────────────────────────────────────────────────────

    def _load_dropdowns(self) -> None:
        # 分析項目
        self._combo_hg.blockSignals(True)
        self._combo_hg.clear()
        self._combo_hg.addItem("すべて", "")
        if self._ds:
            try:
                for hg in self._ds.get_holder_groups():
                    self._combo_hg.addItem(
                        hg.get("holder_group_name", ""),
                        hg.get("holder_group_code", ""),
                    )
            except Exception:
                pass
        self._combo_hg.blockSignals(False)

        # ユーザー
        self._combo_user.blockSignals(True)
        self._combo_user.clear()
        self._combo_user.addItem("すべて", "")
        if self._ds:
            try:
                users = self._ds.get_users()
                for u in users:
                    name = u.get("name", "")
                    if name:
                        self._combo_user.addItem(name, name)
            except Exception:
                pass
        self._combo_user.blockSignals(False)

    # ── データ収集 ────────────────────────────────────────────────────────────

    def _collect_all(self) -> None:
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
                filename = Path(path).name if path else ""
                ext = Path(filename).suffix.lstrip(".").lower() if filename else ""
                files.append({
                    "filename": filename,
                    "added_by": added_by,
                    "path": path,
                    "ext": ext,
                })

            self._all_groups.append({
                "task_name": task.get("task_name", ""),
                "status": task.get("status", ""),
                "created_by": task.get("created_by", ""),
                "created_at": task.get("created_at", ""),
                "holder_group_code": task.get("holder_group_code", ""),
                "holder_group_name": task.get("holder_group_name", ""),
                "flow": flow_str,
                "files": files,
            })

    # ── フィルタ ──────────────────────────────────────────────────────────────

    def _apply_filter(self) -> None:
        simple_q = self._edit_simple.text().strip().lower()
        date_from = self._date_from.text().strip()
        date_to = self._date_to.text().strip()
        hg_code = self._combo_hg.currentData() or ""
        user_name = self._combo_user.currentData() or ""
        file_q = self._edit_file.text().strip().lower()
        ext_q = self._edit_ext.text().strip().lower().lstrip(".")

        filtered: list[dict] = []
        for group in self._all_groups:
            # 期間フィルタ（タスク作成日）
            if date_from or date_to:
                created = group.get("created_at", "")[:10]  # YYYY-MM-DD
                if date_from and created < date_from:
                    continue
                if date_to and created > date_to:
                    continue

            # 分析項目フィルタ
            if hg_code and group.get("holder_group_code", "") != hg_code:
                continue

            # ユーザーフィルタ（起票者）
            if user_name and group.get("created_by", "") != user_name:
                continue

            # シンプル検索（タスク名・ファイル名・添付者を横断）
            if simple_q:
                task_match = simple_q in group["task_name"].lower()
                file_match = any(
                    simple_q in f["filename"].lower()
                    or simple_q in f["added_by"].lower()
                    for f in group["files"]
                )
                if not task_match and not file_match:
                    continue

            # ファイル名・拡張子フィルタ（ファイル単位で絞り込み）
            if file_q or ext_q:
                matched_files = []
                for f in group["files"]:
                    if file_q and file_q not in f["filename"].lower():
                        continue
                    if ext_q and f["ext"] != ext_q:
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

    # ── テーブル更新 ──────────────────────────────────────────────────────────

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
        self._row_path_map.clear()

        total_rows = sum(1 + len(g["files"]) for g in groups)
        self._table.setRowCount(total_rows)

        row_idx = 0
        for group in groups:
            # ── グループヘッダー行 ────────────────────────────────
            # 各列にヘッダーウィジェットを配置（スパンなし）
            parts = [group["task_name"]]
            parts.append(f"[{group['status']}]")
            if group["holder_group_name"]:
                parts.append(group["holder_group_name"])
            parts.append(f"起票: {group['created_by']}")
            if group["flow"]:
                parts.append(f"回覧: {group['flow']}")
            parts.append(f"({len(group['files'])} ファイル)")
            header_text = "    ".join(parts)

            for ci in range(3):
                item = QTableWidgetItem(header_text if ci == 0 else "")
                item.setBackground(QColor(_GROUP_BG))
                item.setFlags(Qt.ItemFlag.ItemIsEnabled)
                if ci == 0:
                    item.setForeground(QColor(_GROUP_COLOR))
                    font = QFont()
                    font.setBold(True)
                    item.setFont(font)
                self._table.setItem(row_idx, ci, item)

            self._table.setSpan(row_idx, 0, 1, 3)
            self._table.setRowHeight(row_idx, 44)
            row_idx += 1

            # ── ファイル行 ────────────────────────────────────────
            for file_info in group["files"]:
                path = file_info["path"]

                # 列0: 開くアイコンボタン
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
                cell_l.setContentsMargins(8, 4, 4, 4)
                cell_l.setAlignment(Qt.AlignmentFlag.AlignCenter)
                cell_l.addWidget(btn)
                self._table.setCellWidget(row_idx, 0, cell_w)

                # 列1: ファイル名（ホバーでリンク風）
                file_btn = QPushButton(file_info["filename"])
                file_btn.setCursor(Qt.CursorShape.PointingHandCursor)
                file_btn.setFlat(True)
                file_btn.setStyleSheet(
                    f"QPushButton {{ font-size:13px; color:{_TEXT};"
                    " text-decoration:none; border:none;"
                    " background:transparent; text-align:left; padding:4px 8px;"
                    " min-height:0; }}"
                    f"QPushButton:hover {{ color:{_ACCENT}; text-decoration:underline; }}"
                )
                file_btn.clicked.connect(
                    lambda _=False, p=path: self._open_file(p)
                )
                self._table.setCellWidget(row_idx, 1, file_btn)
                self._row_path_map[row_idx] = path

                # 列2: 添付者
                user_item = QTableWidgetItem(file_info["added_by"])
                user_item.setTextAlignment(
                    Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter
                )
                self._table.setItem(row_idx, 2, user_item)

                row_idx += 1

    # ── イベント ──────────────────────────────────────────────────────────────

    def _on_cell_double_clicked(self, row: int, _col: int) -> None:
        path = self._row_path_map.get(row)
        if path:
            self._open_file(path)

    def _on_search(self) -> None:
        self._collect_all()
        self._apply_filter()
        if not self._all_groups:
            self._label_count.setText("添付資料が登録されたタスクはありません")

    def _on_clear(self) -> None:
        self._edit_simple.clear()
        self._date_from.clear()
        self._date_to.clear()
        self._combo_hg.setCurrentIndex(0)
        self._combo_user.setCurrentIndex(0)
        self._edit_file.clear()
        self._edit_ext.clear()
        self._table.setRowCount(0)
        self._all_groups.clear()
        self._filtered_groups.clear()
        self._row_path_map.clear()
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
