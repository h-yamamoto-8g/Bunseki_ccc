# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'TasksPage.ui'
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
from PySide6.QtWidgets import (QApplication, QComboBox, QHBoxLayout, QHeaderView,
    QPushButton, QSizePolicy, QSpacerItem, QTableView,
    QVBoxLayout, QWidget)

class Ui_TasksPage(object):
    def setupUi(self, TasksPage):
        if not TasksPage.objectName():
            TasksPage.setObjectName(u"TasksPage")
        TasksPage.resize(1197, 781)
        self.verticalLayout = QVBoxLayout(TasksPage)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.widget_filter = QWidget(TasksPage)
        self.widget_filter.setObjectName(u"widget_filter")
        self.widget_filter.setMinimumSize(QSize(0, 50))
        self.widget_filter.setMaximumSize(QSize(16777215, 50))
        self.horizontalLayout_2 = QHBoxLayout(self.widget_filter)
        self.horizontalLayout_2.setObjectName(u"horizontalLayout_2")
        self.widget_segbar = QWidget(self.widget_filter)
        self.widget_segbar.setObjectName(u"widget_segbar")
        self.widget_segbar.setMinimumSize(QSize(0, 35))
        self.widget_segbar.setMaximumSize(QSize(16777215, 35))
        self.horizontalLayout = QHBoxLayout(self.widget_segbar)
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.horizontalLayout.setContentsMargins(0, 0, 0, 0)
        self.btn_seg_you = QPushButton(self.widget_segbar)
        self.btn_seg_you.setObjectName(u"btn_seg_you")
        self.btn_seg_you.setMinimumSize(QSize(100, 0))
        self.btn_seg_you.setMaximumSize(QSize(100, 16777215))
        font = QFont()
        font.setPointSize(12)
        self.btn_seg_you.setFont(font)

        self.horizontalLayout.addWidget(self.btn_seg_you)

        self.btn_seg_tobecompleted = QPushButton(self.widget_segbar)
        self.btn_seg_tobecompleted.setObjectName(u"btn_seg_tobecompleted")
        self.btn_seg_tobecompleted.setMinimumSize(QSize(100, 0))
        self.btn_seg_tobecompleted.setMaximumSize(QSize(100, 16777215))
        self.btn_seg_tobecompleted.setFont(font)

        self.horizontalLayout.addWidget(self.btn_seg_tobecompleted)

        self.btn_seg_completed = QPushButton(self.widget_segbar)
        self.btn_seg_completed.setObjectName(u"btn_seg_completed")
        self.btn_seg_completed.setMinimumSize(QSize(100, 0))
        self.btn_seg_completed.setMaximumSize(QSize(100, 16777215))
        self.btn_seg_completed.setFont(font)

        self.horizontalLayout.addWidget(self.btn_seg_completed)


        self.horizontalLayout_2.addWidget(self.widget_segbar)

        self.comboBox_holder_groups = QComboBox(self.widget_filter)
        self.comboBox_holder_groups.setObjectName(u"comboBox_holder_groups")
        self.comboBox_holder_groups.setMinimumSize(QSize(200, 35))
        self.comboBox_holder_groups.setMaximumSize(QSize(35, 16777215))
        self.comboBox_holder_groups.setFont(font)

        self.horizontalLayout_2.addWidget(self.comboBox_holder_groups)

        self.comboBox_users = QComboBox(self.widget_filter)
        self.comboBox_users.setObjectName(u"comboBox_users")
        self.comboBox_users.setMinimumSize(QSize(200, 35))
        self.comboBox_users.setMaximumSize(QSize(35, 16777215))
        self.comboBox_users.setFont(font)

        self.horizontalLayout_2.addWidget(self.comboBox_users)

        self.horizontalSpacer = QSpacerItem(428, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_2.addItem(self.horizontalSpacer)


        self.verticalLayout.addWidget(self.widget_filter)

        self.widget_table = QWidget(TasksPage)
        self.widget_table.setObjectName(u"widget_table")
        self.verticalLayout_2 = QVBoxLayout(self.widget_table)
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.tableView = QTableView(self.widget_table)
        self.tableView.setObjectName(u"tableView")
        self.tableView.setFont(font)

        self.verticalLayout_2.addWidget(self.tableView)


        self.verticalLayout.addWidget(self.widget_table)


        self.retranslateUi(TasksPage)

        QMetaObject.connectSlotsByName(TasksPage)
    # setupUi

    def retranslateUi(self, TasksPage):
        TasksPage.setWindowTitle(QCoreApplication.translate("TasksPage", u"TasksPage", None))
        self.btn_seg_you.setText(QCoreApplication.translate("TasksPage", u"\u3042\u306a\u305f", None))
        self.btn_seg_tobecompleted.setText(QCoreApplication.translate("TasksPage", u"\u5b9f\u65bd\u4e2d", None))
        self.btn_seg_completed.setText(QCoreApplication.translate("TasksPage", u"\u7d42\u4e86", None))
        self.comboBox_holder_groups.setCurrentText("")
        self.comboBox_holder_groups.setPlaceholderText(QCoreApplication.translate("TasksPage", u"\u5206\u6790\u9805\u76ee", None))
        self.comboBox_users.setCurrentText("")
        self.comboBox_users.setPlaceholderText(QCoreApplication.translate("TasksPage", u"\u30e6\u30fc\u30b6\u30fc\u540d", None))
    # retranslateUi

