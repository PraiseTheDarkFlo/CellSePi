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
        self.bright_field_channel = gui.csp.config.get_bf_channel()
        self.diameter = gui.csp.config.get_diameter()
        self.segmentation_running = False

    def run(self):
        print("run segmentation")
        self._call_update_listeners("Preparing segmentation")

        if self.segmentation_running == True:
            print("Segmentation already running")
            self._call_completion_listeners()
            return

        def update(update):
            self._call_update_listeners(update.get("progress"))
            pass

        def finished(mask_paths, args):
            self.csp.mask_paths = mask_paths
            self._call_completion_listeners()
            pass

        self.segmentation_running = True
        segmentation_channel = self.bright_field_channel
        diameter = self.diameter
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
#Todo segmentation GUI:

    # modell muss ausgewählt werden -> modell in CellSePi.model abspeichern
    # button um segmentation zu starten
    # dann erscheint progress bar, welche wärenddessen aktualisiert wird
    # und button zum abbrechen der berechnung
    # wenn berechnung fertig ist...


    #Todo segmentation

    # holt model von cellSePi
    # starte segmentation + batchImageSegmentation
    # wärenddessen muss notified werden mit dem progress, d.h. wie viele bilder schon bearbeitet wurden
    # wenn fertig ist muss notifien


