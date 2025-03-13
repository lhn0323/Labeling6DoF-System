import os
import sys
import numpy as np
import PyQt5
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
import typing
from .slabel3dshow import SLabel3dShow
import vtk
from pathlib import Path
import json


# QDockWidget:停靠窗口；停靠在 QMainWindow 的中央部件 (central widget) 的上下左右四个区域，停靠的 QDockWidget 没有框架，有一个较小的标题栏；也可浮动出来作为独立窗口。
# 用于显示模型列表的停靠窗口
class SModelList(QDockWidget):
    signal_load_model = pyqtSignal(int, int)
    signal_double_click = pyqtSignal(str, int, str)
    signal_model_class = pyqtSignal(list)
    obj = None

    # 修饰器：修饰类中的方法，使其可以在不创建类实例的情况下调用方法
    @staticmethod
    def create(parent, title="models"):
        SModelList.obj = SModelList(parent, title)
        return SModelList.obj

    @staticmethod
    def get():
        return SModelList.obj

    def __init__(self, parent, title="models"):
        super().__init__(parent=parent)
        self.setWindowTitle(title)
        self.verticalLayout = QtWidgets.QVBoxLayout(self)
        self.verticalLayout.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout.setObjectName("verticalLayout")
        self.horizontalLayout = QtWidgets.QHBoxLayout()
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.horizontalLayout.setAlignment(QtCore.Qt.AlignLeft)
        self.btnOpenFolder = QtWidgets.QPushButton(self)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.btnOpenFolder.sizePolicy().hasHeightForWidth())
        self.btnOpenFolder.setSizePolicy(sizePolicy)
        self.btnOpenFolder.setObjectName("btnOpenFolder")
        self.btnOpenFolder.setText("&Open 3D Models")
        self.btnOpenFolder.setVisible(False)
        self.horizontalLayout.addWidget(self.btnOpenFolder)
        self.progress_bar_load = QtWidgets.QProgressBar(self)
        self.progress_bar_load.setProperty("value", 24)
        self.progress_bar_load.setObjectName("progress_bar_load")
        self.progress_bar_load.setVisible(False)
        self.horizontalLayout.addWidget(self.progress_bar_load)
        self.horizontalLayout.setStretch(0, 2)
        self.horizontalLayout.setStretch(1, 8)
        self.verticalLayout.addLayout(self.horizontalLayout)
        self.listWidget = QtWidgets.QListWidget(self)
        self.listWidget.setObjectName("listWidget")
        self.verticalLayout.addWidget(self.listWidget)

        self.window = QFrame()
        self.window.setLayout(self.verticalLayout)
        self.setWidget(self.window)
        # connect
        # self.btnOpenFolder.clicked.connect(self.open_files)
        # connect the double click event of self.listWidget
        self.listWidget.doubleClicked.connect(self.listWidgetDoubleClicked)

        # file list
        self.file_list = []
        self.model_list = {}
        self.model_info = {}

    # 根据传入的序数，设置（并滚动到）模型列表中的当前行及选中状态等
    @PyQt5.QtCore.pyqtSlot(str)
    def highlight_item(self, model_file):
        try:
            index = self.file_list.index(model_file)
            if index < self.listWidget.count():
                self.listWidget.setCurrentRow(index)
                self.listWidget.item(index).setSelected(True)
                self.listWidget.setFocus()
        except Exception as e:
            print(e)

    # 根据文件路径，读取将此路径下的json文件中存储的有关各种模型的信息，还实现了读取时的进度条显示
    @PyQt5.QtCore.pyqtSlot(list)
    def open_files(self, file_list=None):
        # file_list, _ = QtWidgets.QFileDialog.getOpenFileNames(
        #     None, "Open 3D Model", "./", "3D Models (*.obj)")

        # # filter
        # file_list = list(set(file_list).difference(self.file_list))
        # self.file_list += file_list

        if file_list is None or len(file_list) == 0:
            return
        # file_list = ['E:/GitCode/LabelImg3D/scenes/KITTI\\models\\car_001.obj',...],path为文件路径
        models_info_file = Path(file_list[0]).parent / "models.json"
        # models_info_file: E:/GitCode/LabelImg3D/scenes/KITTI\models\models.json

        # if you cannot find the models.json, then generate it automatically
        if not os.path.exists(models_info_file):
            # print("not exists")
            for i, f in enumerate(file_list):
                # Path(f).name:文件名；Path(f).stem:去掉文件后缀的文件名
                self.model_info[Path(f).name] = {"class_name": Path(f).stem[:-4], "class_index": i+1}
                # 因此此处自动生成的json文件只有name和index两项，而原有的json还有size项
            with open(models_info_file, 'w+') as f:
                json.dump(self.model_info, f, indent=4)
        else:
            # print("exists")
            with open(models_info_file, "r") as f:
                # 使用 json.load()将其他类型的对象转为Python对象，操作对象为文件流而非字符串
                self.model_info = json.load(f)

        self.file_list = file_list
        self.progress_bar_load.setVisible(True)

        num_model = len(file_list)
        for i in range(num_model):
            self.signal_load_model.emit(i, num_model)
            self.add_item(file_list[i])
            self.progress_bar_load.setValue((i+1)/num_model*100)
            # event loop
            # 让程序处理那些还没有处理的事件，然后再把使用权返回给调用者
            QCoreApplication.processEvents()

        self.progress_bar_load.setVisible(False)

    # 根据模型路径加载模型，使其在此停靠窗口显示
    def add_item(self, model_path):
        name = os.path.split(model_path)[-1][:-4]
        item = QListWidgetItem(self.listWidget, 0)
        widgets = QWidget(self)
        # SLabel3dShow ：用于显示3D模型
        model_label = SLabel3dShow(self, model_path)
        self.model_list[model_path] = model_label.actor
        # QLabel：用于显示模型的名称
        text_label = QLabel(name)
        widget_layout = QHBoxLayout()

        item.setSizeHint(QSize(300, 300))
        widget_layout.addWidget(model_label)
        widget_layout.addWidget(text_label)
        # 设置模型显示区域和模型名称显示区域的比例，索引0和索引1，分别按照3:1比例进行伸缩
        widget_layout.setStretch(0, 3)
        widget_layout.setStretch(1, 1)
        widgets.setLayout(widget_layout)
        # 将模型显示区域和模型名称显示区域添加到item中
        self.listWidget.setItemWidget(item, widgets)
        # 启动模型显示区域的事件循环
        model_label.start()

    # 根据所给模型的路径，获取该模型的 mapper并进行深复制，返回深复制后的 mapper实体化后的 actor
    def getActor(self, model_path):
        # 若路径不在列表中则返回空值
        if model_path not in self.model_list.keys():
            print("Cannot find the 3d model {}".format(model_path))
            return None
        actor = self.model_list[model_path]
        copy_data = vtk.vtkPolyData()
        copy_data.DeepCopy(actor.GetMapper().GetInput())

        # vtkPolyDataMapper()将输入的数据转换为几何图元进行渲染
        mapper = vtk.vtkPolyDataMapper()
        mapper.SetInputData(copy_data)

        actor = vtk.vtkActor()
        # SetMapper 用于设置生成几何图元的mapper，即连接一个actor到可视化管线的末端
        actor.SetMapper(mapper)
        return actor

    # 双击模型名称会将本模型安装到主窗口的3D显示区域，本函数用于传递信号以及打印所添加的模型所在的路径
    def listWidgetDoubleClicked(self, index):
        # index.row()：返回当前行的行号
        file_path = self.file_list[index.row()]
        class_name, class_index = list(self.model_info[Path(file_path).name].values())[0:2]
        self.signal_double_click.emit(file_path, class_index, class_name)
        print("添加模型：", self.file_list[index.row()])


if __name__ == '__main__':
    class MainWindow(QMainWindow):
        def __init__(self,parent=None):
            super(MainWindow, self).__init__(parent)
            layout=QHBoxLayout()

            self.items=SModelList(self, "Models")

            self.setCentralWidget(QTextEdit())
            self.addDockWidget(Qt.LeftDockWidgetArea, self.items)

            self.setLayout(layout)
            # self.setWindowTitle('Dock')

        @staticmethod
        def update(sender):
            print(sender)

    app=QApplication(sys.argv)
    demo=MainWindow()
    demo.show()
    sys.exit(app.exec_())