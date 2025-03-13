from PyQt5.QtCore import *
from PyQt5.QtWidgets import QMessageBox
from PyQt5 import QtWidgets
from libs.utils.Ui_kitti_2_labelimg3d import Ui_FormKitti2LabelImg3D
import os
import json
from libs.utils.kitti_util import Calibration, roty
from libs.utils.utils import get_all_path
import numpy as np
import pandas as pd

# 基于Pyqt的Qt GUI应用程序，将KITTI数据集的标注转化为LabelImg3D的标注格式,通过Pyqt的图形界面,用户选择文件夹进行转化操作
class Kitti2LabelImg3D(QObject):
    def __init__(self, parent):
        super().__init__(parent)
        self.window = QtWidgets.QWidget() #创建窗口
        self.ui = Ui_FormKitti2LabelImg3D() # 关联ui
        self.ui.setupUi(self.window) # 初始化ui界面

        # Data 数据属性初始化
        self.speed_of_progress = 0

        self.scene_folder = ""
        self.images_folder = ""
        self.models_folder = ""
        self.label_folder = ""
        self.calib_folder = ""
        self.annotations_folder = ""
        self.c_distance = 0.52

        # button connect 信号连接
        self.ui.openFolder_Btn.clicked.connect(self.openFolder) # 打开文件夹
        self.ui.btn_Run.clicked.connect(self.run) # 运行转换任务

        # progressBar status
        self.ui.progressBar.setValue(0)

    def openFolder(self):
        """load the scenes, the folder structure should be as follows:

        ..--------
        . --------
        |--models <only obj support>
        |--images
            |--scene1
            |--scene2
            |-- ...
        |--label
            |--scene1
            |--scene2
            |-- ...
        |--calib
            |--scene1
            |--scene2
            |-- ...
        |--annotations
            |--scene1
            |--scene2
            |-- ...
        """
        # 选择文件夹
        scene_folder = QtWidgets.QFileDialog.getExistingDirectory(None, "Choose Scene Folder")
        if scene_folder == '':
            return
        
        #文件夹路径解析和验证
        self.scene_folder = scene_folder
        self.images_folder = os.path.join(scene_folder, 'images')
        self.label_folder = os.path.join(scene_folder, 'label')
        self.models_folder = os.path.join(scene_folder, 'models')
        self.calib_folder = os.path.join(scene_folder, 'calib')

        if not os.path.exists(self.scene_folder) or not os.path.exists(self.images_folder) or not os.path.exists(
                self.label_folder) or not os.path.exists(self.models_folder) or not os.path.exists(self.calib_folder):
            QMessageBox.critical(self.window, "Error", "File structure error!",
                                 QMessageBox.Yes | QMessageBox.No,
                                 QMessageBox.Yes)
            return
        else:
            self.ui.lineEdit_Edt.setText(self.scene_folder)
    
    # 运行转换任务
    def run(self):
        self.ui.progressBar.setValue(0) # 初始化进度条
        img_path = get_all_path(self.images_folder) # 获取图片路径
        label_path = get_all_path(self.label_folder) # 获取标注路径
        calib_path = get_all_path(self.calib_folder) # 获取校准路径
        
        # 数据一致性检查
        if len(img_path) != len(label_path) or len(img_path) != len(calib_path):
            QMessageBox.critical(self.window, "Error",
                                 "The number of images, labels and calibration files does not match!",
                                 QMessageBox.Yes | QMessageBox.No, QMessageBox.Yes)
            return
        
        # 逐文件转换
        for i in range(0, len(img_path)):
            img = img_path[i]
            label = label_path[i]
            calib = calib_path[i]
            self.annotations_folder = "\\".join(self.label_folder.split("\\")[:-1]) + "\\annotations\\" + \
                                      img.split("\\")[-2] + "\\"

            if img.split("\\")[-1].split(".")[0] == label.split("\\")[-1].split(".")[0] == \
                    calib.split("\\")[-1].split(".")[0]:
                self.KITTI_2_LabelImg3D(img, label, self.models_folder, self.annotations_folder, calib, self.c_distance)

            current_speed_of_progress = (i + 1) / len(img_path) * 100
            if current_speed_of_progress != self.speed_of_progress:
                self.ui.progressBar.setValue(current_speed_of_progress)
            QCoreApplication.processEvents()

    def show(self):
        self.ui.lineEdit_Edt.setText(" ")
        self.ui.progressBar.setValue(0)
        self.window.show()

    def KITTI_2_LabelImg3D(self, img_path, label_path, model_path, annotation_path, calib_path, c_distance):
        with open(model_path + "/models.json", 'r') as load_f:
            model_json_data = json.load(load_f)
        model_data = {"Tram": {}, "Car": {}, "Truck": {}, "Van": {}, "Pedestrian": {}}
        for d in model_data:
            for j_d in model_json_data:
                if model_json_data[j_d]["class_name"] == d:
                    model_data[d]["path"] = "models\\" + j_d
                    model_data[d]["index"] = model_json_data[j_d]["class_index"]
                    model_data[d]["size"] = model_json_data[j_d]["size"]
                    break

        # 校准数据加载和处理
        calib = Calibration(calib_path)
        data = {}

        data["image_file"] = "\\".join(img_path.split("\\")[len(img_path.split("\\")) - 3:])

        data["model"] = {}
        data["model"]["num"] = 0
        num = 0

        # calib = pd.read_table(calib_path, sep=' ', header=None)
        # calib_velo2c0 = [[calib[4 * i + n][5] for n in range(1, 5)] for i in range(0, 3)]
        # calib_velo2c0 = np.row_stack([calib_velo2c0, np.array([0, 0, 0, 1])])
        #
        # calib_R0rect = [[calib[3 * i + n][4] for n in range(1, 4)] for i in range(0, 3)]
        # calib_R0rect = np.column_stack([calib_R0rect, np.array([0, 0, 0])])
        # calib_R0rect = np.row_stack([calib_R0rect, np.array([0, 0, 0, 1])])
        #
        # calib_velo2c = np.dot(calib_R0rect, calib_velo2c0)
        # R_velo2c = [[calib_velo2c[i][n] for n in range(0, 3)] for i in range(0, 3)]
        # T_velo2c = [calib_velo2c[i][3] for i in range(0, 3)]

        R_c02c = np.array([[0.9999758, -0.005267463, - 0.004552439],
                           [0.00251945, 0.9999804, - 0.003413835],
                           [0.004570332, 0.003389843, 0.9999838]])# p0到p2的旋转关系

        a = pd.read_table(label_path, sep=' ', header=None)
        for i in reversed(range(0, len(a))):
            obj_class = a[0][i]

            if obj_class == "DontCare" or obj_class == "Misc" or obj_class == "Person_sitting" or a[2][i] == 2 \
                    or a[2][i] == 3 or a[1][i] > 0.7:
                continue
            
            # KiTTi中是以P0相机为视角进行标注的,左前视相机P0,Rope3D本来就是P2相机
            obj_position_c0 = np.array([[a[j][i] for j in range(11, 14)]])
            # obj_position_c0 = np.array(obj_position_c0) 

            # obj_position_c = calib.project_rect0_to_rect2(obj_position_c0)不需要进行p0到p2视角的转换
            obj_position_c = obj_position_c0.squeeze()
            # obj_position_c = [obj_position_c0[i] + T_c02c[i] for i in range(0, 3)]
            # 相机坐标系到世界坐标系
            obj_position_w = np.array([obj_position_c[0], -obj_position_c[1], -(obj_position_c[2] - c_distance)])

            obj_alpha = a[3][i]
            R_oK2oL = [[0, 0, 1],
                       [0, 1, 0],
                       [-1, 0, 0]]# 旋转矩阵,x和z对换,y不变

            obj_r_y = a[14][i]
            R_oK2c = roty(3.14 - obj_r_y)
            #R_oK2c = np.dot(R_oK2c0, R_c02c) 不需要p0到p2的转换了

            R_c2w = [[0, 1, 0],
                     [1, 0, 0],
                     [0, 0, -1]] # 相机到世界
            # R_oL2w = np.dot(np.dot(R_oL2oK, R_oK2c), R_c2w)
            R_oL2w = np.dot(np.dot(R_oK2c, R_c2w), R_oK2oL)# 物体到世界
            # R_oL2w = np.dot(R_oK2c, R_c2w)
            oL_2_w = np.column_stack([R_oL2w, obj_position_w]) # 世界坐标系下的位姿矩阵
            oL_2_w = np.row_stack([oL_2_w, np.array([0, 0, 0, 1])])

            if obj_class == "Cyclist":
                obj_class = "Pedestrian"
            if obj_class == "Bus":
                obj_class = "Tram"

            data["model"]["{}".format(num)] = {
                "model_file": model_data[obj_class]["path"],
                "matrix": oL_2_w.reshape(1, 16).tolist()[0],
                "class": model_data[obj_class]["index"],
                "class_name": obj_class,
                "size": model_data[obj_class]["size"]
            }

            num += 1
        data["model"]["num"] = num
        data["camera"] = {}
        data["camera"]["matrix"] = [2.767086914062e+03,0.000000000000e+00,9.908542480469e+02,0.000000000000e+00,
                                    0.000000000000e+00,2.948181640625e+03,5.605048217773e+02,0.000000000000e+00,
                                    0.000000000000e+00,0.000000000000e+00,1.000000000000e+00,1.41e+00,
                                    0.0, 0.0, 0.0, 1.0]
        data["camera"]["position"] = [0.0, 0.0, 1.41]
        data["camera"]["focalPoint"] = [0.0, 0.0, 0.0]
        data["camera"]["fov"] = 39.05
        data["camera"]["viewup"] = [0.0, 1.0, 0.0]
        data["camera"]["distance"] = 1.41

        

        annotation_file = annotation_path + img_path.split("\\")[-1].split(".")[0] + ".json"
        if not os.path.exists(os.path.dirname(annotation_file)):
            os.makedirs(os.path.dirname(annotation_file))
        with open(annotation_file, 'w+') as f:
            json.dump(data, f, indent=4)




