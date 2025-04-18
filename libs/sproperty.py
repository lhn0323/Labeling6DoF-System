import os
import sys
import PyQt5
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from .pyqtconfig.config import ConfigManager

from .pyqtconfig.qt import (QComboBox, QCheckBox, QSpinBox, QDoubleSpinBox, QMainWindow,
                            QLineEdit, QApplication, QTextEdit,
                            QGridLayout, QWidget, QDockWidget)

from vtk import *
import json
from libs.lsystem_config import SystemConfig


# 3DProperty停靠窗口的设计
class SProperty(QDockWidget):
    """Configure Dockable Widgets. This is a class for showing and modifying the configure of the software
    """
    signal_property_change = pyqtSignal(list)

    # 3DProperty窗口中的控件的初始化
    def __init__(self, parent, title="3DProperty"):
        """Constructor

        Args:
            title (str): windows title
            parent (QWdiget): the parent window
        """
        super().__init__(parent=parent)

        self.setWindowTitle(title)
        self.grid_layout = QGridLayout()
        self.config_edit = QTextEdit()
        # 管理3DProperty窗口中的控件，如显示的文本，控件的类型，控件的值及绑定的事件
        self.config = ConfigManager()
        self.is_changed = True

        # enumerate() 函数用于将一个可遍历的数据对象(如列表、元组或字符串)组合为一个索引序列，同时列出数据和数据下标，一般用在 for 循环当中
        for i, x in enumerate(["actor_id", 'x', 'y', 'z', 'rx', 'ry', 'rz', 'w', 'l', 'h', 's']):
            # QDoubleSpinBox() 函数用于创建一个带有浮点数值的微调控件
            width_spin = QDoubleSpinBox()
            width_spin.setMaximum(50000)
            width_spin.setMinimum(-50000)
            if x == "actor_id":
                # setDecimals() 函数用于设置浮点数的精度
                width_spin.setDecimals(0)
                width_spin.setValue(0)

            # 将config_data中预置的数值作为精度
            if x == "x" or x == "y" or x == "z":
                width_spin.setDecimals(float(SystemConfig.config_data["model"]["position_accuracy"]))
            if x == "w" or x == "l" or x == "h":
                width_spin.setDecimals(float(SystemConfig.config_data["model"]["size_accuracy"]))

            self.add(width_spin, x, 1 if x == 's' else 0, i + 1, 1)
            # s项为1，其余为0

            # 当控件的值发生变化时，调用lambda表达式，将场景中的模型状态更新
            width_spin.valueChanged.connect(lambda: self.parent(
            ).ui.vtk_panel.model_update_with_property(self.is_changed))

        self.window = QFrame()
        self.window.setLayout(self.grid_layout)
        self.setWidget(self.window)

    # 3DProperty窗口中微调控件的布局、初始值及索引等
    def add(self, widget, name, default_value, row, col):
        """The utils function of adding new configured items.

        Args:
            widget (QWidget): The widget you want to add for holding the configure item.
            name (str): configure item name. a QLabel widget will also be created.
            default_value (any): default value of the configure item.
            row (int): row index. (1-index based)
            col (int): column index. (1-index based)
        """
        hlayout = QHBoxLayout()
        label = QLabel(self)
        label.setText(name + ": ")
        hlayout.addWidget(label)
        hlayout.addWidget(widget)

        self.config.set_defaults({name: default_value})
        self.grid_layout.addLayout(hlayout, row, col)
        self.config.add_handler(name, widget)

    # 获取指定键的值
    def get(self, key):
        """Get the configure items

        Args:
            key (str): the key of configure item

        Returns:
            any: the value of configure item
        """
        return self.config.get(key)

    # 更新属性，将传入的（计算得到的）各种数据data传入设置中以显示出来
    @PyQt5.QtCore.pyqtSlot(list)
    def update_property(self, data):
        # for i in range(len(data)):
        #     print(data[i])
        # if语句存在的意义？循环中赋予的数值又会被覆盖。。
        if data[3] > float(SystemConfig.config_data["model"]["max_position"]):
            self.config.set("x", 0)
            self.config.set("y", 0)
            self.config.set("z", float(SystemConfig.config_data["model"]["initial_position"]))

        self.is_changed = False
        # zip() 函数用于将可迭代的对象作为参数，将对象中对应的元素打包成一个个元组，然后返回由这些元组组成的对象
        [self.config.set(s, d) for s, d in zip(
            ["actor_id", "x", "y", "z", "rz", "rx", "ry", "w", "l", "h"], data)
         ]
        self.is_changed = True

    # 将update信号与相关的函数进行绑定
    def connect(self, update):
        """connect the function `update` when the configure updated

        Args:
            update (function): the update function, def update(sender):
        """
        self.config.updated.connect(update)

    def roateX(self):
        self.is_changed = True
        self.config.set("rx", float(self.config.get("rx")) +
                        float(self.config.get("s")))

    def roateX_M(self):
        self.config.set("rx", float(self.config.get("rx")) -
                        float(self.config.get("s")))

    def roateY(self):
        self.config.set("ry", float(self.config.get("ry")) +
                        float(self.config.get("s")))

    def roateY_M(self):
        self.config.set("ry", float(self.config.get("ry")) -
                        float(self.config.get("s")))

    def roateZ(self):
        self.config.set("rz", float(self.config.get("rz")) +
                        float(self.config.get("s")))

    def roateZ_M(self):
        self.config.set("rz", float(self.config.get("rz")) -
                        float(self.config.get("s")))


if __name__ == '__main__':
    class MainWindow(QMainWindow):
        def __init__(self, parent=None):
            super(MainWindow, self).__init__(parent)
            layout = QHBoxLayout()

            self.items = SProperty(self, "3DProperty")

            self.setCentralWidget(QTextEdit())
            self.addDockWidget(Qt.RightDockWidgetArea, self.items)

            self.setLayout(layout)
            self.setWindowTitle('Dock')

        @staticmethod
        def update(sender):
            print(sender)


    app = QApplication(sys.argv)
    demo = MainWindow()
    demo.show()
    sys.exit(app.exec_())
