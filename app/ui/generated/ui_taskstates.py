# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'TaskStates.ui'
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
from PySide6.QtWidgets import (QApplication, QSizePolicy, QStackedWidget, QVBoxLayout,
    QWidget)

class Ui_TasksPage(object):
    def setupUi(self, TasksPage):
        if not TasksPage.objectName():
            TasksPage.setObjectName(u"TasksPage")
        TasksPage.resize(1163, 757)
        self.verticalLayout = QVBoxLayout(TasksPage)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.stack_task_states = QStackedWidget(TasksPage)
        self.stack_task_states.setObjectName(u"stack_task_states")
        self.state_setup = QWidget()
        self.state_setup.setObjectName(u"state_setup")
        self.verticalLayout_6 = QVBoxLayout(self.state_setup)
        self.verticalLayout_6.setObjectName(u"verticalLayout_6")
        self.stack_task_states.addWidget(self.state_setup)
        self.state_analysis_targets = QWidget()
        self.state_analysis_targets.setObjectName(u"state_analysis_targets")
        self.verticalLayout_7 = QVBoxLayout(self.state_analysis_targets)
        self.verticalLayout_7.setObjectName(u"verticalLayout_7")
        self.stack_task_states.addWidget(self.state_analysis_targets)
        self.state_analysis = QWidget()
        self.state_analysis.setObjectName(u"state_analysis")
        self.verticalLayout_2 = QVBoxLayout(self.state_analysis)
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.stack_task_states.addWidget(self.state_analysis)
        self.state_entry = QWidget()
        self.state_entry.setObjectName(u"state_entry")
        self.verticalLayout_4 = QVBoxLayout(self.state_entry)
        self.verticalLayout_4.setObjectName(u"verticalLayout_4")
        self.stack_task_states.addWidget(self.state_entry)
        self.state_result_verification = QWidget()
        self.state_result_verification.setObjectName(u"state_result_verification")
        self.verticalLayout_5 = QVBoxLayout(self.state_result_verification)
        self.verticalLayout_5.setObjectName(u"verticalLayout_5")
        self.stack_task_states.addWidget(self.state_result_verification)
        self.state_completed = QWidget()
        self.state_completed.setObjectName(u"state_completed")
        self.verticalLayout_3 = QVBoxLayout(self.state_completed)
        self.verticalLayout_3.setObjectName(u"verticalLayout_3")
        self.stack_task_states.addWidget(self.state_completed)

        self.verticalLayout.addWidget(self.stack_task_states)


        self.retranslateUi(TasksPage)

        QMetaObject.connectSlotsByName(TasksPage)
    # setupUi

    def retranslateUi(self, TasksPage):
        TasksPage.setWindowTitle(QCoreApplication.translate("TasksPage", u"TaskStates", None))
    # retranslateUi

