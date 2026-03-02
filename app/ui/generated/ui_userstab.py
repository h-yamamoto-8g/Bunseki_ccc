# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'UsersTab.ui'
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
from PySide6.QtWidgets import (QApplication, QHBoxLayout, QHeaderView, QPushButton,
    QSizePolicy, QSpacerItem, QTableView, QVBoxLayout,
    QWidget)
import app.ui.generated.resources_rc  # noqa: F401

class Ui_UsersTab(object):
    def setupUi(self, UsersTab):
        if not UsersTab.objectName():
            UsersTab.setObjectName(u"UsersTab")
        UsersTab.resize(1127, 654)
        self.verticalLayout = QVBoxLayout(UsersTab)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.verticalLayout.setContentsMargins(0, 0, 0, 0)
        self.widget_actions = QWidget(UsersTab)
        self.widget_actions.setObjectName(u"widget_actions")
        self.widget_actions.setMinimumSize(QSize(0, 50))
        self.widget_actions.setMaximumSize(QSize(16777215, 50))
        self.horizontalLayout = QHBoxLayout(self.widget_actions)
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.horizontalSpacer = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout.addItem(self.horizontalSpacer)

        self.btn_reload = QPushButton(self.widget_actions)
        self.btn_reload.setObjectName(u"btn_reload")
        self.btn_reload.setMinimumSize(QSize(0, 35))
        icon = QIcon()
        icon.addFile(u":/icons/reload.svg", QSize(), QIcon.Mode.Normal, QIcon.State.Off)
        self.btn_reload.setIcon(icon)
        self.btn_reload.setIconSize(QSize(24, 24))

        self.horizontalLayout.addWidget(self.btn_reload)

        self.btn_add = QPushButton(self.widget_actions)
        self.btn_add.setObjectName(u"btn_add")
        self.btn_add.setMinimumSize(QSize(0, 35))
        icon1 = QIcon()
        icon1.addFile(u":/icons/add.svg", QSize(), QIcon.Mode.Normal, QIcon.State.Off)
        self.btn_add.setIcon(icon1)
        self.btn_add.setIconSize(QSize(24, 24))

        self.horizontalLayout.addWidget(self.btn_add)

        self.btn_edit = QPushButton(self.widget_actions)
        self.btn_edit.setObjectName(u"btn_edit")
        self.btn_edit.setMinimumSize(QSize(0, 35))
        icon2 = QIcon()
        icon2.addFile(u":/icons/edit.svg", QSize(), QIcon.Mode.Normal, QIcon.State.Off)
        self.btn_edit.setIcon(icon2)
        self.btn_edit.setIconSize(QSize(24, 24))

        self.horizontalLayout.addWidget(self.btn_edit)

        self.btn_password_reset = QPushButton(self.widget_actions)
        self.btn_password_reset.setObjectName(u"btn_password_reset")
        self.btn_password_reset.setMinimumSize(QSize(0, 35))
        icon3 = QIcon()
        icon3.addFile(u":/icons/password-reset.svg", QSize(), QIcon.Mode.Normal, QIcon.State.Off)
        self.btn_password_reset.setIcon(icon3)
        self.btn_password_reset.setIconSize(QSize(24, 24))

        self.horizontalLayout.addWidget(self.btn_password_reset)

        self.btn_active_switch = QPushButton(self.widget_actions)
        self.btn_active_switch.setObjectName(u"btn_active_switch")
        self.btn_active_switch.setMinimumSize(QSize(0, 35))
        icon4 = QIcon()
        icon4.addFile(u":/icons/switch.svg", QSize(), QIcon.Mode.Normal, QIcon.State.Off)
        self.btn_active_switch.setIcon(icon4)
        self.btn_active_switch.setIconSize(QSize(24, 24))

        self.horizontalLayout.addWidget(self.btn_active_switch)


        self.verticalLayout.addWidget(self.widget_actions)

        self.widget_users = QWidget(UsersTab)
        self.widget_users.setObjectName(u"widget_users")
        self.verticalLayout_2 = QVBoxLayout(self.widget_users)
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.tableView_users = QTableView(self.widget_users)
        self.tableView_users.setObjectName(u"tableView_users")

        self.verticalLayout_2.addWidget(self.tableView_users)


        self.verticalLayout.addWidget(self.widget_users)

        self.verticalLayout.setStretch(0, 1)
        self.verticalLayout.setStretch(1, 9)

        self.retranslateUi(UsersTab)

        QMetaObject.connectSlotsByName(UsersTab)
    # setupUi

    def retranslateUi(self, UsersTab):
        UsersTab.setWindowTitle(QCoreApplication.translate("UsersTab", u"UsersTab", None))
        self.btn_reload.setText(QCoreApplication.translate("UsersTab", u"\u66f4\u65b0", None))
        self.btn_add.setText(QCoreApplication.translate("UsersTab", u"\u8ffd\u52a0", None))
        self.btn_edit.setText(QCoreApplication.translate("UsersTab", u"\u7de8\u96c6", None))
        self.btn_password_reset.setText(QCoreApplication.translate("UsersTab", u"\u30d1\u30b9\u30ef\u30fc\u30c9\u518d\u8a2d\u5b9a", None))
        self.btn_active_switch.setText(QCoreApplication.translate("UsersTab", u"\u6709\u52b9 / \u7121\u52b9", None))
    # retranslateUi

