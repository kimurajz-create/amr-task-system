# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'main.ui'
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
from PySide6.QtWidgets import (QApplication, QCheckBox, QComboBox, QDoubleSpinBox,
    QFrame, QHBoxLayout, QHeaderView, QLabel,
    QLineEdit, QListWidget, QListWidgetItem, QMainWindow,
    QPlainTextEdit, QProgressBar, QPushButton, QSizePolicy,
    QSpacerItem, QStatusBar, QTableWidget, QTableWidgetItem,
    QTextEdit, QVBoxLayout, QWidget)
import resources_rc
import images_rc

class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        if not MainWindow.objectName():
            MainWindow.setObjectName(u"MainWindow")
        MainWindow.resize(1920, 1080)
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(MainWindow.sizePolicy().hasHeightForWidth())
        MainWindow.setSizePolicy(sizePolicy)
        MainWindow.setMinimumSize(QSize(1920, 1080))
        MainWindow.setMaximumSize(QSize(1920, 1080))
        font = QFont()
        font.setPointSize(9)
        MainWindow.setFont(font)
        MainWindow.setStyleSheet(u"background-color: rgb(0,0,0);")
        self.centralwidget = QWidget(MainWindow)
        self.centralwidget.setObjectName(u"centralwidget")
        self.centralwidget.setStyleSheet(u"")
        self.btn_StartMission = QPushButton(self.centralwidget)
        self.btn_StartMission.setObjectName(u"btn_StartMission")
        self.btn_StartMission.setGeometry(QRect(1740, 450, 31, 30))
        self.btn_StartMission.setStyleSheet(u"QPushButton {\n"
"	background-color: rgb(72, 72, 72);\n"
"    color: white;                  /* \u767d\u5b57 */\n"
"    border-radius: 10px;           /* \u5713\u89d2 */\n"
"    padding: 6px 12px;             /* \u5167\u8ddd */\n"
"    font-size: 24px;               /* \u5b57\u9ad4\u5927\u5c0f */\n"
"}\n"
"\n"
"QPushButton:hover {\n"
"    background-color: #1E70BF;     /* \u6ed1\u9f20\u79fb\u4e0a\u53bb\u8b8a\u8272 */\n"
"}")
        icon = QIcon()
        icon.addFile(u":/icons/icons/play.svg", QSize(), QIcon.Mode.Normal, QIcon.State.Off)
        self.btn_StartMission.setIcon(icon)
        self.btn_StopMission1 = QPushButton(self.centralwidget)
        self.btn_StopMission1.setObjectName(u"btn_StopMission1")
        self.btn_StopMission1.setGeometry(QRect(1780, 450, 31, 30))
        self.btn_StopMission1.setStyleSheet(u"QPushButton {\n"
"	background-color: rgb(72, 72, 72);\n"
"    color: white;                  /* \u767d\u5b57 */\n"
"    border-radius: 10px;           /* \u5713\u89d2 */\n"
"    padding: 6px 12px;             /* \u5167\u8ddd */\n"
"    font-size: 24px;               /* \u5b57\u9ad4\u5927\u5c0f */\n"
"}\n"
"\n"
"QPushButton:hover {\n"
"    background-color: #1E70BF;     /* \u6ed1\u9f20\u79fb\u4e0a\u53bb\u8b8a\u8272 */\n"
"}")
        icon1 = QIcon()
        icon1.addFile(u":/icons/icons/x-square.svg", QSize(), QIcon.Mode.Normal, QIcon.State.Off)
        self.btn_StopMission1.setIcon(icon1)
        self.lineEdit_PendingMission = QLineEdit(self.centralwidget)
        self.lineEdit_PendingMission.setObjectName(u"lineEdit_PendingMission")
        self.lineEdit_PendingMission.setEnabled(True)
        self.lineEdit_PendingMission.setGeometry(QRect(1220, 440, 224, 40))
        sizePolicy.setHeightForWidth(self.lineEdit_PendingMission.sizePolicy().hasHeightForWidth())
        self.lineEdit_PendingMission.setSizePolicy(sizePolicy)
        self.lineEdit_PendingMission.setMinimumSize(QSize(224, 40))
        self.lineEdit_PendingMission.setMaximumSize(QSize(224, 40))
        font1 = QFont()
        font1.setFamilies([u"Noto Sans TC"])
        self.lineEdit_PendingMission.setFont(font1)
        self.lineEdit_PendingMission.setStyleSheet(u"color: white;                  /* \u767d\u5b57 */\n"
"font-size: 32px; ")
        self.lineEdit_PendingMission.setFrame(False)
        self.lineEdit_PendingMission.setReadOnly(True)
        self.horizontalLayoutWidget_2 = QWidget(self.centralwidget)
        self.horizontalLayoutWidget_2.setObjectName(u"horizontalLayoutWidget_2")
        self.horizontalLayoutWidget_2.setGeometry(QRect(1220, 180, 559, 51))
        self.horizontalLayout_2 = QHBoxLayout(self.horizontalLayoutWidget_2)
        self.horizontalLayout_2.setSpacing(8)
        self.horizontalLayout_2.setObjectName(u"horizontalLayout_2")
        self.horizontalLayout_2.setContentsMargins(0, 0, 0, 0)
        self.label = QLabel(self.horizontalLayoutWidget_2)
        self.label.setObjectName(u"label")
        self.label.setMinimumSize(QSize(200, 24))
        self.label.setMaximumSize(QSize(200, 24))
        self.label.setFont(font1)
        self.label.setStyleSheet(u"color: white;                  /* \u767d\u5b57 */\n"
"font-size: 16px; ")
        self.label.setAlignment(Qt.AlignLeading|Qt.AlignLeft|Qt.AlignVCenter)

        self.horizontalLayout_2.addWidget(self.label)

        self.cmb_location = QComboBox(self.horizontalLayoutWidget_2)
        self.cmb_location.setObjectName(u"cmb_location")
        self.cmb_location.setMinimumSize(QSize(349, 40))
        self.cmb_location.setMaximumSize(QSize(349, 40))
        self.cmb_location.setFont(font1)
        self.cmb_location.setStyleSheet(u"QComboBox {\n"
"    color: white;                  /* \u767d\u5b57 */\n"
"    font-size: 16px;               /* \u5b57\u9ad4\u5927\u5c0f */\n"
"	background-color:#393939;\n"
"}\n"
"\n"
"QComboBox QAbstractItemView {\n"
"    background-color: #1E70BF;     /* \u6ed1\u9f20\u79fb\u4e0a\u53bb\u8b8a\u8272 */\n"
"}")
        self.cmb_location.setEditable(True)

        self.horizontalLayout_2.addWidget(self.cmb_location)

        self.horizontalLayoutWidget = QWidget(self.centralwidget)
        self.horizontalLayoutWidget.setObjectName(u"horizontalLayoutWidget")
        self.horizontalLayoutWidget.setGeometry(QRect(1220, 240, 561, 51))
        self.horizontalLayout = QHBoxLayout(self.horizontalLayoutWidget)
        self.horizontalLayout.setSpacing(8)
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.horizontalLayout.setContentsMargins(0, 0, 0, 0)
        self.label_3 = QLabel(self.horizontalLayoutWidget)
        self.label_3.setObjectName(u"label_3")
        self.label_3.setMinimumSize(QSize(200, 24))
        self.label_3.setMaximumSize(QSize(200, 24))
        self.label_3.setFont(font1)
        self.label_3.setStyleSheet(u"color: white;                  /* \u767d\u5b57 */\n"
"font-size: 16px; ")
        self.label_3.setAlignment(Qt.AlignLeading|Qt.AlignLeft|Qt.AlignVCenter)

        self.horizontalLayout.addWidget(self.label_3)

        self.cmb_mission = QComboBox(self.horizontalLayoutWidget)
        self.cmb_mission.setObjectName(u"cmb_mission")
        self.cmb_mission.setMinimumSize(QSize(0, 40))
        self.cmb_mission.setMaximumSize(QSize(600, 40))
        self.cmb_mission.setFont(font1)
        self.cmb_mission.setStyleSheet(u"QComboBox {\n"
"    color: white;                  /* \u767d\u5b57 */\n"
"    font-size: 16px;               /* \u5b57\u9ad4\u5927\u5c0f */\n"
"	background-color:#393939;\n"
"}\n"
"\n"
"QComboBox QAbstractItemView {\n"
"    background-color: #1E70BF;     /* \u6ed1\u9f20\u79fb\u4e0a\u53bb\u8b8a\u8272 */\n"
"}")
        self.cmb_mission.setEditable(True)
        self.cmb_mission.setInsertPolicy(QComboBox.InsertAtBottom)

        self.horizontalLayout.addWidget(self.cmb_mission)

        self.horizontalLayoutWidget_4 = QWidget(self.centralwidget)
        self.horizontalLayoutWidget_4.setObjectName(u"horizontalLayoutWidget_4")
        self.horizontalLayoutWidget_4.setGeometry(QRect(1220, 120, 561, 51))
        self.horizontalLayout_5 = QHBoxLayout(self.horizontalLayoutWidget_4)
        self.horizontalLayout_5.setSpacing(8)
        self.horizontalLayout_5.setObjectName(u"horizontalLayout_5")
        self.horizontalLayout_5.setContentsMargins(0, 0, 0, 0)
        self.label_6 = QLabel(self.horizontalLayoutWidget_4)
        self.label_6.setObjectName(u"label_6")
        self.label_6.setMinimumSize(QSize(200, 24))
        self.label_6.setMaximumSize(QSize(200, 24))
        self.label_6.setFont(font1)
        self.label_6.setStyleSheet(u"color: white;                  /* \u767d\u5b57 */\n"
"font-size: 16px; ")
        self.label_6.setAlignment(Qt.AlignLeading|Qt.AlignLeft|Qt.AlignVCenter)

        self.horizontalLayout_5.addWidget(self.label_6)

        self.cmb_location2 = QComboBox(self.horizontalLayoutWidget_4)
        self.cmb_location2.setObjectName(u"cmb_location2")
        self.cmb_location2.setMinimumSize(QSize(349, 40))
        self.cmb_location2.setMaximumSize(QSize(349, 40))
        self.cmb_location2.setFont(font1)
        self.cmb_location2.setStyleSheet(u"QComboBox {\n"
"    color: white;                  /* \u767d\u5b57 */\n"
"    font-size: 16px;               /* \u5b57\u9ad4\u5927\u5c0f */\n"
"	background-color:#393939;\n"
"}\n"
"\n"
"QComboBox QAbstractItemView {\n"
"    background-color: #1E70BF;     /* \u6ed1\u9f20\u79fb\u4e0a\u53bb\u8b8a\u8272 */\n"
"}")
        self.cmb_location2.setEditable(True)

        self.horizontalLayout_5.addWidget(self.cmb_location2)

        self.horizontalLayoutWidget_5 = QWidget(self.centralwidget)
        self.horizontalLayoutWidget_5.setObjectName(u"horizontalLayoutWidget_5")
        self.horizontalLayoutWidget_5.setGeometry(QRect(1220, 60, 661, 51))
        self.horizontalLayout_6 = QHBoxLayout(self.horizontalLayoutWidget_5)
        self.horizontalLayout_6.setObjectName(u"horizontalLayout_6")
        self.horizontalLayout_6.setContentsMargins(0, 0, 0, 0)
        self.label_Status_1 = QLabel(self.horizontalLayoutWidget_5)
        self.label_Status_1.setObjectName(u"label_Status_1")
        sizePolicy1 = QSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        sizePolicy1.setHorizontalStretch(0)
        sizePolicy1.setVerticalStretch(0)
        sizePolicy1.setHeightForWidth(self.label_Status_1.sizePolicy().hasHeightForWidth())
        self.label_Status_1.setSizePolicy(sizePolicy1)
        self.label_Status_1.setMinimumSize(QSize(300, 28))
        self.label_Status_1.setMaximumSize(QSize(240, 28))
        self.label_Status_1.setFont(font1)
        self.label_Status_1.setStyleSheet(u"color: white;                  /* \u767d\u5b57 */\n"
"font-size: 16px; ")
        self.label_Status_1.setAlignment(Qt.AlignCenter)

        self.horizontalLayout_6.addWidget(self.label_Status_1)

        self.horizontalSpacer_3 = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_6.addItem(self.horizontalSpacer_3)

        self.lineEdit_IP = QLineEdit(self.horizontalLayoutWidget_5)
        self.lineEdit_IP.setObjectName(u"lineEdit_IP")
        sizePolicy.setHeightForWidth(self.lineEdit_IP.sizePolicy().hasHeightForWidth())
        self.lineEdit_IP.setSizePolicy(sizePolicy)
        self.lineEdit_IP.setMinimumSize(QSize(104, 32))
        self.lineEdit_IP.setMaximumSize(QSize(104, 32))
        self.lineEdit_IP.setFont(font1)
        self.lineEdit_IP.setStyleSheet(u"color: white;                  /* \u767d\u5b57 */\n"
"font-size: 16px; ")
        self.lineEdit_IP.setFrame(False)

        self.horizontalLayout_6.addWidget(self.lineEdit_IP)

        self.btn_save_ip = QPushButton(self.horizontalLayoutWidget_5)
        self.btn_save_ip.setObjectName(u"btn_save_ip")
        sizePolicy.setHeightForWidth(self.btn_save_ip.sizePolicy().hasHeightForWidth())
        self.btn_save_ip.setSizePolicy(sizePolicy)
        self.btn_save_ip.setMinimumSize(QSize(32, 32))
        self.btn_save_ip.setMaximumSize(QSize(32, 32))
        self.btn_save_ip.setStyleSheet(u"QPushButton {\n"
"	background-color: rgb(72, 72, 72);\n"
"    color: white;                  /* \u767d\u5b57 */\n"
"    border-radius: 10px;           /* \u5713\u89d2 */\n"
"    padding: 6px 12px;             /* \u5167\u8ddd */\n"
"    font-size: 24px;               /* \u5b57\u9ad4\u5927\u5c0f */\n"
"}\n"
"\n"
"QPushButton:hover {\n"
"    background-color: #1E70BF;     /* \u6ed1\u9f20\u79fb\u4e0a\u53bb\u8b8a\u8272 */\n"
"}")
        self.btn_save_ip.setIcon(icon)

        self.horizontalLayout_6.addWidget(self.btn_save_ip)

        self.horizontalLayoutWidget_6 = QWidget(self.centralwidget)
        self.horizontalLayoutWidget_6.setObjectName(u"horizontalLayoutWidget_6")
        self.horizontalLayoutWidget_6.setGeometry(QRect(1220, 0, 491, 51))
        self.horizontalLayout_7 = QHBoxLayout(self.horizontalLayoutWidget_6)
        self.horizontalLayout_7.setObjectName(u"horizontalLayout_7")
        self.horizontalLayout_7.setContentsMargins(0, 0, 0, 0)
        self.lineEdit_MiR250_A = QLineEdit(self.horizontalLayoutWidget_6)
        self.lineEdit_MiR250_A.setObjectName(u"lineEdit_MiR250_A")
        sizePolicy.setHeightForWidth(self.lineEdit_MiR250_A.sizePolicy().hasHeightForWidth())
        self.lineEdit_MiR250_A.setSizePolicy(sizePolicy)
        self.lineEdit_MiR250_A.setMinimumSize(QSize(158, 48))
        self.lineEdit_MiR250_A.setMaximumSize(QSize(158, 48))
        self.lineEdit_MiR250_A.setFont(font1)
        self.lineEdit_MiR250_A.setStyleSheet(u"color: white;                  /* \u767d\u5b57 */\n"
"font-size: 32px; ")
        self.lineEdit_MiR250_A.setFrame(False)
        self.lineEdit_MiR250_A.setReadOnly(True)

        self.horizontalLayout_7.addWidget(self.lineEdit_MiR250_A)

        self.progressBar_battery = QProgressBar(self.horizontalLayoutWidget_6)
        self.progressBar_battery.setObjectName(u"progressBar_battery")
        sizePolicy.setHeightForWidth(self.progressBar_battery.sizePolicy().hasHeightForWidth())
        self.progressBar_battery.setSizePolicy(sizePolicy)
        self.progressBar_battery.setMinimumSize(QSize(81, 24))
        self.progressBar_battery.setMaximumSize(QSize(81, 24))
        font2 = QFont()
        self.progressBar_battery.setFont(font2)
        self.progressBar_battery.setStyleSheet(u"QProgressBar {    \n"
"    color:black;\n"
"	border: 2px solid grey;\n"
"    border-radius: 5px;\n"
"    text-align: center;\n"
"    font-size: 16px;\n"
"    height: 30px;\n"
"   \n"
"}\n"
"QProgressBar::chunk {\n"
"    background-color: #085508;\n"
"}")
        self.progressBar_battery.setValue(80)

        self.horizontalLayout_7.addWidget(self.progressBar_battery)

        self.btn_ChargeMission = QPushButton(self.horizontalLayoutWidget_6)
        self.btn_ChargeMission.setObjectName(u"btn_ChargeMission")
        sizePolicy.setHeightForWidth(self.btn_ChargeMission.sizePolicy().hasHeightForWidth())
        self.btn_ChargeMission.setSizePolicy(sizePolicy)
        self.btn_ChargeMission.setMinimumSize(QSize(109, 32))
        self.btn_ChargeMission.setMaximumSize(QSize(109, 32))
        self.btn_ChargeMission.setFont(font1)
        self.btn_ChargeMission.setTabletTracking(False)
        self.btn_ChargeMission.setStyleSheet(u"QPushButton {\n"
"    color: red;                  /* \u767d\u5b57 */\n"
"    border: 2px solid red;      /* \u908a\u6846\u6a23\u5f0f\uff1a2px \u5bec\uff0c\u5be6\u7dda\uff0c\u7d05\u8272 */\n"
"    padding: 6px 12px;             /* \u5167\u8ddd */\n"
"    font-size: 14px;               /* \u5b57\u9ad4\u5927\u5c0f */\n"
"	border-radius: 5px;         /* \u908a\u89d2\u5713\u5f27\u5ea6 */\n"
"}\n"
"\n"
"QPushButton:hover {\n"
"    background-color: #1E70BF;     /* \u6ed1\u9f20\u79fb\u4e0a\u53bb\u8b8a\u8272 */\n"
"}")
        self.btn_ChargeMission.setCheckable(False)

        self.horizontalLayout_7.addWidget(self.btn_ChargeMission)

        self.btn_Reset = QPushButton(self.horizontalLayoutWidget_6)
        self.btn_Reset.setObjectName(u"btn_Reset")
        sizePolicy.setHeightForWidth(self.btn_Reset.sizePolicy().hasHeightForWidth())
        self.btn_Reset.setSizePolicy(sizePolicy)
        self.btn_Reset.setMinimumSize(QSize(109, 32))
        self.btn_Reset.setMaximumSize(QSize(109, 32))
        self.btn_Reset.setFont(font1)
        self.btn_Reset.setStyleSheet(u"QPushButton {\n"
"    color: red;                  /* \u767d\u5b57 */\n"
"    border: 2px solid red;      /* \u908a\u6846\u6a23\u5f0f\uff1a2px \u5bec\uff0c\u5be6\u7dda\uff0c\u7d05\u8272 */\n"
"    padding: 6px 12px;             /* \u5167\u8ddd */\n"
"    font-size: 14px;               /* \u5b57\u9ad4\u5927\u5c0f */\n"
"	border-radius: 5px;         /* \u908a\u89d2\u5713\u5f27\u5ea6 */\n"
"}\n"
"\n"
"QPushButton:hover {\n"
"    background-color: #1E70BF;     /* \u6ed1\u9f20\u79fb\u4e0a\u53bb\u8b8a\u8272 */\n"
"}")

        self.horizontalLayout_7.addWidget(self.btn_Reset)

        self.btn_Emergency_Cut_Line = QPushButton(self.centralwidget)
        self.btn_Emergency_Cut_Line.setObjectName(u"btn_Emergency_Cut_Line")
        self.btn_Emergency_Cut_Line.setGeometry(QRect(1220, 370, 316, 48))
        sizePolicy.setHeightForWidth(self.btn_Emergency_Cut_Line.sizePolicy().hasHeightForWidth())
        self.btn_Emergency_Cut_Line.setSizePolicy(sizePolicy)
        self.btn_Emergency_Cut_Line.setMinimumSize(QSize(316, 48))
        self.btn_Emergency_Cut_Line.setMaximumSize(QSize(316, 48))
        self.btn_Emergency_Cut_Line.setFont(font1)
        self.btn_Emergency_Cut_Line.setStyleSheet(u"QPushButton {\n"
"    color: white;                  /* \u767d\u5b57 */\n"
"    padding: 6px 12px;             /* \u5167\u8ddd */\n"
"    font-size:18px;               /* \u5b57\u9ad4\u5927\u5c0f */\n"
"	border: 2px solid white;\n"
"}\n"
"\n"
" /* \n"
"QPushButton:hover {\n"
"    background-color: #1E70BF;     \u6ed1\u9f20\u79fb\u4e0a\u53bb\u8b8a\u8272 \n"
"}*/")
        self.btn_Add_New_Mission = QPushButton(self.centralwidget)
        self.btn_Add_New_Mission.setObjectName(u"btn_Add_New_Mission")
        self.btn_Add_New_Mission.setGeometry(QRect(1560, 370, 316, 48))
        sizePolicy.setHeightForWidth(self.btn_Add_New_Mission.sizePolicy().hasHeightForWidth())
        self.btn_Add_New_Mission.setSizePolicy(sizePolicy)
        self.btn_Add_New_Mission.setMinimumSize(QSize(316, 48))
        self.btn_Add_New_Mission.setMaximumSize(QSize(316, 48))
        self.btn_Add_New_Mission.setFont(font1)
        self.btn_Add_New_Mission.setStyleSheet(u"QPushButton {\n"
"	background-color:#0678DD;\n"
"    color: white;                  /* \u767d\u5b57 */\n"
"    padding: 6px 12px;             /* \u5167\u8ddd */\n"
"    font-size:18px;               /* \u5b57\u9ad4\u5927\u5c0f */\n"
"}\n"
" /* \n"
"QPushButton:hover {\n"
"    background-color: #1E70BF;     \u6ed1\u9f20\u79fb\u4e0a\u53bb\u8b8a\u8272 \n"
"}*/")
        self.frame_map = QFrame(self.centralwidget)
        self.frame_map.setObjectName(u"frame_map")
        self.frame_map.setGeometry(QRect(0, 0, 1168, 1048))
        sizePolicy.setHeightForWidth(self.frame_map.sizePolicy().hasHeightForWidth())
        self.frame_map.setSizePolicy(sizePolicy)
        self.frame_map.setMinimumSize(QSize(1168, 1048))
        self.frame_map.setMaximumSize(QSize(1168, 1048))
        self.frame_map.setStyleSheet(u"background-color:#FFFFFF")
        self.frame_map.setFrameShape(QFrame.StyledPanel)
        self.frame_map.setFrameShadow(QFrame.Raised)
        self.label_map_1 = QLabel(self.frame_map)
        self.label_map_1.setObjectName(u"label_map_1")
        self.label_map_1.setGeometry(QRect(20, 10, 1072, 608))
        sizePolicy.setHeightForWidth(self.label_map_1.sizePolicy().hasHeightForWidth())
        self.label_map_1.setSizePolicy(sizePolicy)
        self.label_map_1.setMinimumSize(QSize(1072, 608))
        self.label_map_1.setMaximumSize(QSize(1072, 608))
        self.label_map_1.setFont(font2)
        self.label_map_1.setStyleSheet(u"border: 2px solid #2C3E50;")
        self.label_map_1.setScaledContents(True)
        self.label_map_1.setAlignment(Qt.AlignCenter)
        self.chb_map = QCheckBox(self.frame_map)
        self.chb_map.setObjectName(u"chb_map")
        self.chb_map.setGeometry(QRect(760, 636, 141, 31))
        self.chb_map.setFont(font1)
        self.chb_map.setStyleSheet(u"/* \u2705 CheckBox \u6587\u5b57\u6a23\u5f0f */\n"
"QCheckBox {\n"
"    background-color: rgb(72, 72, 72);\n"
"    color: white;                  /* \u767d\u5b57 */\n"
"    border-radius: 10px;           /* \u5713\u89d2 */\n"
"    padding: 6px 12px;             /* \u5167\u8ddd */\n"
"    font-size:14px;               /* \u5b57\u9ad4\u5927\u5c0f */\n"
"    spacing: 10px; /* \u2705 \u63a8\u85a6\u52a0\u4e0a spacing\uff0c\u8b93\u6846\u8207\u6587\u5b57\u4e0d\u6703\u592a\u64e0 */\n"
"}\n"
"\n"
"/* \u2705 CheckBox \u6846\u6846\u5927\u5c0f + \u672a\u52fe\u9078\u6642\u984f\u8272 */\n"
"QCheckBox::indicator {\n"
"    width: 20px;\n"
"    height: 20px;\n"
"    background-color:transparent;   /* \u6c92\u52fe\u9078\u6642\u7684\u6846\u8272 */\n"
"    border: 1px solid white;     /* \u52a0\u908a\u6846\u8b93\u5b83\u66f4\u6e05\u695a */\n"
"    border-radius: 4px;          /* \u5713\u89d2\uff08\u9078\u914d\uff09 */\n"
"}\n"
"\n"
"/* \u2705 CheckBox \u52fe\u9078\u6642\u984f\u8272 */\n"
"QCheckBox::indicator:checked {\n"
"    back"
                        "ground-color:white; \n"
"    image: url(:/icons/icons/check.svg);\n"
"}\n"
"\n"
"")
        self.chb_map.setIconSize(QSize(20, 20))
        self.btn_SentRobotTo = QPushButton(self.frame_map)
        self.btn_SentRobotTo.setObjectName(u"btn_SentRobotTo")
        self.btn_SentRobotTo.setGeometry(QRect(920, 636, 36, 31))
        self.btn_SentRobotTo.setMinimumSize(QSize(36, 31))
        self.btn_SentRobotTo.setMaximumSize(QSize(36, 31))
        self.btn_SentRobotTo.setStyleSheet(u"QPushButton {\n"
"	background-color: rgb(72, 72, 72);\n"
"    color: white;                  /* \u767d\u5b57 */\n"
"    border-radius: 10px;           /* \u5713\u89d2 */\n"
"    padding: 6px 12px;             /* \u5167\u8ddd */\n"
"    font-size: 24px;               /* \u5b57\u9ad4\u5927\u5c0f */\n"
"}\n"
"\n"
"QPushButton:hover {\n"
"    background-color: #1E70BF;     /* \u6ed1\u9f20\u79fb\u4e0a\u53bb\u8b8a\u8272 */\n"
"}")
        self.btn_SentRobotTo.setIcon(icon)
        self.horizontalLayoutWidget_7 = QWidget(self.frame_map)
        self.horizontalLayoutWidget_7.setObjectName(u"horizontalLayoutWidget_7")
        self.horizontalLayoutWidget_7.setGeometry(QRect(190, 636, 91, 31))
        self.horizontalLayout_4 = QHBoxLayout(self.horizontalLayoutWidget_7)
        self.horizontalLayout_4.setObjectName(u"horizontalLayout_4")
        self.horizontalLayout_4.setContentsMargins(0, 0, 0, 0)
        self.lineEdit_MessageAnnounce_6 = QLineEdit(self.horizontalLayoutWidget_7)
        self.lineEdit_MessageAnnounce_6.setObjectName(u"lineEdit_MessageAnnounce_6")
        sizePolicy.setHeightForWidth(self.lineEdit_MessageAnnounce_6.sizePolicy().hasHeightForWidth())
        self.lineEdit_MessageAnnounce_6.setSizePolicy(sizePolicy)
        self.lineEdit_MessageAnnounce_6.setMinimumSize(QSize(12, 16))
        self.lineEdit_MessageAnnounce_6.setMaximumSize(QSize(12, 16))
        self.lineEdit_MessageAnnounce_6.setFont(font1)
        self.lineEdit_MessageAnnounce_6.setLayoutDirection(Qt.RightToLeft)
        self.lineEdit_MessageAnnounce_6.setStyleSheet(u"color: black;                  /* \u767d\u5b57 */\n"
"font-size: 12px; \n"
"background-color:#42BE57")
        self.lineEdit_MessageAnnounce_6.setFrame(False)
        self.lineEdit_MessageAnnounce_6.setAlignment(Qt.AlignBottom|Qt.AlignHCenter)
        self.lineEdit_MessageAnnounce_6.setReadOnly(True)

        self.horizontalLayout_4.addWidget(self.lineEdit_MessageAnnounce_6)

        self.lineEdit_current_tasks = QLineEdit(self.horizontalLayoutWidget_7)
        self.lineEdit_current_tasks.setObjectName(u"lineEdit_current_tasks")
        sizePolicy.setHeightForWidth(self.lineEdit_current_tasks.sizePolicy().hasHeightForWidth())
        self.lineEdit_current_tasks.setSizePolicy(sizePolicy)
        self.lineEdit_current_tasks.setMinimumSize(QSize(68, 24))
        self.lineEdit_current_tasks.setMaximumSize(QSize(64, 24))
        self.lineEdit_current_tasks.setFont(font1)
        self.lineEdit_current_tasks.setStyleSheet(u"color: black;                  /* \u767d\u5b57 */\n"
"font-size: 16px; ")
        self.lineEdit_current_tasks.setFrame(False)
        self.lineEdit_current_tasks.setAlignment(Qt.AlignLeading|Qt.AlignLeft|Qt.AlignVCenter)

        self.horizontalLayout_4.addWidget(self.lineEdit_current_tasks)

        self.horizontalLayoutWidget_8 = QWidget(self.frame_map)
        self.horizontalLayoutWidget_8.setObjectName(u"horizontalLayoutWidget_8")
        self.horizontalLayoutWidget_8.setGeometry(QRect(290, 636, 91, 31))
        self.horizontalLayout_8 = QHBoxLayout(self.horizontalLayoutWidget_8)
        self.horizontalLayout_8.setObjectName(u"horizontalLayout_8")
        self.horizontalLayout_8.setContentsMargins(0, 0, 0, 0)
        self.lineEdit_MessageAnnounce_7 = QLineEdit(self.horizontalLayoutWidget_8)
        self.lineEdit_MessageAnnounce_7.setObjectName(u"lineEdit_MessageAnnounce_7")
        sizePolicy.setHeightForWidth(self.lineEdit_MessageAnnounce_7.sizePolicy().hasHeightForWidth())
        self.lineEdit_MessageAnnounce_7.setSizePolicy(sizePolicy)
        self.lineEdit_MessageAnnounce_7.setMinimumSize(QSize(12, 16))
        self.lineEdit_MessageAnnounce_7.setMaximumSize(QSize(12, 16))
        self.lineEdit_MessageAnnounce_7.setFont(font1)
        self.lineEdit_MessageAnnounce_7.setLayoutDirection(Qt.RightToLeft)
        self.lineEdit_MessageAnnounce_7.setStyleSheet(u"color: black;                  /* \u767d\u5b57 */\n"
"font-size: 12px; \n"
"background-color:#FF832B\n"
"")
        self.lineEdit_MessageAnnounce_7.setFrame(False)
        self.lineEdit_MessageAnnounce_7.setAlignment(Qt.AlignBottom|Qt.AlignHCenter)
        self.lineEdit_MessageAnnounce_7.setReadOnly(True)

        self.horizontalLayout_8.addWidget(self.lineEdit_MessageAnnounce_7)

        self.lineEdit_pending_tasks = QLineEdit(self.horizontalLayoutWidget_8)
        self.lineEdit_pending_tasks.setObjectName(u"lineEdit_pending_tasks")
        sizePolicy.setHeightForWidth(self.lineEdit_pending_tasks.sizePolicy().hasHeightForWidth())
        self.lineEdit_pending_tasks.setSizePolicy(sizePolicy)
        self.lineEdit_pending_tasks.setMinimumSize(QSize(68, 24))
        self.lineEdit_pending_tasks.setMaximumSize(QSize(68, 24))
        self.lineEdit_pending_tasks.setFont(font1)
        self.lineEdit_pending_tasks.setStyleSheet(u"color: black;                  /* \u767d\u5b57 */\n"
"font-size: 16px; ")
        self.lineEdit_pending_tasks.setFrame(False)
        self.lineEdit_pending_tasks.setAlignment(Qt.AlignLeading|Qt.AlignLeft|Qt.AlignVCenter)

        self.horizontalLayout_8.addWidget(self.lineEdit_pending_tasks)

        self.verticalLayoutWidget = QWidget(self.frame_map)
        self.verticalLayoutWidget.setObjectName(u"verticalLayoutWidget")
        self.verticalLayoutWidget.setGeometry(QRect(20, 730, 1121, 281))
        self.verticalLayout_msg = QVBoxLayout(self.verticalLayoutWidget)
        self.verticalLayout_msg.setObjectName(u"verticalLayout_msg")
        self.verticalLayout_msg.setContentsMargins(0, 0, 0, 0)
        self.listWidget_msg = QListWidget(self.verticalLayoutWidget)
        self.listWidget_msg.setObjectName(u"listWidget_msg")
        self.listWidget_msg.setMinimumSize(QSize(1072, 0))
        self.listWidget_msg.setMaximumSize(QSize(1072, 16777215))
        self.listWidget_msg.setStyleSheet(u"QListWidget#listWidget_msg {\n"
"        /* \u8a2d\u5b9a\u5916\u570d\u908a\u6846\u7dda */\n"
"        border: 1px solid blue; \n"
"    }")

        self.verticalLayout_msg.addWidget(self.listWidget_msg)

        self.lineEdit_MessageAnnounce = QLineEdit(self.frame_map)
        self.lineEdit_MessageAnnounce.setObjectName(u"lineEdit_MessageAnnounce")
        self.lineEdit_MessageAnnounce.setGeometry(QRect(20, 689, 76, 24))
        sizePolicy.setHeightForWidth(self.lineEdit_MessageAnnounce.sizePolicy().hasHeightForWidth())
        self.lineEdit_MessageAnnounce.setSizePolicy(sizePolicy)
        self.lineEdit_MessageAnnounce.setMinimumSize(QSize(76, 24))
        self.lineEdit_MessageAnnounce.setMaximumSize(QSize(76, 24))
        self.lineEdit_MessageAnnounce.setFont(font1)
        self.lineEdit_MessageAnnounce.setStyleSheet(u"color: black;                  /* \u767d\u5b57 */\n"
"font-size: 18px; ")
        self.lineEdit_MessageAnnounce.setFrame(False)
        self.lineEdit_MessageAnnounce.setAlignment(Qt.AlignLeading|Qt.AlignLeft|Qt.AlignVCenter)
        self.lineEdit_MessageAnnounce.setReadOnly(True)
        self.label_rp_1 = QLabel(self.frame_map)
        self.label_rp_1.setObjectName(u"label_rp_1")
        self.label_rp_1.setGeometry(QRect(290, 230, 18, 26))
        self.label_rp_1.setMinimumSize(QSize(18, 26))
        self.label_rp_1.setMaximumSize(QSize(18, 26))
        font3 = QFont()
        font3.setBold(False)
        self.label_rp_1.setFont(font3)
        self.label_rp_1.setStyleSheet(u"QLabel#label_rp_1 {\n"
"    /* 1. \u5927\u5c0f\u548c\u908a\u8ddd (\u5c07 QLabel \u8996\u70ba 'Frame 15') \u9019\u4e9b\u7684\u6a23\u5f0f\u4f3c\u4e4e\u88ab\u7a0b\u5f0f\u9650\u5236\u4e86*/\n"
"    /* \u6ce8\u610f\uff1aQt Widgets \u7684\u5927\u5c0f\u901a\u5e38\u7531\u5167\u5bb9\u6216 Layout \u6c7a\u5b9a\uff0c\u9019\u88e1\u8a2d\u5b9a\u4e00\u500b\u57fa\u7dda */\n"
"    min-width: 12px;\n"
"    max-width: 12px;\n"
"    min-height: 20px;\n"
"    max-height: 20px;\n"
"\n"
"    /* 2. \u908a\u6846 (Borders) */\n"
"    /* \u5713\u89d2 (Radius: 2px) */\n"
"    border-radius: 2px;\n"
"    /* \u908a\u6846\u7dda (Border: 1px) + \u984f\u8272 (#525252) */\n"
"    border: 1px solid #525252;\n"
"    \n"
"    /* 3. \u984f\u8272 (Colors) - \u4f5c\u70ba\u80cc\u666f\u8272 */\n"
"    /* \u9019\u88e1\u5c07 #33B1FF \u8a2d\u5b9a\u70ba\u9810\u8a2d\u80cc\u666f\u8272 */\n"
"    background-color: #33B1FF;\n"
"\n"
"    /* 4. \u5167\u908a\u8ddd (Padding: 2px) */\n"
"    /* \u9019\u6703\u5f71\u97ff Label \u5167\u5bb9\uff08\u6587\u5b57\u6216\u5716"
                        "\u7247\uff09\u8207\u908a\u6846\u7684\u8ddd\u96e2 */\n"
"    padding: 2px; \n"
"    \n"
"    /* 5. \u6587\u5b57\u5c0d\u9f4a (Inner alignment) */\n"
"    /* \u5047\u8a2d 'Inner alignment' \u662f\u6307\u5167\u5bb9\u7f6e\u4e2d */\n"
"    text-align: center; \n"
"    \n"
"    /* Flow \u548c Gap \u5c6c\u6027\uff08\u5982 Vertical, 10px\uff09\u5c6c\u65bc Layout \u7ba1\u7406\u5668\u7684\u8077\u8cac\uff0cQSS \u7121\u6cd5\u76f4\u63a5\u63a7\u5236 */\n"
"}\n"
"\n"
"/* \u8a2d\u5b9a\u6240\u6709 QToolTip \u7684\u6a23\u5f0f */\n"
"QToolTip {\n"
"    background-color: black;  /* \u80cc\u666f\u984f\u8272\u8a2d\u70ba\u9ed1\u8272 */\n"
"    color: white;             /* \u6587\u5b57\u984f\u8272\u8a2d\u70ba\u767d\u8272 */\n"
"    border: 1px solid darkgray; /* \u908a\u6846 */\n"
"    border-radius: 4px;       /* \u5713\u89d2 */\n"
"    padding: 4px;             /* \u5167\u908a\u8ddd */\n"
"}")
        self.label_rp_1.setAlignment(Qt.AlignCenter)
        self.label_rp_2 = QLabel(self.frame_map)
        self.label_rp_2.setObjectName(u"label_rp_2")
        self.label_rp_2.setGeometry(QRect(290, 310, 18, 26))
        self.label_rp_2.setFont(font3)
        self.label_rp_2.setStyleSheet(u"QLabel#label_rp_2 {\n"
"    /* 1. \u5927\u5c0f\u548c\u908a\u8ddd (\u5c07 QLabel \u8996\u70ba 'Frame 15') */\n"
"    /* \u6ce8\u610f\uff1aQt Widgets \u7684\u5927\u5c0f\u901a\u5e38\u7531\u5167\u5bb9\u6216 Layout \u6c7a\u5b9a\uff0c\u9019\u88e1\u8a2d\u5b9a\u4e00\u500b\u57fa\u7dda */\n"
"    min-width: 12px;\n"
"    max-width: 12px;\n"
"    min-height: 20px;\n"
"    max-height: 20px;\n"
"\n"
"    /* 2. \u908a\u6846 (Borders) */\n"
"    /* \u5713\u89d2 (Radius: 2px) */\n"
"    border-radius: 2px;\n"
"    /* \u908a\u6846\u7dda (Border: 1px) + \u984f\u8272 (#525252) */\n"
"    border: 1px solid #525252;\n"
"    \n"
"    /* 3. \u984f\u8272 (Colors) - \u4f5c\u70ba\u80cc\u666f\u8272 */\n"
"    /* \u9019\u88e1\u5c07 #33B1FF \u8a2d\u5b9a\u70ba\u9810\u8a2d\u80cc\u666f\u8272 */\n"
"    background-color: #33B1FF;\n"
"\n"
"    /* 4. \u5167\u908a\u8ddd (Padding: 2px) */\n"
"    /* \u9019\u6703\u5f71\u97ff Label \u5167\u5bb9\uff08\u6587\u5b57\u6216\u5716\u7247\uff09\u8207\u908a\u6846\u7684\u8ddd\u96e2 */\n"
"    padding: 2px; \n"
""
                        "    \n"
"    /* 5. \u6587\u5b57\u5c0d\u9f4a (Inner alignment) */\n"
"    /* \u5047\u8a2d 'Inner alignment' \u662f\u6307\u5167\u5bb9\u7f6e\u4e2d */\n"
"    text-align: center; \n"
"    \n"
"    /* Flow \u548c Gap \u5c6c\u6027\uff08\u5982 Vertical, 10px\uff09\u5c6c\u65bc Layout \u7ba1\u7406\u5668\u7684\u8077\u8cac\uff0cQSS \u7121\u6cd5\u76f4\u63a5\u63a7\u5236 */\n"
"}\n"
"\n"
"/* \u8a2d\u5b9a\u6240\u6709 QToolTip \u7684\u6a23\u5f0f */\n"
"QToolTip {\n"
"    background-color: black;  /* \u80cc\u666f\u984f\u8272\u8a2d\u70ba\u9ed1\u8272 */\n"
"    color: white;             /* \u6587\u5b57\u984f\u8272\u8a2d\u70ba\u767d\u8272 */\n"
"    border: 1px solid darkgray; /* \u908a\u6846 */\n"
"    border-radius: 4px;       /* \u5713\u89d2 */\n"
"    padding: 4px;             /* \u5167\u908a\u8ddd */\n"
"}")
        self.label_rp_2.setAlignment(Qt.AlignCenter)
        self.label_rp_3 = QLabel(self.frame_map)
        self.label_rp_3.setObjectName(u"label_rp_3")
        self.label_rp_3.setGeometry(QRect(290, 410, 18, 26))
        sizePolicy2 = QSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred)
        sizePolicy2.setHorizontalStretch(0)
        sizePolicy2.setVerticalStretch(0)
        sizePolicy2.setHeightForWidth(self.label_rp_3.sizePolicy().hasHeightForWidth())
        self.label_rp_3.setSizePolicy(sizePolicy2)
        self.label_rp_3.setMinimumSize(QSize(18, 26))
        self.label_rp_3.setMaximumSize(QSize(18, 26))
        self.label_rp_3.setFont(font3)
        self.label_rp_3.setStyleSheet(u"QLabel#label_rp_3 {\n"
"    /* 1. \u5927\u5c0f\u548c\u908a\u8ddd (\u5c07 QLabel \u8996\u70ba 'Frame 15') */\n"
"    /* \u6ce8\u610f\uff1aQt Widgets \u7684\u5927\u5c0f\u901a\u5e38\u7531\u5167\u5bb9\u6216 Layout \u6c7a\u5b9a\uff0c\u9019\u88e1\u8a2d\u5b9a\u4e00\u500b\u57fa\u7dda */\n"
"    min-width: 12px;\n"
"    max-width: 12px;\n"
"    min-height: 20px;\n"
"    max-height: 20px;\n"
"\n"
"    /* 2. \u908a\u6846 (Borders) */\n"
"    /* \u5713\u89d2 (Radius: 2px) */\n"
"    border-radius: 2px;\n"
"    /* \u908a\u6846\u7dda (Border: 1px) + \u984f\u8272 (#525252) */\n"
"    border: 1px solid #525252;\n"
"    \n"
"    /* 3. \u984f\u8272 (Colors) - \u4f5c\u70ba\u80cc\u666f\u8272 */\n"
"    /* \u9019\u88e1\u5c07 #33B1FF \u8a2d\u5b9a\u70ba\u9810\u8a2d\u80cc\u666f\u8272 */\n"
"    background-color: #33B1FF;\n"
"\n"
"    /* 4. \u5167\u908a\u8ddd (Padding: 2px) */\n"
"    /* \u9019\u6703\u5f71\u97ff Label \u5167\u5bb9\uff08\u6587\u5b57\u6216\u5716\u7247\uff09\u8207\u908a\u6846\u7684\u8ddd\u96e2 */\n"
"    padding: 2px; \n"
""
                        "    \n"
"    /* 5. \u6587\u5b57\u5c0d\u9f4a (Inner alignment) */\n"
"    /* \u5047\u8a2d 'Inner alignment' \u662f\u6307\u5167\u5bb9\u7f6e\u4e2d */\n"
"    text-align: center; \n"
"    \n"
"    /* Flow \u548c Gap \u5c6c\u6027\uff08\u5982 Vertical, 10px\uff09\u5c6c\u65bc Layout \u7ba1\u7406\u5668\u7684\u8077\u8cac\uff0cQSS \u7121\u6cd5\u76f4\u63a5\u63a7\u5236 */\n"
"}\n"
"\n"
"/* \u8a2d\u5b9a\u6240\u6709 QToolTip \u7684\u6a23\u5f0f */\n"
"QToolTip {\n"
"    background-color: black;  /* \u80cc\u666f\u984f\u8272\u8a2d\u70ba\u9ed1\u8272 */\n"
"    color: white;             /* \u6587\u5b57\u984f\u8272\u8a2d\u70ba\u767d\u8272 */\n"
"    border: 1px solid darkgray; /* \u908a\u6846 */\n"
"    border-radius: 4px;       /* \u5713\u89d2 */\n"
"    padding: 4px;             /* \u5167\u908a\u8ddd */\n"
"}")
        self.label_rp_3.setAlignment(Qt.AlignCenter)
        self.label_rp_4 = QLabel(self.frame_map)
        self.label_rp_4.setObjectName(u"label_rp_4")
        self.label_rp_4.setGeometry(QRect(410, 470, 26, 18))
        sizePolicy2.setHeightForWidth(self.label_rp_4.sizePolicy().hasHeightForWidth())
        self.label_rp_4.setSizePolicy(sizePolicy2)
        self.label_rp_4.setFont(font3)
        self.label_rp_4.setStyleSheet(u"QLabel#label_rp_4 {\n"
"    /* 1. \u5927\u5c0f\u548c\u908a\u8ddd (\u5c07 QLabel \u8996\u70ba 'Frame 15') */\n"
"    /* \u6ce8\u610f\uff1aQt Widgets \u7684\u5927\u5c0f\u901a\u5e38\u7531\u5167\u5bb9\u6216 Layout \u6c7a\u5b9a\uff0c\u9019\u88e1\u8a2d\u5b9a\u4e00\u500b\u57fa\u7dda */\n"
"    min-width: 20px;\n"
"    max-width: 20px;\n"
"    min-height: 12px;\n"
"    max-height: 12px;\n"
"\n"
"    /* 2. \u908a\u6846 (Borders) */\n"
"    /* \u5713\u89d2 (Radius: 2px) */\n"
"    border-radius: 2px;\n"
"    /* \u908a\u6846\u7dda (Border: 1px) + \u984f\u8272 (#525252) */\n"
"    border: 1px solid #525252;\n"
"    \n"
"    /* 3. \u984f\u8272 (Colors) - \u4f5c\u70ba\u80cc\u666f\u8272 */\n"
"    /* \u9019\u88e1\u5c07 #33B1FF \u8a2d\u5b9a\u70ba\u9810\u8a2d\u80cc\u666f\u8272 */\n"
"    background-color: #33B1FF;\n"
"\n"
"    /* 4. \u5167\u908a\u8ddd (Padding: 2px) */\n"
"    /* \u9019\u6703\u5f71\u97ff Label \u5167\u5bb9\uff08\u6587\u5b57\u6216\u5716\u7247\uff09\u8207\u908a\u6846\u7684\u8ddd\u96e2 */\n"
"    padding: 2px; \n"
""
                        "    \n"
"    /* 5. \u6587\u5b57\u5c0d\u9f4a (Inner alignment) */\n"
"    /* \u5047\u8a2d 'Inner alignment' \u662f\u6307\u5167\u5bb9\u7f6e\u4e2d */\n"
"    text-align: center; \n"
"    \n"
"    /* Flow \u548c Gap \u5c6c\u6027\uff08\u5982 Vertical, 10px\uff09\u5c6c\u65bc Layout \u7ba1\u7406\u5668\u7684\u8077\u8cac\uff0cQSS \u7121\u6cd5\u76f4\u63a5\u63a7\u5236 */\n"
"}\n"
"/* \u8a2d\u5b9a\u6240\u6709 QToolTip \u7684\u6a23\u5f0f */\n"
"QToolTip {\n"
"    background-color: black;  /* \u80cc\u666f\u984f\u8272\u8a2d\u70ba\u9ed1\u8272 */\n"
"    color: white;             /* \u6587\u5b57\u984f\u8272\u8a2d\u70ba\u767d\u8272 */\n"
"    border: 1px solid darkgray; /* \u908a\u6846 */\n"
"    border-radius: 4px;       /* \u5713\u89d2 */\n"
"    padding: 4px;             /* \u5167\u908a\u8ddd */\n"
"}")
        self.label_rp_4.setAlignment(Qt.AlignCenter)
        self.label_rp_5 = QLabel(self.frame_map)
        self.label_rp_5.setObjectName(u"label_rp_5")
        self.label_rp_5.setGeometry(QRect(510, 470, 26, 18))
        sizePolicy2.setHeightForWidth(self.label_rp_5.sizePolicy().hasHeightForWidth())
        self.label_rp_5.setSizePolicy(sizePolicy2)
        self.label_rp_5.setFont(font3)
        self.label_rp_5.setStyleSheet(u"QLabel#label_rp_5 {\n"
"    /* 1. \u5927\u5c0f\u548c\u908a\u8ddd (\u5c07 QLabel \u8996\u70ba 'Frame 15') */\n"
"    /* \u6ce8\u610f\uff1aQt Widgets \u7684\u5927\u5c0f\u901a\u5e38\u7531\u5167\u5bb9\u6216 Layout \u6c7a\u5b9a\uff0c\u9019\u88e1\u8a2d\u5b9a\u4e00\u500b\u57fa\u7dda */\n"
"    min-width: 20px;\n"
"    max-width: 20px;\n"
"    min-height: 12px;\n"
"    max-height: 12px;\n"
"\n"
"    /* 2. \u908a\u6846 (Borders) */\n"
"    /* \u5713\u89d2 (Radius: 2px) */\n"
"    border-radius: 2px;\n"
"    /* \u908a\u6846\u7dda (Border: 1px) + \u984f\u8272 (#525252) */\n"
"    border: 1px solid #525252;\n"
"    \n"
"    /* 3. \u984f\u8272 (Colors) - \u4f5c\u70ba\u80cc\u666f\u8272 */\n"
"    /* \u9019\u88e1\u5c07 #33B1FF \u8a2d\u5b9a\u70ba\u9810\u8a2d\u80cc\u666f\u8272 */\n"
"    background-color: #33B1FF;\n"
"\n"
"    /* 4. \u5167\u908a\u8ddd (Padding: 2px) */\n"
"    /* \u9019\u6703\u5f71\u97ff Label \u5167\u5bb9\uff08\u6587\u5b57\u6216\u5716\u7247\uff09\u8207\u908a\u6846\u7684\u8ddd\u96e2 */\n"
"    padding: 2px; \n"
""
                        "    \n"
"    /* 5. \u6587\u5b57\u5c0d\u9f4a (Inner alignment) */\n"
"    /* \u5047\u8a2d 'Inner alignment' \u662f\u6307\u5167\u5bb9\u7f6e\u4e2d */\n"
"    text-align: center; \n"
"    \n"
"    /* Flow \u548c Gap \u5c6c\u6027\uff08\u5982 Vertical, 10px\uff09\u5c6c\u65bc Layout \u7ba1\u7406\u5668\u7684\u8077\u8cac\uff0cQSS \u7121\u6cd5\u76f4\u63a5\u63a7\u5236 */\n"
"}\n"
"\n"
"/* \u8a2d\u5b9a\u6240\u6709 QToolTip \u7684\u6a23\u5f0f */\n"
"QToolTip {\n"
"    background-color: black;  /* \u80cc\u666f\u984f\u8272\u8a2d\u70ba\u9ed1\u8272 */\n"
"    color: white;             /* \u6587\u5b57\u984f\u8272\u8a2d\u70ba\u767d\u8272 */\n"
"    border: 1px solid darkgray; /* \u908a\u6846 */\n"
"    border-radius: 4px;       /* \u5713\u89d2 */\n"
"    padding: 4px;             /* \u5167\u908a\u8ddd */\n"
"}")
        self.label_rp_5.setAlignment(Qt.AlignCenter)
        self.label_rp_6 = QLabel(self.frame_map)
        self.label_rp_6.setObjectName(u"label_rp_6")
        self.label_rp_6.setGeometry(QRect(590, 470, 26, 18))
        sizePolicy2.setHeightForWidth(self.label_rp_6.sizePolicy().hasHeightForWidth())
        self.label_rp_6.setSizePolicy(sizePolicy2)
        self.label_rp_6.setFont(font3)
        self.label_rp_6.setStyleSheet(u"QLabel#label_rp_6 {\n"
"    /* 1. \u5927\u5c0f\u548c\u908a\u8ddd (\u5c07 QLabel \u8996\u70ba 'Frame 15') */\n"
"    /* \u6ce8\u610f\uff1aQt Widgets \u7684\u5927\u5c0f\u901a\u5e38\u7531\u5167\u5bb9\u6216 Layout \u6c7a\u5b9a\uff0c\u9019\u88e1\u8a2d\u5b9a\u4e00\u500b\u57fa\u7dda */\n"
"    min-width: 20px;\n"
"    max-width: 20px;\n"
"    min-height: 12px;\n"
"    max-height: 12px;\n"
"\n"
"    /* 2. \u908a\u6846 (Borders) */\n"
"    /* \u5713\u89d2 (Radius: 2px) */\n"
"    border-radius: 2px;\n"
"    /* \u908a\u6846\u7dda (Border: 1px) + \u984f\u8272 (#525252) */\n"
"    border: 1px solid #525252;\n"
"    \n"
"    /* 3. \u984f\u8272 (Colors) - \u4f5c\u70ba\u80cc\u666f\u8272 */\n"
"    /* \u9019\u88e1\u5c07 #33B1FF \u8a2d\u5b9a\u70ba\u9810\u8a2d\u80cc\u666f\u8272 */\n"
"    background-color: #33B1FF;\n"
"\n"
"    /* 4. \u5167\u908a\u8ddd (Padding: 2px) */\n"
"    /* \u9019\u6703\u5f71\u97ff Label \u5167\u5bb9\uff08\u6587\u5b57\u6216\u5716\u7247\uff09\u8207\u908a\u6846\u7684\u8ddd\u96e2 */\n"
"    padding: 2px; \n"
""
                        "    \n"
"    /* 5. \u6587\u5b57\u5c0d\u9f4a (Inner alignment) */\n"
"    /* \u5047\u8a2d 'Inner alignment' \u662f\u6307\u5167\u5bb9\u7f6e\u4e2d */\n"
"    text-align: center; \n"
"    \n"
"    /* Flow \u548c Gap \u5c6c\u6027\uff08\u5982 Vertical, 10px\uff09\u5c6c\u65bc Layout \u7ba1\u7406\u5668\u7684\u8077\u8cac\uff0cQSS \u7121\u6cd5\u76f4\u63a5\u63a7\u5236 */\n"
"}\n"
"\n"
"/* \u8a2d\u5b9a\u6240\u6709 QToolTip \u7684\u6a23\u5f0f */\n"
"QToolTip {\n"
"    background-color: black;  /* \u80cc\u666f\u984f\u8272\u8a2d\u70ba\u9ed1\u8272 */\n"
"    color: white;             /* \u6587\u5b57\u984f\u8272\u8a2d\u70ba\u767d\u8272 */\n"
"    border: 1px solid darkgray; /* \u908a\u6846 */\n"
"    border-radius: 4px;       /* \u5713\u89d2 */\n"
"    padding: 4px;             /* \u5167\u908a\u8ddd */\n"
"}")
        self.label_rp_6.setAlignment(Qt.AlignCenter)
        self.label_rp_7 = QLabel(self.frame_map)
        self.label_rp_7.setObjectName(u"label_rp_7")
        self.label_rp_7.setGeometry(QRect(870, 320, 26, 18))
        sizePolicy2.setHeightForWidth(self.label_rp_7.sizePolicy().hasHeightForWidth())
        self.label_rp_7.setSizePolicy(sizePolicy2)
        self.label_rp_7.setFont(font3)
        self.label_rp_7.setStyleSheet(u"QLabel#label_rp_7 {\n"
"    /* 1. \u5927\u5c0f\u548c\u908a\u8ddd (\u5c07 QLabel \u8996\u70ba 'Frame 15') */\n"
"    /* \u6ce8\u610f\uff1aQt Widgets \u7684\u5927\u5c0f\u901a\u5e38\u7531\u5167\u5bb9\u6216 Layout \u6c7a\u5b9a\uff0c\u9019\u88e1\u8a2d\u5b9a\u4e00\u500b\u57fa\u7dda */\n"
"    min-width: 20px;\n"
"    max-width: 20px;\n"
"    min-height: 12px;\n"
"    max-height: 12px;\n"
"\n"
"    /* 2. \u908a\u6846 (Borders) */\n"
"    /* \u5713\u89d2 (Radius: 2px) */\n"
"    border-radius: 2px;\n"
"    /* \u908a\u6846\u7dda (Border: 1px) + \u984f\u8272 (#525252) */\n"
"    border: 1px solid #525252;\n"
"    \n"
"    /* 3. \u984f\u8272 (Colors) - \u4f5c\u70ba\u80cc\u666f\u8272 */\n"
"    /* \u9019\u88e1\u5c07 #33B1FF \u8a2d\u5b9a\u70ba\u9810\u8a2d\u80cc\u666f\u8272 */\n"
"    background-color: #33B1FF;\n"
"\n"
"    /* 4. \u5167\u908a\u8ddd (Padding: 2px) */\n"
"    /* \u9019\u6703\u5f71\u97ff Label \u5167\u5bb9\uff08\u6587\u5b57\u6216\u5716\u7247\uff09\u8207\u908a\u6846\u7684\u8ddd\u96e2 */\n"
"    padding: 2px; \n"
""
                        "    \n"
"    /* 5. \u6587\u5b57\u5c0d\u9f4a (Inner alignment) */\n"
"    /* \u5047\u8a2d 'Inner alignment' \u662f\u6307\u5167\u5bb9\u7f6e\u4e2d */\n"
"    text-align: center; \n"
"    \n"
"    /* Flow \u548c Gap \u5c6c\u6027\uff08\u5982 Vertical, 10px\uff09\u5c6c\u65bc Layout \u7ba1\u7406\u5668\u7684\u8077\u8cac\uff0cQSS \u7121\u6cd5\u76f4\u63a5\u63a7\u5236 */\n"
"}\n"
"\n"
"/* \u8a2d\u5b9a\u6240\u6709 QToolTip \u7684\u6a23\u5f0f */\n"
"QToolTip {\n"
"    background-color: black;  /* \u80cc\u666f\u984f\u8272\u8a2d\u70ba\u9ed1\u8272 */\n"
"    color: white;             /* \u6587\u5b57\u984f\u8272\u8a2d\u70ba\u767d\u8272 */\n"
"    border: 1px solid darkgray; /* \u908a\u6846 */\n"
"    border-radius: 4px;       /* \u5713\u89d2 */\n"
"    padding: 4px;             /* \u5167\u908a\u8ddd */\n"
"}")
        self.label_rp_7.setAlignment(Qt.AlignCenter)
        self.frame_pending_mission_list = QFrame(self.centralwidget)
        self.frame_pending_mission_list.setObjectName(u"frame_pending_mission_list")
        self.frame_pending_mission_list.setGeometry(QRect(1200, 500, 656, 511))
        self.frame_pending_mission_list.setStyleSheet(u"  border: 2px solid   #2C3E50; /* \u5916\u908a\u6846\u7dda\u689d */")
        self.frame_pending_mission_list.setFrameShape(QFrame.StyledPanel)
        self.frame_pending_mission_list.setFrameShadow(QFrame.Raised)
        self.tableWidget_pending_mission_list = QTableWidget(self.frame_pending_mission_list)
        if (self.tableWidget_pending_mission_list.columnCount() < 8):
            self.tableWidget_pending_mission_list.setColumnCount(8)
        if (self.tableWidget_pending_mission_list.rowCount() < 1):
            self.tableWidget_pending_mission_list.setRowCount(1)
        font4 = QFont()
        font4.setFamilies([u"Noto Sans TC"])
        font4.setPointSize(14)
        __qtablewidgetitem = QTableWidgetItem()
        __qtablewidgetitem.setTextAlignment(Qt.AlignCenter);
        __qtablewidgetitem.setFont(font4);
        self.tableWidget_pending_mission_list.setItem(0, 0, __qtablewidgetitem)
        __qtablewidgetitem1 = QTableWidgetItem()
        self.tableWidget_pending_mission_list.setItem(0, 1, __qtablewidgetitem1)
        __qtablewidgetitem2 = QTableWidgetItem()
        self.tableWidget_pending_mission_list.setItem(0, 2, __qtablewidgetitem2)
        __qtablewidgetitem3 = QTableWidgetItem()
        self.tableWidget_pending_mission_list.setItem(0, 3, __qtablewidgetitem3)
        __qtablewidgetitem4 = QTableWidgetItem()
        self.tableWidget_pending_mission_list.setItem(0, 4, __qtablewidgetitem4)
        self.tableWidget_pending_mission_list.setObjectName(u"tableWidget_pending_mission_list")
        self.tableWidget_pending_mission_list.setGeometry(QRect(0, 0, 656, 511))
        sizePolicy2.setHeightForWidth(self.tableWidget_pending_mission_list.sizePolicy().hasHeightForWidth())
        self.tableWidget_pending_mission_list.setSizePolicy(sizePolicy2)
        self.tableWidget_pending_mission_list.setMinimumSize(QSize(0, 0))
        self.tableWidget_pending_mission_list.setMaximumSize(QSize(16777215, 16777215))
        font5 = QFont()
        font5.setFamilies([u"Noto Sans TC"])
        font5.setPointSize(12)
        self.tableWidget_pending_mission_list.setFont(font5)
        self.tableWidget_pending_mission_list.setStyleSheet(u"QTableWidget::item {\n"
"    padding: 5px;\n"
"    /*background-color: #1a1a1a;   \u6df1\u7070\u8272\u80cc\u666f */\n"
"   /*color: white;                \u6587\u5b57\u984f\u8272 */\n"
"    gridline-color: #333333;    /* \u683c\u7dda\u984f\u8272 */\n"
"    white-space: pre-wrap;\n"
"    border-bottom:1.5px solid   #2b2b2b;\n"
"}\n"
"QHeaderView::section {\n"
"    background-color: #2b2b2b;  /* \u8868\u982d\u80cc\u666f\u8272 */\n"
"    color: white;               /* \u8868\u982d\u6587\u5b57\u984f\u8272\uff0c\u9019\u884c CSS \u544a\u8a34 Qt\uff1a\u8868\u683c\u4e2d\u7684\u6240\u6709\u6587\u5b57\uff0c\u9664\u975e\u88ab\u66f4\u5177\u9ad4\u7684\u898f\u5247\u8986\u84cb\uff0c\u5426\u5247\u90fd\u5fc5\u9808\u662f\u767d\u8272\u3002 */\n"
"    padding: 5px;               /* \u5167\u908a\u8ddd */\n"
"    border-bottom: 2px solid #2b2b2b; /* \u8868\u982d\u5e95\u7dda */\n"
"    font: 14pt;\n"
"}\n"
"\n"
"")
        self.tableWidget_pending_mission_list.setCornerButtonEnabled(True)
        self.tableWidget_pending_mission_list.setRowCount(1)
        self.tableWidget_pending_mission_list.setColumnCount(8)
        self.tableWidget_pending_mission_list.horizontalHeader().setVisible(True)
        self.tableWidget_pending_mission_list.horizontalHeader().setCascadingSectionResizes(False)
        self.tableWidget_pending_mission_list.horizontalHeader().setMinimumSectionSize(25)
        self.tableWidget_pending_mission_list.horizontalHeader().setDefaultSectionSize(75)
        self.tableWidget_pending_mission_list.horizontalHeader().setHighlightSections(True)
        self.tableWidget_pending_mission_list.horizontalHeader().setStretchLastSection(True)
        self.tableWidget_pending_mission_list.verticalHeader().setVisible(False)
        self.tableWidget_pending_mission_list.verticalHeader().setCascadingSectionResizes(False)
        self.tableWidget_pending_mission_list.verticalHeader().setMinimumSectionSize(60)
        self.tableWidget_pending_mission_list.verticalHeader().setDefaultSectionSize(60)
        self.tableWidget_pending_mission_list.verticalHeader().setStretchLastSection(False)
        self.frame_temp = QFrame(self.centralwidget)
        self.frame_temp.setObjectName(u"frame_temp")
        self.frame_temp.setEnabled(True)
        self.frame_temp.setGeometry(QRect(10, 1040, 1111, 161))
        self.frame_temp.setStyleSheet(u"background-color:gray;")
        self.frame_temp.setFrameShape(QFrame.StyledPanel)
        self.frame_temp.setFrameShadow(QFrame.Raised)
        self.dsb_x_m = QDoubleSpinBox(self.frame_temp)
        self.dsb_x_m.setObjectName(u"dsb_x_m")
        self.dsb_x_m.setGeometry(QRect(70, 60, 79, 42))
        sizePolicy3 = QSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Preferred)
        sizePolicy3.setHorizontalStretch(0)
        sizePolicy3.setVerticalStretch(0)
        sizePolicy3.setHeightForWidth(self.dsb_x_m.sizePolicy().hasHeightForWidth())
        self.dsb_x_m.setSizePolicy(sizePolicy3)
        self.dsb_x_m.setStyleSheet(u"/* \u2705 QDoubleSpinBox \u6574\u9ad4\u6a23\u5f0f */\n"
"QDoubleSpinBox {\n"
"    color: white;\n"
"    background-color: transparent;\n"
"    font-size: 20px;\n"
"    border: 1px solid white;\n"
"    border-radius: 4px;\n"
"    padding: 2px 6px;\n"
"}\n"
"/* \u2705 \u8b93\u5167\u90e8\u6587\u5b57\u5340\u57df\u900f\u660e\uff08\u95dc\u9375\uff09 */\n"
"QAbstractSpinBox::viewport {\n"
"    background: transparent;\n"
"}\n"
"\n"
"QAbstractSpinBox::up-button, QAbstractSpinBox::down-button {\n"
"    width: 0;\n"
"    height: 0;\n"
"    border: none;\n"
"}")
        self.dsb_x_m.setMinimum(-100.000000000000000)
        self.dsb_x_m.setMaximum(100.000000000000000)
        self.label_ori_m = QLabel(self.frame_temp)
        self.label_ori_m.setObjectName(u"label_ori_m")
        self.label_ori_m.setGeometry(QRect(310, 70, 41, 21))
        self.label_ori_m.setStyleSheet(u"color: white;                  /* \u767d\u5b57 */\n"
"font-size: 24px; \n"
"background-color: rgba(103, 103, 103, 0);")
        self.label_ori_m.setLocale(QLocale(QLocale.English, QLocale.UnitedStates))
        self.label_ori_m.setAlignment(Qt.AlignCenter)
        self.label_y_rm = QLabel(self.frame_temp)
        self.label_y_rm.setObjectName(u"label_y_rm")
        self.label_y_rm.setGeometry(QRect(720, 70, 61, 21))
        self.label_y_rm.setStyleSheet(u"color: white;                  /* \u767d\u5b57 */\n"
"font-size: 24px; ")
        self.label_y_rm.setLocale(QLocale(QLocale.English, QLocale.UnitedStates))
        self.label_y_rm.setAlignment(Qt.AlignCenter)
        self.dsb_x = QDoubleSpinBox(self.frame_temp)
        self.dsb_x.setObjectName(u"dsb_x")
        self.dsb_x.setGeometry(QRect(630, 60, 79, 42))
        sizePolicy3.setHeightForWidth(self.dsb_x.sizePolicy().hasHeightForWidth())
        self.dsb_x.setSizePolicy(sizePolicy3)
        self.dsb_x.setStyleSheet(u"font-size: 16px")
        self.dsb_y = QDoubleSpinBox(self.frame_temp)
        self.dsb_y.setObjectName(u"dsb_y")
        self.dsb_y.setGeometry(QRect(770, 60, 79, 41))
        sizePolicy3.setHeightForWidth(self.dsb_y.sizePolicy().hasHeightForWidth())
        self.dsb_y.setSizePolicy(sizePolicy3)
        self.dsb_y.setStyleSheet(u"font-size: 16px")
        self.label_x_m = QLabel(self.frame_temp)
        self.label_x_m.setObjectName(u"label_x_m")
        self.label_x_m.setGeometry(QRect(20, 70, 41, 21))
        self.label_x_m.setStyleSheet(u"color: white;                  /* \u767d\u5b57 */\n"
"font-size: 24px; \n"
"background-color: rgba(103, 103, 103, 0);")
        self.label_x_m.setLocale(QLocale(QLocale.English, QLocale.UnitedStates))
        self.label_x_m.setAlignment(Qt.AlignCenter)
        self.label_4 = QLabel(self.frame_temp)
        self.label_4.setObjectName(u"label_4")
        self.label_4.setGeometry(QRect(450, 70, 121, 29))
        self.label_4.setStyleSheet(u"color: white;                  /* \u767d\u5b57 */\n"
"font-size: 24px; ")
        self.label_4.setLocale(QLocale(QLocale.English, QLocale.UnitedStates))
        self.label_4.setAlignment(Qt.AlignCenter)
        self.dsb_ori = QDoubleSpinBox(self.frame_temp)
        self.dsb_ori.setObjectName(u"dsb_ori")
        self.dsb_ori.setGeometry(QRect(920, 60, 79, 41))
        sizePolicy3.setHeightForWidth(self.dsb_ori.sizePolicy().hasHeightForWidth())
        self.dsb_ori.setSizePolicy(sizePolicy3)
        self.dsb_ori.setStyleSheet(u"font-size: 16px")
        self.label_x_rm = QLabel(self.frame_temp)
        self.label_x_rm.setObjectName(u"label_x_rm")
        self.label_x_rm.setGeometry(QRect(570, 70, 61, 21))
        self.label_x_rm.setStyleSheet(u"color: white;                  /* \u767d\u5b57 */\n"
"font-size: 24px; ")
        self.label_x_rm.setLocale(QLocale(QLocale.English, QLocale.UnitedStates))
        self.label_x_rm.setAlignment(Qt.AlignCenter)
        self.label_ori_rm = QLabel(self.frame_temp)
        self.label_ori_rm.setObjectName(u"label_ori_rm")
        self.label_ori_rm.setGeometry(QRect(850, 70, 61, 21))
        self.label_ori_rm.setStyleSheet(u"color: white;                  /* \u767d\u5b57 */\n"
"font-size: 24px; ")
        self.label_ori_rm.setLocale(QLocale(QLocale.English, QLocale.UnitedStates))
        self.label_ori_rm.setAlignment(Qt.AlignCenter)
        self.dsb_y_m = QDoubleSpinBox(self.frame_temp)
        self.dsb_y_m.setObjectName(u"dsb_y_m")
        self.dsb_y_m.setGeometry(QRect(210, 60, 79, 42))
        sizePolicy3.setHeightForWidth(self.dsb_y_m.sizePolicy().hasHeightForWidth())
        self.dsb_y_m.setSizePolicy(sizePolicy3)
        self.dsb_y_m.setStyleSheet(u"/* \u2705 QDoubleSpinBox \u6574\u9ad4\u6a23\u5f0f */\n"
"QDoubleSpinBox {\n"
"    color: white;\n"
"    background-color: transparent;\n"
"    font-size: 20px;\n"
"    border: 1px solid white;\n"
"    border-radius: 4px;\n"
"    padding: 2px 6px;\n"
"}\n"
"/* \u2705 \u8b93\u5167\u90e8\u6587\u5b57\u5340\u57df\u900f\u660e\uff08\u95dc\u9375\uff09 */\n"
"QAbstractSpinBox::viewport {\n"
"    background: transparent;\n"
"}\n"
"\n"
"QAbstractSpinBox::up-button, QAbstractSpinBox::down-button {\n"
"    width: 0;\n"
"    height: 0;\n"
"    border: none;\n"
"}")
        self.dsb_y_m.setMinimum(-100.000000000000000)
        self.dsb_y_m.setMaximum(100.000000000000000)
        self.btn_StartRelativeMove = QPushButton(self.frame_temp)
        self.btn_StartRelativeMove.setObjectName(u"btn_StartRelativeMove")
        self.btn_StartRelativeMove.setGeometry(QRect(1010, 70, 60, 30))
        self.btn_StartRelativeMove.setStyleSheet(u"QPushButton {\n"
"	background-color: rgb(72, 72, 72);\n"
"    color: white;                  /* \u767d\u5b57 */\n"
"    border-radius: 10px;           /* \u5713\u89d2 */\n"
"    padding: 6px 12px;             /* \u5167\u8ddd */\n"
"    font-size: 24px;               /* \u5b57\u9ad4\u5927\u5c0f */\n"
"}\n"
"\n"
"QPushButton:hover {\n"
"    background-color: #1E70BF;     /* \u6ed1\u9f20\u79fb\u4e0a\u53bb\u8b8a\u8272 */\n"
"}")
        self.btn_StartRelativeMove.setIcon(icon)
        self.dsb_ori_m = QDoubleSpinBox(self.frame_temp)
        self.dsb_ori_m.setObjectName(u"dsb_ori_m")
        self.dsb_ori_m.setGeometry(QRect(370, 60, 79, 42))
        sizePolicy3.setHeightForWidth(self.dsb_ori_m.sizePolicy().hasHeightForWidth())
        self.dsb_ori_m.setSizePolicy(sizePolicy3)
        self.dsb_ori_m.setStyleSheet(u"/* \u2705 QDoubleSpinBox \u6574\u9ad4\u6a23\u5f0f */\n"
"QDoubleSpinBox {\n"
"    color: white;\n"
"    background-color: transparent;\n"
"    font-size: 20px;\n"
"    border: 1px solid white;\n"
"    border-radius: 4px;\n"
"    padding: 2px 6px;\n"
"}\n"
"/* \u2705 \u8b93\u5167\u90e8\u6587\u5b57\u5340\u57df\u900f\u660e\uff08\u95dc\u9375\uff09 */\n"
"QAbstractSpinBox::viewport {\n"
"    background: transparent;\n"
"}\n"
"\n"
"QAbstractSpinBox::up-button, QAbstractSpinBox::down-button {\n"
"    width: 0;\n"
"    height: 0;\n"
"    border: none;\n"
"}")
        self.dsb_ori_m.setMinimum(-180.000000000000000)
        self.dsb_ori_m.setMaximum(180.000000000000000)
        self.label_y_m = QLabel(self.frame_temp)
        self.label_y_m.setObjectName(u"label_y_m")
        self.label_y_m.setGeometry(QRect(160, 70, 41, 21))
        self.label_y_m.setStyleSheet(u"color: white;                  /* \u767d\u5b57 */\n"
"font-size: 24px; \n"
"background-color: rgba(103, 103, 103, 0);")
        self.label_y_m.setLocale(QLocale(QLocale.English, QLocale.UnitedStates))
        self.label_y_m.setAlignment(Qt.AlignCenter)
        self.btn_StartMission2 = QPushButton(self.frame_temp)
        self.btn_StartMission2.setObjectName(u"btn_StartMission2")
        self.btn_StartMission2.setGeometry(QRect(460, 20, 31, 30))
        sizePolicy4 = QSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed)
        sizePolicy4.setHorizontalStretch(0)
        sizePolicy4.setVerticalStretch(0)
        sizePolicy4.setHeightForWidth(self.btn_StartMission2.sizePolicy().hasHeightForWidth())
        self.btn_StartMission2.setSizePolicy(sizePolicy4)
        self.btn_StartMission2.setStyleSheet(u"QPushButton {\n"
"	background-color: rgb(72, 72, 72);\n"
"    color: white;                  /* \u767d\u5b57 */\n"
"    border-radius: 10px;           /* \u5713\u89d2 */\n"
"    padding: 6px 12px;             /* \u5167\u8ddd */\n"
"    font-size: 24px;               /* \u5b57\u9ad4\u5927\u5c0f */\n"
"}\n"
"\n"
"QPushButton:hover {\n"
"    background-color: #1E70BF;     /* \u6ed1\u9f20\u79fb\u4e0a\u53bb\u8b8a\u8272 */\n"
"}")
        self.btn_StartMission2.setIcon(icon)
        self.btn_StopMission2 = QPushButton(self.frame_temp)
        self.btn_StopMission2.setObjectName(u"btn_StopMission2")
        self.btn_StopMission2.setGeometry(QRect(510, 20, 31, 30))
        self.btn_StopMission2.setStyleSheet(u"QPushButton {\n"
"	background-color: rgb(72, 72, 72);\n"
"    color: white;                  /* \u767d\u5b57 */\n"
"    border-radius: 10px;           /* \u5713\u89d2 */\n"
"    padding: 6px 12px;             /* \u5167\u8ddd */\n"
"    font-size: 24px;               /* \u5b57\u9ad4\u5927\u5c0f */\n"
"}\n"
"\n"
"QPushButton:hover {\n"
"    background-color: #1E70BF;     /* \u6ed1\u9f20\u79fb\u4e0a\u53bb\u8b8a\u8272 */\n"
"}")
        self.btn_StopMission2.setIcon(icon1)
        self.label_5 = QLabel(self.frame_temp)
        self.label_5.setObjectName(u"label_5")
        self.label_5.setGeometry(QRect(280, 20, 159, 29))
        self.label_5.setStyleSheet(u"color: white;                  /* \u767d\u5b57 */\n"
"font-size: 24px; ")
        self.label_5.setLocale(QLocale(QLocale.English, QLocale.UnitedStates))
        self.label_5.setAlignment(Qt.AlignCenter)
        self.label_IO = QLabel(self.frame_temp)
        self.label_IO.setObjectName(u"label_IO")
        self.label_IO.setGeometry(QRect(10, 20, 141, 21))
        self.label_IO.setFont(font1)
        self.label_IO.setStyleSheet(u"color: black;                  /* \u767d\u5b57 */\n"
"font-size: 18px; ")
        self.label_IO.setLocale(QLocale(QLocale.English, QLocale.UnitedStates))
        self.label_IO.setAlignment(Qt.AlignCenter)
        self.btn_IO_Up = QPushButton(self.frame_temp)
        self.btn_IO_Up.setObjectName(u"btn_IO_Up")
        self.btn_IO_Up.setGeometry(QRect(150, 20, 36, 31))
        self.btn_IO_Up.setFont(font1)
        self.btn_IO_Up.setStyleSheet(u"QPushButton {\n"
"	background-color: rgb(72, 72, 72);\n"
"    color: white;                  /* \u767d\u5b57 */\n"
"    border-radius: 10px;           /* \u5713\u89d2 */\n"
"    padding: 6px 12px;             /* \u5167\u8ddd */\n"
"    font-size: 16px;               /* \u5b57\u9ad4\u5927\u5c0f */\n"
"}\n"
"\n"
"QPushButton:hover {\n"
"    background-color: #1E70BF;     /* \u6ed1\u9f20\u79fb\u4e0a\u53bb\u8b8a\u8272 */\n"
"}")
        self.btn_IO_down = QPushButton(self.frame_temp)
        self.btn_IO_down.setObjectName(u"btn_IO_down")
        self.btn_IO_down.setGeometry(QRect(210, 20, 36, 31))
        self.btn_IO_down.setFont(font1)
        self.btn_IO_down.setStyleSheet(u"QPushButton {\n"
"	background-color: rgb(72, 72, 72);\n"
"    color: white;                  /* \u767d\u5b57 */\n"
"    border-radius: 10px;           /* \u5713\u89d2 */\n"
"    padding: 6px 12px;             /* \u5167\u8ddd */\n"
"    font-size: 16px;               /* \u5b57\u9ad4\u5927\u5c0f */\n"
"}\n"
"\n"
"QPushButton:hover {\n"
"    background-color: #1E70BF;     /* \u6ed1\u9f20\u79fb\u4e0a\u53bb\u8b8a\u8272 */\n"
"}")
        self.txtEdit_GetPM = QTextEdit(self.frame_temp)
        self.txtEdit_GetPM.setObjectName(u"txtEdit_GetPM")
        self.txtEdit_GetPM.setGeometry(QRect(640, 110, 311, 41))
        sizePolicy.setHeightForWidth(self.txtEdit_GetPM.sizePolicy().hasHeightForWidth())
        self.txtEdit_GetPM.setSizePolicy(sizePolicy)
        self.txtEdit_GetPM.setMinimumSize(QSize(0, 0))
        self.txtEdit_GetPM.setMaximumSize(QSize(656, 900))
        self.txtEdit_GetPM.setStyleSheet(u"background-color: rgb(103, 103, 103);\n"
" font-size: 16px;               /* \u5b57\u9ad4\u5927\u5c0f */")
        self.label_7 = QLabel(self.frame_temp)
        self.label_7.setObjectName(u"label_7")
        self.label_7.setGeometry(QRect(500, 120, 121, 29))
        self.label_7.setStyleSheet(u"color: white;                  /* \u767d\u5b57 */\n"
"font-size: 24px; ")
        self.label_7.setLocale(QLocale(QLocale.English, QLocale.UnitedStates))
        self.label_7.setAlignment(Qt.AlignCenter)
        self.btn_GetPM = QPushButton(self.frame_temp)
        self.btn_GetPM.setObjectName(u"btn_GetPM")
        self.btn_GetPM.setGeometry(QRect(970, 110, 121, 36))
        sizePolicy4.setHeightForWidth(self.btn_GetPM.sizePolicy().hasHeightForWidth())
        self.btn_GetPM.setSizePolicy(sizePolicy4)
        self.btn_GetPM.setFont(font1)
        self.btn_GetPM.setStyleSheet(u"QPushButton {\n"
"	background-color: rgb(72, 72, 72);\n"
"    color: white;                  /* \u767d\u5b57 */\n"
"    border-radius: 10px;           /* \u5713\u89d2 */\n"
"    padding: 6px 12px;             /* \u5167\u8ddd */\n"
"    font-size:16px;               /* \u5b57\u9ad4\u5927\u5c0f */\n"
"}\n"
"\n"
"QPushButton:hover {\n"
"    background-color: #1E70BF;     /* \u6ed1\u9f20\u79fb\u4e0a\u53bb\u8b8a\u8272 */\n"
"}")
        self.plntxtEdit_Info = QPlainTextEdit(self.frame_temp)
        self.plntxtEdit_Info.setObjectName(u"plntxtEdit_Info")
        self.plntxtEdit_Info.setGeometry(QRect(190, 120, 211, 31))
        self.plntxtEdit_Info.setStyleSheet(u"background-color: rgb(103,103,103);\n"
" font-size: 16px;               /* \u5b57\u9ad4\u5927\u5c0f */")
        self.btn_UpdateInfo = QPushButton(self.frame_temp)
        self.btn_UpdateInfo.setObjectName(u"btn_UpdateInfo")
        self.btn_UpdateInfo.setGeometry(QRect(20, 130, 141, 21))
        sizePolicy4.setHeightForWidth(self.btn_UpdateInfo.sizePolicy().hasHeightForWidth())
        self.btn_UpdateInfo.setSizePolicy(sizePolicy4)
        font6 = QFont()
        font6.setFamilies([u"Nirmala Text"])
        self.btn_UpdateInfo.setFont(font6)
        self.btn_UpdateInfo.setStyleSheet(u"QPushButton {\n"
"	background-color: rgb(72, 72, 72);\n"
"    color: white;                  /* \u767d\u5b57 */\n"
"    border-radius: 10px;           /* \u5713\u89d2 */\n"
"    padding: 6px 12px;             /* \u5167\u8ddd */\n"
"    font-size:16px;               /* \u5b57\u9ad4\u5927\u5c0f */\n"
"}\n"
"\n"
"QPushButton:hover {\n"
"    background-color: #1E70BF;     /* \u6ed1\u9f20\u79fb\u4e0a\u53bb\u8b8a\u8272 */\n"
"}")
        self.label_8 = QLabel(self.frame_temp)
        self.label_8.setObjectName(u"label_8")
        self.label_8.setGeometry(QRect(20, 110, 101, 20))
        self.label_8.setStyleSheet(u"color: white;                  /* \u767d\u5b57 */\n"
"font-size: 12px; ")
        self.label_8.setLocale(QLocale(QLocale.English, QLocale.UnitedStates))
        self.label_8.setAlignment(Qt.AlignCenter)
        self.btn_SelectDestination = QPushButton(self.centralwidget)
        self.btn_SelectDestination.setObjectName(u"btn_SelectDestination")
        self.btn_SelectDestination.setGeometry(QRect(1790, 190, 91, 30))
        self.btn_SelectDestination.setFont(font1)
        self.btn_SelectDestination.setStyleSheet(u"QPushButton {\n"
"	background-color:#0678DD;\n"
"    color: white;                  /* \u767d\u5b57 */\n"
"    padding: 6px 12px;             /* \u5167\u8ddd */\n"
"    font-size: 16px;               /* \u5b57\u9ad4\u5927\u5c0f */\n"
"}\n"
"\n"
"QPushButton:hover {\n"
"    background-color: #1E70BF;     /* \u6ed1\u9f20\u79fb\u4e0a\u53bb\u8b8a\u8272 */\n"
"}")
        self.btn_SelectStart = QPushButton(self.centralwidget)
        self.btn_SelectStart.setObjectName(u"btn_SelectStart")
        self.btn_SelectStart.setGeometry(QRect(1790, 130, 91, 30))
        self.btn_SelectStart.setFont(font1)
        self.btn_SelectStart.setStyleSheet(u"QPushButton {\n"
"	background-color:#0678DD;\n"
"    color: white;                  /* \u767d\u5b57 */\n"
"    padding: 6px 12px;             /* \u5167\u8ddd */\n"
"    font-size: 16px;               /* \u5b57\u9ad4\u5927\u5c0f */\n"
"}\n"
"\n"
"QPushButton:hover {\n"
"    background-color: #1E70BF;     /* \u6ed1\u9f20\u79fb\u4e0a\u53bb\u8b8a\u8272 */\n"
"}")
        self.btn_Start_Exhibition_Drink = QPushButton(self.centralwidget)
        self.btn_Start_Exhibition_Drink.setObjectName(u"btn_Start_Exhibition_Drink")
        self.btn_Start_Exhibition_Drink.setGeometry(QRect(1560, 320, 121, 30))
        self.btn_Start_Exhibition_Drink.setFont(font1)
        self.btn_Start_Exhibition_Drink.setStyleSheet(u"QPushButton {\n"
"	background-color:#0678DD;\n"
"    color: white;                  /* \u767d\u5b57 */\n"
"    padding: 6px 12px;             /* \u5167\u8ddd */\n"
"    font-size: 16px;               /* \u5b57\u9ad4\u5927\u5c0f */\n"
"}\n"
"\n"
"QPushButton:hover {\n"
"    background-color: #1E70BF;     /* \u6ed1\u9f20\u79fb\u4e0a\u53bb\u8b8a\u8272 */\n"
"}")
        self.btn_Start_Exhibition_Military = QPushButton(self.centralwidget)
        self.btn_Start_Exhibition_Military.setObjectName(u"btn_Start_Exhibition_Military")
        self.btn_Start_Exhibition_Military.setGeometry(QRect(1720, 320, 121, 30))
        self.btn_Start_Exhibition_Military.setFont(font1)
        self.btn_Start_Exhibition_Military.setStyleSheet(u"QPushButton {\n"
"	background-color:#0678DD;\n"
"    color: white;                  /* \u767d\u5b57 */\n"
"    padding: 6px 12px;             /* \u5167\u8ddd */\n"
"    font-size: 16px;               /* \u5b57\u9ad4\u5927\u5c0f */\n"
"}\n"
"\n"
"QPushButton:hover {\n"
"    background-color: #1E70BF;     /* \u6ed1\u9f20\u79fb\u4e0a\u53bb\u8b8a\u8272 */\n"
"}")
        MainWindow.setCentralWidget(self.centralwidget)
        self.frame_map.raise_()
        self.btn_StartMission.raise_()
        self.btn_StopMission1.raise_()
        self.lineEdit_PendingMission.raise_()
        self.horizontalLayoutWidget_2.raise_()
        self.horizontalLayoutWidget.raise_()
        self.horizontalLayoutWidget_4.raise_()
        self.horizontalLayoutWidget_5.raise_()
        self.horizontalLayoutWidget_6.raise_()
        self.btn_Emergency_Cut_Line.raise_()
        self.btn_Add_New_Mission.raise_()
        self.frame_pending_mission_list.raise_()
        self.frame_temp.raise_()
        self.btn_SelectDestination.raise_()
        self.btn_SelectStart.raise_()
        self.btn_Start_Exhibition_Drink.raise_()
        self.btn_Start_Exhibition_Military.raise_()
        self.statusbar = QStatusBar(MainWindow)
        self.statusbar.setObjectName(u"statusbar")
        MainWindow.setStatusBar(self.statusbar)

        self.retranslateUi(MainWindow)

        QMetaObject.connectSlotsByName(MainWindow)
    # setupUi

    def retranslateUi(self, MainWindow):
        MainWindow.setWindowTitle(QCoreApplication.translate("MainWindow", u"ACE Solution", None))
        self.btn_StartMission.setText("")
        self.btn_StopMission1.setText("")
        self.lineEdit_PendingMission.setText(QCoreApplication.translate("MainWindow", u"\u5f85\u57f7\u884c\u4efb\u52d9\u6e05\u55ae", None))
        self.label.setText(QCoreApplication.translate("MainWindow", u"\u76ee\u7684\u5730", None))
        self.cmb_location.setCurrentText(QCoreApplication.translate("MainWindow", u"\u5be6\u9a57\u5ba4-B", None))
        self.label_3.setText(QCoreApplication.translate("MainWindow", u"\u4efb\u52d9\u5167\u5bb9", None))
        self.cmb_mission.setCurrentText(QCoreApplication.translate("MainWindow", u"\u62c9\u8eca\u81f3\u6c99\u767c\u5340", None))
        self.label_6.setText(QCoreApplication.translate("MainWindow", u"\u8d77\u59cb\u9ede", None))
        self.cmb_location2.setCurrentText(QCoreApplication.translate("MainWindow", u"\u5be6\u9a57\u5ba4-A", None))
        self.label_Status_1.setText(QCoreApplication.translate("MainWindow", u"Status\uff1aRun", None))
        self.lineEdit_IP.setText(QCoreApplication.translate("MainWindow", u"10.11.202.251", None))
        self.btn_save_ip.setText("")
        self.lineEdit_MiR250_A.setText(QCoreApplication.translate("MainWindow", u"MiR250-A", None))
        self.btn_ChargeMission.setText(QCoreApplication.translate("MainWindow", u"\u7acb\u5373\u8fd4\u56de\u5145\u96fb", None))
        self.btn_Reset.setText(QCoreApplication.translate("MainWindow", u"Reset", None))
        self.btn_Emergency_Cut_Line.setText(QCoreApplication.translate("MainWindow", u"\u7dca\u6025\u63d2\u55ae", None))
        self.btn_Add_New_Mission.setText(QCoreApplication.translate("MainWindow", u"\u65b0\u589e\u4efb\u52d9", None))
        self.label_map_1.setText("")
        self.chb_map.setText(QCoreApplication.translate("MainWindow", u"\u555f\u7528\u5730\u5716\u9ede\u64ca", None))
        self.btn_SentRobotTo.setText("")
        self.lineEdit_MessageAnnounce_6.setText(QCoreApplication.translate("MainWindow", u"1", None))
        self.lineEdit_current_tasks.setText(QCoreApplication.translate("MainWindow", u"\u73fe\u5728\u4efb\u52d9", None))
        self.lineEdit_MessageAnnounce_7.setText(QCoreApplication.translate("MainWindow", u"1", None))
        self.lineEdit_pending_tasks.setText(QCoreApplication.translate("MainWindow", u"\u5f85\u8fa6\u4efb\u52d9", None))
        self.lineEdit_MessageAnnounce.setText(QCoreApplication.translate("MainWindow", u"\u901a\u77e5\u7d00\u9304", None))
