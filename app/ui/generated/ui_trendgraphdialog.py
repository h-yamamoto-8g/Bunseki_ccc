# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'TrendGraphDialog.ui'
##
## Created by: Qt User Interface Compiler version 6.10.2
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide6.QtCore import (QCoreApplication, QDate, QDateTime, QLocale,
    QMetaObject, QObject, QPoint, QRect,
    QSize, QTime, QUrl, Qt)
from PySide6.QtGui import (QBrush, QColor, QConicalGradient, QCursor,
    QFont, QFontDatabase, QGradient, QIcon,
    QImage, QKeySequence, QLinearGradient, QPainter,
    QPalette, QPixmap, QRadialGradient, QTransform)
from PySide6.QtWidgets import (QApplication, QHBoxLayout, QHeaderView, QLabel,
    QPushButton, QSizePolicy, QSpacerItem, QTableView,
    QVBoxLayout, QWidget)
import app.ui.generated.resources_rc  # noqa: F401

class Ui_TrendGraphDialog(object):
    def setupUi(self, TrendGraphDialog):
        if not TrendGraphDialog.objectName():
            TrendGraphDialog.setObjectName(u"TrendGraphDialog")
        TrendGraphDialog.resize(1298, 833)
        self.verticalLayout = QVBoxLayout(TrendGraphDialog)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.widget_header = QWidget(TrendGraphDialog)
        self.widget_header.setObjectName(u"widget_header")
        self.horizontalLayout_2 = QHBoxLayout(self.widget_header)
        self.horizontalLayout_2.setObjectName(u"horizontalLayout_2")
        self.label_sample_to_holder = QLabel(self.widget_header)
        self.label_sample_to_holder.setObjectName(u"label_sample_to_holder")
        font = QFont()
        font.setFamilies([u"Noto Sans Armenian"])
        font.setPointSize(12)
        self.label_sample_to_holder.setFont(font)

        self.horizontalLayout_2.addWidget(self.label_sample_to_holder)

        self.horizontalSpacer = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_2.addItem(self.horizontalSpacer)

        self.widget = QWidget(self.widget_header)
        self.widget.setObjectName(u"widget")
        self.horizontalLayout = QHBoxLayout(self.widget)
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.btn_csv_save = QPushButton(self.widget)
        self.btn_csv_save.setObjectName(u"btn_csv_save")
        self.btn_csv_save.setMinimumSize(QSize(0, 50))
        font1 = QFont()
        font1.setPointSize(12)
        self.btn_csv_save.setFont(font1)
        icon = QIcon()
        icon.addFile(u":/icons/download.svg", QSize(), QIcon.Mode.Normal, QIcon.State.Off)
        self.btn_csv_save.setIcon(icon)
        self.btn_csv_save.setIconSize(QSize(24, 24))

        self.horizontalLayout.addWidget(self.btn_csv_save)

        self.btn_share = QPushButton(self.widget)
        self.btn_share.setObjectName(u"btn_share")
        self.btn_share.setMinimumSize(QSize(0, 50))
        self.btn_share.setSizeIncrement(QSize(0, 0))
        self.btn_share.setBaseSize(QSize(0, 0))
        self.btn_share.setFont(font1)
        icon1 = QIcon()
        icon1.addFile(u":/icons/send.svg", QSize(), QIcon.Mode.Normal, QIcon.State.Off)
        self.btn_share.setIcon(icon1)
        self.btn_share.setIconSize(QSize(24, 24))

        self.horizontalLayout.addWidget(self.btn_share)


        self.horizontalLayout_2.addWidget(self.widget)


        self.verticalLayout.addWidget(self.widget_header)

        self.widget_graph = QWidget(TrendGraphDialog)
        self.widget_graph.setObjectName(u"widget_graph")
        self.verticalLayout_3 = QVBoxLayout(self.widget_graph)
        self.verticalLayout_3.setObjectName(u"verticalLayout_3")

        self.verticalLayout.addWidget(self.widget_graph)

        self.widget_data = QWidget(TrendGraphDialog)
        self.widget_data.setObjectName(u"widget_data")
        self.verticalLayout_2 = QVBoxLayout(self.widget_data)
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.tableView = QTableView(self.widget_data)
        self.tableView.setObjectName(u"tableView")

        self.verticalLayout_2.addWidget(self.tableView)


        self.verticalLayout.addWidget(self.widget_data)

        self.verticalLayout.setStretch(0, 1)
        self.verticalLayout.setStretch(1, 5)
        self.verticalLayout.setStretch(2, 4)

        self.retranslateUi(TrendGraphDialog)

        QMetaObject.connectSlotsByName(TrendGraphDialog)
    # setupUi

    def retranslateUi(self, TrendGraphDialog):
        TrendGraphDialog.setWindowTitle(QCoreApplication.translate("TrendGraphDialog", u"TrendGraphDialog", None))
        self.label_sample_to_holder.setText("")
        self.btn_csv_save.setText(QCoreApplication.translate("TrendGraphDialog", u"\u4fdd\u5b58", None))
        self.btn_share.setText(QCoreApplication.translate("TrendGraphDialog", u"\u5171\u6709", None))
    # retranslateUi

