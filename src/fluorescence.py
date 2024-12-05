#create class
#listen to listener if segmentation is finished
#if segmentation is finished than option to readout fluoreszenz
#if clicked-> redout fluoreszenz then the data is readout
# if already started readout then no readout possible
# if readout finished output file is created (npy ?)
#save the file in output path

#TODO: wenn execl-Datei vorhanden, kommt folgender Fehler: permission dinied

import images as image
import threading
from src.CellSePi import CellSePi
import flet as ft
from notifier import Notifier

# REVIEW Conclusion: wir sollten uns überlegen, ob alle Funktionalität vom Button in gui_segmentation gelegt werden soll,
# weil ein button halt zur GUI gehört, aber er gehört natürlich auch zur fluoreszenz (frage nach höherer cohesion).
# Wenn man den button in gui_segmentation verlagert muss nur noch zusätzlich ein listener hinzugefügt werden. Ansonsten
# müssen wir uns noch einigen, wie wir Kommentare handhaben wollen, damit wir es auch einheitlich machen (aber so hast du eigentlich genug Kommentare).

#the class readout the fluorescence values of the segmented cells
class Fluorescence(Notifier):
    def __init__(self, CellSePi):
        super().__init__()
        self.csp= CellSePi
        self.fluorescence_button= ft.ElevatedButton(text= "Readout Fluorescence",
                                                    icon=ft.icons.FILE_DOWNLOAD,
                                                    disabled=False,
                                                    visible=True)
#REVIEW: vielleicht sollten wir den button lieber in gui_segmentation tun -> bessere "cohesion"

#method handling the readout
    #if currently no readout is done-> the process is started and the file saved
    #else readout not possible -> error message occurs
    def readout_fluorescence(self):
        #REVIEW: hier noch einen aufruf von start_listeners hin, der mitbekommt, ob ein fehler geworfen wird (also False mitgeben) -> vielleicht wollen wir dann auch so einen Banner unten einfügen
        #        -> damit ich in gui_segmentation das mitbekomme
        if self.check_readout_possible():
            def on_update(progress,current_image):
                print(f"{progress}% is progressed")
                self._call_update_listeners(progress, current_image)

            def completed_readout(readout, readout_path):
                print("fluorescence values readout")
                self.csp.readout= readout
                self.csp.readout_path=readout_path
                self.csp.readout_running=False
                self.fluorescence_button.disabled =False #hier den fluorescence button auf normal setzen
                print(f"values are stored in {readout_path}")
                self._call_completion_listeners()

            print("Preparing readout")
            self.csp.readout_running=True
            # REVIEW: hier könnte man einen start_listener aufrufen mit True, dass die fluorezenz-berechnung gestartet wurde
            self.fluorescence_button.disabled=True #button auf disabled setzen

            brightfield_channel = self.csp.config.get_bf_channel()
            prefix = self.csp.config.get_channel_prefix()
            working_directory = self.csp.working_directory

            #creates the readout image and fills the mask_path
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
            print("Readout not possible. Try later") #REVIEW: s. unten zur fehlerbehandlung
            # REVIEW: hier könnte man start_listener mit false aufrufen
            return

    #error handling. All error that can possibly occur
    # REVIEW: banner (snackbar) unten anzeigen, wenn fehler auftritt (so wie Flo oder wir einigen uns auf ein Aussehen, damit es einheitlich ist)
    # REVIEW: kann diese fehler teilweise auch kontrollieren, indem der "readout fluoreszenz" button nur clickable ist, wenn folgende Bedingungen gegeben sind
    #           -> nur eine Überlegung, ich weiß nicht was besser ist bzw, ob man beides machen möchte für bessere Absicherung
    def check_readout_possible(self):
        if self.csp.readout_running:
            print("Readout is already running")
            return False
        if self.csp.readout_thread is not None and self.csp.readout_thread.is_alive():
            print("Already occupied")
            return False
        if self.csp.image_paths is None or len(self.csp.image_paths) ==0 :
            print("No image to process")
            return False
        return True


