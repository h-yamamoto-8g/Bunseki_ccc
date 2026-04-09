"""メールテンプレート設定・印刷設定ウィジェット。

HgConfigTab の「フロー」「サンプル」ステータスブロックに埋め込まれる。
"""
from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QComboBox,
    QDoubleSpinBox,
    QFormLayout,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from app.core import home_settings_store

_SECTION_LABEL = "font-weight: 600; font-size: 13px; color: #374151;"
_HINT = "font-size: 11px; color: #9ca3af;"
_FRAME_STYLE = (
    "QFrame#settings_frame { background: #ffffff; border: 1px solid #e5e7eb;"
    " border-radius: 6px; }"
    "QFrame#settings_frame QWidget { background: #ffffff; }"
)
_BTN_SAVE = (
    "QPushButton { background: #3b82f6; color: white; border: none;"
    " padding: 4px 16px; border-radius: 5px; font-size: 12px; font-weight: 600; }"
    "QPushButton:hover { background: #2563eb; }"
)


class MailSettingsWidget(QWidget):
    """メールテンプレート設定ウィジェット。"""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._build_ui()
        self._load()

    def _build_ui(self) -> None:
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(8)

        lbl = QLabel("メールテンプレート設定")
        lbl.setStyleSheet(_SECTION_LABEL)
        outer.addWidget(lbl)

        hint = QLabel("回覧メールの件名プレフィックス・ヘッダー色・フッターを設定します。")
        hint.setStyleSheet(_HINT)
        hint.setWordWrap(True)
        outer.addWidget(hint)

        frame = QFrame()
        frame.setObjectName("settings_frame")
        frame.setStyleSheet(_FRAME_STYLE)
        fl = QVBoxLayout(frame)
        fl.setContentsMargins(16, 12, 16, 12)
        fl.setSpacing(10)

        # 件名プレフィックス
        row1 = QHBoxLayout()
        row1.setSpacing(8)
        lbl1 = QLabel("件名プレフィックス:")
        lbl1.setFixedWidth(130)
        lbl1.setStyleSheet("font-size: 12px; color: #475569;")
        row1.addWidget(lbl1)
        self._edit_prefix = QLineEdit()
        self._edit_prefix.setPlaceholderText("[Bunseki]")
        row1.addWidget(self._edit_prefix, 1)
        fl.addLayout(row1)

        # ヘッダー色
        row2 = QHBoxLayout()
        row2.setSpacing(8)
        lbl2 = QLabel("ヘッダー色:")
        lbl2.setFixedWidth(130)
        lbl2.setStyleSheet("font-size: 12px; color: #475569;")
        row2.addWidget(lbl2)
        self._edit_header_color = QLineEdit()
        self._edit_header_color.setPlaceholderText("#1e3a5f")
        self._edit_header_color.setMaximumWidth(120)
        row2.addWidget(self._edit_header_color)
        row2.addStretch()
        fl.addLayout(row2)

        # 完了ヘッダー色
        row3 = QHBoxLayout()
        row3.setSpacing(8)
        lbl3 = QLabel("完了ヘッダー色:")
        lbl3.setFixedWidth(130)
        lbl3.setStyleSheet("font-size: 12px; color: #475569;")
        row3.addWidget(lbl3)
        self._edit_complete_color = QLineEdit()
        self._edit_complete_color.setPlaceholderText("#166534")
        self._edit_complete_color.setMaximumWidth(120)
        row3.addWidget(self._edit_complete_color)
        row3.addStretch()
        fl.addLayout(row3)

        # フッターテキスト
        row4 = QHBoxLayout()
        row4.setSpacing(8)
        lbl4 = QLabel("フッターテキスト:")
        lbl4.setFixedWidth(130)
        lbl4.setStyleSheet("font-size: 12px; color: #475569;")
        row4.addWidget(lbl4)
        self._edit_footer = QLineEdit()
        self._edit_footer.setPlaceholderText("追加のフッターテキスト（任意）")
        row4.addWidget(self._edit_footer, 1)
        fl.addLayout(row4)

        outer.addWidget(frame)

        # 保存ボタン
        btn_row = QHBoxLayout()
        btn_row.addStretch()
        btn = QPushButton("メール設定を保存")
        btn.setStyleSheet(_BTN_SAVE)
        btn.clicked.connect(self._on_save)
        btn_row.addWidget(btn)
        outer.addLayout(btn_row)

    def _load(self) -> None:
        cfg = home_settings_store.get_mail_config()
        self._edit_prefix.setText(cfg.get("subject_prefix", "[Bunseki]"))
        self._edit_header_color.setText(cfg.get("header_color", "#1e3a5f"))
        self._edit_complete_color.setText(cfg.get("complete_color", "#166534"))
        self._edit_footer.setText(cfg.get("footer_text", ""))

    def _on_save(self) -> None:
        home_settings_store.set_mail_config({
            "subject_prefix": self._edit_prefix.text().strip() or "[Bunseki]",
            "header_color": self._edit_header_color.text().strip() or "#1e3a5f",
            "complete_color": self._edit_complete_color.text().strip() or "#166534",
            "footer_text": self._edit_footer.text().strip(),
        })
        QMessageBox.information(self, "保存完了", "メールテンプレート設定を保存しました。")


