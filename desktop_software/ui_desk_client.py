# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'desk_client.ui'
##
## Created by: Qt User Interface Compiler version 6.8.2
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
from PySide6.QtWidgets import (QApplication, QComboBox, QFrame, QGroupBox,
    QLabel, QLineEdit, QMainWindow, QMenuBar,
    QPushButton, QSizePolicy, QStatusBar, QTextEdit,
    QWidget)

class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        if not MainWindow.objectName():
            MainWindow.setObjectName(u"MainWindow")
        MainWindow.resize(800, 600)
        MainWindow.setStyleSheet(u"")
        self.centralwidget = QWidget(MainWindow)
        self.centralwidget.setObjectName(u"centralwidget")
        self.frame_notify_left = QFrame(self.centralwidget)
        self.frame_notify_left.setObjectName(u"frame_notify_left")
        self.frame_notify_left.setGeometry(QRect(10, 60, 491, 391))
        self.frame_notify_left.setStyleSheet(u"")
        self.frame_notify_left.setFrameShape(QFrame.StyledPanel)
        self.frame_notify_left.setFrameShadow(QFrame.Raised)
        self.frame_notify = QFrame(self.frame_notify_left)
        self.frame_notify.setObjectName(u"frame_notify")
        self.frame_notify.setGeometry(QRect(30, 10, 431, 331))
        self.frame_notify.setFrameShape(QFrame.StyledPanel)
        self.frame_notify.setFrameShadow(QFrame.Raised)
        self.lbl_notify_title = QLabel(self.frame_notify)
        self.lbl_notify_title.setObjectName(u"lbl_notify_title")
        self.lbl_notify_title.setGeometry(QRect(20, 60, 391, 41))
        font = QFont()
        self.lbl_notify_title.setFont(font)
        self.lbl_notify_title.setStyleSheet(u"color: white;                  /* \u767d\u5b57 */\n"
"font-size: 32px; ")
        self.lbl_notify_title.setAlignment(Qt.AlignCenter)
        self.lbl_notify_msg = QLabel(self.frame_notify)
        self.lbl_notify_msg.setObjectName(u"lbl_notify_msg")
        self.lbl_notify_msg.setGeometry(QRect(10, 160, 401, 41))
        self.lbl_notify_msg.setFont(font)
        self.lbl_notify_msg.setStyleSheet(u"color: white;                  /* \u767d\u5b57 */\n"
"font-size: 32px; ")
        self.lbl_notify_msg.setAlignment(Qt.AlignCenter)
        self.btn_close_notify = QPushButton(self.frame_notify)
        self.btn_close_notify.setObjectName(u"btn_close_notify")
        self.btn_close_notify.setGeometry(QRect(130, 250, 171, 61))
        self.btn_close_notify.setFont(font)
        self.btn_close_notify.setStyleSheet(u"QPushButton {\n"
"	background-color:#0678DD;\n"
"    color: white;                  /* \u767d\u5b57 */\n"
"    padding: 6px 12px;             /* \u5167\u8ddd */\n"
"    font-size: 32px;               /* \u5b57\u9ad4\u5927\u5c0f */\n"
"}\n"
"\n"
"QPushButton:hover {\n"
"    background-color: #1E70BF;     /* \u6ed1\u9f20\u79fb\u4e0a\u53bb\u8b8a\u8272 */\n"
"}\n"
"")
        self.frame_notify_right = QFrame(self.centralwidget)
        self.frame_notify_right.setObjectName(u"frame_notify_right")
        self.frame_notify_right.setGeometry(QRect(520, 40, 251, 411))
        self.frame_notify_right.setFrameShape(QFrame.StyledPanel)
        self.frame_notify_right.setFrameShadow(QFrame.Raised)
        self.groupBox = QGroupBox(self.frame_notify_right)
        self.groupBox.setObjectName(u"groupBox")
        self.groupBox.setGeometry(QRect(10, 10, 231, 401))
        self.groupBox.setStyleSheet(u"QGroupBox {\n"
"    border: 1px solid #3a3a3a;\n"
"    border-radius: 6px;\n"
"    margin-top: 10px;\n"
"    color: white;\n"
"    font-size: 20px;\n"
"}")
        self.btn_delete_task_db = QPushButton(self.groupBox)
        self.btn_delete_task_db.setObjectName(u"btn_delete_task_db")
        self.btn_delete_task_db.setGeometry(QRect(130, 340, 81, 31))
        self.btn_delete_task_db.setStyleSheet(u"QPushButton {\n"
"	background-color:#0678DD;\n"
"    color: white;                  /* \u767d\u5b57 */\n"
"    padding: 6px 12px;             /* \u5167\u8ddd */\n"
"    font-size: 14px;               /* \u5b57\u9ad4\u5927\u5c0f */\n"
"}\n"
"\n"
"QPushButton:hover {\n"
"    background-color: #1E70BF;     /* \u6ed1\u9f20\u79fb\u4e0a\u53bb\u8b8a\u8272 */\n"
"}\n"
"")
        self.btn_add_task_db = QPushButton(self.groupBox)
        self.btn_add_task_db.setObjectName(u"btn_add_task_db")
        self.btn_add_task_db.setGeometry(QRect(50, 260, 81, 31))
        self.btn_add_task_db.setStyleSheet(u"QPushButton {\n"
"	background-color:#0678DD;\n"
"    color: white;                  /* \u767d\u5b57 */\n"
"    padding: 6px 12px;             /* \u5167\u8ddd */\n"
"    font-size: 14px;               /* \u5b57\u9ad4\u5927\u5c0f */\n"
"}\n"
"\n"
"QPushButton:hover {\n"
"    background-color: #1E70BF;     /* \u6ed1\u9f20\u79fb\u4e0a\u53bb\u8b8a\u8272 */\n"
"}\n"
"")
        self.label_4 = QLabel(self.groupBox)
        self.label_4.setObjectName(u"label_4")
        self.label_4.setGeometry(QRect(50, 180, 61, 20))
        self.label_4.setStyleSheet(u"color: white;                  /* \u767d\u5b57 */\n"
"font-size: 16px; ")
        self.label_4.setAlignment(Qt.AlignCenter)
        self.label_6 = QLabel(self.groupBox)
        self.label_6.setObjectName(u"label_6")
        self.label_6.setGeometry(QRect(50, 310, 71, 21))
        self.label_6.setStyleSheet(u"color: white;                  /* \u767d\u5b57 */\n"
"font-size: 16px; ")
        self.cmb_start_point = QComboBox(self.groupBox)
        self.cmb_start_point.setObjectName(u"cmb_start_point")
        self.cmb_start_point.setGeometry(QRect(50, 90, 141, 22))
        self.cmb_start_point.setStyleSheet(u"QComboBox {\n"
"    color: white;                  /* \u767d\u5b57 */\n"
"    font-size: 14px;               /* \u5b57\u9ad4\u5927\u5c0f */\n"
"	background-color:#393939;\n"
"}\n"
"\n"
"QComboBox QAbstractItemView {\n"
"    background-color: #1E70BF;     /* \u6ed1\u9f20\u79fb\u4e0a\u53bb\u8b8a\u8272 */\n"
"}")
        self.cmb_start_point.setEditable(True)
        self.txt_delete_task_id = QLineEdit(self.groupBox)
        self.txt_delete_task_id.setObjectName(u"txt_delete_task_id")
        self.txt_delete_task_id.setGeometry(QRect(50, 350, 61, 20))
        self.txt_delete_task_id.setStyleSheet(u"QLineEdit {\n"
"    border: 1px solid #3a3a3a;\n"
"    border-radius: 1px;\n"
"    padding: 1px;\n"
"    background-color: #1e1e1e;\n"
"    color: white;\n"
"    font-size: 14px;\n"
"}\n"
"\n"
"QLineEdit:focus {\n"
"    border: 1px solid #4da3ff;\n"
"    background-color: #262626;\n"
"}")
        self.cmb_end_point = QComboBox(self.groupBox)
        self.cmb_end_point.setObjectName(u"cmb_end_point")
        self.cmb_end_point.setGeometry(QRect(50, 150, 141, 22))
        self.cmb_end_point.setStyleSheet(u"QComboBox {\n"
"    color: white;                  /* \u767d\u5b57 */\n"
"    font-size: 14px;               /* \u5b57\u9ad4\u5927\u5c0f */\n"
"	background-color:#393939;\n"
"}\n"
"\n"
"QComboBox QAbstractItemView {\n"
"    background-color: #1E70BF;     /* \u6ed1\u9f20\u79fb\u4e0a\u53bb\u8b8a\u8272 */\n"
"}")
        self.cmb_end_point.setEditable(True)
        self.cmb_mission = QComboBox(self.groupBox)
        self.cmb_mission.setObjectName(u"cmb_mission")
        self.cmb_mission.setGeometry(QRect(50, 220, 141, 22))
        self.cmb_mission.setStyleSheet(u"QComboBox {\n"
"    color: white;                  /* \u767d\u5b57 */\n"
"    font-size: 14px;               /* \u5b57\u9ad4\u5927\u5c0f */\n"
"	background-color:#393939;\n"
"}\n"
"\n"
"QComboBox QAbstractItemView {\n"
"    background-color: #1E70BF;     /* \u6ed1\u9f20\u79fb\u4e0a\u53bb\u8b8a\u8272 */\n"
"}")
        self.cmb_mission.setEditable(True)
        self.label_3 = QLabel(self.groupBox)
        self.label_3.setObjectName(u"label_3")
        self.label_3.setGeometry(QRect(40, 120, 61, 20))
        self.label_3.setStyleSheet(u"color: white;                  /* \u767d\u5b57 */\n"
"font-size: 16px; ")
        self.label_3.setAlignment(Qt.AlignCenter)
        self.label_2 = QLabel(self.groupBox)
        self.label_2.setObjectName(u"label_2")
        self.label_2.setGeometry(QRect(40, 50, 61, 20))
        self.label_2.setStyleSheet(u"color: white;                  /* \u767d\u5b57 */\n"
"font-size: 16px; ")
        self.label_2.setAlignment(Qt.AlignCenter)
        self.label_5 = QLabel(self.centralwidget)
        self.label_5.setObjectName(u"label_5")
        self.label_5.setGeometry(QRect(10, 10, 101, 21))
        font1 = QFont()
        font1.setPointSize(16)
        self.label_5.setFont(font1)
        self.txt_log = QTextEdit(self.centralwidget)
        self.txt_log.setObjectName(u"txt_log")
        self.txt_log.setGeometry(QRect(10, 500, 771, 51))
        self.txt_log.setStyleSheet(u"color: white;                  /* \u767d\u5b57 */\n"
"font-size: 13px; ")
        self.txt_log.setReadOnly(True)
        self.lbl_env = QLabel(self.centralwidget)
        self.lbl_env.setObjectName(u"lbl_env")
        self.lbl_env.setGeometry(QRect(120, 10, 101, 21))
        self.lbl_env.setFont(font1)
        self.lbl_status_v1 = QLabel(self.centralwidget)
        self.lbl_status_v1.setObjectName(u"lbl_status_v1")
        self.lbl_status_v1.setGeometry(QRect(530, 460, 111, 20))
        self.lbl_status_v1.setStyleSheet(u"color: white;                  /* \u767d\u5b57 */\n"
"font-size: 16px; ")
        self.lbl_status_v1.setAlignment(Qt.AlignCenter)
        self.lbl_status_v2 = QLabel(self.centralwidget)
        self.lbl_status_v2.setObjectName(u"lbl_status_v2")
        self.lbl_status_v2.setGeometry(QRect(650, 460, 111, 20))
        self.lbl_status_v2.setStyleSheet(u"color: white;                  /* \u767d\u5b57 */\n"
"font-size: 16px; ")
        self.lbl_status_v2.setAlignment(Qt.AlignCenter)
        MainWindow.setCentralWidget(self.centralwidget)
        self.menubar = QMenuBar(MainWindow)
        self.menubar.setObjectName(u"menubar")
        self.menubar.setGeometry(QRect(0, 0, 800, 21))
        MainWindow.setMenuBar(self.menubar)
        self.statusbar = QStatusBar(MainWindow)
        self.statusbar.setObjectName(u"statusbar")
        MainWindow.setStatusBar(self.statusbar)

        self.retranslateUi(MainWindow)

        QMetaObject.connectSlotsByName(MainWindow)
    # setupUi

    def retranslateUi(self, MainWindow):
        MainWindow.setWindowTitle(QCoreApplication.translate("MainWindow", u"MainWindow", None))
        self.lbl_notify_title.setText(QCoreApplication.translate("MainWindow", u"TextLabel", None))
        self.lbl_notify_msg.setText(QCoreApplication.translate("MainWindow", u"\u8eca\u8f1b\u62b5\u9054", None))
        self.btn_close_notify.setText(QCoreApplication.translate("MainWindow", u"\u95dc\u9589\u901a\u77e5", None))
        self.groupBox.setTitle(QCoreApplication.translate("MainWindow", u"\u6d3e\u9001\u4efb\u52d9", None))
        self.btn_delete_task_db.setText(QCoreApplication.translate("MainWindow", u"\u53d6\u6d88\u4efb\u52d9", None))
        self.btn_add_task_db.setText(QCoreApplication.translate("MainWindow", u"\u65b0\u589e\u4efb\u52d9", None))
        self.label_4.setText(QCoreApplication.translate("MainWindow", u"\u4efb\u52d9\u5167\u5bb9", None))
        self.label_6.setText(QCoreApplication.translate("MainWindow", u"\u4efb\u52d9 ID", None))
        self.label_3.setText(QCoreApplication.translate("MainWindow", u"\u76ee\u7684\u5730", None))
        self.label_2.setText(QCoreApplication.translate("MainWindow", u"\u8d77\u9ede", None))
        self.label_5.setText(QCoreApplication.translate("MainWindow", u"\u624b\u8853\u5ba407", None))
        self.lbl_env.setText(QCoreApplication.translate("MainWindow", u"\u5167\u74b0", None))
        self.lbl_status_v1.setText("")
        self.lbl_status_v2.setText("")
    # retranslateUi

