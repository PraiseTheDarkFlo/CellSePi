#create class
#listen to listener if segmentation is finished
#if segmentation is finished than option to readout fluoreszenz
#if clicked-> redout fluoreszenz then the data is readout
# if already started readout then no readout possible
# if readout finished output file is created (npy ?)
#save the file in output path

import images as image
import threading
from src.CellSePi import CellSePi
import flet as ft

class Fluorescence:
    def __init__(self):
        self.csp= CellSePi()
        self.fluorescence_button= ft.ElevatedButton(text= "Readout fluorescence",
                                                    icon=ft.icons.PLAY_CIRCLE,
                                                    disabled=True,
                                                    on_click=lambda _: ft.FilePicker().pick_files(allow_multiple=False),
                                                    visible=False)


    def readout_fluorescence(self):
        if self.check_readout_possible():
            def on_update(progress):
                print(f"{progress}% is progressed")
                #nikes progressbar update methode
            def completed_readout(readout, readout_path):
                print("fluorescence values readout")
                self.csp.readout= readout
                self.csp.readout_path=readout_path
                self.csp.readout_running=False
                self.fluorescence_button.disabled =False #hier den fluorescence button auf normal setzen
                print(f"values are stored in {readout_path}")

            print("Preparing readout")
            self.csp.readout_running=True
            self.fluorescence_button.disabled=True #button auf disabled setzen

            brightfield_channel = self.csp.config.get_bf_channel()
            prefix = self.csp.config.get_channel_prefix()
            working_directory = self.csp.working_directory

            batch_image_readout = image.BatchImageReadout(image_paths=self.csp.image_paths,
                                                          mask_paths=self.csp.mask_paths,
                                                          segmentation_channel=brightfield_channel,
                                                          channel_prefix=prefix,
                                                          directory=working_directory)
            batch_image_readout.add_update_listener(listener=on_update)
            batch_image_readout.add_completion_listener(listener=completed_readout)

            target = batch_image_readout.run
            self.csp.readout_thread = threading.Thread(target=target)

            print("starting readout")
            self.csp.readout_thread.start()


        else:
            print("Readout not possible. Try later")
            return

    def check_readout_possible(self):
        if self.csp.readout_running:
            print("Readout is already running")
            return False
        if self.csp.readout_thread is not None and self.csp.readout_thread.is_alive():
            print("Already occupied")
            return False
        if self.csp.image_paths is None or len(self.csp.images) ==0 :
            print("No image to process")
            return False
        return True






