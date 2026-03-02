# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'ResetPasswordDialog.ui'
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

class Ui_ResetPasswordDialog(object):
    def setupUi(self, ResetPasswordDialog):
        if not ResetPasswordDialog.objectName():
            ResetPasswordDialog.setObjectName(u"ResetPasswordDialog")
        ResetPasswordDialog.resize(311, 143)
        self.verticalLayout = QVBoxLayout(ResetPasswordDialog)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.widget_picup_id = QWidget(ResetPasswordDialog)
        self.widget_picup_id.setObjectName(u"widget_picup_id")
        self.horizontalLayout_8 = QHBoxLayout(self.widget_picup_id)
        self.horizontalLayout_8.setObjectName(u"horizontalLayout_8")
        self.horizontalLayout_8.setContentsMargins(0, 0, 0, 0)
        self.label_id = QLabel(self.widget_picup_id)
        self.label_id.setObjectName(u"label_id")
        font = QFont()
        font.setPointSize(10)
        self.label_id.setFont(font)

        self.horizontalLayout_8.addWidget(self.label_id)

        self.label_picup_id = QLabel(self.widget_picup_id)
        self.label_picup_id.setObjectName(u"label_picup_id")
        self.label_picup_id.setMinimumSize(QSize(200, 0))
        font1 = QFont()
        font1.setPointSize(12)
        self.label_picup_id.setFont(font1)

        self.horizontalLayout_8.addWidget(self.label_picup_id)

        self.horizontalLayout_8.setStretch(0, 4)

        self.verticalLayout.addWidget(self.widget_picup_id)

        self.widget_new_password = QWidget(ResetPasswordDialog)
        self.widget_new_password.setObjectName(u"widget_new_password")
        self.horizontalLayout_7 = QHBoxLayout(self.widget_new_password)
        self.horizontalLayout_7.setObjectName(u"horizontalLayout_7")
        self.horizontalLayout_7.setContentsMargins(0, 0, 0, 0)
        self.label_new_password = QLabel(self.widget_new_password)
        self.label_new_password.setObjectName(u"label_new_password")
        self.label_new_password.setFont(font)

        self.horizontalLayout_7.addWidget(self.label_new_password)

        self.input_new_password = QLineEdit(self.widget_new_password)
        self.input_new_password.setObjectName(u"input_new_password")
        self.input_new_password.setMinimumSize(QSize(200, 0))
        self.input_new_password.setFont(font1)
        self.input_new_password.setEchoMode(QLineEdit.EchoMode.Password)

        self.horizontalLayout_7.addWidget(self.input_new_password)

        self.horizontalLayout_7.setStretch(0, 4)
        self.horizontalLayout_7.setStretch(1, 6)

        self.verticalLayout.addWidget(self.widget_new_password)

        self.widget_confirm_password = QWidget(ResetPasswordDialog)
        self.widget_confirm_password.setObjectName(u"widget_confirm_password")
        self.horizontalLayout_6 = QHBoxLayout(self.widget_confirm_password)
        self.horizontalLayout_6.setObjectName(u"horizontalLayout_6")
        self.horizontalLayout_6.setContentsMargins(0, 0, 0, 0)
        self.label_confirm_password = QLabel(self.widget_confirm_password)
        self.label_confirm_password.setObjectName(u"label_confirm_password")
        self.label_confirm_password.setFont(font)

        self.horizontalLayout_6.addWidget(self.label_confirm_password)

        self.input_confirl_password = QLineEdit(self.widget_confirm_password)
        self.input_confirl_password.setObjectName(u"input_confirl_password")
        self.input_confirl_password.setMinimumSize(QSize(200, 0))
        self.input_confirl_password.setFont(font1)
        self.input_confirl_password.setEchoMode(QLineEdit.EchoMode.Password)

        self.horizontalLayout_6.addWidget(self.input_confirl_password)

        self.horizontalLayout_6.setStretch(0, 4)
        self.horizontalLayout_6.setStretch(1, 6)

        self.verticalLayout.addWidget(self.widget_confirm_password)

        self.widget_actions = QWidget(ResetPasswordDialog)
        self.widget_actions.setObjectName(u"widget_actions")
        self.horizontalLayout_9 = QHBoxLayout(self.widget_actions)
        self.horizontalLayout_9.setObjectName(u"horizontalLayout_9")
        self.horizontalLayout_9.setContentsMargins(0, 0, 0, 0)
        self.horizontalSpacer_3 = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_9.addItem(self.horizontalSpacer_3)

        self.btn_update = QPushButton(self.widget_actions)
        self.btn_update.setObjectName(u"btn_update")
        self.btn_update.setFont(font1)

        self.horizontalLayout_9.addWidget(self.btn_update)

        self.btn_cancel = QPushButton(self.widget_actions)
        self.btn_cancel.setObjectName(u"btn_cancel")
        self.btn_cancel.setFont(font1)

        self.horizontalLayout_9.addWidget(self.btn_cancel)


        self.verticalLayout.addWidget(self.widget_actions)


        self.retranslateUi(ResetPasswordDialog)

        QMetaObject.connectSlotsByName(ResetPasswordDialog)
    # setupUi

    def retranslateUi(self, ResetPasswordDialog):
        ResetPasswordDialog.setWindowTitle(QCoreApplication.translate("ResetPasswordDialog", u"ResetPasswordDialog", None))
        self.label_id.setText(QCoreApplication.translate("ResetPasswordDialog", u"ID", None))
        self.label_picup_id.setText("")
        self.label_new_password.setText(QCoreApplication.translate("ResetPasswordDialog", u"\u65b0\u30d1\u30b9\u30ef\u30fc\u30c9", None))
        self.label_confirm_password.setText(QCoreApplication.translate("ResetPasswordDialog", u"\u78ba\u8a8d\u7528\u30d1\u30b9\u30ef\u30fc\u30c9", None))
        self.btn_update.setText(QCoreApplication.translate("ResetPasswordDialog", u"\u66f4\u65b0", None))
        self.btn_cancel.setText(QCoreApplication.translate("ResetPasswordDialog", u"\u30ad\u30e3\u30f3\u30bb\u30eb", None))
    # retranslateUi

