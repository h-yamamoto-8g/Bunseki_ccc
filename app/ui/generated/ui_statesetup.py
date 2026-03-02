# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'StateSetup.ui'
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
from PySide6.QtWidgets import (QApplication, QComboBox, QHBoxLayout, QLineEdit,
    QPushButton, QScrollArea, QSizePolicy, QSpacerItem,
    QVBoxLayout, QWidget)
import app.ui.generated.resources_rc  # noqa: F401

class Ui_PageStateStart(object):
    def setupUi(self, PageStateStart):
        if not PageStateStart.objectName():
            PageStateStart.setObjectName(u"PageStateStart")
        PageStateStart.resize(824, 446)
        self.verticalLayout = QVBoxLayout(PageStateStart)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.verticalLayout.setContentsMargins(9, 9, 9, -1)
        self.widget_posted_tasks = QWidget(PageStateStart)
        self.widget_posted_tasks.setObjectName(u"widget_posted_tasks")
        self.horizontalLayout = QHBoxLayout(self.widget_posted_tasks)
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.horizontalLayout.setContentsMargins(0, 0, 0, 0)
        self.widget_setup = QWidget(self.widget_posted_tasks)
        self.widget_setup.setObjectName(u"widget_setup")
        self.horizontalLayout_3 = QHBoxLayout(self.widget_setup)
        self.horizontalLayout_3.setObjectName(u"horizontalLayout_3")
        self.horizontalSpacer = QSpacerItem(481, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_3.addItem(self.horizontalSpacer)

        self.widget_form = QWidget(self.widget_setup)
        self.widget_form.setObjectName(u"widget_form")
        self.widget_form.setMinimumSize(QSize(100, 50))
        self.verticalLayout_2 = QVBoxLayout(self.widget_form)
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.verticalSpacer_2 = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.verticalLayout_2.addItem(self.verticalSpacer_2)

        self.comboBox_holder_groups = QComboBox(self.widget_form)
        self.comboBox_holder_groups.setObjectName(u"comboBox_holder_groups")
        self.comboBox_holder_groups.setMinimumSize(QSize(300, 50))
        self.comboBox_holder_groups.setMaximumSize(QSize(16777215, 16777215))
        font = QFont()
        font.setPointSize(12)
        self.comboBox_holder_groups.setFont(font)

        self.verticalLayout_2.addWidget(self.comboBox_holder_groups)

        self.widget_job_numbers = QWidget(self.widget_form)
        self.widget_job_numbers.setObjectName(u"widget_job_numbers")
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.widget_job_numbers.sizePolicy().hasHeightForWidth())
        self.widget_job_numbers.setSizePolicy(sizePolicy)
        self.widget_job_numbers.setMaximumSize(QSize(16777215, 70))
        self.widget_job_numbers.setLayoutDirection(Qt.LayoutDirection.LeftToRight)
        self.horizontalLayout_4 = QHBoxLayout(self.widget_job_numbers)
        self.horizontalLayout_4.setObjectName(u"horizontalLayout_4")
        self.horizontalLayout_4.setContentsMargins(0, 0, 0, 0)
        self.input_job_number = QLineEdit(self.widget_job_numbers)
        self.input_job_number.setObjectName(u"input_job_number")
        self.input_job_number.setMinimumSize(QSize(160, 50))
        self.input_job_number.setMaximumSize(QSize(16777215, 50))
        self.input_job_number.setFont(font)

        self.horizontalLayout_4.addWidget(self.input_job_number)

        self.btn_job_number_add = QPushButton(self.widget_job_numbers)
        self.btn_job_number_add.setObjectName(u"btn_job_number_add")
        self.btn_job_number_add.setMinimumSize(QSize(50, 50))
        self.btn_job_number_add.setMaximumSize(QSize(50, 50))
        icon = QIcon()
        icon.addFile(u":/icons/add.svg", QSize(), QIcon.Mode.Normal, QIcon.State.Off)
        self.btn_job_number_add.setIcon(icon)
        self.btn_job_number_add.setIconSize(QSize(24, 24))

        self.horizontalLayout_4.addWidget(self.btn_job_number_add)


        self.verticalLayout_2.addWidget(self.widget_job_numbers)

        self.scroll_job_numbers = QScrollArea(self.widget_form)
        self.scroll_job_numbers.setObjectName(u"scroll_job_numbers")
        self.scroll_job_numbers.setMinimumSize(QSize(0, 50))
        self.scroll_job_numbers.setMaximumSize(QSize(16777215, 50))
        self.scroll_job_numbers.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.scroll_job_numbers.setWidgetResizable(True)
        self.scroll_job_numbers_contents = QWidget()
        self.scroll_job_numbers_contents.setObjectName(u"scroll_job_numbers_contents")
        self.scroll_job_numbers_contents.setGeometry(QRect(0, 0, 138, 46))
        self.horizontalLayout_2 = QHBoxLayout(self.scroll_job_numbers_contents)
        self.horizontalLayout_2.setObjectName(u"horizontalLayout_2")
        self.scroll_job_numbers.setWidget(self.scroll_job_numbers_contents)

        self.verticalLayout_2.addWidget(self.scroll_job_numbers)

        self.widget_action = QWidget(self.widget_form)
        self.widget_action.setObjectName(u"widget_action")
        self.horizontalLayout_5 = QHBoxLayout(self.widget_action)
        self.horizontalLayout_5.setObjectName(u"horizontalLayout_5")
        self.horizontalSpacer_3 = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_5.addItem(self.horizontalSpacer_3)

        self.btn_cancel = QPushButton(self.widget_action)
        self.btn_cancel.setObjectName(u"btn_cancel")
        self.btn_cancel.setMinimumSize(QSize(100, 50))
        self.btn_cancel.setMaximumSize(QSize(100, 50))

        self.horizontalLayout_5.addWidget(self.btn_cancel)

        self.btn_create = QPushButton(self.widget_action)
        self.btn_create.setObjectName(u"btn_create")
        self.btn_create.setMinimumSize(QSize(100, 50))
        self.btn_create.setMaximumSize(QSize(100, 50))

        self.horizontalLayout_5.addWidget(self.btn_create)

        self.horizontalSpacer_4 = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_5.addItem(self.horizontalSpacer_4)


        self.verticalLayout_2.addWidget(self.widget_action)

        self.verticalSpacer = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.verticalLayout_2.addItem(self.verticalSpacer)


        self.horizontalLayout_3.addWidget(self.widget_form)

        self.horizontalSpacer_2 = QSpacerItem(481, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_3.addItem(self.horizontalSpacer_2)


        self.horizontalLayout.addWidget(self.widget_setup)


        self.verticalLayout.addWidget(self.widget_posted_tasks)


        self.retranslateUi(PageStateStart)

        QMetaObject.connectSlotsByName(PageStateStart)
    # setupUi

    def retranslateUi(self, PageStateStart):
        PageStateStart.setWindowTitle(QCoreApplication.translate("PageStateStart", u"PageStateStart", None))
        self.comboBox_holder_groups.setPlaceholderText(QCoreApplication.translate("PageStateStart", u"\u5206\u6790\u9805\u76ee", None))
        self.input_job_number.setInputMask("")
        self.input_job_number.setText("")
        self.input_job_number.setPlaceholderText(QCoreApplication.translate("PageStateStart", u"JOB\u756a\u53f7\u3092\u5165\u529b", None))
        self.btn_job_number_add.setText("")
        self.btn_cancel.setText(QCoreApplication.translate("PageStateStart", u"\u30ad\u30e3\u30f3\u30bb\u30eb", None))
        self.btn_create.setText(QCoreApplication.translate("PageStateStart", u"\u4f5c\u6210", None))
    # retranslateUi

