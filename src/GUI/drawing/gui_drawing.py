#TODO REVIEW unused imports
import pathlib
import platform
from cgitb import enable

import numpy as np
from PyQt5.QtCore import Qt, QPoint, pyqtSignal, QThread, QObject
from PyQt5.QtGui import QImage, QPixmap, QPainter, QPen, QColor
from PyQt5.QtWidgets import QApplication, QLabel, QVBoxLayout, QHBoxLayout, QPushButton, QWidget, QGraphicsScene, \
    QGraphicsView, QMainWindow, QGraphicsLineItem, QCheckBox
import sys

from matplotlib.pyplot import draw_if_interactive

from ...CellSePi import CellSePi
import copy

from ...drawing.drawing_util import mask_shifting


class MyQtWindow(QMainWindow):
    """
    Main PyQt window for drawing tools and deleting cells.

    Attributes:
        csp: Current CellSePi instance to access images and masks.
        canvas: DrawingCanvas object for displaying and interacting with the mask.
        tools_widget: Container for tools on the right side.
    """
    def __init__(self,mask_color,outline_color,bf_channel,mask_paths,image_id,adjusted_image_path):
        super().__init__()
        self.mask_color = mask_color
        self.outline_color = outline_color
        self.bf_channel = bf_channel
        self.mask_paths = mask_paths
        self.image_id = image_id
        self.adjusted_image_path = adjusted_image_path
        self.setWindowTitle("Drawing & Mask Editing")
        self.check_shifting = QCheckBox("Cell ID shifting")
        self.check_shifting.setStyleSheet("font-size: 16px; color:#000000; padding: 10px 20px; margin-bottom: 10px; background-color: #F5F5F5; border: 1px solid #CCCCCC; border-radius: 5px;")
        self.canvas = DrawingCanvas(mask_color,outline_color,bf_channel,mask_paths,image_id,adjusted_image_path,self.check_shifting)

        # Main layout with canvas and tools
        central_widget = QWidget()
        main_layout = QHBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)  # Remove margins on all sides

        # Add canvas to the left
        main_layout.addWidget(self.canvas, stretch=3)

        # Add tools box to the right
        self.tools_widget = QWidget()
        tools_layout = QVBoxLayout()
        tools_layout.setContentsMargins(10, 10, 10, 10)  # Consistent padding
        tools_layout.setAlignment(Qt.AlignTop)  # Align tools to the top

        # Add title to the tools box
        title = QLabel("Tools")
        title.setStyleSheet("font-size: 20px; font-weight: bold; color: #333; padding: 10px; text-align: center; background-color: #EDEDED; border-radius: 5px;")
        tools_layout.addWidget(title)

        #TODO REVIEW bei mir wird die Schrift der Buttons als weiß auf weißem Hintergrund angezeigt -> nicht so gut lesbar, sowohl im dark und light mode

        # Add buttons to the tools box
        self.draw_toggle_button = QPushButton("Drawing : OFF")
        self.draw_toggle_button.setCheckable(True)
        self.draw_toggle_button.setStyleSheet("font-size: 16px; color:#000000; padding: 10px 20px; margin-bottom: 10px; background-color: #F5F5F5; border: 1px solid #CCCCCC; border-radius: 5px;")
        self.draw_toggle_button.clicked.connect(self.toggle_draw_mode)
        tools_layout.addWidget(self.draw_toggle_button)

        self.delete_toggle_button = QPushButton("Delete Mode: OFF")
        self.delete_toggle_button.setCheckable(True)
        self.delete_toggle_button.setStyleSheet("font-size: 16px; color: #000000; padding: 10px 20px; margin-bottom: 10px; background-color: #F5F5F5; border: 1px solid #CCCCCC; border-radius: 5px;")
        self.delete_toggle_button.clicked.connect(self.toggle_delete_mode)
        tools_layout.addWidget(self.delete_toggle_button)

        tools_layout.addWidget(self.check_shifting,alignment=Qt.AlignCenter)

        self.restore_button = QPushButton("Restore Deleted Cell")
        self.restore_button.setStyleSheet("font-size: 16px; color: #000000; padding: 10px 20px; background-color: #F5F5F5; border: 1px solid #CCCCCC; border-radius: 5px;")
        self.restore_button.clicked.connect(self.canvas.restore_cell)
        tools_layout.addWidget(self.restore_button)


        self.tools_widget.setLayout(tools_layout)
        self.tools_widget.setStyleSheet("background-color: #FAFAFA; border-left: 2px solid #E0E0E0;")  # Subtle border and clean background
        self.tools_widget.setFixedWidth(250)
        main_layout.addWidget(self.tools_widget)

        central_widget.setLayout(main_layout)
        self.setCentralWidget(central_widget)

        self.canvas.load_mask_to_scene()
        self.canvas.load_image_to_scene()

    def toggle_draw_mode(self):
        """
        Drawing Button functionality
        """
        if self.draw_toggle_button.isChecked():
            self.draw_toggle_button.setText("Drawing : ON")
            self.canvas.enable_draw_mode(True)
        else:
            self.draw_toggle_button.setText("Drawing : OFF")
            self.canvas.enable_draw_mode(False)

    def toggle_delete_mode(self):
        """
        Toggle delete mode when the button is clicked.
        """
        if self.delete_toggle_button.isChecked():
            self.delete_toggle_button.setText("Delete Mode: ON")
            self.canvas.enable_delete_mode(True)
        else:
            self.delete_toggle_button.setText("Delete Mode: OFF")
            self.canvas.enable_delete_mode(False)

    def resizeEvent(self, event):
        self.canvas.fitInView(self.canvas.sceneRect(), Qt.KeepAspectRatio)


