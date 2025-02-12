import images
import threading
import flet as ft
from src.notifier import Notifier
from .GUI.gui_fluorescence import error_banner,fluorescence_button

class Fluorescence(Notifier):
    """
    class handles the readout of fluorescence values

    Attributes:
        csp= current CellSePi object
        gui= current gui object
    """
    def __init__(self, CellSePi,GUI):
        super().__init__()
        self.csp= CellSePi
        self.gui=GUI


    def readout_fluorescence(self):
        """
        starts the readout of fluorescence and creates an Excel list if possible

        """

        if self.check_readout_possible():
            self._call_start_listeners(True)
            def on_update(progress,current_image):
                print(f"{progress}% is progressed")
                self._call_update_listeners(progress, current_image)

            def completed_readout(readout, readout_path):
                print("fluorescence values readout")
                self.csp.readout= readout
                self.csp.readout_path=readout_path
                self.csp.readout_running=False
                if readout_path is not None:
                    self.gui.open_button.visible=True
                self.gui.page.run_task(self.gui.directory.check_masks)
                fluorescence_button.disabled = False
                if self.csp.model_path is not None:
                    self.gui.start_button.disabled =False
                print(f"values are stored in {readout_path}")
                self._call_completion_listeners()

            print("Preparing readout")
            self.csp.readout_running=True
            fluorescence_button.disabled=True

            brightfield_channel = self.csp.config.get_bf_channel()
            prefix = self.csp.config.get_channel_prefix()
            working_directory = self.csp.working_directory

            #creates the readout image and fills the mask_path
            print(self.csp.mask_paths)
            batch_image_readout = images.BatchImageReadout(image_paths=self.csp.image_paths,
                                                          mask_paths=self.csp.mask_paths,
                                                          segmentation_channel=brightfield_channel,
                                                          channel_prefix=prefix,
                                                          directory=working_directory)
            batch_image_readout.add_update_listener(listener=on_update)
            batch_image_readout.add_completion_listener(listener=completed_readout)

            target = batch_image_readout.run
            self.csp.readout_thread = threading.Thread(target=target)

            print("starting readout")
            self._call_start_listeners(False)
            self.csp.readout_thread.start()


        else:
            self._call_start_listeners(False)
            return


    def check_readout_possible(self):
        """
         -error handling. All error that can possibly occur
         -creates a banner visible in the GUI if an error is important
        """

        if self.csp.readout_running:
            error_banner(self.gui,"Readout already started")
            return False,
        if self.csp.readout_thread is not None and self.csp.readout_thread.is_alive():
            print("Already occupied")
            return False
        if self.csp.image_paths is None or len(self.csp.image_paths) ==0 :
            error_banner(self.gui, "No image to process")
            return False

        return True