#if QT_CONFIG(tooltip)
        self.label_rp_1.setToolTip(QCoreApplication.translate("MainWindow", u"<html><head/><body><p>\u6d41\u6c34\u865f:<br/>\u4efb\u52d9\u6392\u5e8f:<br/>\u4efb\u52d9\u5167\u5bb9:\u5f9e\u624b\u8853\u5ba407-A\u524d \u5f80\u6ec5\u83cc\u5ba4-5, \u5b8c\u6210\u5f8c\u7e8c\u57f7\u884c\u4efb\u52d9<br/>\u65b0\u589e\u4eba:\u8521\u660e\u52f3(1002)</p><p><br/></p><p><br/></p></body></html>", None))
#endif // QT_CONFIG(tooltip)
        self.label_rp_1.setText(QCoreApplication.translate("MainWindow", u"0", None))
#if QT_CONFIG(tooltip)
        self.label_rp_2.setToolTip(QCoreApplication.translate("MainWindow", u"<html><head/><body><p>\u6d41\u6c34\u865f:<br/>\u4efb\u52d9\u6392\u5e8f:<br/>\u4efb\u52d9\u5167\u5bb9:\u5f9e\u624b\u8853\u5ba407-A\u524d \u5f80\u6ec5\u83cc\u5ba4-5, \u5b8c\u6210\u5f8c\u7e8c\u57f7\u884c\u4efb\u52d9<br/>\u65b0\u589e\u4eba:\u8521\u660e\u52f3(1002)</p></body></html>", None))
