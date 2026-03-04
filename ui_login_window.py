# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'login_window.ui'
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

class Ui_Form_LoginWindow(object):
    def setupUi(self, Form_LoginWindow):
        if not Form_LoginWindow.objectName():
            Form_LoginWindow.setObjectName(u"Form_LoginWindow")
        Form_LoginWindow.resize(350, 220)
        self.label_title = QLabel(Form_LoginWindow)
        self.label_title.setObjectName(u"label_title")
        self.label_title.setGeometry(QRect(100, 30, 141, 18))
        self.label_title.setAlignment(Qt.AlignCenter)
        self.lineEdit_username_input = QLineEdit(Form_LoginWindow)
        self.lineEdit_username_input.setObjectName(u"lineEdit_username_input")
        self.lineEdit_username_input.setGeometry(QRect(20, 80, 301, 26))
        self.lineEdit_username_input.setAlignment(Qt.AlignLeading|Qt.AlignLeft|Qt.AlignVCenter)
        self.lineEdit_password_input = QLineEdit(Form_LoginWindow)
        self.lineEdit_password_input.setObjectName(u"lineEdit_password_input")
        self.lineEdit_password_input.setGeometry(QRect(20, 140, 301, 26))
        self.lineEdit_password_input.setAlignment(Qt.AlignLeading|Qt.AlignLeft|Qt.AlignVCenter)
        self.btn_login = QPushButton(Form_LoginWindow)
        self.btn_login.setObjectName(u"btn_login")
        self.btn_login.setGeometry(QRect(130, 180, 93, 28))
        self.label_username = QLabel(Form_LoginWindow)
        self.label_username.setObjectName(u"label_username")
        self.label_username.setGeometry(QRect(20, 50, 70, 18))
        self.label_password = QLabel(Form_LoginWindow)
        self.label_password.setObjectName(u"label_password")
        self.label_password.setGeometry(QRect(20, 110, 70, 18))

        self.retranslateUi(Form_LoginWindow)

        QMetaObject.connectSlotsByName(Form_LoginWindow)
    # setupUi

    def retranslateUi(self, Form_LoginWindow):
        Form_LoginWindow.setWindowTitle(QCoreApplication.translate("Form_LoginWindow", u"\u767b\u5165\u7cfb\u7d71", None))
        self.label_title.setText(QCoreApplication.translate("Form_LoginWindow", u"\u767b\u5165\u7cfb\u7d71", None))
        self.lineEdit_username_input.setText("")
        self.lineEdit_username_input.setPlaceholderText(QCoreApplication.translate("Form_LoginWindow", u"\u4f7f\u7528\u8005\u5e33\u865f", None))
        self.lineEdit_password_input.setText("")
        self.lineEdit_password_input.setPlaceholderText(QCoreApplication.translate("Form_LoginWindow", u"\u5bc6\u78bc", None))
        self.btn_login.setText(QCoreApplication.translate("Form_LoginWindow", u"\u767b\u5165", None))
        self.label_username.setText(QCoreApplication.translate("Form_LoginWindow", u"\u5e33\u865f", None))
        self.label_password.setText(QCoreApplication.translate("Form_LoginWindow", u"\u5bc6\u78bc", None))
    # retranslateUi

