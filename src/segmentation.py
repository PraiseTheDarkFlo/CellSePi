from src.images import BatchImageSegmentation
from src.notifier import Notifier


class Segmentation(Notifier):

    def __init__(self, gui):
        super().__init__()

        self.csp = gui.csp
        self.lif_value= gui.directory.is_lif
        self.csp.segmentation_running = False
        device = "cpu"
        self.batch_image_segmentation = BatchImageSegmentation(self,
                                                               self.csp,
                                                               device)

    def to_be_cancelled(self):
        self.batch_image_segmentation.cancel_action()
        self.csp.segmentation_running = False

    def to_be_paused(self):
        self.batch_image_segmentation.pause_action()

    def to_be_resumed(self):
        self.batch_image_segmentation.resume_action()

    def is_cancelled(self, *args, **kwargs):
        pass

    def is_paused(self, *args, **kwargs):
        pass

    def is_resumed(self, *args, **kwargs):
        pass # weiß nicht, ob die notwendig ist

    def run(self):
        print("run segmentation")
        self._call_update_listeners("Preparing segmentation", None)

        if self.csp.segmentation_running:
            print("Segmentation already running")
            self._call_completion_listeners()
            return

        def finished(mask_paths):
            self._call_completion_listeners()

        def update(update,current_image):
            self._call_update_listeners(update, current_image)
            print(update)

        def start():
            self._call_update_listeners("0 %", None)



        self.csp.segmentation_running = True

        self.batch_image_segmentation.add_start_listener(listener=start)
        self.batch_image_segmentation.add_update_listener(listener=update)
        self.batch_image_segmentation.add_cancel_listener(listener=self.is_cancelled)
        self.batch_image_segmentation.add_pause_listener(listener=self.is_paused)
        self.batch_image_segmentation.add_completion_listener(listener=finished)


        self.batch_image_segmentation.run_parallel() if not self.lif_value else self.batch_image_segmentation.run()
        self._call_completion_listeners()
        self.csp.segmentation_running = False


    def stop(self):
        self.csp.segmentation_running = False



