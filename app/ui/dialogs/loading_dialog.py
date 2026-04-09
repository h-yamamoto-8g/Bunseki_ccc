"""ローディングオーバーレイ。

LoadingOverlay: 白半透明背景 + 青い四角ピクセルが四角軌道を回るスピナー。
               メッセージテキスト付き。各ステートの重い処理で共通利用する。
"""
from __future__ import annotations

from typing import Callable, Optional

from PySide6.QtCore import Qt, QTimer, QThread, QRect, Signal
from PySide6.QtGui import QColor, QPainter
from PySide6.QtWidgets import QApplication, QWidget


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# LoadingOverlay — 共通ローディング画面
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


class _OverlayWorker(QThread):
    """ブロッキング処理を別スレッドで実行する。"""

    error_occurred = Signal(str)

    def __init__(self, fn: Callable[[], None], parent=None):
        super().__init__(parent)
        self._fn = fn

    def run(self) -> None:
        try:
            self._fn()
        except Exception as e:
            self.error_occurred.emit(str(e))


class LoadingOverlay(QWidget):
    """白半透明背景 + 青い四角ピクセルが四角く回るスピナーのオーバーレイ。

    Usage::

        # クラスメソッドで簡単に呼び出し
        LoadingOverlay.run_with_overlay(some_blocking_fn, "データを読み込んでいます...")

        # または手動制御
        overlay = LoadingOverlay(msg="処理中...")
        overlay.start()
        ...
        overlay.stop()
    """

    _PIXEL_SIZE = 6
    _SIDE_LEN = 36

    def __init__(self, parent: QWidget | None = None, msg: str = "データを読み込んでいます...") -> None:
        super().__init__(parent)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.resize(400, 220)
        self._angle = 0
        self._timer = QTimer(self)
        self._timer.setInterval(80)
        self._timer.timeout.connect(self._tick)
        self._msg = msg

        # 四角形の辺上にピクセル位置を生成 (時計回り)
        s = self._SIDE_LEN
        steps_per_side = 3
        self._positions: list[tuple[int, int]] = []
        for i in range(steps_per_side):
            self._positions.append((i * s // steps_per_side - s // 2, -s // 2))
        for i in range(steps_per_side):
            self._positions.append((s // 2, i * s // steps_per_side - s // 2))
        for i in range(steps_per_side):
            self._positions.append((s // 2 - i * s // steps_per_side, s // 2))
        for i in range(steps_per_side):
            self._positions.append((-s // 2, s // 2 - i * s // steps_per_side))
        self._dot_count = len(self._positions)

    def start(self) -> None:
        self._center_on_screen()
        self.show()
        self._timer.start()
        QApplication.processEvents()

    def stop(self) -> None:
        self._timer.stop()
        self.close()

    def _center_on_screen(self) -> None:
        screen = QApplication.primaryScreen()
        if screen:
            geo = screen.availableGeometry()
            self.move(
                geo.x() + (geo.width() - self.width()) // 2,
                geo.y() + (geo.height() - self.height()) // 2,
            )

    def _tick(self) -> None:
        self._angle = (self._angle + 1) % self._dot_count
        self.update()
        QApplication.processEvents()

    def paintEvent(self, _event: object) -> None:  # noqa: N802
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)

        p.setBrush(QColor(255, 255, 255, 178))
        p.setPen(Qt.PenStyle.NoPen)
        p.drawRoundedRect(self.rect(), 12, 12)

        cx = self.width() // 2
        cy = self.height() // 2 - 24

        ps = self._PIXEL_SIZE
        for i in range(self._dot_count):
            ox, oy = self._positions[i]
            x = cx + ox - ps // 2
            y = cy + oy - ps // 2

            dist = (i - self._angle) % self._dot_count
            if dist == 0:
                alpha = 255
            elif dist <= 2 or dist >= self._dot_count - 2:
                alpha = 160
            elif dist <= 4 or dist >= self._dot_count - 4:
                alpha = 80
            else:
                alpha = 35

            p.setBrush(QColor(59, 130, 246, alpha))
            p.drawRect(x, y, ps, ps)

        p.setPen(QColor(51, 51, 51))
        text_rect = QRect(0, cy + self._SIDE_LEN // 2 + 28, self.width(), 30)
        p.drawText(text_rect, Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignTop, self._msg)

        p.end()

    @staticmethod
    def run_with_overlay(
        fn: Callable[[], None],
        msg: str = "データを読み込んでいます...",
    ) -> Optional[str]:
        """ブロッキング処理をオーバーレイ表示しながら実行する。

        Args:
            fn: バックグラウンドで実行する関数。
            msg: 表示メッセージ。

        Returns:
            エラーメッセージ (正常終了時は None)。
        """
        overlay = LoadingOverlay(msg=msg)
        overlay.start()

        error: list[str] = []
        done = False

        worker = _OverlayWorker(fn)

        def _on_finished() -> None:
            nonlocal done
            done = True

        def _on_error(err_msg: str) -> None:
            nonlocal done
            error.append(err_msg)
            done = True

        worker.finished.connect(_on_finished)
        worker.error_occurred.connect(_on_error)
        worker.start()

        while not done:
            QApplication.processEvents()
            QThread.msleep(50)

        worker.wait()
        overlay.stop()

        return error[0] if error else None
