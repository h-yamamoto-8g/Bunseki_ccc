# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'StateSubmission.ui'
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
from PySide6.QtWidgets import (QApplication, QComboBox, QFrame, QHBoxLayout,
    QHeaderView, QLabel, QPlainTextEdit, QPushButton,
    QSizePolicy, QSpacerItem, QTableView, QVBoxLayout,
    QWidget)
import app.ui.generated.resources_rc  # noqa: F401

class Ui_StateSubmission(object):
    def setupUi(self, StateSubmission):
        if not StateSubmission.objectName():
            StateSubmission.setObjectName(u"StateSubmission")
        StateSubmission.resize(1312, 686)
        self.verticalLayout = QVBoxLayout(StateSubmission)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.widget_flow = QWidget(StateSubmission)
        self.widget_flow.setObjectName(u"widget_flow")
        self.verticalLayout_4 = QVBoxLayout(self.widget_flow)
        self.verticalLayout_4.setObjectName(u"verticalLayout_4")

        self.verticalLayout.addWidget(self.widget_flow)

        self.widget_analyst = QWidget(StateSubmission)
        self.widget_analyst.setObjectName(u"widget_analyst")
        self.horizontalLayout_3 = QHBoxLayout(self.widget_analyst)
        self.horizontalLayout_3.setObjectName(u"horizontalLayout_3")
        self.icon_analyst = QWidget(self.widget_analyst)
        self.icon_analyst.setObjectName(u"icon_analyst")
        self.icon_analyst.setMinimumSize(QSize(0, 0))
        self.icon_analyst.setMaximumSize(QSize(16777215, 16777215))
        self.horizontalLayout_6 = QHBoxLayout(self.icon_analyst)
        self.horizontalLayout_6.setObjectName(u"horizontalLayout_6")
        self.initial_analyst = QLabel(self.icon_analyst)
        self.initial_analyst.setObjectName(u"initial_analyst")
        self.initial_analyst.setMinimumSize(QSize(75, 75))
        self.initial_analyst.setMaximumSize(QSize(100, 100))
        font = QFont()
        font.setPointSize(18)
        self.initial_analyst.setFont(font)
        self.initial_analyst.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.horizontalLayout_6.addWidget(self.initial_analyst)

        self.line_analyst = QFrame(self.icon_analyst)
        self.line_analyst.setObjectName(u"line_analyst")
        self.line_analyst.setMinimumSize(QSize(30, 0))
        self.line_analyst.setMaximumSize(QSize(30, 16777215))
        self.line_analyst.setFrameShape(QFrame.Shape.HLine)
        self.line_analyst.setFrameShadow(QFrame.Shadow.Sunken)

        self.horizontalLayout_6.addWidget(self.line_analyst)


        self.horizontalLayout_3.addWidget(self.icon_analyst)

        self.widget_add_approval = QWidget(self.widget_analyst)
        self.widget_add_approval.setObjectName(u"widget_add_approval")
        self.horizontalLayout_4 = QHBoxLayout(self.widget_add_approval)
        self.horizontalLayout_4.setObjectName(u"horizontalLayout_4")
        self.comboBox_selection_approval = QComboBox(self.widget_add_approval)
        self.comboBox_selection_approval.setObjectName(u"comboBox_selection_approval")
        self.comboBox_selection_approval.setMinimumSize(QSize(200, 50))
        self.comboBox_selection_approval.setMaximumSize(QSize(16777215, 50))
        font1 = QFont()
        font1.setPointSize(12)
        self.comboBox_selection_approval.setFont(font1)

        self.horizontalLayout_4.addWidget(self.comboBox_selection_approval)

        self.btn_add_approval = QPushButton(self.widget_add_approval)
        self.btn_add_approval.setObjectName(u"btn_add_approval")
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.btn_add_approval.sizePolicy().hasHeightForWidth())
        self.btn_add_approval.setSizePolicy(sizePolicy)
        self.btn_add_approval.setMinimumSize(QSize(50, 50))
        self.btn_add_approval.setMaximumSize(QSize(50, 50))
        icon = QIcon()
        icon.addFile(u":/icons/add.svg", QSize(), QIcon.Mode.Normal, QIcon.State.Off)
        self.btn_add_approval.setIcon(icon)
        self.btn_add_approval.setIconSize(QSize(24, 24))

        self.horizontalLayout_4.addWidget(self.btn_add_approval)

        self.horizontalSpacer_2 = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_4.addItem(self.horizontalSpacer_2)


        self.horizontalLayout_3.addWidget(self.widget_add_approval)


        self.verticalLayout.addWidget(self.widget_analyst)

        self.widget_flow_contents = QWidget(StateSubmission)
        self.widget_flow_contents.setObjectName(u"widget_flow_contents")
        self.horizontalLayout = QHBoxLayout(self.widget_flow_contents)
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.widget_attached = QWidget(self.widget_flow_contents)
        self.widget_attached.setObjectName(u"widget_attached")
        self.verticalLayout_2 = QVBoxLayout(self.widget_attached)
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.tableView = QTableView(self.widget_attached)
        self.tableView.setObjectName(u"tableView")

        self.verticalLayout_2.addWidget(self.tableView)

        self.btn_attached = QPushButton(self.widget_attached)
        self.btn_attached.setObjectName(u"btn_attached")
        self.btn_attached.setMinimumSize(QSize(0, 50))
        font2 = QFont()
        font2.setPointSize(10)
        self.btn_attached.setFont(font2)

        self.verticalLayout_2.addWidget(self.btn_attached)


        self.horizontalLayout.addWidget(self.widget_attached)

        self.widget_comment = QWidget(self.widget_flow_contents)
        self.widget_comment.setObjectName(u"widget_comment")
        self.verticalLayout_3 = QVBoxLayout(self.widget_comment)
        self.verticalLayout_3.setObjectName(u"verticalLayout_3")
        self.plainTextEdit = QPlainTextEdit(self.widget_comment)
        self.plainTextEdit.setObjectName(u"plainTextEdit")

        self.verticalLayout_3.addWidget(self.plainTextEdit)

        self.widget_flow_actions = QWidget(self.widget_comment)
        self.widget_flow_actions.setObjectName(u"widget_flow_actions")
        self.horizontalLayout_2 = QHBoxLayout(self.widget_flow_actions)
        self.horizontalLayout_2.setObjectName(u"horizontalLayout_2")
        self.horizontalLayout_2.setContentsMargins(0, 0, 0, 0)
        self.horizontalSpacer = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_2.addItem(self.horizontalSpacer)

        self.btn_reclaim = QPushButton(self.widget_flow_actions)
        self.btn_reclaim.setObjectName(u"btn_reclaim")
        self.btn_reclaim.setMinimumSize(QSize(100, 50))
        self.btn_reclaim.setFont(font2)
        icon1 = QIcon()
        icon1.addFile(u":/icons/return.svg", QSize(), QIcon.Mode.Normal, QIcon.State.Off)
        self.btn_reclaim.setIcon(icon1)
        self.btn_reclaim.setIconSize(QSize(24, 24))

        self.horizontalLayout_2.addWidget(self.btn_reclaim)

        self.btn_send_back = QPushButton(self.widget_flow_actions)
        self.btn_send_back.setObjectName(u"btn_send_back")
        self.btn_send_back.setMinimumSize(QSize(100, 50))
        self.btn_send_back.setFont(font2)
        self.btn_send_back.setIcon(icon1)
        self.btn_send_back.setIconSize(QSize(24, 24))

        self.horizontalLayout_2.addWidget(self.btn_send_back)

        self.btn_approval_request = QPushButton(self.widget_flow_actions)
        self.btn_approval_request.setObjectName(u"btn_approval_request")
        self.btn_approval_request.setMinimumSize(QSize(100, 50))
        self.btn_approval_request.setFont(font2)
        icon2 = QIcon()
        icon2.addFile(u":/icons/send.svg", QSize(), QIcon.Mode.Normal, QIcon.State.Off)
        self.btn_approval_request.setIcon(icon2)
        self.btn_approval_request.setIconSize(QSize(24, 24))

        self.horizontalLayout_2.addWidget(self.btn_approval_request)

        self.btn_approval = QPushButton(self.widget_flow_actions)
        self.btn_approval.setObjectName(u"btn_approval")
        self.btn_approval.setMinimumSize(QSize(100, 50))
        self.btn_approval.setFont(font2)
        icon3 = QIcon()
        icon3.addFile(u":/icons/end.svg", QSize(), QIcon.Mode.Normal, QIcon.State.Off)
        self.btn_approval.setIcon(icon3)
        self.btn_approval.setIconSize(QSize(24, 24))

        self.horizontalLayout_2.addWidget(self.btn_approval)


        self.verticalLayout_3.addWidget(self.widget_flow_actions)


        self.horizontalLayout.addWidget(self.widget_comment)


        self.verticalLayout.addWidget(self.widget_flow_contents)

        self.widget_actions = QWidget(StateSubmission)
        self.widget_actions.setObjectName(u"widget_actions")
        self.horizontalLayout_5 = QHBoxLayout(self.widget_actions)
        self.horizontalLayout_5.setObjectName(u"horizontalLayout_5")
        self.horizontalSpacer_3 = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_5.addItem(self.horizontalSpacer_3)

        self.btn_back = QPushButton(self.widget_actions)
        self.btn_back.setObjectName(u"btn_back")
        self.btn_back.setMinimumSize(QSize(100, 50))
        self.btn_back.setMaximumSize(QSize(100, 50))

        self.horizontalLayout_5.addWidget(self.btn_back)

        self.horizontalSpacer_4 = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_5.addItem(self.horizontalSpacer_4)


        self.verticalLayout.addWidget(self.widget_actions)


        self.retranslateUi(StateSubmission)

        QMetaObject.connectSlotsByName(StateSubmission)
    # setupUi

    def retranslateUi(self, StateSubmission):
        StateSubmission.setWindowTitle(QCoreApplication.translate("StateSubmission", u"StateSubmission", None))
        self.initial_analyst.setText(QCoreApplication.translate("StateSubmission", u"\u5c71", None))
        self.btn_add_approval.setText("")
        self.btn_attached.setText(QCoreApplication.translate("StateSubmission", u"\u30d5\u30a1\u30a4\u30eb\u3092\u8ffd\u52a0", None))
        self.btn_reclaim.setText(QCoreApplication.translate("StateSubmission", u"\u53d6\u308a\u623b\u3057", None))
        self.btn_send_back.setText(QCoreApplication.translate("StateSubmission", u"\u5dee\u3057\u623b\u3057", None))
        self.btn_approval_request.setText(QCoreApplication.translate("StateSubmission", u"\u9001\u4fe1", None))
        self.btn_approval.setText(QCoreApplication.translate("StateSubmission", u"\u7d42\u4e86", None))
        self.btn_back.setText(QCoreApplication.translate("StateSubmission", u"\u623b\u308b", None))
    # retranslateUi

