# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'JobsPage.ui'
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

class Ui_JobsPage(object):
    def setupUi(self, JobsPage):
        if not JobsPage.objectName():
            JobsPage.setObjectName(u"JobsPage")
        JobsPage.resize(400, 300)
        self.label = QLabel(JobsPage)
        self.label.setObjectName(u"label")
        self.label.setGeometry(QRect(170, 130, 49, 16))

        self.retranslateUi(JobsPage)

        QMetaObject.connectSlotsByName(JobsPage)
    # setupUi

    def retranslateUi(self, JobsPage):
        JobsPage.setWindowTitle(QCoreApplication.translate("JobsPage", u"JobsPage", None))
        self.label.setText(QCoreApplication.translate("JobsPage", u"JobsPage", None))
    # retranslateUi