#endif // QT_CONFIG(tooltip)
        self.label_rp_2.setText(QCoreApplication.translate("MainWindow", u"0", None))
#if QT_CONFIG(tooltip)
        self.label_rp_3.setToolTip(QCoreApplication.translate("MainWindow", u"\u6d41\u6c34\u865f:\n"
"\u4efb\u52d9\u6392\u5e8f:\n"
"\u4efb\u52d9\u5167\u5bb9:\u5f9e\u624b\u8853\u5ba407-A\u524d \u5f80\u6ec5\u83cc\u5ba4-5, \u5b8c\u6210\u5f8c\u7e8c\u57f7\u884c\u4efb\u52d9\n"
"\u65b0\u589e\u4eba:\u8521\u660e\u52f3(1002)", None))
#endif // QT_CONFIG(tooltip)
        self.label_rp_3.setText(QCoreApplication.translate("MainWindow", u"0", None))
#if QT_CONFIG(tooltip)
        self.label_rp_4.setToolTip(QCoreApplication.translate("MainWindow", u"\u6d41\u6c34\u865f:\n"
"\u4efb\u52d9\u6392\u5e8f:\n"
"\u4efb\u52d9\u5167\u5bb9:\u5f9e\u624b\u8853\u5ba407-A\u524d \u5f80\u6ec5\u83cc\u5ba4-5, \u5b8c\u6210\u5f8c\u7e8c\u57f7\u884c\u4efb\u52d9\n"
"\u65b0\u589e\u4eba:\u8521\u660e\u52f3(1002)", None))
#endif // QT_CONFIG(tooltip)
        self.label_rp_4.setText(QCoreApplication.translate("MainWindow", u"0", None))