class Communicator(QObject):
    update_window = pyqtSignal(dict)

class QueueListener(QThread):
    def __init__(self, queue, communicator):
        super().__init__()
        self.queue = queue
        self.communicator = communicator

    def run(self):
        while True:
            data = self.queue.get()
            self.communicator.update_window.emit(data)

# Start the window of the drawing tools
def open_qt_window(queue):
    app = QApplication(sys.argv)
    window = QWidget()
    window.setWindowTitle("Waiting")
    window.setGeometry(100, 100, 400, 300)
    window.setVisible(False)
    while True:
        mask_color, outline_color, bf_channel, mask_paths, image_id, adjusted_image_path = queue.get()
        print(f"Mask Color: {mask_color}")
        print(f"Outline Color: {outline_color}")
        print(f"BF Channel: {bf_channel}")
        print(f"Mask Paths: {mask_paths}")
        print(f"Image ID: {image_id}")
        print(f"Adjusted Image Path: {adjusted_image_path}")
        window = MyQtWindow(mask_color,outline_color,bf_channel,mask_paths,image_id,adjusted_image_path)
        window.setVisible(True)
        window.show()
        app.exec_()

class DrawingCanvas(QGraphicsView):
    """
    Class for displaying and interacting with images (background, mask).
    Includes delete functionality for cells.

    Attributes:
        csp: Object of CellSePi
        scene: Main scene of the window
        image_array: Stores cell data points
        mask_item: Graphics item for the mask
        background_item: Graphics item for the background image
        delete_mode: Boolean to track if delete mode is enabled
        cell_history: List to keep track of deleted cells
        check_box: QCheckBox to check if the cells should be shifted when deleted.
    """

    def __init__(self,mask_color,outline_color,bf_channel,mask_paths,image_id,adjusted_image_path,check_box):
        super().__init__()
        self.mask_color = mask_color
        self.outline_color = outline_color
        self.bf_channel = bf_channel
        self.mask_paths = mask_paths
        self.image_id = image_id
        self.adjusted_image_path = adjusted_image_path
        self.scene = QGraphicsScene(self)
        self.setScene(self.scene)
        self.draw_mode = False
        self.last_point = QPoint()
        self.drawing = False
        self.delete_mode = False
        self.image_array = None
        self.mask_item = None
        self.background_item = None
        self.cell_history = []  # Track deleted cells for restoration
        self.check_box = check_box
        self.image_rect = None  # Stores the boundaries of the background image

    def enable_draw_mode(self, enabled):

        self.draw_mode = enabled
        print(f"Drawing mode {'enabled' if self.draw_mode else 'disabled'}")

    def enable_delete_mode(self, enable):
        """
        Enable or disable delete mode.
        """
        self.delete_mode = enable
        print(f"Delete mode {'enabled' if self.delete_mode else 'disabled'}.")

    def is_point_within_image(self, point):
        """
        Check if the given point in scene coordinates is within the background image.
        """
        return self.image_rect and self.image_rect.contains(point)


    def mousePressEvent(self, event):
        """
        Handle mouse click events for drawing or deleting cells.
        """
        if self.draw_mode:
            if event.button() == Qt.LeftButton:
                # Map the mouse click position to the scene coordinates
                mapped_point = self.mapToScene(event.pos())
                if self.is_point_within_image(mapped_point):  # Check if within the image boundaries
                    self.drawing = True
                    self.last_point = mapped_point  # Store the starting point for the drawing
        elif self.delete_mode:
            pos = event.pos()
            scene_pos = self.mapToScene(pos)
            cell_id = self.get_cell_id_from_position(scene_pos)
            if cell_id:
                self.delete_cell(cell_id)
        else:
            super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self.draw_mode and self.drawing:
            current_point = self.mapToScene(event.pos())
            if self.is_point_within_image(current_point):
                line_item = QGraphicsLineItem(self.last_point.x(), self.last_point.y(),
                                          current_point.x(), current_point.y())
                r,g,b = self.outline_color
                pen = QPen(QColor(r,g,b), 2, Qt.SolidLine)
                line_item.setPen(pen)
                self.scene.addItem(line_item)
                self.last_point = current_point
                self.update()

    def mouseReleaseEvent(self, event):
        if self.draw_mode and self.drawing:
            self.drawing = False
            self.update()


    def get_cell_id_from_position(self, position):
        """
        Get the cell ID from the clicked position.
        """
        x, y = int(position.x()), int(position.y())
        if 0 <= x < self.image_array.shape[1] and 0 <= y < self.image_array.shape[0]:
            return self.image_array[y, x]
        return None

    def delete_cell(self, cell_id):
        """
        Delete the specified cell by updating the mask data.
        """
        mask_path = self.mask_paths[self.image_id][self.bf_channel]
        mask_data = np.load(mask_path, allow_pickle=True).item()

        mask = mask_data["masks"]
        outline = mask_data["outlines"]

        # Save current state of the cell for restoration
        mask_old = mask.copy()
        outline_old = outline.copy()
        self.cell_history.append((mask_old, outline_old, cell_id))

        # Update the mask and outline
        cell_mask = (mask == cell_id).copy()
        cell_outline = (outline == cell_id).copy()
        mask[cell_mask] = 0
        outline[cell_outline] = 0
        if self.check_box.isChecked():
            mask_shifting(mask_data, cell_id)
        # Save the updated mask
        np.save(mask_path, {"masks": mask, "outlines": outline}, allow_pickle=True)
        print(f"Deleted cell ID {cell_id}. Reloading mask...")
        self.load_mask_to_scene()

    def restore_cell(self):
        """
        Restore the most recently deleted cell.
        """
        if not self.cell_history:
            print("No cells to restore.")
            return

        mask_path = self.mask_paths[self.image_id][self.bf_channel]


        # Restore the most recent cell
        mask_old, outline_old, cell_id = self.cell_history.pop()

        mask = mask_old.copy()
        outline = outline_old.copy()

        # Save the updated mask
        np.save(mask_path, {"masks": mask, "outlines": outline}, allow_pickle=True)
        print(f"Restored cell ID {cell_id}. Reloading mask...")
        self.load_mask_to_scene()

    def load_mask_to_scene(self):
        """
        Load the mask and display it on the scene.
        """
        mask_path = self.mask_paths[self.image_id][self.bf_channel]
        mask_data = np.load(mask_path, allow_pickle=True).item()

        mask = mask_data["masks"]
        outline = mask_data["outlines"]
        # Create RGBA mask
        image_mask = np.zeros((mask.shape[0], mask.shape[1], 4), dtype=np.uint8)
        r, g, b = self.mask_color
        image_mask[mask != 0] = (r, g, b, 128)
        r, g, b = self.outline_color
        image_mask[outline != 0] = (r, g, b, 255)
        self.image_array = mask

        # Update mask item in the scene
        height, width, _ = image_mask.shape
        qimage = QImage(image_mask.data, width, height, QImage.Format_RGBA8888)
        pixmap = QPixmap.fromImage(qimage)
        if self.mask_item:
            self.scene.removeItem(self.mask_item)
        self.mask_item = self.scene.addPixmap(pixmap)
        self.mask_item.setZValue(1)

        self.scene.setSceneRect(0, 0, width, height)
        self.fitInView(self.sceneRect(), Qt.KeepAspectRatio)

    def load_image_to_scene(self):
        """
        Load the main background image into the scene.
        """
        pixmap = QPixmap(self.adjusted_image_path)


        if self.background_item:
            self.scene.removeItem(self.background_item)
        self.background_item = self.scene.addPixmap(pixmap)
        self.background_item.setZValue(-1)

        self.image_rect = self.background_item.boundingRect()

        self.scene.setSceneRect(0, 0, pixmap.width(), pixmap.height())
        self.fitInView(self.sceneRect(), Qt.KeepAspectRatio)
