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
from libs.utils.utils import *
from PyQt5.QtCore import pyqtSignal
from PyQt5.Qt import QObject
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from libs.smodellist import SModelList
from itertools import product
import itertools
from libs.lsystem_config import SystemConfig
from PIL import Image


# Actor，其作用就是实体化由  Mapper 得到的映射关系，使人们能够看到最终的绘制结果
class Actor:

    # 初始化参数，生成指定图层的渲染器以及导入指定路径的指定模型
    def __init__(self, render_window, interactor, model_path, model_class, model_name, layer_num, actor_id=0):
        self.renderer_window = render_window
        self.interactor = interactor
        self.renderer = None
        self.actor = None
        self.box_widget = None
        self.model_path = model_path
        self.model_name = model_name
        self.createRenderer(layer_num)
        self.loadModel(model_path, model_name)
        self.type_class = model_class
        self.size = []  # [w, l, h]
        self.actor_id = actor_id

    # vtk绘制管线：
    # 通过指定的路径加载 obj文件得到源数据，通过滤波器对数据做各种转换，
    # Mapper 将 Filter 处理后的数据转换为图形数据，实现由数据到图形的映射关系
    # Actor：实体化由 Mapper 得到的映射关系
    def readObj(self, model_path):
        # obj文件是3D模型文件格式；用于加载obj文件
        reader = vtk.vtkOBJReader()
        reader.SetFileName(model_path)
        reader.Update()

        # vtkpolydata用来表示顶点、线、多边形、三角形带在内的几何结构，即三维实体；是一种广泛使用的vtk数据结构
        # vtkPolyData数据显示时需要定义 vtkPolyDataMapper对象，用来接受vtkPolyData数据以实现图形数据到渲染图元的转换。
        mapper = vtk.vtkPolyDataMapper()
        # 将经过某个filter处理之后的输出作为另一个filter的输入，它是通过 GetOutputPort() 获得的；获取对应于该算法的给定输出端口的代理对象。
        mapper.SetInputConnection(reader.GetOutputPort())

        actor = vtk.vtkActor()
        actor.SetMapper(mapper)
        return actor

    # no usages？
    def importObj(self, model_path):
        self.model_folder, self.obj_name = os.path.split(self.model_path)
        self.obj_name = self.obj_name[:-4]
        self.mtl_path = self.model_folder + "/" + self.obj_name + ".mtl"
        importer = vtk.vtkOBJImporter()
        importer.SetFileName(self.model_path)
        importer.SetFileNameMTL(self.mtl_path)
        importer.SetTexturePath(self.model_folder)

        importer.Read()
        importer.InitializeObjectBase()

        # get all actors and assembly
        actors = importer.GetRenderer().GetActors()
        actors.InitTraversal()
        assembly = vtk.vtkAssembly()
        for i in range(actors.GetNumberOfItems()):
            a = actors.GetNextActor()
            assembly.AddPart(a)

        return assembly

    # 传入模型的路径与名称，将路径传入 SModelList类的对象并调用相关函数获取 actor，添加到渲染器进行渲染场景
    def loadModel(self, model_path, model_name):
        self.model_path = model_path
        self.model_name = model_name
        # SModelList类中设计的是停靠窗口 models，获取actor
        self.actor = SModelList.get().getActor(model_path)
        # 若路径不在存储的列表中，则调用 readObj重新加载模型等操作来获取 actor
        if self.actor is None:
            self.actor = self.readObj(model_path)
        # self.actor = self.importObj(model_path)

        # # move the actor to (0, 0, 0)
        # min_x, _, min_y, _, min_z, _ = self.actor.GetBounds()
        # transform = vtk.vtkTransform()
        # transform.Translate(-min_x, -min_y, -min_z)
        # self.actor.SetUserTransform(transform)

        self.renderer.AddActor(self.actor)
        # 渲染场景
        self.interactor.Render()

    # 为渲染器窗口设置图层总数，返回该窗口中第一个渲染器，并为该渲染器设置一些参数
    def createRenderer(self, layer_num):
        self.renderer = vtk.vtkRenderer()
        # 设置渲染器的总层数
        self.renderer_window.SetNumberOfLayers(layer_num + 1)
        # 设置渲染器的层数
        self.renderer.SetLayer(layer_num)
        # 设置背景色
        self.renderer.SetBackground(0, 0, 0)
        # on/off : 打开/关闭交互状态
        self.renderer.InteractiveOff()
        # 设置场景的透明度
        self.renderer.SetBackgroundAlpha(0)
        # 指定用于此渲染器的相机
        self.renderer.SetActiveCamera(
            # 返回渲染窗口中渲染器的集合；获取列表中的第一个渲染器；获取当前渲染器(vtkRenderer)中的默认相机（的参数）
            self.renderer_window.GetRenderers().GetFirstRenderer().GetActiveCamera()
        )
        self.renderer_window.AddRenderer(self.renderer)
        return self.renderer

    # no usages?
    def setUserTransform(self, transform):
        # self.box_widget.SetTransform(transform)
        self.actor.SetUserTransform(transform)

    # 设置渲染场景的矩阵
    def setMatrix(self, matrix):
        if type(self) is Actor:
            actor = self.actor
        else:
            actor = self
        setActorMatrix(actor, matrix)

    # 获取渲染对象旋转时的8个顶点
    @staticmethod
    def get8Corners(prop3D):
        return getActorRotatedBounds(prop3D)

    # no usages?
    def getCameraMatrix(self):
        matrix = self.renderer.GetActiveCamera().GetModelViewTransformMatrix()
        return [matrix.GetElement(i, j) for i in range(4) for j in range(4)]

    # 获取2d框的边界坐标
    def getBBox2D(self):
        bbox3d_points_world = getActorRotatedBounds(self.actor)

        # 获取渲染对象的旋转边界，并返回最小外接矩形
        bbox3d_min_x, bbox3d_min_y, bbox3d_max_x, bbox3d_max_y \
            = worldToViewBBox(self.renderer, bbox3d_points_world)

        image_ratio = self.interactor.parent().image_ratio
        w, h = self.interactor.parent().image_width, self.interactor.parent().image_height
        image_points_world = [[-0.5, 0.5 / image_ratio, 0], [0.5, -0.5 / image_ratio, 0]]
        image_min_x, image_min_y, image_max_x, image_max_y = worldToViewBBox(self.renderer, image_points_world)
        w_i = image_max_x - image_min_x
        h_i = image_max_y - image_min_y
        # 矩阵乘法 p=[3*3]*[3*3]=[3*3]
        p = np.dot(np.array([
            [w / 2, 0, w / 2],
            [0, -h / 2, h / 2],
            [0, 0, 1]
        ]), np.array([
            [2 / w_i, 0, 0],
            [0, 2 / h_i, 0],
            [0, 0, 1]
        ]))
        # [3*3]*[3*1]=[3*1]
        l, t, _ = np.dot(p, np.array([bbox3d_min_x, bbox3d_max_y, 1]).T)
        r, b, _ = np.dot(p, np.array([bbox3d_max_x, bbox3d_min_y, 1]).T)

        # test the labeled images
        # img = cv2.imread(self.interactor.parent().image_path)
        # img = cv2.rectangle(img, (int(l), int(t)), (int(r), int(b)), [0, 0, 255], 3)
        # cv2.imshow("rect", img)
        # cv2.waitKey(0)

        # 保留两位小数
        return round(l, 2), round(t, 2), round(r, 2), round(b, 2)

    # 获取3d框的边界坐标
    def getBBox3D(self):
        """
        Returns:
            (8,2) array of vertices for the 3d box in following order:
            1 -------- 0
           /|         /|
          2 -------- 3 .
          | |        | |
          . 5 -------- 4
          |/         |/
          6 -------- 7

        """
        renderer = self.renderer
        # 获取图像的宽高
        w, h = Image.open(self.interactor.parent().parent().parent().image_list.file_list[0]).size

        P_v2i = getMatrixW2I(renderer, w, h)
        pts_3d = getActorRotatedBounds(self.actor)

        p_v = np.array(worldToView(renderer, pts_3d))
        p_i = np.dot(P_v2i, cart2hom(p_v[:, :2]).T).T[:, :2]
        return [[int(p_i[i][0]), int(p_i[i][1])] for i in range(0, 8)]

    # 获取3d框的？
    def getBBox3D_w(self):
        """
               Returns:
                   (8,2) array of vertices for the 3d box in following order:
                   1 -------- 0
                  /|         /|
                 2 -------- 3 .
                 | |        | |
                 . 5 -------- 4
                 |/         |/
                 6 -------- 7

               """
        renderer = self.renderer
        # 获取打开的图像的宽高
        w, h = Image.open(self.interactor.parent().parent().parent().image_list.file_list[0]).size

        P_v2i = getMatrixW2I(renderer, w, h)
        pts_3d = getActorRotatedBounds(self.actor)
        # 把numpy数组转换成列表
        return pts_3d.tolist()

    # 计算标注数据中有关 model的各参数
    def toJson(self, scene_folder):
        # 返回物体坐标系到相机坐标系的旋转矩阵，并存入[1，9]的矩阵内，将矩阵中的元素转换成列表
        # GetMatrix则始终返回场景中物体（坐标系）相对世界坐标系的变换矩阵
        # self.actor.GetMatrix()  ->  matrix2List(self.actor.GetMatrix()
        #     1 0 0 0
        #     0 1 0 0       ->  1 0 0 0 0 1 0 0 0 0 1 -30 0 0 0 1
        #     0 0 1 -30
        #     0 0 0 1
        R_c2o = get_R_obj2c(np.array(matrix2List(self.actor.GetMatrix()))).reshape(1, 9).tolist()[0]
        # 获取设置的该参数的数值
        camera_fov = self.interactor.parent().parent().parent().camera_property.get("fov")
        T_c2o = get_T_obj2c(np.array(matrix2List(self.actor.GetMatrix())), camera_fov)
        T_c2o = np.array([-T_c2o[0], T_c2o[1], -T_c2o[2]]).reshape(1, 3).tolist()[0]
        return {
            # 该方法返回一个字符串值，表示从起始目录到给定路径的相对文件路径
            "model_file": os.path.relpath(self.model_path, scene_folder),
            "matrix": matrix2List(self.actor.GetMatrix()),
            "actor_id": int(self.actor_id),
            "R_matrix_c2o": R_c2o,
            "T_matrix_c2o": T_c2o,
            "class": self.type_class,
            "class_name": self.model_name,
            "size": listRound(self.size),
            "2d_bbox": self.getBBox2D(),
            "3d_bbox": self.getBBox3D(),
            "3d_bbox_w": self.getBBox3D_w()
        }

    # 将actor的坐标转换成KITTI格式的标注
    def toKITTI(self):
        # get bottom center point
        # p = [[  x.  y.  z.]]  获取actor的世界坐标系下的坐标
        p = np.array([self.actor.GetPosition()])
        # p = [[  x.  y.  z.  1.]]
        p = cart2hom(p)

        camera = self.renderer.GetActiveCamera()
        x_c, y_c, z_c = camera.GetPosition()
        p_w_c = np.array([
            [1, 0, 0, x_c],
            [0, -1, 0, y_c],
            [0, 0, -1, z_c],
            [0, 0, 0, 1],
        ])
        p_c = np.matmul(p_w_c, p.T).T  # x, y, z

        v_x_o, v_y_o, v_z_o = getActorXYZAxis(self.actor)
        v_x_c, v_y_c, v_z_c = np.identity(3)
        v_y_c, v_z_c = -v_y_c, -v_z_c
        # r_y is the angle between camera x-axis and object -y axis
        r_y = getAngle(-v_y_o, v_x_c)

        # theta is the angle between z_c and vector from camera to object
        v_c2o = np.array(self.actor.GetPosition()) - np.array(camera.GetPosition())
        theta = getAngle(v_c2o, v_z_c)
        alpha = r_y - theta

        l, t, r, b = self.getBBox2D()
        return [
            self.model_name, 0, 0, round(alpha, 2),
            l, t, r, b,  # bounding box 2d
            self.size[2], self.size[0], self.size[1],  # model height, width , length
            round(p_c[0, 0], 2), round(p_c[0, 1], 2), round(p_c[0, 2], 2),
            # location (x, y, z) in camera coordinate) different camera coordinate
            round(r_y, 2)
        ]

