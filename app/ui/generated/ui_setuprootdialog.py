# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'SetupRootDialog.ui'
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
import app.ui.generated.resources_rc  # noqa: F401

class Ui_SetupRootDialog(object):
    def setupUi(self, SetupRootDialog):
        if not SetupRootDialog.objectName():
            SetupRootDialog.setObjectName(u"SetupRootDialog")
        SetupRootDialog.resize(572, 110)
        self.verticalLayout_2 = QVBoxLayout(SetupRootDialog)
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.widget_message = QWidget(SetupRootDialog)
        self.widget_message.setObjectName(u"widget_message")
        self.verticalLayout = QVBoxLayout(self.widget_message)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.verticalLayout.setContentsMargins(0, 0, 0, 0)
        self.label_message = QLabel(self.widget_message)
        self.label_message.setObjectName(u"label_message")
        font = QFont()
        font.setPointSize(10)
        self.label_message.setFont(font)

        self.verticalLayout.addWidget(self.label_message)


        self.verticalLayout_2.addWidget(self.widget_message)

        self.widget_input = QWidget(SetupRootDialog)
        self.widget_input.setObjectName(u"widget_input")
        self.horizontalLayout_2 = QHBoxLayout(self.widget_input)
        self.horizontalLayout_2.setObjectName(u"horizontalLayout_2")
        self.horizontalLayout_2.setContentsMargins(0, 0, 0, 0)
        self.input_data_path = QLineEdit(self.widget_input)
        self.input_data_path.setObjectName(u"input_data_path")
        self.input_data_path.setMinimumSize(QSize(500, 0))
        font1 = QFont()
        font1.setPointSize(12)
        self.input_data_path.setFont(font1)

        self.horizontalLayout_2.addWidget(self.input_data_path)

        self.btn_reference = QPushButton(self.widget_input)
        self.btn_reference.setObjectName(u"btn_reference")
        self.btn_reference.setMinimumSize(QSize(30, 30))
        self.btn_reference.setMaximumSize(QSize(30, 30))
        self.btn_reference.setContextMenuPolicy(Qt.ContextMenuPolicy.DefaultContextMenu)
        self.btn_reference.setLayoutDirection(Qt.LayoutDirection.LeftToRight)
        icon = QIcon()
        icon.addFile(u":/icons/path.svg", QSize(), QIcon.Mode.Normal, QIcon.State.Off)
        self.btn_reference.setIcon(icon)
        self.btn_reference.setIconSize(QSize(16, 16))
        self.btn_reference.setFlat(False)

        self.horizontalLayout_2.addWidget(self.btn_reference)


        self.verticalLayout_2.addWidget(self.widget_input)

        self.widget = QWidget(SetupRootDialog)
        self.widget.setObjectName(u"widget")
        self.horizontalLayout = QHBoxLayout(self.widget)
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.horizontalLayout.setContentsMargins(0, 0, 0, 0)
        self.horizontalSpacer = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout.addItem(self.horizontalSpacer)

        self.btn_ok = QPushButton(self.widget)
        self.btn_ok.setObjectName(u"btn_ok")
        self.btn_ok.setMinimumSize(QSize(100, 0))
        self.btn_ok.setMaximumSize(QSize(100, 16777215))
        self.btn_ok.setFont(font1)

        self.horizontalLayout.addWidget(self.btn_ok)

        self.btn_cancel = QPushButton(self.widget)
        self.btn_cancel.setObjectName(u"btn_cancel")
        self.btn_cancel.setMinimumSize(QSize(100, 0))
        self.btn_cancel.setMaximumSize(QSize(100, 16777215))
        self.btn_cancel.setFont(font1)

        self.horizontalLayout.addWidget(self.btn_cancel)


        self.verticalLayout_2.addWidget(self.widget)


        self.retranslateUi(SetupRootDialog)

        QMetaObject.connectSlotsByName(SetupRootDialog)
    # setupUi

    def retranslateUi(self, SetupRootDialog):
        SetupRootDialog.setWindowTitle(QCoreApplication.translate("SetupRootDialog", u"Setup Root", None))
        self.label_message.setText(QCoreApplication.translate("SetupRootDialog", u"\u30c7\u30fc\u30bf\u4fdd\u5b58\u5148(SharePoint\u540c\u671f\u30d5\u30a9\u30eb\u30c0)\u3092\u9078\u629e\u3057\u3066\u304f\u3060\u3055\u3044\u3002", None))
        self.btn_ok.setText(QCoreApplication.translate("SetupRootDialog", u"OK", None))
        self.btn_cancel.setText(QCoreApplication.translate("SetupRootDialog", u"\u30ad\u30e3\u30f3\u30bb\u30eb", None))
    # retranslateUi

