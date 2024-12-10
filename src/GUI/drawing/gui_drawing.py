import pathlib
import platform
import numpy as np
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtWidgets import QApplication, QLabel, QVBoxLayout, QPushButton, QWidget,QGraphicsScene,QGraphicsView,QMainWindow
import sys
from .. import GUI
from ...CellSePi import CellSePi


# PyQt-Fenster definieren
class MyQtWindow(QMainWindow):

    """
    Class handles the window for the drawing tools

    Attributes:
        csp: current object of CellSePi
        Design attributes: Window title, geometry, Buttons
    """
    def __init__(self, csp: CellSePi):
        super().__init__()
        self.csp = csp
        print(csp.bit_depth)
        self.setWindowTitle("PyQt Window")
        #self.resize(800,600)
        self.canvas= DrawingCanvas(self.csp)
        self.setCentralWidget(self.canvas)

        self.canvas.load_mask_to_scene()
        self.canvas.load_image_to_scene()

        #window layout
        layout = QVBoxLayout()

        #button = QPushButton("Close Window")
        #button.clicked.connect(self.close)

        #layout.addWidget(label)
        #layout.addWidget(button)
        self.setLayout(layout)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.canvas.graphics_view.fitInView(self.canvas.scene.sceneRect(), Qt.KeepAspectRatio)
        print(self.canvas.scene.height())
        print(self.canvas.scene.width())

# start the window of the drawing tools
def open_qt_window(csp: CellSePi):
    app = QApplication(sys.argv)
    window = MyQtWindow(csp)
    window.show()
    app.exec()



class DrawingCanvas(QGraphicsView):

    def __init__(self, csp: CellSePi):
        super().__init__()
        self.csp = csp
        self.scene = QGraphicsScene(self)
        self.graphics_view = QGraphicsView(self.scene,self)
        #self.graphics_view.setMinimumSize(800,600)
        #self.graphics_view.setMaximumSize(800,600)

        self.setScene(self.scene)
        self.canvas = None
        self.image_array=None
        self.background_image=None


    def load_mask_to_scene(self):
        current_path = pathlib.PosixPath
        if platform.system() == "Windows":
            pathlib.PosixPath = pathlib.WindowsPath

        mask = np.load(self.csp.mask_paths[self.csp.image_id][self.csp.config.get_bf_channel()], allow_pickle=True).item()

        mask_data= mask["masks"]
        outline=mask["outlines"]

        #formate npy file to RGB colors
        image_mask = np.zeros(shape=(mask_data.shape[0], mask_data.shape[1], 4), dtype=np.uint8)
        image_mask[mask_data != 0] = (255, 0, 0, 128)
        image_mask[outline != 0] = (0, 255, 0, 255)
        self.image_array=image_mask

        pathlib.PosixPath = current_path
        #creat an image
        height,width,channel= self.image_array.shape
        image= QImage(self.image_array.data,width,height,QImage.Format_RGBA8888)

        #set the image into canvas
        pixmap = QPixmap.fromImage(image)
        self.scale_image(pixmap,self.canvas)
        self.setScene(self.scene)

    def scale_image(self,image,object,depth = 1):
        view_width = self.graphics_view.width()
        view_height = self.graphics_view.height()

        scaled_pixmap = image.scaled(view_width,view_height, Qt.KeepAspectRatio, Qt.SmoothTransformation)

        if object:
            self.scene.removeItem(object)
        object = self.scene.addPixmap(scaled_pixmap)
        object.setZValue(depth)

    def load_image_to_scene(self):

        #if self.csp.adjusted_image_path is not None:
        #    image = QPixmap(self.csp.adjusted_image_path)
        #else:
         #   image= QPixmap(self.csp.image_paths[self.csp.image_id])
        image = QPixmap("my grandmother send her regards.jpg")

        self.scale_image(image,self.background_image,-1)

