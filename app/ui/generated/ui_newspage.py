# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'NewsPage.ui'
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

class Ui_NewsPage(object):
    def setupUi(self, NewsPage):
        if not NewsPage.objectName():
            NewsPage.setObjectName(u"NewsPage")
        NewsPage.resize(400, 300)
        self.label = QLabel(NewsPage)
        self.label.setObjectName(u"label")
        self.label.setGeometry(QRect(170, 120, 49, 16))

        self.retranslateUi(NewsPage)

        QMetaObject.connectSlotsByName(NewsPage)
    # setupUi

    def retranslateUi(self, NewsPage):
        NewsPage.setWindowTitle(QCoreApplication.translate("NewsPage", u"NewsPage", None))
        self.label.setText(QCoreApplication.translate("NewsPage", u"NewsPage", None))
    # retranslateUi

