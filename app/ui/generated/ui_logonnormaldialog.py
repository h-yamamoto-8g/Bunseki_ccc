# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'LogonNormalDialog.ui'
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
from PySide6.QtWidgets import (QApplication, QDialog, QHBoxLayout, QLabel,
    QLineEdit, QPushButton, QSizePolicy, QSpacerItem,
    QVBoxLayout, QWidget)

class Ui_LogonNormalDialog(object):
    def setupUi(self, LogonNormalDialog):
        if not LogonNormalDialog.objectName():
            LogonNormalDialog.setObjectName(u"LogonNormalDialog")
        LogonNormalDialog.setWindowModality(Qt.WindowModality.NonModal)
        LogonNormalDialog.resize(294, 144)
        self.verticalLayout = QVBoxLayout(LogonNormalDialog)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.widget_message = QWidget(LogonNormalDialog)
        self.widget_message.setObjectName(u"widget_message")
        self.verticalLayout_2 = QVBoxLayout(self.widget_message)
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.verticalLayout_2.setContentsMargins(0, 0, 0, 0)
        self.label_message = QLabel(self.widget_message)
        self.label_message.setObjectName(u"label_message")
        font = QFont()
        font.setPointSize(10)
        self.label_message.setFont(font)

        self.verticalLayout_2.addWidget(self.label_message)


        self.verticalLayout.addWidget(self.widget_message)

        self.widget_input = QWidget(LogonNormalDialog)
        self.widget_input.setObjectName(u"widget_input")
        font1 = QFont()
        font1.setPointSize(12)
        self.widget_input.setFont(font1)
        self.verticalLayout_3 = QVBoxLayout(self.widget_input)
        self.verticalLayout_3.setObjectName(u"verticalLayout_3")
        self.verticalLayout_3.setContentsMargins(0, 0, 0, 0)
        self.horizontalLayout_user_id = QHBoxLayout()
        self.horizontalLayout_user_id.setObjectName(u"horizontalLayout_user_id")
        self.lbl_user_id = QLabel(self.widget_input)
        self.lbl_user_id.setObjectName(u"lbl_user_id")
        self.lbl_user_id.setFont(font)
        self.lbl_user_id.setAlignment(Qt.AlignmentFlag.AlignLeading|Qt.AlignmentFlag.AlignLeft|Qt.AlignmentFlag.AlignVCenter)

        self.horizontalLayout_user_id.addWidget(self.lbl_user_id)

        self.input_id = QLineEdit(self.widget_input)
        self.input_id.setObjectName(u"input_id")
        self.input_id.setEnabled(True)
        self.input_id.setMinimumSize(QSize(220, 0))
        self.input_id.setMaximumSize(QSize(200, 16777215))
        self.input_id.setFont(font1)
        self.input_id.setEchoMode(QLineEdit.EchoMode.Normal)

        self.horizontalLayout_user_id.addWidget(self.input_id)


        self.verticalLayout_3.addLayout(self.horizontalLayout_user_id)

        self.horizontalLayout_password = QHBoxLayout()
        self.horizontalLayout_password.setObjectName(u"horizontalLayout_password")
        self.lbl_password = QLabel(self.widget_input)
        self.lbl_password.setObjectName(u"lbl_password")
        self.lbl_password.setFont(font)
        self.lbl_password.setAlignment(Qt.AlignmentFlag.AlignLeading|Qt.AlignmentFlag.AlignLeft|Qt.AlignmentFlag.AlignVCenter)

        self.horizontalLayout_password.addWidget(self.lbl_password)

        self.input_password = QLineEdit(self.widget_input)
        self.input_password.setObjectName(u"input_password")
        self.input_password.setMinimumSize(QSize(220, 0))
        self.input_password.setMaximumSize(QSize(200, 16777215))
        self.input_password.setFont(font1)
        self.input_password.setEchoMode(QLineEdit.EchoMode.Password)

        self.horizontalLayout_password.addWidget(self.input_password)


        self.verticalLayout_3.addLayout(self.horizontalLayout_password)


        self.verticalLayout.addWidget(self.widget_input)

        self.widget_actions = QWidget(LogonNormalDialog)
        self.widget_actions.setObjectName(u"widget_actions")
        self.horizontalLayout_4 = QHBoxLayout(self.widget_actions)
        self.horizontalLayout_4.setObjectName(u"horizontalLayout_4")
        self.horizontalLayout_4.setContentsMargins(0, 0, 0, 0)
        self.horizontalSpacer_4 = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_4.addItem(self.horizontalSpacer_4)

        self.btn_logon = QPushButton(self.widget_actions)
        self.btn_logon.setObjectName(u"btn_logon")
        self.btn_logon.setMinimumSize(QSize(100, 0))
        self.btn_logon.setMaximumSize(QSize(100, 16777215))
        self.btn_logon.setFont(font1)

        self.horizontalLayout_4.addWidget(self.btn_logon)

        self.btn_cancel = QPushButton(self.widget_actions)
        self.btn_cancel.setObjectName(u"btn_cancel")
        self.btn_cancel.setMinimumSize(QSize(100, 0))
        self.btn_cancel.setMaximumSize(QSize(100, 16777215))
        self.btn_cancel.setFont(font1)

        self.horizontalLayout_4.addWidget(self.btn_cancel)


        self.verticalLayout.addWidget(self.widget_actions)

        QWidget.setTabOrder(self.input_id, self.input_password)
        QWidget.setTabOrder(self.input_password, self.btn_logon)
        QWidget.setTabOrder(self.btn_logon, self.btn_cancel)

        self.retranslateUi(LogonNormalDialog)

        QMetaObject.connectSlotsByName(LogonNormalDialog)
    # setupUi

    def retranslateUi(self, LogonNormalDialog):
        LogonNormalDialog.setWindowTitle(QCoreApplication.translate("LogonNormalDialog", u"Bunseki - Logon", None))
        self.label_message.setText(QCoreApplication.translate("LogonNormalDialog", u"\u30e6\u30fc\u30b6\u30fcID\u3068\u30d1\u30b9\u30ef\u30fc\u30c9\u3092\u5165\u529b\u3057\u3066\u304f\u3060\u3055\u3044\u3002", None))
        self.lbl_user_id.setText(QCoreApplication.translate("LogonNormalDialog", u"\u30e6\u30fc\u30b6\u30fc", None))
        self.lbl_password.setText(QCoreApplication.translate("LogonNormalDialog", u"\u30d1\u30b9\u30ef\u30fc\u30c9", None))
        self.btn_logon.setText(QCoreApplication.translate("LogonNormalDialog", u"\u30ed\u30b0\u30aa\u30f3", None))
        self.btn_cancel.setText(QCoreApplication.translate("LogonNormalDialog", u"\u30ad\u30e3\u30f3\u30bb\u30eb", None))
    # retranslateUi

