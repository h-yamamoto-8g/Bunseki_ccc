# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'StateEntry.ui'
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
from PySide6.QtWidgets import (QApplication, QHBoxLayout, QLabel, QPushButton,
    QSizePolicy, QSpacerItem, QVBoxLayout, QWidget)

class Ui_PageStateEntry(object):
    def setupUi(self, PageStateEntry):
        if not PageStateEntry.objectName():
            PageStateEntry.setObjectName(u"PageStateEntry")
        PageStateEntry.resize(332, 198)
        self.verticalLayout_2 = QVBoxLayout(PageStateEntry)
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.widget = QWidget(PageStateEntry)
        self.widget.setObjectName(u"widget")
        self.verticalLayout = QVBoxLayout(self.widget)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.label = QLabel(self.widget)
        self.label.setObjectName(u"label")
        font = QFont()
        font.setPointSize(12)
        self.label.setFont(font)

        self.verticalLayout.addWidget(self.label)

        self.label_2 = QLabel(self.widget)
        self.label_2.setObjectName(u"label_2")
        self.label_2.setFont(font)

        self.verticalLayout.addWidget(self.label_2)

        self.btn_labaid = QPushButton(self.widget)
        self.btn_labaid.setObjectName(u"btn_labaid")
        self.btn_labaid.setFont(font)

        self.verticalLayout.addWidget(self.btn_labaid)


        self.verticalLayout_2.addWidget(self.widget)

        self.widget_action = QWidget(PageStateEntry)
        self.widget_action.setObjectName(u"widget_action")
        self.horizontalLayout_5 = QHBoxLayout(self.widget_action)
        self.horizontalLayout_5.setObjectName(u"horizontalLayout_5")
        self.horizontalSpacer_3 = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_5.addItem(self.horizontalSpacer_3)

        self.btn_back = QPushButton(self.widget_action)
        self.btn_back.setObjectName(u"btn_back")
        self.btn_back.setMinimumSize(QSize(100, 50))
        self.btn_back.setMaximumSize(QSize(100, 50))

        self.horizontalLayout_5.addWidget(self.btn_back)

        self.btn_next = QPushButton(self.widget_action)
        self.btn_next.setObjectName(u"btn_next")
        self.btn_next.setMinimumSize(QSize(100, 50))
        self.btn_next.setMaximumSize(QSize(100, 50))

        self.horizontalLayout_5.addWidget(self.btn_next)

        self.horizontalSpacer_4 = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_5.addItem(self.horizontalSpacer_4)


        self.verticalLayout_2.addWidget(self.widget_action)


        self.retranslateUi(PageStateEntry)

        QMetaObject.connectSlotsByName(PageStateEntry)
    # setupUi

    def retranslateUi(self, PageStateEntry):
        PageStateEntry.setWindowTitle(QCoreApplication.translate("PageStateEntry", u"PageStateEntry", None))
        self.label.setText(QCoreApplication.translate("PageStateEntry", u"\u5b9f\u88c5\u4e2d\u3067\u3059\u3002", None))
        self.label_2.setText(QCoreApplication.translate("PageStateEntry", u"\u901a\u5e38\u901a\u308a\u3001Lab-Aid\u306b\u30c7\u30fc\u30bf\u3092\u5165\u529b\u3057\u3066\u304f\u3060\u3055\u3044\u3002", None))
        self.btn_labaid.setText(QCoreApplication.translate("PageStateEntry", u"Lab-Aid", None))
        self.btn_back.setText(QCoreApplication.translate("PageStateEntry", u"\u623b\u308b", None))
        self.btn_next.setText(QCoreApplication.translate("PageStateEntry", u"\u6b21\u3078", None))
    # retranslateUi

