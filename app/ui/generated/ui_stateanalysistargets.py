# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'StateAnalysisTargets.ui'
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
from PySide6.QtWidgets import (QApplication, QFrame, QHBoxLayout, QHeaderView,
    QLabel, QPushButton, QSizePolicy, QSpacerItem,
    QTableView, QVBoxLayout, QWidget)
import app.ui.generated.resources_rc  # noqa: F401

class Ui_PageStateTarget(object):
    def setupUi(self, PageStateTarget):
        if not PageStateTarget.objectName():
            PageStateTarget.setObjectName(u"PageStateTarget")
        PageStateTarget.resize(1407, 839)
        self.verticalLayout = QVBoxLayout(PageStateTarget)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.widget_header = QWidget(PageStateTarget)
        self.widget_header.setObjectName(u"widget_header")
        self.widget_header.setMaximumSize(QSize(16777215, 70))
        self.horizontalLayout_4 = QHBoxLayout(self.widget_header)
        self.horizontalLayout_4.setObjectName(u"horizontalLayout_4")
        self.widget_task_conditions = QWidget(self.widget_header)
        self.widget_task_conditions.setObjectName(u"widget_task_conditions")
        self.horizontalLayout = QHBoxLayout(self.widget_task_conditions)
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.label_holder_groups = QLabel(self.widget_task_conditions)
        self.label_holder_groups.setObjectName(u"label_holder_groups")
        self.label_holder_groups.setMinimumSize(QSize(200, 50))
        self.label_holder_groups.setMaximumSize(QSize(16777215, 50))
        font = QFont()
        font.setPointSize(12)
        self.label_holder_groups.setFont(font)

        self.horizontalLayout.addWidget(self.label_holder_groups)

        self.widget_job_numbers = QWidget(self.widget_task_conditions)
        self.widget_job_numbers.setObjectName(u"widget_job_numbers")
        self.widget_job_numbers.setMinimumSize(QSize(200, 50))
        self.widget_job_numbers.setMaximumSize(QSize(16777215, 50))
        self.horizontalLayout_2 = QHBoxLayout(self.widget_job_numbers)
        self.horizontalLayout_2.setObjectName(u"horizontalLayout_2")

        self.horizontalLayout.addWidget(self.widget_job_numbers)

        self.label = QLabel(self.widget_task_conditions)
        self.label.setObjectName(u"label")
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.label.sizePolicy().hasHeightForWidth())
        self.label.setSizePolicy(sizePolicy)
        self.label.setMinimumSize(QSize(70, 35))
        self.label.setMaximumSize(QSize(50, 35))
        font1 = QFont()
        font1.setPointSize(10)
        self.label.setFont(font1)
        self.label.setFrameShape(QFrame.Shape.NoFrame)
        self.label.setLineWidth(0)
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.horizontalLayout.addWidget(self.label)


        self.horizontalLayout_4.addWidget(self.widget_task_conditions)

        self.horizontalSpacer = QSpacerItem(632, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_4.addItem(self.horizontalSpacer)

        self.widget_actions = QWidget(self.widget_header)
        self.widget_actions.setObjectName(u"widget_actions")
        self.horizontalLayout_3 = QHBoxLayout(self.widget_actions)
        self.horizontalLayout_3.setObjectName(u"horizontalLayout_3")
        self.btn_edit = QPushButton(self.widget_actions)
        self.btn_edit.setObjectName(u"btn_edit")
        self.btn_edit.setMinimumSize(QSize(100, 35))
        self.btn_edit.setMaximumSize(QSize(16777215, 50))
        self.btn_edit.setFont(font1)

        self.horizontalLayout_3.addWidget(self.btn_edit)

        self.btn_printout = QPushButton(self.widget_actions)
        self.btn_printout.setObjectName(u"btn_printout")
        self.btn_printout.setMinimumSize(QSize(100, 35))
        self.btn_printout.setMaximumSize(QSize(16777215, 50))
        self.btn_printout.setFont(font1)

        self.horizontalLayout_3.addWidget(self.btn_printout)


        self.horizontalLayout_4.addWidget(self.widget_actions)


        self.verticalLayout.addWidget(self.widget_header)

        self.widget_targets = QWidget(PageStateTarget)
        self.widget_targets.setObjectName(u"widget_targets")
        self.verticalLayout_2 = QVBoxLayout(self.widget_targets)
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.tableView_targets = QTableView(self.widget_targets)
        self.tableView_targets.setObjectName(u"tableView_targets")
        self.tableView_targets.setFont(font)

        self.verticalLayout_2.addWidget(self.tableView_targets)


        self.verticalLayout.addWidget(self.widget_targets)

        self.widget_action = QWidget(PageStateTarget)
        self.widget_action.setObjectName(u"widget_action")
        self.horizontalLayout_5 = QHBoxLayout(self.widget_action)
        self.horizontalLayout_5.setObjectName(u"horizontalLayout_5")
        self.horizontalSpacer_3 = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_5.addItem(self.horizontalSpacer_3)

        self.btn_back = QPushButton(self.widget_action)
        self.btn_back.setObjectName(u"btn_back")
        self.btn_back.setMinimumSize(QSize(100, 50))
        self.btn_back.setMaximumSize(QSize(100, 50))

        self.horizontalLayout_5.addWidget(self.btn_back)

        self.btn_next = QPushButton(self.widget_action)
        self.btn_next.setObjectName(u"btn_next")
        self.btn_next.setMinimumSize(QSize(100, 50))
        self.btn_next.setMaximumSize(QSize(100, 50))

        self.horizontalLayout_5.addWidget(self.btn_next)

        self.horizontalSpacer_4 = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_5.addItem(self.horizontalSpacer_4)


        self.verticalLayout.addWidget(self.widget_action)


        self.retranslateUi(PageStateTarget)

        QMetaObject.connectSlotsByName(PageStateTarget)
    # setupUi

    def retranslateUi(self, PageStateTarget):
        PageStateTarget.setWindowTitle(QCoreApplication.translate("PageStateTarget", u"PageStateTarget", None))
        self.label_holder_groups.setText("")
        self.label.setText(QCoreApplication.translate("PageStateTarget", u"\u7de8\u96c6\u6e08\u307f", None))
        self.btn_edit.setText(QCoreApplication.translate("PageStateTarget", u"\u7de8\u96c6", None))
        self.btn_printout.setText(QCoreApplication.translate("PageStateTarget", u"\u5370\u5237", None))
        self.btn_back.setText(QCoreApplication.translate("PageStateTarget", u"\u623b\u308b", None))
        self.btn_next.setText(QCoreApplication.translate("PageStateTarget", u"\u6b21\u3078", None))
    # retranslateUi

