import os
import sys
import vtk
import cv2
from vtkmodules.qt.QVTKRenderWindowInteractor import QVTKRenderWindowInteractor
import PyQt5
from PyQt5 import QtCore, QtWidgets, QtGui
from PyQt5.QtCore import QSize, pyqtSignal, QCoreApplication, QObject
import typing
import math
from libs.utils.utils import *
from PyQt5.QtWidgets import QMessageBox


# 管理场景的类，实现场景导入切换等
class SceneManager(QObject):
    signal_open_files = pyqtSignal(list)
    signal_open_models = pyqtSignal(list)
    signal_highlight_image_list = pyqtSignal(int)

    def __init__(self, parent, image_list_panel, model_list_panel, vtk_panel) -> None:
        super().__init__(parent=parent)
        self.window = QtWidgets.QWidget()
        self.image_list_panel = image_list_panel
        self.model_list_panel = model_list_panel
        self.vtk_panel = vtk_panel

        self.scene_folder = ''
        self.images_folder = ''
        self.models_folder = ''
        self.annotations_folder = ''

        self.image_name_list = []
        self.model_name_list = []
        self.annotation_name_list = []

        self.current_index = -1

    # 导入场景
    def init_scenes(self):
        """load the scenes, the folder structure should be as follows:

        ..--------
        . --------
        |--models <only obj support>
        |--images <only jpg support>
            |--scene1
            |--scene2
            |-- ...
        |--annotations
            |--scene1
            |--scene2
            |-- ...
        """
        # 打开一个已经存在的文件夹
        scene_folder = QtWidgets.QFileDialog.getExistingDirectory(None, "Choose Scene Folder")
        if scene_folder == '':
            QMessageBox.critical(self.window, "Error", "No files selected!",
                                 QMessageBox.Yes | QMessageBox.No,
                                 QMessageBox.Yes)
            return

        # E:/GitCode/LabelImg3D/scenes/KITTI
        self.scene_folder = scene_folder
        # 1. get all the images
        # E:/GitCode/LabelImg3D/scenes/KITTI\\images
        self.images_folder = os.path.join(self.scene_folder, 'images')
        self.image_name_list = getFiles(self.images_folder, ['.jpg'])
        if not self.image_name_list:
            # ['scene1\\000025.png', ......,'scene2\\000025.png', ......]
            self.image_name_list = getFiles(self.images_folder, ['.png'])

        # 2. get all the annotations
        # 'E:/GitCode/LabelImg3D/scenes/KITTI\\annotations'
        self.annotations_folder = os.path.join(self.scene_folder, 'annotations')
        self.annotation_name_list = [
            # 从start后第一个文件夹开始计算相对路径，借用image_name_list的文件名表示标注文件名列表
            os.path.relpath(os.path.join(self.annotations_folder, i)[:-4] + '.json', self.annotations_folder) for i in
            self.image_name_list]
        # ['scene1\\000025.json', ......]
        # 3. get all the models
        self.models_folder = os.path.join(self.scene_folder, 'models')
        self.model_name_list = getFiles(self.models_folder, ['.obj'])

        # 4. get the first item
        # 文件加载完毕后，利用循环将模型和图像的路径通过信号传递出去
        if len(self) > 0:
            self.signal_open_models.emit([os.path.join(self.models_folder, i) for i in self.model_name_list])
            self.signal_open_files.emit([os.path.join(self.images_folder, i) for i in self.image_name_list])
            # 调用私有函数__getitem__，加载第一张图像的场景
            self[0]
            # self
        else:
            QMessageBox.critical(self.window, "Error", "File structure error!",
                                 QMessageBox.Yes | QMessageBox.No,
                                 QMessageBox.Yes)

    def __len__(self):
        return len(self.image_name_list)

    def __getitem__(self, index):
        if type(index) is not int:
            index = index.row()
        if index < 0 or index >= len(self):
            return
        # 1. check annotation_folder
        self.vtk_panel.loadScenes(self.scene_folder, os.path.join(self.images_folder, self.image_name_list[index]),
                                  os.path.join(self.annotations_folder, self.annotation_name_list[index]))

        # 传递信号，选中图像的序数，使选中的图像的该行高亮显示
        self.signal_highlight_image_list.emit(index)

        if self.current_index != index:
            self.vtk_panel.saveScenes()
            self.current_index = index

    # Shortcut key operation
    def next(self):
        self[self.current_index + 1]

    def previous(self):
        self[self.current_index - 1]

    def home(self):
        self[0]

    def end(self):
        self[len(self) - 1]
