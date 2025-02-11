# TODO REVIEW unused imports
import asyncio
import pathlib
import platform
import threading
from cgitb import enable
from tabnanny import process_tokens
from threading import Thread

import cv2
import numpy as np
from PyQt5.QtCore import Qt, QPoint, pyqtSignal, QThread, QObject, QTimer, QCoreApplication, QPointF
from PyQt5.QtGui import QImage, QPixmap, QPainter, QPen, QColor
from PyQt5.QtWidgets import QApplication, QLabel, QVBoxLayout, QHBoxLayout, QPushButton, QWidget, QGraphicsScene, \
    QGraphicsView, QMainWindow, QGraphicsLineItem, QCheckBox
import sys

from distributed.utils_test import throws
from matplotlib.pyplot import draw_if_interactive

from ...CellSePi import CellSePi
import copy

from ...drawing.drawing_util import mask_shifting, bresenham_line, search_free_id, fill_polygon_from_outline, \
    find_border_pixels, trace_contour


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
        self.setWindowTitle("Mask Editing")
        self.check_shifting = QCheckBox("Cell ID shifting")
        self.check_shifting.setStyleSheet(
            "font-size: 16px; color:#000000; padding: 10px 20px; margin-bottom: 10px; background-color: #F5F5F5; border: 1px solid #CCCCCC; border-radius: 5px;")
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
        title.setStyleSheet(
            "font-size: 20px; font-weight: bold; color: #333; padding: 10px; text-align: center; background-color: #EDEDED; border-radius: 5px;")
        tools_layout.addWidget(title)

        # Add buttons to the tools box
        self.draw_toggle_button = QPushButton("Drawing : OFF")
        self.draw_toggle_button.setCheckable(True)
        self.draw_toggle_button.setStyleSheet(
            "font-size: 16px; color:#000000; padding: 10px 20px; margin-bottom: 10px; background-color: #F5F5F5; border: 1px solid #CCCCCC; border-radius: 5px;")
        self.draw_toggle_button.clicked.connect(self.toggle_draw_mode)
        tools_layout.addWidget(self.draw_toggle_button)

        self.delete_toggle_button = QPushButton("Delete Mode: OFF")
        self.delete_toggle_button.setCheckable(True)
        self.delete_toggle_button.setStyleSheet(
            "font-size: 16px; color: #000000; padding: 10px 20px; margin-bottom: 10px; background-color: #F5F5F5; border: 1px solid #CCCCCC; border-radius: 5px;")
        self.delete_toggle_button.clicked.connect(self.toggle_delete_mode)
        tools_layout.addWidget(self.delete_toggle_button)

        tools_layout.addWidget(self.check_shifting, alignment=Qt.AlignCenter)

        self.restore_button = QPushButton("Restore Deleted Cell")
        self.restore_button.setStyleSheet(
            "font-size: 16px; color: #000000; padding: 10px 20px; background-color: #F5F5F5; border: 1px solid #CCCCCC; border-radius: 5px;")
        self.restore_button.clicked.connect(self.restore_cell)
        tools_layout.addWidget(self.restore_button)

        self.redo_button = QPushButton("Redo Delete")
        self.redo_button.setStyleSheet(
            "font-size: 16px; color: #000000; padding: 10px 20px; background-color: #F5F5F5; border: 1px solid #CCCCCC; border-radius: 5px;")
        self.redo_button.clicked.connect(self.redo_delete)
        tools_layout.addWidget(self.redo_button)

        self.tools_widget.setLayout(tools_layout)
        self.tools_widget.setStyleSheet(
            "background-color: #FAFAFA; border-left: 2px solid #E0E0E0;")  # Subtle border and clean background
        self.tools_widget.setFixedWidth(250)
        self.main_layout.addWidget(self.tools_widget)

        central_widget.setLayout(self.main_layout)
        self.setCentralWidget(central_widget)

        #screen layout
        screen = QApplication.primaryScreen()
        screen_geometry = screen.geometry()
        window_geometry = self.geometry()
        x = (screen_geometry.width() - window_geometry.width()) // 2
        y = (screen_geometry.height() - window_geometry.height()) // 2

        self.move(x, y)

    def restore_cell(self):
        if not self.canvas_dummy:
            self.canvas.restore_cell()

    def redo_delete(self):
        if not self.canvas_dummy:
            self.canvas.redo_delete()

    #TODO review by Jenna: nach unserem Standard fehlen hier die Parameter, die übergeben werden
    # Hier würde ich auch noch weitere inline Kommentare hinzufügen
    def set_queue_image(self, mask_color, outline_color, bf_channel, mask_paths, image_id, adjusted_image_path, conn,
                        mask_path,channel_id,channel_prefix):
        """
        Sets the current selected mask and image into the MyQtWindow, replacing the canvas with the current parameters.
        Also updates the window title to include the image_id.
        """
        # Update the window title with the current image's ID and channel ID.
        self.setWindowTitle(f"Mask Editing - {image_id}{channel_prefix}{channel_id}")
        if self.canvas_dummy:
            new_canvas = DrawingCanvas(mask_color, outline_color, bf_channel, mask_paths, image_id, adjusted_image_path,
                                       self.check_shifting, conn, mask_path, False, False)
        else:
            if image_id == self.canvas.image_id and bf_channel == self.canvas.bf_channel:
                self.canvas.adjusted_image_path = adjusted_image_path
                self.canvas.load_image_to_scene()
                return
            else:
                new_canvas = DrawingCanvas(mask_color, outline_color, bf_channel, mask_paths, image_id,
                                           adjusted_image_path,
                                           self.check_shifting, conn, mask_path, self.canvas.draw_mode,
                                           self.canvas.delete_mode)
        self.canvas_dummy = False
        self.main_layout.replaceWidget(self.canvas, new_canvas)
        self.canvas.deleteLater()
        self.canvas = new_canvas
        self.canvas.update()
        self.main_layout.update()

        # Connect signals to update the state of the restore and redo buttons.
        self.canvas.restoreAvailabilityChanged.connect(lambda available: self.restore_button.setEnabled(available))
        self.canvas.redoAvailabilityChanged.connect(lambda available: self.redo_button.setEnabled(available))

        QTimer.singleShot(0, lambda: self.canvas.fitInView(self.canvas.sceneRect(), Qt.KeepAspectRatio)) #TODO: hier dazu schreiben, dass das die Größe anpasst

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

    # TODO: review by Jenna: warum prüfst und setzt du vorher das isChecked, wenn du gar kein
    # checkbox-Kästchen verwendest? Dann ist das ja egal.
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
    Handles the signals that come from the queue.
    """
    update_signal = pyqtSignal(object, object)  # Signal for new main_image
    close_signal = pyqtSignal(object, object)  # Signal to close the drawing window
    delete_signal = pyqtSignal(object, )  # Signal that the main_image mask got deleted
    refresh_signal = pyqtSignal()  # Signal that the main_image mask got deleted
    color_change_signal = pyqtSignal(object, object)

    def __init__(self, window):
        super().__init__()
        self.update_signal.connect(self.handle_update)
        self.close_signal.connect(self.handle_close)
        self.delete_signal.connect(self.handle_delete)
        self.refresh_signal.connect(self.handle_refresh)
        self.color_change_signal.connect(self.update_color)
        self.window: MyQtWindow = window

    def handle_update(self, data, conn):
        """
        If the update signal is received, update the window accordingly.
        """
        print("update signal")
        mask_color, outline_color, bf_channel, mask_paths, image_id, adjusted_image_path, mask_path, channel_id, channel_prefix = data
        self.window.set_queue_image(mask_color, outline_color, bf_channel, mask_paths, image_id, adjusted_image_path,
                                    conn, mask_path,channel_id,channel_prefix)
        self.window.setVisible(True)
        self.window.raise_()
        self.window.activateWindow()

    def handle_close(self, app, running):
        """
        If the close signal is received, close the process.
        """
        print("test close")
        self.window.hide()
        running[0] = False
        app.quit()
        print("handle close finished")

    def handle_delete(self, app):
        print("delete signal")
        self.window.hide()
        app.quit()

    def handle_refresh(self):
        print("refresh signal")
        if not self.window.canvas_dummy:
            self.window.canvas.store_mask()
            self.window.canvas.load_mask_to_scene()

    def update_color(self, mask_color, outline_color):
        if not self.window.canvas_dummy:
            self.window.canvas.mask_color = mask_color
            self.window.canvas.outline_color = outline_color
            self.window.canvas.load_mask_to_scene()

#TODO reviewed by Jenna: Hier würde ich eine Erklärung einfügen, was die Queue für eine Bedeutung/Funktionalität hat
def open_qt_window(queue, conn):
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

            async def queue_listener():
                while running[0]:
                    data = await asyncio.to_thread(queue.get)
                    if data == "close":
                        updater.close_signal.emit(app, running)
                        break
                    elif data == "delete_image":
                        updater.delete_signal.emit(app)
                    elif data == "refresh_mask":
                        updater.refresh_signal.emit()
                    elif data == "close_thread":
                        break
                    elif isinstance(data, (tuple, list)) and data[0] == "color_change":
                        _, mask_color, outline_color = data
                        updater.color_change_signal.emit(mask_color, outline_color)
                    else:
                        updater.update_signal.emit(data, conn)

            try:
                loop.run_until_complete(queue_listener())
            finally:
                loop.stop()
                loop.close()

        thread = threading.Thread(target=background_listener, daemon=True)
        thread.start()
        print("before app.exec")
        app.exec_()
        if running[0]:
            queue.put("close_thread")
        if thread is not None and thread.is_alive():
            thread.join()
        window.close()
        window.deleteLater()
    print("main window closed")
    conn.send("close")
    sys.exit(0)


class DrawingCanvas(QGraphicsView):
    """
    Class for displaying and interacting with images (background, mask).
    Includes delete functionality for cells and supports undo (restore) and redo of cell deletion.

    Attributes:
        csp: Object of CellSePi
        scene: Main scene of the window
        image_array: Stores cell data points
        mask_item: Graphics item for the mask
        background_item: Graphics item for the background image
        delete_mode: Boolean to track if delete mode is enabled
        cell_history: List to keep track of deleted cells for restoration (undo)
        redo_history: List to keep track of restored cells for re-deletion (redo)
        check_box: QCheckBox to check if the cells should be shifted when deleted.
    """
    # Signals to indicate whether a restore or redo action is available.
    restoreAvailabilityChanged = pyqtSignal(bool)
    redoAvailabilityChanged = pyqtSignal(bool)

    def __init__(self, mask_color, outline_color, bf_channel, mask_paths, image_id, adjusted_image_path, check_box,
                 conn, mask_path, draw_mode=False, delete_mode=False):
        super().__init__()
        self.mask_color = mask_color
        self.outline_color = outline_color
        self.bf_channel = bf_channel
        self.mask_paths = mask_paths
        self.image_id = image_id
        self.adjusted_image_path = adjusted_image_path
        self.mask_path = mask_path
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
        self.mask_data = None
        self.cell_history = []  # Track deleted cells for restoration (undo)
        self.redo_history = []  # Track restored cells for re-deletion (redo)
        self.check_box = check_box
        self.points = []  # saves all points in the drawing
        self.conn = conn
        self.load_mask_to_scene()
        self.load_image_to_scene()

    def toggle_draw_mode(self):
        self.draw_mode = not self.draw_mode

    def toggle_delete_mode(self):
        self.delete_mode = not self.delete_mode

    def set_draw_mode(self, value: bool):
        self.draw_mode = value

    def set_delete_mode(self, value: bool):
        self.delete_mode = value

    def is_point_within_image(self, point):
        """
        Check if a point is within the boundaries of the image.
        """
        if self.image_array is None:
            return False  # No image loaded
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
                    self.points = []
                    self.points.append(current_point)
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
                self.points.append(current_point)
            else:
                self.drawing = False

    def mouseReleaseEvent(self, event):
        if self.draw_mode and self.drawing:
            self.drawing = False

            # Connect last point to start point
            if self.last_point and self.start_point:
                line_item = QGraphicsLineItem(self.last_point.x(), self.last_point.y(),
                                              self.start_point.x(), self.start_point.y())
                r, g, b = self.outline_color
                pen = QPen(QColor(r, g, b), 2, Qt.SolidLine)
                line_item.setPen(pen)
                self.scene.addItem(line_item)
                self.points.append(line_item)
            
            # Reset start and last points
            self.start_point = None
            self.last_point = None

            self.update()
            self.update_outlines_from_lineitems()
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

    def store_mask(self):
        mask = self.mask_data["masks"]
        outline = self.mask_data["outlines"]

        # Save current state of the cell for restoration (undo)
        mask_old = mask.copy()
        outline_old = outline.copy()
        self.cell_history.append((mask_old, outline_old, "complete mask"))
        self.restoreAvailabilityChanged.emit(len(self.cell_history) > 0)

    def delete_cell(self, cell_id):
        """
        Delete the specified cell by updating the mask data.
        Also does not clear stored redo history, enabling multiple redo levels.
        """
        mask_path = self.mask_paths[self.image_id][self.bf_channel]
        self.mask_data = np.load(mask_path, allow_pickle=True).item()

        mask = self.mask_data["masks"]
        outline = self.mask_data["outlines"]

        # Save current state of the cell for restoration (undo)
        mask_old = mask.copy()
        outline_old = outline.copy()
        self.cell_history.append((mask_old, outline_old, cell_id))

        # Update the mask and outline (delete the cell)
        cell_mask = (mask == cell_id).copy()
        cell_outline = (outline == cell_id).copy()
        mask[cell_mask] = 0
        outline[cell_outline] = 0
        if self.check_box.isChecked():
            mask_shifting(self.mask_data, cell_id)
        # Save the updated mask
        np.save(mask_path, {"masks": mask, "outlines": outline}, allow_pickle=True)
        print(f"Deleted cell ID {cell_id}. Reloading mask...")
        self.load_mask_to_scene()
        self.conn.send("update_mask")
        self.restoreAvailabilityChanged.emit(len(self.cell_history) > 0)
        self.redoAvailabilityChanged.emit(len(self.redo_history) > 0)

    def restore_cell(self):
        """
        Restore the most recently deleted cell (undo the deletion).
        Also stores the restored cell in a redo history so that the deletion can be re-applied.
        """
        # ToDO by Jenna: in dem Fall, dass keine Cellen in der cell_history sind, ist der Print unnötigt, denn
        # der wird ja nie in der GUI ausgeführt. ALso entweder error banner in der GUI oder gar keinen print machen
        # vielleicht hier auch eine beschränkung einbauen für das restoren. Im Moment ist es möglich die Zellen unendlich oft
        # zu storen, selbst wenn cell_history leer ist: Du könntest den Restore button vielleicht ausgrauen, wenn keine Zellen mehr drinn sind
        if not self.cell_history:
            # No cells to restore; update button state via signal and do nothing.
            self.restoreAvailabilityChanged.emit(False)
            return

        mask_path = self.mask_paths[self.image_id][self.bf_channel]

        # Restore the most recent cell (pop from undo stack)
        mask_old, outline_old, cell_id = self.cell_history.pop()

        mask = mask_old.copy()
        outline = outline_old.copy()

        # Save the updated (restored) mask
        np.save(mask_path, {"masks": mask, "outlines": outline}, allow_pickle=True)
        print(f"Restored cell ID {cell_id}. Reloading mask...")
        self.load_mask_to_scene()
        self.conn.send("update_mask")

        # Store the restored cell in redo history (so that deletion can be redone)
        self.redo_history.append((mask_old, outline_old, cell_id))
        self.restoreAvailabilityChanged.emit(len(self.cell_history) > 0)
        self.redoAvailabilityChanged.emit(len(self.redo_history) > 0)

    def redo_delete(self):
        """
        Re-apply the deletion for the most recently restored cell (redo the deletion).
        """
        if not self.redo_history:
            self.redoAvailabilityChanged.emit(False)
            return
        # Get the last restored cell info from the redo history
        mask_old, outline_old, cell_id = self.redo_history.pop()
        # Re-delete the cell by calling delete_cell
        self.delete_cell(cell_id)
        self.redoAvailabilityChanged.emit(len(self.redo_history) > 0)

    def load_mask_to_scene(self):
        """
        Load the mask and display it on the scene.
        """
        if self.image_id not in self.mask_paths:
            self.mask_paths[self.image_id] = {}

        if self.bf_channel not in self.mask_paths[self.image_id]:
            pixmap = QPixmap(self.adjusted_image_path)
            empty_mask = {
                "masks": np.zeros((pixmap.width(), pixmap.height()), dtype=np.uint8),
                "outlines": np.zeros((pixmap.width(), pixmap.height()), dtype=np.uint8)
            }
            np.save(self.mask_path, empty_mask)
            self.mask_paths[self.image_id][self.bf_channel] = self.mask_path

        mask_path = self.mask_paths[self.image_id][self.bf_channel]

        self.mask_data = np.load(mask_path, allow_pickle=True).item()

        mask = self.mask_data["masks"]
        outline = self.mask_data["outlines"]
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

    def get_npy_of_mask(self):
        mask_path = self.mask_paths[self.image_id][self.bf_channel]
        mask_data = np.load(mask_path, allow_pickle=True).item()

        mask = mask_data["masks"]
        outline = mask_data["outlines"]

        return mask, outline


    def update_outlines_from_lineitems(self):
        """
        - Ermittelt alle Pixelkoordinaten aus den in der Szene vorhandenen QGraphicsLineItems.
        - Setzt in der npy-Datei (im "outlines"-Array) an diesen Pixelpositionen den Wert 100.
        - Entfernt anschließend alle QGraphicsLineItems aus der Szene.
        """
        # 1. Alle Pixel der QGraphicsLineItems sammeln:
        line_pixels = set()  # Set vermeiden Duplikate
        for item in self.scene.items():
            if isinstance(item, QGraphicsLineItem):
                line = item.line()  # QLineF-Objekt
                # Pixelkoordinaten der Linie ermitteln:
                pixels = bresenham_line(line.p1(), line.p2())
                line_pixels.update(pixels)

        # 2. npy-Datei laden und die "outlines" an den gefundenen Pixeln auf 100 setzen:
        mask_path = self.mask_paths[self.image_id][self.bf_channel]
        self.mask_data = np.load(mask_path, allow_pickle=True).item()

        # "masks" und "outlines" laden
        mask = self.mask_data["masks"]
        outline = self.mask_data["outlines"]

        # Iteriere über alle ermittelten Pixelkoordinaten
        print("BEFEHL")
        free_id = search_free_id(mask, outline)
        mask_old = mask.copy()
        outline_old = outline.copy()
        self.cell_history.append((mask_old, outline_old, free_id))
        self.restoreAvailabilityChanged.emit(len(self.cell_history) > 0)
        self.redoAvailabilityChanged.emit(len(self.redo_history) > 0)
        print(free_id)
        outline_cpy = np.zeros_like(outline)
        for x, y in line_pixels:
            # Prüfen, ob (x,y) innerhalb der Array-Grenzen liegt.
            # Achtung: In numpy entspricht der erste Index der Zeile (y) und der zweite der Spalte (x).
            if 0 <= x < outline.shape[1] and 0 <= y < outline.shape[0]:
                outline_cpy[y, x] = free_id

                if outline[y, x] == 0 and mask[y, x] == 0:
                    outline[y, x] = free_id
        outline_pixels = []
        for y in range(outline.shape[0]):
            for x in range(outline.shape[1]):
                if outline_cpy[y, x] == free_id:
                    outline_pixels.append((x, y))
        binary_mask = np.zeros_like(outline_cpy, dtype=np.uint8)
        for x, y in outline_pixels:
            binary_mask[y, x] = 1
        contour = trace_contour(binary_mask)
        polygon_mask = fill_polygon_from_outline(contour, mask.shape)
        mask[(polygon_mask == 1) &(mask == 0) & (outline == 0)] = free_id
        border_pixels = find_border_pixels(mask,outline,free_id)
        for y, x in border_pixels:
            if 0 <= x < outline.shape[1] and 0 <= y < outline.shape[0]:
                mask[y, x] = 0
                outline[y, x] = free_id
        np.save(mask_path, {"masks": mask, "outlines": outline}, allow_pickle=True)
        self.load_mask_to_scene()
        self.conn.send("update_mask")
        for item in list(self.scene.items()):
            if isinstance(item, QGraphicsLineItem):
                self.scene.removeItem(item)
