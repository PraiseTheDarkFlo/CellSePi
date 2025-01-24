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

    def is_resuming(self):
        self._call_resume_listeners()

    def run(self):
        self._call_update_listeners("Preparing segmentation", None)

        if self.gui.csp.segmentation_running:
            self._call_completion_listeners()
            return

        def finished():
            self._call_completion_listeners()

        def update(progress, current_image):
            self._call_update_listeners(progress, current_image)

        def start():
            print("start num seg images: ", self.batch_image_segmentation.num_seg_images)
            current_percentage = round(self.batch_image_segmentation.num_seg_images / len(self.gui.csp.image_paths) * 100)
            print("current percentage: ", current_percentage)
            self._call_update_listeners(str(current_percentage) + " %", None)

        self.gui.csp.segmentation_running = True

        self.batch_image_segmentation.add_start_listener(listener=start)
        self.batch_image_segmentation.add_update_listener(listener=update)
        self.batch_image_segmentation.add_completion_listener(listener=finished)

        self.batch_image_segmentation.run_parallel() if not self.lif_value else self.batch_image_segmentation.run()
        self.gui.csp.segmentation_running = False
        if self.gui_seg.segmentation_cancelling:
            self._call_cancel_listeners()
            return
        elif self.gui_seg.segmentation_pausing:
            self._call_pause_listeners()
            return
        else:
            self._call_completion_listeners()


    def stop(self):
        self.gui.csp.segmentation_running = False



