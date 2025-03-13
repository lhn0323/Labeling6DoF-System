import os
import sys
import vtk
import cv2
import json
from vtkmodules.qt.QVTKRenderWindowInteractor import QVTKRenderWindowInteractor
import PyQt5
from PyQt5 import QtCore, QtWidgets, QtGui
import typing
import math
from vtk import *
from vtkmodules.vtkCommonCore import vtkMath, vtkCommand
from vtkmodules.vtkCommonMath import vtkMatrix4x4
from vtkmodules.vtkCommonTransforms import vtkTransform
from vtkmodules.vtkFiltersSources import vtkOutlineSource
from vtkmodules.vtkInteractionStyle import vtkInteractorStyleTrackballActor
from vtkmodules.vtkRenderingCore import vtkActor, vtkCellPicker, vtkPolyDataMapper

from libs.utils.utils import *
import pandas as pd
from libs.actor_manager import Actor, ActorManager
from libs.sproperty import *
# import tqdm
import numpy as np
from pathlib import Path
from libs.lsystem_config import SystemConfig
import webbrowser

# from PIL import Image


# 使用 vtkInteractorStyleTrackballActor 交互器类来通过鼠标对单个actor的position进行调整
# 该类主要设计 vtk交互
class MouseInteractorHighLightActor(vtkInteractorStyleTrackballActor):
    def __init__(self, slabel, parent=None):
        self.slabel = slabel
        # 向 VTK 对象添加监听器（回调）（要响应的事件、vtk命令、指定优先级值）
        self.AddObserver('LeftButtonPressEvent', self.OnLeftButtonDown, -1)
        self.AddObserver('LeftButtonReleaseEvent', self.OnLeftButtonUp, -1)
        self.AddObserver('RightButtonPressEvent', self.OnRightButtonDown, -1)
        self.AddObserver('RightButtonReleaseEvent', self.OnRightButtonUp, -1)
        self.AddObserver('MouseMoveEvent', self.OnMouseMove, -1)
        self.AddObserver('MouseWheelForwardEvent', self.OnMouseWheelForward, -1)
        self.AddObserver('MouseWheelBackwardEvent', self.OnMouseWheelBackward, -1)
        self.AddObserver('CharEvent', self.RemoveKeyR, -1)
        self.super = super(MouseInteractorHighLightActor, self)
        # 调用reset函数用于清除？？
        self.reset()

    # 用户在按下并放开键盘上的按钮时所触发的事件，但是键盘上的功能区按钮是无法识别的
    def RemoveKeyR(self, obj, event):
        # GetKeySym()获取按下的键的键符号
        key = self.GetInteractor().GetKeySym()
        # 这些按键在vtk中有特别的交互，此处做屏蔽（但从测试结果来看几乎无影响）
        if key in ['r', 'R', 'Control_L', 'Control_R']:
            return
        self.super.OnKeyPress()

    # 设置选中模型的边界框的光照属性、颜色角度等
    def HighlightProp3D(self, prop3D):
        # no prop picked now
        if prop3D is None:
            if (self.PickedRenderer != None and self.OutlineActor):
                # 向渲染器删除 actor
                self.PickedRenderer.RemoveActor(self.OutlineActor)
                self.PickedRenderer = None
        else:
            if self.OutlineActor is None:
                self.OutlineActor = vtkActor()
                # 设置/获取可选取的实例变量。这确定是否可以拾取 vtkProp（通常使用鼠标）。初值为真
                self.OutlineActor.PickableOff()
                # 设置/获取可拖动实例变量的值。决定了道具一旦被拾取，是否可以在空间中平移。为了防止从用户界面中拖动某些 vtkProp。初始值为真。
                self.OutlineActor.DragableOff()
                # 映射器：将参与者连接到可视化管道末端的方法
                self.OutlineActor.SetMapper(self.OutlineMapper)
                # GetProperty():设置/获取控制此 actors 表面属性的属性对象。这应该是 vtkProperty 对象的实例
                self.OutlineActor.GetProperty().SetColor(self.PickColor)
                # 设置环境光系数；表示各种光线照射到物体材质上，经过很多次发射后最终在环境中的光线强度；数值越高越亮
                self.OutlineActor.GetProperty().SetAmbient(1.0)
                # 设置/获取线的宽度，宽度以屏幕单位表示
                self.OutlineActor.GetProperty().SetLineWidth(3)
                # 设置漫反射光系数；表示各种光线照射到物体材质上，经过很多次发射后最终在环境中的光线强度；
                self.OutlineActor.GetProperty().SetDiffuse(0.0)

            # 获取当前渲染器，若为未捕获的渲染器，根据渲染器和渲染对象的状态选择删除或添加actor
            if self.GetCurrentRenderer() != self.PickedRenderer:
                if self.PickedRenderer is not None and self.OutlineActor is not None:
                    self.PickedRenderer.RemoveActor(self.OutlineActor)
                if self.GetCurrentRenderer() is not None:
                    self.GetCurrentRenderer().AddActor(self.OutlineActor)
                self.PickedRenderer = self.GetCurrentRenderer()
            # SetBoxTypeToOriented():设置盒的类型为有方向的;将框类型设置为 Oriented
            self.Outline.SetBoxTypeToOriented()
            # 在 Oriented 模式下指定轮廓的角，值以 8*3 双精度值的形式提供 正确的角排序是对单位立方体使用 {x,y,z} 约定
            self.Outline.SetCorners(Actor.get8Corners(prop3D).reshape(-1))

    # 重置?当模型被选中时，生成指定颜色的边界框
    def reset(self):
        self.is_first = True
        # vtkCellPicker用于拾取某个单元，并返回交点的信息（vtk交互之拾取）
        # 拾取时也是投射一条光线至拾取点，在一定的容差范围内确定光线是否与Actor底层的几何相交，最后返回的就是沿着光线最靠近相机的单元及其相应的对象
        self.InteractionPicker = vtkCellPicker()
        self.isPressedRight = False
        self.isPressedLeft = False
        self.isMouse_Pressed_Move = False
        # self.resetHighlight()
        self.InteractionProp = None

        # for hightlight3D
        self.OutlineActor = None
        # vtkOutlineSource()：继承自vtkPolyDataAlgorithm类，用于创建边界盒状或者带弧度角度的poly data
        self.Outline = vtkOutlineSource()
        # vtkPolyDataMapper()：继承自vtkMapper类，用于将poly data映射到图形硬件上
        self.OutlineMapper = vtkPolyDataMapper()
        if (self.OutlineMapper and self.Outline):
            self.OutlineMapper.SetInputConnection(self.Outline.GetOutputPort())
        self.PickedRenderer = None
        self.CurrentProp = None
        self.PickColor = [1.0, 0.0, 0.0]  # red
        # self.HighlightProp3D(None)

    # 重置模型边界框的光照属性等
    def resetHighlight(self):
        if len(self.slabel.actor_manager.actors) > 0:
            self.InteractionProp = self.slabel.actor_manager.actors[-1].actor
            self.slabel.switchBoxWidgets(self.InteractionProp)
        else:
            self.InteractionProp = None

        self.HighlightProp3D(self.InteractionProp)

    def __del__(self):
        del self.InteractionPicker

    # 设置对象的不透明度，使模型被移动时变稍微透明...
    def SetOpacity(self, op=0.5):
        if self.InteractionProp is not None:
            # 设置对象的不透明度；1.0 是完全不透明的，0.0 是完全透明的
            self.InteractionProp.GetProperty().SetOpacity(op)

    # 交互器观察器获取坐标，对此位置执行拾取，取拾取对象列表中末尾元素，对其设置图层等参数信息
    def switchLayer(self):
        x, y = self.GetInteractor().GetEventPosition()

        # GetProp3D()返回已选取的 vtkProp；Pick()使用提供的选择点执行拾取操作，成功拾取时返回值不为0
        all_picked_actors = [self.InteractionPicker.GetProp3D() for a in self.slabel.actor_manager.actors \
                             if self.InteractionPicker.Pick(x, y, 0, a.renderer) != 0]
        if len(all_picked_actors) > 0:
            # 取最后一个元素（其实只拾取到一个）
            self.NewPickedActor = all_picked_actors[-1]
            # 若取得的元素不为空且不为渲染对象列表（注：非拾取后的渲染对象列表）中最后一个元素即与之前所执行的结果不符，
            if self.NewPickedActor and self.NewPickedActor is not self.slabel.actor_manager.actors[-1].actor:
                # 设置重新选择的actor的相关信息，图层渲染器状态等
                self.slabel.switchBoxWidgets(self.NewPickedActor)

    # 左键按下，观察器获取坐标，对该位置的模型进行场景渲染
    def OnLeftButtonDown(self, obj, event):
        if self.GetCurrentRenderer() is None:
            return

        self.isPressedLeft = True
        self.isMouse_Pressed_Move = False

        if not self.isMouse_Pressed_Move:
            # 当前的 x,y 位置在 EventPosition 中，之前的事件位置在 LastEventPosition 中，每次使用其 Set() 方法设置 EventPosition 时自动更新。
            x, y = self.GetInteractor().GetEventPosition()
            # 设置此位置捕获对象的图层等参数信息
            self.switchLayer()

            self.InteractionPicker.Pick(x, y, 0.0, self.GetCurrentRenderer())
            # GetViewProp()返回已选取的 vtkProp
            self.InteractionProp = self.InteractionPicker.GetViewProp()
            # 设置物体的光照属性及旋转属性
            self.HighlightProp3D(self.InteractionProp)

            # 处理鼠标左键的消息的函数，调用 vtk本身的事件函数，而非自定义的
            self.super.OnLeftButtonDown()

    # 左键松开，对当前渲染器、交互器等参数进行更新
    def OnLeftButtonUp(self, obj, event):
        self.isPressedLeft = False
        if self.InteractionProp is None:
            return
        # 设置对象为完全不透明
        self.SetOpacity(1)

        # 向信号传递参数
        # GetOrientation()返回物体的旋转角度
        self.slabel.signal_on_left_button_up.emit(
            [self.slabel.actor_manager.actors[-1].actor_id] +
            list(self.InteractionProp.GetPosition() + self.InteractionProp.GetOrientation()) +
            self.slabel.actor_manager.actors[-1].size
        )

        self.slabel.signal_update_images.emit(
            # 绘制投影的3D框
            drawProjected3DBox(
                self.GetCurrentRenderer(),
                self.InteractionProp,
                self.slabel.image_data.copy(),
                with_clip=True)
        )

        self.super.OnLeftButtonUp()

    # 右键按下，设置物体的光照属性及旋转属性等
    def OnRightButtonDown(self, obj, event):
        self.isPressedRight = True
        self.isMouse_Pressed_Move = False
        self.switchLayer()
        x, y = self.GetInteractor().GetEventPosition()
        self.InteractionPicker.Pick(x, y, 0.0, self.GetCurrentRenderer())
        self.InteractionProp = self.InteractionPicker.GetViewProp()
        self.HighlightProp3D(self.InteractionProp)

        self.super.OnRightButtonDown()

    # 右键松开，更新透明度
    def OnRightButtonUp(self, obj, event):
        self.isPressedRight = False
        self.SetOpacity(1)
        self.super.OnRightButtonUp()

    def Prop3DTransform(self, prop3D, boxCenter, numRotation, rotate, scale):
        oldMatrix = vtkMatrix4x4()
        prop3D.GetMatrix(oldMatrix)

        orig = prop3D.GetOrigin()

        newTransform = vtkTransform()
        newTransform.PostMultiply()
        if prop3D.GetUserMatrix() is not None:
            newTransform.SetMatrix(prop3D.GetUserMatrix())
        else:
            newTransform.SetMatrix(oldMatrix)

        newTransform.Translate(-boxCenter[0], -boxCenter[1], -boxCenter[2])

        for i in range(numRotation):
            newTransform.RotateWXYZ(*(rotate[i][j] for j in range(3)))

        if 0 not in scale:
            newTransform.Scale(*scale)

        newTransform.Translate(*boxCenter)

        newTransform.Translate(*(-orig[i] for i in range(3)))
        newTransform.PreMultiply()
        newTransform.Translate(*orig)

        if prop3D.GetUserMatrix() is not None:
            newTransform.GetMatrix(prop3D.GetUserMatrix())
        else:
            prop3D.SetPosition(newTransform.GetPosition())
            prop3D.SetScale(newTransform.GetScale())
            prop3D.SetOrientation(newTransform.GetOrientation())

        del oldMatrix
        del newTransform

    # 依据比例因子
    def UniformScale(self, Scaling_factor):
        if self.GetCurrentRenderer() is None or self.InteractionProp is None:
            return
        rwi = self.GetInteractor()
        # 获取鼠标在y轴移动的距离
        dy = rwi.GetEventPosition()[1] - rwi.GetLastEventPosition()[1]
        obj_center = self.InteractionProp.GetCenter()
        center = self.GetCurrentRenderer().GetCenter()

        direction = []
        camera = self.GetCurrentRenderer().GetActiveCamera()
        if camera.GetParallelProjection():
            camera.ComputeViewPlaneNormal()
            direction = camera.GetViewPlaneNormal()
        else:
            cam_x, cam_y, cam_z = self.GetCurrentRenderer().GetActiveCamera().GetPosition()
            # 方向向量
            direction = list((obj_center[0] - cam_x, obj_center[1] - cam_y, obj_center[2] - cam_z))

        # 返回向量的范数
        vtkMath.Normalize(direction)

        # yf = dy / center[1] *  10.0
        # scaleFactor = 0.1 * (1.1 ** yf)
        # 运动向量，比例因子 * 方向向量 * y轴移动距离
        motion_vector = [-Scaling_factor * d * dy for d in direction]
        if self.InteractionProp.GetUserMatrix() is not None:
            t = vtkTransform()
            t.PostMultiply()
            t.SetMatrix(self.InteractionProp.GetUserMatrix())
            t.Translate(*motion_vector)
            self.InteractionProp.GetUserMatrix().DeepCopy(t.GetMatrix())
            del t
        else:
            #
            self.InteractionProp.AddPosition(*motion_vector)

        # if self.GetAutoAdjustCameraClippingRange():
        #     self.GetCurrentRenderer().ResetCameraClippingRange()

        rwi.Render()

    # 鼠标移动时...？
    def OnMouseMove(self, obj, event):
        if self.InteractionProp is None or (not self.isPressedLeft and not self.isPressedRight):
            return

        self.isMouse_Pressed_Move = True

        self.HighlightProp3D(self.InteractionProp)
        self.SetOpacity(0.5)

        x, y = self.GetInteractor().GetEventPosition()

        # Right mouse button movement operation
        # if self.isPressedRight and not self.GetInteractor().GetShiftKey():
        if self.isPressedRight:
            # 确定该位置的事件是哪个渲染器
            self.FindPokedRenderer(x, y)
            #
            self.UniformScale(float(SystemConfig.config_data["model"]["scaling_factor"]))
            self.InvokeEvent(vtkCommand.InteractionEvent, None)
        else:
            self.super.OnMouseMove()
            self.GetInteractor().Render()

        # GetOrientation：从变换矩阵中获取 x、y、z 方向角作为三个（浮点值）的数组
        self.slabel.signal_on_left_button_up.emit(
            [self.slabel.actor_manager.actors[-1].actor_id] +
            list(self.InteractionProp.GetPosition() + self.InteractionProp.GetOrientation()) +
            self.slabel.actor_manager.actors[-1].size
        )
        self.slabel.signal_update_images.emit(
            drawProjected3DBox(
                self.GetCurrentRenderer(),
                self.InteractionProp,
                self.slabel.image_data.copy(),
                with_clip=True)
        )

        self.slabel.actor_manager.ResetCameraClippingRange()
        self.GetInteractor().Render()

    def OnMouseWheelForward(self, obj, event):
        self.super.OnMouseWheelForward()

    def OnMouseWheelBackward(self, obj, event):
        self.super.OnMouseWheelBackward()

