import pathlib
import platform
import numpy as np
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtWidgets import QApplication, QLabel, QVBoxLayout, QHBoxLayout, QPushButton, QWidget, QGraphicsScene, QGraphicsView, QMainWindow
import sys
from ...CellSePi import CellSePi
import copy


class MyQtWindow(QMainWindow):
    """
    Main PyQt window for drawing tools and deleting cells.

    Attributes:
        csp: Current CellSePi instance to access images and masks.
        canvas: DrawingCanvas object for displaying and interacting with the mask.
        tools_widget: Container for tools on the right side.
    """
    def __init__(self, csp: CellSePi):
        super().__init__()
        self.csp = csp
        self.setWindowTitle("Drawing & Mask Editing")

        self.canvas = DrawingCanvas(self.csp)

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

        # Add buttons to the tools box
        self.delete_toggle_button = QPushButton("Delete Mode: OFF")
        self.delete_toggle_button.setCheckable(True)
        self.delete_toggle_button.setStyleSheet("font-size: 16px; padding: 10px 20px; margin-bottom: 10px; background-color: #F5F5F5; border: 1px solid #CCCCCC; border-radius: 5px;")
        self.delete_toggle_button.clicked.connect(self.toggle_delete_mode)
        tools_layout.addWidget(self.delete_toggle_button)

        self.restore_button = QPushButton("Restore Deleted Cell")
        self.restore_button.setStyleSheet("font-size: 16px; padding: 10px 20px; background-color: #F5F5F5; border: 1px solid #CCCCCC; border-radius: 5px;")
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


# Start the window of the drawing tools
def open_qt_window(csp: CellSePi):
    app = QApplication(sys.argv)
    window = MyQtWindow(csp)
    window.show()
    app.exec()


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
    """

    def __init__(self, csp: CellSePi):
        super().__init__()
        self.csp = csp
        self.scene = QGraphicsScene(self)
        self.setScene(self.scene)

        self.delete_mode = False
        self.image_array = None
        self.mask_item = None
        self.background_item = None
        self.cell_history = []  # Track deleted cells for restoration

    def enable_delete_mode(self, enable):
        """
        Enable or disable delete mode.
        """
        self.delete_mode = enable
        print(f"Delete mode {'enabled' if self.delete_mode else 'disabled'}.")

    def mousePressEvent(self, event):
        """
        Handle mouse click events for deleting cells.
        """
        if self.delete_mode:
            pos = event.pos()
            scene_pos = self.mapToScene(pos)
            cell_id = self.get_cell_id_from_position(scene_pos)
            if cell_id:
                self.delete_cell(cell_id)
        else:
            super().mousePressEvent(event)

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
        mask_path = self.csp.mask_paths[self.csp.image_id][self.csp.config.get_bf_channel()]
        mask_data = np.load(mask_path, allow_pickle=True).item()

        mask = mask_data["masks"]
        outline = mask_data["outlines"]

        # Save current state of the cell for restoration
        cell_mask = (mask == cell_id).copy()
        cell_outline = (outline == cell_id).copy()
        self.cell_history.append((cell_id, cell_mask, cell_outline))

        # Update the mask and outline
        mask[cell_mask] = 0
        outline[cell_outline] = 0

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

        mask_path = self.csp.mask_paths[self.csp.image_id][self.csp.config.get_bf_channel()]
        mask_data = np.load(mask_path, allow_pickle=True).item()

        mask = mask_data["masks"]
        outline = mask_data["outlines"]

        # Restore the most recent cell
        cell_id, cell_mask, cell_outline = self.cell_history.pop()
        mask[cell_mask] = cell_id
        outline[cell_outline] = cell_id

        # Save the updated mask
        np.save(mask_path, {"masks": mask, "outlines": outline}, allow_pickle=True)
        print(f"Restored cell ID {cell_id}. Reloading mask...")
        self.load_mask_to_scene()

    def load_mask_to_scene(self):
        """
        Load the mask and display it on the scene.
        """
        mask_path = self.csp.mask_paths[self.csp.image_id][self.csp.config.get_bf_channel()]
        mask_data = np.load(mask_path, allow_pickle=True).item()

        mask = mask_data["masks"]
        outline = mask_data["outlines"]

        # Create RGBA mask
        image_mask = np.zeros((mask.shape[0], mask.shape[1], 4), dtype=np.uint8)
        image_mask[mask != 0] = (255, 0, 0, 128)
        image_mask[outline != 0] = (0, 255, 0, 255)
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
        if self.csp.adjusted_image_path:
            pixmap = QPixmap(self.csp.adjusted_image_path)
        else:
            pixmap = QPixmap(self.csp.image_paths[self.csp.image_id])

        if self.background_item:
            self.scene.removeItem(self.background_item)
        self.background_item = self.scene.addPixmap(pixmap)
        self.background_item.setZValue(-1)

        self.scene.setSceneRect(0, 0, pixmap.width(), pixmap.height())
        self.fitInView(self.sceneRect(), Qt.KeepAspectRatio)
