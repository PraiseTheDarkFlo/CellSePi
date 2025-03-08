
import asyncio
import threading
import numpy as np
from PyQt5.QtCore import Qt, QPoint, pyqtSignal, QObject, QTimer, QPointF
from PyQt5.QtGui import QImage, QPixmap, QPen, QColor
from PyQt5.QtWidgets import QApplication, QLabel, QVBoxLayout, QHBoxLayout, QPushButton, QWidget, QGraphicsScene, \
    QGraphicsView, QMainWindow, QGraphicsLineItem, QCheckBox
import sys



from cellsepi.backend.drawing_window.drawing_util import mask_shifting, bresenham_line, search_free_id, fill_polygon_from_outline, \
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

        #Main layout with canvas and tools
        central_widget = QWidget()
        self.main_layout = QHBoxLayout()
        self.main_layout.setContentsMargins(0, 0, 0, 0)  #Remove margins on all sides

        self.main_layout.addWidget(self.canvas, stretch=3)

        #Add tools box to the right
        self.tools_widget = QWidget()
        tools_layout = QVBoxLayout()
        tools_layout.setContentsMargins(10, 10, 10, 10)  #Consistent padding
        tools_layout.setAlignment(Qt.AlignTop)  #Align tools to the top

        #Add title to the tools box
        title = QLabel("Tools")
        title.setStyleSheet(
            "font-size: 20px; font-weight: bold; color: #333; padding: 10px; text-align: center; background-color: #EDEDED; border-radius: 5px;")
        tools_layout.addWidget(title)



        #Add buttons to the tools box
        self.mask_toggle_button = QPushButton("Mask: ON")
        self.mask_toggle_button.setCheckable(True)
        self.mask_toggle_button.setChecked(True)
        self.mask_toggle_button.setStyleSheet(
            "font-size: 16px; color: #000000; padding: 10px 20px; margin-bottom: 10px; background-color: #F5F5F5; border: 1px solid #CCCCCC; border-radius: 5px;")
        self.mask_toggle_button.clicked.connect(self.toggle_mask)
        tools_layout.addWidget(self.mask_toggle_button)

        self.draw_toggle_button = QPushButton("Drawing: ON")
        self.draw_toggle_button.setCheckable(True)
        self.draw_toggle_button.setChecked(True)
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

        self.restore_button = QPushButton("Undo")
        self.restore_button.clicked.connect(self.restore_cell)
        self.restore_button.setStyleSheet("""
            QPushButton:disabled {
                background-color: lightgray;
                color: gray;
                border: 1px solid darkgray;
            }
            QPushButton:enabled {
                border: 1px solid darkgray;
                color: #000000
            }
        """)
        self.restore_button.setEnabled(False)
        tools_layout.addWidget(self.restore_button)

        self.redo_button = QPushButton("Redo")
        self.redo_button.clicked.connect(self.redo_delete)
        self.redo_button.setStyleSheet("""
            QPushButton:disabled {
                background-color: lightgray;
                color: gray;
                border: 1px solid darkgray;
            }
            QPushButton:enabled {
                border: 1px solid darkgray;
                color: #000000
            }
        """)
        self.redo_button.setEnabled(False)
        tools_layout.addWidget(self.redo_button)

        self.tools_widget.setLayout(tools_layout)
        self.tools_widget.setStyleSheet(
            "background-color: #FAFAFA; border-left: 2px solid #E0E0E0;")  #Subtle border and clean background
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

    def set_queue_image(self, mask_color, outline_color, opacity, bf_channel, mask_paths, image_id, adjusted_image_path, conn,
                        mask_path, channel_id, channel_prefix):
        """
        Sets the current selected mask and image into the MyQtWindow, replacing the canvas with the current parameters.
        Also updates the window title to include the image_id.

        Arguments:
            mask_color: The color to use for the mask
            outline_color: The color to use for the outline
            opacity: The opacity of the mask
            bf_channel: The current bf channel
            mask_paths: The paths to each masks
            image_id: The id of the current selected image
            adjusted_image_path: The path to the adjusted image, which is the current image with the current adjustments like brightness and contrast adjustments
            conn: The pipeline connection to the Flet window to communicate with the main window
            mask_path: The path to the current selected mask
            channel_id: The id of the current selected channel
            channel_prefix: The prefix of the channel
        """
        #Update the window title with the current image's ID and channel ID.
        self.setWindowTitle(f"Mask Editing - {image_id}{channel_prefix}{channel_id}")

        #if canvas is only a dummy create a new_canvas
        if self.canvas_dummy:
            new_canvas = DrawingCanvas(mask_color, outline_color, opacity, bf_channel, mask_paths, image_id, adjusted_image_path,
                                       self.check_shifting, conn, mask_path, True, False,mask_show=self.mask_toggle_button.isChecked())
        else:
            #check if the current image_id and bf_channel equal to the values in canvas than only update the background image (adjusted_image)
            if image_id == self.canvas.image_id and bf_channel == self.canvas.bf_channel:
                if opacity == self.canvas.opacity:
                    self.canvas.adjusted_image_path = adjusted_image_path
                    self.canvas.load_image_to_scene()
                else:
                    self.canvas.opacity = opacity
                    self.canvas.adjusted_image_path = adjusted_image_path
                    self.canvas.load_image_to_scene()
                    self.canvas.load_mask_to_scene()
                return  #return because no new canvas, so no need for replacing the old canvas with the new and update the connections
            else:
                #new mask and image so need for new_canvas
                new_canvas = DrawingCanvas(mask_color, outline_color, opacity, bf_channel, mask_paths, image_id,
                                           adjusted_image_path,
                                           self.check_shifting, conn, mask_path, self.canvas.draw_mode,
                                           self.canvas.delete_mode,mask_show=self.mask_toggle_button.isChecked())

        #replace the old canvas with the new one and update the window
        self.restore_button.setEnabled(False)
        self.redo_button.setEnabled(False)
        self.canvas_dummy = False
        self.main_layout.replaceWidget(self.canvas, new_canvas)
        self.canvas.deleteLater()
        self.canvas = new_canvas
        self.canvas.update()
        self.main_layout.update()
        #Connect signals to update the state of the restore and redo buttons.
        self.canvas.restoreAvailabilityChanged.connect(lambda available: self.restore_button.setEnabled(available))
        self.canvas.redoAvailabilityChanged.connect(lambda available: self.redo_button.setEnabled(available))

        QTimer.singleShot(0, lambda: self.canvas.fitInView(self.canvas.sceneRect(), Qt.KeepAspectRatio)) #sets the right aspect ratio to the canvas

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

    def toggle_mask(self):
        """
        Toggles if the mask is shown or not.
        """
        if not self.canvas_dummy:
            if self.mask_toggle_button.isChecked():
                self.mask_toggle_button.setText("Mask : ON")
                self.canvas.mask_item.setVisible(True)
                self.canvas.mask_show = True
            else:
                self.mask_toggle_button.setText("Mask : OFF")
                self.canvas.mask_item.setVisible(False)
                self.canvas.mask_show = False

    def resizeEvent(self, event):
        self.canvas.fitInView(self.canvas.sceneRect(), Qt.KeepAspectRatio)


