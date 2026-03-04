# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'admin_panel.ui'
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
from PySide6.QtWidgets import (QApplication, QLabel, QLineEdit, QListWidget,
    QListWidgetItem, QPushButton, QSizePolicy, QWidget)

class Ui_Form_AdminPanel(object):
    def setupUi(self, Form_AdminPanel):
        if not Form_AdminPanel.objectName():
            Form_AdminPanel.setObjectName(u"Form_AdminPanel")
        Form_AdminPanel.resize(400, 359)
        self.label_cur_user = QLabel(Form_AdminPanel)
        self.label_cur_user.setObjectName(u"label_cur_user")
        self.label_cur_user.setGeometry(QRect(10, 30, 141, 21))
        self.label = QLabel(Form_AdminPanel)
        self.label.setObjectName(u"label")
        self.label.setGeometry(QRect(10, 10, 191, 18))
        self.listWidget_user = QListWidget(Form_AdminPanel)
        self.listWidget_user.setObjectName(u"listWidget_user")
        self.listWidget_user.setGeometry(QRect(10, 60, 381, 131))
        self.label_new_user_input = QLabel(Form_AdminPanel)
        self.label_new_user_input.setObjectName(u"label_new_user_input")
        self.label_new_user_input.setGeometry(QRect(10, 200, 101, 21))
        self.lineEdit_new_user_input = QLineEdit(Form_AdminPanel)
        self.lineEdit_new_user_input.setObjectName(u"lineEdit_new_user_input")
        self.lineEdit_new_user_input.setGeometry(QRect(10, 230, 381, 26))
        self.lineEdit_new_pass_input = QLineEdit(Form_AdminPanel)
        self.lineEdit_new_pass_input.setObjectName(u"lineEdit_new_pass_input")
        self.lineEdit_new_pass_input.setGeometry(QRect(10, 260, 381, 26))
        self.btn_add = QPushButton(Form_AdminPanel)
        self.btn_add.setObjectName(u"btn_add")
        self.btn_add.setGeometry(QRect(10, 290, 181, 28))
        self.btn_del = QPushButton(Form_AdminPanel)
        self.btn_del.setObjectName(u"btn_del")
        self.btn_del.setGeometry(QRect(210, 290, 181, 28))
        self.btn_change_my_pw = QPushButton(Form_AdminPanel)
        self.btn_change_my_pw.setObjectName(u"btn_change_my_pw")
        self.btn_change_my_pw.setGeometry(QRect(10, 320, 381, 28))

        self.retranslateUi(Form_AdminPanel)

        QMetaObject.connectSlotsByName(Form_AdminPanel)
    # setupUi

    def retranslateUi(self, Form_AdminPanel):
        Form_AdminPanel.setWindowTitle(QCoreApplication.translate("Form_AdminPanel", u"Admin \u4f7f\u7528\u8005\u7ba1\u7406", None))
        self.label_cur_user.setText(QCoreApplication.translate("Form_AdminPanel", u"\u76ee\u524d\u4f7f\u7528\u8005", None))
        self.label.setText(QCoreApplication.translate("Form_AdminPanel", u"\u7ba1\u7406\u8005\uff1a", None))
        self.label_new_user_input.setText(QCoreApplication.translate("Form_AdminPanel", u"\u65b0\u589e\u5e33\u865f\uff1a", None))
        self.lineEdit_new_user_input.setText("")
        self.lineEdit_new_user_input.setPlaceholderText(QCoreApplication.translate("Form_AdminPanel", u"\u65b0\u4f7f\u7528\u8005\u5e33\u865f", None))
        self.lineEdit_new_pass_input.setText("")
        self.lineEdit_new_pass_input.setPlaceholderText(QCoreApplication.translate("Form_AdminPanel", u"\u65b0\u4f7f\u7528\u8005\u5bc6\u78bc", None))
        self.btn_add.setText(QCoreApplication.translate("Form_AdminPanel", u"\u65b0\u589e\u4f7f\u7528\u8005", None))
        self.btn_del.setText(QCoreApplication.translate("Form_AdminPanel", u"\u522a\u9664\u9078\u53d6\u4f7f\u7528\u8005", None))
        self.btn_change_my_pw.setText(QCoreApplication.translate("Form_AdminPanel", u"\u4fee\u6539\u81ea\u5df1\u7684\u5bc6\u78bc", None))
    # retranslateUi

