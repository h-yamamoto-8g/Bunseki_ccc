# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'LogsPage.ui'
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
from PySide6.QtWidgets import (QApplication, QLabel, QSizePolicy, QWidget)

class Ui_LogsPage(object):
    def setupUi(self, LogsPage):
        if not LogsPage.objectName():
            LogsPage.setObjectName(u"LogsPage")
        LogsPage.resize(400, 300)
        self.label = QLabel(LogsPage)
        self.label.setObjectName(u"label")
        self.label.setGeometry(QRect(178, 126, 41, 20))

        self.retranslateUi(LogsPage)

        QMetaObject.connectSlotsByName(LogsPage)
    # setupUi

    def retranslateUi(self, LogsPage):
        LogsPage.setWindowTitle(QCoreApplication.translate("LogsPage", u"LogsPage", None))
        self.label.setText(QCoreApplication.translate("LogsPage", u"LogsPage", None))
    # retranslateUi

