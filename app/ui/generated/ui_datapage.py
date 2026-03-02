# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'DataPage.ui'
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

class Ui_DataPage(object):
    def setupUi(self, DataPage):
        if not DataPage.objectName():
            DataPage.setObjectName(u"DataPage")
        DataPage.resize(400, 300)
        self.label = QLabel(DataPage)
        self.label.setObjectName(u"label")
        self.label.setGeometry(QRect(150, 120, 49, 16))

        self.retranslateUi(DataPage)

        QMetaObject.connectSlotsByName(DataPage)
    # setupUi

    def retranslateUi(self, DataPage):
        DataPage.setWindowTitle(QCoreApplication.translate("DataPage", u"DataPage", None))
        self.label.setText(QCoreApplication.translate("DataPage", u"DataPage", None))
    # retranslateUi