#if QT_CONFIG(tooltip)
        self.label_rp_5.setToolTip(QCoreApplication.translate("MainWindow", u"\u6d41\u6c34\u865f:\n"
"\u4efb\u52d9\u6392\u5e8f:\n"
"\u4efb\u52d9\u5167\u5bb9:\u5f9e\u624b\u8853\u5ba407-A\u524d \u5f80\u6ec5\u83cc\u5ba4-5, \u5b8c\u6210\u5f8c\u7e8c\u57f7\u884c\u4efb\u52d9\n"
"\u65b0\u589e\u4eba:\u8521\u660e\u52f3(1002)", None))
#endif // QT_CONFIG(tooltip)
        self.label_rp_5.setText(QCoreApplication.translate("MainWindow", u"0", None))
#if QT_CONFIG(tooltip)
        self.label_rp_6.setToolTip(QCoreApplication.translate("MainWindow", u"\u6d41\u6c34\u865f:\n"
"\u4efb\u52d9\u6392\u5e8f:\n"
"\u4efb\u52d9\u5167\u5bb9:\u5f9e\u624b\u8853\u5ba407-A\u524d \u5f80\u6ec5\u83cc\u5ba4-5, \u5b8c\u6210\u5f8c\u7e8c\u57f7\u884c\u4efb\u52d9\n"
"\u65b0\u589e\u4eba:\u8521\u660e\u52f3(1002)", None))
#endif // QT_CONFIG(tooltip)
        self.label_rp_6.setText(QCoreApplication.translate("MainWindow", u"0", None))
