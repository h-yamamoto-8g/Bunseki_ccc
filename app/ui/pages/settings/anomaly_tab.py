"""設定 > タスク > 異常検出設定タブ。

異常検出の閾値（σ倍率・最低データ数・トレンド期間）と基準値列の設定を管理する。
分析項目に依存しないグローバル設定。
"""
from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFrame,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QHBoxLayout,
    QLabel,
    QVBoxLayout,
    QWidget,
)

from app.services.hg_config_service import HgConfigService
from app.ui.pages.settings.anomaly_spec_widget import (
    AnomalyConfigWidget,
    SpecColumnsWidget,
)

_BTN_SAVE = (
    "QPushButton { background: #3b82f6; color: white; border: none;"
    " border-radius: 6px; padding: 8px 24px; font-weight: 600; }"
    "QPushButton:hover { background: #2563eb; }"
)
_GLOBAL_HG_CODE = "_global"


class AnomalyTab(QWidget):
    """異常検出設定タブ。"""

    def __init__(
        self,
        hg_config_service: HgConfigService,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._service = hg_config_service
        self._build_ui()
        self._load()

    def _build_ui(self) -> None:
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)

        # ヘッダー
        header = QHBoxLayout()
        header.setContentsMargins(16, 12, 16, 8)
        lbl = QLabel("異常検出設定")
        lbl.setStyleSheet("font-size: 16px; font-weight: 700; color: #1f2937;")
        header.addWidget(lbl)
        header.addStretch()
        self._btn_save = QPushButton("保存")
        self._btn_save.setStyleSheet(_BTN_SAVE)
        self._btn_save.clicked.connect(self._on_save)
        header.addWidget(self._btn_save)
        outer.addLayout(header)

        # スクロール領域
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        content = QWidget()
        cl = QVBoxLayout(content)
        cl.setContentsMargins(16, 8, 16, 16)
        cl.setSpacing(16)

        self._anomaly_config = AnomalyConfigWidget()
        cl.addWidget(self._anomaly_config)

        self._spec_columns = SpecColumnsWidget()
        cl.addWidget(self._spec_columns)

        cl.addStretch()
        scroll.setWidget(content)
        outer.addWidget(scroll, 1)

    def _load(self) -> None:
        self._anomaly_config.set_config(
            self._service.get_anomaly_config(_GLOBAL_HG_CODE),
        )
        self._spec_columns.set_columns(
            self._service.get_spec_columns(_GLOBAL_HG_CODE),
        )

    def _on_save(self) -> None:
        ac = self._anomaly_config.get_config()
        self._service.save_anomaly_config(
            _GLOBAL_HG_CODE, ac["sigma"], ac["min_points"], ac["trend_years"],
        )
        self._service.save_spec_columns(
            _GLOBAL_HG_CODE, self._spec_columns.get_columns(),
        )
        QMessageBox.information(self, "保存完了", "異常検出設定を保存しました。")
