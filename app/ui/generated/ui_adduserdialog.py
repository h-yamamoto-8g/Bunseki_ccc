# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'AddUserDialog.ui'
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
from PySide6.QtWidgets import (QApplication, QCheckBox, QDialog, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QSizePolicy,
    QSpacerItem, QVBoxLayout, QWidget)

class Ui_AddUserDialog(object):
    def setupUi(self, AddUserDialog):
        if not AddUserDialog.objectName():
            AddUserDialog.setObjectName(u"AddUserDialog")
        AddUserDialog.resize(298, 212)
        self.verticalLayout = QVBoxLayout(AddUserDialog)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.widget_id = QWidget(AddUserDialog)
        self.widget_id.setObjectName(u"widget_id")
        self.horizontalLayout = QHBoxLayout(self.widget_id)
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.horizontalLayout.setContentsMargins(0, 0, 0, 0)
        self.label_id = QLabel(self.widget_id)
        self.label_id.setObjectName(u"label_id")
        font = QFont()
        font.setPointSize(10)
        self.label_id.setFont(font)

        self.horizontalLayout.addWidget(self.label_id)

        self.input_id = QLineEdit(self.widget_id)
        self.input_id.setObjectName(u"input_id")
        self.input_id.setMinimumSize(QSize(200, 0))
        font1 = QFont()
        font1.setPointSize(12)
        self.input_id.setFont(font1)

        self.horizontalLayout.addWidget(self.input_id)

        self.horizontalLayout.setStretch(0, 4)
        self.horizontalLayout.setStretch(1, 6)

        self.verticalLayout.addWidget(self.widget_id)

        self.widget_name = QWidget(AddUserDialog)
        self.widget_name.setObjectName(u"widget_name")
        self.horizontalLayout_2 = QHBoxLayout(self.widget_name)
        self.horizontalLayout_2.setObjectName(u"horizontalLayout_2")
        self.horizontalLayout_2.setContentsMargins(0, 0, 0, 0)
        self.label_name = QLabel(self.widget_name)
        self.label_name.setObjectName(u"label_name")
        self.label_name.setFont(font)

        self.horizontalLayout_2.addWidget(self.label_name)

        self.input_name = QLineEdit(self.widget_name)
        self.input_name.setObjectName(u"input_name")
        self.input_name.setMinimumSize(QSize(200, 0))
        self.input_name.setFont(font1)

        self.horizontalLayout_2.addWidget(self.input_name)

        self.horizontalLayout_2.setStretch(0, 4)
        self.horizontalLayout_2.setStretch(1, 6)

        self.verticalLayout.addWidget(self.widget_name)

        self.widget_init_password_2 = QWidget(AddUserDialog)
        self.widget_init_password_2.setObjectName(u"widget_init_password_2")
        self.horizontalLayout_6 = QHBoxLayout(self.widget_init_password_2)
        self.horizontalLayout_6.setObjectName(u"horizontalLayout_6")
        self.horizontalLayout_6.setContentsMargins(0, 0, 0, 0)
        self.label_email = QLabel(self.widget_init_password_2)
        self.label_email.setObjectName(u"label_email")
        self.label_email.setFont(font)

        self.horizontalLayout_6.addWidget(self.label_email)

        self.input_email = QLineEdit(self.widget_init_password_2)
        self.input_email.setObjectName(u"input_email")
        self.input_email.setMinimumSize(QSize(200, 0))
        self.input_email.setFont(font1)
        self.input_email.setEchoMode(QLineEdit.EchoMode.Normal)

        self.horizontalLayout_6.addWidget(self.input_email)

        self.horizontalLayout_6.setStretch(0, 4)
        self.horizontalLayout_6.setStretch(1, 6)

        self.verticalLayout.addWidget(self.widget_init_password_2)

        self.widget_init_password = QWidget(AddUserDialog)
        self.widget_init_password.setObjectName(u"widget_init_password")
        self.horizontalLayout_3 = QHBoxLayout(self.widget_init_password)
        self.horizontalLayout_3.setObjectName(u"horizontalLayout_3")
        self.horizontalLayout_3.setContentsMargins(0, 0, 0, 0)
        self.label_init_password = QLabel(self.widget_init_password)
        self.label_init_password.setObjectName(u"label_init_password")
        self.label_init_password.setFont(font)

        self.horizontalLayout_3.addWidget(self.label_init_password)

        self.input_init_password = QLineEdit(self.widget_init_password)
        self.input_init_password.setObjectName(u"input_init_password")
        self.input_init_password.setMinimumSize(QSize(200, 0))
        self.input_init_password.setFont(font1)
        self.input_init_password.setEchoMode(QLineEdit.EchoMode.Password)

        self.horizontalLayout_3.addWidget(self.input_init_password)

        self.horizontalLayout_3.setStretch(0, 4)
        self.horizontalLayout_3.setStretch(1, 6)

        self.verticalLayout.addWidget(self.widget_init_password)

        self.widget_checkBox = QWidget(AddUserDialog)
        self.widget_checkBox.setObjectName(u"widget_checkBox")
        self.horizontalLayout_4 = QHBoxLayout(self.widget_checkBox)
        self.horizontalLayout_4.setObjectName(u"horizontalLayout_4")
        self.horizontalLayout_4.setContentsMargins(0, 0, 0, 0)
        self.horizontalSpacer = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_4.addItem(self.horizontalSpacer)

        self.checkBox_active = QCheckBox(self.widget_checkBox)
        self.checkBox_active.setObjectName(u"checkBox_active")
        self.checkBox_active.setFont(font)
        self.checkBox_active.setChecked(True)

        self.horizontalLayout_4.addWidget(self.checkBox_active)

        self.checkBox_admin = QCheckBox(self.widget_checkBox)
        self.checkBox_admin.setObjectName(u"checkBox_admin")
        self.checkBox_admin.setFont(font)

        self.horizontalLayout_4.addWidget(self.checkBox_admin)


        self.verticalLayout.addWidget(self.widget_checkBox)

        self.widget_actions = QWidget(AddUserDialog)
        self.widget_actions.setObjectName(u"widget_actions")
        self.horizontalLayout_5 = QHBoxLayout(self.widget_actions)
        self.horizontalLayout_5.setObjectName(u"horizontalLayout_5")
        self.horizontalLayout_5.setContentsMargins(0, 0, 0, 0)
        self.horizontalSpacer_2 = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_5.addItem(self.horizontalSpacer_2)

        self.btn_add = QPushButton(self.widget_actions)
        self.btn_add.setObjectName(u"btn_add")
        self.btn_add.setFont(font1)

        self.horizontalLayout_5.addWidget(self.btn_add)

        self.btn_cancel = QPushButton(self.widget_actions)
        self.btn_cancel.setObjectName(u"btn_cancel")
        self.btn_cancel.setFont(font1)

        self.horizontalLayout_5.addWidget(self.btn_cancel)


        self.verticalLayout.addWidget(self.widget_actions)


        self.retranslateUi(AddUserDialog)

        QMetaObject.connectSlotsByName(AddUserDialog)
    # setupUi

    def retranslateUi(self, AddUserDialog):
        AddUserDialog.setWindowTitle(QCoreApplication.translate("AddUserDialog", u"AddUserDialog", None))
        self.label_id.setText(QCoreApplication.translate("AddUserDialog", u"ID", None))
        self.label_name.setText(QCoreApplication.translate("AddUserDialog", u"\u540d\u524d", None))
        self.label_email.setText(QCoreApplication.translate("AddUserDialog", u"\u30e1\u30fc\u30eb\u30a2\u30c9\u30ec\u30b9", None))
        self.label_init_password.setText(QCoreApplication.translate("AddUserDialog", u"\u521d\u671f\u30d1\u30b9\u30ef\u30fc\u30c9", None))
        self.checkBox_active.setText(QCoreApplication.translate("AddUserDialog", u"\u6709\u52b9", None))
        self.checkBox_admin.setText(QCoreApplication.translate("AddUserDialog", u"\u7ba1\u7406\u8005", None))
        self.btn_add.setText(QCoreApplication.translate("AddUserDialog", u"\u767b\u9332", None))
        self.btn_cancel.setText(QCoreApplication.translate("AddUserDialog", u"\u30ad\u30e3\u30f3\u30bb\u30eb", None))
    # retranslateUi

