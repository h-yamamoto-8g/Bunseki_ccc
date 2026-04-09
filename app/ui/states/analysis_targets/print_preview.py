"""PrintPreviewDialog — 分析対象テーブルの印刷プレビューダイアログ。"""
from __future__ import annotations

import html as _html

from PySide6.QtCore import QMarginsF
from PySide6.QtGui import QPageLayout, QPageSize, QTextDocument
from PySide6.QtPrintSupport import QPrinter, QPrintDialog
from PySide6.QtWidgets import (
    QDialog, QHBoxLayout, QPushButton, QTextBrowser, QVBoxLayout, QWidget,
)


class PrintPreviewDialog(QDialog):
    """HTML テーブルのプレビューを表示し、印刷を実行するダイアログ。"""

    def __init__(
        self,
        title: str,
        headers: list[str],
        rows: list[list[str]],
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle("印刷プレビュー")
        self.resize(900, 650)

        self._html = self._build_html(title, headers, rows)

        layout = QVBoxLayout(self)

        browser = QTextBrowser()
        browser.setOpenExternalLinks(False)
        browser.setHtml(self._html)
        layout.addWidget(browser)

        btn_bar = QHBoxLayout()
        btn_bar.addStretch()

        print_btn = QPushButton("印刷")
        print_btn.setFixedHeight(32)
        print_btn.clicked.connect(self._on_print)
        btn_bar.addWidget(print_btn)

        close_btn = QPushButton("閉じる")
        close_btn.setFixedHeight(32)
        close_btn.clicked.connect(self.accept)
        btn_bar.addWidget(close_btn)

        layout.addLayout(btn_bar)

    # ── Internal ──────────────────────────────────────────────────────────────

    @staticmethod
    def _build_html(title: str, headers: list[str], rows: list[list[str]]) -> str:
        style = (
            "body { font-family: 'Yu Gothic UI','Hiragino Sans','Noto Sans JP',sans-serif;"
            " font-size: 11px; color: #333; }"
            "h2 { font-size: 14px; margin-bottom: 8px; }"
            "table { width: 100%; border-collapse: collapse; page-break-inside: auto; }"
            "thead { display: table-header-group; }"
            "tr { page-break-inside: avoid; page-break-after: auto; }"
            "th { background: #f9fafb; color: #6b7280; font-size: 10px; font-weight: bold;"
            " border-bottom: 2px solid #e5e7eb; padding: 6px 8px; text-align: left; }"
            "td { padding: 5px 8px; border-bottom: 1px solid #e5e7eb; font-size: 11px; }"
            "tr:nth-child(even) td { background: #f9fafb; }"
        )

        esc = _html.escape
        th = "".join(f"<th>{esc(h)}</th>" for h in headers)
        trs = "\n".join(
            "<tr>" + "".join(f"<td>{esc(c)}</td>" for c in row) + "</tr>"
            for row in rows
        )

        return (
            f"<!DOCTYPE html><html><head><meta charset='utf-8'>"
            f"<style>{style}</style></head><body>"
            f"<h2>{esc(title)}</h2>"
            f"<table><thead><tr>{th}</tr></thead><tbody>{trs}</tbody></table>"
            f"</body></html>"
        )

    def _on_print(self) -> None:
        from app.core.home_settings_store import get_print_config

        cfg = get_print_config()

        # 用紙サイズ
        size_map = {
            "A4": QPageSize.PageSizeId.A4,
            "A3": QPageSize.PageSizeId.A3,
            "B4": QPageSize.PageSizeId.JisB4,
            "B5": QPageSize.PageSizeId.JisB5,
            "Letter": QPageSize.PageSizeId.Letter,
        }
        page_size = QPageSize(size_map.get(cfg.get("paper_size", "A4"), QPageSize.PageSizeId.A4))

        # 向き
        orientation = (
            QPageLayout.Orientation.Portrait
            if "縦" in cfg.get("orientation", "")
            else QPageLayout.Orientation.Landscape
        )

        # 余白
        margin = float(cfg.get("margin", 10.0))

        printer = QPrinter(QPrinter.PrinterMode.HighResolution)
        printer.setPageLayout(
            QPageLayout(page_size, orientation, QMarginsF(margin, margin, margin, margin))
        )

        dlg = QPrintDialog(printer, self)
        if dlg.exec() == QPrintDialog.DialogCode.Accepted:
            doc = QTextDocument()
            doc.setHtml(self._html)
            page_rect = printer.pageRect(QPrinter.Unit.Point)
            doc.setPageSize(page_rect.size())
            doc.print_(printer)
