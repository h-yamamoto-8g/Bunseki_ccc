# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'StateAnalysis.ui'
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
    QScrollArea, QSizePolicy, QSpacerItem, QVBoxLayout,
    QWidget)

class Ui_PageStateAnalysis(object):
    def setupUi(self, PageStateAnalysis):
        if not PageStateAnalysis.objectName():
            PageStateAnalysis.setObjectName(u"PageStateAnalysis")
        PageStateAnalysis.resize(1209, 675)
        self.verticalLayout_6 = QVBoxLayout(PageStateAnalysis)
        self.verticalLayout_6.setObjectName(u"verticalLayout_6")
        self.scrollArea_analysis_support = QScrollArea(PageStateAnalysis)
        self.scrollArea_analysis_support.setObjectName(u"scrollArea_analysis_support")
        self.scrollArea_analysis_support.setWidgetResizable(True)
        self.scrollAreaWidgetContents = QWidget()
        self.scrollAreaWidgetContents.setObjectName(u"scrollAreaWidgetContents")
        self.scrollAreaWidgetContents.setGeometry(QRect(0, 0, 1187, 579))
        self.verticalLayout_5 = QVBoxLayout(self.scrollAreaWidgetContents)
        self.verticalLayout_5.setObjectName(u"verticalLayout_5")
        self.widget = QWidget(self.scrollAreaWidgetContents)
        self.widget.setObjectName(u"widget")
        self.verticalLayout_4 = QVBoxLayout(self.widget)
        self.verticalLayout_4.setObjectName(u"verticalLayout_4")
        self.groupBox_links = QGroupBox(self.widget)
        self.groupBox_links.setObjectName(u"groupBox_links")
        font = QFont()
        font.setPointSize(10)
        self.groupBox_links.setFont(font)
        self.horizontalLayout = QHBoxLayout(self.groupBox_links)
        self.horizontalLayout.setObjectName(u"horizontalLayout")

        self.verticalLayout_4.addWidget(self.groupBox_links)


        self.verticalLayout_5.addWidget(self.widget)

        self.widget_check_lists = QWidget(self.scrollAreaWidgetContents)
        self.widget_check_lists.setObjectName(u"widget_check_lists")
        self.verticalLayout_3 = QVBoxLayout(self.widget_check_lists)
        self.verticalLayout_3.setObjectName(u"verticalLayout_3")
        self.groupBox_before_check_list = QGroupBox(self.widget_check_lists)
        self.groupBox_before_check_list.setObjectName(u"groupBox_before_check_list")
        self.groupBox_before_check_list.setFont(font)
        self.verticalLayout = QVBoxLayout(self.groupBox_before_check_list)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.btn_before_all_checked = QPushButton(self.groupBox_before_check_list)
        self.btn_before_all_checked.setObjectName(u"btn_before_all_checked")
        self.btn_before_all_checked.setMinimumSize(QSize(100, 35))
        self.btn_before_all_checked.setMaximumSize(QSize(100, 50))

        self.verticalLayout.addWidget(self.btn_before_all_checked)

        self.widget_before_check_list = QWidget(self.groupBox_before_check_list)
        self.widget_before_check_list.setObjectName(u"widget_before_check_list")
        self.verticalLayout_7 = QVBoxLayout(self.widget_before_check_list)
        self.verticalLayout_7.setObjectName(u"verticalLayout_7")

        self.verticalLayout.addWidget(self.widget_before_check_list)


        self.verticalLayout_3.addWidget(self.groupBox_before_check_list)

        self.groupBox_after_check_list = QGroupBox(self.widget_check_lists)
        self.groupBox_after_check_list.setObjectName(u"groupBox_after_check_list")
        self.groupBox_after_check_list.setFont(font)
        self.verticalLayout_2 = QVBoxLayout(self.groupBox_after_check_list)
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.btn_after_all_checked = QPushButton(self.groupBox_after_check_list)
        self.btn_after_all_checked.setObjectName(u"btn_after_all_checked")
        self.btn_after_all_checked.setMinimumSize(QSize(100, 35))
        self.btn_after_all_checked.setMaximumSize(QSize(100, 50))

        self.verticalLayout_2.addWidget(self.btn_after_all_checked)

        self.widget_after_check_list = QWidget(self.groupBox_after_check_list)
        self.widget_after_check_list.setObjectName(u"widget_after_check_list")
        self.verticalLayout_8 = QVBoxLayout(self.widget_after_check_list)
        self.verticalLayout_8.setObjectName(u"verticalLayout_8")

        self.verticalLayout_2.addWidget(self.widget_after_check_list)


        self.verticalLayout_3.addWidget(self.groupBox_after_check_list)


        self.verticalLayout_5.addWidget(self.widget_check_lists)

        self.scrollArea_analysis_support.setWidget(self.scrollAreaWidgetContents)

        self.verticalLayout_6.addWidget(self.scrollArea_analysis_support)

        self.widget_action = QWidget(PageStateAnalysis)
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


        self.verticalLayout_6.addWidget(self.widget_action)


        self.retranslateUi(PageStateAnalysis)

        QMetaObject.connectSlotsByName(PageStateAnalysis)
    # setupUi

    def retranslateUi(self, PageStateAnalysis):
        PageStateAnalysis.setWindowTitle(QCoreApplication.translate("PageStateAnalysis", u"PageStateAnalysis", None))
        self.groupBox_links.setTitle(QCoreApplication.translate("PageStateAnalysis", u"\u53c2\u8003\u30ea\u30f3\u30af", None))
        self.groupBox_before_check_list.setTitle(QCoreApplication.translate("PageStateAnalysis", u"\u5206\u6790\u524d\u78ba\u8a8d\u30ea\u30b9\u30c8", None))
        self.btn_before_all_checked.setText(QCoreApplication.translate("PageStateAnalysis", u"\u4e00\u62ec\u30c1\u30a7\u30c3\u30af", None))
        self.groupBox_after_check_list.setTitle(QCoreApplication.translate("PageStateAnalysis", u"\u5206\u6790\u524d\u78ba\u8a8d\u30ea\u30b9\u30c8", None))
        self.btn_after_all_checked.setText(QCoreApplication.translate("PageStateAnalysis", u"\u4e00\u62ec\u30c1\u30a7\u30c3\u30af", None))
        self.btn_back.setText(QCoreApplication.translate("PageStateAnalysis", u"\u623b\u308b", None))
        self.btn_next.setText(QCoreApplication.translate("PageStateAnalysis", u"\u6b21\u3078", None))
    # retranslateUi