# 自定义的一个控件
class SLabel3DAnnotation(QtWidgets.QFrame):
    # 传递列表、数组数据，实现多个窗口之间的数据传递
    signal_on_left_button_up = pyqtSignal(list)
    signal_load_scene = pyqtSignal(list)
    # 是用 np.ndarray类的对象 表示n维数组对象
    signal_update_images = pyqtSignal(np.ndarray)

    # 交互的初始状态
    def __init__(self, parent):
        super().__init__(parent=parent)
        # vtkRenderWindowInteractor用于获取渲染窗口上发生的鼠标，键盘，事件事件
        self.interactor = QVTKRenderWindowInteractor(self)

        self.bg_renderer = vtk.vtkRenderer()  # 创建一个 vtkRenderer（窗口渲染器）
        self.bg_renderer.SetBackground(0, 0, 0)  # 设置背景颜色，即初始背景为黑色
        self.bg_renderer.SetBackgroundAlpha(1)  # 设置背景透明度(包括分割线）
        self.bg_renderer.SetLayer(0)  # 设置此渲染器所属的图层，便于构建多层结构，
        # 有效的位置范围是从 0 到该层中组件数减一所得的值。值 -1 指示最底层位置。值 0 指示最顶层位置。
        self.bg_renderer.InteractiveOff()  # 关闭交互状态，交互式渲染器是可以从交互器接收事件的渲染器

        self.renderer_window = self.interactor.GetRenderWindow()  # GetRenderWindow():指定要在其中绘制的渲染窗口
        self.renderer_window.SetNumberOfLayers(1)  # 设置渲染器的层数
        self.renderer_window.AddRenderer(self.bg_renderer)  # 将渲染器添加到渲染器列表

        self.style = MouseInteractorHighLightActor(self) # MouseInteractorHighLightActor类:定义actor操作方法，这个是一个鼠标操作控件的控制方法
        self.interactor.SetInteractorStyle(self.style)  # 该方法用于定义交互器样式

        self.layout = QtWidgets.QHBoxLayout()  # 创建 QHBoxLayout 对象，用于布局其他控件，组成自定义控件的基础控件
        self.layout.addWidget(self.interactor)
        self.layout.setContentsMargins(0, 0, 0, 0)  # 设置要在布局周围使用的左、上、右和下边距
        self.setLayout(self.layout)  # 将此小部件的布局管理器设置为布局
        # 获取默认相机 GetPosition()：(0.0, 0.0, 1.0)；GetDirectionOfProjection()：(0.0, 0.0, -1.0)（从相机位置到焦点的方向的矢量）；
        # camera1 = self.bg_renderer.GetActiveCamera()
        # add the axes actor to the background
        # vtkAxesActor 是一个混合的 2D/3D actor，用于表示场景中的 3D 轴，
        # axes.GetPosition():(0.0, 0.0, 0.0);axes.GetOrientation():(0.0, -0.0, 0.0)？
        axes = vtk.vtkAxesActor()
        # 为三个轴设置文本，文本将看起来跟随相机.启用/禁用绘制轴标签
        axes.SetAxisLabels(True)

        # 创建描述线性变换的矩阵
        transform = vtk.vtkTransform()
        transform.Translate(0, 0, 0.01)  # 平移矩阵
        # usermatrix：用户设置的变换矩阵???
        axes.SetUserTransform(transform)  # 设置用户设置的变换矩阵

        # show axes
        # self.bg_renderer.AddActor(axes)

        self.image_actor = None
        self.image_path = None
        self.image_data = None

        # 实例化 ActorManager类的一个对象，该类用于完成渲染器窗口的事件交互和渲染场景
        self.actor_manager = ActorManager(self.renderer_window, self.interactor, self.bg_renderer)

        # 图像比例
        self.image_scale = 0

        self.json_data = None

        self.is_first_scene = True

        # QApplication.clipboard().changed.connect(self.copy)
        self.copy_actor = None

    # 复制最近一个actor
    def copy(self):
        if self.style.InteractionProp is None:
            self.copy_actor = None
            return
        self.copy_actor = self.actor_manager.actors[-1]
        pass

    # 将复制得到的actor进行渲染，绘制场景
    def paste(self):
        if self.copy_actor is None:
            return
        self.actor_manager.newActor(self.copy_actor.model_path, self.copy_actor.type_class,
                                    self.copy_actor.model_name, self.copy_actor.actor_id)

    # 为了使用交互器，通过Initialize()和 start()方法进行初始化并启动事件循环
    def start(self):
        self.interactor.Initialize()
        self.interactor.Start()

    # 导入图象并设置其相关矩阵、尺度等
    @PyQt5.QtCore.pyqtSlot(str)
    def loadImage(self, image_path):
        if not os.path.exists(image_path):
            return

        self.image_path = image_path

        # remove the previous loaded actors
        if self.image_actor is not None:
            self.bg_renderer.RemoveActor(self.image_actor)
            self.image_actor = None

        # get image width and height
        image = cv_imread(image_path)
        # (375, 1242, 3)
        self.image_height, self.image_width, _ = image.shape
        # 为什么缩放因子设为1/width(？)
        self.image_scale = 1 / self.image_width
        # 宽高比的用处？？
        self.image_ratio = self.image_width / self.image_height
        self.image_data = image

        # Read image data
        if self.image_path.split(".")[-1] == "png":
            img_reader = vtk.vtkPNGReader()
        else:
            img_reader = vtk.vtkJPEGReader()

        # SetFileName()方法用于设置图像文件名
        img_reader.SetFileName(image_path)
        # 调用 Update()方法促使管线执行
        img_reader.Update()
        image_data = img_reader.GetOutput()
        self.image_actor = vtk.vtkImageActor()
        self.image_actor.SetInputData(image_data)

        # self.image_actor.GetBounds():(0.0, 1241.0, 0.0, 374.0, 0.0, 0.0);.GetCenter():(620.5, 187.0, 0.0)
        transform = vtk.vtkTransform()
        # Scale()方法用于设置缩放因子
        transform.Scale(self.image_scale, self.image_scale, self.image_scale)
        # Translate()方法用于设置平移因子
        transform.Translate(-self.image_width / 2, -self.image_height / 2, 0)
        # SetUserTransform()方法用于设置用户设置的变换矩阵；对图像进行放缩和平移。
        self.image_actor.SetUserTransform(transform)
        self.bg_renderer.AddActor(self.image_actor)
        # ResetCamera()方法用于重置相机
        self.bg_renderer.ResetCamera()
        # Render()方法用于渲染场景
        self.interactor.Render()

    # 导入模型
    @PyQt5.QtCore.pyqtSlot(str, int, str)
    def loadModel(self, model_path, model_class, model_name, id=0):
        self.actor_manager.newActor(model_path, model_class, model_name, id)

    # 获取 actor的序数并以此为索引设置actor的相关信息
    def switchBoxWidgets(self, actor):
        index = self.actor_manager.getIndex(actor)
        # 获取的序数的正常结果不可能为-1
        if index != -1:
            self.actor_manager.setActiveActor(index)

    # 导入场景，包括图像和标注
    @PyQt5.QtCore.pyqtSlot(str, str, str)
    def loadScenes(self, scene_folder, image_file, annotation_file):
        # save the last scene before switch scenes
        # a = self.is_first_scene   # a:True
        if self.is_first_scene is True:
            self.is_first_scene = False
        else:
            self.saveScenes()
            # self.exportScenes()

        # clear all the actors
        # scene_folder:   E:/GitCode/LabelImg3D/scenes/KITTI
        self.scene_folder, self.image_file, self.annotation_file = scene_folder, image_file, annotation_file
        # remove the image layer
        if self.image_actor is not None:
            self.bg_renderer.RemoveActor(self.image_actor)
        # remove all actors
        self.actor_manager.clear()
        self.style.reset()

        # load the image
        self.loadImage(image_file)
        # self.bg_renderer.GetActiveCamera().GetPosition(): (0.0, 0.0, 10.790363967354063)

        # load the scenes
        # 根据路径访问标注文件(000025.json)时如果数据读取失败，调用getEmptyJson()方法获取设置的默认参数值赋给data
        data = self.actor_manager.loadAnnotation(annotation_file)
        # 最初设置相机参数的依据
        if data is None:
            data = self.actor_manager.getEmptyJson(os.path.relpath(self.image_path, self.scene_folder))

        self.json_data = data
        # 设置相机参数
        self.actor_manager.setCamera(self.json_data["camera"])
        # 将模型加入到场景中
        self.actor_manager.createActors(self.scene_folder, self.json_data)
        self.actor_manager.ResetCameraClippingRange()

        camera = self.bg_renderer.GetActiveCamera()
        camera_data = [camera.GetPosition()[0], camera.GetPosition()[1], camera.GetPosition()[2],
                       camera.GetViewAngle(), camera.GetDistance()]
        # 发送信号，导入场景时传递相机参数数据
        self.signal_load_scene.emit(camera_data)

    # 保存场景相关数据到annotations/{}-kitti/{}.txt
    @PyQt5.QtCore.pyqtSlot()
    def exportScenes(self):
        if not self.parent().parent().ui.actionKITTI.isChecked():
            return

        if self.image_path is None or self.image_actor is None:
            return

        text_file = Path(self.image_path).parent.parent.parent / (
            Path('annotations/{}-kitti/{}.txt'.format(Path(self.image_path).parent.stem, Path(self.image_path).stem)))
        # print(text_file)
        # E:\GitCode\LabelImg3D\scenes\KITTI\annotations\scene1-kitti\000025.txt
        if not os.path.exists(text_file.parent):
            os.makedirs(text_file.parent)

        camera = self.bg_renderer.GetActiveCamera()
        data = []
        for i in range(len(self.actor_manager.actors)):
            actor = self.actor_manager.actors[i]
            data += [actor.toKITTI()]

        np.savetxt(text_file, np.array(data), delimiter=" ", fmt='%s')

    # 保存场景相关数据到json文件
    @PyQt5.QtCore.pyqtSlot()
    def saveScenes(self):
        if self.image_path is None or self.image_actor is None:
            return
        self.data = {}
        # 保存图像文件的相对路径
        # image_path:  E:/GitCode/LabelImg3D/scenes/KITTI\images\scene1\000025.png
        # scene_folder:  E:/GitCode/LabelImg3D/scenes/KITTI
        # image_file:  images\scene1\000025.png
        self.data["image_file"] = os.path.relpath(self.image_path, self.scene_folder)
        # 更新 data 中 model的各参数
        self.data.update(self.actor_manager.toJson(self.scene_folder))
        # GetPosition()：(0.0, 0.0, 0.52)
        camera = self.bg_renderer.GetActiveCamera()
        self.data["camera"] = {}

        # GetModelViewTransformMatrix():返回一个矩阵，它是当前摄像机的模型视图变换矩阵。
        # GetInverse():返回一个矩阵，它是当前变换矩阵的逆矩阵。
        # print("camera.GetModelViewTransformMatrix()\n", camera.GetModelViewTransformMatrix())
        # print("getTransform(camera.GetModelViewTransformMatrix())\n", getTransform(camera.GetModelViewTransformMatrix()))
        transform = getTransform(camera.GetModelViewTransformMatrix()).GetInverse()
        # 获取相机坐标系到世界坐标系的变换矩阵（存疑：因为此处不是直接使用camera.GetMatrix()）
        self.data["camera"]["matrix"] = matrix2List(transform.GetMatrix())
        # 获取相机在世界坐标系下的坐标并保留小数
        self.data["camera"]["position"] = listRound(transform.GetPosition())
        # 默认的焦点位置在世界坐标系的原点 O
        self.data["camera"]["focalPoint"] = listRound(camera.GetFocalPoint())
        # GetViewAngle():返回当前摄像机的视角（垂直视场角）
        self.data["camera"]["fov"] = camera.GetViewAngle()
        # GetViewUp():返回当前摄像机的视线方向
        self.data["camera"]["viewup"] = listRound(camera.GetViewUp())
        # 返回从相机位置到焦点的距离；预设成像宽为1，故distance与焦距相等。
        self.data["camera"]["distance"] = camera.GetDistance()
        if not os.path.exists(os.path.dirname(self.annotation_file)):
            os.makedirs(os.path.dirname(self.annotation_file))
        # E:/GitCode/LabelImg3D/scenes/KITTI\annotations\scene1\000025.json
        with open(self.annotation_file, 'w+') as f:
            # json.dump()：将python中的对象转化成json储存到文件中
            json.dump(self.data, f, indent=4)

    # 当模型的属性发生变化时，更新模型的属性
    @PyQt5.QtCore.pyqtSlot(bool)
    def model_update_with_property(self, is_changed):
        if is_changed is False:
            return
        if not self.style.isPressedLeft:
            if self.style.InteractionProp is None and len(self.actor_manager.actors) > 0:
                self.style.InteractionProp = self.actor_manager.actors[-1].actor
            elif self.style.InteractionProp is None and len(self.actor_manager.actors) == 0:
                return

            #
            data = [self.parent().parent().property3d.config.get(p)
                    for p in ["actor_id", "x", "y", "z", "rz", "rx", "ry"]]
            # data = [round(Ro, 2) for Ro in data]
            data = [data[0]] + self.resize_Angle(data[1:])

            self.actor_manager.actors[-1].actor_id = data[0]

            Rotate = self.style.InteractionProp.GetOrientation()  # Z, X, Y
            Rotate = [round(Ro, 2) for Ro in Rotate]
            Angle_dif = [Rotate[i] - data[i + 4] for i in range(3)]

            self.style.InteractionProp.SetPosition((0, 0, 0))

            if Angle_dif[0] != 0:
                self.style.InteractionProp.RotateZ(Angle_dif[0])
            if Angle_dif[1] != 0:
                self.style.InteractionProp.RotateX(Angle_dif[1])
            if Angle_dif[2] != 0:
                self.style.InteractionProp.RotateY(Angle_dif[2])
            # self.style.InteractionProp.SetOrientation([data[i + 3] for i in range(3)])

            Rotate = [round(Ro, 2) for Ro in self.style.InteractionProp.GetOrientation()]
            data = [data[0]] + [data[i + 1] for i in range(3)] + [Rotate[i] for i in range(3)]

            self.parent().parent().property3d.update_property(data)

            self.style.InteractionProp.SetPosition(*data[1:4])

            self.style.HighlightProp3D(self.style.InteractionProp)
            self.style.GetInteractor().Render()

            self.signal_update_images.emit(
                drawProjected3DBox(
                    self.style.GetCurrentRenderer(),
                    self.style.InteractionProp,
                    self.image_data.copy(),
                    with_clip=True)
            )

            if self.interactor.GetInteractorStyle().GetAutoAdjustCameraClippingRange():
                self.actor_manager.ResetCameraClippingRange()

    # 重新设置角度
    def resize_Angle(self, data):
        for i in range(len(data)):
            if data[i] > 180:
                data[i] -= 360
            if data[i] <= -180:
                data[i] += 360
        return data

        # Shortcut key operation: delete selected model

    # 删除模型
    def delete_model(self):
        self.actor_manager.delete_actor()

    # 先获取所需要复制的场景的相关参数，然后更改标注、模型、配置等，最后再加载场景
    # copy scene when press down Ctrl+Space
    def copy_scene(self):
        print("Copy scene !")

        self.is_first_scene = True

        scene_folder = self.parent().parent().scene_manager.scene_folder
        annotations_folder = self.parent().parent().scene_manager.annotations_folder
        images_folder = self.parent().parent().scene_manager.images_folder
        current_index = self.parent().parent().scene_manager.current_index
        if current_index == 0:
            return
        annotations_list = self.parent().parent().scene_manager.annotation_name_list
        image_name_list = self.parent().parent().scene_manager.image_name_list
        # 更改名字序数
        pre_img_file = os.path.join(annotations_folder, annotations_list[current_index - 1])
        current_img_file = os.path.join(annotations_folder, annotations_list[current_index])
        # 更新 annotation 中的 model
        # this annotation  pre annotation
        with open(pre_img_file, 'r') as load_f:
            config_data = json.load(load_f)
            model = config_data["model"]

        with open(current_img_file, 'r') as load_f:
            config_data = json.load(load_f)
            config_data["model"] = model

        with open(current_img_file, 'w+') as f:
            json.dump(config_data, f, indent=4)

        self.loadScenes(scene_folder, os.path.join(images_folder, image_name_list[current_index]),
                        os.path.join(annotations_folder, annotations_list[current_index]))

    def author_Haonan_Liu(self):
        webbrowser.open('https://github.com/lhn0323/Labeling6DoF-System')

    def author_Shijie_Sun(self):
        # print("Shijie Sun")
        webbrowser.open('https://js.chd.edu.cn/xxgcxy/ssj102/list.psp')

    def license(self):
        # print("License")
        webbrowser.open('https://creativecommons.org/licenses/by-nc-sa/3.0/')
