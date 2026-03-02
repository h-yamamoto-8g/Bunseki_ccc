# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'StateResultVerification.ui'
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
from PySide6.QtWidgets import (QApplication, QGroupBox, QHBoxLayout, QPushButton,
    QSizePolicy, QSpacerItem, QTabWidget, QVBoxLayout,
    QWidget)
import app.ui.generated.resources_rc  # noqa: F401

class Ui_StateResultVerification(object):
    def setupUi(self, StateResultVerification):
        if not StateResultVerification.objectName():
            StateResultVerification.setObjectName(u"StateResultVerification")
        StateResultVerification.resize(1355, 801)
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(StateResultVerification.sizePolicy().hasHeightForWidth())
        StateResultVerification.setSizePolicy(sizePolicy)
        self.verticalLayout = QVBoxLayout(StateResultVerification)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.widget_report = QWidget(StateResultVerification)
        self.widget_report.setObjectName(u"widget_report")
        self.verticalLayout_2 = QVBoxLayout(self.widget_report)
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.tabWidget_data = QTabWidget(self.widget_report)
        self.tabWidget_data.setObjectName(u"tabWidget_data")

        self.verticalLayout_2.addWidget(self.tabWidget_data)


        self.verticalLayout.addWidget(self.widget_report)

        self.widget_check_list = QWidget(StateResultVerification)
        self.widget_check_list.setObjectName(u"widget_check_list")
        self.verticalLayout_3 = QVBoxLayout(self.widget_check_list)
        self.verticalLayout_3.setObjectName(u"verticalLayout_3")
        self.groupBox_check_list = QGroupBox(self.widget_check_list)
        self.groupBox_check_list.setObjectName(u"groupBox_check_list")
        self.horizontalLayout = QHBoxLayout(self.groupBox_check_list)
        self.horizontalLayout.setObjectName(u"horizontalLayout")

        self.verticalLayout_3.addWidget(self.groupBox_check_list)


        self.verticalLayout.addWidget(self.widget_check_list)

        self.widget_action = QWidget(StateResultVerification)
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


        self.verticalLayout.addWidget(self.widget_action)


        self.retranslateUi(StateResultVerification)

        self.tabWidget_data.setCurrentIndex(-1)


        QMetaObject.connectSlotsByName(StateResultVerification)
    # setupUi

    def retranslateUi(self, StateResultVerification):
        StateResultVerification.setWindowTitle(QCoreApplication.translate("StateResultVerification", u"StateResultVerification", None))
        self.groupBox_check_list.setTitle(QCoreApplication.translate("StateResultVerification", u"\u78ba\u8a8d\u9805\u76ee", None))
        self.btn_back.setText(QCoreApplication.translate("StateResultVerification", u"\u623b\u308b", None))
        self.btn_next.setText(QCoreApplication.translate("StateResultVerification", u"\u6b21\u3078", None))
    # retranslateUi

