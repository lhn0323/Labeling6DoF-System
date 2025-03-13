import os
import sys
import numpy as np
from datetime import datetime
import sys
import PyQt5
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
import cv2


# Label Image停靠窗口的设计
class SLabelImage(QDockWidget):
    """The Log Window
    """
    def __init__(self, parent, title="Label Image"):
        """Constructor

        Args:
            title (str): windows title
            parent (QWdiget): the parent window
        """
        super().__init__(parent=parent)

        self.setWindowTitle(title)
        self.grid_layout = QGridLayout()
        self.grid_layout.setContentsMargins(20, 20, 20, 20)

        self.label = QLabel("")
        self.grid_layout.addWidget(self.label, 1, 1)

        self.window = QFrame()
        self.window.setLayout(self.grid_layout)
        self.setWidget(self.window)

        self.image = None

    # 发生事件时，重新显示label上的图像
    def resizeEvent(self, event):
        self.showImage(self.image)

    # 将传入图像在label上显示
    @PyQt5.QtCore.pyqtSlot(np.ndarray)
    def showImage(self, image=None):
        if image is None or image.size == 0:
            image = np.zeros((512,512,3), np.uint8)
        self.image = image
        # label.geometry()：返回一个矩形，包含了label的位置和大小
        width, height = self.label.geometry().width(), self.label.geometry().height()
        # label.setPixmap()：设置label的图片
        self.label.setPixmap(
            SLabelImage.image_cv2qt(self.image, width, height)
        )

    # 进行图片的格式转换，使其最终能在Label上显示
    def image_cv2qt(cv_img, width, height):
        # cv2.cvtColor()：将图片从BGR转换为RGB
        rgb_image = cv2.cvtColor(cv_img, cv2.COLOR_BGR2RGB)
        # 获取图片的高、宽、通道数
        h, w, ch = rgb_image.shape
        # 获取图片的每行字节数
        bytes_per_line = ch * w
        # 将图片转换为QImage格式
        convert_to_Qt_format = QtGui.QImage(rgb_image.data, w, h, bytes_per_line, QtGui.QImage.Format_RGB888)
        # 保持图片的宽高比将图片缩放到指定大小
        p = convert_to_Qt_format.scaled(width, height, Qt.KeepAspectRatio)
        # 转换成QPixmap类型，用于在标签或按钮上显示图像
        return QPixmap.fromImage(p)


if __name__ == '__main__':
    class MainWindow(QMainWindow):
        def __init__(self,parent=None):
            super(MainWindow, self).__init__(parent)
            layout=QHBoxLayout()

            self.items=SLabelImage(self)

            self.setCentralWidget(QTextEdit())
            self.addDockWidget(Qt.RightDockWidgetArea,self.items)

            self.setLayout(layout)
            self.setWindowTitle('Dock')

        @staticmethod
        def update(sender):
            print(sender)

    app=QApplication(sys.argv)
    demo=MainWindow()
    demo.show()
    sys.exit(app.exec_())
