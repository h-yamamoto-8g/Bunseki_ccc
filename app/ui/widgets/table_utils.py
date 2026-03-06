"""QTableWidget 共通ユーティリティ: 行番号表示 + ヘッダークリックソート。"""

from __future__ import annotations

from typing import Callable

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QTableWidget


def enable_row_numbers_and_sort(
    table: QTableWidget,
    on_sort: Callable[[int, bool], None],
) -> None:
    """行番号表示とヘッダークリックソートを有効にする。

    Args:
        table: 対象テーブル。
        on_sort: ヘッダークリック時に呼ばれるコールバック (col, ascending)。
    """
    # 行番号 (vertical header) を表示
    vh = table.verticalHeader()
    vh.setVisible(True)

    # ソートインジケータ
    hh = table.horizontalHeader()
    hh.setSortIndicatorShown(True)

    state: dict[str, object] = {"col": -1, "asc": True}

    def _on_click(col: int) -> None:
        if state["col"] == col:
            state["asc"] = not state["asc"]
        else:
            state["col"] = col
            state["asc"] = True
        asc: bool = state["asc"]  # type: ignore[assignment]
        order = Qt.SortOrder.AscendingOrder if asc else Qt.SortOrder.DescendingOrder
        hh.setSortIndicator(col, order)
        on_sort(col, asc)

    hh.sectionClicked.connect(_on_click)
