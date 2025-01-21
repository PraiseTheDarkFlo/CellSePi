import os
import re
import subprocess
import sys

import flet as ft
from . import GUI
from ..fluorescence import Fluorescence
from .gui_fluorescence import fluorescence_button
from ..segmentation import Segmentation

class GUISegmentation():

    def __init__(self, gui):
        self.gui = gui
        self.segmentation = Segmentation(self, gui)
        self.fluorescence = Fluorescence(gui.csp, gui)
        self.segmentation_cancelling = False
        self.segmentation_pausing = False

    def create_segmentation_card(self):
        """
        This method creates a segmentation card for the GUI, which contains the progress bar and several buttons for
         controlling the run of the segmentation.

        Returns:
            segmentation_card (ft.Card): the card containing all the elements needed to run the segmentation
        """
        # creating all the necessary buttons and their initial properties
        start_button = ft.ElevatedButton( # button to start the segmentation calculation
            text="Start",
            icon=ft.icons.PLAY_CIRCLE,
            tooltip="Start the segmentation",
            disabled=True,
            on_click=None
        )
        pause_button = ft.ElevatedButton( # button to pause the segmentation calculation while it is running
            text="Pause",
            icon=ft.icons.PAUSE_CIRCLE,
            visible=False,
            on_click=None,
        )
        cancel_button = ft.ElevatedButton( # button to completely cancel the currently running segmentation calculation
            text="Cancel",
            icon=ft.icons.CANCEL,
            visible=False,
            on_click=None,
            color=ft.Colors.RED
        )
        resume_button = ft.ElevatedButton( # button to resume the segmentation calculation after it has been paused
            text="Resume",
            icon=ft.icons.PLAY_CIRCLE,
            visible=False,
            on_click=None,
        )

        # button to start the fluorescence readout
        fl_button = fluorescence_button

        # progress bar, which is updated throughout the segmentation calculation and fluorescence readout
        progress_bar = ft.ProgressBar(value=0, width=180)
        progress_bar_text = ft.Text("Waiting for Input")

        def open_readout(e):
            file_path = self.gui.csp.readout_path
            if os.name == "nt":  # Check if Windows
                os.startfile(file_path)
            elif os.name == "posix":  # Check if Mac or Linux
                subprocess.run(["open", file_path] if sys.platform == "darwin" else ["xdg-open", file_path])

        open_button = ft.IconButton(
            icon=ft.icons.OPEN_IN_NEW_ROUNDED,
            tooltip = "Open fluorescence file",
            on_click=open_readout,
            visible= False
        )

        # the following methods are called when clicking on the corresponding button
        def pick_model_result(e: ft.FilePickerResultEvent):
            """
            The result of the file selection is handled.

            Arguments:
                e (ft.FilePickerResultEvent): the result of the file picker event, i.e. the chosen file
            """
            if e.files is None:
                print("no model selected")
            elif e.files[0].path is not None:
                if self.gui.ready_to_start:
                    progress_bar_text.value = "Ready to Start"
                    start_button.disabled = False
                model_text.title.value = e.files[0].name
                self.gui.csp.model_path = e.files[0].path
                self.gui.page.update()
            else:
                print("no model selected")

        pick_model_dialog = ft.FilePicker(on_result=pick_model_result)
        self.gui.page.overlay.extend([pick_model_dialog])

        def start_segmentation(e): # called when the start button is clicked
            """
            The start of the segmentation is initialized.
            """
            state_fl_button = fl_button.visible # visibility of fluorescence button before start of segmentation
            state_open_button = self.gui.open_button.visible
            try:
                start_button.visible = False
                pause_button.visible = True
                cancel_button.visible = True
                model_text.disabled = True
                model_chooser.disabled = True
                fl_button.visible = False
                self.gui.open_button.visible = False
                self.gui.directory.disable_path_choosing()
                self.gui.page.update()
                self.segmentation.run()
                # this will throw an error if something other than a model was chosen
            except:
                #TODO stop segmentation when exception is thrown
                self.gui.page.snack_bar = ft.SnackBar(ft.Text("You have selected an incompatible file for the segmentation model."))
                self.gui.page.snack_bar.open = True
                start_button.visible = True
                start_button.disabled = True
                pause_button.visible = False
                cancel_button.visible = False
                model_text.disabled = False
                model_chooser.disabled = False
                fl_button.visible = state_fl_button
                self.gui.open_button.visible = state_open_button
                self.gui.directory.enable_path_choosing()
                self.gui.csp.segmentation_running = False
                progress_bar_text.value = "Select new Model"
                self.gui.page.update()


        def cancel_segmentation(e): # called when the cancel button is clicked
            """
            The running segmentation is cancelled and the masks calculated so far are deleted, i.e. return to the start state.
            """
            #TODO hier muss ein notifier hin, der segmentation notified, dass die berechnung gestoppt werden soll
            #TODO in der Wartezeit soll klar sein, dass gerade gecancelt wird (weil es dauern könnte bis aktuelles Bild fertig bearbeitet wird)
            pause_button.visible = False
            cancel_button.visible = False
            model_text.disabled = False
            model_chooser.disabled = False
            self.gui.directory.enable_path_choosing()
            self.gui.page.update()
            self.segmentation_cancelling = True
            self.segmentation.to_be_cancelled()

        def pause_segmentation(e): # called when the pause button is clicked
            """
            The running segmentation is paused and can be resumed again.
            """
            self.segmentation.to_be_paused()
            pause_button.visible = False
            resume_button.visible = True
            progress_bar_text.value = "Paused: " + progress_bar_text.value
            self.gui.page.update()
            self.gui.csp.segmentation_pausing = True

        def resume_segmentation(e): # called when the resume button is clicked
            """
            The segmentation is resumed again from the previously paused state.
            """
            self.segmentation.to_be_resumed()
            resume_button.visible = False
            pause_button.visible = True
            progress_words = progress_bar_text.value.split()
            progress_bar_text.value = progress_words[1] + progress_words[2] # remove "paused:" from string
            self.gui.page.update()

        start_button.on_click = start_segmentation
        cancel_button.on_click = cancel_segmentation
        pause_button.on_click = pause_segmentation
        resume_button.on_click = resume_segmentation

        def finished_segmentation():
            """
            This method updates the segmentation card when the segmentation is finished.
            """
            progress_bar_text.value = "Finished"
            pause_button.visible = False
            cancel_button.visible = False
            fl_button.visible = True
            fl_button.disabled = False
            start_button.visible = True
            start_button.disabled = False
            model_text.disabled = False
            model_chooser.disabled = False
            self.gui.directory.enable_path_choosing()
            self.gui.csp.segmentation_running = False
            self.gui.page.update()

        def cancelled_segmentation():
            progress_bar_text.value = "Ready to Start"
            progress_bar.value = 0
            start_button.visible = True
            self.gui.directory.check_masks()
            if self.gui.csp.readout_path is not None:
                self.gui.open_button.visible = True
            self.segmentation_cancelling = False
            self.gui.csp.segmentation_running = False
            self.gui.page.update()

        def update_progress_bar(progress,current_image):
            """
            This method updates the progress bar at any point before, during and after the segmentation and fluorescence process.

            Arguments:
                progress (int): the current progress
                current_image (dict): the current image number
            """
            if self.segmentation_pausing:
                progress_bar_text.value = "Pausing: " + str(progress)
            elif self.segmentation_cancelling:
                progress_bar_text.value = "Cancelling: " + str(progress)
            else:
                progress_bar_text.value = progress
            extracted_num = re.search(r'\d+', progress)
            if extracted_num is not None:
                progress_bar.value = int(extracted_num.group())/100

            bfc = self.gui.csp.config.get_bf_channel()
            if current_image is not None:
                if current_image["image_id"] == self.gui.csp.image_id:
                    if current_image["image_id"] in self.gui.csp.mask_paths and bfc in self.gui.csp.mask_paths[current_image["image_id"]]:
                        self.gui.drawing_button.disabled = False
                    else:
                        self.gui.drawing_button.disabled = True
            self.gui.page.update()

    #TODO wenn vorher schon masken vorhanden sind, dann sollen diese als backup gespeichert werden bevor die segmentierung startet und wenn der abbrechen button gedrückt wird sollen die alten wiederhergestellt werden
    #TODO wenn neue files ausgewählt werden muss fluoreszenz button verschwinden
    #TODO modell muss neu ausgewählt werden können
    #TODO error anzeigen mit snack_bar (s.gui_config), z.B. wenn man starten will, ohne dass dateien ausgewählt sind
        # wenn image_path==none len(image_path)==0, dann start button nicht anzeigen
    #TODO checken ob für alle bilder schon masken haben -> wenn ja, dann soll der fluoreszenz button schon erscheinen
        def fluorescence_readout(e):
            self.fluorescence.readout_fluorescence()
            fl_button.disabled = True
            start_button.disabled = True
            self.gui.open_button.visible = False
            progress_bar_text.value = "Reading fluorescence"
            self.gui.directory.disable_path_choosing()
            self.gui.page.update()

        def start_fl(e):
            progress_bar.value = 0
            progress_bar_text.value = "0 %"
            self.gui.page.update()

        def complete_fl():
            progress_bar.value = 0
            if self.gui.csp.model_path is not None:
                progress_bar_text.value = "Ready to start"
            else:
                progress_bar_text.value = "Waiting for Input"
            self.gui.directory.enable_path_choosing()
            self.gui.page.update()


        fl_button.on_click = fluorescence_readout
        self.fluorescence.add_start_listener(listener=start_fl)
        self.fluorescence.add_update_listener(listener=update_progress_bar)
        self.fluorescence.add_completion_listener(listener=complete_fl)
        self.segmentation.add_update_listener(listener=update_progress_bar)
        self.segmentation.add_completion_listener(listener=finished_segmentation)
        self.segmentation.add_cancel_listener(listener=cancelled_segmentation)

        pick_model_row = ft.Row(
            [
                ft.Container(content=ft.Row([progress_bar, progress_bar_text])),
                ft.Container(content=ft.Row([start_button, pause_button, resume_button, cancel_button, fl_button, open_button]))
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN
        )

        model_text = ft.ListTile(
                                        leading=ft.Icon(name=ft.icons.HUB_OUTLINED),
                                        title=ft.Text("Choose Model"),
                                    )

        segmentation_container = ft.Container(
                            content=ft.Column(
                                [   model_text,
                                    pick_model_row,
                                ]
                            )
                        )

        project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        model_directory = os.path.join(project_root, "models")

        model_chooser = ft.Container(
                            content=ft.IconButton(
                                icon=ft.icons.UPLOAD_FILE,
                                tooltip="Choose Model",
                                on_click=lambda _: pick_model_dialog.pick_files(allow_multiple=False, initial_directory=model_directory),
                            ), alignment=ft.alignment.bottom_right,
                        )

        segmentation_card = ft.Card(
            content=ft.Container(
                content=ft.Stack(
                    [   segmentation_container,
                        model_chooser
                    ]
                ),
                padding=10
            ),
        )
        return segmentation_card,start_button,open_button,progress_bar,progress_bar_text