from PyQt5.QtCore import *
from PyQt5.QtWidgets import QMessageBox
from PyQt5 import QtWidgets
from libs.Ui_system_config import Ui_System_config
import json
from libs.utils.utils import get_distance, get_fov
import os
from pathlib import Path
import sys


# 设计config窗口界面，实现各种控件所控制的参数的更新和调用等；
# 从system_config.json文件中获取参数的默认值并显示在控件中，参数值被改变时，将新的参数值写入system_config.json文件中
class SystemConfig(QObject):
    # sys.argv[0]表示代码本身文件路径；parent()获得路径的逻辑父级；joinpath()拼接路径；
    # （拼接后的路径是 E:\GitCode\LabelImg3D\libs\system_config.json
    # .json文件中存储了camera和model两种类型下的参数的初始值）
    # 总之，判断拼接后的路径是否为普通文件
    if Path(sys.argv[0]).parent.joinpath('system_config.json').is_file():
        # 以只读方式(r)打开该文件，将读取对象赋给 load_f
        with open(Path(sys.argv[0]).parent.joinpath('system_config.json'), 'r') as load_f:
            # 并使用 json.load()将其他类型的对象转为Python对象，操作对象为文件流而非字符串
            config_data = json.load(load_f)
    else:
        # dirname()返回父路径； abspath()返回当前运行脚本的绝对路径；join()用于路径拼接文件路径;
        # 已对比pathlib和os的区别，但不知此处使用if区分的目的是什么？？？？？？
        with open(os.path.join(os.path.abspath(os.path.dirname(__file__)), 'system_config.json'), 'r') as load_f:
            config_data = json.load(load_f)
    signal_update_camera_property = pyqtSignal(list)  # 传递列表数据，实现多个窗口之间的数据传递

    def __init__(self, parent):
        # 继承父类的引用方法
        super().__init__(parent)
        self.window = QtWidgets.QWidget()
        self.ui = Ui_System_config()
        self.ui.setupUi(self.window)
        self.ui.Camera_parameter.addItem("fov")
        self.ui.Camera_parameter.addItem("distance")

        # system parameter
        # System_config窗口中 model控件的五个属性的初始数值
        self.initial_position = SystemConfig.config_data["model"]["initial_position"]
        self.max_position = SystemConfig.config_data["model"]["max_position"]
        self.position_accuracy = SystemConfig.config_data["model"]["position_accuracy"]
        self.size_accuracy = SystemConfig.config_data["model"]["size_accuracy"]
        self.scaling_factor = SystemConfig.config_data["model"]["scaling_factor"]

        # System_config窗口中 camera控件的属性的初始数值
        self.camera_matrix = SystemConfig.config_data["camera"]["matrix"]
        self.camera_position = SystemConfig.config_data["camera"]["position"]
        self.camera_focalPoint = SystemConfig.config_data["camera"]["focalPoint"]
        self.camera_fov = SystemConfig.config_data["camera"]["fov"]
        self.camera_viewup = SystemConfig.config_data["camera"]["viewup"]
        self.camera_distance = SystemConfig.config_data["camera"]["distance"]

        self.camera_parameter_value = self.camera_fov

        # connect
        self.ui.Btn_apply.clicked.connect(self.apply)
        # currentIndexChanged.connect()：当下拉列表的索引发生改变时，触发该信号
        self.ui.Camera_parameter.currentIndexChanged.connect(self.change_camera_parameter)

    # 显示文本
    def show(self):
        self.ui.lineEdit_initial_position.setText(str(self.initial_position))
        self.ui.lineEdit_max_position.setText(str(self.max_position))
        self.ui.lineEdit_position_accuracy.setText(str(self.position_accuracy))
        self.ui.lineEdit_size_accuracy.setText(str(self.size_accuracy))
        self.ui.lineEdit_scaling_factor.setText(str(self.scaling_factor))
        self.ui.Camera_parameter_value.setText(str(self.camera_parameter_value))
        self.window.show()

    # 改变参数时进行更新
    def change_camera_parameter(self):
        if self.ui.Camera_parameter.currentText() == "fov":
            self.camera_parameter_value = self.camera_fov
        else:
            self.camera_parameter_value = self.camera_distance
        self.ui.Camera_parameter_value.setText(str(self.camera_parameter_value))

    # 将更新后的参数(输入的数值)写入system_config.json进行应用，其中使用一些异常处理对参数更新的过程进行检测
    def apply(self):
        # camera config
        if self.ui.Camera_parameter.currentText() == "fov":
            try:
                self.camera_fov = float(self.ui.Camera_parameter_value.text())
            except ValueError:
                QMessageBox.critical(self.window, "Error",
                                     "Invalid input data {}!".format(self.ui.Camera_parameter_value.text()),
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.Yes)
                return
            self.camera_distance = get_distance(self.camera_fov)
        else:
            try:
                self.camera_distance = float(self.ui.Camera_parameter_value.text())
            except ValueError:
                QMessageBox.critical(self.window, "Error",
                                     "Invalid input data {}!".format(self.ui.Camera_parameter_value.text()),
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.Yes)
                return
            # 根据相机坐标系到世界坐标系之间的距离可以计算水平视场角fov
            self.camera_fov = get_fov(self.camera_distance)

        # 相机坐标
        self.camera_position = [0, 0, self.camera_distance]
        # 构造相机矩阵，三维点的齐次表达，引入一个新的维度（貌似是绕着相机平移的一个矩阵）
        self.camera_matrix = [1.0, 0.0, 0.0, 0.0,
                              0.0, 1.0, 0.0, 0.0,
                              0.0, 0.0, 1.0, self.camera_distance,
                              0.0, 0.0, 0.0, 1.0]
        # model config
        try:
            self.initial_position = float(self.ui.lineEdit_initial_position.text())
            self.max_position = float(self.ui.lineEdit_max_position.text())
            self.position_accuracy = int(self.ui.lineEdit_position_accuracy.text())
            self.size_accuracy = int(self.ui.lineEdit_size_accuracy.text())
            self.scaling_factor = float(self.ui.lineEdit_scaling_factor.text())
        except ValueError:
            QMessageBox.critical(self.window, "Error", "Invalid input data!",
                                 QMessageBox.Yes | QMessageBox.No, QMessageBox.Yes)

            self.initial_position = SystemConfig.config_data["model"]["initial_position"]
            self.max_position = SystemConfig.config_data["model"]["max_position"]
            self.position_accuracy = SystemConfig.config_data["model"]["position_accuracy"]
            self.size_accuracy = SystemConfig.config_data["model"]["size_accuracy"]
            self.scaling_factor = SystemConfig.config_data["model"]["scaling_factor"]

            return

            # update SystemConfig.config_data
        SystemConfig.config_data["camera"]["matrix"] = self.camera_matrix
        SystemConfig.config_data["camera"]["position"] = self.camera_position
        SystemConfig.config_data["camera"]["focalPoint"] = self.camera_focalPoint
        SystemConfig.config_data["camera"]["fov"] = self.camera_fov
        SystemConfig.config_data["camera"]["viewup"] = self.camera_viewup
        SystemConfig.config_data["camera"]["distance"] = self.camera_distance

        SystemConfig.config_data["model"]["initial_position"] = self.initial_position
        SystemConfig.config_data["model"]["max_position"] = self.max_position
        SystemConfig.config_data["model"]["position_accuracy"] = self.position_accuracy
        SystemConfig.config_data["model"]["size_accuracy"] = self.size_accuracy
        SystemConfig.config_data["model"]["scaling_factor"] = self.scaling_factor

        # Save to local file(.json)
        # if not Path(sys.argv[0]).parent.joinpath('system_config.json').is_file():

        # ’w+'读写模式
        with open(Path(sys.argv[0]).parent.joinpath('system_config.json'), 'w+') as f:
            # json.dump()是把python对象转换成json对象生成一个 f 的文件流并写入文件，和文件相关
            # 设置indent=4, 数据增加换行符, 数据层级以4个空格为缩进
            json.dump(SystemConfig.config_data, f, indent=4)

        # update scene
        # emit实现不同类中参数的传递
        self.signal_update_camera_property.emit(self.camera_position + [self.camera_fov, self.camera_distance])
