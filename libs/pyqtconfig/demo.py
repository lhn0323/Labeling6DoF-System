'''
    创建并初始化应用程序窗口，添加子窗口，
    并在子窗口中使用相应的控件，最终调用函数显示窗口各项数据，
    并在每次触发更新信号时均对数据进行更新显示
'''
import sys
from .config import ConfigManager

from qt import (QComboBox, QCheckBox, QSpinBox, QMainWindow,
                QLineEdit, QApplication, QTextEdit,
                QGridLayout, QWidget)

class MainWindow(QMainWindow):

    def __init__(self):
        super(MainWindow, self).__init__()

        # 设置窗口标题为‘***’
        self.setWindowTitle('PyQtConfig Demo')
        # config.py中的类，用于管理配置管理器，此处创建对象
        self.config = ConfigManager()

        CHOICE_A = 1
        CHOICE_B = 2
        CHOICE_C = 3
        CHOICE_D = 4

        # 建立映射字典,作为下拉框的列表项
        map_dict = {
            'Choice A': CHOICE_A,
            'Choice B': CHOICE_B,
            'Choice C': CHOICE_C,
            'Choice D': CHOICE_D,
        }

        # C：设置默认值
        self.config.set_defaults({
            'number': 13,
            'text': 'hello',
            'active': True,
            'combo': CHOICE_C,
        })

        # 创建网格布局控件
        gd = QGridLayout()

        # QSpinBox()，主要处理整数和离散值集合的步长调节器控件，允许用户通过单击增减按钮或用键盘输入值来实现当前显示值的改变
        sb = QSpinBox()
        # 在gd中添加子窗口sb，（0，1）表示横纵坐标
        gd.addWidget(sb, 0, 1)
        # 为 number添加处理程序 sb
        self.config.add_handler('number', sb)

        # QLineEdit()，允许用户输入和编辑单行纯文本
        te = QLineEdit()
        gd.addWidget(te, 1, 1)
        self.config.add_handler('text', te)

        # QCheckBox(),复选框为用户提供 “多选多” 的选择
        cb = QCheckBox()
        gd.addWidget(cb, 2, 1)
        self.config.add_handler('active', cb)

        # QComboBox(),显示可见下拉列表，每个项（item，或称列表项）还可以关联一个 QVariant 类型的变量，用于存储一些不可见数据
        cmb = QComboBox()
        # 添加一个下拉选项
        cmb.addItems(map_dict.keys())
        gd.addWidget(cmb, 3, 1)
        self.config.add_handler('combo', cmb, mapper=map_dict)

        # QTextEdit()，可以加载纯文本和富文本文件，用来显示图像、列表和表格
        self.current_config_output = QTextEdit()
        # （待添加的子窗口，横坐标，纵坐标，横向跨越单元格数，纵向跨越单元格数）
        gd.addWidget(self.current_config_output, 0, 3, 3, 1)

        # 将配置管理器的更新信号与 show_config()连接起来
        self.config.updated.connect(self.show_config)

        # 将各配置的信息显示出来
        self.show_config()

        self.window = QWidget()
        self.window.setLayout(gd)
        self.setCentralWidget(self.window)

    # 将各配置的信息显示出来
    def show_config(self):
        # setText用于设置文本显示
        # as_dict()是类内的函数，将默认值和配置存入字典 result_dict中，作为返回值
        self.current_config_output.setText(str(self.config.as_dict()))

# Create a Qt application
app = QApplication(sys.argv)
# QSettings类中的内容：依次设置组织名称，组织的Internet域，应用程序名称
app.setOrganizationName("PyQtConfig")
app.setOrganizationDomain("martinfitzpatrick.name")
app.setApplicationName("PyQtConfig")

w = MainWindow()
w.show()
# 调用该方法进入程序的主循环直到调用exit （）结束
app.exec_()  # Enter Qt application main loop
