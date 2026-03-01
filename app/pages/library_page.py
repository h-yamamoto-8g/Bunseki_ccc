"""ライブラリページ — 回覧時の添付資料を一覧で管理・閲覧"""
import os
import shutil
from pathlib import Path
from datetime import datetime

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QTableWidget, QTableWidgetItem, QHeaderView,
    QAbstractItemView, QComboBox, QLineEdit, QFileDialog,
    QMessageBox, QScrollArea, QDateEdit,
)
from PySide6.QtCore import Qt, QDate
from PySide6.QtGui import QColor, QFont

from app.config import DATA_PATH
from app.data import task_store

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

_ATTACHMENTS_PATH = DATA_PATH / "bunseki" / "attachments"

_TABLE_SS = f"""
    QTableWidget {{ background:{_BG2}; color:{_TEXT}; border:1px solid {_BORDER};
                   border-radius:8px; gridline-color:{_BORDER}; }}
    QTableWidget::item {{ color:{_TEXT}; border:none; padding:2px 8px; }}
    QTableWidget::item:alternate {{ background:{_BG3}; }}
    QTableWidget::item:selected {{ background:{_ACCENT}; color:white; }}
    QHeaderView::section {{ background:{_BG2}; color:{_TEXT3}; border:none;
        border-bottom:1px solid {_BORDER}; padding:8px 12px;
        font-size:11px; font-weight:bold; }}
"""


class LibraryPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._all_files: list[dict] = []
        self._setup_ui()
        self._load()

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
        title_lbl = QLabel("ライブラリ")
        title_lbl.setStyleSheet(f"font-size:13px; font-weight:600; color:{_TEXT2};")
        tl.addWidget(title_lbl)
        tl.addStretch()

        bulk_btn = QPushButton("↓ 一括ダウンロード")
        bulk_btn.setStyleSheet(f"""
            QPushButton {{ background:{_BG3}; color:{_TEXT}; border:1px solid {_BORDER};
                          padding:5px 12px; border-radius:6px; font-size:12px; }}
            QPushButton:hover {{ border-color:{_ACCENT}; color:{_ACCENT}; }}
        """)
        bulk_btn.clicked.connect(self._bulk_download)
        tl.addWidget(bulk_btn)
        root.addWidget(topbar)

        # Body
        body = QWidget()
        bl = QVBoxLayout(body)
        bl.setContentsMargins(20, 20, 20, 20)
        bl.setSpacing(12)
        root.addWidget(body)

        h1 = QLabel("ライブラリ")
        h1.setStyleSheet(f"font-size:20px; font-weight:700; color:{_TEXT};")
        bl.addWidget(h1)
        sub = QLabel("回覧時に添付された資料の一覧")
        sub.setStyleSheet(f"font-size:12px; color:{_TEXT3};")
        bl.addWidget(sub)

        # Filters
        fcard = QFrame()
        fcard.setStyleSheet(f"QFrame {{ background:{_BG2}; border:1px solid {_BORDER}; border-radius:8px; }}")
        fl = QHBoxLayout(fcard)
        fl.setContentsMargins(16, 12, 16, 12)
        fl.setSpacing(16)

        def _col(label_text, widget):
            c = QVBoxLayout()
            c.setSpacing(3)
            lbl = QLabel(label_text)
            lbl.setStyleSheet(f"font-size:10px; color:{_TEXT3};")
            c.addWidget(lbl)
            c.addWidget(widget)
            return c

        self.hg_combo = QComboBox()
        self.hg_combo.setFixedWidth(160)
        self.hg_combo.addItem("全て")

        self.date_from = QDateEdit()
        self.date_from.setCalendarPopup(True)
        self.date_from.setDisplayFormat("yyyy-MM-dd")
        self.date_from.setSpecialValueText("指定なし")
        self.date_from.setDate(QDate(2020, 1, 1))
        self.date_from.setFixedWidth(120)

        self.date_to = QDateEdit()
        self.date_to.setCalendarPopup(True)
        self.date_to.setDisplayFormat("yyyy-MM-dd")
        self.date_to.setDate(QDate.currentDate())
        self.date_to.setFixedWidth(120)

        self.user_input = QLineEdit()
        self.user_input.setPlaceholderText("ユーザー名で絞り込み...")
        self.user_input.setFixedWidth(150)

        fl.addLayout(_col("ホルダグループ", self.hg_combo))
        fl.addLayout(_col("期間（開始）", self.date_from))
        fl.addLayout(_col("期間（終了）", self.date_to))
        fl.addLayout(_col("ユーザー", self.user_input))
        fl.addStretch()

        filter_btn = QPushButton("絞り込む")
        filter_btn.setStyleSheet(f"""
            QPushButton {{ background:{_ACCENT}; color:white; border:none;
                          padding:6px 14px; border-radius:6px; font-size:12px; }}
            QPushButton:hover {{ background:#5a9dff; }}
        """)
        filter_btn.clicked.connect(self._apply_filter)
        fl.addWidget(filter_btn, alignment=Qt.AlignmentFlag.AlignBottom)
        bl.addWidget(fcard)

        self.count_lbl = QLabel("")
        self.count_lbl.setStyleSheet(f"font-size:11px; color:{_TEXT3};")
        bl.addWidget(self.count_lbl)

        # Table
        headers = ["タスクID", "ホルダグループ", "ファイル名", "サイズ", "更新日時", "担当者", "アクション"]
        self.table = QTableWidget(0, len(headers))
        self.table.setHorizontalHeaderLabels(headers)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setAlternatingRowColors(True)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        self.table.setStyleSheet(_TABLE_SS)
        self.table.verticalHeader().setVisible(False)
        bl.addWidget(self.table)
        bl.addStretch()

    def _load(self):
        """attachments/ フォルダをスキャンして tasks.json とマージ"""
        tasks = {t["task_id"]: t for t in task_store.load_tasks()}
        files = []
        if _ATTACHMENTS_PATH.exists():
            for task_dir in sorted(_ATTACHMENTS_PATH.iterdir()):
                if not task_dir.is_dir():
                    continue
                task_id = task_dir.name
                task = tasks.get(task_id, {})
                hg_name = task.get("holder_group_name", task_id)
                assigned = task.get("assigned_to", "")
                updated = task.get("updated_at", "")[:10] if task.get("updated_at") else ""
                for f in task_dir.iterdir():
                    if f.is_file():
                        size_kb = f.stat().st_size / 1024
                        size_str = f"{size_kb:.1f} KB" if size_kb < 1024 else f"{size_kb/1024:.1f} MB"
                        mtime = datetime.fromtimestamp(f.stat().st_mtime).strftime("%Y-%m-%d %H:%M")
                        files.append({
                            "task_id": task_id,
                            "hg_name": hg_name,
                            "filename": f.name,
                            "path": f,
                            "size": size_str,
                            "mtime": mtime,
                            "user": assigned,
                            "date": updated,
                        })

        self._all_files = files

        # populate holder group filter
        hg_names = sorted({f["hg_name"] for f in files})
        self.hg_combo.clear()
        self.hg_combo.addItem("全て")
        self.hg_combo.addItems(hg_names)

        self._apply_filter()

    def _apply_filter(self):
        hg = self.hg_combo.currentText()
        date_from = self.date_from.date().toString("yyyy-MM-dd")
        date_to = self.date_to.date().toString("yyyy-MM-dd")
        user = self.user_input.text().strip().lower()

        filtered = self._all_files
        if hg != "全て":
            filtered = [f for f in filtered if f["hg_name"] == hg]
        if date_from and date_from != "2020-01-01":
            filtered = [f for f in filtered if f["date"] >= date_from]
        if date_to:
            filtered = [f for f in filtered if not f["date"] or f["date"] <= date_to]
        if user:
            filtered = [f for f in filtered if user in f["user"].lower()]

        self.table.setRowCount(0)
        for f in filtered:
            r = self.table.rowCount()
            self.table.insertRow(r)
            vals = [f["task_id"], f["hg_name"], f["filename"], f["size"], f["mtime"], f["user"]]
            for col, v in enumerate(vals):
                self.table.setItem(r, col, QTableWidgetItem(str(v)))

            # Action button
            action_w = QWidget()
            action_l = QHBoxLayout(action_w)
            action_l.setContentsMargins(4, 2, 4, 2)
            action_l.setSpacing(4)

            open_btn = QPushButton("開く")
            open_btn.setStyleSheet(f"""
                QPushButton {{ background:{_BG3}; color:{_ACCENT}; border:1px solid {_BORDER};
                              padding:2px 8px; border-radius:4px; font-size:11px; }}
                QPushButton:hover {{ border-color:{_ACCENT}; }}
            """)
            open_btn.clicked.connect(lambda _=False, p=f["path"]: self._open_file(p))
            action_l.addWidget(open_btn)

            dl_btn = QPushButton("DL")
            dl_btn.setStyleSheet(f"""
                QPushButton {{ background:{_BG3}; color:{_TEXT2}; border:1px solid {_BORDER};
                              padding:2px 8px; border-radius:4px; font-size:11px; }}
                QPushButton:hover {{ border-color:{_ACCENT}; color:{_ACCENT}; }}
            """)
            dl_btn.clicked.connect(lambda _=False, p=f["path"], n=f["filename"]: self._download_file(p, n))
            action_l.addWidget(dl_btn)

            self.table.setCellWidget(r, 6, action_w)

        self.count_lbl.setText(f"{len(filtered)} 件")

        if not filtered and not self._all_files:
            self.count_lbl.setText("添付ファイルはまだありません。回覧時にファイルを添付すると、ここに表示されます。")

    def _open_file(self, path: Path):
        try:
            import subprocess, sys
            if sys.platform == "darwin":
                subprocess.run(["open", str(path)], check=False)
            elif sys.platform == "win32":
                os.startfile(str(path))
            else:
                subprocess.run(["xdg-open", str(path)], check=False)
        except Exception as e:
            QMessageBox.warning(self, "エラー", f"ファイルを開けませんでした:\n{e}")

    def _download_file(self, path: Path, filename: str):
        dest, _ = QFileDialog.getSaveFileName(self, "保存先を選択", filename)
        if dest:
            try:
                shutil.copy2(str(path), dest)
                QMessageBox.information(self, "完了", f"保存しました:\n{dest}")
            except Exception as e:
                QMessageBox.warning(self, "エラー", f"ダウンロードに失敗しました:\n{e}")

    def _bulk_download(self):
        rows = self.table.selectedItems()
        if not rows:
            QMessageBox.information(self, "情報", "ダウンロードする行を選択してください。")
            return
        dest_dir = QFileDialog.getExistingDirectory(self, "保存先フォルダを選択")
        if not dest_dir:
            return
        dest_path = Path(dest_dir)
        selected_rows = sorted({self.table.row(item) for item in rows})
        count = 0
        for r in selected_rows:
            task_id = self.table.item(r, 0).text()
            filename = self.table.item(r, 2).text()
            src = _ATTACHMENTS_PATH / task_id / filename
            if src.exists():
                shutil.copy2(str(src), str(dest_path / filename))
                count += 1
        QMessageBox.information(self, "完了", f"{count} ファイルをダウンロードしました:\n{dest_dir}")
