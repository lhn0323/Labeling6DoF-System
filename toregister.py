import pymysql
from PyQt5.QtCore import pyqtSignal
from PyQt5.QtWidgets import QWidget, QMessageBox

from register import Ui_Register


class ToRegister(QWidget, Ui_Register):
    # 定义一个注册成功信号
    SuccessReg = pyqtSignal()

    def __init__(self, parent=None):
        super(ToRegister, self).__init__(parent)
        self.register_ui = Ui_Register()
        self.register_ui.setupUi(self)
        self.initUi()
        self.clearregistertext()

    def initUi(self):

        self.register_ui.registerbutton.clicked.connect(self.emit_register)  # 确认
        self.register_ui.cancelregisterbutton.clicked.connect(self.emit_cancel_register)  # 取消

    def clearregistertext(self):
        self.register_ui.number_in.clear()
        self.register_ui.password_in.clear()
        self.register_ui.phone_in.clear()

    def emit_register(self):

        register_number = self.register_ui.number_in.text()
        register_password = self.register_ui.password_in.text()
        register_phone = self.register_ui.phone_in.text()
        if register_number == '' or register_password == '' or register_phone == '':
            QMessageBox.critical(self, '错误', '账号或密码或手机号不能为空')
            self.clearregistertext()
        else:
            # 连接数据库
            db = pymysql.connect(host='localhost', port=3306, user='root', passwd='156321', db='label')
            # 使用 cursor() 方法创建一个游标对象 cursor
            cursor = db.cursor()
            sql = "select * from login where number = %s"
            cursor.execute(sql, register_number)
            # 使用fetchone（）方法获取单条数据；b为None说明找不到此账号
            whether_number = cursor.fetchone()
            if whether_number is None:
                sql = "insert into login(number, password, phone) values(%s, %s, %s)"
                cursor.execute(sql, [register_number, register_password, register_phone])
                # 提交到数据库执行
                db.commit()
                QMessageBox.information(self, '提示', '注册成功')
                self.clearregistertext()
                self.SuccessReg.emit()
            else:
                QMessageBox.critical(self, '错误', '账号已存在')
                self.clearregistertext()
            # 关闭数据库
            cursor.close()
            db.close()

    def emit_cancel_register(self):
        self.clearregistertext()
        self.SuccessReg.emit()