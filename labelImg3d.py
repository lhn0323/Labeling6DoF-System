from PyQt5.QtCore import *
from PyQt5.QtGui import *
import libs.Ui_main as Ui_main
from libs.simagelist import SImageList
from libs.smodellist import SModelList
from libs.sproperty import SProperty
from libs.lcamera_property import LCamera_Property

import os
from PyQt5 import uic, QtWidgets, QtGui
from libs.scene_manager import SceneManager
from libs.slog import SLog
from libs.slabelimage import SLabelImage
from libs.utils.lKitti2LabelImg3D import Kitti2LabelImg3D
from libs.lsystem_config import SystemConfig
import vtk as vtk


class Draw3D(QtWidgets.QMainWindow):

    def __init__(self, data_dir):
        # Parent constructor
        self.super = super(Draw3D, self)
        self.super.__init__()

        # 实例化 SystemConfig类的一个对象（用于config窗口界面的设计）
        self.system_config = SystemConfig(self)
        self.vtk_widget = None
        self.ui = None
        # 调用setup()函数，在此函数中实例化一个新的类的对象，用于 MainWindow窗口界面的设计
        self.setup()
        self.setWindowIcon(QIcon('libs/icons/icon.ico'))

        # 停靠窗口
        self.image_list = SImageList(self, "Images")
        # model_list = SModelList.obj
        self.model_list = SModelList.create(self, "Models")
        self.property3d = SProperty(self, "3DProperty")
        self.widget_log = SLog(self)
        self.camera_property = LCamera_Property(self, "Camera_Property")
        self.label_image = SLabelImage(self, "LabelImage")
        self.label_image.showImage()
        # no usage
        self.kitti_2_labelimg3d = Kitti2LabelImg3D(self)

        self.addDockWidget(Qt.RightDockWidgetArea, self.image_list)
        self.addDockWidget(Qt.LeftDockWidgetArea, self.model_list)
        self.addDockWidget(Qt.RightDockWidgetArea, self.property3d)
        self.addDockWidget(Qt.LeftDockWidgetArea, self.widget_log)
        self.addDockWidget(Qt.RightDockWidgetArea, self.camera_property)
        self.addDockWidget(Qt.RightDockWidgetArea, self.label_image)

        self.scene_manager = SceneManager(self, self.image_list, self.model_list, self.ui.vtk_panel)

        # menu in main window
        # triggered.connect 将信号与槽函数绑定
        self.ui.action_Load_Scenes.triggered.connect(self.init_scenes)
        self.ui.action_Save_Scenes.triggered.connect(self.ui.vtk_panel.saveScenes)
        self.ui.action_Save_Scenes.triggered.connect(self.ui.vtk_panel.exportScenes)
        self.ui.actionHome.triggered.connect(self.scene_manager.home)
        self.ui.actionEnd.triggered.connect(self.scene_manager.end)
        self.ui.actionPrevious.triggered.connect(self.scene_manager.previous)
        self.ui.actionNext.triggered.connect(self.scene_manager.next)
        self.ui.action_Delete_Model.triggered.connect(self.ui.vtk_panel.delete_model)
        self.ui.actionkitti_2_labelimg3D.triggered.connect(self.kitti_2_labelimg3d.show)
        self.ui.actionSystem_Config.triggered.connect(self.system_config.show)
        # self.ui.actionKITTI.triggered.connect(self.exportKITTI)
        self.ui.actionCopy.triggered.connect(self.ui.vtk_panel.copy)
        self.ui.actionPaste.triggered.connect(self.ui.vtk_panel.paste)
        self.ui.actioncopy_scene.triggered.connect(self.ui.vtk_panel.copy_scene)

        # About
        self.ui.actionHaonan_liu.triggered.connect(self.ui.vtk_panel.author_Haonan_liu)
        self.ui.actionShijie_Sun.triggered.connect(self.ui.vtk_panel.author_Shijie_Sun)
        self.ui.actionLicense.triggered.connect(self.ui.vtk_panel.license)

        # rotate
        # eval() 函数用来执行一个字符串表达式，并返回表达式的值
        for s in ['X', 'Y', 'Z', 'X_M', 'Y_M', 'Z_M']:
            eval('self.ui.actionRoate{}.triggered.connect'.format(s))(eval('self.property3d.roate{}'.format(s)))

        # connect the signals and slots
        # self.image_list.signal_double_click.connect(self.ui.vtk_panel.loadImage)
        self.image_list.listWidget.doubleClicked.connect(self.scene_manager.__getitem__)
        self.model_list.signal_double_click.connect(self.ui.vtk_panel.loadModel)
        self.scene_manager.signal_open_files.connect(self.image_list.open_files)
        self.scene_manager.signal_open_models.connect(self.model_list.open_files)
        self.ui.vtk_panel.signal_on_left_button_up.connect(self.property3d.update_property)
        self.ui.vtk_panel.signal_update_images.connect(self.label_image.showImage)
        self.ui.vtk_panel.signal_load_scene.connect(self.camera_property.new_camera_data)

        # highlist listWidget item
        self.ui.vtk_panel.actor_manager.signal_highlight_model_list.connect(self.model_list.highlight_item)
        self.scene_manager.signal_highlight_image_list.connect(self.image_list.highlight_item)

        # update property when enter a scene
        self.ui.vtk_panel.actor_manager.signal_update_property_enter_scene.connect(self.property3d.update_property)

        # update camera property when change the config
        self.system_config.signal_update_camera_property.connect(self.camera_property.update_camera)

    #  MainWindow窗口界面的设计
    def setup(self):
        # 实例化一个 Ui_MainWindow()对象，并调用类内的函数
        self.ui = Ui_main.Ui_MainWindow()
        # 用于 MainWindow窗口界面的设计
        self.ui.setupUi(self)
        # self.vtk_widget = ui.vtk_panel
        # self.ui.vtk_layout = QtWidgets.QHBoxLayout()
        # self.ui.vtk_layout.addWidget(self.vtk_widget)
        # self.ui.vtk_layout.setContentsMargins(0, 0, 0, 0)
        # self.ui.vtk_panel.setLayout(self.ui.vtk_layout)

    def initialize(self):
        self.ui.vtk_panel.start()

    def mousePressEvent(self, ev: QtGui.QMouseEvent) -> None:
        return self.super.mousePressEvent(ev)

    def init_scenes(self):
        self.scene_manager.init_scenes()

    # def exportKITTI(self, checked):
    #     if checked:
    #         reconnect(self.ui.action_Save_Scenes.triggered, self.ui.vtk_panel.exportScenes, self.ui.vtk_panel.exportScenes)
    #     else:
    #         reconnect(self.ui.action_Save_Scenes.triggered, None, self.ui.vtk_panel.exportScenes)

    def closeEvent(self, a0: QtGui.QCloseEvent) -> None:
        self.ui.vtk_panel.saveScenes()
        self.ui.vtk_panel.interactor.Finalize()
        self.ui.vtk_panel.renderer_window.Finalize()


def main():
    vtk.vtkOutputWindow.SetGlobalWarningDisplay(0)
    os.chdir(os.path.dirname(__file__))
    # Recompile ui
    with open("libs/main.ui") as ui_file:
        with open("libs/Ui_main.py", "w") as py_ui_file:
            uic.compileUi(ui_file, py_ui_file)

    app = QtWidgets.QApplication([])
    # qtmodern.styles.dark(app)
    main_window = Draw3D("volume")
    # style_main_window = qtmodern.windows.ModernWindow(main_window)
    main_window.show()
    main_window.initialize()
    app.exec_()


if __name__ == "__main__":
    main()
