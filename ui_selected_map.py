# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'selected_map.ui'
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
from PySide6.QtWidgets import (QApplication, QLabel, QLineEdit, QPushButton,
    QSizePolicy, QWidget)
import images_rc

class Ui_Form_SelectedMap(object):
    def setupUi(self, Form_SelectedMap):
        if not Form_SelectedMap.objectName():
            Form_SelectedMap.setObjectName(u"Form_SelectedMap")
        Form_SelectedMap.resize(1200, 928)
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(Form_SelectedMap.sizePolicy().hasHeightForWidth())
        Form_SelectedMap.setSizePolicy(sizePolicy)
        font = QFont()
        font.setFamilies([u"Noto Sans TC"])
        font.setPointSize(24)
        font.setBold(True)
        Form_SelectedMap.setFont(font)
        Form_SelectedMap.setStyleSheet(u"background-color: rgb(0, 0, 0);")
        self.label_sm_map_1 = QLabel(Form_SelectedMap)
        self.label_sm_map_1.setObjectName(u"label_sm_map_1")
        self.label_sm_map_1.setGeometry(QRect(20, 90, 1152, 672))
        self.label_sm_map_1.setStyleSheet(u"")
        self.label_sm_map_1.setPixmap(QPixmap(u":/img/picture/MiR floor plan_V7_Demo_now_edit_V1.png"))
        self.label_sm_map_1.setAlignment(Qt.AlignCenter)
        self.btn_sm_cancel = QPushButton(Form_SelectedMap)
        self.btn_sm_cancel.setObjectName(u"btn_sm_cancel")
        self.btn_sm_cancel.setGeometry(QRect(20, 870, 564, 40))
        font1 = QFont()
        font1.setFamilies([u"Noto Sans TC"])
        font1.setBold(True)
        self.btn_sm_cancel.setFont(font1)
        self.btn_sm_cancel.setStyleSheet(u"QPushButton {\n"
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
        self.btn_sm_enter = QPushButton(Form_SelectedMap)
        self.btn_sm_enter.setObjectName(u"btn_sm_enter")
        self.btn_sm_enter.setGeometry(QRect(600, 870, 564, 40))
        self.btn_sm_enter.setFont(font1)
        self.btn_sm_enter.setStyleSheet(u"QPushButton {\n"
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
        self.label_sm_text1 = QLabel(Form_SelectedMap)
        self.label_sm_text1.setObjectName(u"label_sm_text1")
        self.label_sm_text1.setGeometry(QRect(30, 770, 141, 21))
        font2 = QFont()
        font2.setFamilies([u"Noto Sans TC"])
        font2.setBold(False)
        self.label_sm_text1.setFont(font2)
        self.label_sm_text1.setStyleSheet(u"color: white;                  /* \u767d\u5b57 */\n"
"font-size: 16px")
        self.label_sm_text2 = QLabel(Form_SelectedMap)
        self.label_sm_text2.setObjectName(u"label_sm_text2")
        self.label_sm_text2.setGeometry(QRect(30, 20, 501, 61))
        font3 = QFont()
        font3.setFamilies([u"Noto Sans TC"])
        font3.setPointSize(16)
        font3.setBold(True)
        self.label_sm_text2.setFont(font3)
        self.label_sm_text2.setStyleSheet(u"color: white;                  /* \u767d\u5b57 */\n"
"")
        self.lineEdit_sm_selectedpoint = QLineEdit(Form_SelectedMap)
        self.lineEdit_sm_selectedpoint.setObjectName(u"lineEdit_sm_selectedpoint")
        self.lineEdit_sm_selectedpoint.setGeometry(QRect(30, 810, 521, 41))
        self.lineEdit_sm_selectedpoint.setFont(font3)
        self.lineEdit_sm_selectedpoint.setStyleSheet(u"color: white;                  /* \u767d\u5b57 */\n"
"")
        self.retranslateUi(Form_SelectedMap)

        QMetaObject.connectSlotsByName(Form_SelectedMap)
    # setupUi

    def retranslateUi(self, Form_SelectedMap):
        Form_SelectedMap.setWindowTitle(QCoreApplication.translate("Form_SelectedMap", u"\u5730\u5716", None))
        self.label_sm_map_1.setText("")
        self.btn_sm_cancel.setText(QCoreApplication.translate("Form_SelectedMap", u"\u53d6\u6d88", None))
        self.btn_sm_enter.setText(QCoreApplication.translate("Form_SelectedMap", u"\u78ba\u5b9a", None))
        self.label_sm_text1.setText(QCoreApplication.translate("Form_SelectedMap", u"\u5df2\u9078\u64c7:", None))
        self.label_sm_text2.setText(QCoreApplication.translate("Form_SelectedMap", u"\u8acb\u9ede\u9078\u5730\u5716\u8a2d\u5b9a\u76ee\u7684\u5730", None))
        self.lineEdit_sm_selectedpoint.setText("")
    # retranslateUi

