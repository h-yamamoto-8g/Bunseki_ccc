"""起動時ローディングダイアログ。

ステータスバーのスピナーを拡大した、テキストなしのオーバーレイ。
_run_data_update() 等のブロッキング処理をバックグラウンドスレッドで実行し、
完了後に自動で閉じる。
"""
from __future__ import annotations

from typing import Callable, Optional

from PySide6.QtCore import Qt, QTimer, QThread, Signal
from PySide6.QtWidgets import QDialog, QVBoxLayout, QLabel, QApplication


_SPINNER_FRAMES = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]
_ACCENT = "#3b82f6"


class _WorkerThread(QThread):
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


class LoadingDialog(QDialog):
    """フレームレスのスピナーダイアログ。

    Usage::

        dlg = LoadingDialog(some_blocking_function)
        dlg.exec()          # 処理完了で自動 accept
        if dlg.error():     # エラーがあれば取得
            print(dlg.error())
    """

    def __init__(
        self,
        fn: Callable[[], None],
        parent: Optional[object] = None,
    ) -> None:
        super().__init__(parent)
        self._fn = fn
        self._error: Optional[str] = None
        self._frame_idx = 0

        # ── ウィンドウ属性 ────────────────────────────────────────────────
        self.setWindowFlags(
            Qt.WindowType.Dialog
            | Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setModal(True)
        self.setFixedSize(160, 160)

        # ── レイアウト ────────────────────────────────────────────────────
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # 背景パネル (角丸白背景 + 影)
        self._panel = QLabel()
        self._panel.setFixedSize(160, 160)
        self._panel.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._panel.setStyleSheet(
            "QLabel {"
            "  background: #ffffff;"
            "  border: 1px solid #e5e7eb;"
            "  border-radius: 16px;"
            f"  color: {_ACCENT};"
            "  font-size: 64px;"
            "  font-weight: bold;"
            "}"
        )
        self._panel.setText(_SPINNER_FRAMES[0])
        root.addWidget(self._panel)

        # ── アニメーションタイマー ────────────────────────────────────────
        self._timer = QTimer(self)
        self._timer.setInterval(80)
        self._timer.timeout.connect(self._tick)

    # ── QDialog overrides ────────────────────────────────────────────────────

    def exec(self) -> int:
        """ダイアログを表示し、バックグラウンドで処理を実行する。"""
        self._timer.start()

        self._worker = _WorkerThread(self._fn, self)
        self._worker.finished.connect(self._on_finished)
        self._worker.error_occurred.connect(self._on_error)
        self._worker.start()

        return super().exec()

    def reject(self) -> None:
        """Esc キー等での閉じを無効化する。"""
        pass

    # ── public API ───────────────────────────────────────────────────────────

    def error(self) -> Optional[str]:
        """処理中に発生したエラーメッセージを返す (なければ None)。"""
        return self._error

    # ── private slots ────────────────────────────────────────────────────────

    def _tick(self) -> None:
        self._frame_idx = (self._frame_idx + 1) % len(_SPINNER_FRAMES)
        self._panel.setText(_SPINNER_FRAMES[self._frame_idx])

    def _on_error(self, msg: str) -> None:
        self._error = msg

    def _on_finished(self) -> None:
        self._timer.stop()
        self.accept()
