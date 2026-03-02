# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'LibraryPage.ui'
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

class Ui_LibraryPage(object):
    def setupUi(self, LibraryPage):
        if not LibraryPage.objectName():
            LibraryPage.setObjectName(u"LibraryPage")
        LibraryPage.resize(400, 300)
        self.label = QLabel(LibraryPage)
        self.label.setObjectName(u"label")
        self.label.setGeometry(QRect(170, 130, 49, 16))

        self.retranslateUi(LibraryPage)

        QMetaObject.connectSlotsByName(LibraryPage)
    # setupUi

    def retranslateUi(self, LibraryPage):
        LibraryPage.setWindowTitle(QCoreApplication.translate("LibraryPage", u"LibraryPage", None))
        self.label.setText(QCoreApplication.translate("LibraryPage", u"LibraryPage", None))
    # retranslateUi

