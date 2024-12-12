from click.core import batch
from torch.fx.experimental.migrate_gradual_types.constraint_generator import batchnorm_inference_rule

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
        self.config = gui.csp.config
        self.segmentation_running = False
        segmentation_channel = self.config.get_bf_channel()
        diameter = self.config.get_diameter()
        suffix = self.config.get_mask_suffix()
        device = "cpu"
        self.batch_image_segmentation = BatchImageSegmentation(segmentation_channel,
                                                               self,
                                                               self.csp,
                                                               diameter,
                                                               device,
                                                               self.csp.model_path,
                                                               suffix)

    def to_be_cancelled(self):
        self.batch_image_segmentation.cancel_action()
        self.segmentation_running = False

    def to_be_paused(self):
        self.batch_image_segmentation.pause_action()

    def to_be_resumed(self):
        self.batch_image_segmentation.resume_action()

    def is_cancelled(self):
        pass

    def is_paused(self):
        pass

    def is_resumed(self):
        pass # weiß nicht, ob die notwendig ist

    def run(self):
        print("run segmentation")
        self._call_update_listeners("Preparing segmentation", None)

        if self.segmentation_running:
            print("Segmentation already running")
            self._call_completion_listeners()
            return

        def finished(mask_paths):
            self.csp.mask_paths = mask_paths
            self._call_completion_listeners()

        def update(update,current_image):
            self._call_update_listeners(update, current_image)
            print(update)

        def start():
            self._call_update_listeners("0 %", None)



        self.segmentation_running = True

        self.batch_image_segmentation.add_start_listener(listener=start)
        self.batch_image_segmentation.add_update_listener(listener=update)
        self.batch_image_segmentation.add_cancel_listener(listener=self.is_cancelled)
        self.batch_image_segmentation.add_stop_listener(listener=self.is_paused)
        self.batch_image_segmentation.add_completion_listener(listener=finished)

        self.batch_image_segmentation.run()
        self._call_completion_listeners()
        self.segmentation_running = False


    def stop(self):
        self.segmentation_running = False



