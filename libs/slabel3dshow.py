import os
import sys
import vtk
from vtkmodules.qt.QVTKRenderWindowInteractor import QVTKRenderWindowInteractor
from PyQt5 import QtCore, QtWidgets, QtGui
from PyQt5.QtCore import pyqtSignal
import typing


class SLabel3dShow(QtWidgets.QLabel):

    def __init__(self, parent, model_path):
        super().__init__(parent=parent)
        self.interactor = QVTKRenderWindowInteractor(self)
        self.render_window = self.interactor.GetRenderWindow()
        self.renderer = vtk.vtkRenderer()
        # 设置模型停靠窗口中加载模型的背景色，（白，完全不透明）
        self.renderer.SetBackground(1, 1, 1)
        self.renderer.SetBackgroundAlpha(1)
        self.style = vtk.vtkInteractorStyleTrackballCamera()
        self.interactor.SetInteractorStyle(self.style)
        self.render_window.AddRenderer(self.renderer)

        self.layout = QtWidgets.QHBoxLayout()
        self.layout.addWidget(self.interactor)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(self.layout)

        # analysis the obj model
        self.model_path = model_path
        # os.path.split()：分割路径，返回路径名和文件名的元组
        self.model_folder, self.obj_name = os.path.split(self.model_path)
        # 负数在右侧，则是排除了后n个
        self.obj_name = self.obj_name[:-4]
        self.mtl_path = self.model_folder + "/" + self.obj_name + ".obj.mtl"

        # self.load_3d_model()
        self.read_3d_model()

    def load_3d_model(self):
        reader = vtk.vtkOBJImporter()
        reader.SetFileName(self.model_path)
        reader.SetFileNameMTL(self.mtl_path)
        reader.SetTexturePath(self.model_folder)
        reader.SetRenderWindow(self.render_window)
        reader.Update()
        self.renderer.ResetCamera()

    def read_3d_model(self):
        self.model_path = self.model_path
        # 将obj文件转换为可渲染的对象
        self.actor = self.readObj(self.model_path)
        self.renderer.AddActor(self.actor)
        self.renderer.ResetCamera()

    # 加载obj文件，以此为输入最终转换为图元进行渲染显示
    def readObj(self, model_path):
        # 加载obj文件
        reader = vtk.vtkOBJReader()
        reader.SetFileName(model_path)
        reader.Update()

        # vtkPolyDataMapper:该类用于渲染多边形几何数据，将输入的数据转换为图元（点/线/多边形）进行渲染；
        # SetInputConnection: VTK可视化管线的输入数据接口。
        mapper = vtk.vtkPolyDataMapper()
        mapper.SetInputConnection(reader.GetOutputPort())

        actor = vtk.vtkActor()
        actor.SetMapper(mapper)
        return actor

    # 进行初始化并启动事件循环
    def start(self):
        self.interactor.Initialize()
        self.interactor.Start()

    def __del__(self):
        self.interactor.Finalize()