#
class ActorManager(QObject):
    # 定义了一些信号，实现多页面间的信息传递
    signal_active_model = pyqtSignal(list)
    signal_highlight_model_list = pyqtSignal(str)
    signal_update_property_enter_scene = pyqtSignal(list)

    def __init__(self, render_window, interactor, bg_renderer):
        super(ActorManager, self).__init__()
        self.render_window = render_window
        self.interactor = interactor
        self.bg_renderer = bg_renderer
        # self.bg_renderer.GetActiveCamera()
        # 必须覆盖此方法，以便将设置传递给底层样式。从 vtkInteractorStyle 重新实现
        self.interactor.GetInteractorStyle().SetAutoAdjustCameraClippingRange(False)
        # self.bg_renderer.GetActiveCamera().SetClippingRange(0.00001, 1000000)
        self.actors = []

    # 生成一个新的actor，并设置其属性（即绘制场景）
    def newActor(self, model_path, model_class, model_name, actor_id=0, actor_matrix=None, actor_size=[]):
        actor = Actor(self.render_window, self.interactor, model_path, model_class, model_name,
                      len(self.actors) + 1, actor_id)
        if actor_matrix is None and actor_size == []:
            # only copy the matrix of previous actors
            if len(self.actors) > 0 and self.actors[-1].model_path == actor.model_path:
                actor.setMatrix(self.actors[-1].actor.GetMatrix())
                actor.size = self.actors[-1].size
            else:
                # newPosition = list(actor.renderer.GetActiveCamera().GetPosition())
                # actor.actor.SetPosition(newPosition)
                # matrix = actor.renderer.GetActiveCamera().GetModelViewTransformMatrix()
                # actor.actor.SetOrigin(actor.actor.GetCenter())
                matrix = vtk.vtkMatrix4x4()
                actor.setMatrix(matrix)

                # Set the initial loading position of the model
                # 设置模型的初始加载位置
                actor.actor.SetPosition([0, 0, float(SystemConfig.config_data["model"]["initial_position"])])
                actor.size = list(getActorXYZRange(actor.actor))
        else:
            # copy the camera matrix
            matrix = vtk.vtkMatrix4x4()
            matrix.DeepCopy(actor_matrix)
            # matrix.Invert()
            transform = getTransform(matrix)
            if actor.actor.GetUserMatrix() is not None:
                transform.GetMatrix(actor.actor.GetUserMatrix())
                actor.size = actor_size
            else:
                # GetOrientation：从变换矩阵中获取 x、y、z 方向角作为三个（浮点值）的数组
                actor.actor.SetOrientation(transform.GetOrientation())
                # 获取纹理贴图的位置并赋给actor
                actor.actor.SetPosition(transform.GetPosition())
                # 获取纹理贴图的缩放比例并赋给actor
                actor.actor.SetScale(transform.GetScale())
                actor.size = actor_size

        # 添加到 actors列表中
        self.actors.append(actor)
        self.setActiveActor(-1)
        # list(self.InteractionProp.GetPosition() + self.InteractionProp.GetOrientation()) +
        # self.slabel.actor_manager.actors[-1].size
        # self.getCurrentActiveActor().Get

        if self.interactor.GetInteractorStyle().GetAutoAdjustCameraClippingRange():
            self.ResetCameraClippingRange()

        self.ResetCameraClippingRange()
        self.interactor.Render()

    # 按照索引来设置绘制对象实体的相关信息，如图层以及交互器观察期的渲染器状态
    def setActiveActor(self, index):
        """Set Active Actor by index.
        The specified actor will be moved to the last item

        Args:
            index (int): The index specified.
        """
        len_actors = len(self.actors)
        # print("len_actors: ", len_actors)
        if len_actors == 0 or index < -len_actors or index >= len_actors:
            raise IndexError("index error")

        # print("index1: ", index)
        index %= len(self.actors)
        # print("index2: ", index)

        if index != len(self.actors) - 1:
            actor = self.actors[index]
            del self.actors[index]
            self.actors.append(actor)
            # highlight in the model list
            self.signal_highlight_model_list.emit(actor.model_path)

        # 设置渲染窗口的总图层数，即渲染对象总数+1
        self.render_window.SetNumberOfLayers(len(self.actors) + 1)

        # 将一个可遍历的数据对象组合为一个索引序列，同时列出数据和数据下标
        for i, a in enumerate(self.actors):
            a.renderer.SetLayer(i + 1)
            # a.renderer.Render()

        renderer = self.actors[-1].renderer
        # very important for set the default render
        self.interactor.GetInteractorStyle().SetDefaultRenderer(renderer)
        self.interactor.GetInteractorStyle().SetCurrentRenderer(renderer)
        # if actor is not None:
        #     self.signal_active_model.emit(list(actor.actor.GetBounds()))

    # TODO: Remove the function
    def reformat(self):
        for a in self.actors:
            actor_matrix = deepCopyMatrix(a.actor.GetMatrix())
            actor_matrix.Invert()
            actor_transform = getTransform(actor_matrix)

            a.actor.SetUserMatrix(vtk.vtkMatrix4x4())
            # a.box_widget.SetTransform(vtk.vtkTransform())

            print(a.actor.GetBounds())
            camera = a.renderer.GetActiveCamera()
            camera.ApplyTransform(actor_transform)

    # 获取当前活动的actor即列表中最后一个actor
    def getCurrentActiveActor(self):
        if len(self.actors) == 0:
            return None
        return self.actors[-1].actor

    # 获取当前活动的渲染器
    def getCurrentActiveRenderer(self):
        return self.actors[-1].renderer

    # 将传入的 actor生成一个列表并反转，返回其序数 i = actors总长度-actor序数
    def getIndex(self, actor):
        i = -1
        # print("len: ", len(self.actors))
        # range() 函数可创建一个整数列表；reversed 函数返回一个反转的迭代器
        for i in reversed(range(len(self.actors))):
            if self.actors[i].actor is actor:
                # print("index: ", i)
                break
        return i

    # 清空所有的actor
    def clear(self):
        for a in self.actors:
            a.renderer.RemoveActor(a.actor)
            self.render_window.RemoveRenderer(a.renderer)
        self.actors = []

    # 导入给定路径下的json标注数据
    def loadAnnotation(self, annotation_file):
        if not os.path.exists(annotation_file):
            return
        data = None
        with open(annotation_file, 'r') as f:
            data = json.load(f)

        return data

    # 设置相机的位置，焦点，视角，视角方向，距离
    def setCamera(self, camera_data):
        # 获取当前相机（最初获取的就是vtk默认的相机，默认相机的viewangle=30）
        camera = self.bg_renderer.GetActiveCamera()
        # 此处设置相机的位置，焦点，视角，视角方向，距离，将vtk默认的相机参数更改为设置的默认值
        camera.SetPosition(camera_data["position"])
        camera.SetFocalPoint(camera_data["focalPoint"])
        camera.SetViewAngle(camera_data["fov"])
        camera.SetViewUp(camera_data["viewup"])
        camera.SetDistance(camera_data["distance"])

    # 重置相机的渲染范围
    def ResetCameraClippingRange(self):
        bounds = []
        bounds += [self.bg_renderer.ComputeVisiblePropBounds()]
        bounds += [a.renderer.ComputeVisiblePropBounds() for a in self.actors]
        bound = []
        for i in range(6):
            if i % 2 == 0:
                bound += [min([b[i] for b in bounds])]
            else:
                bound += [max([b[i] for b in bounds])]

        # if there only an image
        if bound[-1] - bound[-2] == 0:
            bound[-1] = 0.5

        self.bg_renderer.ResetCameraClippingRange(bound)
        for a in self.actors:
            a.renderer.ResetCameraClippingRange(bound)

    # 生成一个actor列表
    def createActors(self, scene_folder, data):
        # scene_folder:   E:/GitCode/LabelImg3D/scenes/KITTI
        # 根据json数据中的model数量，生成对应数量的actor
        for i in range(data["model"]["num"]):
            model_path = os.path.join(scene_folder, data["model"][str(i)]["model_file"])

            if "actor_id" not in (data["model"][str(i)].keys()):
                data["model"][str(i)]["actor_id"] = 0

            # 生成新的actor，并设置其初始属性
            self.newActor(model_path, data["model"][str(i)]["class"],
                          data["model"][str(i)]["class_name"],
                          data["model"][str(i)]["actor_id"],
                          data["model"][str(i)]["matrix"],
                          data["model"][str(i)]["size"]
                          )

            # updata property when enter a scene
            self.signal_update_property_enter_scene.emit(
                [self.actors[-1].actor_id] +
                list(self.getCurrentActiveActor().GetPosition() + self.getCurrentActiveActor().GetOrientation()) +
                self.actors[-1].size
            )

    # 为actors列表内所有actor依次设置json中保存的参数
    def toJson(self, scene_folder):
        # self.reformat()
        # print info
        # for i, a in enumerate(self.actors):
        #     print("======{}======\n".format(i), a.actor.GetUserTransform().GetMatrix())
        #     print(a.renderer.GetActiveCamera().GetViewTransformMatrix())
        data = {"model": {}}
        data["model"]["num"] = len(self.actors)
        for i in range(len(self.actors)):
            data["model"]["{}".format(i)] = self.actors[i].toJson(scene_folder)
        return data

    # 更新相机参数
    @PyQt5.QtCore.pyqtSlot(list, bool)
    def update_camera(self, camera_data, is_change):
        if is_change is False:
            return
        camera = self.bg_renderer.GetActiveCamera()
        camera_position = [camera_data[0], camera_data[1], camera_data[2]]
        camera.SetPosition(camera_position)
        camera.SetViewAngle(camera_data[3])
        camera.SetDistance(camera_data[4])
        camera.SetViewUp([0, 1, 0])

        # Refresh the content in the field of view
        # self.slabel.actor_manager.ResetCameraClippingRange()
        # self.GetInteractor().Render()
        self.ResetCameraClippingRange()
        self.interactor.Render()

    # 获取json数据
    def getEmptyJson(self, image_file):
        return {
            "image_file": image_file,
            "model": {"num": 0},
            "camera": {
                "matrix": SystemConfig.config_data["camera"]["matrix"],
                "position": SystemConfig.config_data["camera"]["position"],
                "focalPoint": SystemConfig.config_data["camera"]["focalPoint"],
                "fov": SystemConfig.config_data["camera"]["fov"],
                "viewup": SystemConfig.config_data["camera"]["viewup"],
                "distance": SystemConfig.config_data["camera"]["distance"]
            }
        }

    # 删除列表中最后一个actor及其渲染器，重置相机的渲染范围，刷新渲染器
    def delete_actor(self):
        if self.getCurrentActiveActor() is not None:
            a = self.actors[-1]
            a.renderer.RemoveActor(a.actor)
            self.render_window.RemoveRenderer(a.renderer)
            self.actors.pop()
            self.ResetCameraClippingRange()
            self.interactor.Render()
            self.interactor.GetInteractorStyle().resetHighlight()
