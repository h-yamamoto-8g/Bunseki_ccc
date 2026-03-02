# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'SettingPage.ui'
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
from PySide6.QtWidgets import (QApplication, QSizePolicy, QTabWidget, QVBoxLayout,
    QWidget)

class Ui_SettingPage(object):
    def setupUi(self, SettingPage):
        if not SettingPage.objectName():
            SettingPage.setObjectName(u"SettingPage")
        SettingPage.resize(1381, 809)
        self.verticalLayout = QVBoxLayout(SettingPage)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.verticalLayout.setContentsMargins(0, 0, 0, 0)
        self.tabs = QTabWidget(SettingPage)
        self.tabs.setObjectName(u"tabs")
        self.tab_users = QWidget()
        self.tab_users.setObjectName(u"tab_users")
        self.tabs.addTab(self.tab_users, "")
        self.tab_home = QWidget()
        self.tab_home.setObjectName(u"tab_home")
        self.tabs.addTab(self.tab_home, "")
        self.tab_tasks = QWidget()
        self.tab_tasks.setObjectName(u"tab_tasks")
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.tab_tasks.sizePolicy().hasHeightForWidth())
        self.tab_tasks.setSizePolicy(sizePolicy)
        self.tabs.addTab(self.tab_tasks, "")
        self.tab_news = QWidget()
        self.tab_news.setObjectName(u"tab_news")
        self.tabs.addTab(self.tab_news, "")
        self.tab_data = QWidget()
        self.tab_data.setObjectName(u"tab_data")
        self.tabs.addTab(self.tab_data, "")
        self.tab_library = QWidget()
        self.tab_library.setObjectName(u"tab_library")
        self.tabs.addTab(self.tab_library, "")
        self.tab_logs = QWidget()
        self.tab_logs.setObjectName(u"tab_logs")
        self.tabs.addTab(self.tab_logs, "")
        self.tab_jobs = QWidget()
        self.tab_jobs.setObjectName(u"tab_jobs")
        self.tabs.addTab(self.tab_jobs, "")

        self.verticalLayout.addWidget(self.tabs)


        self.retranslateUi(SettingPage)

        self.tabs.setCurrentIndex(6)


        QMetaObject.connectSlotsByName(SettingPage)
    # setupUi

    def retranslateUi(self, SettingPage):
        SettingPage.setWindowTitle(QCoreApplication.translate("SettingPage", u"SettingPage", None))
        self.tabs.setTabText(self.tabs.indexOf(self.tab_users), QCoreApplication.translate("SettingPage", u"\u30e6\u30fc\u30b6\u30fc", None))
        self.tabs.setTabText(self.tabs.indexOf(self.tab_home), QCoreApplication.translate("SettingPage", u"\u30db\u30fc\u30e0", None))
        self.tabs.setTabText(self.tabs.indexOf(self.tab_tasks), QCoreApplication.translate("SettingPage", u"\u30bf\u30b9\u30af", None))
        self.tabs.setTabText(self.tabs.indexOf(self.tab_news), QCoreApplication.translate("SettingPage", u"\u30cb\u30e5\u30fc\u30b9", None))
        self.tabs.setTabText(self.tabs.indexOf(self.tab_data), QCoreApplication.translate("SettingPage", u"\u30c7\u30fc\u30bf", None))
        self.tabs.setTabText(self.tabs.indexOf(self.tab_library), QCoreApplication.translate("SettingPage", u"\u30e9\u30a4\u30d6\u30e9\u30ea", None))
        self.tabs.setTabText(self.tabs.indexOf(self.tab_logs), QCoreApplication.translate("SettingPage", u"\u30ed\u30b0", None))
        self.tabs.setTabText(self.tabs.indexOf(self.tab_jobs), QCoreApplication.translate("SettingPage", u"\u30b8\u30e7\u30d6", None))
    # retranslateUi

