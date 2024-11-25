from click.core import batch

import images as image
import threading
from src.CellSePi import CellSePi
import flet as ft
import os.path
from notifier import Notifier
from src.images import BatchImageSegmentation


class segmentation(Notifier):

    def __init__(self, gui):
        super().__init__()
        self.csp = gui.csp
        self.config = gui.config
        self.segmentation_running = False

    def run(self):
        print("run segmentation")
        self._call_update_listeners("Preparing segmentation")

        if self.segmentation_running == True:
            print("Segmentation already running")
            self._call_completion_listeners()
            return

        def finished(mask_paths, args):
            self.csp.mask_paths = mask_paths
            self._call_completion_listeners()
            pass

        def update(update):
            self._call_update_listeners(update.get("progress"))
            pass

        self.segmentation_running = True
        segmentation_channel = self.config.get_bf_channel()
        diameter = self.config.get_diameter()
        device = "cpu"

        batch_image_segmentation = BatchImageSegmentation(self.csp.image_paths,
                                                          segmentation_channel,
                                                          diameter,
                                                          device,
                                                          self.csp.model_path)
        batch_image_segmentation.add_update_listener(listener=update)
        batch_image_segmentation.add_completion_listener(listener=finished)
        batch_image_segmentation.run()
        self._call_completion_listeners()

    def stop(self):
        print("stop")
        pass



