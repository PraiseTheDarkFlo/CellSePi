import pathlib
import platform
import numpy as np
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtWidgets import QApplication, QLabel, QVBoxLayout, QPushButton, QWidget,QGraphicsScene,QGraphicsView,QMainWindow
import sys
from ...CellSePi import CellSePi


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
        self.setWindowTitle("PyQt Window")

        self.canvas= DrawingCanvas(self.csp)
        self.setCentralWidget(self.canvas)

        self.canvas.load_mask_to_scene()
        self.canvas.load_image_to_scene()


    def resizeEvent(self, event):
        self.canvas.fitInView(self.canvas.sceneRect(), Qt.KeepAspectRatio)


# start the window of the drawing tools
def open_qt_window(csp: CellSePi):
    app = QApplication(sys.argv)
    window = MyQtWindow(csp)
    window.show()
    app.exec()




class DrawingCanvas(QGraphicsView):
    """
    In the class the images(background, mask) are loaded. Also the Drawing Canvas is implemented in here

    Attributes:
        csp=object of CellSePi
        scene= main scene of the window, framework for images
        mask= saves the mask of the cells
        image_array= saves the datapoints of the cells
        background_image= saves the main image of the cell
    """

    def __init__(self, csp: CellSePi):
        super().__init__()
        self.csp = csp
        self.scene = QGraphicsScene(self)

        self.setScene(self.scene)
        self.mask = None
        self.image_array=None
        self.background_image=None


    def load_mask_to_scene(self):
        """
        loads the mask of the main image as png into the scene and scales it to the
        scene geometry

        """

        current_path = pathlib.PosixPath
        if platform.system() == "Windows":
            pathlib.PosixPath = pathlib.WindowsPath

        #loads the mask of the current image
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

        #set the image into the mask
        pixmap = QPixmap.fromImage(image)
        self.scale_image(pixmap, self.mask)

    def scale_image(self,image,object,depth = 1):
        """
        does the scaling for the needed image and adds it to the window

        Args:
            image= the used image
            object= the used object
            depth= the depth of the image in the scene

        """
        view_width = self.width()
        view_height = self.height()

        scaled_pixmap = image.scaled(view_width,view_height, Qt.KeepAspectRatio, Qt.SmoothTransformation)

        if object:
            self.scene.removeItem(object)
        object = self.scene.addPixmap(scaled_pixmap)
        object.setZValue(depth)

    def load_image_to_scene(self):
        """
        loads the main image into the scene
        """
        if self.csp.adjusted_image_path is not None:
            image = QPixmap(self.csp.adjusted_image_path)
        else:
            image= QPixmap(self.csp.image_paths[self.csp.image_id])


        self.scale_image(image,self.background_image,-1)