#if QT_CONFIG(tooltip)
        self.label_rp_7.setToolTip(QCoreApplication.translate("MainWindow", u"\u6d41\u6c34\u865f:\n"
"\u4efb\u52d9\u6392\u5e8f:\n"
"\u4efb\u52d9\u5167\u5bb9:\u5f9e\u624b\u8853\u5ba407-A\u524d \u5f80\u6ec5\u83cc\u5ba4-5, \u5b8c\u6210\u5f8c\u7e8c\u57f7\u884c\u4efb\u52d9\n"
"\u65b0\u589e\u4eba:\u8521\u660e\u52f3(1002)", None))
#endif // QT_CONFIG(tooltip)
        self.label_rp_7.setText(QCoreApplication.translate("MainWindow", u"0", None))

        __sortingEnabled = self.tableWidget_pending_mission_list.isSortingEnabled()
        self.tableWidget_pending_mission_list.setSortingEnabled(False)
        self.tableWidget_pending_mission_list.setSortingEnabled(__sortingEnabled)

        self.label_ori_m.setText(QCoreApplication.translate("MainWindow", u"ORI", None))
        self.label_y_rm.setText(QCoreApplication.translate("MainWindow", u"Y", None))
        self.label_x_m.setText(QCoreApplication.translate("MainWindow", u"X", None))
        self.label_4.setText(QCoreApplication.translate("MainWindow", u"\u76f8\u5c0d\u79fb\u52d5", None))
        self.label_x_rm.setText(QCoreApplication.translate("MainWindow", u"X", None))
        self.label_ori_rm.setText(QCoreApplication.translate("MainWindow", u"ORI", None))
        self.btn_StartRelativeMove.setText("")
        self.label_y_m.setText(QCoreApplication.translate("MainWindow", u"Y", None))
        self.btn_StartMission2.setText("")
        self.btn_StopMission2.setText("")
        self.label_5.setText(QCoreApplication.translate("MainWindow", u"\u57f7\u884c\u6307\u5b9a\u4efb\u52d9", None))
        self.label_IO.setText(QCoreApplication.translate("MainWindow", u"\u62c9\u8eca\u9802\u5347", None))
        self.btn_IO_Up.setText(QCoreApplication.translate("MainWindow", u"\u4e0a", None))
        self.btn_IO_down.setText(QCoreApplication.translate("MainWindow", u"\u4e0b", None))
        self.txtEdit_GetPM.setHtml(QCoreApplication.translate("MainWindow", u"<!DOCTYPE HTML PUBLIC \"-//W3C//DTD HTML 4.0//EN\" \"http://www.w3.org/TR/REC-html40/strict.dtd\">\n"
"<html><head><meta name=\"qrichtext\" content=\"1\" /><style type=\"text/css\">\n"
"p, li { white-space: pre-wrap; }\n"
"</style></head><body style=\" font-family:'PMingLiU'; font-size:16px; font-weight:400; font-style:normal;\">\n"
"<p style=\"-qt-paragraph-type:empty; margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:9pt;\"><br /></p></body></html>", None))
        self.label_7.setText(QCoreApplication.translate("MainWindow", u"\u7b49\u5f85\u4e2d\u4efb\u52d9", None))
        self.btn_GetPM.setText(QCoreApplication.translate("MainWindow", u"\u66f4\u65b0\u4efb\u52d9\u6e05\u55ae", None))
        self.btn_UpdateInfo.setText(QCoreApplication.translate("MainWindow", u"Current Status", None))
        self.label_8.setText(QCoreApplication.translate("MainWindow", u"check mir status", None))
        self.btn_SelectDestination.setText(QCoreApplication.translate("MainWindow", u"MAP", None))
        self.btn_SelectStart.setText(QCoreApplication.translate("MainWindow", u"MAP", None))
        self.btn_Start_Exhibition_Drink.setText(QCoreApplication.translate("MainWindow", u"\u5927\u5ef3\u9650\u5b9a", None))
        self.btn_Start_Exhibition_Military.setText(QCoreApplication.translate("MainWindow", u"\u5c55\u5834\u9650\u5b9a", None))
    # retranslateUi

