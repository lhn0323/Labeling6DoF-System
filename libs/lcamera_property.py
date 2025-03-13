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
from math import degrees, radians, tan, atan
from PIL import Image


# Camera_Property停靠窗口的设计
class LCamera_Property(QDockWidget):
    """Configure Dockable Widgets. This is a class for showing and modifying the configure of the camera
    """
    signal_camera_change = pyqtSignal(list)

    def __init__(self, parent, title="Camera_Property"):
        """Constructor

        Args:
            title (str): windows title
            parent (QWdiget): the parent window
        """
        super().__init__(parent=parent)

        self.setWindowTitle(title)
        self.grid_layout = QGridLayout()
        # self.layout().addChildLayout(self.grid_layout)
        self.config_edit = QTextEdit()
        self.config = ConfigManager()
        self.camera_data = []
        self.is_change = True
        self.img_size = []

        for i, x in enumerate(['x', 'y', 'z', "fov", 'distance']):
            # QDoubleSpinBox() 函数用于创建一个带有浮点数值的微调控件
            width_spin = QDoubleSpinBox()
            width_spin.setMaximum(50000)
            width_spin.setMinimum(-50000)
            self.add(width_spin, x, 0, i + 1, 1)

            # 当控件的值发生变化时，调用lambda表达式，更新？？？相机的状态
            width_spin.valueChanged.connect(lambda: self.update_camera_data())
            #
            width_spin.valueChanged.connect(
                lambda: self.parent().ui.vtk_panel.actor_manager.update_camera(self.camera_data, self.is_change))

        self.window = QFrame()
        self.window.setLayout(self.grid_layout)
        self.setWidget(self.window)

    # 在config中设置单个微调控件的布局及初始值，并绑定一些处理程序（完成事件响应等）；
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

    def get(self, key):
        """Get the configure items

        Args:
            key (str): the key of configure item

        Returns:
            any: the value of configure item
        """
        return self.config.get(key)

    def connect(self, update):
        """connect the function `update` when the configure updated

        Args:
            update (function): the update function, def update(sender):
        """
        self.config.updated.connect(update)

    # 当控件中相机参数发生改变，相应的在主窗口中也要更新相机参数
    @PyQt5.QtCore.pyqtSlot()
    def update_camera_data(self):
        if self.is_change is False:
            return

        # 获取当前控件中相机参数的值
        camera_data_present = [self.config.get(p)
                               for p in ["x", "y", "z", "fov", "distance"]]

        num = -1
        for i in range(len(camera_data_present)):
            if camera_data_present[i] == self.camera_data[i]:
                pass
            else:
                num = i

        if num == 0 or num == 1:  # x or y
            self.config.set("x", 0.00)
            self.config.set("y", 0.00)

        # The three(z, fov and distance) are interrelated
        if num == 2:  # z
            self.is_change = False
            if camera_data_present[2] != 0:
                self.config.set("distance", camera_data_present[2])
                # self.image_width *（ 1 / self.image_width）/(2 * z)
                # fov = degrees(2 * atan(1 / (2 * distance)))   水平视场角
                fov = degrees(2 * atan((self.img_size[0] * self.parent().ui.vtk_panel.image_scale) /
                                       (2 * camera_data_present[2])))
                self.config.set("fov", fov)

            self.is_change = True

        if num == 3:  # fov
            self.is_change = False
            try:
                distance = (self.img_size[0] * self.parent().ui.vtk_panel.image_scale) / \
                           (2 * (tan(radians(camera_data_present[3] / 2))))
                self.config.set("z", distance)
                self.config.set("distance", distance)
            except Exception as e:
                print(f"Exception in {__name__}: {e}")
            self.is_change = True
            pass

        if num == 4:  # distance
            self.is_change = False
            if camera_data_present[4] != 0:
                self.config.set("z", camera_data_present[4])
                # fov = degrees(2 * atan(1 / (2 * distance)))
                fov = degrees(2 * atan((self.img_size[0] * self.parent().ui.vtk_panel.image_scale) /
                                       (2 * camera_data_present[4])))
                self.config.set("fov", fov)

            self.is_change = True

        self.camera_data.clear()
        self.camera_data = [self.config.get(p)
                            for p in ["x", "y", "z", "fov", "distance"]]

    # 清楚原有相机参数，更新相机参数
    @PyQt5.QtCore.pyqtSlot(list)
    def new_camera_data(self, new_camera_data):
        self.camera_data.clear()
        self.is_change = False

        for i in range(len(new_camera_data)):
            self.camera_data.append(new_camera_data[i])
            # print(self.camera_data[i])

        self.config.set("x", self.camera_data[0])
        self.config.set("y", self.camera_data[1])
        self.config.set("z", self.camera_data[2])
        self.config.set("fov", self.camera_data[3])
        self.config.set("distance", self.camera_data[4])
        # image.size = (width, height)
        self.img_size = Image.open(self.parent().image_list.file_list[0]).size

        self.is_change = True

    # update camera data when changing system config
    @PyQt5.QtCore.pyqtSlot(list)
    def update_camera(self, camera_data):
        self.config.set("x", camera_data[0])
        self.config.set("y", camera_data[1])
        self.config.set("z", camera_data[2])
        self.config.set("fov", camera_data[3])
        self.config.set("distance", camera_data[4])


if __name__ == '__main__':
    class MainWindow(QMainWindow):
        def __init__(self, parent=None):
            super(MainWindow, self).__init__(parent)
            layout = QHBoxLayout()

            self.items = LCamera_Property(self, "Camera_Property")

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