class Updater(QObject):
    """
    Handles the signals that come from the queue.
    """
    update_signal = pyqtSignal(object, object)  #Signal for new main_image
    close_signal = pyqtSignal(object, object)  #Signal to close the drawing window
    delete_signal = pyqtSignal(object, )  #Signal that the main_image mask got deleted
    refresh_signal = pyqtSignal()  #Signal that the main_image mask got deleted
    color_change_signal = pyqtSignal(object, object) #Signal that the colors got changed

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
        mask_color, outline_color, opacity, bf_channel, mask_paths, image_id, adjusted_image_path, mask_path, channel_id, channel_prefix = data
        self.window.set_queue_image(mask_color, outline_color, opacity, bf_channel, mask_paths, image_id, adjusted_image_path,
                                    conn, mask_path, channel_id, channel_prefix)
        self.window.setVisible(True)
        self.window.raise_()
        self.window.activateWindow()

    def handle_close(self, app, running):
        """
        If the close signal is received, close the process.
        """
        self.window.hide()
        running[0] = False
        app.quit()

    def handle_delete(self, app):
        """
        If the delete signal is received, closes the process, but lets it restart invisible.
        """
        self.window.hide()
        app.quit()

    def handle_refresh(self):
        """
        If the refresh signal is received, refreshes the mask in canvas from disc.
        """
        if not self.window.canvas_dummy:
            self.window.canvas.store_mask_and_update()

    def update_color(self, mask_color, outline_color):
        """
        If the color change signal is received, update the color of mask and outline.
        """
        if not self.window.canvas_dummy:
            self.window.canvas.mask_color = mask_color
            self.window.canvas.outline_color = outline_color
            self.window.canvas.load_mask_to_scene()

