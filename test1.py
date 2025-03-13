from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_Login_Register(object):
    def setupUi(self, Login_Register):
        Login_Register.setObjectName("Login_Register")
        Login_Register.resize(800, 600)
        Login_Register.setMinimumSize(QtCore.QSize(800, 600))
        Login_Register.setMaximumSize(QtCore.QSize(800, 600))

        font = QtGui.QFont()
        font.setFamily("Arial")
        Login_Register.setFont(font)
        Login_Register.setStyleSheet("""
            background-color: rgb(240, 240, 240);
        """)

        self.groupBox = QtWidgets.QGroupBox(Login_Register)
        self.groupBox.setGeometry(QtCore.QRect(150, 150, 500, 300))
        self.groupBox.setStyleSheet("""
            background-color: rgba(255, 255, 255, 0.8);
            border-radius: 15px;
        """)  # Removed box-shadow
        self.groupBox.setObjectName("groupBox")
        self.formLayout = QtWidgets.QFormLayout(self.groupBox)
        self.formLayout.setSpacing(20)
        self.formLayout.setContentsMargins(30, 30, 30, 30)

        # Username
        self.username_label = QtWidgets.QLabel(self.groupBox)
        self.username_label.setText("用户名:")
        self.username_label.setFont(QtGui.QFont("Arial", 12))
        self.formLayout.setWidget(0, QtWidgets.QFormLayout.LabelRole, self.username_label)

        self.username_input = QtWidgets.QLineEdit(self.groupBox)
        self.username_input.setStyleSheet("""
            border: 2px solid #ccc;
            border-radius: 10px;
            padding: 10px;
            background-color: #f4f4f4;
        """)
        self.formLayout.setWidget(0, QtWidgets.QFormLayout.FieldRole, self.username_input)

        # Password
        self.password_label = QtWidgets.QLabel(self.groupBox)
        self.password_label.setText("密码:")
        self.password_label.setFont(QtGui.QFont("Arial", 12))
        self.formLayout.setWidget(1, QtWidgets.QFormLayout.LabelRole, self.password_label)

        self.password_input = QtWidgets.QLineEdit(self.groupBox)
        self.password_input.setEchoMode(QtWidgets.QLineEdit.Password)
        self.password_input.setStyleSheet("""
            border: 2px solid #ccc;
            border-radius: 10px;
            padding: 10px;
            background-color: #f4f4f4;
        """)
        self.formLayout.setWidget(1, QtWidgets.QFormLayout.FieldRole, self.password_input)

        # Buttons layout
        self.buttonLayout = QtWidgets.QHBoxLayout()
        self.buttonLayout.setSpacing(15)

        # Login Button
        self.login_button = QtWidgets.QPushButton("登录", self.groupBox)
        self.login_button.setFont(QtGui.QFont("Arial", 12))
        self.login_button.setStyleSheet("""
            background-color: #66b3ff;
            color: white;
            border-radius: 10px;
            padding: 10px 20px;
        """)
        self.buttonLayout.addWidget(self.login_button)

        # Register Button
        self.register_button = QtWidgets.QPushButton("注册", self.groupBox)
        self.register_button.setFont(QtGui.QFont("Arial", 12))
        self.register_button.setStyleSheet("""
            background-color: #ff7f50;
            color: white;
            border-radius: 10px;
            padding: 10px 20px;
        """)
        self.buttonLayout.addWidget(self.register_button)

        self.formLayout.setLayout(2, QtWidgets.QFormLayout.FieldRole, self.buttonLayout)

        # Background Image
        self.bg_image = QtWidgets.QLabel(Login_Register)
        self.bg_image.setGeometry(QtCore.QRect(0, 0, 800, 600))
        self.bg_image.setStyleSheet("""
            border-image: url('background.jpg');
            border-radius: 20px;
        """)
        self.bg_image.setObjectName("bg_image")
        self.bg_image.setAlignment(QtCore.Qt.AlignCenter)

        self.retranslateUi(Login_Register)
        QtCore.QMetaObject.connectSlotsByName(Login_Register)

    def retranslateUi(self, Login_Register):
        _translate = QtCore.QCoreApplication.translate
        Login_Register.setWindowTitle(_translate("Login_Register", "登录与注册"))
        
        self.username_label.setText(_translate("Login_Register", "用户名:"))
        self.password_label.setText(_translate("Login_Register", "密码:"))
        self.login_button.setText(_translate("Login_Register", "登录"))
        self.register_button.setText(_translate("Login_Register", "注册"))

# Run the application
if __name__ == "__main__":
    app = QtWidgets.QApplication([])
    MainWindow = QtWidgets.QWidget()
    ui = Ui_Login_Register()
    ui.setupUi(MainWindow)
    MainWindow.show()
    app.exec_()
