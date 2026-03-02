# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'HomePage.ui'
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
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtWidgets import (QApplication, QHBoxLayout, QHeaderView, QLabel,
    QSizePolicy, QTableView, QVBoxLayout, QWidget)

class Ui_HomePage(object):
    def setupUi(self, HomePage):
        if not HomePage.objectName():
            HomePage.setObjectName(u"HomePage")
        HomePage.resize(1632, 867)
        self.verticalLayout = QVBoxLayout(HomePage)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.widget_top = QWidget(HomePage)
        self.widget_top.setObjectName(u"widget_top")
        self.horizontalLayout = QHBoxLayout(self.widget_top)
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.verticalLayout_3 = QVBoxLayout()
        self.verticalLayout_3.setObjectName(u"verticalLayout_3")
        self.label_mytasks = QLabel(self.widget_top)
        self.label_mytasks.setObjectName(u"label_mytasks")
        self.label_mytasks.setMaximumSize(QSize(16777215, 50))
        font = QFont()
        font.setFamilies([u"\u30e1\u30a4\u30ea\u30aa"])
        font.setPointSize(14)
        self.label_mytasks.setFont(font)

        self.verticalLayout_3.addWidget(self.label_mytasks)

        self.tableView_mytasks = QTableView(self.widget_top)
        self.tableView_mytasks.setObjectName(u"tableView_mytasks")

        self.verticalLayout_3.addWidget(self.tableView_mytasks)


        self.horizontalLayout.addLayout(self.verticalLayout_3)

        self.verticalLayout_4 = QVBoxLayout()
        self.verticalLayout_4.setObjectName(u"verticalLayout_4")
        self.label_news = QLabel(self.widget_top)
        self.label_news.setObjectName(u"label_news")
        self.label_news.setMaximumSize(QSize(16777215, 50))
        self.label_news.setFont(font)

        self.verticalLayout_4.addWidget(self.label_news)

        self.tableView_news = QTableView(self.widget_top)
        self.tableView_news.setObjectName(u"tableView_news")

        self.verticalLayout_4.addWidget(self.tableView_news)


        self.horizontalLayout.addLayout(self.verticalLayout_4)


        self.verticalLayout.addWidget(self.widget_top)

        self.widget_bottom = QWidget(HomePage)
        self.widget_bottom.setObjectName(u"widget_bottom")
        self.verticalLayout_2 = QVBoxLayout(self.widget_bottom)
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.label_calendar = QLabel(self.widget_bottom)
        self.label_calendar.setObjectName(u"label_calendar")
        self.label_calendar.setMaximumSize(QSize(16777215, 50))
        self.label_calendar.setFont(font)

        self.verticalLayout_2.addWidget(self.label_calendar)

        self.webEngineView = QWebEngineView(self.widget_bottom)
        self.webEngineView.setObjectName(u"webEngineView")
        self.webEngineView.setUrl(QUrl(u"about:blank"))

        self.verticalLayout_2.addWidget(self.webEngineView)


        self.verticalLayout.addWidget(self.widget_bottom)

        self.verticalLayout.setStretch(0, 1)
        self.verticalLayout.setStretch(1, 2)

        self.retranslateUi(HomePage)

        QMetaObject.connectSlotsByName(HomePage)
    # setupUi

    def retranslateUi(self, HomePage):
        HomePage.setWindowTitle(QCoreApplication.translate("HomePage", u"HomePage", None))
        self.label_mytasks.setText(QCoreApplication.translate("HomePage", u"\u30de\u30a4\u30bf\u30b9\u30af", None))
        self.label_news.setText(QCoreApplication.translate("HomePage", u"\u30cb\u30e5\u30fc\u30b9", None))
        self.label_calendar.setText(QCoreApplication.translate("HomePage", u"\u30ab\u30ec\u30f3\u30c0\u30fc", None))
    # retranslateUi