def open_qt_window(queue, conn):
    """
    Opens the Qt window invisibly and updates it based on signals received through the queue (e.g., close, update, color change, refresh).

    Arguments:
        queue: The connection to the main application, which sends information to the Qt window.
            - mask_color, outline_color, bf_channel, mask_paths, image_id, adjusted_image_path, mask_path, channel_id, channel_prefix: Makes the window visible or updates the canvas image if already visible.
            - "close": Closes the Qt window.
            - "delete_mask": Closes the Qt window, because the mask got deleted.
            - "refresh_mask": Refreshes the current mask from disk.
            - "color_change", mask_color, outline_color: Changes the mask and outline color.
        conn: A communication pipeline to the main application for sending information to the main window.
            - "update_mask": Updates the current mask from disk in the main window.
            - "close": Closes the pipeline listener on the main window side.
    """
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
                    elif data == "delete_mask":
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
        app.exec_()
        if running[0]:
            queue.put("close_thread")
        if thread is not None and thread.is_alive():
            thread.join()
        window.close()
        window.deleteLater()
    conn.send("close")
    sys.exit(0)


class DrawingCanvas(QGraphicsView):
    """
    Class for displaying and interacting with images (background, mask).
    Includes delete functionality for cells and supports undo (restore) and redo of cell deletion.
    """
    #Signals to indicate whether a restore or redo action is available.
    restoreAvailabilityChanged = pyqtSignal(bool)
    redoAvailabilityChanged = pyqtSignal(bool)

    def __init__(self, mask_color, outline_color,opacity, bf_channel, mask_paths, image_id, adjusted_image_path, check_box,
                 conn, mask_path, draw_mode=True, delete_mode=False,mask_show=True):
        super().__init__()

        self.mask_color = mask_color
        self.outline_color = outline_color
        self.opacity = opacity
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
        self.cell_history = []  #Each entry: (old_state, new_state)
        self.redo_history = []  #Each entry: (old_state, new_state)
        self.check_box = check_box
        self.points = []  #saves all points in the drawing
        self.conn = conn
        self.mask_show = mask_show
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
            return False  #No image loaded
        x, y = int(point.x()), int(point.y())
        return 0 <= x < self.image_array.shape[1] and 0 <= y < self.image_array.shape[0]

    def mousePressEvent(self, event):
        """
        Handle mouse click events for drawing or deleting cells.
        """
        if self.draw_mode:
            if event.button() == Qt.LeftButton:
                current_point = self.mapToScene(event.pos())
                if not self.is_point_within_image(current_point):
                    x,y = self.clamp_to_image_bounds(current_point)
                    current_point = QPointF(x, y)

                self.drawing = True
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
        """
        What happens, if you move the clicked mouse
        """
        if self.draw_mode:
            current_point = self.mapToScene(event.pos())

            if self.is_point_within_image(current_point):
                x, y = int(current_point.x()), int(current_point.y())
            else:
                x, y = self.clamp_to_image_bounds(current_point)

            if self.last_point:
                line_item = QGraphicsLineItem(self.last_point.x(), self.last_point.y(), x, y)
                r, g, b = self.outline_color
                pen = QPen(QColor(r, g, b), 2, Qt.SolidLine)
                line_item.setPen(pen)
                self.scene.addItem(line_item)

            self.last_point = QPointF(x, y)

    def clamp_to_image_bounds(self, point):
        """
        If mouse goes out of image, the line stays in the image bounds.
        """
        x, y = int(point.x()), int(point.y())
        x = max(0, min(x, self.image_array.shape[1] - 1))
        y = max(0, min(y, self.image_array.shape[0] - 1))

        return x, y

    def mouseReleaseEvent(self, event):
        """
        If you release the left click.
        """
        if self.draw_mode and self.drawing:
            self.drawing = False

            # connect last and first point in pic
            if self.start_point and self.last_point:
                first_inside = self.clamp_to_image_bounds(self.start_point)
                last_inside = self.clamp_to_image_bounds(self.last_point)

                line_item = QGraphicsLineItem(first_inside[0], first_inside[1],
                                              last_inside[0], last_inside[1])
                r, g, b = self.outline_color
                pen = QPen(QColor(r, g, b), 2, Qt.SolidLine)
                line_item.setPen(pen)
                self.scene.addItem(line_item)
            self.start_point = None
            self.last_point = None

            self.update()
            self.add_drawn_cell()
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

    def store_mask_and_update(self):
        mask = self.mask_data["masks"]
        outline = self.mask_data["outlines"]

        #Save current state of the cell for restoration (undo)
        mask_old = mask.copy()
        outline_old = outline.copy()
        self.load_mask_to_scene()
        mask = self.mask_data["masks"]
        outline = self.mask_data["outlines"]

        # Save current state of the cell for restoration (undo)
        new_mask = mask.copy()
        new_outline = outline.copy()
        self.cell_history.append(((mask_old, outline_old), (new_mask, new_outline)))

        self.restoreAvailabilityChanged.emit(len(self.cell_history) > 0)
        self.redoAvailabilityChanged.emit(len(self.redo_history) > 0)

    def delete_cell(self, cell_id):
        """
        Delete the specified cell by updating the mask data.
        Also does not clear stored redo history, enabling multiple redo levels.
        """
        mask_path = self.mask_paths[self.image_id][self.bf_channel]
        self.mask_data = np.load(mask_path, allow_pickle=True).item()

        mask = self.mask_data["masks"]
        outline = self.mask_data["outlines"]

        #Save current complete state before deletion
        old_state = (mask.copy(), outline.copy())

        #Update the mask and outline (delete the cell)
        cell_mask = (mask == cell_id).copy()
        cell_outline = (outline == cell_id).copy()
        mask[cell_mask] = 0
        outline[cell_outline] = 0
        if self.check_box.isChecked():
            mask_shifting(self.mask_data, cell_id)
        #Save new state after deletion
        np.save(mask_path, {"masks": mask, "outlines": outline}, allow_pickle=True)
        new_state = (mask.copy(), outline.copy())

        self.load_mask_to_scene()
        self.conn.send("update_mask")

        #Save the state transition in undo history
        self.cell_history.append((old_state, new_state))
        self.restoreAvailabilityChanged.emit(len(self.cell_history) > 0)
        self.redoAvailabilityChanged.emit(len(self.redo_history) > 0)

    def restore_cell(self):
        """
        Restore the most recent state (undo the deletion or drawing).
        Also stores the undone action in a redo history so that the change can be re-applied.
        """
        if not self.cell_history:
            #No state to restore; update button state via signal and do nothing.
            self.restoreAvailabilityChanged.emit(False)
            return

        mask_path = self.mask_paths[self.image_id][self.bf_channel]
        #Retrieve the last state transition from undo history
        old_state, new_state = self.cell_history.pop()

        #Restore the old state (undo)
        np.save(mask_path, {"masks": old_state[0], "outlines": old_state[1]}, allow_pickle=True)
        self.load_mask_to_scene()
        self.conn.send("update_mask")

        #Save the undone action in redo history
        self.redo_history.append((old_state, new_state))
        self.restoreAvailabilityChanged.emit(len(self.cell_history) > 0)
        self.redoAvailabilityChanged.emit(len(self.redo_history) > 0)

    def redo_delete(self):
        """
        Re-apply the deletion (redo the undone deletion or drawing).
        """
        if not self.redo_history:
            self.redoAvailabilityChanged.emit(False)
            return
        mask_path = self.mask_paths[self.image_id][self.bf_channel]
        #Retrieve the state transition from redo history
        old_state, new_state = self.redo_history.pop()

        #Redo: restore the new state
        np.save(mask_path, {"masks": new_state[0], "outlines": new_state[1]}, allow_pickle=True)
        self.load_mask_to_scene()
        self.conn.send("update_mask")

        #After redoing, push it back to undo history
        self.cell_history.append((old_state, new_state))
        self.restoreAvailabilityChanged.emit(len(self.cell_history) > 0)
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
            self.conn.send(f"new_mask.{self.image_id}")
            self.mask_paths[self.image_id][self.bf_channel] = self.mask_path

        mask_path = self.mask_paths[self.image_id][self.bf_channel]

        self.mask_data = np.load(mask_path, allow_pickle=True).item()

        mask = self.mask_data["masks"]
        outline = self.mask_data["outlines"]
        #Create RGBA mask
        image_mask = np.zeros((mask.shape[0], mask.shape[1], 4), dtype=np.uint8)
        r, g, b = self.mask_color
        image_mask[mask != 0] = (r, g, b, self.opacity)
        r, g, b = self.outline_color
        image_mask[outline != 0] = (r, g, b, 255)
        self.image_array = mask

        #Update mask item in the scene
        height, width, _ = image_mask.shape
        qimage = QImage(image_mask.data, width, height, QImage.Format_RGBA8888)
        pixmap = QPixmap.fromImage(qimage)
        if self.mask_item:
            self.scene.removeItem(self.mask_item)
        self.mask_item = self.scene.addPixmap(pixmap)
        self.mask_item.setTransformationMode(Qt.SmoothTransformation)
        self.mask_item.setZValue(1)
        self.mask_item.setVisible(self.mask_show)

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

    def add_drawn_cell(self):
        """
        Adds the new drawn cell to the mask.npy based on current LineItems and updates the scene with the new mask.
        """
        #gets the pixels that build the lines of the drawn cell
        line_pixels = set()
        for item in self.scene.items():
            if isinstance(item, QGraphicsLineItem):
                line = item.line()
                pixels = bresenham_line(line.p1(), line.p2()) #Calculates the pixels along the line
                line_pixels.update(pixels)

        #get the current mask and outline npy arrays
        mask_path = self.mask_paths[self.image_id][self.bf_channel]
        self.mask_data = np.load(mask_path, allow_pickle=True).item()
        mask = self.mask_data["masks"]
        outline = self.mask_data["outlines"]

        #Save current state before drawing for undo
        old_state = (mask.copy(), outline.copy())

        free_id = search_free_id(mask, outline)  #search for the next free id in mask and outline

        #add the outline of the new mask (only the parts which not overlap with already existing cells) to outline npy array and fill the complete outline to new_cell_outline to calculate inner pixels
        new_cell_outline = np.zeros_like(outline, dtype=np.uint8)
        for x, y in line_pixels:
            if 0 <= x < outline.shape[1] and 0 <= y < outline.shape[0]:
                new_cell_outline[y, x] = 1
                if outline[y, x] == 0 and mask[y, x] == 0:
                    outline[y, x] = free_id

        #Traces the outline of the new cell and fills the mask based on the outline
        contour = trace_contour(new_cell_outline)
        new_mask = fill_polygon_from_outline(contour, mask.shape) #gets the inner pixels of the new cell
        mask[(new_mask == 1) &(mask == 0) & (outline == 0)] = free_id #adds them to the npy if they not overlap with the already existing cells

        #search if inline pixels (mask) have no outline, if the pixel have no outline neighbor make them to outline and delete them from mask
        new_border_pixels = find_border_pixels(mask,outline,free_id)
        for y, x in new_border_pixels:
            if 0 <= x < outline.shape[1] and 0 <= y < outline.shape[0]:
                mask[y, x] = 0
                outline[y, x] = free_id

        #Save new state after drawing
        np.save(mask_path, {"masks": mask, "outlines": outline}, allow_pickle=True)
        new_state = (mask.copy(), outline.copy())
        self.load_mask_to_scene()
        self.conn.send("update_mask")
        #Save the state transition in undo history
        self.cell_history.append((old_state, new_state))
        self.restoreAvailabilityChanged.emit(len(self.cell_history) > 0)
        self.redoAvailabilityChanged.emit(len(self.redo_history) > 0)
        #Delete the LineItems (the lines that the user have drawn), because the cell now exists through the mask
        for item in list(self.scene.items()):
            if isinstance(item, QGraphicsLineItem):
                self.scene.removeItem(item)
