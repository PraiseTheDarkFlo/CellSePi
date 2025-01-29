#TODO REVIEW unused imports
import asyncio
import pathlib
import platform
import threading
from cgitb import enable
from tabnanny import process_tokens
from threading import Thread


import numpy as np
from PyQt5.QtCore import Qt, QPoint, pyqtSignal, QThread, QObject, QTimer, QCoreApplication
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
        canvas: DrawingCanvas object for displaying and interacting with the mask.
        canvas_dummy: says if the canvas is a dummy or not.
        tools_widget: Container for tools on the right side.
    """
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Drawing & Mask Editing")
        self.check_shifting = QCheckBox("Cell ID shifting")
        self.check_shifting.setStyleSheet("font-size: 16px; color:#000000; padding: 10px 20px; margin-bottom: 10px; background-color: #F5F5F5; border: 1px solid #CCCCCC; border-radius: 5px;")
        self.canvas_dummy = True

        self.canvas = QWidget()

        # Main layout with canvas and tools
        central_widget = QWidget()
        self.main_layout = QHBoxLayout()
        self.main_layout.setContentsMargins(0, 0, 0, 0)  # Remove margins on all sides


        self.main_layout.addWidget(self.canvas, stretch=3)

        # Add tools box to the right
        self.tools_widget = QWidget()
        tools_layout = QVBoxLayout()
        tools_layout.setContentsMargins(10, 10, 10, 10)  # Consistent padding
        tools_layout.setAlignment(Qt.AlignTop)  # Align tools to the top

        # Add title to the tools box
        title = QLabel("Tools")
        title.setStyleSheet("font-size: 20px; font-weight: bold; color: #333; padding: 10px; text-align: center; background-color: #EDEDED; border-radius: 5px;")
        tools_layout.addWidget(title)

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

        tools_layout.addWidget(self.check_shifting, alignment=Qt.AlignCenter)

        self.restore_button = QPushButton("Restore Deleted Cell")
        self.restore_button.setStyleSheet("font-size: 16px; color: #000000; padding: 10px 20px; background-color: #F5F5F5; border: 1px solid #CCCCCC; border-radius: 5px;")
        self.restore_button.clicked.connect(self.restore_cell)
        tools_layout.addWidget(self.restore_button)

        self.tools_widget.setLayout(tools_layout)
        self.tools_widget.setStyleSheet("background-color: #FAFAFA; border-left: 2px solid #E0E0E0;")  # Subtle border and clean background
        self.tools_widget.setFixedWidth(250)
        self.main_layout.addWidget(self.tools_widget)

        central_widget.setLayout(self.main_layout)
        self.setCentralWidget(central_widget)

        screen = QApplication.primaryScreen()
        screen_geometry = screen.geometry()
        window_geometry = self.geometry()
        x = (screen_geometry.width() - window_geometry.width()) // 2
        y = (screen_geometry.height() - window_geometry.height()) // 2

        self.move(x, y)

    def restore_cell(self):
        if not self.canvas_dummy:
            self.canvas.restore_cell()

    def set_queue_image(self, mask_color, outline_color, bf_channel, mask_paths, image_id, adjusted_image_path, conn):
        """
        Sets the current selected mask and image into the MyQtWindow, with replacing the canvas with the current parameters.
        """
        if self.canvas_dummy:
            new_canvas = DrawingCanvas(mask_color, outline_color, bf_channel, mask_paths, image_id, adjusted_image_path,
                                        self.check_shifting, conn, False, False)
        else:
            new_canvas = DrawingCanvas(mask_color, outline_color, bf_channel, mask_paths, image_id, adjusted_image_path,
                                        self.check_shifting, conn, self.canvas.draw_mode, self.canvas.delete_mode)
        self.canvas_dummy = False
        self.main_layout.replaceWidget(self.canvas, new_canvas)
        self.canvas.deleteLater()
        self.canvas = new_canvas
        self.canvas.update()
        self.main_layout.update()
        QTimer.singleShot(0, lambda: self.canvas.fitInView(self.canvas.sceneRect(), Qt.KeepAspectRatio)) #Use singleShot to delay the fitInView so that it can update

    def toggle_draw_mode(self):
        """
        Drawing Button functionality
        """
        if not self.canvas_dummy:
            if self.draw_toggle_button.isChecked():
                self.draw_toggle_button.setText("Drawing : ON")
                self.delete_toggle_button.setChecked(False)
                self.delete_toggle_button.setText("Delete Mode: OFF")
                self.canvas.set_delete_mode(False)
            else:
                self.draw_toggle_button.setText("Drawing : OFF")
            self.canvas.toggle_draw_mode()

    def toggle_delete_mode(self):
        """
        Toggle delete mode when the button is clicked.
        """
        if not self.canvas_dummy:
            if self.delete_toggle_button.isChecked():
                self.delete_toggle_button.setText("Delete Mode: ON")
                self.draw_toggle_button.setChecked(False)
                self.draw_toggle_button.setText("Drawing : OFF")
                self.canvas.set_draw_mode(False)
            else:
                self.delete_toggle_button.setText("Delete Mode: OFF")
            self.canvas.toggle_delete_mode()

    def resizeEvent(self, event):
        self.canvas.fitInView(self.canvas.sceneRect(), Qt.KeepAspectRatio)


class Updater(QObject):
    """
    Handles the signals that he becomes from the queue.
    """
    update_signal = pyqtSignal(object,object)  # Signal für GUI-Updates
    close_signal = pyqtSignal(object,object,object)

    def __init__(self, window):
        super().__init__()
        self.update_signal.connect(self.handle_update)
        self.close_signal.connect(self.handle_close)
        self.window: MyQtWindow = window

    def handle_update(self, data, conn):
        """
        If the update signal is received, update the window accordingly.
        """
        print("update signal")
        mask_color, outline_color, bf_channel, mask_paths, image_id, adjusted_image_path = data
        self.window.set_queue_image(mask_color, outline_color, bf_channel, mask_paths, image_id, adjusted_image_path,conn)
        self.window.setVisible(True)

    def handle_close(self,app,running,queue):
        """
        If the close signal is received, close the process.
        """
        print("test close")
        self.window.close()
        self.window.deleteLater()
        running[0] = False
        app.quit()
        print("handle close finished")

def open_qt_window(queue,conn):
    app = QApplication(sys.argv)
    running = [True]
    thread = None
    while running[0]:
        window = MyQtWindow()
        window.setVisible(False)
        updater = Updater(window)

        def background_listener():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            async def query_listener():
                while running[0]:
                    data = await asyncio.to_thread(queue.get)
                    if data == "close":
                        updater.close_signal.emit(app, running, queue)
                        break
                    else:
                        updater.update_signal.emit(data, conn)

            loop.run_until_complete(query_listener())

        thread = threading.Thread(target=background_listener, daemon=True)
        thread.start()
        print("before app.exec")
        app.exec_()
    print("join thread")
    queue.put("close")
    thread.join()
    print("main window closed")
    sys.exit(0)

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

    def __init__(self,mask_color,outline_color,bf_channel,mask_paths,image_id,adjusted_image_path,check_box,conn,draw_mode = False,delete_mode = False):
        super().__init__()
        self.mask_color = mask_color
        self.outline_color = outline_color
        self.bf_channel = bf_channel
        self.mask_paths = mask_paths
        self.image_id = image_id
        self.adjusted_image_path = adjusted_image_path
        self.scene = QGraphicsScene(self)
        self.setScene(self.scene)
        self.draw_mode = draw_mode
        self.last_point = QPoint()
        self.start_point = None
        self.drawing = False
        self.delete_mode = delete_mode
        self.image_array = None
        self.mask_item = None
        self.background_item = None
        self.cell_history = []  # Track deleted cells for restoration
        self.check_box = check_box
        self.current_path_points = []  # saves all points in the drawing
        self.conn = conn
        self.load_mask_to_scene()
        self.load_image_to_scene()

    def toggle_draw_mode(self):
        self.draw_mode = not self.draw_mode
        print(f"Drawing mode {'enabled' if self.draw_mode else 'disabled'}")

    def toggle_delete_mode(self):
        self.delete_mode = not self.delete_mode
        print(f"Delete mode {'enabled' if self.delete_mode else 'disabled'}.")

    def set_draw_mode(self,value: bool):
        self.draw_mode = value
        print(f"Drawing mode {'enabled' if self.draw_mode else 'disabled'}")

    def set_delete_mode(self,value: bool):
        self.delete_mode = value
        print(f"Delete mode {'enabled' if self.delete_mode else 'disabled'}.")

    def is_point_within_image(self, point):

        """
            Check if a point is within the boundaries of the image.
        """

        if self.image_array is None:
            return False  # Kein Bild geladen
        x, y = int(point.x()), int(point.y())
        return 0 <= x < self.image_array.shape[1] and 0 <= y < self.image_array.shape[0]

    def mousePressEvent(self, event):
        """
        Handle mouse click events for drawing or deleting cells.
        """
        if self.draw_mode:
            if event.button() == Qt.LeftButton:
                self.drawing = True
                current_point = self.mapToScene(event.pos())
                self.last_point = current_point

                if self.start_point is None:
                    self.start_point = current_point
        elif self.delete_mode:
            pos = event.pos()
            scene_pos = self.mapToScene(pos)
            cell_id = self.get_cell_id_from_position(scene_pos)
            if cell_id:
                self.delete_cell(cell_id)
        else:
            super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self.draw_mode:
            current_point = self.mapToScene(event.pos())

            # drawing in picture
            if self.is_point_within_image(current_point):
                x, y = int(current_point.x()), int(current_point.y())

                # drawing in cell
                if self.image_array[y, x] != 0:
                    self.drawing = False
                else:
                    # after cell continue drawing
                    if not self.drawing:
                        self.drawing = True
                        self.last_point = current_point

                    # draw a line
                    line_item = QGraphicsLineItem(self.last_point.x(), self.last_point.y(),
                                                  current_point.x(), current_point.y())
                    r, g, b = self.outline_color
                    pen = QPen(QColor(r, g, b), 2, Qt.SolidLine)
                    line_item.setPen(pen)
                    self.scene.addItem(line_item)
                    self.last_point = current_point
            else:
                self.drawing = False

    def mouseReleaseEvent(self, event):
        if self.draw_mode and self.drawing:
            self.drawing = False

            # start last point connection
            if self.last_point and self.start_point:
                line_item = QGraphicsLineItem(self.last_point.x(), self.last_point.y(),
                                              self.start_point.x(), self.start_point.y())
                r, g, b = self.outline_color
                pen = QPen(QColor(r, g, b), 2, Qt.SolidLine)
                line_item.setPen(pen)
                self.scene.addItem(line_item)

            # Reset start and last points
            self.start_point = None
            self.last_point = None

            self.update()
        else:
            super().mouseReleaseEvent(event)

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
        self.conn.send("update_mask")

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
        self.conn.send("update_mask")

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

        self.scene.setSceneRect(0, 0, pixmap.width(), pixmap.height())
        self.fitInView(self.sceneRect(), Qt.KeepAspectRatio)
