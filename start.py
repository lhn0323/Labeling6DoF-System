import os
import sys
import pymysql
import vtk
from PyQt5 import uic
from PyQt5.QtCore import pyqtSignal
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QMessageBox

import toregister
from labelImg3d import Draw3D
from login import Ui_Login


class Start(QWidget, Ui_Login):
    SuccessLog = pyqtSignal()

    def __init__(self, parent=None):
        super(Start, self).__init__(parent)
        # 用于跳转注册界面
        self.re = toregister.ToRegister()
        self.login_ui = Ui_Login()
        self.login_ui.setupUi(self)
        self.initUi()
        self.clearlogintext()
        self.draw = Draw3D("volume")

    def initUi(self):
        # 跳转到注册页面
        self.login_ui.registerbutton.clicked.connect(self.register)
        # 注册或者取消跳转回来
        self.re.SuccessReg.connect(self.success_register)
        # 登录
        self.login_ui.loginbutton.clicked.connect(self.emit_login)
        # 取消登录
        self.login_ui.cancelloginbutton.clicked.connect(self.cancel_login)
        # 登录成功实现向主界面的跳转
        self.SuccessLog.connect(self.todraw)

    def clearlogintext(self):
        self.login_ui.number_in.clear()
        self.login_ui.password_in.clear()

    # 跳转到注册页面
    def register(self):
        self.re.show()
        windowLogin.close()  # 哪种写法？
        # self.close()

    # 成功注册或取消注册时返回
    def success_register(self):
        windowLogin.show()
        # self.close()
        self.re.close()

    # 输入账号和密码后，点击登录按钮，查询数据库判断账号信息是否正确
    def emit_login(self):
        # 获取输入的账号和密码
        login_number = self.login_ui.number_in.text()
        login_password = self.login_ui.password_in.text()
        # 判断账号和密码是否正确
        if login_number == '' or login_password == '':
            QMessageBox.critical(self, '错误','账号或密码不能为空')
            self.clearlogintext()
        else:
            # 连接数据库
            db = pymysql.connect(host='localhost', port=3306, user='root', passwd='156321', db='label')
            # 使用 cursor() 方法创建一个游标对象 cursor
            cursor = db.cursor()
            sql = "select password from login where number = %s"
            cursor.execute(sql, login_number)
            # 使用fetchone（）方法获取单条数据；b为None说明找不到此账号
            whether_number = cursor.fetchone()
            if whether_number is None:
                QMessageBox.critical(self, '错误','账号不存在')
                self.clearlogintext()
            elif whether_number[0] != login_password:
                QMessageBox.critical(self, '错误', '密码错误')
                self.clearlogintext()
            else:
                QMessageBox.information(self, '欢迎', '登录成功')
                # 此处还需一步跳转到 mainwindow
                self.clearlogintext()
                self.SuccessLog.emit()
            # 关闭数据库
            cursor.close()
            db.close()

    def cancel_login(self):
        # self.close()
        windowLogin.close()

    def todraw(self):

        vtk.vtkOutputWindow.SetGlobalWarningDisplay(0)
        os.chdir(os.path.dirname(__file__))
        # Recompile ui
        with open("libs/main.ui") as ui_file:
            with open("libs/Ui_main.py", "w") as py_ui_file:
                uic.compileUi(ui_file, py_ui_file)

        self.draw.show()
        self.draw.initialize()
        # self.close()
        windowLogin.close()

if __name__ == '__main__':
    # QApplication -> 应用程序，一个程序只能有一个应用程序接口
    # sys -> 获取系统的信息，比如命令行的，并且承担关闭窗口后完全退出的责任
    # 创建一个应用
    QApp = QApplication(sys.argv)
    # QMainWindow -> 主窗口，一个程序也只能有一个主窗口
    windowLogin = Start()
    # 调用show方法来显示窗口
    windowLogin.show()
    # 让窗口一直运行直到被关闭
    QApp.exec_()