class PrintSettingsWidget(QWidget):
    """印刷設定ウィジェット。"""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._build_ui()
        self._load()

    def _build_ui(self) -> None:
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(8)

        lbl = QLabel("印刷設定")
        lbl.setStyleSheet(_SECTION_LABEL)
        outer.addWidget(lbl)

        hint = QLabel("印刷時の用紙サイズ・向き・余白を設定します。")
        hint.setStyleSheet(_HINT)
        outer.addWidget(hint)

        frame = QFrame()
        frame.setObjectName("settings_frame")
        frame.setStyleSheet(_FRAME_STYLE)
        fl = QVBoxLayout(frame)
        fl.setContentsMargins(16, 12, 16, 12)
        fl.setSpacing(10)

        # 用紙サイズ
        row1 = QHBoxLayout()
        row1.setSpacing(8)
        lbl1 = QLabel("用紙サイズ:")
        lbl1.setFixedWidth(80)
        lbl1.setStyleSheet("font-size: 12px; color: #475569;")
        row1.addWidget(lbl1)
        self._combo_paper = QComboBox()
        self._combo_paper.addItems(home_settings_store.PAPER_SIZE_OPTIONS)
        row1.addWidget(self._combo_paper)
        row1.addStretch()
        fl.addLayout(row1)

        # 向き
        row2 = QHBoxLayout()
        row2.setSpacing(8)
        lbl2 = QLabel("向き:")
        lbl2.setFixedWidth(80)
        lbl2.setStyleSheet("font-size: 12px; color: #475569;")
        row2.addWidget(lbl2)
        self._combo_orient = QComboBox()
        self._combo_orient.addItems(home_settings_store.ORIENTATION_OPTIONS)
        row2.addWidget(self._combo_orient)
        row2.addStretch()
        fl.addLayout(row2)

        # 余白
        row3 = QHBoxLayout()
        row3.setSpacing(8)
        lbl3 = QLabel("余白:")
        lbl3.setFixedWidth(80)
        lbl3.setStyleSheet("font-size: 12px; color: #475569;")
        row3.addWidget(lbl3)
        self._spin_margin = QDoubleSpinBox()
        self._spin_margin.setRange(0, 50)
        self._spin_margin.setSingleStep(1)
        self._spin_margin.setDecimals(1)
        self._spin_margin.setSuffix(" mm")
        row3.addWidget(self._spin_margin)
        row3.addStretch()
        fl.addLayout(row3)

        outer.addWidget(frame)

        # 保存ボタン
        btn_row = QHBoxLayout()
        btn_row.addStretch()
        btn = QPushButton("印刷設定を保存")
        btn.setStyleSheet(_BTN_SAVE)
        btn.clicked.connect(self._on_save)
        btn_row.addWidget(btn)
        outer.addLayout(btn_row)

    def _load(self) -> None:
        cfg = home_settings_store.get_print_config()
        idx_p = self._combo_paper.findText(cfg.get("paper_size", "A4"))
        if idx_p >= 0:
            self._combo_paper.setCurrentIndex(idx_p)
        idx_o = self._combo_orient.findText(cfg.get("orientation", "横 (Landscape)"))
        if idx_o >= 0:
            self._combo_orient.setCurrentIndex(idx_o)
        self._spin_margin.setValue(float(cfg.get("margin", 10.0)))

    def _on_save(self) -> None:
        home_settings_store.set_print_config({
            "paper_size": self._combo_paper.currentText(),
            "orientation": self._combo_orient.currentText(),
            "margin": self._spin_margin.value(),
        })
        QMessageBox.information(self, "保存完了", "印刷設定を保存しました。")
