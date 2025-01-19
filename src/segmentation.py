from src.images import BatchImageSegmentation
from src.notifier import Notifier


class Segmentation(Notifier):

    def __init__(self, gui_seg, gui):
        super().__init__()

        self.gui = gui
        self.gui_seg = gui_seg
        self.lif_value= gui.directory.is_lif
        device = "cpu"
        self.batch_image_segmentation = BatchImageSegmentation(self,
                                                               self.gui,
                                                               device)

    def to_be_cancelled(self):
        self.batch_image_segmentation.cancel_action()
        #self.csp.segmentation_running = False

    def to_be_paused(self):
        self.batch_image_segmentation.pause_action()
        #self.csp.segmentation_running = False

    def to_be_resumed(self):
        self.batch_image_segmentation.resume_action()
        #self.csp.segmentation_running = True

    def is_cancelled(self):
        self._call_cancel_listeners()

    def is_paused(self):
        pass

    def is_resumed(self):
        pass # weiß nicht, ob die notwendig ist

    def run(self):
        self._call_update_listeners("Preparing segmentation", None)

        if self.gui.csp.segmentation_running:
            self._call_completion_listeners()
            return

        def finished():
            self._call_completion_listeners()

        def update(update,current_image):
            self._call_update_listeners(update, current_image)

        def start():
            self._call_update_listeners("0 %", None)

        self.gui.csp.segmentation_running = True

        self.batch_image_segmentation.add_start_listener(listener=start)
        self.batch_image_segmentation.add_update_listener(listener=update)
        self.batch_image_segmentation.add_cancel_listener(listener=self.is_cancelled)
        self.batch_image_segmentation.add_pause_listener(listener=self.is_paused)
        self.batch_image_segmentation.add_resume_listener(listener=self.is_resumed)
        self.batch_image_segmentation.add_completion_listener(listener=finished)

        self.batch_image_segmentation.run_parallel() if not self.lif_value else self.batch_image_segmentation.run()
        self.gui.csp.segmentation_running = False
        if self.gui_seg.segmentation_cancelling:
            self._call_cancel_listeners()
            return
        else:
            self._call_completion_listeners()


    def stop(self):
        self.gui.csp.segmentation_running = False



